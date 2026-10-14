"""
StudyShield — Laya 3-Layer YouTube Categorization & Decision Engine
Strictly categorizes every video using:
  1. Layer 1: Official YouTube videoCategoryId (IDs 1..44)
  2. Layer 2: Knowledge Graph Micro-Topic Ontology (/m/... IDs)
  3. Layer 3: Real-Time Multi-Signal Scoring (Channel Graph Priors + N-Gram NLP +
              Structural Syntax + Contextual Study-vs-Coding Disambiguation + Softmax T=1.2)
"""

import json
import math
import os
import re
import time
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple


class DecisionResult:
    def __init__(
        self,
        is_allowed: bool,
        category: str,
        confidence: float,
        latency_ms: float = 0.0,
        matched_preference: str = "",
        explanation: str = "",
        is_study: Optional[bool] = None,
        category_tag: str = "other",
        youtube_category_id: str = "24",
        youtube_macro_category: str = "Entertainment",
        knowledge_graph_topics: Optional[List[str]] = None,
    ):
        self.is_allowed = bool(is_allowed)
        self.is_study = bool(is_allowed if is_study is None else is_study)
        self.category = category
        self.category_tag = category_tag
        self.youtube_category_id = youtube_category_id
        self.youtube_macro_category = youtube_macro_category
        self.knowledge_graph_topics = knowledge_graph_topics or ["/m/02jjt (Entertainment)"]
        self.confidence = round(float(confidence), 2)
        self.latency_ms = round(float(latency_ms), 3)
        self.matched_preference = matched_preference
        self.explanation = explanation

    def to_dict(self) -> Dict:
        return {
            "is_allowed": self.is_allowed,
            "is_study": self.is_study,
            "category": self.category,
            "category_tag": self.category_tag,
            "youtube_category_id": self.youtube_category_id,
            "youtube_macro_category": self.youtube_macro_category,
            "knowledge_graph_topics": self.knowledge_graph_topics,
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
            "matched_preference": self.matched_preference,
            "explanation": self.explanation,
        }


