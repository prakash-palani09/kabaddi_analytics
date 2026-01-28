import os
from court.midline_manager import has_midline

VIDEO_PATH = "data/videos/sin2.mp4"

def main():
    print("🏏 Kabaddi Analytics Pipeline")
    print("=" * 40)
    
    # Check if midline is configured
    if not has_midline(VIDEO_PATH):
        print("⚠️  Midline not configured for this video")
        print("🔧 Setting up midline...")
        os.system("python setup_midline.py")
        
        # Check again after setup
        if not has_midline(VIDEO_PATH):
            print("❌ Midline setup failed or cancelled")
            return
    
    print("✅ Midline configured")
    print("🚀 Starting raid tracking...")
    os.system("python select_midline.py")

if __name__ == "__main__":
    main()