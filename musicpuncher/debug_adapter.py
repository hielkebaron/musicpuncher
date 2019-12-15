import math
from time import sleep

from .keyboard import Keyboard


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
        print(f"move({note}, {delay})")
        self.__delay(emulated_time)
        self.__delay(delay * 2)
        self.position = row

    def punch(self):
        print(f"punch")
        self.__delay(1)

    def __delay(self, time):
        if self.timed:
            sleep(time)
