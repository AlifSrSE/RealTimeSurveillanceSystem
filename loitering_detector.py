from time import time

class LoiteringDetector:
    def __init__(self, loitering_threshold_sec=300):
        self.loitering_threshold_sec = loitering_threshold_sec
        self.loitering_objects = {}  # object_id -> start_time

    def update(self, tracked_objects):
        alerts = []
        current_time = time()
        active_ids = set(tracked_objects.keys())

        for obj_id in list(self.loitering_objects.keys()):
            if obj_id not in active_ids:
                del self.loitering_objects[obj_id]

        for obj_id, (cx, cy) in tracked_objects.items():
            if obj_id not in self.loitering_objects:
                self.loitering_objects[obj_id] = current_time
            elif current_time - self.loitering_objects[obj_id] >= self.loitering_threshold_sec:
                alerts.append(f"⚠️ Loitering Detected for Object {obj_id}")

        return alerts
