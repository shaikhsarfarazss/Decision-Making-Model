"""
Verification test for multi-preference profiles and toggle switch in StudyShield
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
from decision_engine import LayaDecisionEngine

def run_tests():
    engine = LayaDecisionEngine()

    print("\n--- TEST CASE 1: Shield ON with Study + Sci-Fi + Anime ---")
    engine.save_preferences({
        "shield_enabled": True,
        "active_categories": ["study", "scifi", "anime"],
        "custom_keywords": ["cyberpunk"]
    })

    anime_res = engine.decide("Attack on Titan Season 4 Episode 12 Discussion", "AnimeZone")
    print(f"1. Anime Video: is_allowed={anime_res.is_allowed} ({anime_res.category.encode('ascii', 'ignore').decode()}) -> Expected: True")
    assert anime_res.is_allowed is True

    scifi_res = engine.decide("Interstellar Black Hole Physics Explained by Kip Thorne", "ScienceDaily")
    print(f"2. Sci-Fi Video: is_allowed={scifi_res.is_allowed} ({scifi_res.category.encode('ascii', 'ignore').decode()}) -> Expected: True")
    assert scifi_res.is_allowed is True

    study_res = engine.decide("Machine Learning Algorithms Unit 2 Lecture", "CollegeProf")
    print(f"3. Study Video:  is_allowed={study_res.is_allowed} ({study_res.category.encode('ascii', 'ignore').decode()}) -> Expected: True")
    assert study_res.is_allowed is True

    custom_res = engine.decide("Cyberpunk City Night Drive Aesthetic", "MusicLover")
    print(f"4. Custom Video: is_allowed={custom_res.is_allowed} ({custom_res.category.encode('ascii', 'ignore').decode()}) -> Expected: True")
    assert custom_res.is_allowed is True

    distract_res = engine.decide("MrBeast $1 vs $1000000 Hotel Room Challenge", "MrBeast")
    print(f"5. Vlogger Video: is_allowed={distract_res.is_allowed} ({distract_res.category.encode('ascii', 'ignore').decode()}) -> Expected: False (BLURRED)")
    assert distract_res.is_allowed is False

    game_res = engine.decide("Minecraft But Diamonds Are Everywhere", "GamerBoy")
    print(f"6. Gaming Video:  is_allowed={game_res.is_allowed} ({game_res.category.encode('ascii', 'ignore').decode()}) -> Expected: False (BLURRED)")
    assert game_res.is_allowed is False

    print("\n--- TEST CASE 2: Toggle Shield OFF (User wants normal browsing) ---")
    engine.save_preferences({
        "shield_enabled": False,
        "active_categories": ["study"]
    })

    off_res = engine.decide("Minecraft But Diamonds Are Everywhere", "GamerBoy")
    print(f"7. Gaming with Shield OFF: is_allowed={off_res.is_allowed} ({off_res.category.encode('ascii', 'ignore').decode()}) -> Expected: True (Unblurred)")
    assert off_res.is_allowed is True

    print("\nALL MULTI-PREFERENCE AND TOGGLE TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    run_tests()
