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

# Useful equations and other mathematical tools

PI = 3.1415926535
E = 2.71828
G = 9.8


def _deg_to_rad(angle):
    """
    Convert degrees to radians

    :arg angle: float which is an angle in degree (°)

    :return: a float (angle in rad)
    """
    return angle * 0.0174533  # pi / 180 = 0.0174533


def _rad_to_deg(angle):
    """
    Convert radians to degrees

    :arg angle: float which is an angle in rad

    :return: a float (angle in deg)
    """
    return angle * 57.2958  # 180 / pi = 57.2958


def _sigmoid(x):
    """
    Sigmoid function, used to map any number of a list as a number between 0 and 1

    :arg x: The number (float) to be mapped onto ]0,1[

    :return: a float between 0 and 1
    """
    return 1 / (1 + (E ** (-1 * x)))


def _effective_length(percent, limb):
    """
    The effective length is the length of the limb that is perpendicular to the force applied by the weight used

    :arg percent: a float which is the percentage (in decimals) of the length of the moving limb
    perpendicular to the force
    :arg limb: the length (in meter) of the moving limb

    :return: (float) The length (in meter) perpendicular to force
    """
    return percent * limb


def _cos_to_sin(cos):
    """
    Convert a cosine to a sine

    :arg cos: a float which is the cosine of an angle

    :return: (float) the sine of that angle
    """
    return 1 - (cos**2)


def _center_of_mass(cm_human, body_weight, position, used_weight):
    """
    Finds the center of mass between two masses in 1D

    :arg cm_human: The location of the center of mass of the human body. The hip is used to find the x component
    :arg body_weight: The body weight (kg) of the human
    :arg position: The location of the weight used for the exercise
    :arg used_weight: The weight (kg) used for the exercise

    :return: (integer) The center of mass in the corresponding axis
    """
    return int((cm_human * body_weight) + (position * used_weight) / (body_weight + used_weight))


def _law_of_cosine(x1, x2, x3, y1, y2, y3):
    """
    :args: Three pairs of points in a 2D space

    :return: (float) The cosine of the angle between side_a and side_c
    """
    side_c = (((x3 - x2) ** 2) + ((y3 - y2) ** 2)) ** (1 / 2)
    side_a = (((x2 - x1) ** 2) + ((y2 - y1) ** 2)) ** (1 / 2)
    side_b = (((x3 - x1) ** 2) + ((y3 - y1) ** 2)) ** (1 / 2)
    deno = 2 * side_c * side_a

    if deno == 0:  # Shouldn't happen, but prevents a potential bug
        deno = 0.001

    angle_cos = ((side_c ** 2) + (side_a ** 2) - (side_b ** 2)) / deno
    return angle_cos


def _pythagorean_theorem(x1, x2, y1, y2, z1=0, z2=0):
    """
    :args: Two or three pairs of points (2D or 3D)

    :return: (float) The length of the hypotenuse
    """
    return (((x2-x1)**2) + ((y2-y1)**2) + (z2-z1)**2) ** (1/2)


def _pendulum_period(max_angle, length):
    """
    :arg max_angle: The biggest angle (rad)
    :arg length: The length of the pendulum

    :return: (float) The period (s) of a pendulum
    """
    simple_pendulum = ((2 * PI) * (length / G) ** (1/2))
    # Taylor series to approximate
    complex_pendulum = simple_pendulum * (1 + ((max_angle ** 2) / 16) + ((11 / 3074) * (max_angle ** 4)))
    return complex_pendulum


def _standard_deviation(average, sample):
    """
    :arg average: (float) The average of a sample
    :arg sample: (array) The sample on which to calculate the standard deviation

    :return: (float) The standard deviation
    """
    n = 0.0
    n += [((i - average) ** 2) for i in sample]
    std = (n / len(sample)) ** (1/2)
    return std


def _average(data):
    """
    :arg data: (array) Data on which to calculate an average

    :return: (float) The average of the data provided
    """
    summ = 0
    for i in data:
        summ += i
    if len(data) == 0:
        raise Exception("Division by zero. Often caused by video not restricted to the lift "
                        "(eg. the lifter preparing is included).")
    return round((abs(summ) / len(data)), 4)
