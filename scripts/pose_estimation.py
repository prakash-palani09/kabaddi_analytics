#!/usr/bin/env python3
"""
Multi-Player Pose Estimation using YOLOv8-Pose
Detects all players and estimates their body pose with keypoints
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import cv2
from ultralytics import YOLO

def pose_estimation_yolo(video_path):
    """Apply YOLOv8-Pose estimation to all detected players"""
    
    # Initialize YOLOv8-Pose model
    model = YOLO("yolov8n-pose.pt")  # Nano pose model
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = 0
    
    print("🎥 Starting YOLOv8-Pose estimation on all players...")
    print("Press ESC to exit, SPACE to pause")
    
    cv2.namedWindow("YOLOv8 Pose Estimation", cv2.WINDOW_NORMAL)
    paused = False
    
    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Run YOLOv8-Pose detection
            results = model(frame, conf=0.3, verbose=False)
            
            # Draw results on frame
            annotated_frame = results[0].plot()
            
            # Count detected players
            player_count = len(results[0].boxes) if results[0].boxes is not None else 0
            
            # Display info
            cv2.putText(annotated_frame, f"Frame: {frame_count} | Players: {player_count}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(annotated_frame, "ESC: Exit | SPACE: Pause", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Display frame
        display_resized = cv2.resize(annotated_frame, (1280, 720))
        cv2.imshow("YOLOv8 Pose Estimation", display_resized)
        
        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == 32:  # SPACE
            paused = not paused
            print("⏸️  Paused" if paused else "▶️  Resumed")
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\n✅ Pose estimation completed!")
    print(f"Total frames processed: {frame_count}")

def main():
    video_path = "data/videos/jan2.mp4"
    
    print("🏏 YOLOv8-Pose Estimation for Kabaddi Players")
    print("=" * 60)
    
    # Check if video exists
    import os
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        print("Please place your kabaddi video at: data/videos/current_video.mp4")
        return
    
    pose_estimation_yolo(video_path)

if __name__ == "__main__":
    main()
