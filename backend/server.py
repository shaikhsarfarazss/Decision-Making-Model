"""
StudyShield — FastAPI Local Decision Microservice & Web Control Center
Provides low-latency (<25ms) offline decision endpoints, YouTube URL analyzer,
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
    description="Offline Laya decision engine with link analysis, fine-grained categorization & Web Control Center",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = LayaDecisionEngine()
recent_decisions: deque = deque(maxlen=30)


class DecisionRequest(BaseModel):
    title: str = Field(..., description="Video title")
    channel: Optional[str] = Field("", description="Channel name")
    focus_domain: Optional[str] = Field(None, description="Optional domain override")


class LinkAnalysisRequest(BaseModel):
    url_or_title: str = Field(..., description="YouTube URL or plain video title")


class PreferenceUpdate(BaseModel):
    shield_enabled: Optional[bool] = None
    active_categories: Optional[List[str]] = None
    custom_keywords: Optional[List[str]] = None


@app.get("/health")
def health_check() -> Dict[str, Any]:
    prefs = engine.load_preferences()
    return {
        "status": "active",
        "model": "Laya (ModernBERT-large, 803MB)",
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
    if pref.shield_enabled is not None:
        update_dict["shield_enabled"] = pref.shield_enabled
    if pref.active_categories is not None:
        update_dict["active_categories"] = pref.active_categories
    if pref.custom_keywords is not None:
        update_dict["custom_keywords"] = pref.custom_keywords
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
        "title": req.title[:70],
        "channel": (req.channel or "YouTube")[:35],
        "is_allowed": res_dict["is_allowed"],
        "category": res_dict["category"],
        "confidence": res_dict["confidence"],
        "latency_ms": res_dict["latency_ms"],
        "timestamp": time.strftime("%H:%M:%S"),
    })
    return res_dict


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
        "title": title[:70],
        "channel": channel[:35],
        "is_allowed": res_dict["is_allowed"],
        "category": res_dict["category"],
        "confidence": res_dict["confidence"],
        "latency_ms": res_dict["latency_ms"],
        "timestamp": time.strftime("%H:%M:%S"),
    })
    return res_dict


@app.get("/", response_class=HTMLResponse)
def web_dashboard() -> str:
    """Serves a sleek, real-time Web Control Center at http://127.0.0.1:8000/."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>StudyShield — AI Focus Command Center</title>
  <style>
    :root {
      --bg: #070b14;
      --surface: #0f172a;
      --surface-hover: #1e293b;
      --border: rgba(148, 163, 184, 0.14);
      --accent: #38bdf8;
      --accent-indigo: #6366f1;
      --emerald: #10b981;
      --rose: #f43f5e;
      --text: #f8fafc;
      --muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', system-ui, -apple-system, sans-serif; }
    body { background: radial-gradient(circle at top right, #1e1b4b, #070b14 55%); color: var(--text); min-height: 100vh; padding: 28px; }
    .container { max-width: 1180px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; padding: 18px 24px; background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(16px); border: 1px solid var(--border); border-radius: 16px; margin-bottom: 24px; }
    .brand { display: flex; align-items: center; gap: 14px; }
    .shield-icon { width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, var(--accent), var(--accent-indigo)); display: flex; align-items: center; justify-content: center; font-size: 22px; box-shadow: 0 0 24px rgba(56, 189, 248, 0.35); }
    .brand h1 { font-size: 20px; font-weight: 800; letter-spacing: -0.3px; }
    .brand p { font-size: 12px; color: var(--muted); }
    .badge-online { display: flex; align-items: center; gap: 8px; padding: 7px 14px; border-radius: 999px; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.35); color: #34d399; font-size: 12px; font-weight: 700; }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--emerald); box-shadow: 0 0 10px var(--emerald); }
    .stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
    .stat-card { background: rgba(15, 23, 42, 0.75); border: 1px solid var(--border); border-radius: 14px; padding: 18px 20px; }
    .stat-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted); }
    .stat-val { font-size: 28px; font-weight: 800; margin-top: 6px; }
    .grid-main { display: grid; grid-template-columns: 1.35fr 1fr; gap: 24px; }
    .panel { background: rgba(15, 23, 42, 0.8); border: 1px solid var(--border); border-radius: 16px; padding: 22px; margin-bottom: 24px; }
    .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    .panel-title { font-size: 14px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.6px; color: #cbd5e1; }
    .cat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 18px; }
    .cat-card { display: flex; align-items: center; gap: 10px; padding: 11px 13px; border-radius: 10px; background: rgba(30, 41, 59, 0.5); border: 1px solid var(--border); cursor: pointer; user-select: none; font-size: 13px; font-weight: 600; transition: all 0.18s; }
    .cat-card:hover { border-color: rgba(56, 189, 248, 0.4); }
    .cat-card.active { background: rgba(56, 189, 248, 0.15); border-color: var(--accent); color: var(--accent); box-shadow: 0 0 16px rgba(56, 189, 248, 0.15); }
    .cat-card input { display: none; }
    .btn-group { display: flex; gap: 8px; }
    .btn-sm { background: #1e293b; border: 1px solid rgba(255,255,255,0.1); color: #cbd5e1; padding: 6px 11px; border-radius: 7px; font-size: 11px; font-weight: 700; cursor: pointer; }
    .btn-sm:hover { background: #334155; color: #fff; }
    .btn-primary { width: 100%; background: linear-gradient(135deg, #059669, #10b981); color: #fff; border: none; padding: 13px; border-radius: 10px; font-size: 14px; font-weight: 800; cursor: pointer; box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3); transition: 0.2s; }
    .btn-primary:hover { transform: translateY(-1px); }
    .input-row { display: flex; gap: 10px; margin-bottom: 12px; }
    .text-input { flex: 1; background: #090d16; border: 1px solid var(--border); border-radius: 9px; padding: 10px 14px; color: #fff; font-size: 13px; outline: none; }
    .text-input:focus { border-color: var(--accent); }
    .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }
    .chip { background: #1e293b; border: 1px solid rgba(56, 189, 248, 0.3); color: #e2e8f0; padding: 4px 10px; border-radius: 999px; font-size: 12px; display: inline-flex; align-items: center; gap: 6px; }
    .chip span.del { color: var(--rose); cursor: pointer; font-weight: 800; }
    .verdict-box { margin-top: 14px; padding: 16px; border-radius: 12px; display: none; border: 1px solid var(--border); background: #090d16; }
    .feed-list { max-height: 360px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
    .feed-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-radius: 9px; background: rgba(9, 13, 22, 0.7); border-left: 3px solid var(--emerald); font-size: 12px; }
    .feed-item.blocked { border-left-color: var(--rose); }
  </style>
</head>
<body>
  <div class="container">
    <div class="topbar">
      <div class="brand">
        <div class="shield-icon">🛡️</div>
        <div>
          <h1>StudyShield Command Center</h1>
          <p>Real-Time System-1 Local AI Video Focus Filter • Laya Decision Engine</p>
        </div>
      </div>
      <div class="badge-online"><div class="dot"></div><span>Laya Engine Active (0.2ms Local)</span></div>
    </div>

    <div class="stats-row">
      <div class="stat-card"><div class="stat-label">Shield Status</div><div class="stat-val" id="statShield" style="color:#38bdf8">ACTIVE</div></div>
      <div class="stat-card"><div class="stat-label">Allowed Videos</div><div class="stat-val" id="statAllowed" style="color:#34d399">0</div></div>
      <div class="stat-card"><div class="stat-label">Blurred Distractions</div><div class="stat-val" id="statBlocked" style="color:#f43f5e">0</div></div>
      <div class="stat-card"><div class="stat-label">Engine Mode</div><div class="stat-val" style="font-size:18px;margin-top:12px;color:#a5b4fc">100% Offline</div></div>
    </div>

    <div class="grid-main">
      <div>
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">Allowed Content Categories</span>
            <div class="btn-group">
              <button class="btn-sm" onclick="toggleMaster()">Toggle Shield ON/OFF</button>
              <button class="btn-sm" onclick="setPreset(['study'])">📚 Study Only</button>
              <button class="btn-sm" onclick="setPreset('all')">Select All</button>
              <button class="btn-sm" onclick="setPreset([])">Clear</button>
            </div>
          </div>
          <div class="cat-grid" id="catGrid"></div>
          <div class="input-row">
            <input type="text" id="kwInput" class="text-input" placeholder="Add custom allowed keyword (e.g. robotics, chess, gate)..." />
            <button class="btn-sm" onclick="addKw()">+ Add Keyword</button>
          </div>
          <div class="chips" id="chipsBox"></div>
          <button class="btn-primary" id="saveBtn" onclick="savePrefs()">⚡ Save & Sync to Chrome Extension + Desktop</button>
        </div>
      </div>

      <div>
        <div class="panel">
          <div class="panel-header"><span class="panel-title">🔍 Live YouTube Link / Title Tester</span></div>
          <div class="input-row">
            <input type="text" id="testInput" class="text-input" placeholder="Paste YouTube URL or video title..." />
            <button class="btn-sm" style="background:#0284c7;color:#fff" onclick="analyzeInput()">Analyze</button>
          </div>
          <div class="verdict-box" id="verdictBox"></div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">📡 Live Interception Feed</span>
            <button class="btn-sm" onclick="resetStats()">Reset Stats</button>
          </div>
          <div class="feed-list" id="feedList"><div style="color:var(--muted);font-size:12px">Waiting for video evaluations...</div></div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const CATEGORIES = [
      {tag:'study', label:'📚 Study & Code'}, {tag:'tech', label:'💻 Technology'},
      {tag:'scifi', label:'🚀 Sci-Fi & Space'}, {tag:'cooking', label:'🍲 Cooking'},
      {tag:'cartoon', label:'🎨 Cartoon'}, {tag:'anime', label:'⚔️ Anime'},
      {tag:'gaming', label:'🎮 Gaming'}, {tag:'music', label:'🎵 Music'},
      {tag:'sports', label:'🏏 Sports'}, {tag:'vlog', label:'💄 Daily Vlogs'},
      {tag:'comedy', label:'😂 Comedy'}, {tag:'clickbait', label:'🚨 Clickbait'}
    ];
    let state = { shield_enabled: true, active_categories: ['study'], custom_keywords: [] };

    function renderCategories() {
      const grid = document.getElementById('catGrid');
      grid.innerHTML = '';
      CATEGORIES.forEach(c => {
        const active = state.active_categories.includes(c.tag);
        const div = document.createElement('div');
        div.className = 'cat-card' + (active ? ' active' : '');
        div.innerHTML = `<span>${c.label}</span>`;
        div.onclick = () => {
          if (state.active_categories.includes(c.tag)) {
            state.active_categories = state.active_categories.filter(x => x !== c.tag);
          } else {
            state.active_categories.push(c.tag);
          }
          renderCategories();
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
      }
    }
    function removeKw(i) { state.custom_keywords.splice(i, 1); renderChips(); }
    function toggleMaster() { state.shield_enabled = !state.shield_enabled; savePrefs(); }
    function setPreset(p) {
      state.active_categories = p === 'all' ? CATEGORIES.map(c => c.tag) : p;
      renderCategories();
    }

    async function savePrefs() {
      const btn = document.getElementById('saveBtn');
      await fetch('/preferences', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(state)
      });
      btn.innerText = '✅ Saved & Broadcasted!';
      setTimeout(() => btn.innerText = '⚡ Save & Sync to Chrome Extension + Desktop', 1800);
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
        state.shield_enabled = d.shield_enabled;
        document.getElementById('statShield').innerText = d.shield_enabled ? 'ACTIVE' : 'PAUSED';
        document.getElementById('statShield').style.color = d.shield_enabled ? '#38bdf8' : '#f59e0b';
        document.getElementById('statAllowed').innerText = d.allowed_count || 0;
        document.getElementById('statBlocked').innerText = d.blocked_count || 0;
        if (d.recent_decisions && d.recent_decisions.length) {
          const fl = document.getElementById('feedList');
          fl.innerHTML = d.recent_decisions.map(item => `
            <div class="feed-item ${item.is_allowed ? '' : 'blocked'}">
              <div>
                <div style="font-weight:700;color:#f1f5f9">${item.title}</div>
                <div style="color:#94a3b8;font-size:11px">${item.category} • ${item.latency_ms}ms</div>
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
      state.active_categories = d.active_categories || ['study'];
      state.custom_keywords = d.custom_keywords || [];
      renderCategories();
      renderChips();
      pollState();
      setInterval(pollState, 2000);
    })();
  </script>
</body>
</html>"""


if __name__ == "__main__":
    print("[StudyShield Server] Starting on http://127.0.0.1:8000 ...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False, access_log=False)
