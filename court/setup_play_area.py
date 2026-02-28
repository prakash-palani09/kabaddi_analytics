#!/usr/bin/env python3
"""
Setup Play Area for Kabaddi
Draw: Play Box (5 corners - PENTAGON), Midline, Baulk Line, Bonus Line
"""

import cv2
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

points = []
current_step = 0
steps = [
    "Click 5 corners of PLAY BOX (pentagon, clockwise)",
    "Click 2 points for MIDLINE (left to right)",
    "Click 2 points for BAULK LINE (left to right)",
    "Click 2 points for BONUS LINE (left to right)",
    "Click 2 points for END LINE (left to right)"
]
points_needed = [5, 2, 2, 2, 2]

def mouse_callback(event, x, y, flags, param):
    global points, current_step
    if event == cv2.EVENT_LBUTTONDOWN and current_step < len(steps):
        points.append((x, y))
        print(f"Point {len(points)}: ({x}, {y})")

if __name__ == "__main__":
    video_path = "../data/videos/jan2.mp4"
    
    if len(sys.argv) >= 2:
        video_path = sys.argv[1]
    
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("Error: Cannot read video")
        sys.exit(1)
    
    print("\n[PLAY AREA SETUP]")
    print("=" * 70)
    print("1. Play Box (5 corners - PENTAGON)")
    print("2. Midline (2 points) - 0m")
    print("3. Baulk Line (2 points) - 3.75m from midline")
    print("4. Bonus Line (2 points) - 4.75m from midline")
    print("5. End Line (2 points) - 6.5m from midline")
    print("=" * 70)
    
    cv2.namedWindow("Setup Play Area", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Setup Play Area", mouse_callback)
    
    play_box = []
    midline = []
    baulk_line = []
    bonus_line = []
    
    while True:
        display = frame.copy()
        
        # Draw all points
        for i, pt in enumerate(points):
            cv2.circle(display, pt, 5, (0, 255, 0), -1)
            cv2.putText(display, str(i+1), (pt[0]+10, pt[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Draw play box (pentagon)
        if len(points) >= 5:
            for i in range(5):
                cv2.line(display, points[i], points[(i+1)%5], (255, 255, 0), 2)
        
        # Draw midline
        if len(points) >= 7:
            cv2.line(display, points[5], points[6], (0, 255, 255), 2)
            cv2.putText(display, "MIDLINE", points[5], cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Draw baulk line
        if len(points) >= 9:
            cv2.line(display, points[7], points[8], (0, 0, 255), 2)
            cv2.putText(display, "BAULK", points[7], cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Draw bonus line
        if len(points) >= 11:
            cv2.line(display, points[9], points[10], (0, 255, 0), 2)
            cv2.putText(display, "BONUS", points[9], cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw end line
        if len(points) >= 13:
            cv2.line(display, points[11], points[12], (255, 0, 255), 2)
            cv2.putText(display, "END LINE", points[11], cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
            cv2.putText(display, "Press ENTER to save", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            # Show current instruction
            total_needed = sum(points_needed[:current_step+1])
            cv2.putText(display, steps[current_step], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(display, f"Points: {len(points)}/{total_needed}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow("Setup Play Area", display)
        
        # Update step
        total_so_far = sum(points_needed[:current_step+1])
        if len(points) >= total_so_far and current_step < len(steps) - 1:
            current_step += 1
        
        key = cv2.waitKey(1)
        if key == 13 and len(points) == 13:  # ENTER
            break
        elif key == 27:  # ESC
            print("\nCancelled")
            cv2.destroyAllWindows()
            sys.exit(0)
    
    cv2.destroyAllWindows()
    
    if len(points) == 13:
        # Save configuration
        config = {
            'play_box': [points[0], points[1], points[2], points[3], points[4]],
            'midline': [points[5], points[6]],
            'baulk_line': [points[7], points[8]],
            'bonus_line': [points[9], points[10]],
            'end_line': [points[11], points[12]]
        }
        
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
        os.makedirs(config_dir, exist_ok=True)
        
        config_file = os.path.join(config_dir, 'play_area.json')
        
        # Load existing configs
        all_configs = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                all_configs = json.load(f)
        
        # Add/update this video's config
        all_configs[video_path] = config
        
        # Save
        with open(config_file, 'w') as f:
            json.dump(all_configs, f, indent=2)
        
        print("\nPlay area saved!")
        print(f"Play Box: {config['play_box']}")
        print(f"Midline: {config['midline']}")
        print(f"Baulk Line: {config['baulk_line']}")
        print(f"Bonus Line: {config['bonus_line']}")
        print(f"End Line: {config['end_line']}")
    else:
        print("\nNeed 13 points total")
