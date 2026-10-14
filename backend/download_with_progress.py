"""
StudyShield — High-Performance Direct Streaming Downloader
Downloads model.safetensors with real-time percentage, speed, and ETA tracking.
Updates backend/models/laya/download_status.json for live web viewing.
"""

import os
import sys
import time
import json
import requests

URL = "https://huggingface.co/convaiinnovations/laya/resolve/main/model.safetensors"
TARGET_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "models/laya"))
TARGET_FILE = os.path.join(TARGET_DIR, "model.safetensors")
STATUS_FILE = os.path.join(TARGET_DIR, "download_status.json")

def update_status(downloaded, total, speed, eta, status_text):
    data = {
        "percentage": round((downloaded / total) * 100, 1) if total > 0 else 0,
        "downloaded_mb": round(downloaded / (1024 * 1024), 1),
        "total_mb": round(total / (1024 * 1024), 1),
        "speed_mb_s": round(speed / (1024 * 1024), 2),
        "eta_seconds": int(eta),
        "status": status_text
    }
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

def start_download():
    os.makedirs(TARGET_DIR, exist_ok=True)
    print("==================================================================")
    print("      Laya Model Streaming Downloader (Real-Time Progress)       ")
    print(f" Target File: {TARGET_FILE}")
    print("==================================================================")
    
    update_status(0, 842609210, 0, 0, "Connecting to Hugging Face...")
    
    start_time = time.time()
    last_update_time = start_time
    last_downloaded = 0
    
    headers = {"User-Agent": "StudyShield-Downloader/1.0"}
    
    with requests.get(URL, stream=True, headers=headers, timeout=30) as r:
        r.raise_for_status()
        total_size = int(r.headers.get("content-length", 842609210))
        downloaded = 0
        chunk_size = 1024 * 1024 # 1 MB chunks
        
        with open(TARGET_FILE, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                
                now = time.time()
                if now - last_update_time >= 0.8:
                    speed = (downloaded - last_downloaded) / (now - last_update_time)
                    remaining = total_size - downloaded
                    eta = (remaining / speed) if speed > 0 else 0
                    
                    pct = (downloaded / total_size) * 100
                    mb_done = downloaded / (1024 * 1024)
                    mb_total = total_size / (1024 * 1024)
                    speed_mb = speed / (1024 * 1024)
                    
                    print(f"[{pct:5.1f}%] {mb_done:.1f} / {mb_total:.1f} MB | {speed_mb:.2f} MB/s | ETA: {int(eta)}s", flush=True)
                    
                    update_status(downloaded, total_size, speed, eta, f"Streaming at {speed_mb:.1f} MB/s...")
                    last_update_time = now
                    last_downloaded = downloaded

    total_time = round(time.time() - start_time, 1)
    update_status(total_size, total_size, 0, 0, f"Completed in {total_time}s!")
    print(f"\n[DONE] Model downloaded successfully to {TARGET_FILE} in {total_time}s!")

if __name__ == "__main__":
    start_download()
