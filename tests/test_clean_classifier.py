"""
Standalone verification of all 20 YouTube Categories in LayaDecisionEngine
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
from decision_engine import LayaDecisionEngine


def test_all_20_categories():
    engine = LayaDecisionEngine()
    engine.save_preferences({
        "shield_enabled": True,
        "active_categories": ["study", "coding"],
        "custom_keywords": [],
    })

    samples = [
        ("Linear Algebra Eigenvalues & Gate Exam Lecture", "3Blue1Brown", "study"),
        ("Python FastAPI & React Full Stack Coding Tutorial", "freeCodeCamp", "coding"),
        ("RTX 5090 Gaming PC Build & Linux Hardware Review", "Linus Tech Tips", "tech"),
        ("James Webb Telescope Black Hole & Cosmos Astronomy", "Veritasium", "scifi"),
        ("Breaking News: Parliament Foreign Policy & Geopolitics", "WION", "news"),
        ("Stock Market Investing, Mutual Funds & Macroeconomics", "Zerodha", "finance"),
        ("How To Build a Second Brain in Notion & DIY Repair", "Ali Abdaal", "howto"),
        ("Lex Fridman Podcast Full Episode: Deep Conversation", "Lex Fridman", "podcast"),
        ("Chicken Biryani Recipe & Street Food MasterChef", "Ranveer Brar", "cooking"),
        ("Ferrari Supercar vs Tesla EV Drag Race Car Review", "carwow", "autos"),
        ("National Geographic Wildlife Safari & Cute Puppies", "BBC Earth", "pets"),
        ("Solo Travel Guide Across Japan & Flight Review", "Drew Binsky", "travel"),
        ("Lofi Hip Hop Beats Playlist & Official Music Video", "Lofi Girl", "music"),
        ("Cricket World Cup Super Over Match Highlights", "ICC Official", "sports"),
        ("Jujutsu Kaisen Gojo vs Sukuna & Attack on Titan Anime", "Crunchyroll", "anime"),
        ("Tom and Jerry Classic Cartoon & Pixar 3D Animation", "WB Kids", "cartoon"),
        ("INSANE 1v5 Clutch in Valorant Ranked Gameplay", "TenZ", "gaming"),
        ("Day in My Life Daily Vlog & Minimalist Room Tour", "Flying Beast", "vlog"),
        ("Stand-Up Comedy Special & Prank Calling Strangers", "Samay Raina", "comedy"),
        ("$1 vs $1,000,000 Hotel Room! Shocking Wealth Hack", "MrBeast", "clickbait"),
    ]

    print(f"{'STATUS':<10} | {'YT ID':<7} | {'TAG':<10} | {'TITLE'}")
    print("-" * 88)
    for title, channel, expected_tag in samples:
        res = engine.decide(title=title, channel=channel, track_stats=False)
        status = "ALLOWED" if res.is_allowed else "BLURRED"
        print(f"{status:<10} | ID {res.youtube_category_id:<4} | {res.category_tag:<10} | {title}")
        assert res.category_tag == expected_tag, f"Expected {expected_tag}, got {res.category_tag} for '{title}'"

    print("\nALL 20 YOUTUBE CATEGORIES VERIFIED PERFECTLY!")


if __name__ == "__main__":
    test_all_20_categories()
