"""
StudyShield — Native Desktop Control Center & Real-Time YouTube Link Analyzer
Features a modern dark-mode UI, non-blocking background worker threads,
live telemetry counters, and instant synchronization with the Chrome Extension.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk
import webbrowser
import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
from decision_engine import LayaDecisionEngine

API_URL = "http://127.0.0.1:8000"

CATEGORIES = [
    ("study", "📚 Study & Education"),
    ("tech", "💻 Technology & Software"),
    ("scifi", "🚀 Sci-Fi & Space"),
    ("cooking", "🍲 Cooking & Food"),
    ("cartoon", "🎨 Cartoon & Animation"),
    ("anime", "⚔️ Anime & Manga"),
    ("gaming", "🎮 Gaming & Esports"),
    ("music", "🎵 Music & Songs"),
    ("sports", "🏏 Sports & Fitness"),
    ("vlog", "💄 Vlog & Daily Life"),
    ("comedy", "😂 Comedy & Pranks"),
    ("clickbait", "🚨 Sensational & Clickbait"),
]


class StudyShieldDesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("StudyShield — AI Focus Control Center")
        self.root.geometry("920x680")
        self.root.minsize(860, 640)
        self.root.configure(bg="#070b14")

        self.local_engine = LayaDecisionEngine()
        self.shield_enabled = tk.BooleanVar(value=True)
        self.cat_vars = {tag: tk.BooleanVar(value=(tag == "study")) for tag, _ in CATEGORIES}
        self.custom_keywords = []

        self._build_ui()
        self._load_initial_state()
        self._schedule_telemetry_poll()

    def _build_ui(self):
        # Top Header Bar
        header = tk.Frame(self.root, bg="#0f172a", padx=22, pady=16, highlightthickness=1, highlightbackground="#1e293b")
        header.pack(fill="x", padx=20, pady=(18, 12))

        title_col = tk.Frame(header, bg="#0f172a")
        title_col.pack(side="left")
        tk.Label(
            title_col,
            text="🛡️ StudyShield Command Center",
            font=("Segoe UI", 17, "bold"),
            fg="#f8fafc",
            bg="#0f172a",
        ).pack(anchor="w")
        tk.Label(
            title_col,
            text="Real-Time Local System-1 AI Video Focus Filter • Laya Decision Engine",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#0f172a",
        ).pack(anchor="w", pady=(2, 0))

        self.status_badge = tk.Label(
            header,
            text="● Laya Engine Ready",
            font=("Segoe UI", 10, "bold"),
            fg="#34d399",
            bg="#064e3b",
            padx=12,
            pady=6,
        )
        self.status_badge.pack(side="right")

        # Main Two-Column Container
        body = tk.Frame(self.root, bg="#070b14")
        body.pack(fill="both", expand=True, padx=20, pady=4)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)

        # Left Column: Shield Toggle + Category Grid + Custom Keywords
        left_panel = tk.Frame(body, bg="#0f172a", padx=20, pady=18, highlightthickness=1, highlightbackground="#1e293b")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        toggle_row = tk.Frame(left_panel, bg="#1e293b", padx=14, pady=12)
        toggle_row.pack(fill="x", pady=(0, 14))

        tk.Checkbutton(
            toggle_row,
            text=" Enable Real-Time YouTube Focus Shield Protection",
            variable=self.shield_enabled,
            command=self.save_preferences_async,
            font=("Segoe UI", 11, "bold"),
            fg="#38bdf8",
            bg="#1e293b",
            selectcolor="#0f172a",
            activebackground="#1e293b",
            activeforeground="#38bdf8",
            cursor="hand2",
        ).pack(side="left")

        preset_row = tk.Frame(left_panel, bg="#0f172a")
        preset_row.pack(fill="x", pady=(0, 10))
        tk.Label(
            preset_row,
            text="ALLOWED CONTENT CATEGORIES",
            font=("Segoe UI", 9, "bold"),
            fg="#cbd5e1",
            bg="#0f172a",
        ).pack(side="left")

        for label, mode in [("Clear", "none"), ("All", "all"), ("📚 Study Only", "study")]:
            tk.Button(
                preset_row,
                text=label,
                command=lambda m=mode: self.apply_preset(m),
                font=("Segoe UI", 8, "bold"),
                fg="#e2e8f0",
                bg="#1e293b",
                activebackground="#334155",
                relief="flat",
                padx=8,
                pady=3,
                cursor="hand2",
            ).pack(side="right", padx=3)

        grid_frame = tk.Frame(left_panel, bg="#0f172a")
        grid_frame.pack(fill="x", pady=(0, 14))
        for idx, (tag, name) in enumerate(CATEGORIES):
            r, c = divmod(idx, 2)
            grid_frame.columnconfigure(c, weight=1)
            cb = tk.Checkbutton(
                grid_frame,
                text=f" {name}",
                variable=self.cat_vars[tag],
                font=("Segoe UI", 10),
                fg="#f1f5f9",
                bg="#131c31",
                selectcolor="#0284c7",
                activebackground="#1e293b",
                activeforeground="#38bdf8",
                anchor="w",
                padx=10,
                pady=7,
                cursor="hand2",
            )
            cb.grid(row=r, column=c, sticky="ew", padx=4, pady=4)

        # Custom Keywords Input
        kw_label = tk.Label(
            left_panel,
            text="CUSTOM ALLOWED KEYWORDS (COMMA SEPARATED)",
            font=("Segoe UI", 9, "bold"),
            fg="#cbd5e1",
            bg="#0f172a",
        )
        kw_label.pack(anchor="w", pady=(4, 4))

        self.kw_entry = tk.Entry(
            left_panel,
            font=("Segoe UI", 10),
            fg="#ffffff",
            bg="#070b14",
            insertbackground="#ffffff",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#334155",
        )
        self.kw_entry.pack(fill="x", ipady=7, pady=(0, 14))

        self.save_btn = tk.Button(
            left_panel,
            text="⚡ Save Preferences & Sync with Chrome Extension",
            command=self.save_preferences_async,
            font=("Segoe UI", 11, "bold"),
            fg="#ffffff",
            bg="#10b981",
            activebackground="#059669",
            relief="flat",
            pady=10,
            cursor="hand2",
        )
        self.save_btn.pack(fill="x")

        # Right Column: Live Telemetry + Link Analyzer
        right_panel = tk.Frame(body, bg="#0f172a", padx=20, pady=18, highlightthickness=1, highlightbackground="#1e293b")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        tk.Label(
            right_panel,
            text="SESSION TELEMETRY",
            font=("Segoe UI", 9, "bold"),
            fg="#cbd5e1",
            bg="#0f172a",
        ).pack(anchor="w", pady=(0, 8))

        stats_frame = tk.Frame(right_panel, bg="#0f172a")
        stats_frame.pack(fill="x", pady=(0, 16))
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)

        allowed_card = tk.Frame(stats_frame, bg="#131c31", padx=12, pady=10)
        allowed_card.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        tk.Label(allowed_card, text="ALLOWED", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#131c31").pack(anchor="w")
        self.lbl_allowed = tk.Label(allowed_card, text="0", font=("Segoe UI", 20, "bold"), fg="#34d399", bg="#131c31")
        self.lbl_allowed.pack(anchor="w")

        blocked_card = tk.Frame(stats_frame, bg="#131c31", padx=12, pady=10)
        blocked_card.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        tk.Label(blocked_card, text="BLURRED", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#131c31").pack(anchor="w")
        self.lbl_blocked = tk.Label(blocked_card, text="0", font=("Segoe UI", 20, "bold"), fg="#f43f5e", bg="#131c31")
        self.lbl_blocked.pack(anchor="w")

        # YouTube URL / Title Analyzer
        tk.Label(
            right_panel,
            text="🔍 YOUTUBE LINK / TITLE TESTER",
            font=("Segoe UI", 9, "bold"),
            fg="#cbd5e1",
            bg="#0f172a",
        ).pack(anchor="w", pady=(6, 6))

        self.test_entry = tk.Entry(
            right_panel,
            font=("Segoe UI", 10),
            fg="#ffffff",
            bg="#070b14",
            insertbackground="#ffffff",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#334155",
        )
        self.test_entry.pack(fill="x", ipady=7, pady=(0, 8))
        self.test_entry.insert(0, "Complete Machine Learning Course with Python")

        tk.Button(
            right_panel,
            text="Analyze with Laya Engine",
            command=self.analyze_input_async,
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg="#0284c7",
            activebackground="#0369a1",
            relief="flat",
            pady=8,
            cursor="hand2",
        ).pack(fill="x", pady=(0, 12))

        self.result_box = tk.Label(
            right_panel,
            text="Enter any YouTube URL or video title above to inspect Laya's real-time classification and latency.",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#070b14",
            justify="left",
            wraplength=290,
            padx=12,
            pady=12,
        )
        self.result_box.pack(fill="both", expand=True)

        tk.Button(
            right_panel,
            text="🌐 Open Web Dashboard (localhost:8000)",
            command=lambda: webbrowser.open("http://127.0.0.1:8000"),
            font=("Segoe UI", 9, "bold"),
            fg="#38bdf8",
            bg="#1e293b",
            relief="flat",
            pady=7,
            cursor="hand2",
        ).pack(fill="x", pady=(10, 0))

    def apply_preset(self, mode: str):
        for tag, var in self.cat_vars.items():
            if mode == "study":
                var.set(tag == "study")
            elif mode == "all":
                var.set(True)
            else:
                var.set(False)
        self.save_preferences_async()

    def _load_initial_state(self):
        prefs = self.local_engine.load_preferences()
        self.shield_enabled.set(prefs.get("shield_enabled", True))
        active = prefs.get("active_categories", ["study"])
        for tag, var in self.cat_vars.items():
            var.set(tag in active)
        kws = prefs.get("custom_keywords", [])
        self.kw_entry.delete(0, tk.END)
        self.kw_entry.insert(0, ", ".join(kws))
        self.lbl_allowed.config(text=str(prefs.get("allowed_count", 0)))
        self.lbl_blocked.config(text=str(prefs.get("blocked_count", 0)))

    def save_preferences_async(self):
        active_cats = [tag for tag, var in self.cat_vars.items() if var.get()]
        raw_kws = self.kw_entry.get().split(",")
        kws = [k.strip().lower() for k in raw_kws if k.strip()]
        payload = {
            "shield_enabled": self.shield_enabled.get(),
            "active_categories": active_cats,
            "custom_keywords": kws,
        }
        self.save_btn.config(text="✅ Saved & Synced!", bg="#059669")
        self.root.after(1500, lambda: self.save_btn.config(text="⚡ Save Preferences & Sync with Chrome Extension", bg="#10b981"))

        def worker():
            self.local_engine.save_preferences(payload)
            try:
                requests.post(f"{API_URL}/preferences", json=payload, timeout=0.6)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def analyze_input_async(self):
        query = self.test_entry.get().strip()
        if not query:
            return
        self.result_box.config(text="⏳ Evaluating...", fg="#38bdf8")

        def worker():
            data = None
            try:
                resp = requests.post(f"{API_URL}/analyze_link", json={"url_or_title": query}, timeout=2.5)
                if resp.status_code == 200:
                    data = resp.json()
            except Exception:
                pass

            if not data:
                res = self.local_engine.decide(title=query, channel="Desktop Analyzer")
                data = res.to_dict()
                data["title"] = query

            def update_ui():
                allowed = data.get("is_allowed", False)
                verdict = "✅ ALLOWED (CLEAR)" if allowed else "🚫 BLOCKED (BLURRED)"
                color = "#34d399" if allowed else "#fb7185"
                text = (
                    f"{verdict}\n\n"
                    f"Category: {data.get('category')}\n"
                    f"Confidence: {int(data.get('confidence', 0.95) * 100)}%\n"
                    f"Latency: {data.get('latency_ms', 0.2)} ms\n\n"
                    f"{data.get('explanation', '')}"
                )
                self.result_box.config(text=text, fg=color)

            self.root.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def _schedule_telemetry_poll(self):
        def worker():
            online = False
            prefs = None
            try:
                r = requests.get(f"{API_URL}/preferences", timeout=0.5)
                if r.status_code == 200:
                    prefs = r.json()
                    online = True
            except Exception:
                prefs = self.local_engine.load_preferences()

            def update_ui():
                if online:
                    self.status_badge.config(text="● Server Connected (8000)", fg="#34d399", bg="#064e3b")
                else:
                    self.status_badge.config(text="● Local Fallback Mode", fg="#38bdf8", bg="#0c4a6e")
                if prefs:
                    self.lbl_allowed.config(text=str(prefs.get("allowed_count", 0)))
                    self.lbl_blocked.config(text=str(prefs.get("blocked_count", 0)))

            self.root.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(2500, self._schedule_telemetry_poll)


if __name__ == "__main__":
    root = tk.Tk()
    app = StudyShieldDesktopApp(root)
    root.mainloop()
