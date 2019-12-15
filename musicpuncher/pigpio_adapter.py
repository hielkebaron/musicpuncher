from time import sleep

import pigpio

MIN_SPS = 1000  # steps per second
MAX_SPS = 2000  # steps per second
ACCELERATION = 400  # SPS per second
from .keyboard import Keyboard

class PiGPIOPuncherAdapter(object):
    ROW0 = 100  # Number of steps from neutral position to ROW 0
    ROW_STEPS = 100  # Number of steps per row
    TIME_STEPS = 100  # Number of steps per time unit

    def __init__(self, keyboard: Keyboard, address: str = 'localhost', port: int = 8888):
        self.pi = pigpio.pi(address, port)
        if not self.pi.connected:
            raise RuntimeError(f"PI Not connected, make sure the pi is available on {address} and is running pigpiod on port {port}")

        self.keyboard = keyboard
        self.time_stepper = PiGPIOStepperMotor(self.pi, 17, 18, MIN_SPS, MAX_SPS, ACCELERATION)
        self.row_stepper = PiGPIOStepperMotor(self.pi, 22, 23, MIN_SPS, MAX_SPS, ACCELERATION)
        # self.zero_button = Button(2)
        # self.punch_pin = OutputDevice(3)
        self.punch_pin = 3
        self.pi.set_mode(3, pigpio.OUTPUT)
        self.position = None

    def reset(self):
        print('* reset *')
        # self.row_stepper.move_until(-1, self.zero_button.is_pressed)
        # self.row_stepper.move(self.ROW0)
        self.position = 0

    def move(self, note: int, delay: float):
        print()
        self.pi.wave_clear()

        print(f"move(note={note}, delay={delay}")

        moved = self.time_stepper.move(round(delay * self.TIME_STEPS))
        if note != 0: # HACK voor rij zonder noten
            row = self.keyboard.get_index(note)
            delta = row - self.position
            moved = moved or self.row_stepper.move(delta * self.ROW_STEPS)
            self.position = row

        if moved:
            id = self.pi.wave_create()
            if id < 0:
                raise RuntimeError(f"pigpio error on wave_create: {id}")
            cbs = self.pi.wave_send_once(id)
            print(f"Send waveform with {cbs} control blocks")

            while self.pi.wave_tx_busy():  # wait for waveform to be sent
                sleep(0.1)
            print(f"Waveform has ended")
            self.pi.wave_clear()
        print()


    def punch(self):
        print(f"punch")
        self.pi.write(self.punch_pin, 1)
        sleep(0.2)
        self.pi.write(self.punch_pin, 0)
        sleep(0.3)

def calculate_acceleration_profile(min_sps, max_sps, acceleration):
    profile = []

    sps = min_sps
    while sps < max_sps:
        profile.append(1 / sps)
        sps += acceleration * (1 / sps)
    return profile


class PiGPIOStepperMotor(object):

    def __init__(self, pi: pigpio.pi, dir_pin, step_pin, min_sps, max_sps, acceleration):
        # self.dir_pin = OutputDevice(dir_pin)
        # self.step_pin = OutputDevice(step_pin)
        self.pi = pi
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.acceleration_profile = calculate_acceleration_profile(min_sps, max_sps, acceleration)
        self.min_delay = 1 / max_sps
        self.max_delay = 1 / min_sps

        pi.set_mode(dir_pin, pigpio.OUTPUT)
        pi.set_mode(step_pin, pigpio.OUTPUT)

        # print(f"Acceleration profile (ms): {[round(delay * 1000) for delay in self.acceleration_profile]}")
        # print(f"pulses per second {[round(1 / delay) for delay in self.acceleration_profile]}")

    def __set_dir(self, dir: int):
        self.pi.write(self.dir_pin, 0 if dir < 0 else 1)

    def __step(self, delay):
        # self.step_pin.on()
        sleep(delay / 2)
        # self.step_pin.off()
        sleep(delay / 2)

    def move_until(self, dir: int, condition):
        """Slowly moves the motor in the given direction (-1,+1) until the condition becomes true"""
        self.__set_dir(dir)
        while not condition():
            self.__step(self.max_delay)

    def move(self, steps: int) -> bool:
        print(f"MOVE {self.step_pin} {steps}")
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
            pulses.append(pigpio.pulse(1 << self.step_pin, 0, round(delay * 1000000 / 2)))
            pulses.append(pigpio.pulse(0, 1 << self.step_pin, round(delay * 1000000 / 2)))

        if len(pulses) > 0:
            count = self.pi.wave_add_generic(pulses)
            print(f"Added {len(pulses)} pulses, total is {count}")
            return True
        return False
