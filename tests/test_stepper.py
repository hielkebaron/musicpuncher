import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from musicpuncher.music_puncher import calculate_acceleration_profile


def test_calculate_acceleration_profile1():
    profile = calculate_acceleration_profile(10, 20, 10)

    print()
    total = 0
    for delay in profile:
        print("%0.2fs: %0.3f %3.0f" % (total, delay, 1/delay))
        total += delay

def test_calculate_acceleration_profile2():
    profile = calculate_acceleration_profile(10, 10, 10)

    print()
    total = 0
    for delay in profile:
        print("%0.2fs: %0.3f %3.0f" % (total, delay, 1 / delay))
        total += delay
