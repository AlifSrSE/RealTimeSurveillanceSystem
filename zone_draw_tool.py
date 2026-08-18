import cv2
import json
import os
import numpy as np

zones = []
current_zone = []

def mouse_callback(event, x, y, flags, param):
    global current_zone
    if event == cv2.EVENT_LBUTTONDOWN:
        current_zone.append((x, y))
    elif event == cv2.EVENT_RBUTTONDOWN:
        if len(current_zone) >= 3:
            zones.append({
                "id": f"zone_{len(zones)+1}",
                "type": "restricted",
                "points": current_zone
            })
        current_zone = []

def draw_zones(frame):
    for zone in zones:
        pts = zone["points"]
        cv2.polylines(frame, [np.array(pts, np.int32)], isClosed=True, color=(0, 0, 255), thickness=2)
    if current_zone:
        cv2.polylines(frame, [np.array(current_zone, np.int32)], isClosed=False, color=(255, 0, 0), thickness=1)

def save_zones(camera_name):
    os.makedirs("zones", exist_ok=True)
    config_path = "zones/zone_config.json"
    
    # Load existing config
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            data = json.load(f)
    else:
        data = {}

    data[camera_name] = zones
    with open(config_path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"[✓] Zones saved for {camera_name} to {config_path}")

if __name__ == "__main__":
    camera_name = input("Enter camera ID (e.g., store_front): ")
    video_path = input("Enter video path: ")

    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Failed to load video.")
        exit(0)

    cv2.namedWindow("Draw Zones")
    cv2.setMouseCallback("Draw Zones", mouse_callback)

    while True:
        display_frame = frame.copy()
        draw_zones(display_frame)
        cv2.imshow("Draw Zones", display_frame)

        key = cv2.waitKey(1)
        if key == ord("s"):
            save_zones(camera_name)
            break
        elif key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()