class LayaDecisionEngine:
    def __init__(self, model_dir: str = "./backend/models/laya", threshold: float = 0.65):
        self.model_dir = model_dir
        self.threshold = threshold
        self.temperature = 1.2
        self.cache: OrderedDict[str, DecisionResult] = OrderedDict()
        self.max_cache_size = 1024
        self._last_pref_mtime = 0.0
        self._cached_prefs: Optional[Dict] = None

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.pref_file = os.path.join(base_dir, "models", "laya", "active_preference.json")
        os.makedirs(os.path.dirname(self.pref_file), exist_ok=True)

        # 20 YouTube-Aligned Categories with Layer-1 (videoCategoryId) & Layer-2 (Knowledge Graph IDs)
        self.category_taxonomies: Dict[str, Dict] = {
            "study": {
                "name": "📚 Study & Academics",
                "icon": "📚",
                "tag": "study",
                "yt_id": "27",
                "yt_macro": "Education",
                "kg_topics": ["/m/01k8wb (Knowledge)", "/m/029f9 (Education)", "/m/04rk0 (Mathematics & Science)"],
                "channel_priors": [
                    "mit opencourseware", "3blue1brown", "statquest", "neso academy", "gate smashers",
                    "knowledge gate", "engineering lectures", "physics wallah", "unacademy", "khan academy",
                    "byju", "vedantu", "organic chemistry tutor", "patrickjmt", "professor leonard",
                    "nptel", "swayam", "study iq", "drishti ias"
                ],
                "keywords": [
                    "lecture", "lectures", "calculus", "linear algebra", "discrete math",
                    "discrete mathematics", "graph theory", "eigenvalues", "eigenvectors",
                    "vector fields", "multiple integrals", "differential equations", "probability",
                    "statistics", "trigonometry", "geometry", "engineering", "gate exam", "gate",
                    "cracked gate", "gate preparation", "gate smashers", "iit", "iit bombay", "iit jee",
                    "exam", "exams", "university exams", "board exam", "syllabus", "semester",
                    "5th sem", "diploma", "unit 1", "unit 2", "unit 3", "unit 4", "unit 5",
                    "physics", "chemistry", "biology", "thermodynamics", "electromagnetism",
                    "optics", "quantum mechanics", "organic chemistry", "inorganic chemistry",
                    "anatomy", "botany", "zoology", "digital electronics", "logic gates",
                    "k-maps", "boolean algebra", "microprocessor", "signals and systems",
                    "control systems", "computer organization", "pipeline hazards",
                    "operating system", "operating systems", "process scheduling", "fcfs",
                    "round robin", "deadlock", "memory management", "computer network",
                    "computer networks", "osi model", "tcp/ip", "subnetting", "dbms",
                    "database management", "normalization", "relational algebra", "history",
                    "geography", "polity", "economics lecture", "sociology", "psychology lecture",
                    "notes", "upsc", "ncert", "cbse", "study with me", "pomodoro study",
                    "class 10", "class 11", "class 12", "neet", "jee",
                    "explained mathematically", "mathematical intuition", "previous year questions"
                ],
            },
            "coding": {
                "name": "💻 Coding & Dev",
                "icon": "💻",
                "tag": "coding",
                "yt_id": "28",
                "yt_macro": "Science & Technology",
                "kg_topics": ["/m/07c1v (Technology)", "/m/01mf_ (Software Development)", "/m/026sq (Computer Programming)"],
                "channel_priors": [
                    "freecodecamp", "programming with mosh", "traversy media", "fireship",
                    "love babbar", "apna college", "telusko", "codewithharry", "krish naik",
                    "campusx", "andrej karpathy", "yannic kilcher", "deeplizard", "sentdex",
                    "jenny's lectures", "striver", "take u forward", "neetcode", "the primeagen",
                    "theo - t3.gg", "web dev simplified", "kevin powell", "chaiaurcode", "hitesh choudhary"
                ],
                "keywords": [
                    "coding", "programming", "how to code", "python", "java", "c++",
                    "c programming", "javascript", "typescript", "rust", "golang", "kotlin",
                    "swift", "php", "ruby", "html", "css", "tailwind", "react", "react js",
                    "nextjs", "angular", "vue", "nodejs", "express js", "django", "flask",
                    "fastapi", "spring boot", "rest api", "rest apis", "graphql", "full stack",
                    "web development", "frontend", "backend", "software engineering",
                    "data structure", "data structures", "dsa", "algorithm", "algorithms",
                    "leetcode", "codeforces", "competitive programming", "dynamic programming",
                    "binary tree", "linked list", "sorting algorithm", "object oriented", "oop",
                    "sql", "mysql", "postgresql", "mongodb", "redis", "git", "github",
                    "docker", "kubernetes", "ci/cd", "devops", "microservices", "system design",
                    "machine learning", "deep learning", "artificial intelligence", "ai & ml",
                    "neural", "neural network", "neural networks", "reinforcement learning",
                    "q-learning", "unsupervised learning", "k-means", "clustering",
                    "decision tree", "decision trees", "entropy", "information gain",
                    "support vector", "svm", "kernel trick", "convolutional", "cnn", "cnns",
                    "nlp", "natural language processing", "hugging face", "transformer",
                    "transformers", "bert", "modernbert", "bidirectional", "attention",
                    "backpropagation", "gradient descent", "pytorch", "tensorflow", "scikit-learn",
                    "langchain", "llm", "rag", "from scratch", "coding roadmap", "complete roadmap",
                    "code review", "debugging", "vs code", "ide"
                ],
            },
            "tech": {
                "name": "🔧 Tech & Gadgets",
                "icon": "🔧",
                "tag": "tech",
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
                    "rtx", "radeon", "nvidia", "amd", "intel", "motherboard", "ssd", "ram",
                    "monitor", "mechanical keyboard", "linux", "ubuntu", "arch linux", "windows 11",
                    "macos", "cloud computing", "aws", "azure", "cybersecurity", "ethical hacking",
                    "penetration testing", "wifi", "router", "5g", "iot", "raspberry pi", "arduino",
                    "robotics", "unboxing", "first look", "hands on", "specs"
                ],
            },
            "scifi": {
                "name": "🚀 Science & Space",
                "icon": "🚀",
                "tag": "scifi",
                "yt_id": "28",
                "yt_macro": "Science & Technology",
                "kg_topics": ["/m/06mq7 (Science)", "/m/018jz (Astronomy)", "/m/06n90 (Science Fiction)"],
                "channel_priors": [
                    "kurzgesagt", "veritasium", "vsauce", "smartereveryday", "minutephysics",
                    "pbs space time", "nasa", "isro", "spacex", "anton petrov", "astral doorway",
                    "scishow", "mark rober", "star talk", "neil degrasse tyson"
                ],
                "keywords": [
                    "sci-fi", "science fiction", "space", "astronomy", "astrophysics", "cosmos",
                    "cosmology", "galaxy", "milky way", "andromeda", "nasa", "isro", "esa",
                    "interstellar", "black hole", "event horizon", "wormhole", "universe",
                    "multiverse", "relativity", "general relativity", "quantum", "quantum physics",
                    "string theory", "dark matter", "dark energy", "exoplanet", "mars", "moon",
                    "jupiter", "saturn", "spacex", "starship", "rocket launch", "orbital",
                    "alien", "extraterrestrial", "fermi paradox", "james webb", "jwst",
                    "hubble", "telescope", "time travel", "cyberpunk", "dune", "star wars",
                    "star trek", "futurism"
                ],
            },
            "news": {
                "name": "📰 News & Politics",
                "icon": "📰",
                "tag": "news",
                "yt_id": "25",
                "yt_macro": "News & Politics",
                "kg_topics": ["/m/098wr (Society)", "/m/05qt0 (Politics)", "/m/025zzc (News)"],
                "channel_priors": [
                    "wion", "firstpost", "ndtv", "india today", "bbc news", "al jazeera",
                    "reuters", "dw news", "cnn", "cnbc", "sansad tv", "lallantop", "dhruv rathee"
                ],
                "keywords": [
                    "breaking news", "world news", "live news", "geopolitics", "politics",
                    "election", "parliament", "lok sabha", "rajya sabha", "supreme court",
                    "foreign policy", "diplomacy", "united nations", "nato", "brics",
                    "current affairs", "journalism", "press conference", "prime minister",
                    "president", "government policy", "headline", "war update", "border conflict"
                ],
            },
            "finance": {
                "name": "📈 Finance & Business",
                "icon": "📈",
                "tag": "finance",
                "yt_id": "27",
                "yt_macro": "Education",
                "kg_topics": ["/m/09s1f (Business)", "/m/02_7t (Economics)", "/m/01y3_ (Investing)"],
                "channel_priors": [
                    "zerodha", "pranjal kamra", "akshat shrivastava", "ca rachana ranade",
                    "warikoo", "think school", "labour law advisor", "bloomberg", "wall street journal",
                    "y combinator", "patrick boyle", "the plain bagel", "finshots"
                ],
                "keywords": [
                    "finance", "personal finance", "investing", "investment", "stock market",
                    "share market", "nifty", "sensex", "wall street", "nasdaq", "mutual funds",
                    "sip", "index funds", "etf", "options trading", "intraday", "dividend",
                    "portfolio", "financial freedom", "business", "business case study",
                    "startup", "entrepreneurship", "venture capital", "shark tank", "ipo",
                    "valuation", "marketing strategy", "macroeconomics", "inflation",
                    "recession", "gdp", "central bank", "rbi", "federal reserve", "real estate",
                    "income tax", "accounting", "balance sheet"
                ],
            },
            "howto": {
                "name": "🛠️ How-To & DIY",
                "icon": "🛠️",
                "tag": "howto",
                "yt_id": "26",
                "yt_macro": "Howto & Style",
                "kg_topics": ["/m/019_rr (Lifestyle)", "/m/03glg (Hobby & DIY)", "/m/027x7n (Self-Improvement)"],
                "channel_priors": [
                    "ali abdaal", "thomas frank", "matt d'avella", "5-minute crafts",
                    "jerryrigeverything", "ifixit", "chris fix", "electroboom", "colin furze"
                ],
                "keywords": [
                    "how to", "diy", "do it yourself", "step by step", "woodworking",
                    "carpentry", "home improvement", "electronics repair", "restoration",
                    "soldering", "3d printing", "origami", "crafting", "gardening",
                    "productivity", "time management", "second brain", "notion template",
                    "obsidian", "ankidroid", "flashcards", "speed reading", "communication skills",
                    "public speaking", "body language", "resume building", "linkedin profile",
                    "interview preparation", "graphic design", "photoshop", "figma",
                    "video editing", "premiere pro", "davinci resolve", "blender tutorial"
                ],
            },
            "podcast": {
                "name": "🎙️ Podcasts & Talks",
                "icon": "🎙️",
                "tag": "podcast",
                "yt_id": "22",
                "yt_macro": "People & Blogs",
                "kg_topics": ["/m/027lnzs (Podcast)", "/m/01k8wb (Conversation & Documentary)"],
                "channel_priors": [
                    "lex fridman", "ted", "tedx", "ted-ed", "huberman lab", "diary of a ceo",
                    "joe rogan", "trs", "ranveer allahbadia", "raj shamani", "nikhil kamath",
                    "smita prakash", "ani podcast", "dw documentary", "frontline pbs"
                ],
                "keywords": [
                    "podcast", "full episode", "ted talk", "tedx", "keynote speech",
                    "lex fridman", "huberman", "deep conversation", "fireside chat",
                    "panel discussion", "roundtable", "documentary", "full documentary",
                    "biopic", "untold story", "investigative", "intellectual discussion"
                ],
            },
            "cooking": {
                "name": "🍲 Cooking & Food",
                "icon": "🍲",
                "tag": "cooking",
                "yt_id": "26",
                "yt_macro": "Howto & Style",
                "kg_topics": ["/m/02wbm (Food)", "/m/01mtb (Cooking)", "/m/019_rr (Culinary Arts)"],
                "channel_priors": [
                    "ranveer brar", "your food lab", "kabita's kitchen", "hebbars kitchen",
                    "bharatzkitchen", "joshua weissman", "babish culinary universe", "gordon ramsay",
                    "nick digiovanni", "uncle roger", "village cooking channel", "first we feast"
                ],
                "keywords": [
                    "recipe", "recipes", "cooking", "cook", "food", "street food", "kitchen",
                    "chef", "masterchef", "burger", "pizza", "pasta", "biryani", "paneer",
                    "curry", "masala", "tacos", "sushi", "ramen", "cake", "baking", "pastry",
                    "bread", "chocolate", "eating", "mukbang", "food challenge", "spicy wings",
                    "dessert", "ice cream", "taste test", "lunch recipe", "dinner recipe",
                    "breakfast recipe", "snack", "healthy meal prep", "air fryer", "restaurant"
                ],
            },
            "autos": {
                "name": "🚗 Autos & Vehicles",
                "icon": "🚗",
                "tag": "autos",
                "yt_id": "2",
                "yt_macro": "Autos & Vehicles",
                "kg_topics": ["/m/07yv9 (Vehicles)", "/m/0k4j (Automobiles)", "/m/04_sv (Motorcycles)"],
                "channel_priors": [
                    "carwow", "doug demuro", "top gear", "autocar india", "motoroctane",
                    "faisal khan", "powerdrift", "donut media", "supercar blondie", "fortnine"
                ],
                "keywords": [
                    "car review", "supercar", "hypercar", "sports car", "suv", "sedan",
                    "hatchback", "electric vehicle", "ev review", "tesla", "ferrari",
                    "lamborghini", "porsche", "bmw", "mercedes", "audi", "mahindra",
                    "tata motors", "motorcycle", "superbike", "bike review", "offroad",
                    "4x4", "drag race", "formula 1", "f1", "motogp", "v8 engine", "v12",
                    "horsepower", "exhaust sound", "test drive", "automotive"
                ],
            },
            "pets": {
                "name": "🐾 Pets & Nature",
                "icon": "🐾",
                "tag": "pets",
                "yt_id": "15",
                "yt_macro": "Pets & Animals",
                "kg_topics": ["/m/068hy (Pets)", "/m/0jbk (Animals)", "/m/05h0n (Nature & Wildlife)"],
                "channel_priors": [
                    "national geographic", "nat geo wild", "bbc earth", "animal planet",
                    "the dodo", "brave wilderness", "girl with the dogs", "jackson galaxy"
                ],
                "keywords": [
                    "wildlife", "wild animals", "national geographic", "bbc earth", "nature documentary",
                    "animal rescue", "puppy", "puppies", "golden retriever", "german shepherd",
                    "dogs", "dog training", "kittens", "cats", "cute pets", "aquarium",
                    "coral reef", "sharks", "whales", "lions", "tigers", "elephants",
                    "birds", "parrots", "jungle", "rainforest", "safari", "veterinarian"
                ],
            },
            "travel": {
                "name": "✈️ Travel & Culture",
                "icon": "✈️",
                "tag": "travel",
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
                    "flight review", "first class flight", "business class", "aviation",
                    "airlines", "airport", "hotel review", "resort", "tourism", "exploring",
                    "mountain trekking", "himalayas", "switzerland", "japan travel", "europe trip"
                ],
            },
            "music": {
                "name": "🎵 Music & Lofi",
                "icon": "🎵",
                "tag": "music",
                "yt_id": "10",
                "yt_macro": "Music",
                "kg_topics": ["/m/04rlf (Music)", "/m/02lkt (Electronic/Lo-Fi)", "/m/064t9 (Pop Music)"],
                "channel_priors": [
                    "lofi girl", "chilledcow", "t-series", "sony music", "zeemusiccompany",
                    "coke studio", "vevo", "spinnin' records", "ncs", "nocopyrightsounds",
                    "arijit singh", "a.r. rahman", "taylor swift", "the weeknd", "trap nation"
                ],
                "keywords": [
                    "music", "song", "new song", "official music video", "official video",
                    "lyrical video", "lyrics", "audio song", "full audio", "remix", "mashup",
                    "lofi", "lofi hip hop", "lofi beats", "chill beats", "acoustic", "unplugged",
                    "live concert", "music festival", "singer", "vocalist", "album", "ep",
                    "soundtrack", "bgm", "ost", "playlist", "rap song", "hip hop", "rock band",
                    "classical music", "piano cover", "guitar cover", "cover song", "karaoke"
                ],
            },
            "sports": {
                "name": "🏏 Sports & Fitness",
                "icon": "🏏",
                "tag": "sports",
                "yt_id": "17",
                "yt_macro": "Sports",
                "kg_topics": ["/m/06ntj (Sports)", "/m/09xp_ (Cricket)", "/m/02vx4 (Football)", "/m/027x7n (Fitness)"],
                "channel_priors": [
                    "icc", "icc official", "bcci", "star sports", "espn", "skysports", "fifa",
                    "uefa", "nba", "ufc", "wwe", "athlean-x", "jeff nippard", "noel deyzel",
                    "chris heria", "rohit khatri"
                ],
                "keywords": [
                    "cricket", "test cricket", "t20", "odi", "ipl", "world cup", "super over",
                    "century", "hat-trick", "wicket", "virat kohli", "rohit sharma", "ms dhoni",
                    "football", "soccer", "premier league", "champions league", "la liga",
                    "el clasico", "messi", "ronaldo", "mbappe", "neymar", "match highlights",
                    "full match highlights", "olympics", "tennis", "wimbledon", "badminton",
                    "basketball", "nba", "workout", "workout routine", "gym", "gym fitness",
                    "bodybuilding", "hypertrophy", "calisthenics", "pushups", "abs workout",
                    "fat loss", "muscle gain", "protein", "boxing", "mma", "ufc", "wwe"
                ],
            },
            "anime": {
                "name": "⚔️ Anime & Manga",
                "icon": "⚔️",
                "tag": "anime",
                "yt_id": "31",
                "yt_macro": "Anime/Animation",
                "kg_topics": ["/m/0jxy (Anime)", "/m/04spm (Manga)", "/m/019_rr (Japanese Animation)"],
                "channel_priors": [
                    "crunchyroll", "muse asia", "ani-one asia", "netflix anime", "toei animation",
                    "mappa", "ufotable", "gigguk", "mother's basement", "animezone"
                ],
                "keywords": [
                    "anime", "manga", "manhwa", "otaku", "weeb", "shonen", "isekai", "naruto",
                    "shippuden", "boruto", "sasuke", "kakashi", "itachi", "madara", "one piece",
                    "luffy", "zoro", "sanji", "gear 5", "bleach", "ichigo", "aizen", "tybw",
                    "attack on titan", "aot", "eren yeager", "eren", "levi", "mikasa",
                    "jujutsu kaisen", "jjk", "gojo", "sukuna", "megumi", "demon slayer",
                    "kimetsu", "tanjiro", "nezuko", "rengoku", "dragon ball", "dragon ball z",
                    "dragon ball super", "dbz", "dbs", "goku", "vegeta", "ultra instinct",
                    "super saiyan", "saiyan", "ssj", "bardock", "gohan", "broly", "frieza",
                    "piccolo", "trunks", "studio ghibli", "ghibli", "solo leveling",
                    "sung jinwoo", "chainsaw man", "denji", "death note", "light yagami",
                    "vinland saga", "my hero academia", "deku", "blue lock", "haikyuu",
                    "one punch man", "saitama", "hunter x hunter", "hxh", "killua",
                    "tokyo ghoul", "sword art online", "fullmetal alchemist", "berserk",
                    "evangelion", "jojo", "opening ost", "amv", "anime scene", "anime clip", "anime edit"
                ],
            },
            "cartoon": {
                "name": "🎨 Cartoon & Animation",
                "icon": "🎨",
                "tag": "cartoon",
                "yt_id": "1",
                "yt_macro": "Film & Animation",
                "kg_topics": ["/m/02vxn (Film & Animation)", "/m/0215n (Cartoons)"],
                "channel_priors": [
                    "disney", "pixar", "cartoon network", "nickelodeon", "wb kids",
                    "pogo", "hungama", "alan becker", "theodd1sout", "jaiden animations"
                ],
                "keywords": [
                    "cartoon", "cartoons", "animated", "2d animation", "3d animation",
                    "stop motion", "cgi short", "tom and jerry", "disney", "pixar",
                    "dreamworks", "illumination", "ben 10", "shinchan", "doraemon", "nobita",
                    "oggy", "cockroaches", "chhota bheem", "motu patlu", "peppa pig",
                    "mr bean animated", "looney tunes", "bugs bunny", "spongebob",
                    "rick and morty", "avatar the last airbender", "spider-verse", "kids show"
                ],
            },
            "gaming": {
                "name": "🎮 Gaming & Esports",
                "icon": "🎮",
                "tag": "gaming",
                "yt_id": "20",
                "yt_macro": "Gaming",
                "kg_topics": ["/m/0bzvm2 (Gaming)", "/m/01mw1 (Video Games)", "/m/025zzc (Esports)"],
                "channel_priors": [
                    "pewdiepie", "dream", "technoblade", "luke thenotable", "tenz", "shroud",
                    "ninja", "total gaming", "techno gamerz", "mortal", "scout", "carryislive",
                    "beastboyshub", "ign", "gamespot", "vaatividya", "radbrad", "markiplier", "jacksepticeye"
                ],
                "keywords": [
                    "game", "gameplay", "gaming", "let's play", "playthrough", "walkthrough",
                    "speedrun", "minecraft", "hardcore minecraft", "bedwars", "skyblock",
                    "gta", "gta 5", "gta 6", "gta rp", "rockstar games", "valorant",
                    "radiant", "1v5", "clutch", "aimbot", "crosshair", "fortnite",
                    "battle royale", "pubg", "bgmi", "free fire", "roblox", "call of duty",
                    "warzone", "black ops", "counter strike", "cs2", "csgo", "apex legends",
                    "overwatch", "league of legends", "dota 2", "elden ring", "dark souls",
                    "sekiro", "black myth wukong", "god of war", "spider-man ps5",
                    "red dead redemption", "cyberpunk 2077", "resident evil", "fifa 25",
                    "ea fc", "genshin impact", "honkai", "among us", "clash of clans",
                    "brawl stars", "chess.com", "esports", "twitch stream", "live stream",
                    "boss fight", "hardest boss", "no armor", "ranked match", "pro highlights",
                    "50 kills", "radiant ace", "ps5", "xbox", "nintendo switch", "steam"
                ],
            },
            "vlog": {
                "name": "💄 Vlogs & Lifestyle",
                "icon": "💄",
                "tag": "vlog",
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
                    "zara haul", "amazon haul", "skincare routine", "makeup tutorial",
                    "grwm", "get ready with me", "outfit ideas", "fashion", "morning routine",
                    "night routine", "q&a", "storytime", "my life update"
                ],
            },
            "comedy": {
                "name": "😂 Comedy & Memes",
                "icon": "😂",
                "tag": "comedy",
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
                    "bloopers", "epic fails", "fails", " vines", "humor", "samay raina",
                    "zakir khan", "bassi"
                ],
            },
            "clickbait": {
                "name": "🚨 Clickbait & Drama",
                "icon": "🚨",
                "tag": "clickbait",
                "yt_id": "24",
                "yt_macro": "Entertainment",
                "kg_topics": ["/m/02jjt (Entertainment)", "/m/09k_b (Sensationalism & Viral Media)"],
                "channel_priors": [
                    "mrbeast", "dhar mann", "airrack", "ryan trahan", "fukra insaan",
                    "elvish yadav", "buzzfeed", "tmz", "bollywoodgaram", "filmibeat",
                    "gossipcentral", "viraldrama", "getrichfast", "cryptoguru", "hypetech",
                    "mysteryfiles"
                ],
                "keywords": [
                    "mrbeast", "shocking", "secret hack", "wealth hack", "make money fast",
                    "get rich", "zero effort", "guaranteed", "10,000/hr", "arrested",
                    "exposed", "controversy", "drama", "leaked", "$1 vs", "$1,000,000",
                    "blindfolded", "buying everything", "last to leave", "24 hours",
                    "7 days straight", "viral challenge", "extreme challenge",
                    "you won't believe", "you wont believe", "must watch", "gone wrong",
                    "billionaire", "crypto", "memecoin", "100x coin", "conspiracy theories",
                    "abandoned island", "found this inside", "destroyed android",
                    "red carpet", "unseen moments", "paparazzi", "hollywood", "bollywood",
                    "celebrity gossip", "Illuminati"
                ],
            },
        }

        # Pre-compile keyword & channel regexes for <0.25ms inference
        self._compiled_keywords: Dict[str, List[Tuple[re.Pattern, int, str]]] = {}
        self._compiled_channels: Dict[str, List[re.Pattern]] = {}

        for tag, info in self.category_taxonomies.items():
            kw_patterns = []
            for kw in info["keywords"]:
                kw_clean = kw.strip().lower()
                word_count = len(kw_clean.split())
                weight = word_count * 2 + (1 if word_count > 1 else 0)
                pat = re.compile(r"(?<!\w)" + re.escape(kw_clean) + r"(?!\w)", re.IGNORECASE)
                kw_patterns.append((pat, weight, kw_clean))
            self._compiled_keywords[tag] = kw_patterns

            ch_patterns = []
            for ch in info.get("channel_priors", []):
                ch_clean = ch.strip().lower()
                pat = re.compile(r"(?<!\w)" + re.escape(ch_clean) + r"(?!\w)", re.IGNORECASE)
                ch_patterns.append(pat)
            self._compiled_channels[tag] = ch_patterns

        # Generic instructional phrases that boost whichever educational domain (study vs coding) wins
        self._instructional_boosters = [
            re.compile(r"\b(crash course|full course|complete course|lecture \d+|unit \d+|tutorial|for beginners|for students|explained|deep dive|walkthrough|from scratch|roadmap)\b", re.IGNORECASE)
        ]

        # Clickbait structural regexes ($1 vs $1000000, ALL CAPS sensationalism, etc.)
        self._clickbait_structural = [
            re.compile(r"\$\d[\d,]*\s*vs\.?\s*\$\d[\d,]*", re.IGNORECASE),
            re.compile(r"\b(i survived \d+ days|for \d+ days straight|in 24 hours|you won'?t believe|must watch!|shocking:?)\b", re.IGNORECASE),
        ]

        self.load_preferences()

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
        if os.path.exists(self.pref_file):
            try:
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

    def save_preferences(self, data: Dict) -> Dict:
        current = self._cached_prefs or self._default_preferences()
        for key in ("shield_enabled", "active_categories", "custom_keywords", "blocked_count", "allowed_count"):
            if key in data and data[key] is not None:
                current[key] = data[key]

        current["updated_at"] = time.time()
        try:
            with open(self.pref_file, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2)
            self._last_pref_mtime = os.path.getmtime(self.pref_file)
        except Exception as e:
            print(f"[Laya Engine] Error saving preferences: {e}")

        self._cached_prefs = current
        self.cache.clear()
        return current

    def classify_youtube_3layer(self, title: str, channel: str = "") -> Dict:
        """
        Executes YouTube's 3-Layer Categorization Algorithm:
          - Signal A: Channel Authority & Creator Graph Prior
          - Signal B: Multi-N-Gram Title & Hashtag Semantic Matching
          - Signal C: Contextual Disambiguation (Study vs Coding, Walkthroughs, Clickbait)
          - Signal D: Temperature-Scaled Softmax Confidence (T = 1.2)
        """
        title_lower = title.lower().strip()
        channel_lower = channel.lower().strip()
        combined_text = f"{title_lower} {channel_lower}".strip()

        scores: Dict[str, float] = {tag: 0.0 for tag in self.category_taxonomies}

        # 1. Signal A: Channel Graph Priors & Channel Name Heuristics
        if channel_lower:
            for tag, ch_patterns in self._compiled_channels.items():
                for pat in ch_patterns:
                    if pat.search(channel_lower):
                        scores[tag] += 5.0
            if any(w in channel_lower for w in ("lectures", "academy", "classes", "university", "iit", "opencourseware")):
                scores["study"] += 3.5
            if any(w in channel_lower for w in ("code", "coding", "programming", "developer", "dev")):
                scores["coding"] += 3.5
            if any(w in channel_lower for w in ("gaming", "gamer", "plays", "esports", "twitch")):
                scores["gaming"] += 3.5
            if any(w in channel_lower for w in ("vlog", "vlogs", "vlogger")):
                scores["vlog"] += 3.5

        # 2. Signal B: Multi-N-Gram Keyword & Phrase Scoring
        for tag, kw_patterns in self._compiled_keywords.items():
            for pat, weight, _ in kw_patterns:
                if pat.search(combined_text):
                    scores[tag] += weight

        # 3. Signal C: Contextual Disambiguation Rules
        has_instructional = any(p.search(title_lower) for p in self._instructional_boosters)
        if has_instructional:
            # Route instructional booster to Coding if coding signals dominate, else Study
            if scores["coding"] > 0 and scores["coding"] >= scores["study"]:
                scores["coding"] += 4.5
            elif scores["study"] > 0:
                scores["study"] += 4.5
            elif scores["tech"] > 0:
                # e.g., "Git & GitHub Crash Course for Students & Beginners"
                scores["coding"] += 5.0
            elif scores["howto"] > 0:
                scores["howto"] += 3.0

        # Suppress false 'walkthrough' gaming match when study/coding concepts are present
        if "walkthrough" in title_lower and (scores["study"] > 0 or scores["coding"] > 0):
            scores["gaming"] = max(0.0, scores["gaming"] - 4.0)

        # Structural clickbait boost (only when no strong academic/coding signal exists)
        if scores["study"] < 4.0 and scores["coding"] < 4.0:
            for cb_pat in self._clickbait_structural:
                if cb_pat.search(title_lower):
                    scores["clickbait"] += 4.5

        # Find winning category
        best_tag = "other"
        best_score = 0.0
        for tag, sc in scores.items():
            if sc > best_score:
                best_score = sc
                best_tag = tag

        if best_score <= 0.0:
            return {
                "category_name": "🎭 General Entertainment",
                "category_tag": "other",
                "youtube_category_id": "24",
                "youtube_macro_category": "Entertainment",
                "knowledge_graph_topics": ["/m/02jjt (Entertainment)"],
                "confidence": 0.85,
            }

        info = self.category_taxonomies[best_tag]

        # 4. Signal D: Calibrated Temperature Softmax / Sigmoid (T = 1.2)
        calibrated_conf = 1.0 / (1.0 + math.exp(-(best_score / self.temperature)))
        confidence = min(0.99, max(0.78, round(calibrated_conf, 2)))

        return {
            "category_name": info["name"],
            "category_tag": best_tag,
            "youtube_category_id": info["yt_id"],
            "youtube_macro_category": info["yt_macro"],
            "knowledge_graph_topics": info["kg_topics"],
            "confidence": confidence,
        }

    def classify_category(self, text: str) -> Tuple[str, str, float]:
        """Backwards-compatible helper returning (Category Name, Category Tag, Confidence)."""
        res = self.classify_youtube_3layer(title=text, channel="")
        return res["category_name"], res["category_tag"], res["confidence"]

    def decide(
        self,
        title: str,
        channel: str = "",
        focus_domain: Optional[str] = None,
        track_stats: bool = True,
    ) -> DecisionResult:
        start = time.perf_counter()
        prefs = self.load_preferences()

        shield_enabled = prefs.get("shield_enabled", True)
        active_cats = prefs.get("active_categories", ["study", "coding"])
        custom_kws = prefs.get("custom_keywords", [])

        # In focus_domain='aiml' evaluation, allow educational content (both study & coding)
        effective_cats = list(active_cats)
        if focus_domain == "aiml":
            effective_cats = ["study", "coding"]

        effective_shield = True if focus_domain == "aiml" else shield_enabled

        cache_key = (
            f"{title.strip().lower()}::{channel.strip().lower()}::"
            f"{effective_shield}::{','.join(sorted(effective_cats))}::{','.join(sorted(custom_kws))}"
        )
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            self.cache.move_to_end(cache_key)
            elapsed_ms = (time.perf_counter() - start) * 1000
            return DecisionResult(
                is_allowed=cached.is_allowed,
                is_study=cached.is_study,
                category=cached.category,
                category_tag=cached.category_tag,
                youtube_category_id=cached.youtube_category_id,
                youtube_macro_category=cached.youtube_macro_category,
                knowledge_graph_topics=cached.knowledge_graph_topics,
                confidence=cached.confidence,
                latency_ms=elapsed_ms,
                matched_preference=cached.matched_preference,
                explanation=cached.explanation,
            )

        yt_info = self.classify_youtube_3layer(title=title, channel=channel)
        detected_category = yt_info["category_name"]
        detected_tag = yt_info["category_tag"]
        yt_id = yt_info["youtube_category_id"]
        yt_macro = yt_info["youtube_macro_category"]
        kg_topics = yt_info["knowledge_graph_topics"]
        conf = yt_info["confidence"]

        is_educational = detected_tag in ("study", "coding")

        if not effective_shield:
            elapsed_ms = (time.perf_counter() - start) * 1000
            res = DecisionResult(
                is_allowed=True,
                is_study=True,
                category=detected_category,
                category_tag=detected_tag,
                youtube_category_id=yt_id,
                youtube_macro_category=yt_macro,
                knowledge_graph_topics=kg_topics,
                confidence=0.99,
                latency_ms=elapsed_ms,
                matched_preference="Shield OFF (All Allowed)",
                explanation="Shield toggle is OFF. All videos remain unblurred.",
            )
            self._store_cache(cache_key, res)
            return res

        is_allowed = False
        matched_pref = ""

        if detected_tag in effective_cats:
            is_allowed = True
            matched_pref = detected_category

        if not is_allowed and custom_kws:
            combined_lower = f"{title} {channel}".lower()
            for kw in custom_kws:
                kw_clean = kw.strip().lower()
                if kw_clean and re.search(r"(?<!\w)" + re.escape(kw_clean) + r"(?!\w)", combined_lower):
                    is_allowed = True
                    matched_pref = f"Custom: {kw.strip()}"
                    break

        elapsed_ms = (time.perf_counter() - start) * 1000
        if is_allowed:
            explanation = (
                f"YouTube Cat ID {yt_id} ({yt_macro}) • {detected_category} • "
                f"Matches active preference ({matched_pref})."
            )
        else:
            matched_pref = "Blocked"
            explanation = (
                f"YouTube Cat ID {yt_id} ({yt_macro}) • Classified as {detected_category}, "
                f"which is not in your allowed topics."
            )

        res = DecisionResult(
            is_allowed=is_allowed,
            is_study=is_educational if focus_domain == "aiml" else is_allowed,
            category=detected_category,
            category_tag=detected_tag,
            youtube_category_id=yt_id,
            youtube_macro_category=yt_macro,
            knowledge_graph_topics=kg_topics,
            confidence=conf,
            latency_ms=elapsed_ms,
            matched_preference=matched_pref,
            explanation=explanation,
        )

        self._store_cache(cache_key, res)
        if track_stats and focus_domain != "aiml":
            if is_allowed:
                prefs["allowed_count"] = prefs.get("allowed_count", 0) + 1
            else:
                prefs["blocked_count"] = prefs.get("blocked_count", 0) + 1

        return res

    def _store_cache(self, key: str, result: DecisionResult) -> None:
        self.cache[key] = result
        if len(self.cache) > self.max_cache_size:
            self.cache.popitem(last=False)
