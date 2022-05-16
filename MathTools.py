"""
Useful equations and other mathematical tools
"""

import math

PI = 3.1415926535
E = 2.71828
G = 9.8


def _deg_to_rad(angle):
    return angle * 0.0174533  # pi / 180 = 0.0174533


def _rad_to_deg(angle):
    return angle * 57.2958  # 180 / pi = 57.2958


def _sigmoid(p):
    return 1 / (1 + (E ** (-1 * p)))


def _effective_length(percent, limb):
    return percent * limb


def _cos_to_sin(cos):
    return 1 - (cos**2)


def _center_of_mass(cm_human, body_weight, position, used_weight):
    return ((cm_human * body_weight) + (position * used_weight)) / (body_weight + used_weight)


def _linear_interpolation(x0, x1, y0, y1):
    return (y1 - y0) / (x1 - x0)


def _law_of_cosine(x1, x2, x3, y1, y2, y3):
    side_c = (((x3 - x2) ** 2) + ((y3 - y2) ** 2)) ** (1 / 2)
    side_a = (((x2 - x1) ** 2) + ((y2 - y1) ** 2)) ** (1 / 2)
    side_b = (((x3 - x1) ** 2) + ((y3 - y1) ** 2)) ** (1 / 2)
    deno = 2 * side_c * side_a
    # Shouldn't happen, but prevents a potential bug
    if deno == 0:
        deno = 0.001
    angle_cos = ((side_c ** 2) + (side_a ** 2) - (side_b ** 2)) / deno
    return angle_cos


def _pythagorean_theorem(x1, x2, y1, y2, z1=0, z2=0):
    return (((x2-x1)**2) + ((y2-y1)**2) + (z2-z1)**2) ** (1/2)


def _pendulum_velocity(min_angle, max_angle, length):
    simple_pendulum = ((2 * PI) * (length / G) ** (1/2))
    # Taylor series to approximate
    complex_pendulum = simple_pendulum * (1 + ((max_angle ** 2) / 16) + ((11 / 3074) * (max_angle ** 4)))
    used_amp = 0.25 - (min_angle / 360)
    grav_vel = ((max_angle - min_angle) / (complex_pendulum * used_amp))
    return grav_vel


def _standard_deviation(average, sample):
    n = 0.0
    n += [((i - average) ** 2) for i in sample]
    std = (n / len(sample)) ** (1/2)
    return std


def _average(data):
    sum = 0
    for i in data:
        sum += i
    if len(data) == 0:
        raise Exception("Division by zero. Often caused by video not restricted to the lift "
                        "(eg. the lifter preparing is included).")
    return round((abs(sum) / len(data)), 4)
