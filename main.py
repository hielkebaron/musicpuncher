import sys

from mido import MidiFile

from keyboard import Keyboard

MIN_VELOCITY = 20  # PPP

class DebugTarget(object):
    def __init__(self, keyboard: Keyboard):
        self.keyboard = keyboard
        self.position = None

    def reset(self):
        print('* reset *')
        self.position = 0

    def move(self, tone, delta_time):
        row = self.keyboard.get_index(tone)
        delta = row - self.position
        print(f"move({delta}, {delta_time})")
        self.position = row

    def punch(self):
        print(f"punch")


class MidiProcessor(object):
    @staticmethod
    def __get_notes(filename):
        noteset = set()
        with MidiFile(filename) as mid:
            for msg in mid:
                if (msg.type == 'note_on' or msg.type == 'note_off'):
                    noteset.add(msg.note)
        return noteset

    def __init__(self, filename, target):
        self.filename = filename
        self.target = target
        noteset = MidiProcessor.__get_notes(filename)
        self.transposition = target.keyboard.calculate_transposition(noteset)
        print(f"Notes: {sorted(noteset)}")
        print(f"Transposing by {self.transposition}")

    def process(self):
        self.target.reset()
        self.last_note = 0  # we remember last note so we can optimize the order

        with MidiFile(self.filename) as mid:
            notes_on = set()
            delta = 0
            for msg in mid:
                if msg.type == 'note_on' and msg.velocity >= MIN_VELOCITY:
                    notes_on.add(msg.note + self.transposition)
                if (msg.type == 'note_on' or msg.type == 'note_off') and msg.time != 0:
                    self.__punch(delta, notes_on)
                    delta = msg.time

    def __punch(self, delta, notes):
        if len(notes) == 0:
            self.target.move(0, delta)
        else:
            note_list = sorted(notes)
            if abs(self.last_note - note_list[0]) > abs(self.last_note - note_list[-1]):
                note_list.reverse()
            for note in note_list:
                self.target.move(note, delta)
                self.target.punch()
                self.last_note = note
                delta = 0


#                    c   d   e   f   g   a   b   c   d   e   f   g   a   b   c
keyboard = Keyboard([48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72])
target = DebugTarget(keyboard)
processor = MidiProcessor(sys.argv[1], target)

processor.process()
