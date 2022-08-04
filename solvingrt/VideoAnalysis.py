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

import matplotlib.pyplot as plt
from solvingrt import MathTools as mt
import os


class _VideoAnalysis:

    G = 9.8  # Gravitational constant
    RAD_TO_DEG = 57.2958  # 180 / pi = 57.2958
    DEG_TO_RAD = 0.0174533  # pi / 180 = 0.0174533

    def __init__(self, athlete, exercise):
        self.athlete = athlete  # Class Athlete from SolvingRT file
        self.exercise = exercise  # Class Exercise from SolvingRT file
        self.measures = self.exercise.measures

    def angle(self) -> float:
        """
        :return: The angle (°) of the moving joint
        """
        return self.exercise.pose.find_angle(self.exercise._get_pose_landmarks_())

    def angle_gravity(self) -> float:
        """
        :return: The angle (°) between the moving limb and a parallel line to gravity
        """
        return self.exercise.pose.find_angle_gravity(self.exercise._get_pose_landmarks_())

    def torque(self, eff_length: float) -> float:
        """
        The torque is defined as 𝜏 = 𝐹×𝑟 (torque = force [cross product] radius) = 𝐹𝑟sin𝜃

        :arg eff_length: a percentage in decimals (calculated by the find_length method in file PoseDetector)
        which represents sin𝜃 in the torque formula

        :return: torque (Nm)
        """
        return self.athlete.moving_limb * self.athlete.weight_used * eff_length * _VideoAnalysis.G

    def power(self, velocity: float, eff_length: float) -> float:
        """
        The power is defined as 𝑃 = 𝜏𝜔 (Power = torque x angular velocity)

        :arg velocity: a float (calculated by the speed method) which is the angular velocity (rad/s)
        :arg eff_length: a percentage in decimals (calculated by the find_length method in file PoseDetector)
        which represents sin𝜃 in the torque formula

        :return: power (W)
        """
        return self.athlete.moving_limb * self.athlete.weight_used * velocity * eff_length * _VideoAnalysis.G

    @staticmethod
    def speed(angles: list[float], times: list[float]) -> float:
        """
        Measures the angular velocity (rad/s) of the moving joint.

        :arg angles: List of every angles
        :arg times: List of the times that match the angles

        :return: angular velocity (rad/s) of the last angle/time by the 4th to last angle/time.
        It is "instantaneous" enough, and the risk of errors diminishes
        """
        return (mt._deg_to_rad(angles[len(angles)-1] - angles[len(angles)-4])) / \
               (times[len(times)-1] - times[len(times)-4])

    @staticmethod
    def time_under_tension(eff_length: float) -> int:
        """
        The time under (significant) tension is the amount of time spent where the targeted muscle is
        in a "challenging" position. In this case, it is defined as a position where at least 5% of
        the length of the limb is perpendicular to the force applied by the weight.

        :arg eff_length: a float which represents the percentage (in decimals) of the length of the limb
        perpendicular to the force applied by the weight used

        :return: an integer which means if yes (1) or no (0) the length perpendicular is above 5%
        The number are then added (file SolvingRT) and a time is calculated with the FPS of the video.
        """
        return 0 if eff_length < 0.05 else 1

    # First number is the time spent in the eccentric portion, second is the time while the muscle is
    # in a lengthened position, third concentric, fourth shortened
    def tempo(self):
        """
        Currently, the tempo is calculated in "SolvingRT" file.
        However, only the first and third number are being measured
        """
        raise NotImplementedError

    def resistance_profile(self, torque: list[float], angles: list[float]) -> None:
        """
        The resistance profile is defined as the torque for every angle of the exercise

        :arg torque: List of every torque calculated
        :arg angles: List of every matching angles

        Saves the graph as a png file
        """
        plt.plot(angles, torque, "b")
        plt.xlabel("Angle (°)")
        plt.ylabel("Torque (Nm)")
        plt.title(f"Resistance profile of a {self.exercise.name.lower()}")
        plt.savefig(os.getcwd() + f"/resistance_profile ({self.exercise.name}).png")
        plt.cla()
        plt.clf()
        plt.close()

