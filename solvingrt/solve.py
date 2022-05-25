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


import os
import cv2
from numpy import add
from solvingrt import PoseDetector as pd
from solvingrt import VideoAnalysis as va
from solvingrt import MathTools as mt
from time import perf_counter


class Athlete:

    def __init__(self, height_meter, body_weight_kg, moving_limb_meter, weight_used_kg, side_seen):
        self.height = height_meter
        self.body_weight = body_weight_kg
        self.moving_limb = moving_limb_meter
        self.weight_used = weight_used_kg
        self.side_seen = side_seen

    def inches_to_meter(self):
        """
        Changes the length that were entered (in inches) to length in meter
        """
        self.height = self.height * 0.0254
        self.moving_limb = self.moving_limb * 0.0254

    def lb_to_kg(self):
        """
        Change the weights that were entered (lb) to weights in kg
        """
        self.weight_used = self.weight_used * 0.453592
        self.body_weight = self.body_weight * 0.453592

    def set_weight_used(self, weight):
        """
        Can change the weight without changing the class

        :arg weight: (float) New weight used
        """
        self.weight_used = weight


class Exercise:

    def __init__(self, exercise_name, muscle, path_to_video, athlete, measures):
        self.name = exercise_name
        self.muscle = muscle
        self.video = path_to_video
        self.athlete = athlete
        self.measures = measures
        self.draw = True
        self.show_joint_angle = False
        self.show_angle_with_gravity = False
        self.save_f = False
        self.right_side = False
        self.width, self.height = 0, 0
        self.pose = pd._PoseDetector(self)

    def play_video(self):
        """
        MAIN METHOD
        Must be the last function called (see README)

        Every other classes and methods are called from this function. It computes and stores basically every
        piece of data possible (in this library)
        """
        VID = cv2.VideoCapture(self.video)
        POINTS = Exercise._get_pose_landmarks_(self)
        ANALYSIS = va._VideoAnalysis(self.athlete, self)
        frame_counts = 0
        times = []
        angles = []
        rep_angles = []
        concentric_time = 0
        eccentric_time = 0
        # TODO: Measure the amount of time spent while in lengthened or shortened position (for tempo)
        # lengthened_time = 0
        # shortened_time = 0
        tust = 0  # time under significant tension
        concentric_speed = []  # To measure velocity lost
        conc_velocity = []
        ecc_velocity = []
        conc_power = []
        ecc_power = []
        torque = []
        res_pro_angles = []
        res_pro_torque = []
        is_parallel = False

        time_under_tension = False
        min_max_angles = False
        velocity_lost = False
        res_pro = False
        parallel = False
        work = False
        for measure in self.measures:
            measure = measure.lower()
            if measure == "time under tension":
                time_under_tension = True
            elif measure == "angles":
                min_max_angles = True
            elif measure == "velocity lost":
                velocity_lost = True
            elif measure == "resistance profile":
                res_pro = True
            elif (measure == "parallel") and ("squat" in self.name.lower()):
                parallel = True
            elif measure == "work":
                work = True
            elif measure == "speed":
                pass
            elif measure == "torque":
                pass
            elif measure == "power":
                pass
            elif measure == "tempo":
                pass
            else:
                print(f"{measure} is not a valid input.")
                raise ValueError(measure)

        rep_data = []  # Data that is calculated for each rep (eg power and velocity)
        set_data = []  # Data that is calculated for the full set (eg time under tension)
        add_data = False

        # Count reps
        rep_count = 0
        last_rep = 0
        conc_motion = Exercise._get_muscle_info_(self, "conc_motion")
        is_shortening = Exercise._get_muscle_info_(self, "conc_motion")
        angle_decreasing = Exercise._get_muscle_info_(self, "decreasing")

        if (self.width == 0) or (self.height == 0):
            self.height = int(VID.get(cv2.CAP_PROP_FRAME_HEIGHT) / 2)
            self.width = int(VID.get(cv2.CAP_PROP_FRAME_WIDTH) / 2)

        total_frames = int(VID.get(cv2.CAP_PROP_FRAME_COUNT))

        while VID.isOpened():
            success, frame = VID.read()
            video = cv2.resize(frame, (self.width, self.height))
            landmarks = self.pose.find_position(video)
            start_time = perf_counter()
            frame_counts += 1
            if len(landmarks) > 0:
                x1, y1 = landmarks[POINTS[0]]
                x2, y2 = landmarks[POINTS[1]]
                x3, y3 = landmarks[POINTS[2]]

                angle = ANALYSIS.angle()
                effective_length = self.pose.find_length(POINTS)

                times += [perf_counter()]
                angles += [angle]
                rep_angles += [angle]

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

                # Loops on store data depending on if the user wants this measure or not
                for measure in self.measures:
                    measure = measure.lower()
                    if measure == "torque":
                        if frame_counts % 4 == 0:
                            torque += [ANALYSIS.torque(effective_length)]
                        if add_data:
                            rep_data[len(rep_data) - 1] += [f"Torque: {mt._average(torque)} Nm"]
                            torque *= 0

                    elif (measure == "power") or (work is True):
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
                        if add_data: 
                            avg_conc_power = mt._average(conc_power)
                            avg_ecc_power = mt._average(ecc_power)
                            if measure == "power":
                                rep_data[len(rep_data) - 1] += [f"Conc. power: {avg_conc_power} W",
                                                                f"Ecc. power: {avg_ecc_power} W"]
                            if work is True:
                                total_work = avg_conc_power * (max(rep_angles) - min(rep_angles))
                                rep_data[len(rep_data) - 1] += [f"Work (concentric): {total_work}J"]
                            conc_power *= 0
                            ecc_power *= 0

                    elif (measure == "speed") or (velocity_lost is True):
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

                    elif measure == "parallel":
                        if (self.muscle.lower() == "quadriceps") or (self.muscle.lower() == "hamstrings"):
                            if y1 >= y2:
                                is_parallel = True
                        elif self.muscle.lower() == "glutes":
                            if y2 >= y3:
                                is_parallel = True
                        if add_data:
                            rep_data[len(rep_data) - 1] += [f"Parallel: {is_parallel}"]
                            is_parallel = False

                    elif measure == "time under tension":
                        tust += ANALYSIS.time_under_tension(effective_length)

                    elif measure == "tempo":
                        if add_data:
                            conc_time = concentric_time * (perf_counter() / frame_counts)
                            ecc_time = eccentric_time * (perf_counter() / frame_counts)
                            rep_data[len(rep_data) - 1] += [f"Concentric time: {round(conc_time, 4)}s",
                                                            f"Eccentric time: {round(ecc_time, 4)}s"]
                            concentric_time *= 0
                            eccentric_time *= 0
                    
                    elif measure == "angles":
                        if add_data:
                            rep_data[len(rep_data) - 1] += [f"Min angle: {min(rep_angles)}",
                                                            f"Max angle: {max(rep_angles)}"]

                    elif measure == "resistance profile":
                        # The first rep is excluded for the graph because it is
                        # often paired with a little bit of setting-up for the exercise
                        if (frame_counts % 4 == 0) and (1 < rep_count < 3):
                            res_pro_angles += [angle]
                            res_pro_torque += [ANALYSIS.torque(effective_length)]

                if add_data is True:
                    rep_angles *= 0  # Used at two places, that's why it's emptied here
                    add_data = False

                if self.draw:
                    if parallel is True:
                        if (self.muscle.lower() == "quadriceps") or (self.muscle.lower() == "hamstrings"):
                            if y2 >= y1:
                                cv2.line(video, (x2, y2), (x1, y2), (0, 0, 255), 3)
                            else:
                                cv2.line(video, (x2, y2), (x1, y2), (0, 255, 0), 3)
                            cv2.circle(video, (x1, y1), 5, (255, 255, 255), cv2.FILLED)
                            cv2.circle(video, (x2, y2), 5, (255, 255, 255), cv2.FILLED)
                        elif self.muscle.lower() == "glutes":
                            if y1 >= y3:
                                cv2.line(video, (x3, y3), (x2, y3), (0, 0, 255), 3)
                            else:
                                cv2.line(video, (x3, y3), (x2, y3), (0, 255, 0), 3)
                            cv2.circle(video, (x2, y2), 5, (255, 255, 255), cv2.FILLED)
                            cv2.circle(video, (x3, y3), 5, (255, 255, 255), cv2.FILLED)
                    else:
                        cv2.line(video, (x1, y1), (x2, y2), (255, 255, 255), 3)
                        cv2.line(video, (x3, y3), (x2, y2), (255, 255, 255), 3)
                        cv2.circle(video, (x1, y1), 8, (255, 0, 0), cv2.FILLED)
                        cv2.circle(video, (x1, y1), 15, (255, 255, 255), 2)
                        cv2.circle(video, (x2, y2), 8, (255, 0, 0), cv2.FILLED)
                        cv2.circle(video, (x2, y2), 15, (255, 255, 255), 2)
                        cv2.circle(video, (x3, y3), 8, (255, 0, 0), cv2.FILLED)
                        cv2.circle(video, (x3, y3), 15, (255, 255, 255), 2)
                if self.show_joint_angle:
                    cv2.putText(video, f"{round(angle)}", (x2 - 70, y2 + 50),
                                cv2.FONT_HERSHEY_COMPLEX_SMALL, 2, (255, 0, 0), 2)
                if self.show_angle_with_gravity:
                    if ("deadlift" not in self.name.lower()) and ("squat" not in self.name.lower()):
                        angle_gravity = ANALYSIS.angle_gravity()
                        cv2.putText(video, f"{round(angle_gravity)}", (x3 - 90, y3 + 50),
                                    cv2.FONT_HERSHEY_COMPLEX_SMALL, 2, (255, 0, 0), 2)
                        cv2.line(video, (x3, (y3 + 8)), (x3, (y3+70)), (255, 255, 255), 3)
                        cv2.putText(video, "V", ((x3-5), (y3+72)),
                                    cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 3)
                    else:
                        raise Exception(f"Can't show the angle with gravity with a {self.name.lower()}")

            cv2.imshow(f"{str(self.name)} - Calculating {self.measures}", video)

            if cv2.waitKey(1) == 27:  # 27 is escape
                break
            elif total_frames - 1 == frame_counts:
                # Work around an OpenCV problem
                # Error: (-215:Assertion failed) !ssize.empty() in function 'cv::resize'
                break

        VID.release()
        cv2.destroyAllWindows()

        if time_under_tension:
            tust_in_sec = tust * ((perf_counter() - start_time) / frame_counts)
            set_data += [f"Time under significant tension: {tust_in_sec} s"]
        if min_max_angles:
            set_data += [f"Min angle: {round(min(angles), 4)}", f"Max angle: {round(max(angles), 4)}"]
        if velocity_lost:
            max_vel = max(concentric_speed)
            min_vel = min(concentric_speed)
            vel_lost = round(((max_vel - min_vel) / max_vel) * 100, 2)
            set_data += [f"Velocity lost: {vel_lost}%"]
        if res_pro:
            ANALYSIS.resistance_profile(res_pro_torque, res_pro_angles)

        if self.save_f is False:
            print(f"Data calculated for each rep: {rep_data}")
            print(f"Data calculated for the set: {set_data}")
        elif self.save_f is True:
            f = open(os.getcwd() + "/Data_for_" + self.name + ".txt", "a")
            f.write(self.name + "\n\n")
            f.write("Data calculated for each rep:\n\n")
            for rep in rep_data:
                for measures in rep:
                    f.write(measures + "\n")
                f.write("\n")
            f.write("\nData calculated for the set:\n")
            for measures in set_data:
                f.write(measures + "\n\n")
            f.close()
        return

    def change_muscle(self, new_muscle):
        """
        Change which muscle to analyse without changing Exercise

        :arg new_muscle: (string)
        """
        self.muscle = new_muscle

    def video_resize(self, width, height):
        """
        Change the size of the video

        :arg width: (integer) Width of the video in pixels
        :arg height: (integer) Height of the video in pixels
        """
        self.width = int(width)
        self.height = int(height)

    def no_lines(self):
        """
        Don't draw lines over the moving limb
        """
        self.draw = False

    def joint_angle(self):
        """
        Show the angle of the moving joint
        """
        self.show_joint_angle = True

    def angle_with_gravity(self):
        """
        Show the angle between the moving limb and a line parallel to gravity
        """
        self.show_angle_with_gravity = True

    def save_in_file(self):
        """
        Stores the data in a text file instead of printing it on the screen
        """
        self.save_f = True

    def switch_side(self):
        """
        When filming from front or back, the side analyzed is the left one.
        This method switches it to the left side
        """
        self.right_side = True

    def _get_pose_landmarks_(self):
        """
        Dict of the landmarks depending on the muscle and the side seen by the camera.
        If the side seen is the front or the back, the landmarks to follow are adjusted from those
        https://google.github.io/mediapipe/solutions/pose.html

        :return: An array of the three points to follow
        """

        # Front and back are mostly used to draw the lines, not for measurements
        LANDMARKS = {"chest": {"right": [12, 14, 16], "left": [11, 13, 15],
                               "front": [14, 12, 24] if self.right_side else [13, 11, 23],
                               "back": [14, 12, 24] if self.right_side else [13, 11, 23]},
                     "biceps": {"right": [12, 14, 16], "left": [11, 13, 15],
                                "front": [14, 12, 24] if self.right_side else [13, 11, 23],
                                "back": [14, 12, 24] if self.right_side else [13, 11, 23]},
                     "triceps": {"right": [12, 14, 16], "left": [11, 13, 15],
                                 "front": [14, 12, 24] if self.right_side else [13, 11, 23],
                                 "back": [14, 12, 24] if self.right_side else [13, 11, 23]},
                     "deltoids": {"right": [14, 12, 24], "left": [13, 11, 23],
                                  "front": [14, 12, 24] if self.right_side else [13, 11, 23],
                                  "back": [14, 12, 24] if self.right_side else [13, 11, 23]},
                     "back": {"right": [14, 12, 24], "left": [13, 11, 23],
                              "front": [14, 12, 24] if self.right_side else [13, 11, 23],
                              "back": [14, 12, 24] if self.right_side else [13, 11, 23]},
                     "quadriceps": {"right": [24, 26, 28], "left": [23, 25, 27],
                                    "front": [24, 26, 28] if self.right_side else [23, 25, 27],
                                    "back": [24, 26, 28] if self.right_side else [23, 25, 27]},
                     "hamstrings": {"right": [24, 26, 28], "left": [23, 25, 27],
                                    "front": [24, 26, 28] if self.right_side else [23, 25, 27],
                                    "back": [24, 26, 28] if self.right_side else [23, 25, 27]},
                     "glutes": {"right": [12, 24, 26], "left": [11, 23, 25],
                                "front": [12, 24, 26] if self.right_side else [11, 23, 25],
                                "back": [12, 24, 26] if self.right_side else [11, 23, 25]}}
        return LANDMARKS[self.muscle.lower()][self.athlete.side_seen.lower()]

    def _get_muscle_info_(self, info_needed):
        """
        :arg info_needed: (string)

        conc_motion is True means the first part of the movement is in the concentric portion (muscle shortening)
        False means that the muscle starts shortened

        decreasing is True means that the joint angle is decreasing during the concentric portion of the movement
        False means the angle increases

        :return: (boolean)
        """
        INFO = {"chest": {"conc_motion": True, "decreasing": False} if "stretch" in self.muscle.lower()
                else {"conc_motion": False, "decreasing": False},
                "biceps": {"conc_motion": True, "decreasing": True},
                "triceps": {"conc_motion": False, "decreasing": True},
                "deltoids": {"conc_motion": False, "decreasing": False} if "high" in self.muscle.lower()
                else {"conc_motion": True, "decreasing": False},
                "back": {"conc_motion": True, "decreasing": True},
                "quadriceps": {"conc_motion": True, "decreasing": False} if "extension" in self.muscle.lower()
                else {"conc_motion": False, "decreasing": False},
                "hamstrings": {"conc_motion": True, "decreasing": True},
                "glutes": {"conc_motion": False, "decreasing": True}}
        return INFO[self.muscle.lower()][info_needed.lower()]

