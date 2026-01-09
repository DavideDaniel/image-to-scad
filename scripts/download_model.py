"""
Download required models from Hugging Face Hub
Run this after setting up the virtual environment
"""
from huggingface_hub import snapshot_download

def download_models():
    """Download Intel DPT Hybrid Midas model"""
    print("Downloading Intel DPT Hybrid Midas model...")
    model_path = snapshot_download(repo_id="Intel/dpt-hybrid-midas")
    print(f"Model downloaded successfully to: {model_path}")
    return model_path

if __name__ == "__main__":
    download_models()