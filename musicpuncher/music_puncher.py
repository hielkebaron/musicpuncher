from enum import auto, Enum
from time import sleep, time
from typing import List

import pigpio

from .music import NoteSequence

MIN_SPS = 1000  # steps per second
MAX_SPS = 3000  # steps per second
ACCELERATION = 1000  # SPS per second
from .keyboard import Keyboard


class MusicPuncher(object):
    def __init__(self, config, keyboard: Keyboard, address: str = 'localhost', port: int = 8888):
        self.pi = pigpio.pi(address, port)
        if not self.pi.connected:
            raise RuntimeError(
                f"PI Not connected, make sure the pi is available on {address} and is running pigpiod on port {port}")

        self.keyboard = keyboard

        feed_stepper = PiGPIOStepperMotor(self.pi, config['feed-stepper'])
        tone_stepper = PiGPIOStepperMotor(self.pi, config['tone-stepper'])
        self.steppers = Steppers(self.pi, [feed_stepper, tone_stepper])

        self.zero_button = Button(self.pi, config['zero-button']) if 'zero-button' in config else None
        self.status_led = StatusLed(self.pi, config['status-led']) if 'status-led' in config else DummyStatusLed()
        self.puncher = Puncher(self.pi, config['puncher'])
        self.cutter = Cutter(self.pi, config['cutter'])

        self.idle_position = config['idle-position']
        self.row0 = config['row0']
        self.tone_steps = config['tone-steps']
        self.feed_steps = config['feed-steps']
        self.cutter_position = config['cutter-position']
        self.end_feed = config['end-feed']
        self.position = None

        print(f"PiGPIO max pulses: {self.pi.wave_get_max_pulses()}")
        print(f"PiGPIO max cbs:    {self.pi.wave_get_max_cbs()}")

    def on(self):
        print(f"Switching the music puncher ON")
        self.status_led.set(Status.ON)
        self.steppers.on()

    def off(self, reset=False):
        if reset:
            try:
                self.reset()
            except Exception as e:
                print(f"Failed reset: {repr(e)}")

        print(f"Switching the music puncher OFF")
        try:
            self.steppers.off()
            self.status_led.set(Status.OFF)
        except Exception as e:
            print(f"Failed to switch the music puncher off: {repr(e)}")

    def calibrate(self):
        try:
            self.__do_calibrate()
        except:
            self.off(reset=True)
            raise

    def __do_calibrate(self):
        self.on()
        self.reset()
        self.__move(0, self.row0 - self.position)
        self.puncher.punch()
        self.__move(0, round((self.keyboard.size() - 1) * self.tone_steps) - self.position)
        self.puncher.punch()
        self.__move(self.feed_steps * 2, 0)
        self.puncher.punch()
        self.__move(0, self.row0 - self.position)
        self.puncher.punch()
        self.__move(0, self.idle_position - self.position)
        self.off()

    def run(self, notesequence: NoteSequence, ):
        self.on()
        try:
            self.reset()

            steps = self.__calculate_all_steps(notesequence)
            self.do_run(steps)
            self.off()
        except:
            self.off(reset=True)
            raise

    def __calculate_all_steps(self, notesequence: NoteSequence):
        """returns a list of tuples with (delay, note) steps for each hole"""
        position = self.position
        steps = []
        for delayNotes in notesequence:
            if delayNotes.notes == []:
                raise (RuntimeError("Empty note set is not supported, consolidate consecutive delays first"))
            positions = sorted(
                [self.row0 + round(self.keyboard.get_index(note) * self.tone_steps) for note in delayNotes.notes])
            if abs(position - positions[-1]) < abs(position - positions[0]):
                positions.reverse()  # Start from nearest end
            delay = round(delayNotes.delay * self.feed_steps)
            for targetPosition in positions:
                tuple = (delay, targetPosition - position)
                if tuple != (0, 0):
                    steps.append(tuple)
                position = targetPosition
                delay = 0
        return steps

    def do_run(self, steps):
        total_time_steps = 0
        for step in steps:
            # print(f"{step[1]}")
            total_time_steps += step[0]

        cutter_step = total_time_steps + self.cutter_position
        did_cut = False

        total_time_steps = 0
        for idx, step in enumerate(steps):
            # if idx == 0:
            #     self.steppers.prepare_waveform(step)
            # self.steppers.create_and_send_wave()  # run wave prepared for previous step
            # if idx < len(steps) - 1:
            #     self.steppers.prepare_waveform([steps[idx + 1][0], steps[idx + 1][1]])
            # self.steppers.wait_for_wave()

            self.steppers.prepare_waveform(step)
            self.steppers.create_and_send_wave()
            self.steppers.wait_for_wave()

            self.position += step[1]
            self.puncher.punch()
            total_time_steps += step[0]

            if not did_cut and total_time_steps >= cutter_step:
                self.cutter.cut()
                did_cut = True

        if not did_cut:
            if self.cutter_position > 0:
                self.__move(self.cutter_position, self.idle_position - self.position)
            self.cutter.cut()

        if self.end_feed > 0:
            self.__move(self.end_feed, self.idle_position - self.position)

        self.__move(0, self.idle_position - self.position)  # will do nothing if already in position

    def __move(self, feedsteps, tonesteps):
        if feedsteps == 0 and tonesteps == 0:
            return
        self.steppers.prepare_waveform([feedsteps, tonesteps])
        self.steppers.create_and_send_wave()
        self.steppers.wait_for_wave()
        self.position += tonesteps

    def reset(self):
        print('> reset')
        if self.zero_button:
            self.steppers.steppers[1].move_until(-1, lambda: self.zero_button.is_on())
            self.position = 0
            self.__move(0, self.idle_position)
        else:
            print(f"Assuming that the puncher is manually aligned at step {self.idle_position}")
            self.position = self.idle_position
        print('< reset')


