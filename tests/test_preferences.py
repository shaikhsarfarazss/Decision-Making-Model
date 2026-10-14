"""
Verification test for 20-Category YouTube 3-Layer Classifier (Study vs. Coding separation)
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
from decision_engine import LayaDecisionEngine


def run_tests():
    engine = LayaDecisionEngine()

    print("\n--- TEST CASE 1: STUDY ONLY MODE (Allows Math/Physics/Exams, Blurs Coding) ---")
    engine.save_preferences({
        "shield_enabled": True,
        "active_categories": ["study"],
        "custom_keywords": []
    })

    calc_res = engine.decide("Calculus 3: Multiple Integrals and Vector Fields Lecture 12", "MIT OpenCourseWare")
    print(f"1. Calculus Lecture: is_allowed={calc_res.is_allowed}, tag={calc_res.category_tag}, YT_ID={calc_res.youtube_category_id}")
    assert calc_res.is_allowed is True and calc_res.category_tag == "study"

    code_res = engine.decide("FastAPI Crash Course: Build REST APIs with Python", "Traversy Media")
    print(f"2. FastAPI Coding in Study-Only Mode: is_allowed={code_res.is_allowed}, tag={code_res.category_tag}, YT_ID={code_res.youtube_category_id}")
    assert code_res.is_allowed is False and code_res.category_tag == "coding"

    print("\n--- TEST CASE 2: CODING ONLY MODE (Allows Programming/DSA/ML, Blurs General Study) ---")
    engine.save_preferences({
        "shield_enabled": True,
        "active_categories": ["coding"],
        "custom_keywords": []
    })

    code_res2 = engine.decide("FastAPI Crash Course: Build REST APIs with Python", "Traversy Media")
    print(f"3. FastAPI Coding in Coding-Only Mode: is_allowed={code_res2.is_allowed}, tag={code_res2.category_tag}")
    assert code_res2.is_allowed is True and code_res2.category_tag == "coding"

    calc_res2 = engine.decide("Calculus 3: Multiple Integrals and Vector Fields Lecture 12", "MIT OpenCourseWare")
    print(f"4. Calculus Lecture in Coding-Only Mode: is_allowed={calc_res2.is_allowed}, tag={calc_res2.category_tag}")
    assert calc_res2.is_allowed is False and calc_res2.category_tag == "study"

    print("\n--- TEST CASE 3: STUDY + CODING + SCIFI + ANIME ---")
    engine.save_preferences({
        "shield_enabled": True,
        "active_categories": ["study", "coding", "scifi", "anime"],
        "custom_keywords": ["cyberpunk"]
    })

    assert engine.decide("Attack on Titan Season 4 Episode 12", "AnimeZone").is_allowed is True
    assert engine.decide("Interstellar Black Hole Physics Explained", "Veritasium").is_allowed is True
    assert engine.decide("MrBeast $1 vs $1,000,000 Hotel Room", "MrBeast").is_allowed is False

    print("\nALL 3-LAYER YOUTUBE CATEGORIZATION & STUDY/CODING SEPARATION TESTS PASSED!")


if __name__ == "__main__":
    run_tests()
