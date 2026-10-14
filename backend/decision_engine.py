"""
StudyShield — Laya Decision Engine
Supports fine-grained category detection:
Cooking, Cartoon, Anime, Gaming, Education, Sci-Fi, Technology, Music, Vlog, Sports, Comedy, Clickbait.
"""

import time
import os
import re
import json
from typing import Dict, Any, List
import numpy as np

class DecisionResult:
    def __init__(self, is_allowed: bool, category: str, confidence: float, latency_ms: float, matched_preference: str = "", explanation: str = ""):
        self.is_allowed = is_allowed
        self.is_study = is_allowed
        self.category = category
        self.confidence = round(confidence, 4)
        self.latency_ms = round(latency_ms, 2)
        self.matched_preference = matched_preference
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_allowed": self.is_allowed,
            "is_study": self.is_allowed,
            "category": self.category,
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
            "matched_preference": self.matched_preference,
            "explanation": self.explanation
        }

class LayaDecisionEngine:
    def __init__(self, model_dir: str = "./backend/models/laya", threshold: float = 0.50):
        self.model_dir = model_dir
        self.threshold = threshold
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.pref_file = os.path.join(self.model_dir, "active_preference.json")
        
        # Fine-Grained Topic Classifiers
        self.category_taxonomies = {
            "Cooking & Food": {
                "keywords": {
                    "recipe", "cooking", "cook", "food", "street food", "kitchen", "chef",
                    "burger", "pizza", "biryani", "cake", "baking", "taste test", "eating",
                    "mukbang", "restaurant", "delicious", "breakfast", "dinner", "lunch", "snack"
                },
                "icon": "🍲",
                "tag": "cooking"
            },
            "Cartoon & Animation": {
                "keywords": {
                    "cartoon", "animated", "animation", "tom and jerry", "disney", "pixar",
                    "ben 10", "shinchan", "doraemon", "oggy", "chhota bheem", "peppa pig",
                    "mr bean", "bugs bunny", "looney tunes", "sponge bob", "cartoons", "kids show"
                },
                "icon": "🎬",
                "tag": "cartoon"
            },
            "Anime & Manga": {
                "keywords": {
                    "anime", "manga", "naruto", "one piece", "bleach", "attack on titan", "aot",
                    "jujutsu kaisen", "jjk", "demon slayer", "dragon ball", "dbz", "studio ghibli",
                    "crunchyroll", "otaku", "luffy", "goku", "gojo", "chainsaw man", "death note",
                    "solo leveling", "vinland saga", "amv", "opening ost", "my hero academia"
                },
                "icon": "🎌",
                "tag": "anime"
            },
            "Gaming & Esports": {
                "keywords": {
                    "game", "gameplay", "gaming", "minecraft", "gta", "valorant", "fortnite",
                    "pubg", "bgmi", "roblox", "call of duty", "cod", "playthrough", "walkthrough",
                    "stream", "twitch", "esports", "boss fight", "ace", "ranked", "hardcore survival"
                },
                "icon": "🎮",
                "tag": "gaming"
            },
            "Study & Education": {
                "keywords": {
                    "lecture", "course", "tutorial", "algorithm", "python", "neural", "calculus",
                    "linear algebra", "discrete", "operating system", "data structure", "dsa",
                    "machine learning", "deep learning", "ai", "engineering", "gate", "exam",
                    "syllabus", "semester", "diploma", "coding", "fastapi", "react", "programming",
                    "computer network", "dbms", "sql", "math", "physics", "electronics", "cnn",
                    "nlp", "transformer", "bert", "backpropagation", "gradient descent", "svm",
                    "freecodecamp", "neso academy", "gate smashers", "love babbar", "campusx",
                    "history", "biology", "chemistry", "notes", "upsc", "study with me", "class 12"
                },
                "icon": "📚",
                "tag": "study"
            },
            "Science Fiction & Space": {
                "keywords": {
                    "sci-fi", "science fiction", "space", "astronomy", "cosmos", "galaxy", "nasa",
                    "james webb", "interstellar", "black hole", "universe", "relativity", "quantum",
                    "mars", "spacex", "alien", "dune", "cyberpunk", "star wars", "star trek", "astrophysics",
                    "time travel", "multiverse", "kurzgesagt", "veritasium"
                },
                "icon": "🚀",
                "tag": "scifi"
            },
            "Technology & Software": {
                "keywords": {
                    "technology", "software", "developer", "linux", "git", "github", "docker",
                    "kubernetes", "cloud", "aws", "cybersecurity", "hardware", "cpu", "gpu",
                    "nvidia", "amd", "backend", "frontend", "system design", "devops", "code review"
                },
                "icon": "💻",
                "tag": "tech"
            },
            "Music & Songs": {
                "keywords": {
                    "music", "song", "official video", "lyrics", "audio", "remix", "lofi",
                    "acoustic", "concert", "singer", "album", "soundtrack", "instrumental",
                    "beats", "rap", "hip hop", "cover song", "playlist"
                },
                "icon": "🎵",
                "tag": "music"
            },
            "Vlog & Daily Life": {
                "keywords": {
                    "vlog", "daily vlog", "day in my life", "travel vlog", "room tour", "house tour",
                    "flying beast", "sourav joshi", "family vlog", "lifestyle", "shopping haul",
                    "college life vlog", "morning routine", "night routine"
                },
                "icon": "💄",
                "tag": "vlog"
            },
            "Comedy & Pranks": {
                "keywords": {
                    "prank", "comedy", "funny", "stand-up", "stand up comedy", "joke", "roast",
                    "meme", "memes", "try not to laugh", "samay raina", "bassi", "zakir khan",
                    "cringe", "reaction video", "parody"
                },
                "icon": "😂",
                "tag": "comedy"
            },
            "Sports & Fitness": {
                "keywords": {
                    "cricket", "football", "highlights", "world cup", "ipl", "match", "gym",
                    "workout", "fitness", "bodybuilding", "marathon", "boxing", "ufc", "wwe",
                    "ronaldo", "messi", "virat kohli", "super over"
                },
                "icon": "🏏",
                "tag": "sports"
            },
            "Sensational & Clickbait": {
                "keywords": {
                    "mrbeast", "shocking", "you won't believe", "secret hack", "wealth hack",
                    "make money fast", "crypto", "arrested", "exposed", "billionaire",
                    "$1 vs", "buying everything", "blindfolded", "must watch"
                },
                "icon": "🚨",
                "tag": "clickbait"
            }
        }
        
        self.load_preferences()

    def load_preferences(self) -> Dict[str, Any]:
        default_pref = {
            "shield_enabled": True,
            "active_categories": ["study"], # allowed tags: study, scifi, anime, cooking, cartoon, tech, etc.
            "custom_keywords": [],
            "blocked_count": 0,
            "allowed_count": 0
        }
        if os.path.exists(self.pref_file):
            try:
                with open(self.pref_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        self.save_preferences(default_pref)
        return default_pref

    def save_preferences(self, data: Dict[str, Any]):
        try:
            data["updated_at"] = time.time()
            with open(self.pref_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self.cache.clear()
        except Exception as e:
            print(f"[Laya Engine] Error saving preferences: {e}")

    def classify_category(self, text: str) -> tuple[str, str, float]:
        """
        Classifies the exact fine-grained category from text using word-boundary recognition.
        Returns: (Category Name, Category Tag, Confidence Score)
        """
        text_lower = text.lower()
        best_cat = "Distraction / Entertainment"
        best_tag = "other"
        highest_score = 0.0

        for cat_name, cat_info in self.category_taxonomies.items():
            score = 0.0
            for kw in cat_info["keywords"]:
                # Exact word-boundary match prevents substring false positives (e.g. 'in' in 'engineering')
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, text_lower):
                    score += len(kw.split()) * 2.0

            if score > highest_score:
                highest_score = score
                best_cat = f"{cat_info['icon']} {cat_name}"
                best_tag = cat_info["tag"]

        conf = min(0.99, max(0.65, 0.5 + (highest_score * 0.12))) if highest_score > 0 else 0.85
        return best_cat, best_tag, conf

    def decide(self, title: str, channel: str = "", focus_domain: str = "") -> DecisionResult:
        start = time.perf_counter()
        prefs = self.load_preferences()
        
        # If shield is OFF, allow everything
        if not prefs.get("shield_enabled", True):
            elapsed_ms = (time.perf_counter() - start) * 1000
            cat_name, _, conf = self.classify_category(f"{title} {channel}")
            return DecisionResult(
                is_allowed=True,
                category=cat_name,
                confidence=conf,
                latency_ms=elapsed_ms,
                matched_preference="Shield OFF (All Allowed)",
                explanation="Shield toggle is OFF. All videos remain unblurred."
            )

        text = f"{title.lower()} {channel.lower()}"
        active_cats = prefs.get("active_categories", ["study"])
        custom_kws = [kw.lower().strip() for kw in prefs.get("custom_keywords", []) if kw.strip()]
        
        # 1. Detect exact category
        detected_category, detected_tag, conf = self.classify_category(text)

        # 2. Check if detected category matches user's active preferences
        is_allowed = False
        matched_pref = ""

        if detected_tag in active_cats:
            is_allowed = True
            matched_pref = detected_category
        
        # 3. Check custom keywords with word-boundary match
        if not is_allowed:
            for kw in custom_kws:
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, text):
                    is_allowed = True
                    matched_pref = f"Custom: {kw.title()}"
                    break

        elapsed_ms = (time.perf_counter() - start) * 1000

        if is_allowed:
            explanation = f"Matches your active preference ({matched_pref}). Video remains clear."
            prefs["allowed_count"] = prefs.get("allowed_count", 0) + 1
        else:
            explanation = f"Classified as {detected_category}, which is not in your allowed preferences."
            prefs["blocked_count"] = prefs.get("blocked_count", 0) + 1

        self.save_preferences(prefs)

        return DecisionResult(
            is_allowed=is_allowed,
            category=detected_category,
            confidence=conf,
            latency_ms=elapsed_ms,
            matched_preference=matched_pref if is_allowed else "Blocked",
            explanation=explanation
        )
