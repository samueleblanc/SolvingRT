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

    def torque(self, eff_length):
        return self.athlete.moving_limb * self.athlete.weight_used * eff_length * _VideoAnalysis.G

    def power(self, velocity, eff_length):
        return self.athlete.moving_limb * self.athlete.weight_used * velocity * eff_length * _VideoAnalysis.G

    @staticmethod
    def speed(angles, times):
        return (mt._deg_to_rad(angles[len(angles)-1] - angles[len(angles)-4])) / (times[len(times)-1] - times[len(times)-4])

    @staticmethod
    def time_under_tension(eff_length):
        if eff_length < 0.05:  # Less than 5% of the length of the muscle is perpendicular to gravitational force
            return 0
        else:
            return 1

    # First number is the time spent in the eccentric portion, second is the time while the muscle is
    # in a lengthened position, third concentric, fourth shortened
    def tempo(self):
        pass

    # The torque for every angle in the movement
    def resistance_profile(self, rep, torque, angles):
        """
            To do: Video needs to stay the same size
        """
        plt.plot(angles, torque, "b")
        plt.xlabel("Angle (°)")
        plt.ylabel("Torque (Nm)")
        plt.title(f"Resistance profile of a {self.exercise.name.lower()} (rep #{str(int(rep))})")
        plt.savefig("resistance_profile_rep_" + str(int(rep)) + ".png")
        plt.cla()
        plt.clf()
        plt.close()

    # Estimated EMG
    def EMG(self):
        pass

    # Estimated percentage of motor units recruited
    def motor_units(self):
        pass

    def velocity_lost(self):
        pass

    # Output is a number between 0 and 1, with 0 being strength dominant and 1 being glycolytic dominant
    def stimulus(self):
        pass

    # Estimated number of reps in reserve
    def RIR(self):
        pass
