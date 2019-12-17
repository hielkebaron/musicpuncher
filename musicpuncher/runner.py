import re
from typing import List, Set

from mido import MidiFile

MIN_VELOCITY = 20  # PPP


class TimeNotes(object):
    def __init__(self, delay: float, notes: List[int]):
        self.delay = delay
        self.notes = notes


NoteSequence = List[TimeNotes]


class MidiProcessor(object):

    def __init__(self, notes: NoteSequence, adapter):
        self.notes = notes
        self.adapter = adapter
        noteset = get_notes(notes)
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
            self.adapter.move(delay=delay)
        else:
            note_list = sorted([note + self.transposition for note in notes])
            # print(f"note_list: {note_list}")
            if abs(self.last_note - note_list[0]) > abs(self.last_note - note_list[-1]):
                note_list.reverse()
            for note in note_list:
                self.adapter.move(note=note, delay=delay)
                self.adapter.punch()
                self.last_note = note
                delay = 0


def get_notes(notes: NoteSequence) -> Set[int]:
    noteset = set()
    for tuple in notes:
        noteset.update(tuple.notes)
    return noteset


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
                if len(notes_on) > 0:
                    notes.append(TimeNotes(delta, list(notes_on)))
                    delta = 0
                delta += msg.time
                notes_on.clear()
    return notes


def __print_notes(noteseq: NoteSequence):
    for notes in noteseq:
        print(f"{notes.delay}: {notes.notes}")


def __parseAdjustments(adjustments: str):
    adjustmentDict = dict()
    if adjustments == '':
        return adjustmentDict
    splitted = adjustments.split(',')
    for split in splitted:
        matchObj = re.match( r'(\d+)([+]+|[-]+)', split)
        if matchObj:
            note = int(matchObj.group(1))
            adj = matchObj.group(2)
            adjusted = note
            for c in adj:
                if c == '+':
                    adjusted += 12
                elif c == '-':
                    adjusted -= 12
            adjustmentDict[note] = adjusted
        else:
           raise RuntimeError(f"Illegal adjustment specification: {adjustments}")
    return adjustmentDict

def __adjust(noteseq: NoteSequence, adjustments: str):
    adjustmentDict = __parseAdjustments(adjustments)
    print(f"Adjustments: {adjustmentDict}")
    for notes in noteseq:
        newnotes = set()
        for note in notes.notes:
            if note in adjustmentDict:
                newnotes.add(adjustmentDict[note])
            else:
                newnotes.add(note)
        notes.notes = newnotes

def punch(file: str, adapter, adjustments: str):
    notes = __parse_midi(file)
    __adjust(notes, adjustments)
    # __print_notes(notes)

    processor = MidiProcessor(notes, adapter)

    processor.process()
