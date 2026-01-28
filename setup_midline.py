import cv2
from court.midline_manager import save_midline

VIDEO_PATH = "data/videos/sin5.mp4"
DISPLAY_SCALE = 0.6

midline_points = []

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and len(midline_points) < 2:
        midline_points.append(
            (int(x / DISPLAY_SCALE), int(y / DISPLAY_SCALE))
        )
        print(f"Midline point {len(midline_points)}: {midline_points[-1]}")

def setup_midline(video_path):
    cap = cv2.VideoCapture(video_path)
    ret, first_frame = cap.read()
    
    if not ret:
        print("❌ Cannot read video")
        return None
    
    cv2.namedWindow("Setup Midline", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Setup Midline", mouse_callback)
    
    print("👉 Click 2 midline points, press ENTER to save")
    
    while True:
        temp = first_frame.copy()
        for p in midline_points:
            cv2.circle(temp, p, 6, (0,255,255), -1)
        
        if len(midline_points) == 2:
            cv2.line(temp, midline_points[0], midline_points[1], (0,255,255), 2)
        
        display = cv2.resize(temp, None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE)
        cv2.imshow("Setup Midline", display)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 13 and len(midline_points) == 2:  # Enter
            break
        elif key == 27:  # Escape
            cap.release()
            cv2.destroyAllWindows()
            return None
    
    cap.release()
    cv2.destroyAllWindows()
    
    p1, p2 = midline_points
    save_midline(video_path, p1, p2)
    return p1, p2

if __name__ == "__main__":
    result = setup_midline(VIDEO_PATH)
    if result:
        print(f"✅ Midline configured: {result[0]} to {result[1]}")
    else:
        print("❌ Setup cancelled")