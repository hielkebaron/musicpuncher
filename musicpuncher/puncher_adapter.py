import math
from time import sleep

from gpiozero import Button

from .keyboard import Keyboard
from .stepper import StepperMotor


class DebugAdapter(object):
    def __init__(self, keyboard: Keyboard, timed=False):
        self.keyboard = keyboard
        self.position = None
        self.timed = timed

    def reset(self):
        print('* reset *')
        self.position = 0
        self.__delay(2)

    def move(self, note: int, delay: float):
        row = self.keyboard.get_index(note)
        delta = row - self.position
        emulated_time = math.log(abs(delta) + 1, 2)
        print(f"move({delta}, {delay}) # {emulated_time}")
        self.__delay(emulated_time)
        self.__delay(delay*2)
        self.position = row

    def punch(self):
        print(f"punch")
        self.__delay(1)

    def __delay(self, time):
        if self.timed:
            sleep(time)


MIN_SPS = 1000  # steps per second
MAX_SPS = 2000  # steps per second
ACCELERATION = 400  # SPS per second


class PuncherAdapter(object):
    ROW0 = 100  # Number of steps from neutral position to ROW 0
    ROW_STEPS = 100  # Number of steps per row
    TIME_STEPS = 100  # Number of steps per time unit

    def __init__(self, keyboard: Keyboard):
        self.keyboard = keyboard
        self.time_stepper = StepperMotor(12, 16, MIN_SPS, MAX_SPS, ACCELERATION)
        self.row_stepper = StepperMotor(20, 21, MIN_SPS, MAX_SPS, ACCELERATION)
        self.zero_button = Button(2)
        self.position = None

    def reset(self):
        print('* reset *')
        # self.row_stepper.move_until(-1, self.zero_button.is_pressed)
        # self.row_stepper.move(self.ROW0)
        self.position = 0

    def move(self, note: int, delay: float):
        # print(f"move({delta}, {delay})")
        self.time_stepper.move(round(delay * self.TIME_STEPS))
        print("move")
        if note != 0: # HACK voor rij zonder noten
            row = self.keyboard.get_index(note)
            delta = row - self.position
            self.row_stepper.move(delta * self.ROW_STEPS)
            self.position = row

    def punch(self):
        print(f"punch")
        sleep(0.5)
