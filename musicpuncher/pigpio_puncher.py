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
    CUTTER_POSITION = -3000  # number of steps after last punch (minus means number of steps before last punch)
    END_FEED = 5000  # number of steps to feed after last punch or cut (whichever is last)

    def __init__(self, keyboard: Keyboard, notesequence: NoteSequence, address: str = 'localhost', port: int = 8888):
        self.pi = pigpio.pi(address, port)
        if not self.pi.connected:
            raise RuntimeError(
                f"PI Not connected, make sure the pi is available on {address} and is running pigpiod on port {port}")

        self.keyboard = keyboard

        self.time_stepper = PiGPIOStepperMotor(self.pi, 17, 18, MIN_SPS, MAX_SPS, ACCELERATION)
        self.row_stepper = PiGPIOStepperMotor(self.pi, 22, 23, MIN_SPS, MAX_SPS, ACCELERATION)

        self.zero_pin = 2
        self.pi.set_mode(self.zero_pin, pigpio.INPUT)
        self.pi.set_pull_up_down(self.zero_pin, pigpio.PUD_DOWN)

        self.punch_pin = 3
        self.pi.set_mode(self.punch_pin, pigpio.OUTPUT)

        self.cutter_pin = 4
        self.pi.set_mode(self.cutter_pin, pigpio.INPUT)
        self.pi.set_pull_up_down(self.cutter_pin, pigpio.PUD_DOWN)

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
                if tuple != (0, 0):
                    steps.append(tuple)
                position = targetPosition
                delay = 0

        self.do_run(steps)

    def do_run(self, steps):
        total_time_steps = 0
        for step in steps:
            total_time_steps += step[0]

        cutter_step = total_time_steps + self.CUTTER_POSITION
        did_cut = False

        total_time_steps = 0
        for idx, step in enumerate(steps):
            if idx == 0:
                self.__prepare_waveform(step[0], step[1])
            self.__create_and_send_wave()  # run wave prepared for previous step
            if idx < len(steps) - 1:
                self.__prepare_waveform(steps[idx + 1][0], steps[idx + 1][1])
            self.__wait_for_wave()
            self.__punch()
            total_time_steps += step[0]

            if not did_cut and total_time_steps >= cutter_step:
                self.__cut()
                did_cut = True

        if not did_cut:
            if self.CUTTER_POSITION > 0:
                self.__prepare_waveform(self.CUTTER_POSITION, 0)
                self.__create_and_send_wave()
                self.__wait_for_wave()
            self.__cut()

        if self.END_FEED > 0:
            self.__prepare_waveform(self.END_FEED, 0)
            self.__create_and_send_wave()
            self.__wait_for_wave()

    def reset(self):
        print('* reset *')
        self.row_stepper.move_until(-1, lambda: self.pi.read(self.zero_pin) == 1)
        self.__prepare_waveform(0, self.ROW0)
        self.__create_and_send_wave()
        self.__wait_for_wave()
        self.position = 0

    def __prepare_waveform(self, timesteps, notesteps):
        self.pi.wave_clear()
        wave1 = self.time_stepper.create_move_waveform(timesteps)
        wave2 = self.row_stepper.create_move_waveform(notesteps)
        self.__synchronize(wave1, wave2)
        self.__add_wave(wave1)
        self.__add_wave(wave2)

    def __punch(self):
        print(f"punch")
        self.pi.write(self.punch_pin, 1)
        sleep(0.2)
        self.pi.write(self.punch_pin, 0)
        sleep(0.3)

    def __cut(self):
        print(f"cut")
        self.pi.write(self.cutter_pin, 1)
        sleep(0.2)
        self.pi.write(self.cutter_pin, 0)
        sleep(0.3)

    def __create_and_send_wave(self):
        id = self.pi.wave_create()
        if id < 0:
            raise RuntimeError(f"pigpio error on wave_create: {id}")
        self.pi.wave_send_once(id)

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
        min_delay_us = round(self.min_delay * 1000000)
        count = abs(steps)
        steps_to_stop = 0
        rem = count
        for i in range(0, count):
            rem -= 1
            if rem <= steps_to_stop:
                delay_us = profile[rem]
            elif i < proflen:
                delay_us = profile[i]
                steps_to_stop = i
            else:
                delay_us = min_delay_us
            pulses.append(pigpio.pulse(1 << self.step_pin, 0, delay_us >> 1))
            pulses.append(pigpio.pulse(0, 1 << self.step_pin, delay_us >> 1))

        return pulses
