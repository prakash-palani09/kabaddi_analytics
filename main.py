import cv2

VIDEO_PATH = "data/videos/match_01.mp4"

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("❌ ERROR: Cannot open video")
    exit()

print("✅ Video opened successfully")

while True:
    ret, frame = cap.read()
    if not ret:
        print("🎬 End of video")
        break

    cv2.imshow("Kabaddi Video", frame)

    # Press ESC to quit
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
