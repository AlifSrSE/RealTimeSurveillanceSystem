import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ObjectDetector:
    def __init__(self, proto=None, weights=None, conf_thresh=0.6):
        self.enabled = True
        try:
            if proto and weights:
                self.net = cv2.dnn.readNetFromCaffe(proto, weights)
            else:
                self.net = None
                self.enabled = False
        except Exception as e:
            logger.warning(f"Failed to load object detection model: {e}")
            self.enabled = False
        self.classes = ["background", "aeroplane", "bicycle", "bird", "boat",
                        "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                        "dog", "horse", "motorbike", "person", "pottedplant",
                        "sheep", "sofa", "train", "tvmonitor", "bag"]
        self.conf_thresh = conf_thresh

    def detect_objects(self, frame):
        if not self.enabled or self.net is None:
            return []
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)
        self.net.setInput(blob)
        detections = self.net.forward()
        results = []

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            class_id = int(detections[0, 0, i, 1])
            if confidence > self.conf_thresh:
                if self.classes[class_id] in ["bag", "backpack", "suitcase"]:
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (x1, y1, x2, y2) = box.astype("int")
                    results.append(((x1, y1, x2, y2), self.classes[class_id], confidence))
        return results
