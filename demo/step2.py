#!/usr/bin/env python3
"""
STEP 2: Court Setup and Raid Detection
Demonstrates midline setup and basic raid detection logic
"""

import cv2
import numpy as np
import csv
import sys
import os
sys.path.append('..')
from ultralytics import YOLO
from court.midline_manager import load_midline, has_midline, save_midline

def step2_court_and_raids():
    print("=" * 60)
    print("STEP 2: COURT SETUP AND RAID DETECTION")
    print("=" * 60)
    print("🎯 Objective: Setup court midline and detect raid events")
    print("📋 Features:")
    print("   • Interactive midline selection")
    print("   • Player side detection")
    print("   • Raid start/end detection")
    print("   • Real-time raid tracking")
    print()
    
    video_path = "../data/videos/current_video.mp4"
    
    try:
        cap = cv2.VideoCapture(video_path)
        model = YOLO("../yolov8n.pt")
        
        if not cap.isOpened():
            print("❌ Error: Cannot open video file")
            return
        
        print(f"📹 Video loaded: {video_path}")
        
        # Check if midline exists
        if not has_midline(video_path):
            print("⚙️  Setting up court midline...")
            setup_midline_interactive(video_path)
        
        # Load midline
        midline_data = load_midline(video_path)
        p1, p2 = midline_data["p1"], midline_data["p2"]
        
        print(f"✅ Midline loaded: {p1} ↔ {p2}")
        print()
        print("🚀 Starting raid detection...")
        print("   Press ESC to exit")
        print("   Press SPACE to pause/resume")
        print()
        
        cv2.namedWindow("Step 2: Raid Detection", cv2.WINDOW_NORMAL)
        
        # Tracking variables
        frame_count = 0
        player_sides = {}
        side_counts = {}
        raid_active = False
        raider_id = None
        raid_count = 0
        paused = False
        
        def point_side(x, y):
            return np.sign((p2[0] - p1[0]) * (y - p1[1]) - (p2[1] - p1[1]) * (x - p1[0]))
        
        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_count += 1
            
            # Draw midline
            cv2.line(frame, p1, p2, (0, 255, 255), 3)
            cv2.putText(frame, "MIDLINE", (p1[0], p1[1]-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            
            # Track players
            results = model.track(frame, persist=True, conf=0.4, classes=[0], tracker="bytetrack.yaml")
            
            if results and results[0].boxes.id is not None:
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    tid = int(box.id[0])
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    side = point_side(cx, cy)
                    
                    # Track player baseline
                    if tid not in player_sides:
                        player_sides[tid] = side
                        side_counts[tid] = 1
                    elif side == player_sides[tid]:
                        side_counts[tid] += 1
                    
                    # Determine player color based on side
                    if side > 0:
                        color = (255, 0, 0)  # Blue team
                        team = "BLUE"
                    else:
                        color = (0, 0, 255)  # Red team
                        team = "RED"
                    
                    # Draw player
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f"{team} {tid}", (x1, y1-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    cv2.circle(frame, (cx, cy), 4, color, -1)
                    
                    # Raid detection
                    if (not raid_active and 
                        side_counts.get(tid, 0) >= 5 and 
                        side != player_sides[tid]):
                        
                        raider_id = tid
                        raid_active = True
                        raid_count += 1
                        print(f"🏃 RAID {raid_count} STARTED - Player {tid} crossing midline!")
                    
                    # Track active raider
                    if raid_active and tid == raider_id:
                        # Highlight raider
                        cv2.rectangle(frame, (x1-5, y1-5), (x2+5, y2+5), (0, 255, 0), 4)
                        cv2.putText(frame, "RAIDER", (x1, y1-30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 3)
                        
                        # Check raid end
                        if side == player_sides[tid]:
                            print(f"✅ RAID {raid_count} ENDED - Player {tid} returned safely!")
                            raid_active = False
                            raider_id = None
                            player_sides.clear()
                            side_counts.clear()
            
            # Display statistics
            stats = [
                f"Frame: {frame_count}",
                f"Raids Detected: {raid_count}",
                f"Raid Status: {'ACTIVE' if raid_active else 'WAITING'}",
                f"Active Raider: {raider_id if raid_active else 'None'}",
                f"Players Tracked: {len(player_sides)}"
            ]
            
            for i, stat in enumerate(stats):
                color = (0, 255, 0) if raid_active and i == 2 else (255, 255, 255)
                cv2.putText(frame, stat, (10, 30 + i*25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Draw court zones
            cv2.putText(frame, "BLUE ZONE", (50, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 3)
            cv2.putText(frame, "RED ZONE", (frame.shape[1]-200, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            
            # Display frame
            display_frame = cv2.resize(frame, None, fx=0.6, fy=0.6)
            cv2.imshow("Step 2: Raid Detection", display_frame)
            
            # Handle input
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == 32:  # SPACE
                paused = not paused
                print(f"{'⏸️  PAUSED' if paused else '▶️  RESUMED'}")
        
        cap.release()
        cv2.destroyAllWindows()
        
        print()
        print("📊 STEP 2 RESULTS:")
        print(f"   ✅ Frames processed: {frame_count}")
        print(f"   🏃 Total raids detected: {raid_count}")
        print(f"   🎯 Midline coordinates: {p1} to {p2}")
        print(f"   👥 Players tracked: {len(player_sides)}")
        print()
        print("🎉 Step 2 completed successfully!")
        print("   Next: Full analytics pipeline with data extraction")
        
    except Exception as e:
        print(f"❌ Error in Step 2: {str(e)}")

def setup_midline_interactive(video_path):
    """Interactive midline setup"""
    print("🖱️  Click 2 points on the court midline...")
    
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ Cannot read video frame")
        return
    
    midline_points = []
    DISPLAY_SCALE = 0.6
    
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(midline_points) < 2:
            # Convert back to original coordinates
            orig_x = int(x / DISPLAY_SCALE)
            orig_y = int(y / DISPLAY_SCALE)
            midline_points.append((orig_x, orig_y))
            print(f"   Point {len(midline_points)}: ({orig_x}, {orig_y})")
    
    cv2.namedWindow("Setup Midline", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Setup Midline", mouse_callback)
    
    while len(midline_points) < 2:
        temp_frame = frame.copy()
        
        # Draw existing points
        for point in midline_points:
            cv2.circle(temp_frame, point, 8, (0, 255, 255), -1)
        
        # Draw line if we have 2 points
        if len(midline_points) == 2:
            cv2.line(temp_frame, midline_points[0], midline_points[1], (0, 255, 255), 3)
        
        # Instructions
        instruction = f"Click point {len(midline_points)+1}/2 on midline"
        if len(midline_points) == 2:
            instruction = "Press ENTER to save"
        
        cv2.putText(temp_frame, instruction, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display
        display_frame = cv2.resize(temp_frame, None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE)
        cv2.imshow("Setup Midline", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 13 and len(midline_points) == 2:  # ENTER
            break
        elif key == 27:  # ESC
            cv2.destroyAllWindows()
            return
    
    cv2.destroyAllWindows()
    
    if len(midline_points) == 2:
        save_midline(video_path, midline_points[0], midline_points[1])
        print(f"✅ Midline saved: {midline_points[0]} to {midline_points[1]}")

if __name__ == "__main__":
    step2_court_and_raids()