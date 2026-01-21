import cv2
from ultralytics import YOLO

VIDEO_PATH = "data/videos/match_01.mp4"

model = YOLO("yolov8n.pt")

cap = cv2.VideoCapture(VIDEO_PATH)

player_id_map = {}

player_metadata = {}

player_count = 0

if not cap.isOpened():
    print("❌ Cannot open video")
    exit()

print("✅ Video opened")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run detection + tracking
    results = model.track(
        frame,
        persist=True,
        conf=0.4,
        classes=[0],   # person
        tracker="bytetrack.yaml"
    )

    if results[0].boxes.id is not None:
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            track_id = int(box.id[0])

            if track_id not in player_id_map:
                player_count += 1
                semantic_id = f"tp{player_count}"

                player_id_map[track_id] = semantic_id
                player_metadata[semantic_id] = {
                    "track_id": [track_id],
                    "first_seen_frame": cap.get(cv2.CAP_PROP_POS_FRAMES),
                }
            else:
                semantic_id = player_id_map[track_id]

            conf = box.conf[0]

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.putText(
                frame,
                semantic_id,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

    cv2.imshow("Player Tracking", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
