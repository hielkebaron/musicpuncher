import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from musicpuncher.stepper import calculate_acceleration_profile


def test_calculate_acceleration_profile1():
    profile = calculate_acceleration_profile(10, 20, 10)

    print()
    total = 0
    for delay in profile:
        print("%0.2fs: %0.3f %3.0f" % (total, delay, 1/delay))
        total += delay
    # pps = [round(1 / delay) for delay in profile]
    # assert pps == [10, 20, 30, 40, 50, 60, 70, 80, 90]
    #
    # ms = [round(delay * 1000) for delay in profile]
    # assert ms == [100, 50, 33, 25, 20, 17, 14, 12, 11]


# def test_calculate_acceleration_profile2():
#     profile = calculate_acceleration_profile(0.01, 0.1, 8)
#
#     pps = [round(1 / delay) for delay in profile]
#     assert pps == [10, 18, 26, 34, 42, 50, 58, 66, 74, 82, 90, 98]
#
#     ms = [round(delay * 1000) for delay in profile]
#     assert ms == [100, 56, 38, 29, 24, 20, 17, 15, 14, 12, 11, 10]
