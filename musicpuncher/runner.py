from mido import MidiFile

from .keyboard import Keyboard
from .puncher_adapter import DebugAdapter

MIN_VELOCITY = 20  # PPP


class MidiProcessor(object):
    @staticmethod
    def __get_notes(filename: str):
        noteset = set()
        with MidiFile(filename) as mid:
            for msg in mid:
                if (msg.type == 'note_on' or msg.type == 'note_off'):
                    noteset.add(msg.note)
        return noteset

    def __init__(self, filename: str, adapter):
        self.filename = filename
        self.adapter = adapter
        noteset = MidiProcessor.__get_notes(filename)
        self.transposition = adapter.keyboard.calculate_transposition(noteset)
        print(f"Notes: {sorted(noteset)}")
        print(f"Transposing by {self.transposition}")

    def process(self):
        self.adapter.reset()
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
            self.adapter.move(0, delta)
        else:
            note_list = sorted(notes)
            if abs(self.last_note - note_list[0]) > abs(self.last_note - note_list[-1]):
                note_list.reverse()
            for note in note_list:
                self.adapter.move(note, delta)
                self.adapter.punch()
                self.last_note = note
                delta = 0


def run(args):
    #                    c   d   e   f   g   a   b   c   d   e   f   g   a   b   c
    keyboard = Keyboard([48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72])
    adapter = DebugAdapter(keyboard)
    processor = MidiProcessor(args[1], adapter)

    processor.process()
