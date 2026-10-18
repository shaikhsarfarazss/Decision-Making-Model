"""
API validation script for StudyShield FastAPI 3-Layer YouTube Backend
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_api():
    print("1. Testing /health and /preferences endpoints...")
    client.post(
        "/preferences",
        json={
            "shield_enabled": True,
            "active_categories": ["study", "coding"],
            "custom_keywords": [],
        },
    )
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health = res.json()
    print(f"   PASS: {len(health['categories_supported'])} YouTube categories supported.")
    assert "study" in health["categories_supported"] and "coding" in health["categories_supported"]

    print("\n2. Testing /decide with Academic Study Lecture (YouTube ID 27)...")
    res = client.post(
        "/decide",
        json={
            "title": "Calculus 3: Multiple Integrals and Vector Fields Lecture 12",
            "channel": "MIT OpenCourseWare",
            "focus_domain": "aiml",
        },
    )
    assert res.status_code == 200
    data = res.json()
    print(f"   PASS: tag={data['category_tag']}, yt_id={data['youtube_category_id']} ({data['youtube_macro_category']})")
    assert data["is_study"] is True
    assert data["category_tag"] == "study"
    assert data["youtube_category_id"] == "27"

    print("\n3. Testing /decide with Coding & Dev Tutorial (YouTube ID 28)...")
    res = client.post(
        "/decide",
        json={
            "title": "FastAPI Crash Course: Build REST APIs with Python",
            "channel": "Traversy Media",
            "focus_domain": "aiml",
        },
    )
    assert res.status_code == 200
    data = res.json()
    print(f"   PASS: tag={data['category_tag']}, yt_id={data['youtube_category_id']} ({data['youtube_macro_category']})")
    assert data["is_study"] is True
    assert data["category_tag"] == "coding"
    assert data["youtube_category_id"] == "28"

    print("\n4. Testing /decide with Gaming Distraction (YouTube ID 20)...")
    res = client.post(
        "/decide",
        json={
            "title": "I Survived 100 Days in Hardcore Minecraft Survival",
            "channel": "Luke TheNotable",
            "focus_domain": "aiml",
        },
    )
    assert res.status_code == 200
    data = res.json()
    print(f"   PASS: tag={data['category_tag']}, yt_id={data['youtube_category_id']} ({data['youtube_macro_category']})")
    assert data["is_study"] is False
    assert data["category_tag"] == "gaming"
    assert data["youtube_category_id"] == "20"

    print("\n5. Testing /batch_decide with multi-item batch including Bardock anime test...")
    batch_res = client.post(
        "/batch_decide",
        json={
            "items": [
                {"id": "test_mit", "title": "Calculus 1: Derivatives and Integrals", "channel": "MIT OpenCourseWare"},
                {"id": "test_bardock", "title": "Bardock Super Saiyan Transformation Scene", "channel": "DragonBallClips"},
                {"id": "test_coding", "title": "FastAPI Crash Course", "channel": "Traversy Media"},
            ],
            "focus_domain": "aiml",
        },
    )
    assert batch_res.status_code == 200
    batch_data = batch_res.json()
    assert batch_data["success"] is True
    results = batch_data["results"]
    assert "test_mit" in results and "test_bardock" in results and "test_coding" in results
    print(f"   PASS: MIT Calculus action={results['test_mit']['action']}, tag={results['test_mit']['category_tag']}")
    assert results["test_mit"]["action"] == "ALLOW"
    print(f"   PASS: Bardock action={results['test_bardock']['action']}, tag={results['test_bardock']['category_tag']}")
    assert results["test_bardock"]["action"] == "BLUR"
    assert results["test_bardock"]["category_tag"] == "anime"
    print(f"   PASS: Coding action={results['test_coding']['action']}, tag={results['test_coding']['category_tag']}")
    assert results["test_coding"]["action"] == "ALLOW"

    print("\nALL FASTAPI 3-LAYER YOUTUBE ENDPOINT & BATCH TESTS PASSED!")


if __name__ == "__main__":
    test_api()