class Button:
    def __init__(self, pi: pigpio.pi, config):
        self.pi = pi
        self.pin = config['pin']
        self.pi.set_mode(self.pin, pigpio.INPUT)
        self.pi.set_pull_up_down(self.pin, pigpio.PUD_DOWN)

    def is_on(self):
        return self.pi.read(self.pin) == 1

    def is_off(self):
        return self.pi.read(self.pin) == 0


class Puncher:
    def __init__(self, pi: pigpio.pi, config):
        self.pi = pi
        self.pin = config['pin']
        self.on_length = config['on-length']
        self.off_length = config['off-length']
        self.pi.set_mode(self.pin, pigpio.OUTPUT)

    def punch(self):
        # print(f"punch")
        self.pi.write(self.pin, 1)
        sleep(self.on_length)
        self.pi.write(self.pin, 0)
        sleep(self.off_length)


class Cutter:
    def __init__(self, pi: pigpio.pi, config):
        self.pi = pi
        self.pin = config['pin']
        self.on_length = config['on-length']
        self.off_length = config['off-length']
        self.pi.set_mode(self.pin, pigpio.OUTPUT)

    def cut(self):
        # print(f"cut")
        self.pi.write(self.pin, 1)
        sleep(self.on_length)
        self.pi.write(self.pin, 0)
        sleep(self.off_length)


class Status(Enum):
    ON = auto()
    OFF = auto()
    ERROR = auto()


class StatusLed:
    def __init__(self, pi: pigpio.pi, config):
        self.pi = pi
        self.pins = [config['red-pin'], config['green-pin'], config['blue-pin']]
        self.colors = {
            Status.ON: config['rgb-on'],
            Status.OFF: config['rgb-off'],
            Status.ERROR: config['rgb-error']
        }
        for pin in self.pins:
            self.pi.set_mode(pin, pigpio.OUTPUT)

    def set(self, status: Status):
        rgb = self.colors[status]
        for idx, value in enumerate(rgb):
            pin = self.pins[idx]
            self.pi.set_PWM_dutycycle(pin, value)


class DummyStatusLed:
    def set(self, status: Status):
        pass


def calculate_acceleration_profile(min_sps, max_sps, acceleration):
    "Returns a list of delays in microseconds"
    profile = []

    sps = min_sps
    while sps < max_sps:
        profile.append(round(1000000 / sps))
        sps += acceleration * (1 / sps)
    return profile


