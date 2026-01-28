import json
import os

MIDLINE_CONFIG_FILE = "court/midline_config.json"

def save_midline(video_path, p1, p2):
    """Save midline coordinates for a specific video"""
    config = load_all_midlines()
    config[video_path] = {"p1": p1, "p2": p2}
    
    os.makedirs(os.path.dirname(MIDLINE_CONFIG_FILE), exist_ok=True)
    with open(MIDLINE_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✅ Midline saved for {video_path}")

def load_midline(video_path):
    """Load midline coordinates for a specific video"""
    config = load_all_midlines()
    return config.get(video_path)

def load_all_midlines():
    """Load all saved midline configurations"""
    if os.path.exists(MIDLINE_CONFIG_FILE):
        with open(MIDLINE_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def has_midline(video_path):
    """Check if midline exists for a video"""
    return video_path in load_all_midlines()