from time import sleep, time
from typing import List

import pigpio

MIN_SPS = 1000  # steps per second
MAX_SPS = 3000  # steps per second
ACCELERATION = 1000  # SPS per second
from .keyboard import Keyboard


class PiGPIOPuncherAdapter(object):
    ROW0 = 100  # Number of steps from neutral position to ROW 0
    ROW_STEPS = 100  # Number of steps per row
    TIME_STEPS = 100  # Number of steps per time unit

    def __init__(self, keyboard: Keyboard, address: str = 'localhost', port: int = 8888):
        self.pi = pigpio.pi(address, port)
        if not self.pi.connected:
            raise RuntimeError(
                f"PI Not connected, make sure the pi is available on {address} and is running pigpiod on port {port}")

        self.keyboard = keyboard
        self.time_stepper = PiGPIOStepperMotor(self.pi, 17, 18, MIN_SPS, MAX_SPS, ACCELERATION)
        self.row_stepper = PiGPIOStepperMotor(self.pi, 22, 23, MIN_SPS, MAX_SPS, ACCELERATION)
        # self.zero_button = Button(2)
        self.punch_pin = 3
        self.pi.set_mode(self.punch_pin, pigpio.OUTPUT)
        self.position = None
        self.punch_completed_time = time()

    def reset(self):
        print('* reset *')
        # self.row_stepper.move_until(-1, self.zero_button.is_pressed)
        # self.row_stepper.move(self.ROW0)
        self.position = 0

    def move(self, note: int = -1, delay: float = 0):
        print()

        # print(f"move(note={note}, delay={delay})")

        calc_start = time()
        wave1 = self.time_stepper.create_move_waveform(round(delay * self.TIME_STEPS))
        wave2 = []
        if note >= 0:
            row = self.keyboard.get_index(note)
            delta = row - self.position
            wave2 = self.row_stepper.create_move_waveform(delta * self.ROW_STEPS)
            self.position = row
        calc_end = time()

        self.__synchronize(wave1, wave2)
        # print(f"Waveform created in {round((calc_end - calc_start) * 1000)} milliseconds")
        self.__wait_for_wave()  # wait until eventual punch wave is completed
        if len(wave1) > 0 or len(wave2):
            self.pi.wave_clear()
            self.__add_wave(wave1)
            self.__add_wave(wave2)
            id = self.pi.wave_create()
            if id < 0:
                raise RuntimeError(f"pigpio error on wave_create: {id}")
            self.wait_for_punch()  # Ensure the puncher is raised again before sending the next wave
            cbs = self.pi.wave_send_once(id)
            wave_start = time()
            # print(f"Send waveform with {cbs} control blocks")

            self.__wait_for_wave()
            wave_end = time()
            # print(f"Waveform took {round((wave_end - wave_start) * 1000)} milliseconds")
            self.pi.wave_clear()
        print()

    def start_punch(self):
        """
           Initiates the punching.
           Can be followed by a move call, otherwise use wait_for_punch to wait for completeness.
        """
        print(f"punch")
        self.pi.wave_clear()
        pulses = [pigpio.pulse(1 << self.punch_pin, 0, 200000),
                  pigpio.pulse(0, 1 << self.punch_pin, 0)]
        self.__add_wave(pulses)
        id = self.pi.wave_create()
        self.pi.wave_send_once(id)
        self.punch_completed_time = time() + 0.3

    def __wait_for_wave(self):
        while self.pi.wave_tx_busy():  # wait for waveform to be sent
            sleep(0.1)

    def wait_for_punch(self):
        self.__wait_for_wave()
        now = time()
        if now < self.punch_completed_time:
            # print(f"Relaxing for {round((self.punch_completed_time - now) * 1000)} milliseconds")
            sleep(self.punch_completed_time - now)
        # else:
            # print(f"Calculation took {round((now - self.punch_completed_time) * 1000)} milliseconds too much")

    def __add_wave(self, pulses: List[pigpio.pulse]):
        if len(pulses) > 0:
            self.pi.wave_add_generic(pulses)

    def __synchronize(self, wave1: List[pigpio.pulse], wave2: List[pigpio.pulse]):
        if wave1 == [] or wave2 == []:
            return

        def wavelength(pulses):
            l = 0
            for pulse in pulses:
                l += pulse.delay
            return l

        def scale(pulses, factor):
            for pulse in pulses:
                pulse.delay = round(pulse.delay * factor)

        l1 = wavelength(wave1)
        l2 = wavelength(wave2)

        if l1 > l2:
            scale(wave2, l1 / l2)
        if l2 > l1:
            scale(wave1, l2 / l1)


def calculate_acceleration_profile(min_sps, max_sps, acceleration):
    "Returns a list of delays in microseconds"
    profile = []

    sps = min_sps
    while sps < max_sps:
        profile.append(round(1000000 / sps))
        sps += acceleration * (1 / sps)
    return profile


class PiGPIOStepperMotor(object):

    def __init__(self, pi: pigpio.pi, dir_pin, step_pin, min_sps, max_sps, acceleration):
        self.pi = pi
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.acceleration_profile = calculate_acceleration_profile(min_sps, max_sps, acceleration)
        self.min_delay = 1 / max_sps
        self.max_delay = 1 / min_sps

        pi.set_mode(dir_pin, pigpio.OUTPUT)
        pi.set_mode(step_pin, pigpio.OUTPUT)

    def __set_dir(self, dir: int):
        self.pi.write(self.dir_pin, 0 if dir < 0 else 1)

    def __step(self, delay):
        self.pi.write(self.step_pin, 1)
        sleep(delay / 2)
        self.pi.write(self.step_pin, 0)
        sleep(delay / 2)

    def move_until(self, dir: int, condition):
        """Slowly moves the motor in the given direction (-1,+1) until the condition becomes true"""
        self.__set_dir(dir)
        while not condition():
            self.__step(self.max_delay)

    def create_move_waveform(self, steps: int) -> List[pigpio.pulse]:
        self.__set_dir(-1 if steps < 0 else 1)

        pulses = []

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
            pulses.append(pigpio.pulse(1 << self.step_pin, 0, delay >> 1))
            pulses.append(pigpio.pulse(0, 1 << self.step_pin, delay >> 1))

        return pulses