class PiGPIOStepperMotor(object):

    def __init__(self, pi: pigpio.pi, config):
        self.pi = pi
        self.enable_pin = config['enable-pin']
        self.dir_pin = config['dir-pin']
        self.step_pin = config['step-pin']
        self.reverse = config['reverse-dir']
        self.acceleration_profile = calculate_acceleration_profile(config['min-sps'], config['max-sps'],
                                                                   config['acceleration'])
        self.min_delay = 1 / config['max-sps']
        self.max_delay = 1 / config['min-sps']

        pi.set_mode(self.dir_pin, pigpio.OUTPUT)
        pi.set_mode(self.step_pin, pigpio.OUTPUT)

    def on(self):
        self.pi.write(self.enable_pin, 1)

    def off(self):
        self.pi.write(self.enable_pin, 0)

    # def __set_dir(self, dir: int):
    #     dir = dir * -1 if self.reverse else dir
    #     self.pi.write(self.dir_pin, 0 if dir < 0 else 1)

    def __is_dir_enable(self, steps: int) -> bool:
        enable = steps > 0
        if self.reverse:
            enable = not enable
        return enable

    def __step(self, delay):
        self.pi.write(self.step_pin, 1)
        sleep(delay / 2)
        self.pi.write(self.step_pin, 0)
        sleep(delay / 2)

    def move_until(self, dir: int, condition):
        """Slowly moves the motor in the given direction (-1,+1) until the condition becomes true"""
        # self.__set_dir(dir)
        self.pi.write(self.dir_pin, 1 if self.__is_dir_enable(dir) else 0)
        while not condition():
            self.__step(self.max_delay)

    def create_move_waveform(self, steps: int) -> List[pigpio.pulse]:
        # self.__set_dir(-1 if steps < 0 else 1)
        dir_enable = 0
        dir_disable = 0
        if self.__is_dir_enable(steps):
            dir_enable = 1 << self.dir_pin
        else:
            dir_disable = 1 << self.dir_pin

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
            pulses.append(pigpio.pulse(1 << self.step_pin | dir_enable, dir_disable, delay_us >> 1))
            pulses.append(pigpio.pulse(0, 1 << self.step_pin, delay_us >> 1))
            dir_enable = 0
            dir_disable = 0

        return pulses


class Steppers:
    """Class for controlling synchronous movements of multiple stepper motors"""

    def __init__(self, pi: pigpio.pi, steppers: List[PiGPIOStepperMotor]):
        self.pi = pi
        self.steppers = steppers

    def on(self):
        for stepper in self.steppers:
            stepper.on()

    def off(self):
        for stepper in self.steppers:
            stepper.off()

    def prepare_waveform(self, steps: List[int]):
        """
           Prepares the next wave form. Can be called between create_and_send_wave and wait_for_wave in order to prepare
           the next waveform while executing the previous one
        """
        # print(f"Prepare waveforms for {steps}")
        self.pi.wave_clear()
        waves = [self.steppers[idx].create_move_waveform(s) for idx, s in enumerate(steps)]
        self.prepared_wave_length = self.__synchronize(waves) / 1000000

        for wave in waves:
            self.__add_wave(wave)

    def create_and_send_wave(self):
        id = self.pi.wave_create()
        if id < 0:
            raise RuntimeError(f"pigpio error on wave_create: {id}")
        self.pi.wave_send_once(id)
        self.expected_wave_end_time = time() + self.prepared_wave_length

    def wait_for_wave(self):
        now = time()
        expected_end = self.expected_wave_end_time + 0.001
        if expected_end > now:
            sleep(expected_end - now)
        while self.pi.wave_tx_busy():  # wait for waveform to be sent
            sleep(0.1)  # it should be really exceptional to we arrive here

    def __add_wave(self, pulses: List[pigpio.pulse]):
        delay = 0
        while len(pulses) > 0:
            # Submit long waves in parts to avoid hitting pigpio package size limits
            # This only marginally helps, because the next limit is total number of pulses
            part = pulses[:5000]
            pulses = pulses[5000:]
            if delay > 0:
                part.insert(0, pigpio.pulse(0, 0, delay))
            delay += self.__wavelength(part[1:])
            self.pi.wave_add_generic(part)

    def __wavelength(self, pulses):
        l = 0
        for pulse in pulses:
            l += pulse.delay
        return l

    def __synchronize(self, waves: List[List[pigpio.pulse]]) -> int:
        """Scales the wave to the longest to have the same length, and returns the length in microseconds"""

        filtered = [wave for wave in waves if wave != []]
        if len(filtered) == 0:
            return 0
        if len(filtered) == 1:
            return self.__wavelength(filtered[0])

        def scale(pulses, factor):
            for pulse in pulses:
                pulse.delay = round(pulse.delay * factor)

        lengths = [self.__wavelength(wave) for wave in filtered]

        maxlen = max(lengths)
        for idx, wave in enumerate(filtered):
            l = lengths[idx]
            if l != maxlen:
                scale(wave, maxlen / l)
        return maxlen
