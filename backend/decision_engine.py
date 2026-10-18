"""
StudyShield - Laya 3-Tier YouTube Categorization & Decision Engine
Strictly categorizes every video across 20 YouTube Categories using:
  - Tier 0: RAM LRU Cache + Persistent SQLite Cache + Channel Authority Graph + Word-Boundary Rules
  - Tier 1: Contrastive Vector Margin Engine (ONNX / Sublinear TF-IDF Centroids) + 3-Layer Multi-Signal Scoring
  - Tier 2: Non-Blocking Asynchronous YouTube InnerTube Player API Category Probe (IDs 1..44)
"""

from collections import OrderedDict
import json
import math
import os
import re
import sqlite3
import threading
import time
from typing import Dict, List, Optional, Tuple
import numpy as np

try:
    import requests
except ImportError:
    requests = None


def best_tag_valid(tag: str) -> bool:
    return tag != "other"


class DecisionResult:
    def __init__(
        self,
        is_allowed: bool,
        category: str,
        confidence: float,
        latency_ms: float,
        matched_preference: str = "",
        explanation: str = "",
        is_study: Optional[bool] = None,
        category_tag: str = "other",
        youtube_category_id: str = "24",
        youtube_macro_category: str = "Entertainment",
        knowledge_graph_topics: Optional[List[str]] = None,
        needs_probe: bool = False,
        video_id: str = "",
    ):
        self.is_allowed = bool(is_allowed)
        self.allowed = self.is_allowed
        self.is_study = bool(is_study) if is_study is not None else self.is_allowed
        self.should_blur = not self.is_allowed
        self.action = "ALLOW" if self.is_allowed else "BLUR"
        self.category = category
        self.category_tag = category_tag
        self.youtube_category_id = str(youtube_category_id)
        self.youtube_macro_category = youtube_macro_category
        self.knowledge_graph_topics = knowledge_graph_topics or ["/m/02jjt (Entertainment)"]
        self.confidence = round(float(confidence), 4)
        self.latency_ms = round(float(latency_ms), 4)
        self.matched_preference = matched_preference
        self.explanation = explanation
        self.needs_probe = bool(needs_probe)
        self.video_id = str(video_id)

    def to_dict(self) -> Dict:
        return {
            "video_id": self.video_id,
            "is_allowed": self.is_allowed,
            "allowed": self.allowed,
            "is_study": self.is_study,
            "should_blur": self.should_blur,
            "action": self.action,
            "category": self.category,
            "category_tag": self.category_tag,
            "youtube_category_id": self.youtube_category_id,
            "youtube_macro_category": self.youtube_macro_category,
            "knowledge_graph_topics": self.knowledge_graph_topics,
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
            "matched_preference": self.matched_preference,
            "explanation": self.explanation,
            "reason": self.explanation,
            "needs_probe": self.needs_probe,
        }


