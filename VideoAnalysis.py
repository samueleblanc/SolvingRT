import MathTools as mt
import math
import matplotlib.pyplot as plt


class _VideoAnalysis:

    G = 9.8
    RAD_TO_DEG = 57.2958  # 180 / pi = 57.2958
    DEG_TO_RAD = 0.0174533  # pi / 180 = 0.0174533

    def __init__(self, athlete, exercise):
        self.athlete = athlete
        self.exercise = exercise
        self.measures = self.exercise.measures

    def angle(self):
        return self.exercise.pose.find_angle(self.exercise._get_pose_landmarks_())

    def angle_gravity(self):
        return self.exercise.pose.find_angle_gravity(self.exercise._get_pose_landmarks_())

    def torque(self, angle):
        return self.athlete.moving_limb * self.athlete.weight_used * math.sin(angle * _VideoAnalysis.DEG_TO_RAD) * _VideoAnalysis.G

    def power(self, velocity, angle):
        return self.athlete.moving_limb * self.athlete.weight_used * velocity * math.sin(angle * _VideoAnalysis.DEG_TO_RAD) * _VideoAnalysis.G

    @staticmethod
    def speed(angles, times):
        return (mt._deg_to_rad(angles[len(angles)-1] - angles[len(angles)-5])) / (times[len(times)-1] - times[len(times)-5])

    @staticmethod
    def time_under_tension(angle):
        if math.sin(angle * _VideoAnalysis.DEG_TO_RAD) < 0.05:
            return 0
        else:
            return 1

    # First number is the time spent in the eccentric portion, second is the time while the muscle is
    # in a lengthened position, third concentric, fourth shortened
    def tempo(self):
        pass

    # The power for every angle in the movement
    def resistance_profile(self, rep, concentric_power, eccentric_power, angles):
        plt.plot(angles[:len(concentric_power)], concentric_power, "b", label="Concentric")
        plt.plot(angles[len(concentric_power):], eccentric_power, "g", label="Eccentric")
        plt.legend(loc="upper left")
        plt.xlabel("Angle (°)")
        plt.ylabel("Power (W)")
        plt.title(f"Resistance profile of a {self.exercise.name} (rep #{str(rep)})")
        plt.savefig("resistance_profile_rep_" + str(rep) + ".png")

    # Estimated EMG
    def EMG(self):
        # Link to paper used
        pass

    # Estimated percentage of motor units recruited
    def motor_units(self):
        # Link to paper used
        pass

    # Estimated number of reps in reserved based on velocity changes (and facial features?!)
    def reps_in_reserves(self):
        pass

    # Output is a number between 0 and 1, with 0 being strength dominant and 1 being glycolytic dominant
    def stimulus(self):
        # beta version
        pass
