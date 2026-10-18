"""
StudyShield — FastAPI Local Decision Microservice & 20-Category Web Command Center
Provides low-latency (<1ms) offline decision endpoints, YouTube URL oEmbed analyzer,
and an interactive Web Dashboard UI at http://127.0.0.1:8000/.
"""

import os
import sys
import time
from collections import deque
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decision_engine import LayaDecisionEngine

app = FastAPI(
    title="StudyShield Local Decision API",
    description="3-Layer YouTube Categorization Engine (20 Categories: Study & Coding Separated)",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = LayaDecisionEngine()
recent_decisions: deque = deque(maxlen=35)


class DecisionRequest(BaseModel):
    title: str = Field(..., description="Video title")
    channel: Optional[str] = Field("", description="Channel name")
    focus_domain: Optional[str] = Field(None, description="Optional domain override")


class LinkAnalysisRequest(BaseModel):
    url_or_title: str = Field(..., description="YouTube URL or plain video title")


class PreferenceUpdate(BaseModel):
    shield_enabled: Optional[bool] = None
    shieldEnabled: Optional[bool] = None
    active_categories: Optional[List[str]] = None
    activeCategories: Optional[List[str]] = None
    custom_keywords: Optional[List[str]] = None
    customKeywords: Optional[List[str]] = None
    updated_at: Optional[float] = None


class BatchDecisionRequest(BaseModel):
    items: List[Dict[str, Any]] = Field(..., description="List of video items to classify in a batch")
    focus_domain: Optional[str] = Field(None, description="Optional domain override")


class ProbeRequest(BaseModel):
    video_id: str = Field(..., description="YouTube Video ID to probe via InnerTube player API")


@app.get("/health")
def health_check() -> Dict[str, Any]:
    prefs = engine.load_preferences()
    return {
        "status": "active",
        "model": "Laya 3-Layer YouTube Classifier (ModernBERT-large, 803MB)",
        "offline": True,
        "categories_supported": list(engine.category_taxonomies.keys()),
        "shield_enabled": prefs.get("shield_enabled", True),
        "allowed_count": prefs.get("allowed_count", 0),
        "blocked_count": prefs.get("blocked_count", 0),
    }


@app.get("/preferences")
def get_preferences() -> Dict[str, Any]:
    prefs = engine.load_preferences()
    prefs["recent_decisions"] = list(recent_decisions)
    return prefs


@app.post("/preferences")
def update_preferences(pref: PreferenceUpdate) -> Dict[str, Any]:
    update_dict = {}
    shield = pref.shield_enabled if pref.shield_enabled is not None else pref.shieldEnabled
    if shield is not None:
        update_dict["shield_enabled"] = shield
    cats = pref.active_categories if pref.active_categories is not None else pref.activeCategories
    if cats is not None:
        update_dict["active_categories"] = cats
    kws = pref.custom_keywords if pref.custom_keywords is not None else pref.customKeywords
    if kws is not None:
        update_dict["custom_keywords"] = kws
    curr = engine.save_preferences(update_dict)
    return {"status": "updated", "preferences": curr}


@app.post("/reset_stats")
def reset_stats() -> Dict[str, Any]:
    curr = engine.save_preferences({"blocked_count": 0, "allowed_count": 0})
    recent_decisions.clear()
    return {"status": "reset", "preferences": curr}


@app.post("/decide")
def get_decision(req: DecisionRequest) -> Dict[str, Any]:
    result = engine.decide(
        title=req.title,
        channel=req.channel or "",
        focus_domain=req.focus_domain,
    )
    res_dict = result.to_dict()
    recent_decisions.appendleft({
        "title": req.title[:72],
        "channel": (req.channel or "YouTube")[:36],
        "is_allowed": res_dict["is_allowed"],
        "category": res_dict["category"],
        "youtube_category_id": res_dict["youtube_category_id"],
        "youtube_macro_category": res_dict["youtube_macro_category"],
        "confidence": res_dict["confidence"],
        "latency_ms": res_dict["latency_ms"],
        "timestamp": time.strftime("%H:%M:%S"),
    })
    return res_dict


@app.post("/classify")
def classify_endpoint(req: DecisionRequest) -> Dict[str, Any]:
    """Alias for /decide endpoint."""
    return get_decision(req)


@app.post("/batch_decide")
def batch_decide(req: BatchDecisionRequest) -> Dict[str, Any]:
    """
    Classifies up to 25 videos in a single vectorized batch (<15ms).
    Uses Tier 0 (RAM/SQLite + Channel Authority) -> Tier 1 (3-Layer + Contrastive Vector) -> Tier 2 Flagging.
    """
    results = engine.decide_batch(req.items, focus_domain=req.focus_domain or "aiml")
    now_str = time.strftime("%H:%M:%S")

    # Push batch evaluations into the Live YouTube Interception Stream on the Web Dashboard
    for item in req.items[:10]:
        vid = str(item.get("id") or item.get("video_id") or "")
        res = results.get(vid)
        if res and item.get("title"):
            recent_decisions.appendleft(
                {
                    "title": item.get("title", "Batch Item")[:72],
                    "channel": item.get("channel", "YouTube")[:36],
                    "is_allowed": res.get("is_allowed", False),
                    "category": res.get("category", "General"),
                    "youtube_category_id": res.get("youtube_category_id", "24"),
                    "youtube_macro_category": res.get("youtube_macro_category", "Entertainment"),
                    "confidence": res.get("confidence", 0.90),
                    "latency_ms": res.get("latency_ms", 0.5),
                    "timestamp": now_str,
                }
            )
    return {"success": True, "results": results}


@app.post("/probe_metadata")
def probe_metadata(req: ProbeRequest) -> Dict[str, Any]:
    """
    Tier 2 Async Probe: Queries YouTube's internal player API for official categoryId and microformat.
    """
    result = engine.probe_youtube_category(req.video_id)
    if result:
        return {"success": True, "data": result}
    return {"success": False, "message": f"Could not probe metadata for video {req.video_id}"}



@app.post("/analyze_link")
def analyze_link(req: LinkAnalysisRequest) -> Dict[str, Any]:
    input_str = req.url_or_title.strip()
    title = input_str
    channel = "Direct Input"
    thumbnail = ""

    if "youtube.com/" in input_str or "youtu.be/" in input_str:
        try:
            oembed_url = f"https://www.youtube.com/oembed?url={quote(input_str, safe=':/?=&')}&format=json"
            resp = requests.get(oembed_url, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                title = data.get("title", input_str)
                channel = data.get("author_name", "YouTube Channel")
                thumbnail = data.get("thumbnail_url", "")
        except Exception:
            pass

    decision = engine.decide(title=title, channel=channel)
    res_dict = decision.to_dict()
    res_dict["title"] = title
    res_dict["channel"] = channel
    res_dict["thumbnail"] = thumbnail

    recent_decisions.appendleft({
        "title": title[:72],
        "channel": channel[:36],
        "is_allowed": res_dict["is_allowed"],
        "category": res_dict["category"],
        "youtube_category_id": res_dict["youtube_category_id"],
        "youtube_macro_category": res_dict["youtube_macro_category"],
        "confidence": res_dict["confidence"],
        "latency_ms": res_dict["latency_ms"],
        "timestamp": time.strftime("%H:%M:%S"),
    })
    return res_dict


@app.get("/", response_class=HTMLResponse)
def web_dashboard() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>StudyShield — 20-Category YouTube AI Command Center</title>
  <style>
    :root {
      --bg: #070b14;
      --surface: #0f172a;
      --border: rgba(148, 163, 184, 0.15);
      --accent: #38bdf8;
      --accent-indigo: #6366f1;
      --emerald: #10b981;
      --rose: #f43f5e;
      --text: #f8fafc;
      --muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', system-ui, -apple-system, sans-serif; }
    body { background: radial-gradient(circle at top right, #1e1b4b, #070b14 55%); color: var(--text); min-height: 100vh; padding: 26px; }
    .container { max-width: 1240px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; padding: 18px 24px; background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(16px); border: 1px solid var(--border); border-radius: 16px; margin-bottom: 22px; }
    .brand { display: flex; align-items: center; gap: 14px; }
    .shield-icon { width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, var(--accent), var(--accent-indigo)); display: flex; align-items: center; justify-content: center; font-size: 22px; box-shadow: 0 0 24px rgba(56, 189, 248, 0.35); }
    .brand h1 { font-size: 20px; font-weight: 800; letter-spacing: -0.3px; }
    .brand p { font-size: 12px; color: var(--muted); }
    .badge-online { display: flex; align-items: center; gap: 8px; padding: 7px 14px; border-radius: 999px; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.35); color: #34d399; font-size: 12px; font-weight: 700; }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--emerald); box-shadow: 0 0 10px var(--emerald); }
    .stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 22px; }
    .stat-card { background: rgba(15, 23, 42, 0.78); border: 1px solid var(--border); border-radius: 14px; padding: 16px 20px; }
    .stat-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted); }
    .stat-val { font-size: 26px; font-weight: 800; margin-top: 6px; }
    .grid-main { display: grid; grid-template-columns: 1.45fr 1fr; gap: 22px; }
    .panel { background: rgba(15, 23, 42, 0.82); border: 1px solid var(--border); border-radius: 16px; padding: 22px; margin-bottom: 22px; }
    .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px; }
    .panel-title { font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.6px; color: #cbd5e1; }
    .cat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 9px; margin-bottom: 18px; }
    .cat-card { display: flex; flex-direction: column; gap: 3px; padding: 10px 12px; border-radius: 10px; background: rgba(30, 41, 59, 0.5); border: 1px solid var(--border); cursor: pointer; user-select: none; transition: all 0.16s; }
    .cat-card:hover { border-color: rgba(56, 189, 248, 0.45); }
    .cat-card.active { background: rgba(56, 189, 248, 0.16); border-color: var(--accent); color: var(--accent); box-shadow: 0 0 14px rgba(56, 189, 248, 0.14); }
    .cat-card .c-name { font-size: 12.5px; font-weight: 700; }
    .cat-card .c-sub { font-size: 10px; color: var(--muted); }
    .btn-group { display: flex; gap: 6px; flex-wrap: wrap; }
    .btn-sm { background: #1e293b; border: 1px solid rgba(255,255,255,0.1); color: #cbd5e1; padding: 6px 10px; border-radius: 7px; font-size: 11px; font-weight: 700; cursor: pointer; }
    .btn-sm:hover { background: #334155; color: #fff; }
    .btn-primary { width: 100%; background: linear-gradient(135deg, #059669, #10b981); color: #fff; border: none; padding: 13px; border-radius: 10px; font-size: 14px; font-weight: 800; cursor: pointer; box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3); }
    .input-row { display: flex; gap: 10px; margin-bottom: 12px; }
    .text-input { flex: 1; background: #090d16; border: 1px solid var(--border); border-radius: 9px; padding: 10px 14px; color: #fff; font-size: 13px; outline: none; }
    .text-input:focus { border-color: var(--accent); }
    .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }
    .chip { background: #1e293b; border: 1px solid rgba(56, 189, 248, 0.3); color: #e2e8f0; padding: 4px 10px; border-radius: 999px; font-size: 12px; display: inline-flex; align-items: center; gap: 6px; }
    .chip span.del { color: var(--rose); cursor: pointer; font-weight: 800; }
    .verdict-box { margin-top: 12px; padding: 16px; border-radius: 12px; display: none; border: 1px solid var(--border); background: #090d16; }
    .feed-list { max-height: 360px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
    .feed-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-radius: 9px; background: rgba(9, 13, 22, 0.75); border-left: 3px solid var(--emerald); font-size: 12px; }
    .feed-item.blocked { border-left-color: var(--rose); }
  </style>
</head>
<body>
  <div class="container">
    <div class="topbar">
      <div class="brand">
        <div class="shield-icon">🛡️</div>
        <div>
          <h1>StudyShield — 3-Layer YouTube Categorization Engine</h1>
          <p>20 Fine-Grained YouTube Categories • Separate Study & Coding Modes • Sub-Millisecond Local AI</p>
        </div>
      </div>
      <div class="badge-online"><div class="dot"></div><span>Laya 3-Layer Engine Active</span></div>
    </div>

    <div class="stats-row">
      <div class="stat-card"><div class="stat-label">Shield Status</div><div class="stat-val" id="statShield" style="color:#38bdf8">ACTIVE</div></div>
      <div class="stat-card"><div class="stat-label">Allowed Videos</div><div class="stat-val" id="statAllowed" style="color:#34d399">0</div></div>
      <div class="stat-card"><div class="stat-label">Blurred Distractions</div><div class="stat-val" id="statBlocked" style="color:#f43f5e">0</div></div>
      <div class="stat-card"><div class="stat-label">Categorization</div><div class="stat-val" style="font-size:16px;margin-top:11px;color:#a5b4fc">YT ID + Knowledge Graph</div></div>
    </div>

    <div class="grid-main">
      <div>
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">20 YouTube Content Categories</span>
            <div class="btn-group">
              <button class="btn-sm" onclick="toggleMaster()">Toggle Shield ON/OFF</button>
              <button class="btn-sm" onclick="setPreset(['study'])">📚 Study Only</button>
              <button class="btn-sm" onclick="setPreset(['coding'])">💻 Code Only</button>
              <button class="btn-sm" onclick="setPreset(['study','coding'])">🎓 Study + Code</button>
              <button class="btn-sm" onclick="setPreset('all')">All</button>
              <button class="btn-sm" onclick="setPreset([])">Clear</button>
            </div>
          </div>
          <div class="cat-grid" id="catGrid"></div>
          <div class="input-row">
            <input type="text" id="kwInput" class="text-input" placeholder="Add custom keyword (e.g. Gate Unit 3, transformers, chess)..." />
            <button class="btn-sm" onclick="addKw()">+ Add Keyword</button>
          </div>
          <div class="chips" id="chipsBox"></div>
          <button class="btn-primary" id="saveBtn" onclick="savePrefs()">⚡ Save & Sync to Chrome Extension + Desktop</button>
        </div>
      </div>

      <div>
        <div class="panel">
          <div class="panel-header"><span class="panel-title">🔍 3-Layer YouTube Video Analyzer</span></div>
          <div class="input-row">
            <input type="text" id="testInput" class="text-input" placeholder="Paste YouTube URL or video title..." />
            <button class="btn-sm" style="background:#0284c7;color:#fff" onclick="analyzeInput()">Analyze</button>
          </div>
          <div class="verdict-box" id="verdictBox"></div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">📡 Live YouTube Interception Stream</span>
            <button class="btn-sm" onclick="resetStats()">Reset Stats</button>
          </div>
          <div class="feed-list" id="feedList"><div style="color:var(--muted);font-size:12px">Waiting for YouTube evaluations...</div></div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const CATEGORIES = [
      {tag:'study', label:'📚 Study & Exams', yt:'ID 27 • Education'},
      {tag:'coding', label:'💻 Coding & Dev', yt:'ID 28 • Sci & Tech'},
      {tag:'tech', label:'🔧 Tech & Gadgets', yt:'ID 28 • Hardware/OS'},
      {tag:'scifi', label:'🚀 Science & Space', yt:'ID 28 • Astronomy'},
      {tag:'news', label:'📰 News & Politics', yt:'ID 25 • Current Affairs'},
      {tag:'finance', label:'📈 Finance & Biz', yt:'ID 27 • Economics'},
      {tag:'howto', label:'🛠️ How-To & DIY', yt:'ID 26 • Productivity'},
      {tag:'podcast', label:'🎙️ Podcasts & Talks', yt:'ID 22 • Interviews'},
      {tag:'cooking', label:'🍲 Cooking & Food', yt:'ID 26 • Culinary'},
      {tag:'autos', label:'🚗 Autos & Bikes', yt:'ID 2 • Vehicles'},
      {tag:'pets', label:'🐾 Pets & Nature', yt:'ID 15 • Wildlife'},
      {tag:'travel', label:'✈️ Travel & Culture', yt:'ID 19 • World Tours'},
      {tag:'music', label:'🎵 Music & Lofi', yt:'ID 10 • Audio/Beats'},
      {tag:'sports', label:'🏏 Sports & Gym', yt:'ID 17 • Athletics'},
      {tag:'anime', label:'⚔️ Anime & Manga', yt:'ID 31 • Anime'},
      {tag:'cartoon', label:'🎨 Cartoons', yt:'ID 1 • Animation'},
      {tag:'gaming', label:'🎮 Gaming & Esports', yt:'ID 20 • Gameplay'},
      {tag:'vlog', label:'💄 Vlogs & Life', yt:'ID 22 • People/Blogs'},
      {tag:'comedy', label:'😂 Comedy & Memes', yt:'ID 23 • Humor/Skits'},
      {tag:'clickbait', label:'🚨 Clickbait & Drama', yt:'ID 24 • Sensational'}
    ];
    let state = { shield_enabled: true, active_categories: ['study', 'coding'], custom_keywords: [] };

    function renderCategories() {
      const grid = document.getElementById('catGrid');
      grid.innerHTML = '';
      CATEGORIES.forEach(c => {
        const active = state.active_categories.includes(c.tag);
        const div = document.createElement('div');
        div.className = 'cat-card' + (active ? ' active' : '');
        div.innerHTML = `<span class="c-name">${c.label}</span><span class="c-sub">${c.yt}</span>`;
        div.onclick = () => {
          if (state.active_categories.includes(c.tag)) {
            state.active_categories = state.active_categories.filter(x => x !== c.tag);
          } else {
            state.active_categories.push(c.tag);
          }
          renderCategories();
          savePrefs(false);
        };
        grid.appendChild(div);
      });
    }

    function renderChips() {
      const box = document.getElementById('chipsBox');
      box.innerHTML = '';
      state.custom_keywords.forEach((kw, i) => {
        const s = document.createElement('span');
        s.className = 'chip';
        s.innerHTML = `#${kw} <span class="del" onclick="removeKw(${i})">×</span>`;
        box.appendChild(s);
      });
    }

    function addKw() {
      const inp = document.getElementById('kwInput');
      const v = inp.value.trim().toLowerCase();
      if (v && !state.custom_keywords.includes(v)) {
        state.custom_keywords.push(v);
        inp.value = '';
        renderChips();
        savePrefs(false);
      }
    }
    function removeKw(i) {
      state.custom_keywords.splice(i, 1);
      renderChips();
      savePrefs(false);
    }
    function toggleMaster() {
      state.shield_enabled = !state.shield_enabled;
      savePrefs(true);
    }
    function setPreset(p) {
      state.active_categories = p === 'all' ? CATEGORIES.map(c => c.tag) : p;
      renderCategories();
      savePrefs(false);
    }

    async function savePrefs(showFeedback = true) {
      const btn = document.getElementById('saveBtn');
      await fetch('/preferences', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(state)
      });
      if (showFeedback) {
        btn.innerText = '✅ Saved & Broadcasted!';
        setTimeout(() => btn.innerText = '⚡ Save & Sync to Chrome Extension + Desktop', 1800);
      }
      pollState();
    }

    async function analyzeInput() {
      const val = document.getElementById('testInput').value.trim();
      if (!val) return;
      const res = await fetch('/analyze_link', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({url_or_title: val})
      });
      const d = await res.json();
      const box = document.getElementById('verdictBox');
      box.style.display = 'block';
      box.style.borderColor = d.is_allowed ? '#10b981' : '#f43f5e';
      box.innerHTML = `
        <div style="font-weight:800;font-size:14px;color:${d.is_allowed ? '#34d399' : '#fb7185'}">
          ${d.is_allowed ? '✅ ALLOWED (UNBLURRED)' : '🚫 BLOCKED (BLURRED)'} — ${d.category} (${Math.round(d.confidence*100)}%)
        </div>
        <div style="font-size:12px;color:#e2e8f0;margin-top:6px"><strong>Title:</strong> ${d.title}</div>
        <div style="font-size:11.5px;color:#38bdf8;margin-top:4px">
          <strong>Layer 1 (YouTube ID):</strong> Category ${d.youtube_category_id} (${d.youtube_macro_category})
        </div>
        <div style="font-size:11.5px;color:#a5b4fc;margin-top:2px">
          <strong>Layer 2 (Knowledge Graph):</strong> ${(d.knowledge_graph_topics || []).join(', ')}
        </div>
        <div style="font-size:11px;color:#94a3b8;margin-top:4px">${d.explanation} • Latency: ${d.latency_ms} ms</div>
      `;
      pollState();
    }

    async function resetStats() {
      await fetch('/reset_stats', {method: 'POST'});
      pollState();
    }

    async function pollState() {
      try {
        const res = await fetch('/preferences');
        const d = await res.json();

        // 1. Sync Shield Enabled toggle
        if (d.shield_enabled !== undefined && state.shield_enabled !== d.shield_enabled) {
          state.shield_enabled = d.shield_enabled;
        }
        document.getElementById('statShield').innerText = state.shield_enabled ? 'ACTIVE' : 'PAUSED';
        document.getElementById('statShield').style.color = state.shield_enabled ? '#38bdf8' : '#f59e0b';
        document.getElementById('statAllowed').innerText = d.allowed_count || 0;
        document.getElementById('statBlocked').innerText = d.blocked_count || 0;

        // 2. Real-time two-way synchronization: If preferences updated in Extension, reflect them immediately!
        const currentCatsSorted = (state.active_categories || []).slice().sort();
        const serverCatsSorted = (d.active_categories || []).slice().sort();
        const categoriesChanged = JSON.stringify(currentCatsSorted) !== JSON.stringify(serverCatsSorted);

        const currentKwSorted = (state.custom_keywords || []).slice().sort();
        const serverKwSorted = (d.custom_keywords || []).slice().sort();
        const keywordsChanged = JSON.stringify(currentKwSorted) !== JSON.stringify(serverKwSorted);

        if (categoriesChanged) {
          state.active_categories = d.active_categories || ['study', 'coding'];
          renderCategories();
        }
        if (keywordsChanged) {
          state.custom_keywords = d.custom_keywords || [];
          renderChips();
        }

        // 3. Update live interception stream
        if (d.recent_decisions && d.recent_decisions.length) {
          const fl = document.getElementById('feedList');
          fl.innerHTML = d.recent_decisions.map(item => `
            <div class="feed-item ${item.is_allowed ? '' : 'blocked'}">
              <div>
                <div style="font-weight:700;color:#f1f5f9">${item.title}</div>
                <div style="color:#94a3b8;font-size:11px">YT ID ${item.youtube_category_id || '24'} (${item.youtube_macro_category || 'Video'}) • ${item.category} • ${item.latency_ms}ms</div>
              </div>
              <span style="font-weight:800;color:${item.is_allowed ? '#34d399' : '#fb7185'}">${item.is_allowed ? 'ALLOWED' : 'BLURRED'}</span>
            </div>
          `).join('');
        }
      } catch (e) {}
    }

    (async () => {
      const res = await fetch('/preferences');
      const d = await res.json();
      state.shield_enabled = d.shield_enabled !== undefined ? d.shield_enabled : true;
      state.active_categories = d.active_categories || ['study', 'coding'];
      state.custom_keywords = d.custom_keywords || [];
      renderCategories();
      renderChips();
      pollState();
      setInterval(pollState, 1000);
    })();
  </script>
</body>
</html>"""


if __name__ == "__main__":
    print("[StudyShield Server] Starting on http://127.0.0.1:8000 ...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False, access_log=False)
