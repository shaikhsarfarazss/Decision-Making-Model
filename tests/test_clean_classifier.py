import re

def test_classifier():
    categories = {
        "study": {
            "name": "📚 Study & Education",
            "keywords": [
                "lecture", "course", "tutorial", "algorithm", "algorithms", "python", "neural",
                "calculus", "linear algebra", "discrete", "operating system", "data structure",
                "dsa", "machine learning", "deep learning", "artificial intelligence", "engineering",
                "gate", "exam", "exams", "syllabus", "semester", "diploma", "coding", "fastapi",
                "react", "programming", "computer network", "dbms", "sql", "math", "mathematics",
                "physics", "electronics", "cnn", "nlp", "transformer", "backpropagation",
                "gradient descent", "svm", "freecodecamp", "neso academy", "gate smashers",
                "love babbar", "campusx", "history", "biology", "chemistry", "notes", "upsc",
                "study with me", "class 12", "neet", "jee", "learn", "how to code", "beginner tutorial"
            ]
        },
        "gaming": {
            "name": "🎮 Gaming & Esports",
            "keywords": [
                "game", "gameplay", "gaming", "minecraft", "gta", "valorant", "fortnite",
                "pubg", "bgmi", "roblox", "call of duty", "cod", "playthrough", "walkthrough",
                "stream", "twitch", "esports", "boss fight", "clutch", "ranked", "1v5", "ace"
            ]
        },
        "comedy": {
            "name": "😂 Comedy & Pranks",
            "keywords": [
                "prank", "comedy", "funny", "stand-up", "joke", "roast", "meme", "memes",
                "try not to laugh", "fails", "humor", "lol", "cringe", "reaction", "parody"
            ]
        },
        "clickbait": {
            "name": "🚨 Clickbait & Distraction",
            "keywords": [
                "mrbeast", "shocking", "you wont believe", "you won't believe", "secret hack",
                "wealth hack", "make money fast", "crypto", "arrested", "exposed", "billionaire",
                "$1 vs", "buying everything", "blindfolded", "viral challenge"
            ]
        }
    }

    test_titles = [
        "INSANE 1v5 Clutch in Valorant Ranked! #shorts",
        "Funniest Cat Fails of the Week 😂 #shorts #funny",
        "Python One-Liner Every Developer Must Know #coding #shorts",
        "MrBeast gave me 10000 dollars #shorts",
        "Dancing to viral sound in public prank",
        "Fast Derivative & Calculus Shortcut for Engineering Exams #shorts",
        "I showed this to my mom and she cried 😭 #shorts",
        "How backpropagation works in Deep Neural Networks",
        "Bro thought he was him 💀 #shorts #relatable"
    ]

    for title in test_titles:
        text = title.lower()
        best_cat = "Distraction / Entertainment"
        best_tag = "other"
        max_score = 0

        for tag, info in categories.items():
            score = 0
            for kw in info["keywords"]:
                # Use word boundary matching for clean recognition
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, text):
                    score += len(kw.split()) * 2 # multi-word keywords get higher weight
            if score > max_score:
                max_score = score
                best_cat = info["name"]
                best_tag = tag

        is_allowed = (best_tag == "study")
        label = "ALLOWED [OK]" if is_allowed else "BLURRED [BLOCK]"
        print(f"[{label}] ({best_cat.encode('ascii', 'ignore').decode()}) -> {title.encode('ascii', 'ignore').decode()}")

if __name__ == "__main__":
    test_classifier()
