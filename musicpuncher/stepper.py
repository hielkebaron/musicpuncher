from time import sleep

from gpiozero import OutputDevice


def calculate_acceleration_profile(min_sps, max_sps, acceleration):
    profile = []

    sps = min_sps
    while sps < max_sps:
        profile.append(1 / sps)
        sps += acceleration * (1 / sps)
    return profile


class StepperMotor(object):

    def __init__(self, dir_pin, step_pin, min_sps, max_sps, acceleration):
        self.dir_pin = OutputDevice(dir_pin)
        self.step_pin = OutputDevice(step_pin)
        self.acceleration_profile = calculate_acceleration_profile(min_sps, max_sps, acceleration)
        self.min_delay = 1 / max_sps
        self.max_delay = 1 / min_sps
        # print(f"Acceleration profile (ms): {[round(delay * 1000) for delay in self.acceleration_profile]}")
        # print(f"pulses per second {[round(1 / delay) for delay in self.acceleration_profile]}")

    def __set_dir(self, dir: int):
        self.dir_pin.value = False if dir < 0 else True

    def __step(self, delay):
        self.step_pin.on()
        sleep(delay / 2)
        self.step_pin.off()
        sleep(delay / 2)

    def move_until(self, dir: int, condition):
        """Slowly moves the motor in the given direction (-1,+1) until the condition becomes true"""
        self.__set_dir(dir)
        while not condition():
            self.__step(self.max_delay)

    def move(self, steps: int):
        self.__set_dir(-1 if steps < 0 else 1)
        profile = self.acceleration_profile
        proflen = len(profile)
        min_delay = self.min_delay
        count = abs(steps)
        steps_to_stop = 0
        rem = count
        for i in range(0, count):
            rem -= 1
            if rem <= steps_to_stop:
                delay = profile[rem]
            elif i < proflen:
                delay = profile[i]
                steps_to_stop = i
            else:
                delay = min_delay
            self.__step(delay)
