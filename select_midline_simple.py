import cv2
import numpy as np
from ultralytics import YOLO
from court.midline_manager import load_midline, has_midline

VIDEO_PATH = "data/videos/sin2.mp4"
MODEL_PATH = "yolov8n.pt"
DISPLAY_SCALE = 0.6
player_baseline_side = {}
BASELINE_FRAMES = 5
baseline_counter = {}
RAIDER_MISSING_TOLERANCE = 60
raider_missing_counter = 0
last_raider_bbox = None
last_raider_position = None

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
    A = p2[1] - p1[1]
    B = p1[0] - p2[0]
    C = p2[0] * p1[1] - p1[0] * p2[1]
    return abs(A * x + B * y + C) / np.sqrt(A * A + B * B)

# ---------------- RAID STATE ---------------- #

raider_track_id = None
raider_start_side = None
raid_active = False

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

            if (
                not raid_active
                and baseline_counter.get(tid, 0) >= BASELINE_FRAMES
                and side != player_baseline_side[tid]
            ):
                raider_track_id = tid
                raider_start_side = player_baseline_side[tid]
                raid_active = True
                raid_start_frame = frame_count
                print(f"Raid START | Raider ID {tid} | Frame {raid_start_frame}")

            # TRACK RAIDER
            if raid_active and tid == raider_track_id:
                raider_missing_counter = 0
                last_raider_bbox = (x1, y1, x2, y2)
                last_raider_position = (cx, cy)

                cv2.rectangle(frame,(x1,y1),(x2,y2),(0,0,255),2)
                cv2.putText(frame,"RAIDER",(x1,y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)

                if side == raider_start_side:
                    print(f"Raid END | Frame {frame_count}")
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
        
        if results and results[0].boxes.id is not None:
            for box in results[0].boxes:
                tid = int(box.id[0])
                if tid == raider_track_id:
                    raider_found_this_frame = True
                    break
        
        # Find player closest to midline
        if not raider_found_this_frame:
            best_candidate = None
            min_midline_distance = float('inf')
            
            if results and results[0].boxes.id is not None:
                for box in results[0].boxes:
                    x1,y1,x2,y2 = map(int, box.xyxy[0])
                    tid = int(box.id[0])
                    cx = (x1 + x2)//2
                    cy = (y1 + y2)//2
                    current_side = point_side(p1, p2, cx, cy)
                    
                    if current_side == raider_start_side:
                        continue
                    
                    midline_dist = distance_to_midline(p1, p2, cx, cy)
                    if midline_dist < min_midline_distance and midline_dist < 80:
                        min_midline_distance = midline_dist
                        best_candidate = tid
            
            if best_candidate:
                print(f"🔄 Raider ID switched: {raider_track_id} → {best_candidate}")
                raider_track_id = best_candidate
                raider_found_this_frame = True
        
        if not raider_found_this_frame:
            raider_missing_counter += 1
        else:
            raider_missing_counter = 0
        
        if raider_missing_counter > 0:
            status_text = f"SEARCHING RAIDER ({raider_missing_counter}/{RAIDER_MISSING_TOLERANCE})"
            cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,165,255), 2)
        
        if raider_missing_counter > RAIDER_MISSING_TOLERANCE:
            print("⚠ Raider lost permanently, ending raid")
            raid_active = False
            raider_track_id = None
            raider_start_side = None
            raider_missing_counter = 0
            last_raider_bbox = None
            last_raider_position = None

    if raid_active:
        status = f"RAID ACTIVE - Raider ID: {raider_track_id}"
        cv2.putText(frame, status, (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
    
    # Save frame instead of display
    if frame_count % 30 == 0:
        cv2.imwrite(f"output_frame_{frame_count}.jpg", frame)
        print(f"Frame {frame_count} processed")

cap.release()
print("✅ Processing complete!")