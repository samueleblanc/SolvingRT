"""
The main goal of this class is to find the length of the limb of the targeted muscle
(perpendicular to gravity)
"""

import mediapipe as mp
import cv2
import math
import MathTools


class _PoseDetector:

    def __init__(self, side_seen, exercise, static_image_mode=False, model_complexity=1,
                 enable_segmentation=True, smooth_segmentation=True, min_detection_confidence=0.8, min_tracking_confidence=0.8):
        self.side_seen = side_seen
        self.exercise = exercise
        self.static_image_mode = static_image_mode
        self.model_complexity = model_complexity
        self.enable_segmentation = enable_segmentation
        self.smooth_segmentation = smooth_segmentation
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.pose = mp.solutions.pose.Pose(static_image_mode=self.static_image_mode, model_complexity=self.model_complexity,
                                           enable_segmentation=self.enable_segmentation, smooth_segmentation=self.smooth_segmentation,
                                           min_detection_confidence=self.min_detection_confidence,
                                           min_tracking_confidence=self.min_tracking_confidence)

    def find_position(self, video):
        self.positions = []
        results = self.pose.process(cv2.cvtColor(video, cv2.COLOR_BGR2RGB))
        if results.pose_landmarks:
            for pt, landmarks in enumerate(results.pose_landmarks.landmark):
                height, width, _ = video.shape
                x_axis, y_axis = int(landmarks.x * width), int(landmarks.y * height)
                self.positions.append([pt, x_axis, y_axis])
        return self.positions

    def find_angle(self, pts):
        if self.side_seen == "left" or "right":
            x1, y1 = self.positions[pts[0]][1:]
            x2, y2 = self.positions[pts[1]][1:]
            x3, y3 = self.positions[pts[2]][1:]

        else:
            x1, y1 = self.positions[pts[1]][1:]
            x2, y2 = self.positions[pts[0]][1:]
            x3, y3 = [x2, y1][pts[2]]

        cos_angle = MathTools._law_of_cosine(x1, x2, x3, y1, y2, y3)
        angle = MathTools._rad_to_deg(math.acos(cos_angle))

        return angle

    """
        To do: Find a way to take into consideration shoulder flexion in arms exercises
    """

    def find_angle_gravity(self, pts):
        if self.side_seen == "left" or "right":
            x2, y2 = self.positions[pts[2]][1:]
            x1, y1 = x2, (y2 + 60)
            x3, y3 = self.positions[pts[1]][1:]
        else:
            x2, y2 = self.positions[pts[0]][1:]
            x1, y1 = x2, (y2 + 100)
            x3, y3 = self.positions[pts[2]][1:]

        cos_angle = MathTools._law_of_cosine(x1, x2, x3, y1, y2, y3)
        angle = MathTools._rad_to_deg(math.acos(cos_angle))

        return angle

    # MediaPipe landmarks
    # https://google.github.io/mediapipe/solutions/pose.html
    def weight_position(self):
        if "squat" in self.exercise.lower():
            return {"right": 12, "left": 11}
        elif "deadlift" in self.exercise.lower():
            return {"right": 16, "left": 15}
        elif ("hip" in self.exercise.lower()) or ("bridge" in self.exercise.lower()):
            return {"right": 24, "left": 23}
        elif (self.exercise.muscle.lower() == "chest") or (self.exercise.muscle.lower() == "back") or (self.exercise.muscle.lower() == "deltoids"):
            return {"right": 16, "left": 15}
        else:
            return None

    # Fine length (in percentage of the full limb length in pixels) perpendicular to gravity
    def find_length(self, pts):
        if self.side_seen == "left" or "right":
            weight_pos = _PoseDetector.weight_position(self)
            if weight_pos is None:
                weight_pos_x, weight_pos_y = self.positions[pts[2]][1:]
            else:
                # Use the center of mass between the weight used and the center of mass of the lifter for exercises like squats and deadlifts
                weight_position_x, weight_pos_y = self.positions[weight_pos[self.side_seen]][1:]
                human_cm_x = self.positions[23][1:] if self.side_seen == "left" else self.positions[24][1:]
                weight_pos_x = MathTools._center_of_mass(human_cm_x, self.exercise.athlete.body_weight, weight_position_x, self.exercise.athlete.weight_used)

            total_length = MathTools._pythagorean_theorem(weight_pos_x, self.positions[pts[1]][1], weight_pos_y, self.positions[pts[1]][2])
            effective_length = (abs(weight_pos_x - self.positions[pts[1]][1])) / total_length
        else:
            raise Exception("Only side 'left' and 'right' are currently accepted")

        return effective_length


