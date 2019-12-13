from typing import List, Set

from mido import MidiFile
from gpiozero import Button

from .stepper import StepperMotor
from .keyboard import Keyboard
from .puncher_adapter import DebugAdapter, PuncherAdapter

MIN_VELOCITY = 20  # PPP


class TimeNotes(object):
    def __init__(self, delay: float, notes: List[int]):
        self.delay = delay
        self.notes = notes


NoteSequence = List[TimeNotes]


class MidiProcessor(object):
    @staticmethod
    def __get_notes(notes: NoteSequence) -> Set[int]:
        noteset = set()
        for tuple in notes:
            noteset.update(tuple.notes)
        return noteset

    def __init__(self, notes: NoteSequence, adapter):
        self.notes = notes
        self.adapter = adapter
        noteset = MidiProcessor.__get_notes(notes)
        self.transposition = adapter.keyboard.calculate_transposition(noteset)
        print(f"Notes: {sorted(noteset)}")
        print(f"Transposing by {self.transposition}")

    def process(self):
        self.adapter.reset()
        self.last_note = 0  # we remember last note so we can optimize the order

        for tuple in self.notes:
            self.__punch(tuple.delay, tuple.notes)

    def __punch(self, delay, notes):
        if len(notes) == 0:
            self.adapter.move(0, delay)
        else:
            note_list = sorted([note + self.transposition for note in notes])
            # print(f"note_list: {note_list}")
            if abs(self.last_note - note_list[0]) > abs(self.last_note - note_list[-1]):
                note_list.reverse()
            for note in note_list:
                self.adapter.move(note, delay)
                self.adapter.punch()
                self.last_note = note
                delay = 0


def __parse_midi(filename: str) -> NoteSequence:
    """Returns a list of (timedelta, notelist) tuples"""
    notes = []
    with MidiFile(filename) as mid:
        notes_on = set()
        delta = 0
        for msg in mid:
            if msg.type == 'note_on' and msg.velocity >= MIN_VELOCITY:
                notes_on.add(msg.note)
            if (msg.type == 'note_on' or msg.type == 'note_off') and msg.time != 0:
                notes.append(TimeNotes(delta, list(notes_on)))
                delta = msg.time
                notes_on.clear()
    return notes


def run1(args):
    motor = StepperMotor(12,16,500,1000,100)
    # motor = StepperMotor(20,21,500,1000,100)
    motor.move(10000)
    button = Button(2)
    print(f"Button status: {button.value}")

def run(args):
    #                    c   d   e   f   g   a   b   c   d   e   f   g   a   b   c
    keyboard = Keyboard([48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72])
    # adapter = DebugAdapter(keyboard, timed=False)
    adapter = PuncherAdapter(keyboard)
    notes = __parse_midi(args[1])
    processor = MidiProcessor(notes, adapter)

    processor.process()
