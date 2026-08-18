import numpy as np
import cv2
import logging
from mediapipe.solutions.pose import PoseLandmark

logger = logging.getLogger(__name__)

class PostureClassifier:
    def __init__(self, visibility_threshold=0.5):
        self.prev_state = {}
        self.visibility_threshold = visibility_threshold

    def classify(self, landmarks):
        if landmarks is None:
            return "Unknown"

        def get_point(lm):
            return np.array([lm.x, lm.y]) if lm.visibility > self.visibility_threshold else None

        keypoints = {
            "left_shoulder": get_point(landmarks.landmark[PoseLandmark.LEFT_SHOULDER]),
            "right_shoulder": get_point(landmarks.landmark[PoseLandmark.RIGHT_SHOULDER]),
            "left_hip": get_point(landmarks.landmark[PoseLandmark.LEFT_HIP]),
            "right_hip": get_point(landmarks.landmark[PoseLandmark.RIGHT_HIP]),
            "left_knee": get_point(landmarks.landmark[PoseLandmark.LEFT_KNEE]),
            "right_knee": get_point(landmarks.landmark[PoseLandmark.RIGHT_KNEE]),
        }

        if any(v is None for v in keypoints.values()):
            return "Uncertain"

        shoulders_y = np.mean([keypoints["left_shoulder"][1], keypoints["right_shoulder"][1]])
        hips_y = np.mean([keypoints["left_hip"][1], keypoints["right_hip"][1]])
        knees_y = np.mean([keypoints["left_knee"][1], keypoints["right_knee"][1]])

        shoulder_hip_dist = hips_y - shoulders_y
        hip_knee_dist = knees_y - hips_y
        total_height = knees_y - shoulders_y

        if total_height < 0.15:
            return "Lying"
        elif shoulder_hip_dist < 0.1 and hip_knee_dist > 0.1:
            return "Sitting"
        elif shoulder_hip_dist > 0.1 and hip_knee_dist > 0.1:
            return "Standing"
        else:
            return "Unknown"

class DemographicsDetector:
    def __init__(self, age_proto=None, age_model=None, gender_proto=None, gender_model=None):
        self.enabled = True
        try:
            if all([age_proto, age_model, gender_proto, gender_model]):
                self.age_net = cv2.dnn.readNetFromCaffe(age_proto, age_model)
                self.gender_net = cv2.dnn.readNetFromCaffe(gender_proto, gender_model)
            else:
                self.enabled = False
        except Exception as e:
            logger.warning(f"Failed to load demographics models: {e}")
            self.enabled = False

        self.age_list = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
        self.gender_list = ['Male', 'Female']

    def detect_age_gender(self, frame):
        # Prepare input for the model
        blob = cv2.dnn.blobFromImage(frame, 1, (227, 227), (78.0, 87.0, 114.0), swapRB=False)
        
        # Predict Gender
        self.gender_net.setInput(blob)
        gender_preds = self.gender_net.forward()
        gender = self.gender_list[gender_preds[0].argmax()]

        # Predict Age
        self.age_net.setInput(blob)
        age_preds = self.age_net.forward()
        age = self.age_list[age_preds[0].argmax()]

        return age, gender
