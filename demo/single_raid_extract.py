#!/usr/bin/env python3
"""
Single Raid Data Extractor - Extract penetration and duration from single raid video
"""

import cv2
import numpy as np
from ultralytics import YOLO

def extract_single_raid_data(video_path):
    """Extract penetration, duration, and success from single raid video"""
    
    # Initialize
    model = YOLO("../yolov8n.pt")
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Tracking variables
    positions = []
    frame_count = 0
    raider_detected = False
    
    print("🎥 Processing single raid video...")
    print("📊 Extracting penetration, duration, and success data...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        
        # Detect players
        results = model.track(frame, persist=True, conf=0.4, classes=[0], tracker="bytetrack.yaml")
        
        if results and results[0].boxes.id is not None:
            # Get the most prominent player (largest bounding box)
            max_area = 0
            best_box = None
            
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                area = (x2 - x1) * (y2 - y1)
                if area > max_area:
                    max_area = area
                    best_box = box
            
            if best_box is not None:
                x1, y1, x2, y2 = map(int, best_box.xyxy[0])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                positions.append((cx, cy))
                raider_detected = True
                
                # Draw tracking
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, "RAIDER", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
        
        # Show progress
        if frame_count % 30 == 0:
            print(f"Processing frame {frame_count}...")
    
    cap.release()
    cv2.destroyAllWindows()
    
    if not positions:
        print("❌ No raider detected in video")
        return None, None, None
    
    # Calculate metrics
    duration = frame_count / fps
    
    # Calculate penetration as maximum distance from starting position
    start_pos = positions[0]
    max_penetration = 0
    
    for pos in positions:
        distance = np.sqrt((pos[0] - start_pos[0])**2 + (pos[1] - start_pos[1])**2)
        max_penetration = max(max_penetration, distance)
    
    # Determine success based on penetration depth (simple heuristic)
    success = 1 if max_penetration > 100 else 0  # Success if penetration > 100 pixels
    
    return duration, max_penetration, success

def main():
    video_path = "../data/videos/current_video.mp4"
    
    print("🏏 Single Raid Data Extraction")
    print("=" * 50)
    
    # Check if video exists
    import os
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        print("Please place your single raid video at: data/videos/current_video.mp4")
        return
    
    # Extract data
    duration, penetration, success = extract_single_raid_data(video_path)
    
    if duration is not None and penetration is not None:
        print("\n✅ Extraction Complete!")
        print("=" * 50)
        print(f"📏 Penetration: {penetration:.1f} pixels")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"🎯 Success: {success} ({'Successful' if success == 1 else 'Failed'})")
        print("=" * 50)
        
        # Save to simple format
        with open("single_raid_data.txt", "w") as f:
            f.write(f"Penetration: {penetration:.1f} pixels\n")
            f.write(f"Duration: {duration:.2f} seconds\n")
            f.write(f"Success: {success}\n")
        
        print("💾 Data saved to: single_raid_data.txt")
    else:
        print("❌ Failed to extract data from video")

if __name__ == "__main__":
    main()