"""
StudyShield — FastAPI Local Decision Microservice
Provides low-latency (<25ms) offline decision endpoints and YouTube URL analyzer.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
import requests
import re
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decision_engine import LayaDecisionEngine

app = FastAPI(
    title="StudyShield Local Decision API",
    description="Offline Laya decision engine with link analysis & fine-grained categorization",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = LayaDecisionEngine()

class DecisionRequest(BaseModel):
    title: str = Field(..., description="Video title")
    channel: Optional[str] = Field("", description="Channel name")
    focus_domain: Optional[str] = Field("", description="Optional domain override")

class LinkAnalysisRequest(BaseModel):
    url_or_title: str = Field(..., description="YouTube URL or plain video title")

class PreferenceUpdate(BaseModel):
    shield_enabled: Optional[bool] = None
    active_categories: Optional[List[str]] = None
    custom_keywords: Optional[List[str]] = None

@app.get("/health")
def health_check():
    return {
        "status": "active",
        "model": "Laya (ModernBERT-large, 803MB)",
        "offline": True,
        "categories_supported": list(engine.category_taxonomies.keys())
    }

@app.get("/preferences")
def get_preferences():
    return engine.load_preferences()

@app.post("/preferences")
def update_preferences(pref: PreferenceUpdate):
    curr = engine.load_preferences()
    if pref.shield_enabled is not None:
        curr["shield_enabled"] = pref.shield_enabled
    if pref.active_categories is not None:
        curr["active_categories"] = pref.active_categories
    if pref.custom_keywords is not None:
        curr["custom_keywords"] = pref.custom_keywords
    engine.save_preferences(curr)
    return {"status": "updated", "preferences": curr}

@app.post("/reset_stats")
def reset_stats():
    curr = engine.load_preferences()
    curr["blocked_count"] = 0
    curr["allowed_count"] = 0
    engine.save_preferences(curr)
    return {"status": "reset", "preferences": curr}

@app.post("/decide")
def get_decision(req: DecisionRequest):
    result = engine.decide(
        title=req.title,
        channel=req.channel or ""
    )
    return result.to_dict()

@app.post("/analyze_link")
def analyze_link(req: LinkAnalysisRequest):
    """
    Accepts a YouTube URL or video title.
    If it is a URL, fetches title/channel via oEmbed.
    Runs Laya decision model and returns verdict, fine-grained category, and explanation.
    """
    input_str = req.url_or_title.strip()
    title = input_str
    channel = ""
    thumbnail = ""

    # Check if input is a YouTube URL
    if "youtube.com" in input_str or "youtu.be" in input_str:
        try:
            oembed_url = f"https://www.youtube.com/oembed?url={input_str}&format=json"
            resp = requests.get(oembed_url, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                title = data.get("title", input_str)
                channel = data.get("author_name", "")
                thumbnail = data.get("thumbnail_url", "")
        except Exception:
            pass # Fall back to input string

    decision = engine.decide(title=title, channel=channel)
    res_dict = decision.to_dict()
    res_dict["title"] = title
    res_dict["channel"] = channel
    res_dict["thumbnail"] = thumbnail
    return res_dict

if __name__ == "__main__":
    print("[StudyShield Server] Starting on http://localhost:8000...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False, access_log=False)
