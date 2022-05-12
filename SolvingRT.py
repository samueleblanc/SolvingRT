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

    def __init__(self, height_meter, moving_limb_meter, weight_used_kg, side_seen):
        self.height = height_meter
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

    def __init__(self, name, muscle, video, athlete, measures, draw=True, show_joint_angle=True, show_angle_with_gravity=False):
        self.name = name
        self.muscle = muscle
        self.video = video
        self.athlete = athlete
        self.measures = measures
        self.draw = draw
        self.show_joint_angle = show_joint_angle
        self.show_angle_with_gravity = show_angle_with_gravity
        self.width, self.height = 0, 0
        self.pose = pd._PoseDetector(self.athlete.side_seen, self.draw)

    def play_video(self):
        VID = cv2.VideoCapture(self.video)
        POINTS = Exercise._get_pose_landmarks_(self)
        ANALYSIS = va._VideoAnalysis(self.athlete, self)
        frame_counts = 0
        times = []
        angles = []
        conc_velocity = []
        ecc_velocity = []
        conc_power = []
        ecc_power = []
        torque = []
        tust = 0  # time under significant tension
        add_data = False
        time_under_tension = False

        # For resistance profile
        res_pro_angles = []
        res_pro_conc_power = []
        res_pro_ecc_power = []

        rep_data = []  # Data that is calculated for each rep (eg power and velocity)
        set_data = []  # Data that is calculated for the full set (eg time under tension)

        if self.width or self.height == 0:
            self.height = int(VID.get(cv2.CAP_PROP_FRAME_HEIGHT) / 2)
            self.width = int(VID.get(cv2.CAP_PROP_FRAME_WIDTH) / 2)

        # Count reps
        rep_count = 0
        last_rep = 0
        conc_motion = True
        start_angle, end_angle = Exercise._get_muscle_info_(self, "start"), Exercise._get_muscle_info_(self, "end")

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
                angle_gravity = ANALYSIS.angle_gravity()
                times += [perf_counter()]
                angles += [angle]

                # Count reps
                if angle >= start_angle:
                    if conc_motion:
                        rep_count += 0.5
                        conc_motion = False
                elif angle <= end_angle:
                    if conc_motion is False:
                        rep_count += 0.5
                        conc_motion = True

                if (rep_count % 1 == 0) and (rep_count > last_rep):
                    rep_data += [[f"Rep #{int(rep_count)}"]]
                    add_data = True
                    last_rep = rep_count

                for measure in self.measures:
                    if measure == "torque":
                        if frame_counts % 4 == 0:
                            torque += [ANALYSIS.torque(angle_gravity)]
                        if add_data:
                            rep_data[len(rep_data) - 1] += [f"Torque: {mt._average(torque)} Nm"]
                            torque *= 0

                    elif measure == "power":
                        if frame_counts % 4 == 0:
                            velocity = ANALYSIS.speed(angles, times)
                            """
                                To do: Adjust velocity if eccentric
                            """
                            power = ANALYSIS.power(velocity, angle_gravity)
                            if Exercise._get_muscle_info_(self, "type") == "l":
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
                            if Exercise._get_muscle_info_(self, "type") == "l":
                                if velocity < 0:
                                    conc_velocity += [velocity]
                                else:
                                    ecc_velocity += [velocity]
                            else:
                                if velocity > 0:
                                    conc_velocity += [velocity]
                                else:
                                    ecc_velocity += [velocity]
                        # Separates data per rep
                        if add_data:
                            rep_data[len(rep_data) - 1] += [f"Conc. velocity: {mt._average(conc_velocity)} rad/s",
                                                            f"Ecc. velocity: {mt._average(ecc_velocity)} rad/s"]
                            conc_velocity *= 0
                            ecc_velocity *= 0

                    elif measure == "time under tension":
                        time_under_tension = True
                        tust += ANALYSIS.time_under_tension(angle_gravity)
                    elif measure == "tempo":
                        ANALYSIS.tempo()
                    elif measure == "EMG":
                        pass
                    elif measure == "motor units":
                        pass
                    elif measure == "resistance profile":
                        """
                            To do: Adjust velocity when eccentric
                        """
                        if frame_counts % 4 == 0:
                            res_pro_angles += [angle]
                            velocity = ANALYSIS.speed(angles, times)
                            res_pro_power = ANALYSIS.power(velocity, angle_gravity)
                            if Exercise._get_muscle_info_(self, "type") == "l":
                                if res_pro_power < 0:
                                    res_pro_conc_power += [res_pro_power]
                                else:
                                    res_pro_ecc_power += [res_pro_power]
                            else:
                                if res_pro_power > 0:
                                    res_pro_conc_power += [res_pro_power]
                                else:
                                    res_pro_ecc_power += [res_pro_power]
                        if add_data:
                            ANALYSIS.resistance_profile(rep_count, res_pro_conc_power, res_pro_ecc_power, res_pro_angles)
                            res_pro_conc_power *= 0
                            res_pro_ecc_power *= 0
                            res_pro_angles *= 0

                    elif measure == "stimulus":
                        ANALYSIS.stimulus()
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
                    cv2.putText(video, f"{round(angle_gravity)}", (x3 - 90, y3 + 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 2, (255, 0, 0), 2)
                    cv2.line(video, (x3, (y3 + 8)), (x3, (y3+70)), (255, 255, 255), 3)
                    cv2.putText(video, "V", ((x3-5), (y3+72)), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 3)

            cv2.imshow(str(self.name), video)
            if cv2.waitKey(1) == 27:  # 27 is escape
                break
        VID.release()
        cv2.destroyAllWindows()
        if time_under_tension:
            tust_in_sec = tust * (perf_counter() / frame_counts)
            set_data += [f"Time under significant tension: {tust_in_sec} s"]
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

    def no_joint_angle(self):
        self.show_joint_angle = False

    def angle_with_gravity(self):
        self.show_angle_with_gravity = True

    # MediaPipe landmarks
    # https://google.github.io/mediapipe/solutions/pose.html
    def _get_pose_landmarks_(self):
        # Landmarks are for side view only. They are adjusted if it's front or back view
        LANDMARKS = {"chest": {"right": [], "left": []},
                     "biceps": {"right": [12, 14, 16], "left": [11, 13, 15]},
                     "triceps": {"right": [12, 14, 16], "left": [11, 13, 15]},
                     "deltoids": {"right": [14, 12, 24], "left": [13, 11, 23]},
                     "back": {"right": [], "left": []},
                     "quadriceps": {"right": [24, 26, 28], "left": [23, 25, 27]},
                     "hamstrings": {"right": [24, 26, 28], "left": [23, 25, 27]}}
        return LANDMARKS[self.muscle][self.athlete.side_seen]

    def _get_muscle_info_(self, info_needed):
        # type "l" => muscle starts in a lengthened position, "s" => shortened
        # start and end are approximate values (deg) for the extrema of a range of motion (used to count reps)
        INFO = {"chest": {"type": "s", "start": 0, "end": 0},
                "biceps": {"type": "l", "start": 140, "end": 60},
                "triceps": {"type": "s", "start": 140, "end": 60},
                "deltoids": {"type": "l", "start": 30, "end": 80},
                "back": {"type": "l", "start": 0, "end": 0},
                "quadriceps": {"type": "s", "start": 160, "end": 90},  # Flip everything if leg extension
                "hamstrings": {"type": "l", "start": 160, "end": 90}}
        return INFO[self.muscle][info_needed]


