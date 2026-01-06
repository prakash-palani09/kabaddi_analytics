import cv2
import json

VIDEO_PATH = "data/videos/match_01.mp4"
OUTPUT_JSON = "court/court_config.json"

points = []
midline_points = []
mode = "court"  # "court" or "midline"

def mouse_callback(event, x, y, flags, param):
    global points, midline_points, mode

    if event == cv2.EVENT_LBUTTONDOWN:
        if mode == "court":
            points.append([x, y])
            print(f"Court point added: {x}, {y}")
        elif mode == "midline":
            midline_points.append([x, y])
            print(f"Midline point added: {x}, {y}")

cap = cv2.VideoCapture(VIDEO_PATH)
ret, frame = cap.read()
cap.release()

if not ret:
    print("❌ Cannot read video")
    exit()

clone = frame.copy()
cv2.namedWindow("Define Court")
cv2.setMouseCallback("Define Court", mouse_callback)

print("INSTRUCTIONS:")
print("1️⃣ Click 4 corners of the COURT (clockwise)")
print("2️⃣ Press 'm' to switch to MIDLINE mode")
print("3️⃣ Click 2 points on the MIDLINE")
print("4️⃣ Press 's' to save and exit")

while True:
    temp = clone.copy()

    for p in points:
        cv2.circle(temp, tuple(p), 5, (0, 255, 0), -1)

    for p in midline_points:
        cv2.circle(temp, tuple(p), 5, (0, 0, 255), -1)

    cv2.imshow("Define Court", temp)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('m'):
        mode = "midline"
        print("🔁 Switched to MIDLINE mode")

    if key == ord('s'):
        if len(points) >= 4 and len(midline_points) == 2:
            data = {
                "court_polygon": points,
                "midline": {
                    "p1": midline_points[0],
                    "p2": midline_points[1]
                }
            }
            with open(OUTPUT_JSON, "w") as f:
                json.dump(data, f, indent=2)
            print("✅ Court saved to", OUTPUT_JSON)
            break
        else:
            print("❌ Need 4 court points and 2 midline points")

    if key == 27:
        break

cv2.destroyAllWindows()