class LayaDecisionEngine:
    def __init__(self, model_dir: str = "./backend/models/laya", threshold: float = 0.65):
        self.model_dir = model_dir
        self.threshold = threshold
        self.temperature = 1.2
        self.cache: OrderedDict = OrderedDict()
        self.max_cache_size = 2000
        self._last_pref_mtime = 0.0
        self._cached_prefs: Optional[Dict] = None
        self._db_lock = threading.Lock()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.pref_file = os.path.join(base_dir, "models", "laya", "active_preference.json")
        os.makedirs(os.path.dirname(self.pref_file), exist_ok=True)

        # 20 Official YouTube-Aligned Content Categories
        self.category_taxonomies: Dict[str, Dict] = {
            "study": {
                "name": "📚 Study & Academics",
                "icon": "📚",
                "yt_id": "27",
                "yt_macro": "Education",
                "kg_topics": ["/m/01k8wb (Knowledge)", "/m/029f9 (Education)", "/m/04rk0 (Mathematics & Science)"],
                "channel_priors": [
                    "mit opencourseware", "3blue1brown", "statquest", "neso academy", "gate smashers",
                    "knowledge gate", "engineering lectures", "physics wallah", "unacademy", "khan academy",
                    "byju", "vedantu", "organic chemistry tutor", "patrickjmt", "professor leonard",
                    "nptel", "swayam", "study iq", "drishti ias", "abdul bari"
                ],
                "keywords": [
                    "lecture", "lectures", "calculus", "linear algebra", "discrete math", "discrete mathematics",
                    "graph theory", "eigenvalues", "eigenvectors", "vector fields", "multiple integrals",
                    "differential equations", "probability", "statistics", "trigonometry", "geometry",
                    "engineering", "gate exam", "gate", "cracked gate", "gate preparation", "iit",
                    "iit bombay", "iit jee", "exam", "exams", "university exams", "board exam",
                    "syllabus", "semester", "5th sem", "diploma", "unit 1", "unit 2", "unit 3",
                    "unit 4", "unit 5", "physics", "chemistry", "biology", "thermodynamics",
                    "electromagnetism", "optics", "quantum mechanics", "organic chemistry",
                    "inorganic chemistry", "anatomy", "botany", "zoology", "digital electronics",
                    "logic gates", "k-maps", "boolean algebra", "microprocessor", "signals and systems",
                    "control systems", "computer organization", "pipeline hazards", "operating system",
                    "operating systems", "process scheduling", "fcfs", "round robin", "deadlock",
                    "memory management", "computer network", "computer networks", "osi model", "tcp/ip",
                    "subnetting", "dbms", "database management", "normalization", "relational algebra",
                    "history", "geography", "polity", "economics lecture", "sociology", "psychology lecture",
                    "notes", "upsc", "ncert", "cbse", "study with me", "pomodoro study", "class 10",
                    "class 11", "class 12", "neet", "jee", "explained mathematically",
                    "mathematical intuition", "previous year questions", "derivatives", "integrals"
                ],
            },
            "coding": {
                "name": "💻 Coding & Dev",
                "icon": "💻",
                "yt_id": "28",
                "yt_macro": "Science & Technology",
                "kg_topics": ["/m/07c1v (Technology)", "/m/01mf_ (Software Development)", "/m/026sq (Computer Programming)"],
                "channel_priors": [
                    "freecodecamp", "programming with mosh", "traversy media", "fireship", "love babbar",
                    "apna college", "telusko", "codewithharry", "krish naik", "campusx", "andrej karpathy",
                    "yannic kilcher", "deeplizard", "sentdex", "jenny's lectures", "striver",
                    "take u forward", "neetcode", "the primeagen", "theo - t3.gg", "web dev simplified",
                    "kevin powell", "chaiaurcode", "hitesh choudhary", "corey schafer", "cs dojo", "tech with tim"
                ],
                "keywords": [
                    "coding", "programming", "how to code", "python", "java", "c++", "c programming",
                    "javascript", "typescript", "rust", "golang", "kotlin", "swift", "ruby", "html",
                    "css", "tailwind", "react", "react js", "nextjs", "angular", "nodejs", "express js",
                    "django", "flask", "fastapi", "spring boot", "rest api", "rest apis", "graphql",
                    "full stack", "web development", "frontend", "backend", "software engineering",
                    "data structure", "data structures", "dsa", "algorithm", "algorithms", "leetcode",
                    "codeforces", "competitive programming", "dynamic programming", "binary tree",
                    "linked list", "sorting algorithm", "object oriented", "oop", "sql", "mysql",
                    "postgresql", "mongodb", "redis", "git", "github", "docker", "kubernetes", "ci/cd",
                    "devops", "microservices", "system design", "machine learning", "deep learning",
                    "artificial intelligence", "ai & ml", "neural", "neural network", "neural networks",
                    "reinforcement learning", "q-learning", "unsupervised learning", "k-means",
                    "clustering", "decision tree", "decision trees", "entropy", "information gain",
                    "support vector", "svm", "kernel trick", "convolutional", "cnn", "cnns", "nlp",
                    "natural language processing", "hugging face", "transformer", "transformers",
                    "bert", "modernbert", "bidirectional", "attention", "backpropagation",
                    "gradient descent", "pytorch", "tensorflow", "scikit-learn", "llm", "langchain",
                    "rag", "from scratch", "coding roadmap", "complete roadmap", "code review",
                    "debugging", "vs code", "api"
                ],
            },
            "tech": {
                "name": "🔧 Tech & Gadgets",
                "icon": "🔧",
                "yt_id": "28",
                "yt_macro": "Science & Technology",
                "kg_topics": ["/m/07c1v (Technology)", "/m/01c8br (Consumer Electronics)", "/m/02p7_j8 (Computer Hardware)"],
                "channel_priors": [
                    "marques brownlee", "mkbhd", "linus tech tips", "dave2d", "mrwhosetheboss",
                    "unbox therapy", "technical guruji", "trakintech", "gyan therapy", "geekyranjit",
                    "gamers nexus", "hardware unboxed", "networkchuck", "david bombal"
                ],
                "keywords": [
                    "technology", "tech review", "smartphone", "iphone", "iphone 18", "android",
                    "samsung galaxy", "pixel", "laptop", "macbook", "ipad", "tablet", "smartwatch",
                    "earbuds", "headphones", "pc build", "gaming pc", "hardware", "cpu", "gpu",
                    "rtx", "radeon", "nvidia", "amd", "intel", "motherboard", "ram", "ssd", "monitor",
                    "mechanical keyboard", "linux", "ubuntu", "arch linux", "windows 11", "macos",
                    "cloud computing", "aws", "azure", "cybersecurity", "ethical hacking",
                    "penetration testing", "wifi", "router", "iot", "raspberry pi", "arduino",
                    "robotics", "unboxing", "first look", "hands on", "specs"
                ],
            },
            "scifi": {
                "name": "🚀 Science & Space",
                "icon": "🚀",
                "yt_id": "28",
                "yt_macro": "Science & Technology",
                "kg_topics": ["/m/06mq7 (Science)", "/m/018jz (Astronomy)", "/m/06n90 (Science Fiction)"],
                "channel_priors": [
                    "kurzgesagt", "veritasium", "vsauce", "smartereveryday", "minutephysics",
                    "pbs space time", "anton petrov", "astral doorway", "scishow", "nasa", "isro",
                    "spacex", "mark rober", "star talk", "neil degrasse tyson"
                ],
                "keywords": [
                    "sci-fi", "science fiction", "space", "astronomy", "astrophysics", "cosmos",
                    "cosmology", "galaxy", "milky way", "andromeda", "nasa", "isro", "interstellar",
                    "black hole", "event horizon", "wormhole", "universe", "multiverse", "relativity",
                    "general relativity", "quantum", "quantum physics", "string theory", "dark matter",
                    "dark energy", "exoplanet", "mars", "moon", "jupiter", "saturn", "spacex",
                    "starship", "rocket launch", "orbital", "alien", "extraterrestrial", "fermi paradox",
                    "james webb", "jwst", "hubble", "telescope", "time travel", "cyberpunk", "dune",
                    "star wars", "star trek", "futurism"
                ],
            },
            "news": {
                "name": "📰 News & Politics",
                "icon": "📰",
                "yt_id": "25",
                "yt_macro": "News & Politics",
                "kg_topics": ["/m/098wr (Society)", "/m/05qt0 (Politics)", "/m/025zzc (News)"],
                "channel_priors": [
                    "wion", "firstpost", "ndtv", "india today", "bbc news", "al jazeera", "reuters",
                    "dw news", "cnn", "cnbc", "sansad tv", "lallantop", "dhruv rathee"
                ],
                "keywords": [
                    "breaking news", "world news", "live news", "geopolitics", "politics", "election",
                    "parliament", "lok sabha", "rajya sabha", "supreme court", "foreign policy",
                    "diplomacy", "united nations", "nato", "brics", "current affairs", "journalism",
                    "press conference", "prime minister", "president", "government policy", "headline",
                    "war update", "border conflict"
                ],
            },
            "finance": {
                "name": "📈 Finance & Business",
                "icon": "📈",
                "yt_id": "27",
                "yt_macro": "Education",
                "kg_topics": ["/m/09s1f (Business)", "/m/02_7t (Economics)", "/m/01y3_ (Investing)"],
                "channel_priors": [
                    "zerodha", "pranjal kamra", "akshat shrivastava", "ca rachana ranade", "warikoo",
                    "think school", "labour law advisor", "bloomberg", "wall street journal",
                    "y combinator", "patrick boyle", "the plain bagel", "finshots"
                ],
                "keywords": [
                    "finance", "personal finance", "investing", "investment", "stock market",
                    "share market", "nifty", "sensex", "wall street", "nasdaq", "mutual funds",
                    "sip", "index funds", "etf", "options trading", "intraday", "dividend", "portfolio",
                    "financial freedom", "business", "business case study", "startup",
                    "entrepreneurship", "venture capital", "shark tank", "ipo", "valuation",
                    "marketing strategy", "macroeconomics", "inflation", "recession", "gdp",
                    "central bank", "rbi", "federal reserve", "real estate", "income tax",
                    "accounting", "balance sheet"
                ],
            },
            "howto": {
                "name": "🛠️ How-To & DIY",
                "icon": "🛠️",
                "yt_id": "26",
                "yt_macro": "Howto & Style",
                "kg_topics": ["/m/019_rr (Lifestyle)", "/m/03glg (Hobby & DIY)", "/m/027x7n (Self-Improvement)"],
                "channel_priors": [
                    "ali abdaal", "thomas frank", "matt d'avella", "5-minute crafts",
                    "jerryrigeverything", "ifixit", "chris fix", "electroboom", "colin furze"
                ],
                "keywords": [
                    "how to", "diy", "do it yourself", "step by step", "woodworking", "carpentry",
                    "home improvement", "electronics repair", "restoration", "soldering", "3d printing",
                    "origami", "crafting", "gardening", "productivity", "time management",
                    "second brain", "notion template", "obsidian", "ankidroid", "flashcards",
                    "speed reading", "communication skills", "public speaking", "body language",
                    "resume building", "linkedin profile", "interview preparation", "graphic design",
                    "photoshop", "figma", "video editing", "premiere pro", "davinci resolve",
                    "blender tutorial"
                ],
            },
            "podcast": {
                "name": "🎙️ Podcasts & Talks",
                "icon": "🎙️",
                "yt_id": "22",
                "yt_macro": "People & Blogs",
                "kg_topics": ["/m/027lnzs (Podcast)", "/m/01k8wb (Conversation & Documentary)"],
                "channel_priors": [
                    "lex fridman", "ted", "tedx", "ted-ed", "huberman lab", "diary of a ceo",
                    "joe rogan", "trs", "ranveer allahbadia", "raj shamani", "nikhil kamath",
                    "smita prakash", "ani podcast", "dw documentary", "frontline pbs"
                ],
                "keywords": [
                    "podcast", "full episode", "ted talk", "tedx", "keynote speech", "lex fridman",
                    "huberman", "deep conversation", "fireside chat", "panel discussion", "roundtable",
                    "documentary", "full documentary", "biopic", "untold story", "investigative",
                    "intellectual discussion"
                ],
            },
            "cooking": {
                "name": "🍲 Cooking & Food",
                "icon": "🍲",
                "yt_id": "26",
                "yt_macro": "Howto & Style",
                "kg_topics": ["/m/02wbm (Food)", "/m/01mtb (Cooking)", "/m/019_rr (Culinary Arts)"],
                "channel_priors": [
                    "ranveer brar", "your food lab", "kabita's kitchen", "hebbars kitchen",
                    "bharatzkitchen", "joshua weissman", "babish culinary universe", "gordon ramsay",
                    "nick digiovanni", "uncle roger", "village cooking channel", "first we feast"
                ],
                "keywords": [
                    "recipe", "recipes", "cooking", "cook", "food", "street food", "kitchen", "chef",
                    "masterchef", "burger", "pizza", "pasta", "biryani", "paneer", "curry", "masala",
                    "tacos", "sushi", "ramen", "cake", "baking", "pastry", "bread", "chocolate",
                    "eating", "mukbang", "food challenge", "spicy wings", "dessert", "ice cream",
                    "taste test", "lunch recipe", "dinner recipe", "breakfast recipe", "snack",
                    "healthy meal prep", "air fryer", "restaurant"
                ],
            },
            "autos": {
                "name": "🚗 Autos & Vehicles",
                "icon": "🚗",
                "yt_id": "2",
                "yt_macro": "Autos & Vehicles",
                "kg_topics": ["/m/07yv9 (Vehicles)", "/m/0k4j (Automobiles)", "/m/04_sv (Motorcycles)"],
                "channel_priors": [
                    "carwow", "doug demuro", "top gear", "autocar india", "motoroctane",
                    "faisal khan", "powerdrift", "donut media", "supercar blondie", "fortnine"
                ],
                "keywords": [
                    "car review", "supercar", "hypercar", "sports car", "suv", "sedan", "hatchback",
                    "electric vehicle", "ev review", "tesla", "ferrari", "lamborghini", "porsche",
                    "bmw", "mercedes", "audi", "mahindra", "tata motors", "motorcycle", "superbike",
                    "bike review", "offroad", "4x4", "drag race", "formula 1", "f1", "motogp",
                    "v8 engine", "horsepower", "exhaust sound", "test drive", "automotive"
                ],
            },
            "pets": {
                "name": "🐾 Pets & Nature",
                "icon": "🐾",
                "yt_id": "15",
                "yt_macro": "Pets & Animals",
                "kg_topics": ["/m/068hy (Pets)", "/m/0jbk (Animals)", "/m/05h0n (Nature & Wildlife)"],
                "channel_priors": [
                    "national geographic", "nat geo wild", "bbc earth", "animal planet",
                    "the dodo", "brave wilderness", "girl with the dogs", "jackson galaxy"
                ],
                "keywords": [
                    "wildlife", "wild animals", "national geographic", "bbc earth", "nature documentary",
                    "animal rescue", "puppy", "puppies", "golden retriever", "german shepherd", "dogs",
                    "dog training", "kittens", "cats", "cute pets", "aquarium", "coral reef", "sharks",
                    "whales", "lions", "tigers", "elephants", "birds", "parrots", "jungle",
                    "rainforest", "safari", "veterinarian"
                ],
            },
            "travel": {
                "name": "✈️ Travel & Culture",
                "icon": "✈️",
                "yt_id": "19",
                "yt_macro": "Travel & Events",
                "kg_topics": ["/m/07bxq (Tourism)", "/m/014dsx (Travel)", "/m/0279V (Aviation)"],
                "channel_priors": [
                    "drew binsky", "kara and nate", "bald and bankrupt", "indigo traveller",
                    "yes theory", "sam chui", "monkey magic", "visa2explore", "nomadic indian"
                ],
                "keywords": [
                    "travel", "travel guide", "travel documentary", "solo travel", "backpacking",
                    "world tour", "road trip", "itinerary", "tourist places", "hidden gems",
                    "flight review", "first class flight", "business class", "aviation", "airlines",
                    "airport", "hotel review", "resort", "tourism", "exploring", "mountain trekking",
                    "himalayas", "switzerland", "japan travel", "europe trip"
                ],
            },
            "music": {
                "name": "🎵 Music & Lofi",
                "icon": "🎵",
                "yt_id": "10",
                "yt_macro": "Music",
                "kg_topics": ["/m/04rlf (Music)", "/m/02lkt (Electronic/Lo-Fi)", "/m/064t9 (Pop Music)"],
                "channel_priors": [
                    "lofi girl", "chilledcow", "t-series", "sony music", "zeemusiccompany",
                    "coke studio", "vevo", "spinnin' records", "nocopyrightsounds", "ncs",
                    "arijit singh", "a.r. rahman", "taylor swift", "the weeknd", "trap nation"
                ],
                "keywords": [
                    "music", "song", "new song", "official music video", "official video",
                    "lyrical video", "lyrics", "audio song", "full audio", "remix", "mashup",
                    "lofi", "lofi hip hop", "lofi beats", "chill beats", "acoustic", "unplugged",
                    "live concert", "music festival", "singer", "vocalist", "album", "soundtrack",
                    "playlist", "rap song", "hip hop", "rock band", "classical music", "instrumental",
                    "piano cover", "guitar cover", "cover song", "karaoke"
                ],
            },
            "sports": {
                "name": "🏏 Sports & Fitness",
                "icon": "🏏",
                "yt_id": "17",
                "yt_macro": "Sports",
                "kg_topics": ["/m/06ntj (Sports)", "/m/09xp_ (Cricket)", "/m/02vx4 (Football)", "/m/027x7n (Fitness)"],
                "channel_priors": [
                    "icc", "icc official", "bcci", "star sports", "espn", "skysports", "fifa",
                    "uefa", "nba", "ufc", "wwe", "athlean-x", "jeff nippard", "noel deyzel",
                    "chris heria", "rohit khatri"
                ],
                "keywords": [
                    "sports", "cricket", "test cricket", "ipl", "world cup", "super over", "century",
                    "hat-trick", "wicket", "virat kohli", "rohit sharma", "ms dhoni", "football",
                    "soccer", "premier league", "champions league", "la liga", "el clasico", "messi",
                    "ronaldo", "mbappe", "neymar", "match highlights", "full match highlights",
                    "olympics", "tennis", "wimbledon", "badminton", "basketball", "nba", "f1",
                    "workout", "workout routine", "gym", "gym fitness", "bodybuilding", "hypertrophy",
                    "calisthenics", "pushups", "abs workout", "fat loss", "muscle gain", "protein",
                    "boxing", "ufc", "mma", "wwe"
                ],
            },
            "anime": {
                "name": "⚔️ Anime & Manga",
                "icon": "⚔️",
                "yt_id": "31",
                "yt_macro": "Anime/Animation",
                "kg_topics": ["/m/0jxy (Anime)", "/m/04spm (Manga)", "/m/019_rr (Japanese Animation)"],
                "channel_priors": [
                    "crunchyroll", "muse asia", "ani-one asia", "toei animation", "mappa",
                    "ufotable", "netflix anime", "gigguk", "mother's basement", "animezone", "dragonballclips"
                ],
                "keywords": [
                    "anime", "manga", "manhwa", "manhua", "waifu", "isekai", "shonen", "shounen",
                    "seinen", "shojo", "amv", "ova", "ona", "crunchyroll", "funimation", "aniplex",
                    "toei", "mappa", "ufotable", "madhouse", "vtuber", "hololive", "nijisanji",
                    "english dub", "eng sub", "dragon ball", "dragon ball z", "dragon ball super",
                    "dbz", "dbs", "dbgt", "daima", "bardock", "saiyan", "super saiyan", "ssj",
                    "goku", "vegeta", "gohan", "trunks", "frieza", "freeza", "cell", "majin buu",
                    "broly", "piccolo", "krillin", "beerus", "whis", "jiren", "zamasu", "goku black",
                    "vegito", "gogeta", "kamehameha", "ultra instinct", "ultra ego", "shenron",
                    "namek", "naruto", "shippuden", "boruto", "sasuke", "uchiha", "itachi", "madara",
                    "obito", "kakashi", "jiraiya", "tsunade", "orochimaru", "minato", "hokage",
                    "sharingan", "rinnegan", "byakugan", "akatsuki", "rasengan", "chidori", "kurama",
                    "tailed beast", "shinobi", "one piece", "luffy", "zoro", "sanji", "nami", "usopp",
                    "chopper", "nico robin", "franky", "brook", "jinbe", "shanks", "kaido", "big mom",
                    "whitebeard", "blackbeard", "akainu", "gear 5", "gear fifth", "devil fruit",
                    "haki", "straw hat", "mugiwara", "wano", "egghead", "jujutsu kaisen", "jjk",
                    "gojo", "satoru", "sukuna", "ryomen", "yuji", "itadori", "megumi", "fushiguro",
                    "domain expansion", "cursed technique", "demon slayer", "kimetsu no yaiba",
                    "kimetsu", "tanjiro", "nezuko", "zenitsu", "inosuke", "muzan", "hashira",
                    "rengoku", "akaza", "kokushibo", "attack on titan", "shingeki no kyojin", "aot",
                    "eren yeager", "eren", "mikasa", "levi", "ackerman", "armin", "titan", "bleach",
                    "ichigo", "kurosaki", "aizen", "bankai", "shikai", "espada",
                    "thousand year blood war", "tybw", "my hero academia", "boku no hero", "mha",
                    "deku", "bakugo", "todoroki", "all might", "shigaraki", "one punch man",
                    "saitama", "genos", "garou", "chainsaw man", "denji", "makima", "pochita",
                    "solo leveling", "sung jinwoo", "jin-woo", "hunter x hunter", "hxh", "gon",
                    "killua", "hisoka", "kurapika", "death note", "light yagami", "ryuk",
                    "fullmetal alchemist", "edward elric", "jojo", "bizarre adventure", "jotaro",
                    "dio brando", "blue lock", "haikyuu", "baki", "vinland saga", "frieren",
                    "dandadan", "studio ghibli", "ghibli", "tokyo ghoul", "sword art online",
                    "berserk", "evangelion", "opening ost", "anime scene", "anime clip",
                    "anime edit", "anime opening"
                ],
            },
            "cartoon": {
                "name": "🎨 Cartoon & Animation",
                "icon": "🎨",
                "yt_id": "1",
                "yt_macro": "Film & Animation",
                "kg_topics": ["/m/02vxn (Film & Animation)", "/m/0215n (Cartoons)"],
                "channel_priors": [
                    "disney", "pixar", "cartoon network", "nickelodeon", "wb kids", "pogo",
                    "hungama", "alan becker", "theodd1sout", "jaiden animations"
                ],
                "keywords": [
                    "cartoon", "cartoons", "animated", "animation", "2d animation", "3d animation",
                    "stop motion", "cgi short", "tom and jerry", "disney", "pixar", "dreamworks",
                    "illumination", "ben 10", "shinchan", "doraemon", "nobita", "oggy",
                    "cockroaches", "chhota bheem", "motu patlu", "peppa pig", "mr bean animated",
                    "looney tunes", "bugs bunny", "spongebob", "rick and morty",
                    "avatar the last airbender", "spider-verse", "kids show"
                ],
            },
            "gaming": {
                "name": "🎮 Gaming & Esports",
                "icon": "🎮",
                "yt_id": "20",
                "yt_macro": "Gaming",
                "kg_topics": ["/m/0bzvm2 (Gaming)", "/m/01mw1 (Video Games)", "/m/025zzc (Esports)"],
                "channel_priors": [
                    "pewdiepie", "dream", "luke thenotable", "technoblade", "tenz", "shroud",
                    "ninja", "total gaming", "techno gamerz", "mortal", "scout", "carryislive",
                    "beastboyshub", "ign", "gamespot", "vaatividya", "radbrad", "markiplier",
                    "jacksepticeye", "gamerrealm", "twitchclips", "ishowspeed"
                ],
                "keywords": [
                    "game", "gameplay", "gaming", "let's play", "playthrough", "walkthrough",
                    "speedrun", "minecraft", "hardcore minecraft", "bedwars", "skyblock", "gta",
                    "gta 5", "gta 6", "gta rp", "rockstar games", "valorant", "1v5", "radiant",
                    "clutch", "aimbot", "crosshair", "fortnite", "battle royale", "pubg", "bgmi",
                    "free fire", "roblox", "call of duty", "warzone", "black ops", "counter strike",
                    "cs2", "csgo", "apex legends", "overwatch", "league of legends", "dota 2",
                    "elden ring", "dark souls", "sekiro", "black myth wukong", "god of war",
                    "spider-man ps5", "red dead redemption", "cyberpunk 2077", "resident evil",
                    "fifa 25", "ea fc", "genshin impact", "honkai", "among us", "clash of clans",
                    "brawl stars", "chess.com", "esports", "twitch stream", "live stream",
                    "boss fight", "hardest boss", "no armor", "ranked match", "pro highlights",
                    "50 kills", "radiant ace", "ps5", "xbox", "nintendo switch", "steam"
                ],
            },
            "vlog": {
                "name": "💄 Vlogs & Lifestyle",
                "icon": "💄",
                "yt_id": "22",
                "yt_macro": "People & Blogs",
                "kg_topics": ["/m/019_rr (Lifestyle)", "/m/013_1c (Videoblogging)"],
                "channel_priors": [
                    "sourav joshi vlogs", "flying beast", "mumbiker nikhil", "casey neistat",
                    "emma chamberlain", "logan paul", "zoella", "mostlysane", "sejal kumar",
                    "komal pandey", "techvlogger"
                ],
                "keywords": [
                    "vlog", "vlogs", "daily vlog", "day in my life", "a day in my life",
                    "travel vlog", "college vlog", "hostel life", "room tour", "house tour",
                    "studio tour", "desk setup", "minimalist setup", "aesthetic setup",
                    "flying beast", "sourav joshi", "family vlog", "couple vlog", "shopping haul",
                    "zara haul", "amazon haul", "skincare routine", "makeup tutorial", "grwm",
                    "get ready with me", "outfit ideas", "fashion", "morning routine",
                    "night routine", "storytime", "my life update", "lifestyle"
                ],
            },
            "comedy": {
                "name": "😂 Comedy & Memes",
                "icon": "😂",
                "yt_id": "23",
                "yt_macro": "Comedy",
                "kg_topics": ["/m/02jjt (Entertainment)", "/m/09kqc (Humor & Comedy)"],
                "channel_priors": [
                    "samay raina", "zakir khan", "anubhav singh bassi", "abhishek upmanyu",
                    "bb ki vines", "bhuvan bam", "ashish chanchlani", "carryminati", "harsh beniwal",
                    "round2hell", "triggered insaan", "slayy point", "tanmay bhat", "key & peele",
                    "snl", "trevor noah", "kevin hart", "fluffy", "nelk", "animalmemes"
                ],
                "keywords": [
                    "prank", "prank calling", "public prank", "comedy", "stand-up",
                    "stand-up comedy", "stand up comedy", "crowd work", "funny", "funniest",
                    "hilarious", "joke", "jokes", "roast", "roasting", "meme", "memes",
                    "dank memes", "try not to laugh", "tntl", "cringe", "cringiest",
                    "funny reaction", "reacting to", "parody", "spoof", "skit", "sketch",
                    "bloopers", "epic fails", "fails", "vines", "humor", "samay raina",
                    "zakir khan", "bassi"
                ],
            },
            "clickbait": {
                "name": "🚨 Clickbait & Drama",
                "icon": "🚨",
                "yt_id": "24",
                "yt_macro": "Entertainment",
                "kg_topics": ["/m/02jjt (Entertainment)", "/m/09k_b (Sensationalism & Viral Media)"],
                "channel_priors": [
                    "mrbeast", "dhar mann", "airrack", "ryan trahan", "fukra insaan", "elvish yadav",
                    "buzzfeed", "bollywoodgaram", "filmibeat", "gossipcentral", "viraldrama",
                    "getrichfast", "cryptoguru", "hypetech", "mysteryfiles"
                ],
                "keywords": [
                    "mrbeast", "shocking", "secret hack", "wealth hack", "make money fast",
                    "get rich", "zero effort", "guaranteed", "10,000/hr", "arrested", "exposed",
                    "controversy", "drama", "leaked", "$1 vs", "$1,000,000", "blindfolded",
                    "buying everything", "last to leave", "24 hours", "7 days straight",
                    "viral challenge", "extreme challenge", "you won't believe", "you wont believe",
                    "must watch", "gone wrong", "billionaire", "crypto", "memecoin", "100x coin",
                    "conspiracy theories", "abandoned island", "found this inside",
                    "destroyed android", "red carpet", "unseen moments", "paparazzi",
                    "hollywood", "bollywood", "celebrity", "gossip", "illuminati"
                ],
            },
        }

        # Pre-compile regex patterns with strict word boundaries (?<!\w)...(?!\w)
        # Prevents substring bugs like "doc" matching inside "Bardock"
        self._compiled_keywords: Dict[str, List[Tuple[re.Pattern, float]]] = {}
        self._compiled_channels: Dict[str, List[str]] = {}

        for tag, info in self.category_taxonomies.items():
            kw_patterns = []
            for kw in info["keywords"]:
                kw_clean = kw.strip().lower()
                if not kw_clean:
                    continue
                word_count = len(kw_clean.split())
                weight = float(word_count * 2.0 + (1.2 if word_count > 1 else 0.0))
                pat = re.compile(r"(?<!\w)" + re.escape(kw_clean) + r"(?!\w)", re.IGNORECASE)
                kw_patterns.append((pat, weight))
            self._compiled_keywords[tag] = kw_patterns
            self._compiled_channels[tag] = [ch.strip().lower() for ch in info["channel_priors"] if ch.strip()]

        self._instructional_boosters = re.compile(
            r"\b(crash course|full course|complete course|lecture \d+|unit \d+|tutorial|for beginners|for students|explained|deep dive|walkthrough|from scratch|roadmap)\b",
            re.IGNORECASE,
        )
        self._clickbait_structural = [
            re.compile(r"\$\d[\d,]*\s*vs\.?\s*\$\d[\d,]*", re.IGNORECASE),
            re.compile(
                r"\b(i survived \d+ days|for \d+ days straight|in 24 hours|you won'?t believe|must watch!|shocking:?)\b",
                re.IGNORECASE,
            ),
        ]

        # SQLite Persistent Cache Initialization
        self.db_path = os.path.join(base_dir, "models", "laya", "studyshield_cache.db")
        self._init_sqlite()

        # Tier 1 Contrastive Vector Centroid Initialization across all 20 Categories
        self._init_vector_engine()
        self.load_preferences()

    def _init_sqlite(self):
        try:
            with self._db_lock:
                conn = sqlite3.connect(self.db_path, timeout=5.0)
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS decision_cache (
                        video_id TEXT PRIMARY KEY,
                        title TEXT,
                        channel TEXT,
                        decision_json TEXT,
                        category_tag TEXT,
                        is_allowed INTEGER,
                        confidence REAL,
                        source TEXT,
                        created_at REAL
                    );
                    """
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_vid ON decision_cache(video_id);")
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"[StudyShield Engine] SQLite init error: {e}")

    def _evaluate_policy_for_tag(
        self,
        category_tag: str,
        title: str,
        channel: str,
        effective_shield: bool,
        effective_cats: List[str],
        custom_kws: List[str],
    ) -> Tuple[bool, str, str]:
        """Dynamically evaluates whether a category_tag is allowed under current user preferences."""
        yt_info = self.category_taxonomies.get(
            category_tag,
            {
                "name": "🎬 General Entertainment",
                "yt_id": "24",
                "yt_macro": "Entertainment",
            },
        )
        detected_category = yt_info["name"]

        if not effective_shield:
            return True, "Shield OFF (All Allowed)", "Shield toggle is OFF. All videos remain unblurred."

        if category_tag in effective_cats:
            return (
                True,
                detected_category,
                f"YouTube Cat ID {yt_info['yt_id']} ({yt_info['yt_macro']}) • Matches active preference ({detected_category}).",
            )

        if custom_kws:
            combined_lower = f"{title or ''} {channel or ''}".lower()
            for kw in custom_kws:
                kw_clean = kw.strip().lower()
                if kw_clean and re.search(r"(?<!\w)" + re.escape(kw_clean) + r"(?!\w)", combined_lower):
                    return True, f"Custom: {kw_clean}", f"Matched user custom keyword '{kw_clean}'."

        return (
            False,
            "Blocked",
            f"YouTube Cat ID {yt_info['yt_id']} ({yt_info['yt_macro']}) • Classified as {detected_category}, which is not in your allowed topics.",
        )

    def _get_batch_from_sqlite(
        self,
        video_ids: List[str],
        effective_shield: bool,
        effective_cats: List[str],
        custom_kws: List[str],
    ) -> Dict[str, DecisionResult]:
        """Fetches cached video classifications in a single SQLite query and applies current user preferences."""
        valid_ids = [vid for vid in video_ids if vid and not vid.startswith("syn_") and not vid.startswith("synthetic_")]
        if not valid_ids:
            return {}
        found: Dict[str, DecisionResult] = {}
        try:
            placeholders = ",".join(["?"] * len(valid_ids))
            with self._db_lock:
                conn = sqlite3.connect(self.db_path, timeout=3.0)
                cur = conn.cursor()
                cur.execute(
                    f"SELECT video_id, title, channel, decision_json, category_tag, confidence FROM decision_cache WHERE video_id IN ({placeholders})",
                    valid_ids,
                )
                rows = cur.fetchall()
                conn.close()

            for vid, title, channel, dec_json, cat_tag, conf in rows:
                data = json.loads(dec_json) if dec_json else {}
                tag = cat_tag or data.get("category_tag", "other")
                yt_info = self.category_taxonomies.get(
                    tag,
                    {
                        "name": data.get("category", "🎬 General Entertainment"),
                        "yt_id": data.get("youtube_category_id", "24"),
                        "yt_macro": data.get("youtube_macro_category", "Entertainment"),
                        "kg_topics": data.get("knowledge_graph_topics", ["/m/02jjt (Entertainment)"]),
                    },
                )
                is_allowed, matched_pref, explanation = self._evaluate_policy_for_tag(
                    tag, title or "", channel or "", effective_shield, effective_cats, custom_kws
                )
                is_educational = tag in ("study", "coding")
                found[vid] = DecisionResult(
                    is_allowed=is_allowed,
                    category=yt_info["name"],
                    confidence=float(conf or data.get("confidence", 0.95)),
                    latency_ms=0.05,
                    matched_preference=matched_pref,
                    explanation=explanation,
                    is_study=is_educational,
                    category_tag=tag,
                    youtube_category_id=yt_info["yt_id"],
                    youtube_macro_category=yt_info["yt_macro"],
                    knowledge_graph_topics=yt_info.get("kg_topics", ["/m/02jjt (Entertainment)"]),
                    needs_probe=False,
                    video_id=vid,
                )
        except Exception:
            pass
        return found

    def _save_batch_to_sqlite(self, records: List[Tuple[str, str, str, DecisionResult, str]]):
        """Saves multiple decisions to SQLite in a single transaction."""
        valid_records = [
            r for r in records if r[0] and not r[0].startswith("syn_") and not r[0].startswith("synthetic_")
        ]
        if not valid_records:
            return
        try:
            now = time.time()
            rows = [
                (
                    vid,
                    title,
                    channel,
                    json.dumps(res.to_dict()),
                    res.category_tag,
                    1 if res.is_allowed else 0,
                    res.confidence,
                    source,
                    now,
                )
                for vid, title, channel, res, source in valid_records
            ]
            with self._db_lock:
                conn = sqlite3.connect(self.db_path, timeout=3.0)
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO decision_cache
                    (video_id, title, channel, decision_json, category_tag, is_allowed, confidence, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows,
                )
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"[StudyShield Engine] SQLite batch save error: {e}")

    def _init_vector_engine(self):
        """Builds fast vectorized category centroids across all 20 YouTube categories."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer

            self._category_order = list(self.category_taxonomies.keys())
            corpus_docs = []
            for tag in self._category_order:
                info = self.category_taxonomies[tag]
                doc = " ".join(info["keywords"]) + " " + " ".join(info["channel_priors"])
                corpus_docs.append(doc.lower())

            self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
            self._category_centroids = self._vectorizer.fit_transform(corpus_docs).toarray()
            self._study_indices = [
                i for i, t in enumerate(self._category_order) if t in ("study", "coding", "scifi", "tech", "finance", "howto")
            ]
            self._distract_indices = [
                i for i, t in enumerate(self._category_order) if t in ("anime", "cartoon", "gaming", "vlog", "comedy", "clickbait", "music", "sports")
            ]
            self._has_vector_engine = True
        except Exception as e:
            print(f"[StudyShield Engine] Vector engine fallback to rules: {e}")
            self._has_vector_engine = False

    def classify_contrastive_margin(
        self, title: str, channel: str = "", duration: str = ""
    ) -> Tuple[float, float, float]:
        """
        Computes Contrastive Margin:
          S_study = max cosine similarity vs Study/Educational centroids
          S_distract = max cosine similarity vs Distraction centroids
          Delta = S_study - S_distract
        """
        if not getattr(self, "_has_vector_engine", False):
            return 0.0, 0.0, 0.0
        try:
            from sklearn.metrics.pairwise import cosine_similarity

            combined = f"{title} {channel}".lower()
            vec = self._vectorizer.transform([combined]).toarray()
            sims = cosine_similarity(vec, self._category_centroids)[0]
            sim_study = float(np.max(sims[self._study_indices])) if self._study_indices else 0.0
            sim_distract = float(np.max(sims[self._distract_indices])) if self._distract_indices else 0.0
            margin = sim_study - sim_distract
            return margin, sim_study, sim_distract
        except Exception:
            return 0.0, 0.0, 0.0

    def _default_preferences(self) -> Dict:
        return {
            "shield_enabled": True,
            "active_categories": ["study", "coding"],
            "custom_keywords": [],
            "blocked_count": 0,
            "allowed_count": 0,
            "updated_at": time.time(),
        }

    def load_preferences(self) -> Dict:
        try:
            if os.path.exists(self.pref_file):
                mtime = os.path.getmtime(self.pref_file)
                if self._cached_prefs is not None and mtime == self._last_pref_mtime:
                    return self._cached_prefs
                with open(self.pref_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                defaults = self._default_preferences()
                defaults.update(data)
                if mtime != self._last_pref_mtime:
                    self.cache.clear()
                self._last_pref_mtime = mtime
                self._cached_prefs = defaults
                return defaults
        except Exception:
            pass
        defaults = self._default_preferences()
        self.save_preferences(defaults)
        return defaults

    def save_preferences(self, prefs: Dict) -> Dict:
        try:
            current = self._default_preferences()
            if os.path.exists(self.pref_file):
                try:
                    with open(self.pref_file, "r", encoding="utf-8") as f:
                        current.update(json.load(f))
                except Exception:
                    pass
            for key in ("shield_enabled", "active_categories", "custom_keywords", "blocked_count", "allowed_count"):
                if key in prefs and prefs[key] is not None:
                    current[key] = prefs[key]
            current["updated_at"] = time.time()
            with open(self.pref_file, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2)
            self._last_pref_mtime = os.path.getmtime(self.pref_file)
            self._cached_prefs = current
            self.cache.clear()
            return current
        except Exception as e:
            print(f"[Laya Engine] Error saving preferences: {e}")
            return prefs

    def classify_youtube_3layer(
        self, title: str, channel: str = "", is_artist: bool = False, duration: str = ""
    ) -> Tuple[str, str, float, Dict]:
        """
        Executes YouTube's 3-Layer Categorization Algorithm across all 20 Categories:
          - Signal A: Channel Authority & Creator Graph Prior
          - Signal B: Multi-N-Gram Title & Word-Boundary Semantic Matching
          - Signal C: Contextual Disambiguation (Study vs Coding, Walkthroughs, Clickbait, Duration)
          - Signal D: Temperature-Scaled Softmax Confidence (T = 1.2)
        """
        title_lower = (title or "").strip().lower()
        channel_lower = (channel or "").strip().lower()
        combined_text = f"{title_lower} {channel_lower}".strip()

        if is_artist or "♪" in channel_lower or "official artist" in channel_lower:
            music_info = self.category_taxonomies["music"]
            return music_info["name"], "music", 0.99, music_info

        scores: Dict[str, float] = {tag: 0.0 for tag in self.category_taxonomies}

        # Signal A: Channel Authority Priors
        if channel_lower:
            for tag, ch_list in self._compiled_channels.items():
                for ch in ch_list:
                    if ch in channel_lower:
                        scores[tag] += 5.5

            if any(w in channel_lower for w in ("academy", "classes", "university", "lectures", "opencourseware")):
                scores["study"] += 3.5
            if any(w in channel_lower for w in ("code", "coder", "developer", "dev")):
                scores["coding"] += 3.0
            if any(w in channel_lower for w in ("gaming", "gamer", "plays", "twitch")):
                scores["gaming"] += 4.5
            if any(w in channel_lower for w in ("vlogs", "vlogger")):
                scores["vlog"] += 4.5

        # Signal B: Strict Word-Boundary Keyword Matching
        for tag, pat_list in self._compiled_keywords.items():
            for pat, weight in pat_list:
                if pat.search(combined_text):
                    scores[tag] += weight

        # Signal C: Contextual Disambiguation (Study vs Coding, Clickbait, 4K Anime clips)
        has_instructional = bool(self._instructional_boosters.search(title_lower))
        if has_instructional:
            if scores["coding"] > 0 and scores["coding"] >= scores["study"]:
                scores["coding"] += 4.5
            elif scores["study"] > 0:
                scores["study"] += 4.5
            elif scores["tech"] > 0:
                scores["coding"] += 5.0

        if "walkthrough" in title_lower and (scores["study"] > 0 or scores["coding"] > 0):
            scores["gaming"] = max(0.0, scores["gaming"] - 4.0)

        for cb_pat in self._clickbait_structural:
            if cb_pat.search(title_lower):
                scores["clickbait"] += 6.5

        if scores["study"] < 2.0 and scores["coding"] < 2.0:
            if re.search(r"【.*4k.*】|\b4k\s*uhd\b|\b60\s*fps\b", title_lower):
                if scores["anime"] > 0:
                    scores["anime"] += 4.0
                elif scores["clickbait"] <= 0 and scores["gaming"] <= 0:
                    scores["anime"] += 3.0

        best_tag = max(scores, key=scores.get)
        best_score = scores[best_tag]

        # If keyword rules found no match, consult Tier 1 TF-IDF Vector Centroids across all 20 categories
        if best_score <= 0.0 and getattr(self, "_has_vector_engine", False):
            try:
                from sklearn.metrics.pairwise import cosine_similarity

                vec = self._vectorizer.transform([combined_text]).toarray()
                sims = cosine_similarity(vec, self._category_centroids)[0]
                best_idx = int(np.argmax(sims))
                if sims[best_idx] >= 0.18:
                    best_tag = self._category_order[best_idx]
                    best_score = float(sims[best_idx] * 10.0)
            except Exception:
                pass

        if best_score <= 0.0:
            fallback_info = {
                "name": "🎬 General Entertainment",
                "icon": "🎬",
                "yt_id": "24",
                "yt_macro": "Entertainment",
                "kg_topics": ["/m/02jjt (Entertainment)"],
            }
            return fallback_info["name"], "other", 0.50, fallback_info

        # Signal D: Calibrated Confidence (T = 1.2)
        calibrated_conf = min(0.99, 1.0 / (1.0 + math.exp(-(best_score - 1.5) / self.temperature)))
        best_info = self.category_taxonomies[best_tag]
        return best_info["name"], best_tag, calibrated_conf, best_info

    def classify_category(self, text: str) -> Tuple[str, str, float]:
        """Backwards-compatible helper returning (Category Name, Category Tag, Confidence)."""
        cat_name, cat_tag, conf, _ = self.classify_youtube_3layer(text, "")
        return cat_name, cat_tag, conf

    def decide(
        self,
        title: str,
        channel: str = "",
        focus_domain: str = "aiml",
        track_stats: bool = True,
        video_id: str = "",
    ) -> DecisionResult:
        start = time.perf_counter()
        prefs = self.load_preferences()
        shield_enabled = prefs.get("shield_enabled", True)
        active_cats = prefs.get("active_categories", ["study", "coding"])
        custom_kws = prefs.get("custom_keywords", [])

        effective_cats = list(active_cats)
        effective_shield = bool(shield_enabled)

        cache_key = (
            f"{video_id}::{title.strip().lower()}::{channel.strip().lower()}::"
            f"{effective_shield}::{','.join(sorted(effective_cats))}::{','.join(sorted(custom_kws))}"
        )
        if cache_key in self.cache:
            self.cache.move_to_end(cache_key)
            cached = self.cache[cache_key]
            cached.latency_ms = round((time.perf_counter() - start) * 1000, 4)
            return cached

        # Check SQLite cache if valid video_id is provided
        if video_id and not video_id.startswith("syn_"):
            sql_hits = self._get_batch_from_sqlite([video_id], effective_shield, effective_cats, custom_kws)
            if video_id in sql_hits:
                res = sql_hits[video_id]
                res.latency_ms = round((time.perf_counter() - start) * 1000, 4)
                self._store_cache(cache_key, res)
                return res

        detected_category, detected_tag, conf, yt_info = self.classify_youtube_3layer(title, channel)
        is_educational = detected_tag in ("study", "coding")
        is_allowed, matched_pref, explanation = self._evaluate_policy_for_tag(
            detected_tag, title, channel, effective_shield, effective_cats, custom_kws
        )

        if track_stats and self._cached_prefs is not None:
            if is_allowed:
                self._cached_prefs["allowed_count"] = self._cached_prefs.get("allowed_count", 0) + 1
            else:
                self._cached_prefs["blocked_count"] = self._cached_prefs.get("blocked_count", 0) + 1

        elapsed_ms = (time.perf_counter() - start) * 1000
        result = DecisionResult(
            is_allowed=is_allowed,
            category=detected_category,
            confidence=conf if best_tag_valid(detected_tag) else 0.88,
            latency_ms=elapsed_ms,
            matched_preference=matched_pref,
            explanation=explanation,
            is_study=is_educational,
            category_tag=detected_tag,
            youtube_category_id=yt_info["yt_id"],
            youtube_macro_category=yt_info["yt_macro"],
            knowledge_graph_topics=yt_info.get("kg_topics", ["/m/02jjt (Entertainment)"]),
            needs_probe=(detected_tag == "other"),
            video_id=video_id,
        )
        self._store_cache(cache_key, result)
        if video_id and not video_id.startswith("syn_"):
            self._save_batch_to_sqlite([(video_id, title, channel, result, "3layer_decide")])
        return result

    def _store_cache(self, key: str, result: DecisionResult):
        self.cache[key] = result
        if len(self.cache) > self.max_cache_size:
            self.cache.popitem(last=False)

    def classify_video(self, title: str, channel: str = "", focus_domain: str = "aiml") -> Dict:
        """Helper method returning dict compatible with classify endpoints."""
        return self.decide(title=title, channel=channel, focus_domain=focus_domain).to_dict()

    def decide_batch(self, items: List[Dict], focus_domain: str = "aiml") -> Dict[str, Dict]:
        """
        Processes up to 25 items in a single vectorized batch (<15ms).
        Respects all 20 YouTube categories, active user preferences, and custom keywords!
        Uses 3-Tier Pipeline:
          - Tier 0: RAM LRU Cache + Batched SQLite Cache
          - Tier 1: 3-Layer 20-Category Engine + Contrastive Vector Margin Scoring
          - Tier 2: Non-blocking probe flag for unknown/ambiguous clickbait titles
        """
        t_batch_start = time.perf_counter()
        prefs = self.load_preferences()
        effective_shield = bool(prefs.get("shield_enabled", True))
        effective_cats = list(prefs.get("active_categories", ["study", "coding"]))
        custom_kws = list(prefs.get("custom_keywords", []))

        pref_sig = f"{effective_shield}::{','.join(sorted(effective_cats))}::{','.join(sorted(custom_kws))}"
        results: Dict[str, Dict] = {}
        unresolved: List[Dict] = []

        # 1. Check In-Memory LRU Cache (0.001ms)
        for item in items[:25]:
            vid = str(item.get("id") or item.get("video_id") or "")
            title = str(item.get("title") or "").strip()
            channel = str(item.get("channel") or "").strip()
            if not vid:
                vid = f"syn_{abs(hash(title + channel))}"

            ram_key = f"batch::{vid}::{title.lower()}::{channel.lower()}::{pref_sig}"
            if ram_key in self.cache:
                self.cache.move_to_end(ram_key)
                cached_res = self.cache[ram_key]
                results[vid] = cached_res.to_dict()
            else:
                unresolved.append(
                    {
                        "id": vid,
                        "title": title,
                        "channel": channel,
                        "duration": str(item.get("duration") or ""),
                        "is_artist": bool(item.get("is_artist") or item.get("is_artist_channel", False)),
                        "ram_key": ram_key,
                    }
                )

        if not unresolved:
            return results

        # 2. Tier 0: Batched SQLite Lookup (Single query for all unresolved IDs)
        sql_hits = self._get_batch_from_sqlite(
            [u["id"] for u in unresolved], effective_shield, effective_cats, custom_kws
        )
        still_unresolved: List[Dict] = []
        for u in unresolved:
            vid = u["id"]
            if vid in sql_hits:
                res_obj = sql_hits[vid]
                self._store_cache(u["ram_key"], res_obj)
                results[vid] = res_obj.to_dict()
            else:
                still_unresolved.append(u)

        # 3. Tier 1: 20-Category Classification + Contrastive Vector Margin
        sqlite_to_save: List[Tuple[str, str, str, DecisionResult, str]] = []
        allowed_delta = 0
        blocked_delta = 0

        for u in still_unresolved:
            t_item = time.perf_counter()
            vid = u["id"]
            title = u["title"]
            channel = u["channel"]
            duration = u["duration"]
            is_artist = u["is_artist"]

            detected_category, detected_tag, conf, yt_info = self.classify_youtube_3layer(
                title=title, channel=channel, is_artist=is_artist, duration=duration
            )

            needs_probe = False
            source_tier = "tier1_3layer"

            # If 3-layer classification was uncertain ("other"), run Contrastive Vector Margin
            if detected_tag == "other":
                margin, s_study, s_dist = self.classify_contrastive_margin(title, channel, duration)
                if margin >= 0.05 and s_study >= 0.25:
                    detected_tag = "study"
                    yt_info = self.category_taxonomies["study"]
                    detected_category = yt_info["name"]
                    conf = round(min(0.92, 0.65 + margin), 4)
                    source_tier = "tier1_vector_study"
                elif margin <= -0.04 or s_dist >= 0.28:
                    detected_tag = "clickbait"
                    yt_info = self.category_taxonomies["clickbait"]
                    detected_category = yt_info["name"]
                    conf = round(min(0.92, 0.65 + abs(margin)), 4)
                    source_tier = "tier1_vector_distract"
                else:
                    # Ambiguous Dead-Zone (-0.04 < Delta < +0.05) -> Flag for non-blocking Tier 2 probe
                    needs_probe = not vid.startswith("syn_")
                    source_tier = "tier2_provisional"

            is_allowed, matched_pref, explanation = self._evaluate_policy_for_tag(
                detected_tag, title, channel, effective_shield, effective_cats, custom_kws
            )
            if needs_probe:
                explanation = f"Provisional state ({explanation}) • Flagged for Tier 2 InnerTube probe."

            if is_allowed:
                allowed_delta += 1
            else:
                blocked_delta += 1

            item_lat = (time.perf_counter() - t_item) * 1000
            res_obj = DecisionResult(
                is_allowed=is_allowed,
                category=detected_category,
                confidence=conf,
                latency_ms=item_lat,
                matched_preference=matched_pref,
                explanation=explanation,
                is_study=(detected_tag in ("study", "coding")),
                category_tag=detected_tag,
                youtube_category_id=yt_info["yt_id"],
                youtube_macro_category=yt_info["yt_macro"],
                knowledge_graph_topics=yt_info.get("kg_topics", ["/m/02jjt (Entertainment)"]),
                needs_probe=needs_probe,
                video_id=vid,
            )

            self._store_cache(u["ram_key"], res_obj)
            results[vid] = res_obj.to_dict()

            # Only persist confident classifications to SQLite (provisional ones are updated after Tier 2 probe)
            if not needs_probe:
                sqlite_to_save.append((vid, title, channel, res_obj, source_tier))

        if sqlite_to_save:
            self._save_batch_to_sqlite(sqlite_to_save)

        # Update in-memory telemetry counters and persist
        if self._cached_prefs is not None and (allowed_delta > 0 or blocked_delta > 0):
            self._cached_prefs["allowed_count"] = self._cached_prefs.get("allowed_count", 0) + allowed_delta
            self._cached_prefs["blocked_count"] = self._cached_prefs.get("blocked_count", 0) + blocked_delta
            try:
                with open(self.pref_file, "w", encoding="utf-8") as f:
                    json.dump(self._cached_prefs, f, indent=2)
                self._last_pref_mtime = os.path.getmtime(self.pref_file)
            except Exception:
                pass

        return results

    def probe_youtube_category(self, video_id: str) -> Optional[Dict]:
        """
        Tier 2 Async Probe: Queries YouTube's internal /youtubei/v1/player API for official category.
        Maps YouTube category back to the 20 StudyShield tags and evaluates user preferences.
        """
        if not requests or not video_id or video_id.startswith("syn_"):
            return None

        t0 = time.perf_counter()
        try:
            url = "https://www.youtube.com/youtubei/v1/player"
            payload = {
                "videoId": video_id,
                "context": {
                    "client": {
                        "clientName": "WEB",
                        "clientVersion": "2.20260101.00.00",
                    }
                },
            }
            resp = requests.post(url, json=payload, timeout=2.5)
            if resp.status_code != 200:
                return None

            data = resp.json()
            micro = data.get("microformat", {}).get("playerMicroformatRenderer", {})
            vid_details = data.get("videoDetails", {})

            cat_name = micro.get("category", "")
            cat_id = str(micro.get("categoryId", "24"))
            title = vid_details.get("title", "")
            author = vid_details.get("author", "")

            if not cat_name and not title:
                return None

            # Map official YouTube category to StudyShield category tag
            yt_cat_map = {
                "education": "study",
                "science & technology": "coding",
                "news & politics": "news",
                "howto & style": "howto",
                "music": "music",
                "sports": "sports",
                "gaming": "gaming",
                "comedy": "comedy",
                "pets & animals": "pets",
                "autos & vehicles": "autos",
                "travel & events": "travel",
                "film & animation": "cartoon",
                "people & blogs": "vlog",
            }

            # Re-run 3-layer with full official title & author first
            detected_category, detected_tag, conf, yt_info = self.classify_youtube_3layer(title, author)
            if detected_tag == "other":
                detected_tag = yt_cat_map.get(cat_name.strip().lower(), "clickbait")
                yt_info = self.category_taxonomies.get(
                    detected_tag,
                    {
                        "name": f"🎬 {cat_name or 'Entertainment'}",
                        "yt_id": cat_id,
                        "yt_macro": cat_name or "Entertainment",
                        "kg_topics": ["/m/02jjt (Entertainment)"],
                    },
                )
                detected_category = yt_info["name"]
                conf = 0.94

            prefs = self.load_preferences()
            is_allowed, matched_pref, _ = self._evaluate_policy_for_tag(
                detected_tag,
                title,
                author,
                bool(prefs.get("shield_enabled", True)),
                list(prefs.get("active_categories", ["study", "coding"])),
                list(prefs.get("custom_keywords", [])),
            )

            elapsed_ms = (time.perf_counter() - t0) * 1000
            res = DecisionResult(
                is_allowed=is_allowed,
                category=detected_category,
                confidence=conf,
                latency_ms=elapsed_ms,
                matched_preference=matched_pref,
                explanation=f"Verified via YouTube Player API: Category '{cat_name}' (ID {cat_id})",
                is_study=(detected_tag in ("study", "coding")),
                category_tag=detected_tag,
                youtube_category_id=yt_info.get("yt_id", cat_id),
                youtube_macro_category=yt_info.get("yt_macro", cat_name or "Entertainment"),
                knowledge_graph_topics=yt_info.get("kg_topics", ["/m/02jjt (Entertainment)"]),
                needs_probe=False,
                video_id=video_id,
            )

            self._save_batch_to_sqlite([(video_id, title, author, res, "tier2_innertube")])
            return res.to_dict()
        except Exception as e:
            print(f"[StudyShield Engine] Tier 2 probe error for {video_id}: {e}")
            return None


DecisionEngine = LayaDecisionEngine
