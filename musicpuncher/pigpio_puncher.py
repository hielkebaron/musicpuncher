from time import sleep
from typing import List

import pigpio

from .music import NoteSequence

MIN_SPS = 1000  # steps per second
MAX_SPS = 3000  # steps per second
ACCELERATION = 1000  # SPS per second
from .keyboard import Keyboard


class PiGPIOPuncher(object):
    ROW0 = 100  # Number of steps from neutral position to ROW 0
    ROW_STEPS = 100  # Number of steps per row
    TIME_STEPS = 100  # Number of steps per time unit

    def __init__(self, keyboard: Keyboard, notesequence: NoteSequence, address: str = 'localhost', port: int = 8888):
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
        self.notesequence = notesequence

    def run(self):
        self.reset()

        position = self.ROW0
        steps = []  # list of tuple with (delay, note) steps for each hole
        for delayNotes in self.notesequence:
            if delayNotes.notes == []:
                raise (RuntimeError("Empty note set is not supported, consolidate consecutive delays first"))
            positions = sorted(
                [self.ROW0 + (self.keyboard.get_index(note) * self.ROW_STEPS) for note in delayNotes.notes])
            if abs(position - positions[-1]) < abs(position - positions[0]):
                positions.reverse()  # Start from nearest end
            delay = round(delayNotes.delay * self.TIME_STEPS)
            for targetPosition in positions:
                tuple = (delay, targetPosition - position)
                if tuple != (0,0):
                    steps.append(tuple)
                position = targetPosition
                delay = 0

        self.__calculate_waveforms(steps[0][0], steps[0][1])
        for step in steps[1:]:
            self.__move(lambda: self.__calculate_waveforms(step[0], step[1]))
            self.__punch()
        self.__move(lambda: None)
        self.__punch()

    def reset(self):
        print('* reset *')
        # self.row_stepper.move_until(-1, self.zero_button.is_pressed)
        # self.row_stepper.move(self.ROW0)
        self.position = 0

    def __calculate_waveforms(self, timesteps, notesteps):
        self.pi.wave_clear()
        wave1 = self.time_stepper.create_move_waveform(timesteps)
        wave2 = self.row_stepper.create_move_waveform(notesteps)
        self.__synchronize(wave1, wave2)
        self.__add_wave(wave1)
        self.__add_wave(wave2)

    def __move(self, calculate_next):
        id = self.pi.wave_create()

        if id < 0:
            raise RuntimeError(f"pigpio error on wave_create: {id}")
        self.pi.wave_send_once(id)
        calculate_next()
        self.__wait_for_wave()

    def __punch(self):
        print(f"punch")
        self.pi.write(self.punch_pin, 1)
        sleep(0.2)
        self.pi.write(self.punch_pin, 0)
        sleep(0.3)

    def __wait_for_wave(self):
        while self.pi.wave_tx_busy():  # wait for waveform to be sent
            sleep(0.1)

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
