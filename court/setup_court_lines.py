#!/usr/bin/env python3
"""
Interactive Court Lines Setup
Draw baulk line and bonus line within the court square
"""

import cv2
import sys
import os
# From court/ to root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from court.midline_manager import load_midline, has_midline, save_midline
import json

VIDEO_PATH = "data/videos/jan1.mp4"
DISPLAY_SCALE = 0.6

# Store all court lines
court_lines = {
    'midline': None,
    'baulk_line': [],
    'bonus_line': []
}

current_line = 'baulk_line'  # Start with baulk line

def mouse_callback(event, x, y, flags, param):
    global current_line
    
    if event == cv2.EVENT_LBUTTONDOWN:
        # Convert to original coordinates
        orig_x = int(x / DISPLAY_SCALE)
        orig_y = int(y / DISPLAY_SCALE)
        
        if current_line == 'baulk_line' and len(court_lines['baulk_line']) < 2:
            court_lines['baulk_line'].append((orig_x, orig_y))
            print(f"Baulk line point {len(court_lines['baulk_line'])}: ({orig_x}, {orig_y})")
            
            if len(court_lines['baulk_line']) == 2:
                print("✅ Baulk line complete! Now draw bonus line...")
                current_line = 'bonus_line'
        
        elif current_line == 'bonus_line' and len(court_lines['bonus_line']) < 2:
            court_lines['bonus_line'].append((orig_x, orig_y))
            print(f"Bonus line point {len(court_lines['bonus_line'])}: ({orig_x}, {orig_y})")
            
            if len(court_lines['bonus_line']) == 2:
                print("✅ Bonus line complete!")

def setup_court_lines(video_path):
    """Interactive setup for baulk and bonus lines"""
    
    # Load existing midline
    if not has_midline(video_path):
        print("❌ No midline found. Run midline setup first!")
        return None
    
    midline_data = load_midline(video_path)
    court_lines['midline'] = [midline_data['p1'], midline_data['p2']]
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    ret, first_frame = cap.read()
    
    if not ret:
        print("❌ Cannot read video")
        return None
    
    cv2.namedWindow("Setup Court Lines", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Setup Court Lines", mouse_callback)
    
    print("🏏 Court Lines Setup")
    print("=" * 50)
    print("1️⃣  Draw BAULK LINE (2 points)")
    print("2️⃣  Draw BONUS LINE (2 points)")
    print("Press ENTER to save, ESC to cancel")
    print("=" * 50)
    
    while True:
        frame = first_frame.copy()
        
        # Draw midline (yellow)
        cv2.line(frame, court_lines['midline'][0], court_lines['midline'][1], (0, 255, 255), 3)
        cv2.putText(frame, "MIDLINE", 
                   (court_lines['midline'][0][0], court_lines['midline'][0][1] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        # Draw baulk line (red)
        if len(court_lines['baulk_line']) > 0:
            for p in court_lines['baulk_line']:
                cv2.circle(frame, p, 8, (0, 0, 255), -1)
            
            if len(court_lines['baulk_line']) == 2:
                cv2.line(frame, court_lines['baulk_line'][0], court_lines['baulk_line'][1], (0, 0, 255), 3)
                cv2.putText(frame, "BAULK LINE", 
                           (court_lines['baulk_line'][0][0], court_lines['baulk_line'][0][1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # Draw bonus line (green)
        if len(court_lines['bonus_line']) > 0:
            for p in court_lines['bonus_line']:
                cv2.circle(frame, p, 8, (0, 255, 0), -1)
            
            if len(court_lines['bonus_line']) == 2:
                cv2.line(frame, court_lines['bonus_line'][0], court_lines['bonus_line'][1], (0, 255, 0), 3)
                cv2.putText(frame, "BONUS LINE", 
                           (court_lines['bonus_line'][0][0], court_lines['bonus_line'][0][1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Status text
        if current_line == 'baulk_line':
            status = f"Draw BAULK LINE: {len(court_lines['baulk_line'])}/2 points"
            color = (0, 0, 255)
        else:
            status = f"Draw BONUS LINE: {len(court_lines['bonus_line'])}/2 points"
            color = (0, 255, 0)
        
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        if len(court_lines['baulk_line']) == 2 and len(court_lines['bonus_line']) == 2:
            cv2.putText(frame, "Press ENTER to save", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display
        display = cv2.resize(frame, None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE)
        cv2.imshow("Setup Court Lines", display)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 13 and len(court_lines['baulk_line']) == 2 and len(court_lines['bonus_line']) == 2:  # Enter
            break
        elif key == 27:  # Escape
            cap.release()
            cv2.destroyAllWindows()
            return None
    
    cap.release()
    cv2.destroyAllWindows()
    
    return court_lines

def save_court_lines(video_path, court_lines):
    """Save all court lines to config"""
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = os.path.join(config_dir, 'court_lines.json')
    
    # Load existing config or create new
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            all_configs = json.load(f)
    else:
        all_configs = {}
    
    # Save for this video
    all_configs[video_path] = {
        'midline': court_lines['midline'],
        'baulk_line': court_lines['baulk_line'],
        'bonus_line': court_lines['bonus_line']
    }
    
    with open(config_file, 'w') as f:
        json.dump(all_configs, f, indent=2)
    
    print(f"✅ Court lines saved to {config_file}")

def load_court_lines(video_path):
    """Load court lines from config"""
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'court_lines.json')
    
    if not os.path.exists(config_file):
        return None
    
    with open(config_file, 'r') as f:
        all_configs = json.load(f)
    
    return all_configs.get(video_path)

def main():
    print("🏏 Kabaddi Court Lines Setup")
    print("=" * 50)
    
    # Check if video exists
    if not os.path.exists(VIDEO_PATH):
        print(f"❌ Video not found: {VIDEO_PATH}")
        return
    
    # Setup court lines
    result = setup_court_lines(VIDEO_PATH)
    
    if result:
        save_court_lines(VIDEO_PATH, result)
        print("\n✅ Court lines configured successfully!")
        print(f"   Midline: {result['midline']}")
        print(f"   Baulk Line: {result['baulk_line']}")
        print(f"   Bonus Line: {result['bonus_line']}")
    else:
        print("\n❌ Setup cancelled")

if __name__ == "__main__":
    main()
