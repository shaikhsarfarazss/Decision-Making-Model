"""
Quick API validation script for StudyShield FastAPI backend
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_api():
    print("Testing /health endpoint...")
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("  Health check PASS:", res.json())

    print("\nTesting /decide endpoint with Educational Video...")
    res = client.post("/decide", json={
        "title": "Machine Learning Algorithms Crash Course for Beginners",
        "channel": "freeCodeCamp.org",
        "focus_domain": "aiml"
    })
    assert res.status_code == 200, f"Decide failed: {res.text}"
    data = res.json()
    print("  Educational result: is_study =", data["is_study"], "category =", data["category"].encode('ascii', 'ignore').decode())
    assert data["is_study"] is True, "Expected study=True for ML course!"

    print("\nTesting /decide endpoint with Gaming Video...")
    res = client.post("/decide", json={
        "title": "I Survived 100 Days in Hardcore Minecraft Survival",
        "channel": "GamingGuy",
        "focus_domain": "aiml"
    })
    assert res.status_code == 200, f"Decide failed: {res.text}"
    data = res.json()
    print("  Gaming result: is_study =", data["is_study"], "category =", data["category"].encode('ascii', 'ignore').decode())
    assert data["is_study"] is False, "Expected study=False for Minecraft!"

    print("\nALL API TESTS PASSED SUCCESSFULLY! Ready for Chrome Extension connection.")

if __name__ == "__main__":
    test_api()
