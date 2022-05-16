"""
File to import to use SolvingRT
"""


import os
import cv2
import numpy
import PoseDetector as pd
import VideoAnalysis as va
import MathTools as mt
from time import perf_counter


class Athlete:

    def __init__(self, height_meter, body_weight_kg, moving_limb_meter, weight_used_kg, side_seen):
        self.height = height_meter
        self.body_weight = body_weight_kg
        self.moving_limb = moving_limb_meter
        self.weight_used = weight_used_kg
        self.side_seen = side_seen
        """
            To do: Side seen could also be front and back
        """

    def inches_to_meter(self):
        self.height = self.height * 0.0254
        self.moving_limb = self.moving_limb * 0.0254

    # Change weight without changing Athlete
    def set_weight_used(self, weight):
        self.weight_used = weight

    def lb_to_kg(self, weight):
        self.weight_used = weight * 0.453592


class Exercise:

    def __init__(self, name, muscle, video, athlete, measures):
        self.name = name
        self.muscle = muscle
        self.video = video
        self.athlete = athlete
        self.measures = measures
        self.draw = True
        self.show_joint_angle = False
        self.show_angle_with_gravity = False
        self.width, self.height = 0, 0
        self.pose = pd._PoseDetector(self.athlete.side_seen, self.name)

    def play_video(self):
        VID = cv2.VideoCapture(self.video)
        POINTS = Exercise._get_pose_landmarks_(self)
        ANALYSIS = va._VideoAnalysis(self.athlete, self)
        frame_counts = 0
        times = []
        angles = []
        concentric_time = 0
        eccentric_time = 0
        # stretched_time = 0
        # shortened_time = 0
        tust = 0  # time under significant tension
        concentric_speed = []  # To measure velocity lost
        conc_velocity = []
        ecc_velocity = []
        conc_power = []
        ecc_power = []
        torque = []
        add_data = False
        time_under_tension = False
        min_max_angles = False
        velocity_lost = False

        # For resistance profile
        res_pro_angles = []
        res_pro_torque = []

        rep_data = []  # Data that is calculated for each rep (eg power and velocity)
        set_data = []  # Data that is calculated for the full set (eg time under tension)

        if self.width or self.height == 0:
            self.height = int(VID.get(cv2.CAP_PROP_FRAME_HEIGHT) / 2)
            self.width = int(VID.get(cv2.CAP_PROP_FRAME_WIDTH) / 2)

        # Count reps
        rep_count = 0
        last_rep = 0
        conc_motion = Exercise._get_muscle_info_(self, "conc_motion")
        is_shortening = Exercise._get_muscle_info_(self, "conc_motion")
        angle_decreasing = Exercise._get_muscle_info_(self, "decreasing")

        while VID.isOpened():
            success, frame = VID.read()
            video = cv2.resize(frame, (self.width, self.height))
            landmarks = self.pose.find_position(video)
            if len(landmarks) > 0:
                x1, y1 = landmarks[POINTS[0]][1:]
                x2, y2 = landmarks[POINTS[1]][1:]
                x3, y3 = landmarks[POINTS[2]][1:]

                frame_counts += 1

                angle = ANALYSIS.angle()
                effective_length = self.pose.find_length(POINTS)

                times += [perf_counter()]
                angles += [angle]

                # Count reps
                if frame_counts % 4 == 0:
                    if is_shortening:
                        if angle_decreasing:
                            if (angle > last_angle) and (last_angle <= 100):
                                rep_count += 0.5
                                is_shortening = False
                            else:
                                concentric_time += 4
                        else:
                            if (angle < last_angle) and (last_angle >= 80):
                                rep_count += 0.5
                                is_shortening = False
                            else:
                                concentric_time += 4
                    else:
                        if angle_decreasing:
                            if angle < last_angle and (last_angle >= 80):
                                rep_count += 0.5
                                is_shortening = True
                            else:
                                eccentric_time += 4
                        else:
                            if angle > last_angle and (last_angle <= 100):
                                rep_count += 0.5
                                is_shortening = True
                            else:
                                eccentric_time += 4
                elif frame_counts % 2 == 0:
                    last_angle = angle

                if (rep_count % 1 == 0) and (rep_count > last_rep):
                    rep_data += [[f"Rep #{int(rep_count)}"]]
                    add_data = True
                    last_rep = rep_count

                for measure in self.measures:
                    if measure == "torque":
                        if frame_counts % 4 == 0:
                            torque += [ANALYSIS.torque(effective_length)]
                        if add_data:
                            rep_data[len(rep_data) - 1] += [f"Torque: {mt._average(torque)} Nm"]
                            torque *= 0

                    elif measure == "power":
                        if frame_counts % 4 == 0:
                            velocity = ANALYSIS.speed(angles, times)
                            power = ANALYSIS.power(velocity, effective_length)
                            if conc_motion:
                                if power < 0:
                                    conc_power += [power]
                                else:
                                    ecc_power += [power]
                            else:
                                if power > 0:
                                    conc_power += [power]
                                else:
                                    ecc_power += [power]
                        # Separates data per rep
                        if add_data:
                            rep_data[len(rep_data) - 1] += [f"Conc. power: {mt._average(conc_power)} W",
                                                            f"Ecc. power: {mt._average(ecc_power)} W"]
                            conc_power *= 0
                            ecc_power *= 0

                    elif measure == "speed":
                        if frame_counts % 4 == 0:
                            velocity = ANALYSIS.speed(angles, times)
                            if conc_motion:
                                if velocity < 0:
                                    conc_velocity += [velocity]
                                else:
                                    ecc_velocity += [velocity]
                            else:
                                if velocity > 0:
                                    conc_velocity += [velocity]
                                else:
                                    ecc_velocity += [velocity]

                        if add_data:
                            avg_conc_vel = mt._average(conc_velocity)
                            avg_ecc_vel = mt._average(ecc_velocity)
                            rep_data[len(rep_data) - 1] += [f"Conc. velocity: {avg_conc_vel} rad/s",
                                                            f"Ecc. velocity: {avg_ecc_vel} rad/s"]
                            concentric_speed += [avg_conc_vel]
                            conc_velocity *= 0
                            ecc_velocity *= 0

                    elif measure == "time under tension":
                        time_under_tension = True
                        tust += ANALYSIS.time_under_tension(effective_length)

                    elif measure == "angles":
                        min_max_angles = True

                    elif measure == "velocity lost":
                        velocity_lost = True

                    elif measure == "tempo":
                        if add_data:
                            conc_time = concentric_time * (perf_counter() / frame_counts)
                            ecc_time = eccentric_time * (perf_counter() / frame_counts)
                            rep_data[len(rep_data) - 1] += [f"Concentric time: {round(conc_time, 4)}",
                                                            f"Eccentric time: {round(ecc_time, 4)}"]
                            concentric_time *= 0
                            eccentric_time *= 0

                    elif measure == "resistance profile":
                        if frame_counts % 4 == 0:
                            res_pro_angles += [angle]
                            res_pro_torque += [ANALYSIS.torque(effective_length)]
                        if add_data:
                            ANALYSIS.resistance_profile(rep_count, res_pro_torque, res_pro_angles)
                            res_pro_angles *= 0
                            res_pro_torque *= 0

                    elif measure == "stimulus":
                        pass

                    elif measure == "EMG":
                        pass

                    elif measure == "motor units":
                        pass

                    else:
                        print(f"'{measure}' is not a valid input")
                        raise ValueError(measure)

                add_data = False

                if self.draw:
                    cv2.line(video, (x1, y1), (x2, y2), (255, 255, 255), 3)
                    cv2.line(video, (x3, y3), (x2, y2), (255, 255, 255), 3)
                    cv2.circle(video, (x1, y1), 8, (255, 0, 0), cv2.FILLED)
                    cv2.circle(video, (x1, y1), 15, (255, 255, 255), 2)
                    cv2.circle(video, (x2, y2), 8, (255, 0, 0), cv2.FILLED)
                    cv2.circle(video, (x2, y2), 15, (255, 255, 255), 2)
                    cv2.circle(video, (x3, y3), 8, (255, 0, 0), cv2.FILLED)
                    cv2.circle(video, (x3, y3), 15, (255, 255, 255), 2)
                if self.show_joint_angle:
                    cv2.putText(video, f"{round(angle)}", (x2 - 70, y2 + 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 2, (255, 0, 0), 2)
                if self.show_angle_with_gravity:
                    if ("deadlift" not in self.name.lower()) and ("squat" not in self.name.lower()):
                        angle_gravity = ANALYSIS.angle_gravity()
                        cv2.putText(video, f"{round(angle_gravity)}", (x3 - 90, y3 + 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 2, (255, 0, 0), 2)
                        cv2.line(video, (x3, (y3 + 8)), (x3, (y3+70)), (255, 255, 255), 3)
                        cv2.putText(video, "V", ((x3-5), (y3+72)), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 3)
                    else:
                        raise Exception(f"Can't show the angle with gravity with a {self.name.lower()}")

            cv2.imshow(f"{str(self.name)} - Calculating {self.measures}", video)
            if cv2.waitKey(1) == 27:  # 27 is escape
                break
        VID.release()
        cv2.destroyAllWindows()
        if time_under_tension:
            tust_in_sec = tust * (perf_counter() / frame_counts)
            set_data += [f"Time under significant tension: {tust_in_sec} s"]
        if min_max_angles:
            set_data += [f"Min angle: {round(min(angles), 4)}", f"Max angle: {round(max(angles), 4)}"]
        if velocity_lost:
            max_vel = max(concentric_speed)
            min_vel = min(concentric_speed)
            vel_lost = round((min_vel / max_vel) * 100, 2)
            set_data += [f"Velocity lost: {vel_lost}%"]
        print(rep_data)
        print(set_data)
        return

    # Change which muscle to analyse without changing Exercise
    def change_muscle(self, new_muscle):
        self.muscle = new_muscle

    def video_resize(self, height, width):
        self.height = int(height)
        self.width = int(width)

    def no_lines(self):
        self.draw = False

    def joint_angle(self):
        self.show_joint_angle = True

    def angle_with_gravity(self):
        self.show_angle_with_gravity = True

    # MediaPipe landmarks
    # https://google.github.io/mediapipe/solutions/pose.html
    def _get_pose_landmarks_(self):
        # Landmarks are for side view only. They are adjusted if it's front or back view
        LANDMARKS = {"chest": {"right": [], "left": []},
                     "biceps": {"right": [12, 14, 16], "left": [11, 13, 15]},
                     "triceps": {"right": [12, 14, 16], "left": [11, 13, 15]},
                     "deltoids": {"right": [14, 12, 24], "left": [13, 11, 23]},  # Different if shoulder press
                     "back": {"right": [], "left": []},
                     "quadriceps": {"right": [24, 26, 28], "left": [23, 25, 27]},
                     "hamstrings": {"right": [24, 26, 28], "left": [23, 25, 27]},
                     "glutes": {"right": [12, 24, 26], "left": [11, 23, 25]}}
        return LANDMARKS[self.muscle][self.athlete.side_seen]

    def _get_muscle_info_(self, info_needed):
        # conc_motion is True means the first part of the movement is in the concentric portion (muscle shortening)
        # False means that the muscle starts shortened
        # decreasing is True means that the joint angle is decreasing during the concentric portion of the movement
        # False means the angle increases
        INFO = {"chest": {"conc_motion": True, "decreasing": False} if "stretch" in self.muscle.lower() else {"conc_motion": False, "decreasing": False},
                "biceps": {"conc_motion": True, "decreasing": True},
                "triceps": {"conc_motion": False, "decreasing": True},
                "deltoids": {"conc_motion": False, "decreasing": False} if "high" in self.muscle.lower() else {"conc_motion": True, "decreasing": False},
                "back": {"conc_motion": True, "decreasing": True},
                "quadriceps": {"conc_motion": True, "decreasing": False} if "extension" in self.muscle.lower() else {"conc_motion": False, "decreasing": False},
                "hamstrings": {"conc_motion": True, "decreasing": True},
                "glutes": {"conc_motion": False, "decreasing": True}}
        return INFO[self.muscle][info_needed]


