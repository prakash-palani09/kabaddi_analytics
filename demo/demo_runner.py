#!/usr/bin/env python3
"""
Kabaddi Analytics - Demo Runner for Review Presentation
Run individual steps to demonstrate project capabilities
"""

import os
import sys

def print_header():
    print("=" * 70)
    print("🏏 KABADDI ANALYTICS - PROJECT DEMONSTRATION")
    print("=" * 70)
    print("Vision-Based Raid Analysis and Player Performance Profiling")
    print()
    print("📋 Available Demonstrations:")
    print()

def print_menu():
    print("1️⃣  Step 1: Basic Player Detection and Tracking")
    print("   • YOLOv8 person detection")
    print("   • Multi-object tracking with persistent IDs")
    print("   • Real-time bounding boxes and statistics")
    print()
    
    print("2️⃣  Step 2: Court Setup and Raid Detection")
    print("   • Interactive midline selection")
    print("   • Player side detection (Blue/Red teams)")
    print("   • Automatic raid start/end detection")
    print()
    
    print("3️⃣  Full Analytics Pipeline")
    print("   • Complete data extraction")
    print("   • Player ranking system")
    print("   • Performance metrics calculation")
    print()
    
    print("4️⃣  Enhanced Tracking (with MediaPipe)")
    print("   • Pose estimation integration")
    print("   • Stable tracking with position smoothing")
    print("   • Advanced movement analysis")
    print()
    
    print("5️⃣  UI Dashboard")
    print("   • Interactive player rankings")
    print("   • Video processing interface")
    print("   • Live process viewer")
    print()
    
    print("0️⃣  Exit")
    print()

def run_step(step_num):
    """Run the selected demonstration step"""
    
    if step_num == 1:
        print("🚀 Running Step 1: Player Detection...")
        os.system("python step1.py")
        
    elif step_num == 2:
        print("🚀 Running Step 2: Court Setup and Raids...")
        os.system("python step2.py")
        
    elif step_num == 3:
        print("🚀 Running Full Analytics Pipeline...")
        os.system("python single_raid_extract.py")
        
    elif step_num == 4:
        print("🚀 Running Enhanced Tracking...")
        # Check if midline exists, if not run setup first
        if not check_midline_setup():
            print("⚠️  No midline found. Running court setup first...")
            os.system("python step2.py")
            print("\n🔄 Now running enhanced tracking...")
        os.system("python enhanced_data_extract.py")
        
    elif step_num == 5:
        print("🚀 Running UI Dashboard...")
        os.system("python ../kabaddi_ui_clean.py")
        
    else:
        print("❌ Invalid selection")
        return False
    
    return True

def check_midline_setup():
    """Check if midline is configured for current video"""
    sys.path.append('..')
    try:
        from court.midline_manager import has_midline
        return has_midline("../data/videos/current_video.mp4")
    except:
        return False

def check_requirements():
    """Check if required files exist"""
    required_files = [
        "../data/videos/current_video.mp4",
        "../yolov8n.pt",
        "step1.py",
        "step2.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("⚠️  Missing required files:")
        for file in missing_files:
            print(f"   • {file}")
        print()
        print("📝 Setup Instructions:")
        print("   1. Place your kabaddi video at: ../data/videos/current_video.mp4")
        print("   2. Ensure YOLOv8 model is downloaded: ../yolov8n.pt")
        print("   3. Run: pip install -r ../requirements.txt")
        print()
        return False
    
    return True

def main():
    print_header()
    
    # Check requirements
    if not check_requirements():
        print("❌ Please fix the missing requirements before running demos.")
        return
    
    print("✅ All requirements satisfied!")
    print()
    
    while True:
        print_menu()
        
        try:
            choice = input("👉 Select demonstration (0-5): ").strip()
            
            if choice == '0':
                print("👋 Thank you for viewing the Kabaddi Analytics demonstration!")
                break
                
            elif choice in ['1', '2', '3', '4', '5']:
                step_num = int(choice)
                print()
                
                if run_step(step_num):
                    print()
                    print("✅ Demonstration completed!")
                    input("Press ENTER to return to menu...")
                
                print("\n" + "="*50 + "\n")
                
            else:
                print("❌ Please enter a number between 0-5")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()