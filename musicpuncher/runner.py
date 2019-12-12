from typing import List, Tuple

from mido import MidiFile

from .keyboard import Keyboard
from .puncher_adapter import DebugAdapter

MIN_VELOCITY = 20  # PPP

class TimeNotes(object):
    def __init__(self, delta: float, notes: List[int]):
        self.delta = delta
        self.notes = notes

NoteList = List[TimeNotes]

class MidiProcessor(object):
    @staticmethod
    def __get_notes(notes: NoteList):
        noteset = set()
        for tuple in notes:
            noteset.update(tuple.notes)
        return noteset

    def __init__(self, notes: NoteList, adapter):
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
            self.__punch(tuple.delta, tuple.notes)

    def __punch(self, delta, notes):
        if len(notes) == 0:
            self.adapter.move(0, delta)
        else:
            note_list = sorted([note + self.transposition for note in notes])
            if abs(self.last_note - note_list[0]) > abs(self.last_note - note_list[-1]):
                note_list.reverse()
            for note in note_list:
                self.adapter.move(note, delta)
                self.adapter.punch()
                self.last_note = note
                delta = 0

def __parse_midi(filename: str) -> NoteList:
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
    return notes


def run(args):
    #                    c   d   e   f   g   a   b   c   d   e   f   g   a   b   c
    keyboard = Keyboard([48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72])
    adapter = DebugAdapter(keyboard)
    notes = __parse_midi(args[1])
    processor = MidiProcessor(notes, adapter)

    processor.process()
