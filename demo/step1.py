#!/usr/bin/env python3
"""
STEP 1: Basic Player Detection and Tracking
Demonstrates YOLO-based player detection with tracking IDs
"""

import cv2
import numpy as np
from ultralytics import YOLO

def step1_player_detection():
    print("=" * 60)
    print("STEP 1: BASIC PLAYER DETECTION AND TRACKING")
    print("=" * 60)
    print("🎯 Objective: Detect and track kabaddi players using YOLO")
    print("📋 Features:")
    print("   • YOLOv8 person detection")
    print("   • ByteTrack multi-object tracking")
    print("   • Persistent player IDs")
    print("   • Real-time bounding boxes")
    print()
    
    # Load video
    video_path = "../data/videos/current_video.mp4"
    
    try:
        cap = cv2.VideoCapture(video_path)
        model = YOLO("../yolov8n.pt")
        
        print(f"📹 Loading video: {video_path}")
        
        if not cap.isOpened():
            print("❌ Error: Cannot open video file")
            return
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"✅ Video loaded successfully")
        print(f"   📊 Total frames: {total_frames}")
        print(f"   🎬 FPS: {fps:.1f}")
        print()
        print("🚀 Starting player detection...")
        print("   Press ESC to exit")
        print("   Press SPACE to pause/resume")
        print()
        
        cv2.namedWindow("Step 1: Player Detection", cv2.WINDOW_NORMAL)
        
        frame_count = 0
        paused = False
        detected_players = set()
        
        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_count += 1
            
            # Run YOLO detection with tracking
            results = model.track(frame, persist=True, conf=0.4, classes=[0], tracker="bytetrack.yaml")
            
            # Draw detections
            if results and results[0].boxes.id is not None:
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    track_id = int(box.id[0])
                    confidence = float(box.conf[0])
                    
                    detected_players.add(track_id)
                    
                    # Draw bounding box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Draw player info
                    label = f"Player {track_id} ({confidence:.2f})"
                    cv2.putText(frame, label, (x1, y1-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # Draw center point
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
            
            # Display statistics
            stats_text = [
                f"Frame: {frame_count}/{total_frames}",
                f"Players Detected: {len(detected_players)}",
                f"Current Players: {len(results[0].boxes) if results and results[0].boxes.id is not None else 0}",
                f"Status: {'PAUSED' if paused else 'RUNNING'}"
            ]
            
            for i, text in enumerate(stats_text):
                cv2.putText(frame, text, (10, 30 + i*25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Progress bar
            progress = frame_count / total_frames
            bar_width = 400
            bar_height = 20
            bar_x, bar_y = 10, frame.shape[0] - 40
            
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_width * progress), bar_y + bar_height), (0, 255, 0), -1)
            cv2.putText(frame, f"{progress*100:.1f}%", (bar_x + bar_width + 10, bar_y + 15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Display frame
            display_frame = cv2.resize(frame, None, fx=0.6, fy=0.6)
            cv2.imshow("Step 1: Player Detection", display_frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == 32:  # SPACE
                paused = not paused
                print(f"{'⏸️  PAUSED' if paused else '▶️  RESUMED'}")
        
        cap.release()
        cv2.destroyAllWindows()
        
        print()
        print("📊 STEP 1 RESULTS:")
        print(f"   ✅ Total frames processed: {frame_count}")
        print(f"   👥 Unique players detected: {len(detected_players)}")
        print(f"   🎯 Detection confidence: 40%+")
        print()
        print("🎉 Step 1 completed successfully!")
        print("   Next: Step 2 - Court Setup and Midline Detection")
        
    except Exception as e:
        print(f"❌ Error in Step 1: {str(e)}")

if __name__ == "__main__":
    step1_player_detection()