import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from court.midline_manager import has_midline, load_midline
import json

VIDEO_PATH = "data/videos/jan1.mp4"

def has_court_lines(video_path):
    """Check if court lines are configured"""
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'court_lines.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            all_configs = json.load(f)
            return video_path in all_configs
    return False

def main():
    print("🏏 Kabaddi Analytics Pipeline")
    print("=" * 40)
    
    # Check if midline is configured
    if not has_midline(VIDEO_PATH):
        print("⚠️  Midline not configured for this video")
        print("🔧 Setting up midline...")
        os.system("python court/setup_midline.py")
        
        # Check again after setup
        if not has_midline(VIDEO_PATH):
            print("❌ Midline setup failed or cancelled")
            return
    
    # Display midline info
    midline_data = load_midline(VIDEO_PATH)
    print(f"✅ Midline configured: {midline_data['p1']} to {midline_data['p2']}")
    
    # Check if court lines are configured
    if not has_court_lines(VIDEO_PATH):
        print("⚠️  Court lines (baulk/bonus) not configured")
        print("🔧 Setting up court lines...")
        os.system("python court/setup_court_lines.py")
        
        if not has_court_lines(VIDEO_PATH):
            print("⚠️  Court lines not set (optional, continuing anyway)")
    else:
        print("✅ Court lines configured")
    
    print("🚀 Starting raid tracking and data extraction...")
    os.system("python scripts/data_extract.py")

if __name__ == "__main__":
    main()