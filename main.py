import os
import time
import signal
import csv
import json
import cv2
import numpy as np
import logging
from datetime import datetime

from db import init_db, insert_log
from detector import PersonDetector
from tracker import CentroidTracker
from line_counter import LineCounter
from pose_utils import PoseDetector
from posture_classifier import PostureClassifier, DemographicsDetector
from object_detector import ObjectDetector
from loitering_detector import LoiteringDetector
from alerts import send_email_alert, send_whatsapp_alert, send_alert
from detectors.zone_intrusion import ZoneIntrusionDetector
from config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def process_camera(camera_id, path, config, headless=False):
    abandoned_objects = {}
    last_alert_times = {}
    zone_grid = tuple(config["zones"]["grid"])

    if not os.path.exists(path):
        logger.error(f"Video file not found: {path}")
        return

    zone_config_path = "zones/zone_config.json"
    if not os.path.exists(zone_config_path):
        os.makedirs("zones", exist_ok=True)
        with open(zone_config_path, "w") as f:
            json.dump({}, f)

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        logger.error(f"Could not open video {path}")
        return

    try:
        detector = PersonDetector(
            model_path=config["detection"]["person_model"],
            conf_threshold=config["detection"]["person_conf_threshold"]
        )
        tracker = CentroidTracker(max_disappeared=config.get("tracker", {}).get("max_disappeared", 10))
        pose_detector = PoseDetector(
            min_detection_confidence=config["pose"]["min_detection_confidence"],
            min_tracking_confidence=config["pose"]["min_tracking_confidence"]
        )
        object_detector = ObjectDetector(
            proto=config["detection"]["object_model_proto"],
            weights=config["detection"]["object_model_weights"],
            conf_thresh=config["detection"]["object_conf_threshold"]
        )
        zone_detector = ZoneIntrusionDetector(zone_config_path="zones/zone_config.json")
        posture_classifier = PostureClassifier(visibility_threshold=config["posture"]["visibility_threshold"])
        demographics_detector = DemographicsDetector(
            age_proto=config["demographics"]["age_proto"],
            age_model=config["demographics"]["age_model"],
            gender_proto=config["demographics"]["gender_proto"],
            gender_model=config["demographics"]["gender_model"]
        )
        loitering_detector = LoiteringDetector(loitering_threshold_sec=config["loitering"]["threshold_sec"])
        counter = LineCounter(line_position=config["line_position"])

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            orig_frame = frame.copy()
            alert_text = ""

            # People detection and tracking
            boxes = detector.detect(frame)
            tracked = tracker.update(boxes)
            counter.update(tracked)

            for (x1, y1, x2, y2) in boxes:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            for (object_id, (cx, cy)) in tracked.items():
                cv2.circle(frame, (cx, cy), 4, (255, 0, 0), -1)
                cv2.putText(frame, str(object_id), (cx, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Update loitering detection
            loitering_alerts = loitering_detector.update(tracked)

            if loitering_alerts:
                for alert in loitering_alerts:
                    alert_type = "loitering"
                    if time.time() - last_alert_times.get(alert_type, 0) >= config["alerts"]["cooldown_sec"]:
                        if config["alerts"]["email"]["enabled"]:
                            send_email_alert("Loitering Alert", alert)
                        if config["alerts"]["whatsapp"]["enabled"]:
                            send_whatsapp_alert(f"Loitering Alert: {alert}")
                        last_alert_times[alert_type] = time.time()

            if not headless:
                cv2.imshow(f"Camera {camera_id}", frame)

            # Inactivity check
            inactive_objects = []
            for obj_id, points in tracker.object_history.items():
                if len(points) >= config["inactivity"]["min_frames"]:
                    xs, ys = zip(*points)
                    if max(xs) - min(xs) < config["inactivity"]["max_pixel_movement"] and max(ys) - min(ys) < config["inactivity"]["max_pixel_movement"]:
                        inactive_objects.append(obj_id)

            # Face blur
            faces = face_cascade.detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 1.3, 5)
            for (x, y, w, h) in faces:
                face_roi = frame[y:y + h, x:x + w]
                face_roi = cv2.GaussianBlur(face_roi, (99, 99), 30)
                frame[y:y + h, x:x + w] = face_roi

            # Pose detection
            pose_result = pose_detector.detect_pose(frame)
            frame = pose_detector.draw_landmarks(frame, pose_result)
            posture = posture_classifier.classify(pose_result.pose_landmarks) if pose_result.pose_landmarks else "Unknown"

            # Posture alert
            if posture == "Lying":
                cv2.putText(frame, "ALERT: Possible Fall!", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
                alert_text += "Fall "

            # Crowd alert
            if len(tracked) > config["alerts"]["crowd_threshold"]:
                cv2.putText(frame, "⚠️ Crowd Alert!", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 100, 255), 2)
                alert_text += "Crowd "

            # Inactivity alert
            if any(obj_id in inactive_objects for obj_id in tracked.keys()):
                alert_text += "Inactivity "

            # Zone counting
            zone_counts = np.zeros(zone_grid, dtype=np.int32)

            frame_height, frame_width = frame.shape[:2]
            zone_height = frame_height // zone_grid[0]
            zone_width = frame_width // zone_grid[1]

            # Track Person Position in Zones
            for (object_id, (cx, cy)) in tracked.items():
                zone_y = min(cy // zone_height, zone_grid[0] - 1)
                zone_x = min(cx // zone_width, zone_grid[1] - 1)
                zone_counts[zone_y, zone_x] += 1

                # Crop the face or upper body of the detected person
                size = config["demographics"]["face_roi_size"]
                y1, y2 = max(0, cy - size), min(frame.shape[0], cy + size)
                x1, x2 = max(0, cx - size), min(frame.shape[1], cx + size)
                face_roi = frame[y1:y2, x1:x2]

                # Get Age and Gender predictions
                if demographics_detector.enabled:
                    age, gender = demographics_detector.detect_age_gender(face_roi)
                    cv2.putText(frame, f"Age: {age}, Gender: {gender}", (cx, cy - 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Line and status info
            cv2.line(frame, (0, counter.line_y), (frame.shape[1], counter.line_y), (0, 0, 255), 2)
            cv2.putText(frame, f"IN: {counter.count_in} | OUT: {counter.count_out}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, f"Camera: {camera_id}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame, f"Posture: {posture}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # Object detection and abandoned object check
            if object_detector.enabled:
                object_boxes = object_detector.detect_objects(frame)
                object_tracked = tracker.update([box for (box, _, _) in object_boxes])

                for obj_id, (cx, cy) in object_tracked.items():
                    if obj_id in abandoned_objects:
                        abandoned_objects[obj_id]["frames"] += 1
                    else:
                        abandoned_objects[obj_id] = {"centroid": (cx, cy), "frames": 1}

                    if abandoned_objects[obj_id]["frames"] > config["alerts"]["abandoned_object_frames"]:
                        alert_text += "Abandoned Object "
                        cv2.putText(frame, "⚠️ ABANDONED OBJECT", (cx, cy + 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Draw zones and detect intrusions
            frame = zone_detector.draw_zones(frame, camera_id)
            tracked_wrapped = {oid: {"centroid": pos} for oid, pos in tracked.items()}
            intrusions = zone_detector.detect_intrusions(camera_id, tracked_wrapped)

            for intrusion in intrusions:
                object_id = intrusion["object_id"]
                zone_id = intrusion["zone_id"]
                centroid = intrusion["centroid"]

                cv2.putText(frame, f"INTRUSION: {zone_id}", tuple(centroid), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                logger.warning(f"Object {object_id} entered restricted zone {zone_id}")
                alert_text += f"Intrusion({zone_id}) "

            # Logging
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            counter.history.append({
                "time": timestamp,
                "in": counter.count_in,
                "out": counter.count_out,
                "posture": posture,
                "alert": alert_text.strip(),
                "camera_id": camera_id
            })

            alert_type = "general"
            if alert_text.strip():
                if time.time() - last_alert_times.get(alert_type, 0) >= config["alerts"]["cooldown_sec"]:
                    if config["alerts"]["email"]["enabled"]:
                        send_email_alert("⚠️ Camera Alert", f"{alert_text.strip()} @ {timestamp}")
                    if config["alerts"]["whatsapp"]["enabled"]:
                        send_whatsapp_alert(f"⚠️ {alert_text.strip()} @ {timestamp}")
                    last_alert_times[alert_type] = time.time()

            # Zone heatmap overlay
            zone_overlay = frame.copy()
            max_count = zone_counts.max() or 1

            for row in range(zone_grid[0]):
                for col in range(zone_grid[1]):
                    x1, y1 = col * zone_width, row * zone_height
                    x2, y2 = x1 + zone_width, y1 + zone_height
                    alpha = zone_counts[row, col] / max_count
                    overlay_color = (0, int(255 * (1 - alpha)), int(255 * alpha))  # blue to red
                    cv2.rectangle(zone_overlay, (x1, y1), (x2, y2), overlay_color, -1)

            frame = cv2.addWeighted(zone_overlay, 0.4, frame, 0.6, 0)

            if not headless:
                cv2.imshow(f"People Flow - {camera_id}", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                # In headless mode, still allow 'q' via non-blocking check if needed
                # but skip GUI entirely to avoid display errors
                pass

        # Saving results
        os.makedirs("logs", exist_ok=True)

        # Save traffic log
        with open(f"logs/traffic_log_{camera_id}.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["time", "in", "out", "camera_id", "posture", "alert"])
            writer.writeheader()
            for entry in counter.history:
                entry["camera_id"] = camera_id
                writer.writerow(entry)

        # Save zone counts
        with open(f"logs/zone_counts_{camera_id}.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Zone(Row,Col)", "Count"])
            for row in range(zone_grid[0]):
                for col in range(zone_grid[1]):
                    writer.writerow([(row, col), zone_counts[row, col]])

        conn = init_db()
        for entry in counter.history:
            entry["camera_id"] = camera_id
            insert_log(conn, entry)
        conn.close()

    finally:
        cap.release()
        if not headless:
            cv2.destroyAllWindows()


def main(headless=False):
    config = load_config()
    init_db()
    cameras = config.get("cameras", {})
    if not cameras:
        logger.warning("No cameras configured in config.yaml")
        return
    for camera_id, path in cameras.items():
        process_camera(camera_id, path, config, headless=headless)


def cleanup_handler(signum, frame):
    raise KeyboardInterrupt

signal.signal(signal.SIGINT, cleanup_handler)

if __name__ == "__main__":
    main()
