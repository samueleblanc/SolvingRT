"""
MIT License

Copyright (c) [2022] [Samuel Leblanc]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import mediapipe as mp
import cv2
import math
from solvingrt import MathTools


class _PoseDetector:

    def __init__(self, exercise, static_image_mode=False, model_complexity=1,
                 enable_segmentation=True, smooth_segmentation=True,
                 min_detection_confidence=0.4, min_tracking_confidence=0.4):
        self.exercise = exercise
        self.side_seen = self.exercise.athlete.side_seen
        self.exercise_name = self.exercise.name
        self.muscle = self.exercise.muscle
        self.static_image_mode = static_image_mode
        self.model_complexity = model_complexity
        self.enable_segmentation = enable_segmentation
        self.smooth_segmentation = smooth_segmentation
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.pose = mp.solutions.pose.Pose(static_image_mode=self.static_image_mode,
                                           model_complexity=self.model_complexity,
                                           enable_segmentation=self.enable_segmentation,
                                           smooth_segmentation=self.smooth_segmentation,
                                           min_detection_confidence=self.min_detection_confidence,
                                           min_tracking_confidence=self.min_tracking_confidence)

    def find_position(self, video):
        """
        Uses MediaPipe to find where the landmarks are
        https://google.github.io/mediapipe/solutions/pose.html

        :arg video: The video in which to find the landmarks

        :return: An array with the position as landmarks, and the x,y components in pixels
        """
        self.positions = []
        results = self.pose.process(cv2.cvtColor(video, cv2.COLOR_BGR2RGB))
        if results.pose_landmarks:
            for pt, landmarks in enumerate(results.pose_landmarks.landmark):
                height, width, _ = video.shape
                x_axis, y_axis = int(landmarks.x * width), int(landmarks.y * height)
                self.positions.append([x_axis, y_axis])
        return self.positions

    def find_angle(self, pts):
        """
        :arg pts: The array of the three joints to follow

        :return: The angle (°) created between the three points (angle of the moving joint)
        """
        if (self.side_seen.lower() == "left") or (self.side_seen.lower() == "right"):
            x1, y1 = self.positions[pts[0]]
            x2, y2 = self.positions[pts[1]]
            x3, y3 = self.positions[pts[2]]
        elif (self.side_seen.lower() == "front") or (self.side_seen.lower() == "back"):
            if _PoseDetector.is_upper_body(self):
                if self.exercise.right_side is True:
                    x1, y1 = self.positions[14]
                    x2, y2 = self.positions[12]
                    x3, y3 = x2, (y2 + 100)
                else:
                    x1, y1 = self.positions[13]
                    x2, y2 = self.positions[11]
                    x3, y3 = x2, (y2 + 100)
            else:
                raise Exception("Sides 'front' and 'back' are only supported for upper body muscles.")
        else:
            print(f"{self.side_seen} is not a valid input. Options are 'right', 'left', 'front' and 'back'.")
            raise ValueError(self.side_seen)

        cos_angle = MathTools._law_of_cosine(x1, x2, x3, y1, y2, y3)
        angle = MathTools._rad_to_deg(math.acos(cos_angle))

        return angle

    def find_angle_gravity(self, pts):
        """
        :arg pts: The array of the three joints to follow

        :return: The angle (°) created between the moving limb and a line parallel to gravity
        """
        if (self.side_seen.lower() == "left") or (self.side_seen.lower() == "right"):
            x2, y2 = self.positions[pts[2]]
            x1, y1 = x2, (y2 + 60)
            x3, y3 = self.positions[pts[1]]
        else:
            if self.exercise.right_side is True:
                x1, y1 = self.positions[14]
                x2, y2 = self.positions[12]
                x3, y3 = x2, (y2 + 100)
            else:
                x1, y1 = self.positions[13]
                x2, y2 = self.positions[11]
                x3, y3 = x2, (y2 + 100)

        cos_angle = MathTools._law_of_cosine(x1, x2, x3, y1, y2, y3)
        angle = MathTools._rad_to_deg(math.acos(cos_angle))

        return angle

    def weight_position(self):
        """
        :return: The landmark for the coordinates (pixels) approximately where the weight is located
        or None if the weight is located (like most of the time) at the end of the moving limb
        """
        if "squat" in self.exercise_name.lower():
            return {"right": 12, "left": 11}
        elif "deadlift" in self.exercise_name.lower():
            return {"right": 16, "left": 15}
        elif ("hip" in self.exercise_name.lower()) or ("bridge" in self.exercise_name.lower()):
            return {"right": 24, "left": 23}
        elif (self.muscle.lower() == "chest") or (self.muscle.lower() == "back") or (self.muscle.lower() == "deltoids"):
            return {"right": 16, "left": 15}
        else:
            return None

    def is_upper_body(self):
        """
        :return: (boolean) True if the muscle is part of the upper body musculature, False if not
        """
        UPPER = {"chest": True,
                 "back": True,
                 "deltoids": True,
                 "biceps": True,
                 "triceps": True,
                 "quadriceps": False,
                 "hamstrings": False,
                 "glutes": False}
        return UPPER[self.muscle.lower()]

    def find_length(self, pts):
        """
        :arg pts: The array of the three joints to follow

        :return: (float) The length (in percentage of the full limb length in pixels) perpendicular to gravity
        """
        if (self.side_seen == "left") or (self.side_seen == "right"):
            weight_pos = _PoseDetector.weight_position(self)
            if weight_pos is None:
                weight_pos_x, weight_pos_y = self.positions[pts[2]]
            else:
                # Use the center of mass between the weight used and the center of mass of the lifter
                # for exercises like squats and deadlifts
                weight_position_x, weight_pos_y = self.positions[weight_pos[self.side_seen]]
                human_cm_x = self.positions[23][0] if self.side_seen == "left" else self.positions[24][0]
                weight_pos_x = MathTools._center_of_mass(human_cm_x, self.exercise.athlete.body_weight,
                                                         weight_position_x, self.exercise.athlete.weight_used)

            total_length = MathTools._pythagorean_theorem(weight_pos_x, self.positions[pts[1]][0],
                                                          weight_pos_y, self.positions[pts[1]][1])
            effective_length = (abs(weight_pos_x - self.positions[pts[1]][0])) / total_length
        else:
            if self.exercise.right_side is True:
                x1, y1 = self.positions[12]
                x2, y2 = self.positions[16]
                total_length = MathTools._pythagorean_theorem(x1, x2, y1, y2)
                effective_length = abs(self.positions[16][0] - self.positions[12][0]) / total_length
            else:
                x1, y1 = self.positions[11]
                x2, y2 = self.positions[15]
                total_length = MathTools._pythagorean_theorem(x1, x2, y1, y2)
                effective_length = abs(self.positions[15][0] - self.positions[11][0]) / total_length

        return effective_length

        # TODO: Find a way to take into consideration shoulder flexion in arms exercises
        # Will be useful when the length of the muscle will be needed
