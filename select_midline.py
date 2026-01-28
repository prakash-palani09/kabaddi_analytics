import cv2
import numpy as np
from ultralytics import YOLO
from court.midline_manager import load_midline, has_midline
import easyocr

VIDEO_PATH = "data/videos/sin5.mp4"
MODEL_PATH = "yolov8n.pt"
DISPLAY_SCALE = 0.6
player_baseline_side = {}   # track_id → initial side
BASELINE_FRAMES = 5         # frames to confirm baseline
baseline_counter = {}       # track_id → count
RAIDER_MISSING_TOLERANCE = 100   # frames (~1 sec)
raider_missing_counter = 0
last_raider_bbox = None
last_raider_position = None
switch_cooldown = 0  # Prevent frequent switching

# OCR reader for jersey numbers
ocr_reader = easyocr.Reader(['en'], gpu=False)

# ---------------- LOAD SAVED MIDLINE ---------------- #

if has_midline(VIDEO_PATH):
    midline_data = load_midline(VIDEO_PATH)
    p1, p2 = midline_data["p1"], midline_data["p2"]
    print(f"✅ Using saved midline: {p1} to {p2}")
else:
    print("❌ No saved midline found!")
    print("👉 Run 'python setup_midline.py' first to configure midline")
    exit()

# ---------------- LOAD MODEL ---------------- #

cap = cv2.VideoCapture(VIDEO_PATH)
model = YOLO(MODEL_PATH)

FPS = cap.get(cv2.CAP_PROP_FPS)
frame_count = 0

def point_side(p1, p2, x, y):
    return np.sign(
        (p2[0] - p1[0]) * (y - p1[1]) -
        (p2[1] - p1[1]) * (x - p1[0])
    )

def distance_to_midline(p1, p2, x, y):
    """Calculate perpendicular distance from point to midline"""
    A = p2[1] - p1[1]
    B = p1[0] - p2[0]
    C = p2[0] * p1[1] - p1[0] * p2[1]
    return abs(A * x + B * y + C) / np.sqrt(A * A + B * B)

def detect_jersey_number(frame, x1, y1, x2, y2):
    """Detect jersey number from player bounding box"""
    try:
        # Extract chest area (upper torso)
        h = y2 - y1
        chest_crop = frame[y1 + int(0.2*h):y1 + int(0.6*h), x1:x2]
        
        if chest_crop.size == 0:
            return None
            
        # Enhance contrast for better OCR
        gray = cv2.cvtColor(chest_crop, cv2.COLOR_BGR2GRAY)
        enhanced = cv2.equalizeHist(gray)
        
        # OCR detection
        results = ocr_reader.readtext(enhanced, allowlist='0123456789')
        
        for (bbox, text, conf) in results:
            if conf > 0.5 and text.strip() == '5':
                return '5'
        return None
    except:
        return None

# ---------------- RAID STATE ---------------- #

raider_track_id = None
raider_start_side = None
raid_active = False
raid_count = 0

# Create output directory
os.makedirs("sample_output_frame", exist_ok=True)

