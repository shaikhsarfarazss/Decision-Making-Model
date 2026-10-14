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
    print("1. Testing /health endpoint...")
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

    print("\nALL FASTAPI 3-LAYER YOUTUBE ENDPOINT TESTS PASSED!")


if __name__ == "__main__":
    test_api()
