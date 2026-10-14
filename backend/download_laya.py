"""
Script to download official Laya model weights from Hugging Face
Repository: convaiinnovations/laya
Destination: backend/models/laya/
"""

import os
from huggingface_hub import snapshot_download

def download():
    target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "models/laya"))
    os.makedirs(target_dir, exist_ok=True)
    
    print("=" * 65)
    print("  Downloading official Laya Decision Model (convaiinnovations/laya)  ")
    print(f"  Target Local Directory: {target_dir}")
    print("  Model Size: ~803 MB")
    print("=" * 65)

    snapshot_download(
        repo_id="convaiinnovations/laya",
        local_dir=target_dir,
        allow_patterns=[
            "config.json",
            "model.safetensors",
            "tokenizer/*",
            "typed-decisions/*"
        ]
    )
    print("\nDownload complete! Laya weights are now saved locally.")

if __name__ == "__main__":
    download()
