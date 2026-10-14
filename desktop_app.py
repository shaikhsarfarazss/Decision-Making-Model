"""
StudyShield Desktop Application
Modern, high-performance UI for managing Laya Decision Model preferences.
Allows user to toggle shield, select preferences (Study, Cooking, Cartoon, Anime, Sci-Fi, Tech, etc.),
save preferences with automatic trigger to YouTube, and analyze video links with real-time Red/Green verdicts.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import webbrowser
import threading
import json
import time
import os
import sys
import requests
import subprocess
import urllib.request

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))
from decision_engine import LayaDecisionEngine

# Appearance settings
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class StudyShieldApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("StudyShield Desktop — AI Focus & Category Control")
        self.geometry("980x800")
        self.minsize(920, 720)

        # Set window icon if available
        ico_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "studyshield.ico"))
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        # Auto-launch FastAPI server in background if not already active
        self._ensure_backend_running()

        # Initialize Laya engine locally
        self.engine = LayaDecisionEngine()
        self.preferences = self.engine.load_preferences()

        self._build_ui()

    def _ensure_backend_running(self):
        """Checks if server.py is running on port 8000; if not, starts it silently."""
        def check_and_start():
            try:
                urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1)
            except Exception:
                server_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend", "server.py"))
                python_exe = sys.executable
                creation_flags = 0x08000000 if os.name == 'nt' else 0 # CREATE_NO_WINDOW
                try:
                    subprocess.Popen(
                        [python_exe, server_py],
                        creationflags=creation_flags,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except Exception as e:
                    print(f"Failed to auto-start backend: {e}")

        threading.Thread(target=check_and_start, daemon=True).start()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----------------- 1. Top Header -----------------
        header_frame = ctk.CTkFrame(self, corner_radius=14, fg_color="#0f172a", border_width=1, border_color="#1e293b")
        header_frame.grid(row=0, column=0, padx=22, pady=(18, 8), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=20, pady=14)

        app_title = ctk.CTkLabel(
            title_box, 
            text="🛡️ StudyShield AI Control Center", 
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#f8fafc"
        )
        app_title.pack(anchor="w")

        app_subtitle = ctk.CTkLabel(
            title_box, 
            text="Laya System 1 Decision Model • 803 MB Offline • Real-Time YouTube Blur Control", 
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        )
        app_subtitle.pack(anchor="w")

        status_box = ctk.CTkFrame(header_frame, fg_color="#132338", corner_radius=20, border_width=1, border_color="#38bdf8")
        status_box.pack(side="right", padx=20, pady=14)

        self.status_lbl = ctk.CTkLabel(
            status_box, 
            text="● Laya Engine Active (Local)", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38bdf8"
        )
        self.status_lbl.pack(padx=14, pady=6)

        # ----------------- 2. Main Scrollable Body -----------------
        content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content_frame.grid(row=1, column=0, padx=22, pady=6, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)

        # Card A: Master Shield Protection Switch
        toggle_card = ctk.CTkFrame(content_frame, corner_radius=14, fg_color="#1e293b", border_width=1, border_color="#334155")
        toggle_card.pack(fill="x", pady=(0, 14))

        toggle_header = ctk.CTkFrame(toggle_card, fg_color="transparent")
        toggle_header.pack(fill="x", padx=20, pady=14)

        toggle_text_box = ctk.CTkFrame(toggle_header, fg_color="transparent")
        toggle_text_box.pack(side="left")

        ctk.CTkLabel(
            toggle_text_box, 
            text="Master Focus Shield Protection", 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f8fafc"
        ).pack(anchor="w")

        self.toggle_desc_lbl = ctk.CTkLabel(
            toggle_text_box, 
            text="Active: Automatically blurs all videos & Shorts on YouTube that do not match your allowed preferences.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        )
        self.toggle_desc_lbl.pack(anchor="w")

        self.shield_switch = ctk.CTkSwitch(
            toggle_header, 
            text="SHIELD ON", 
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_shield_toggle,
            progress_color="#0284c7"
        )
        self.shield_switch.pack(side="right")
        if self.preferences.get("shield_enabled", True):
            self.shield_switch.select()
        else:
            self.shield_switch.deselect()

        # Card B: Category Preferences Panel
        pref_card = ctk.CTkFrame(content_frame, corner_radius=14, fg_color="#1e293b", border_width=1, border_color="#334155")
        pref_card.pack(fill="x", pady=(0, 14))

        pref_top_row = ctk.CTkFrame(pref_card, fg_color="transparent")
        pref_top_row.pack(fill="x", padx=20, pady=(16, 6))

        pref_title_box = ctk.CTkFrame(pref_top_row, fg_color="transparent")
        pref_title_box.pack(side="left")

        ctk.CTkLabel(
            pref_title_box, 
            text="🎯 What Content Do You Want to Allow?", 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f8fafc"
        ).pack(anchor="w")

        ctk.CTkLabel(
            pref_title_box, 
            text="Checked categories will remain clear. Unchecked categories will be blurred immediately on YouTube.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        ).pack(anchor="w")

        # Quick Preset Buttons
        presets_bar = ctk.CTkFrame(pref_top_row, fg_color="transparent")
        presets_bar.pack(side="right")

        btn_study_preset = ctk.CTkButton(
            presets_bar, 
            text="📚 Study Only", 
            font=ctk.CTkFont(size=11, weight="bold"),
            width=96, height=28,
            fg_color="#0284c7", hover_color="#0369a1",
            command=self._preset_study_only
        )
        btn_study_preset.pack(side="left", padx=3)

        btn_all_preset = ctk.CTkButton(
            presets_bar, 
            text="Select All", 
            font=ctk.CTkFont(size=11),
            width=76, height=28,
            fg_color="#334155", hover_color="#475569",
            command=self._preset_select_all
        )
        btn_all_preset.pack(side="left", padx=3)

        btn_clear_preset = ctk.CTkButton(
            presets_bar, 
            text="Clear All", 
            font=ctk.CTkFont(size=11),
            width=76, height=28,
            fg_color="#334155", hover_color="#475569",
            command=self._preset_clear_all
        )
        btn_clear_preset.pack(side="left", padx=3)

        # Checkboxes Grid
        presets_grid = ctk.CTkFrame(pref_card, fg_color="transparent")
        presets_grid.pack(fill="x", padx=20, pady=8)
        presets_grid.grid_columnconfigure((0, 1), weight=1)

        active_cats = self.preferences.get("active_categories", ["study"])

        self.cb_study = ctk.CTkCheckBox(presets_grid, text="📚 Study & Technical (AI/ML, Math, Coding, Lectures)", font=ctk.CTkFont(size=13))
        self.cb_study.grid(row=0, column=0, padx=10, pady=6, sticky="w")
        if "study" in active_cats: self.cb_study.select()

        self.cb_cooking = ctk.CTkCheckBox(presets_grid, text="🍲 Cooking & Food (Recipes, Street Food, Kitchen)", font=ctk.CTkFont(size=13))
        self.cb_cooking.grid(row=0, column=1, padx=10, pady=6, sticky="w")
        if "cooking" in active_cats: self.cb_cooking.select()

        self.cb_cartoon = ctk.CTkCheckBox(presets_grid, text="🎬 Cartoon & Kids (Animation, Tom & Jerry, Disney)", font=ctk.CTkFont(size=13))
        self.cb_cartoon.grid(row=1, column=0, padx=10, pady=6, sticky="w")
        if "cartoon" in active_cats: self.cb_cartoon.select()

        self.cb_anime = ctk.CTkCheckBox(presets_grid, text="🎌 Anime & Manga (Anime Series, Manga, Ghibli)", font=ctk.CTkFont(size=13))
        self.cb_anime.grid(row=1, column=1, padx=10, pady=6, sticky="w")
        if "anime" in active_cats: self.cb_anime.select()

        self.cb_scifi = ctk.CTkCheckBox(presets_grid, text="🚀 Science Fiction & Space (Cosmos, Astrophysics, NASA)", font=ctk.CTkFont(size=13))
        self.cb_scifi.grid(row=2, column=0, padx=10, pady=6, sticky="w")
        if "scifi" in active_cats: self.cb_scifi.select()

        self.cb_tech = ctk.CTkCheckBox(presets_grid, text="💻 Technology & Software (DevOps, Linux, Cloud, Hardware)", font=ctk.CTkFont(size=13))
        self.cb_tech.grid(row=2, column=1, padx=10, pady=6, sticky="w")
        if "tech" in active_cats: self.cb_tech.select()

        self.cb_music = ctk.CTkCheckBox(presets_grid, text="🎵 Music & Audio (Lo-Fi, Beats, Soundtracks, Songs)", font=ctk.CTkFont(size=13))
        self.cb_music.grid(row=3, column=0, padx=10, pady=6, sticky="w")
        if "music" in active_cats: self.cb_music.select()

        self.cb_sports = ctk.CTkCheckBox(presets_grid, text="🏏 Sports & Fitness (Cricket, Football, Gym, Workout)", font=ctk.CTkFont(size=13))
        self.cb_sports.grid(row=3, column=1, padx=10, pady=6, sticky="w")
        if "sports" in active_cats: self.cb_sports.select()

        # Custom Keyword Entry
        custom_input_frame = ctk.CTkFrame(pref_card, fg_color="#0f172a", corner_radius=10)
        custom_input_frame.pack(fill="x", padx=20, pady=(10, 12))

        ctk.CTkLabel(
            custom_input_frame, 
            text="Add Custom Allowed Topic / Keyword:", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#cbd5e1"
        ).pack(anchor="w", padx=14, pady=(8, 4))

        input_row = ctk.CTkFrame(custom_input_frame, fg_color="transparent")
        input_row.pack(fill="x", padx=14, pady=(0, 8))

        self.custom_entry = ctk.CTkEntry(
            input_row, 
            placeholder_text="e.g. chess, documentary, podcast, woodworking, machine learning...",
            font=ctk.CTkFont(size=12),
            height=34
        )
        self.custom_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.custom_entry.bind("<Return>", lambda e: self._add_custom_keyword())

        add_btn = ctk.CTkButton(
            input_row, 
            text="+ Add Keyword", 
            font=ctk.CTkFont(size=12, weight="bold"),
            width=110, 
            height=34,
            command=self._add_custom_keyword
        )
        add_btn.pack(side="right")

        self.custom_chips_frame = ctk.CTkFrame(custom_input_frame, fg_color="transparent")
        self.custom_chips_frame.pack(fill="x", padx=14, pady=(0, 8))
        self._render_custom_chips()

        # PROMINENT DEDICATED SAVE BUTTON INSIDE PREFERENCES CARD
        save_action_container = ctk.CTkFrame(pref_card, fg_color="#131b2e", corner_radius=10, border_width=1, border_color="#10b981")
        save_action_container.pack(fill="x", padx=20, pady=(4, 16))

        save_btn_row = ctk.CTkFrame(save_action_container, fg_color="transparent")
        save_btn_row.pack(fill="x", padx=14, pady=10)

        self.save_btn = ctk.CTkButton(
            save_btn_row,
            text="💾 SAVE PREFERENCES & APPLY TO YOUTUBE NOW",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            fg_color="#059669",
            hover_color="#047857",
            command=self._save_preferences_and_trigger
        )
        self.save_btn.pack(fill="x", expand=True)

        self.save_feedback_lbl = ctk.CTkLabel(
            save_action_container,
            text="Clicking Save will instantly trigger your preferences and blur other videos across YouTube.",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8"
        )
        self.save_feedback_lbl.pack(pady=(0, 8))

        # Card C: Real-Time Link & Title Video Analyzer
        tester_card = ctk.CTkFrame(content_frame, corner_radius=14, fg_color="#1e293b", border_width=1, border_color="#334155")
        tester_card.pack(fill="x", pady=(0, 14))

        test_header = ctk.CTkFrame(tester_card, fg_color="transparent")
        test_header.pack(fill="x", padx=20, pady=(16, 6))

        ctk.CTkLabel(
            test_header, 
            text="🔗 YouTube Video Link & Title Analyzer", 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f8fafc"
        ).pack(anchor="w")

        ctk.CTkLabel(
            test_header, 
            text="Paste any YouTube URL or video title to preview Laya's instant Red (Blocked) or Green (Allowed) judgment.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        ).pack(anchor="w")

        test_input_row = ctk.CTkFrame(tester_card, fg_color="transparent")
        test_input_row.pack(fill="x", padx=20, pady=(10, 12))

        self.test_link_entry = ctk.CTkEntry(
            test_input_row,
            placeholder_text="Paste YouTube URL or title here (e.g. 'https://youtube.com/watch?v=...' or 'Python DSA Tutorial')...",
            font=ctk.CTkFont(size=13),
            height=40
        )
        self.test_link_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.test_link_entry.bind("<Return>", lambda e: self._analyze_link())

        analyze_btn = ctk.CTkButton(
            test_input_row, 
            text="⚡ Analyze Video", 
            font=ctk.CTkFont(size=13, weight="bold"),
            width=140, 
            height=40,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self._analyze_link
        )
        analyze_btn.pack(side="right")

        # Visual Result Box (Red or Green Card)
        self.result_box = ctk.CTkFrame(tester_card, fg_color="#0f172a", corner_radius=12, border_width=2, border_color="#334155")
        self.result_box.pack(fill="x", padx=20, pady=(0, 16))

        self.verdict_badge = ctk.CTkLabel(
            self.result_box,
            text="READY TO ANALYZE",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#94a3b8"
        )
        self.verdict_badge.pack(pady=(12, 4))

        self.title_display_label = ctk.CTkLabel(
            self.result_box,
            text="Paste a link or title above to test the decision model.",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f8fafc",
            wraplength=840
        )
        self.title_display_label.pack(pady=4)

        self.category_badge = ctk.CTkLabel(
            self.result_box,
            text="Category: Pending Analysis",
            font=ctk.CTkFont(size=12),
            text_color="#cbd5e1"
        )
        self.category_badge.pack(pady=2)

        self.meta_label = ctk.CTkLabel(
            self.result_box,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8"
        )
        self.meta_label.pack(pady=(2, 12))

        # ----------------- 3. Bottom Action Bar -----------------
        footer_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#0f172a", border_width=1, border_color="#1e293b")
        footer_frame.grid(row=2, column=0, padx=22, pady=(6, 18), sticky="ew")

        yt_launch_btn = ctk.CTkButton(
            footer_frame,
            text="🌐 Open YouTube in Browser",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            command=lambda: webbrowser.open("https://youtube.com")
        )
        yt_launch_btn.pack(side="left", padx=16, pady=10)

        mock_test_btn = ctk.CTkButton(
            footer_frame,
            text="🧪 Open Simulation Test Page",
            font=ctk.CTkFont(size=12),
            height=36,
            fg_color="#334155",
            hover_color="#475569",
            command=lambda: webbrowser.open(os.path.abspath(os.path.join(os.path.dirname(__file__), "test_youtube_mock.html")))
        )
        mock_test_btn.pack(side="left", padx=6, pady=10)

    # ----------------- Preference Logic -----------------
    def _preset_study_only(self):
        self.cb_study.select()
        self.cb_cooking.deselect()
        self.cb_cartoon.deselect()
        self.cb_anime.deselect()
        self.cb_scifi.deselect()
        self.cb_tech.deselect()
        self.cb_music.deselect()
        self.cb_sports.deselect()

    def _preset_select_all(self):
        self.cb_study.select()
        self.cb_cooking.select()
        self.cb_cartoon.select()
        self.cb_anime.select()
        self.cb_scifi.select()
        self.cb_tech.select()
        self.cb_music.select()
        self.cb_sports.select()

    def _preset_clear_all(self):
        self.cb_study.deselect()
        self.cb_cooking.deselect()
        self.cb_cartoon.deselect()
        self.cb_anime.deselect()
        self.cb_scifi.deselect()
        self.cb_tech.deselect()
        self.cb_music.deselect()
        self.cb_sports.deselect()

    def _on_shield_toggle(self):
        enabled = self.shield_switch.get() == 1
        self.preferences["shield_enabled"] = enabled
        if enabled:
            self.shield_switch.configure(text="SHIELD ON")
            self.toggle_desc_lbl.configure(text="Active: Automatically blurs all videos & Shorts on YouTube that do not match your allowed preferences.")
        else:
            self.shield_switch.configure(text="SHIELD OFF")
            self.toggle_desc_lbl.configure(text="Disabled: All videos remain visible and unblurred on YouTube.")
        self.engine.save_preferences(self.preferences)

    def _save_preferences_and_trigger(self):
        """Saves preferences and triggers automatic real-time blur update across YouTube."""
        active = []
        if self.cb_study.get(): active.append("study")
        if self.cb_cooking.get(): active.append("cooking")
        if self.cb_cartoon.get(): active.append("cartoon")
        if self.cb_anime.get(): active.append("anime")
        if self.cb_scifi.get(): active.append("scifi")
        if self.cb_tech.get(): active.append("tech")
        if self.cb_music.get(): active.append("music")
        if self.cb_sports.get(): active.append("sports")

        self.preferences["active_categories"] = active
        self.preferences["shield_enabled"] = (self.shield_switch.get() == 1)
        self.preferences["updated_at"] = time.time()

        # 1. Save locally to file
        self.engine.save_preferences(self.preferences)

        # 2. Push to local FastAPI backend to broadcast
        def push_to_api():
            try:
                requests.post("http://127.0.0.1:8000/preferences", json={
                    "shield_enabled": self.preferences["shield_enabled"],
                    "active_categories": self.preferences["active_categories"],
                    "custom_keywords": self.preferences.get("custom_keywords", [])
                }, timeout=1)
            except Exception:
                pass

        threading.Thread(target=push_to_api, daemon=True).start()

        # 3. Dynamic visual feedback
        allowed_str = ", ".join([c.title() for c in active]) if active else "None (All Blurred)"
        self.save_feedback_lbl.configure(
            text=f"✅ Preferences Saved & Triggered! Allowed: {allowed_str}. Other videos are now blurring on YouTube.",
            text_color="#34d399"
        )
        self.save_btn.configure(text="✔ PREFERENCES SAVED & TRIGGERED!", fg_color="#047857")

        def reset_btn():
            time.sleep(2.5)
            try:
                self.save_btn.configure(text="💾 SAVE PREFERENCES & APPLY TO YOUTUBE NOW", fg_color="#059669")
                self.save_feedback_lbl.configure(
                    text="Clicking Save will instantly trigger your preferences and blur other videos across YouTube.",
                    text_color="#94a3b8"
                )
            except Exception:
                pass

        threading.Thread(target=reset_btn, daemon=True).start()

    def _add_custom_keyword(self):
        kw = self.custom_entry.get().strip()
        if not kw: return
        curr = self.preferences.get("custom_keywords", [])
        if kw.lower() not in [k.lower() for k in curr]:
            curr.append(kw)
            self.preferences["custom_keywords"] = curr
            self.engine.save_preferences(self.preferences)
            self.custom_entry.delete(0, "end")
            self._render_custom_chips()

    def _remove_custom_keyword(self, kw):
        curr = self.preferences.get("custom_keywords", [])
        if kw in curr:
            curr.remove(kw)
            self.preferences["custom_keywords"] = curr
            self.engine.save_preferences(self.preferences)
            self._render_custom_chips()

    def _render_custom_chips(self):
        for widget in self.custom_chips_frame.winfo_children():
            widget.destroy()

        kws = self.preferences.get("custom_keywords", [])
        if not kws:
            ctk.CTkLabel(
                self.custom_chips_frame, 
                text="No custom keywords added yet.", 
                font=ctk.CTkFont(size=11, slant="italic"),
                text_color="#64748b"
            ).pack(anchor="w", pady=4)
            return

        chip_container = ctk.CTkFrame(self.custom_chips_frame, fg_color="transparent")
        chip_container.pack(fill="x", pady=4)

        for kw in kws:
            chip = ctk.CTkFrame(chip_container, fg_color="#334155", corner_radius=15)
            chip.pack(side="left", padx=4, pady=4)

            ctk.CTkLabel(chip, text=f"🏷️ {kw}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#f8fafc").pack(side="left", padx=(10, 4), pady=4)

            remove_btn = ctk.CTkButton(
                chip, text="✕", font=ctk.CTkFont(size=10, weight="bold"),
                width=18, height=18, corner_radius=9,
                fg_color="transparent", hover_color="#ef4444",
                command=lambda k=kw: self._remove_custom_keyword(k)
            )
            remove_btn.pack(side="right", padx=(2, 6), pady=4)

    def _analyze_link(self):
        input_text = self.test_link_entry.get().strip()
        if not input_text:
            messagebox.showinfo("Enter Link or Title", "Please paste a YouTube URL or type a video title first.")
            return

        title = input_text
        channel = ""

        # Auto-resolve title if user gave a YouTube URL
        if "youtube.com" in input_text or "youtu.be" in input_text:
            try:
                oembed_url = f"https://www.youtube.com/oembed?url={input_text}&format=json"
                r = requests.get(oembed_url, timeout=3)
                if r.status_code == 200:
                    d = r.json()
                    title = d.get("title", input_text)
                    channel = d.get("author_name", "")
            except Exception:
                pass

        result = self.engine.decide(title=title, channel=channel)
        conf_pct = round(result.confidence * 100, 1)

        self.title_display_label.configure(text=f'"{title}"' + (f' • Channel: {channel}' if channel else ''))
        self.category_badge.configure(text=f"Detected Category: {result.category}")

        if result.is_allowed:
            # 🟢 GREEN VERDICT (YOU CAN WATCH / NOT BLURRED)
            self.result_box.configure(border_color="#10b981", fg_color="#064e3b")
            self.verdict_badge.configure(
                text="🟢 YOU CAN WATCH (ALLOWED)",
                text_color="#34d399"
            )
            self.meta_label.configure(
                text=f"{result.explanation} | Confidence: {conf_pct}% | Decision Latency: {result.latency_ms} ms (Laya Offline)",
                text_color="#a7f3d0"
            )
        else:
            # 🔴 RED VERDICT (DO NOT WATCH / BLURRED)
            self.result_box.configure(border_color="#ef4444", fg_color="#450a0a")
            self.verdict_badge.configure(
                text="🔴 DO NOT WATCH (BLURRED DISTRACTION)",
                text_color="#f87171"
            )
            self.meta_label.configure(
                text=f"{result.explanation} | Confidence: {conf_pct}% | Decision Latency: {result.latency_ms} ms (Laya Offline)",
                text_color="#fca5a5"
            )

if __name__ == "__main__":
    app = StudyShieldApp()
    app.mainloop()
