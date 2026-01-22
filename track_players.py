import cv2
import numpy as np
from ultralytics import YOLO

VIDEO_PATH = "data/videos/sample_match.mp4"

model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("❌ Cannot open video")
    exit()

print("✅ Video opened")

# ---------------- BLUE JERSEY DETECTION ---------------- #

LOWER_BLUE = np.array([100, 120, 80])
UPPER_BLUE = np.array([130, 255, 255])

def is_blue_jersey(crop):
    if crop is None or crop.size == 0:
        return False

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOWER_BLUE, UPPER_BLUE)

    blue_pixels = np.count_nonzero(mask)
    total_pixels = crop.shape[0] * crop.shape[1]

    blue_ratio = blue_pixels / total_pixels

    return blue_ratio > 0.20   # strict dominance

# ---------------- TEMPORAL STABILITY ---------------- #

blue_confirm_counter = 0
BLUE_CONFIRM_FRAMES = 3

raider_bbox = None

# ----------------------------------------------------- #

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.track(
        frame,
        persist=True,
        conf=0.4,
        classes=[0],   # person only
        tracker="bytetrack.yaml"
    )

    raider_found_this_frame = False

    if results[0].boxes.id is not None:
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # upper torso only (remove face & legs)
            h = y2 - y1
            torso_crop = frame[
                y1 + int(0.3 * h) : y1 + int(0.65 * h),
                x1 : x2
            ]

            if is_blue_jersey(torso_crop):
                raider_found_this_frame = True
                candidate_bbox = (x1, y1, x2, y2)

    # ---------- TEMPORAL CONFIRMATION ----------
    if raider_found_this_frame:
        blue_confirm_counter += 1
    else:
        blue_confirm_counter = max(0, blue_confirm_counter - 1)

    if blue_confirm_counter >= BLUE_CONFIRM_FRAMES:
        raider_bbox = candidate_bbox

    # ---------- DRAW RAIDER ----------
    if raider_bbox is not None:
        x1, y1, x2, y2 = raider_bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
        cv2.putText(
            frame, "RAIDER",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 0),
            2
        )

    cv2.imshow("Raider Tracking (Blue Jersey)", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
