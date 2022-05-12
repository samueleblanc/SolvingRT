"""
The main goal of this class is to find the length of the limb of the targeted muscle
(perpendicular to gravity)
"""

import mediapipe as mp
import cv2
import math
import MathTools


class _PoseDetector:

    def __init__(self, side_seen, draw, static_image_mode=False, model_complexity=1, enable_segmentation=True,
                 smooth_segmentation=True, min_detection_confidence=0.7, min_tracking_confidence=0.5):
        self.side_seen = side_seen
        self.draw = draw
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
        """
            To do: Add landmarks for exercise which the third point is not where the weight is (eg squats)
        """
        pass

