import cv2
import numpy as np
from ultralytics import YOLO

# ---------------- CONFIG ---------------- #
VIDEO_PATH = "data/videos/sin2.mp4"
MODEL_PATH = "yolov8n.pt"

WINDOW_NAME = "Manual Midline Setup"
DISPLAY_SCALE = 0.6
# ---------------------------------------- #

# ---------------- GLOBAL STATE ---------------- #
midline_points = []
# --------------------------------------------- #

model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("❌ Cannot open video")
    exit()

print("✅ Video opened")

FPS = cap.get(cv2.CAP_PROP_FPS)
frame_count = 0

# ---------------- MOUSE CALLBACK ---------------- #

def mouse_callback(event, x, y, flags, param):
    global midline_points
    if event == cv2.EVENT_LBUTTONDOWN and len(midline_points) < 2:
        orig_x = int(x / DISPLAY_SCALE)
        orig_y = int(y / DISPLAY_SCALE)
        midline_points.append((orig_x, orig_y))
        print(f"Clicked midline point: {(orig_x, orig_y)}")

# ---------------- WINDOW SETUP ---------------- #

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.setMouseCallback(WINDOW_NAME, mouse_callback)

print("👉 Click TWO points on the midline, then press ENTER")

# ---------------- RAID STATE ---------------- #

raider_track_id = None
raider_start_side = None
raid_active = False
raid_start_frame = None

# -------------------------------------------- #

def point_side(p1, p2, x, y):
    return np.sign(
        (p2[0] - p1[0]) * (y - p1[1]) -
        (p2[1] - p1[1]) * (x - p1[0])
    )

# -------------------------------------------- #

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    # -------- MIDLINE SELECTION MODE -------- #
    if len(midline_points) < 2:
        temp = frame.copy()

        for p in midline_points:
            cv2.circle(temp, p, 6, (0, 255, 255), -1)

        display = cv2.resize(
            temp, None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE
        )
        cv2.imshow(WINDOW_NAME, display)

        if cv2.waitKey(1) == 13 and len(midline_points) == 2:
            print("✅ Midline fixed")
        continue
    # --------------------------------------- #

    p1, p2 = midline_points

    # draw midline
    cv2.line(frame, p1, p2, (0, 255, 255), 2)

    results = model.track(
        frame,
        persist=True,
        conf=0.4,
        classes=[0],
        tracker="bytetrack.yaml"
    )

    if results[0].boxes.id is not None:
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            track_id = int(box.id[0])

            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            side = point_side(p1, p2, cx, cy)

            # -------- SELECT RAIDER (ONCE) -------- #
            if not raid_active:
                if raider_start_side is None:
                    raider_start_side = side
                elif side != raider_start_side:
                    raider_track_id = track_id
                    raid_active = True
                    raid_start_frame = frame_count
                    print(f"Raid START | Frame {raid_start_frame}")
            # -------------------------------------- #

            # -------- TRACK LOCKED RAIDER -------- #
            if raid_active and track_id == raider_track_id:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(
                    frame,
                    "RAIDER",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )

                # RAID END (return crossing)
                if side == raider_start_side:
                    raid_end_frame = frame_count
                    duration = (raid_end_frame - raid_start_frame) / FPS

                    print(
                        f"Raid END | Frame {raid_end_frame} | "
                        f"Duration {duration:.2f}s"
                    )

                    # RESET
                    raider_track_id = None
                    raider_start_side = None
                    raid_active = False
                    raid_start_frame = None
                    break
            # ------------------------------------- #

    # -------- DISPLAY (RESIZED ONLY) -------- #
    display = cv2.resize(
        frame, None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE
    )
    cv2.imshow(WINDOW_NAME, display)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
