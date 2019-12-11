from gpiozero import Button

from .keyboard import Keyboard
from .stepper import StepperMotor


class DebugAdapter(object):
    def __init__(self, keyboard: Keyboard):
        self.keyboard = keyboard
        self.position = None

    def reset(self):
        print('* reset *')
        self.position = 0

    def move(self, note: int, delta_time: float):
        row = self.keyboard.get_index(note)
        delta = row - self.position
        print(f"move({delta}, {delta_time})")
        self.position = row

    def punch(self):
        print(f"punch")


class PuncherAdapter(object):
    ROW0 = 100  # Number of steps from neutral position to ROW 0
    ROW_STEPS = 100  # Number of steps per row
    TIME_STEPS = 100  # Number of steps per time unit

    def __init__(self, keyboard: Keyboard):
        self.keyboard = keyboard
        self.time_stepper = StepperMotor(12, 16, 10, 20, 10)
        self.row_stepper = StepperMotor(20, 21, 10, 20, 10)
        self.zero_button = Button(2)
        self.position = None

    def reset(self):
        print('* reset *')
        self.row_stepper.move_until(lambda: self.zero_button.is_pressed())
        self.row_stepper.move(self.ROW0)
        self.position = 0

    def move(self, note: int, delta_time: float):
        row = self.keyboard.get_index(note)
        delta = row - self.position
        print(f"move({delta}, {delta_time})")
        self.time_stepper.move(round(delta_time * self.TIME_STEPS))
        self.row_stepper.move(delta * self.ROW_STEPS)
        self.position = row

    def punch(self):
        print(f"punch")