# ---------------- PROCESS VIDEO ---------------- #

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    cv2.line(frame, p1, p2, (0,255,255), 2)

    results = model.track(
        frame,
        persist=True,
        conf=0.4,
        classes=[0],
        tracker="bytetrack.yaml"
    )

    if results and results[0].boxes.id is not None:
        for box in results[0].boxes:
            x1,y1,x2,y2 = map(int, box.xyxy[0])
            tid = int(box.id[0])

            cx = (x1 + x2)//2
            cy = (y1 + y2)//2
            side = point_side(p1, p2, cx, cy)

            # 🔍 DEBUG DRAW ALL PLAYERS
            cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),1)
            cv2.putText(frame,f"ID {tid}",(x1,y1-5),
                        cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,0),1)

            # RAID START
            if tid not in player_baseline_side:
                player_baseline_side[tid] = side
                baseline_counter[tid] = 1
            else:
                if side == player_baseline_side[tid]:
                    baseline_counter[tid] += 1

            # ---------- SELECT RAIDER (ONLY FROM BASELINE → CROSS) ----------
            if (
                not raid_active
                and baseline_counter.get(tid, 0) >= BASELINE_FRAMES
                and side != player_baseline_side[tid]
            ):
                raider_track_id = tid
                raider_start_side = player_baseline_side[tid]
                raid_active = True
                raid_start_frame = frame_count
                raid_count += 1

                print(
                    f"Raid START | Raider ID {tid} | "
                    f"From side {raider_start_side} | Frame {raid_start_frame}"
                )
                
                # Save raid start frame
                cv2.imwrite(f"sample_output_frame/raid_{raid_count}_start_frame_{frame_count}.jpg", frame)

            # TRACK RAIDER
            if raid_active and tid == raider_track_id:
                # Raider is visible this frame
                raider_missing_counter = 0
                last_raider_bbox = (x1, y1, x2, y2)
                last_raider_position = (cx, cy)

                cv2.rectangle(frame,(x1,y1),(x2,y2),(0,0,255),2)
                cv2.putText(frame,"RAIDER",(x1,y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)

                # RAID END - only when raider returns to start side
                if side == raider_start_side:
                    print(f"Raid END | Frame {frame_count}")
                    
                    # Save raid end frame
                    cv2.imwrite(f"sample_output_frame/raid_{raid_count}_end_frame_{frame_count}.jpg", frame)
                    
                    raid_active = False
                    raider_track_id = None
                    raider_start_side = None
                    raider_missing_counter = 0
                    last_raider_bbox = None
                    last_raider_position = None
                    player_baseline_side.clear()
                    baseline_counter.clear()
                
    # -------- HANDLE RAIDER LOSS & RECOVERY --------
    if raid_active:
        raider_found_this_frame = False
        switch_cooldown = max(0, switch_cooldown - 1)
        
        # Check if current raider ID is still visible
        if results and results[0].boxes.id is not None:
            for box in results[0].boxes:
                tid = int(box.id[0])
                if tid == raider_track_id:
                    raider_found_this_frame = True
                    break
        
        # Try switching more aggressively when raider is lost
        if not raider_found_this_frame and switch_cooldown == 0 and raider_missing_counter > 5:
            best_candidate = None
            min_midline_distance = float('inf')
            
            if results and results[0].boxes.id is not None:
                for box in results[0].boxes:
                    x1,y1,x2,y2 = map(int, box.xyxy[0])
                    tid = int(box.id[0])
                    cx = (x1 + x2)//2
                    cy = (y1 + y2)//2
                    current_side = point_side(p1, p2, cx, cy)
                    
                    # Only consider players on opponent side
                    if current_side == raider_start_side:
                        continue
                    
                    # Find player closest to midline - more lenient now
                    midline_dist = distance_to_midline(p1, p2, cx, cy)
                    if midline_dist < min_midline_distance and midline_dist < 100:  # More lenient
                        min_midline_distance = midline_dist
                        best_candidate = tid
            
            # Switch if we found any reasonable candidate
            if best_candidate:
                print(f"🔄 Raider ID switched: {raider_track_id} → {best_candidate} (distance: {min_midline_distance:.1f})")
                raider_track_id = best_candidate
                raider_found_this_frame = True
                switch_cooldown = 30  # Shorter cooldown
        
        # Update missing counter
        if not raider_found_this_frame:
            raider_missing_counter += 1
        else:
            raider_missing_counter = 0
        
        # Show tracking status
        if raider_missing_counter > 0:
            status_text = f"SEARCHING RAIDER ({raider_missing_counter}/{RAIDER_MISSING_TOLERANCE})"
            cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,165,255), 2)
            
            # Draw last known position
            if last_raider_bbox:
                x1, y1, x2, y2 = last_raider_bbox
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
        
        # End raid if missing too long
        if raider_missing_counter > RAIDER_MISSING_TOLERANCE:
            print("⚠ Raider lost permanently, ending raid")
            
            # Save raid failure frame
            cv2.imwrite(f"sample_output_frame/raid_{raid_count}_lost_frame_{frame_count}.jpg", frame)
            
            raid_active = False
            raider_track_id = None
            raider_start_side = None
            raider_missing_counter = 0
            last_raider_bbox = None
            last_raider_position = None
            switch_cooldown = 0


    # Show raid status
    if raid_active:
        status = f"RAID ACTIVE - Raider ID: {raider_track_id}"
        cv2.putText(frame, status, (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
    
    try:
        display = cv2.resize(frame,None,fx=DISPLAY_SCALE,fy=DISPLAY_SCALE)
        cv2.imshow("Raid Tracking", display)
        
        if cv2.waitKey(1) & 0xFF == 27:
            break
    except cv2.error:
        # Fallback: save key frames only
        pass

cap.release()
cv2.destroyAllWindows()

print(f"\n=== PROCESSING COMPLETE ===")
print(f"Total raids detected: {raid_count}")
print(f"Key frames saved in: sample_output_frame/")
