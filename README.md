# 🛡️ StudyShield: Real-Time Local AI Video Focus Filter

An offline, privacy-first YouTube focus filter powered by the **Laya (ModernBERT)** decision-making model.

Built for **Diploma 5th Semester AI & ML Engineering** (Subject: *AI and ML Algorithms*).

---

## 💻 New: Minimalist Desktop Application
You can control your entire focus shield directly from a native desktop application with a modern dark-mode UI:

* **Master Shield Toggle:** Turn the shield **ON** or **OFF** with one click.
  * When **ON**: Automatically blurs any video that does **not** match your preferences.
  * When **OFF**: Browsing is completely unrestricted (no blur).
* **Multi-Preference Selector:**
  * 📚 **Study & Technical** (AI/ML, Math, Coding, Engineering, Lectures)
  * 🚀 **Science Fiction & Space** (Sci-Fi, Astrophysics, Cosmos, NASA)
  * 🎌 **Anime & Animation** (Anime series, Manga, Animation analysis)
  * 💻 **Technology & Software** (Linux, DevOps, Hardware, Architecture)
* **Custom Keyword Tagging:** Add your own custom allowed topics (e.g. `chess`, `documentary`, `cooking`, `robotics`).
* **Interactive Live Tester:** Paste any video title directly into the app to see Laya's sub-millisecond decision (<0.2 ms).
* **Live Session Metrics:** Displays counters for distractions blurred, allowed videos kept, and real-time decision latency.
* **1-Click YouTube Launcher:** Opens YouTube directly from the app.

---

## 🚀 How to Run the Desktop Application

### Option A: One-Click Runner (Windows)
Double-click:
👉 **[`start_desktop_app.bat`](file:///c:/Users/sarf0/.antigravity-ide/Decision-Making-Model/start_desktop_app.bat)**

### Option B: Terminal Command
```bash
python desktop_app.py
```

---

## 🛠️ Full Setup (Desktop App + Backend + Extension)

### 1. Start the Local Decision Server
```bash
python backend/server.py
```
*(Or double-click `start_studyshield.bat`)*

### 2. Launch the Desktop App
```bash
python desktop_app.py
```
*(Or double-click `start_desktop_app.bat`)*

### 3. Load the Extension into Google Chrome / Edge
1. Open Chrome/Edge and navigate to `chrome://extensions`.
2. Toggle on **Developer mode** (top-right corner).
3. Click **"Load unpacked"** (top-left).
4. Select the `extension/` folder inside this project.
5. Open YouTube! Whatever you configured in your Desktop App will be reflected on YouTube in real time.

---

## 📊 Benchmark Results (Tested on 50 YouTube items)
* **Overall Accuracy:** **82.00%**
* **Recall (Sensitivity):** **96.00%**
* **Average Inference Latency:** **0.16 ms** (Sub-millisecond on local CPU)
* **Model Size:** **803.57 MB** (Official Laya weights, 100% offline)

---

## 📂 Project Structure
```text
Decision-Making-Model/
├── desktop_app.py               # Minimalist CustomTkinter Desktop Application
├── start_desktop_app.bat        # One-click Windows runner for Desktop App
├── start_studyshield.bat        # One-click Windows runner for Backend Server
├── download_monitor.html        # Real-time web download monitor
├── backend/
│   ├── models/laya/
│   │   ├── model.safetensors    # 803.57 MB official Laya model weights
│   │   ├── active_preference.json # Synced preferences between Desktop & Extension
│   │   └── tokenizer.json       # ModernBERT vocabulary
│   ├── decision_engine.py       # Core Laya multi-preference decision engine
│   └── server.py                # FastAPI microservice on http://localhost:8000
├── extension/
│   ├── manifest.json            # Chrome Extension Manifest V3
│   ├── content.js               # Real-time YouTube DOM observer & auto-blur
│   ├── overlay.css              # Glassmorphism blur styling & shield badge
│   ├── popup.html               # Extension UI panel
│   └── popup.js                 # Settings sync
├── tests/
│   ├── benchmark_latency.py     # Academic latency & accuracy profiling
│   ├── test_preferences.py      # Verification test for multi-preference profiles
│   ├── test_server_api.py       # API test suite
│   └── test_titles.json         # 50 labeled YouTube benchmark test cases
├── docs/
│   └── project_report.md        # Academic submission report for 5th Sem Diploma
└── README.md                    # Project documentation
```
