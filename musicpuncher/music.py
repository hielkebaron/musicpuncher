import re
import sys
from collections import deque
from types import SimpleNamespace
from typing import List, Set, Dict, Iterable

from mido import MidiFile, MidiTrack, Message, second2tick, MetaMessage

from .keyboard import Keyboard

MIN_VELOCITY = 20  # PPP


class DelayNotes(object):
    def __init__(self, delay: float, notes: Iterable[int]):
        self.delay = delay
        self.notes = sorted(notes)

    def __eq__(self, other):
        if not isinstance(other, DelayNotes):
            return NotImplemented

        return self.delay == other.delay and self.notes == other.notes

    def __repr__(self):
        return f"DelayNotes({self.delay}, {self.notes})"


NoteSequence = List[DelayNotes]


def get_notes(notes: NoteSequence) -> Set[int]:
    noteset = set()
    for tuple in notes:
        noteset.update(tuple.notes)
    return noteset


def parse_midi(filename: str = None, file=None) -> NoteSequence:
    """Returns a list of (timedelta, notelist) tuples"""
    notes = []
    with MidiFile(filename=filename, file=file) as mid:
        notes_on = set()
        delta = 0
        for msg in mid:
            # print(f"{msg.type}: {msg}")
            # if (msg.type == 'note_on' or msg.type == 'note_off' or msg.type == 'time_signature') and msg.time != 0:
            if msg.time != 0:
                if len(notes_on) > 0:
                    notes.append(DelayNotes(delta, list(notes_on)))
                    delta = 0
                delta += msg.time
                notes_on.clear()
            if msg.type == 'note_on' and msg.velocity >= MIN_VELOCITY:
                notes_on.add(msg.note)
    return notes


def print_notes(noteseq: NoteSequence):
    for notes in noteseq[:4]:
        print(f"{notes.delay:0.4f}: {notes.notes}")


def __parseAdjustments(adjustments: str) -> Dict[int, int]:
    adjustmentDict = dict()
    if adjustments == '':
        return adjustmentDict
    splitted = adjustments.split(',')
    for split in splitted:
        matchObj = re.match(r'(\d+)([+]+|[-]+)', split)
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


def __apply_adjustments(noteseq: NoteSequence, adjustmentDict: Dict[int, int]) -> NoteSequence:
    print(f"Adjustments: {adjustmentDict}")

    result = []
    for delayNotes in noteseq:
        newnotes = set()
        for note in delayNotes.notes:
            if note in adjustmentDict:
                if adjustmentDict[note] != sys.maxsize:
                    newnotes.add(adjustmentDict[note])
            else:
                newnotes.add(note)
        delayNotes.notes = newnotes
        result.append(DelayNotes(delayNotes.delay, newnotes))
    return result


def __apply_transposition(noteseq: NoteSequence, transposition: int) -> NoteSequence:
    result = []
    for delayNotes in noteseq:
        newnotes = set()
        for note in delayNotes.notes:
            newnotes.add(note + transposition)
        result.append(DelayNotes(delayNotes.delay, newnotes))
    return result


def consolidate(noteseq: NoteSequence) -> NoteSequence:
    result = []
    increment = 0
    for idx, delayNotes in enumerate(noteseq):
        if len(delayNotes.notes) == 0:
            increment += delayNotes.delay
        else:
            newNotes = DelayNotes(delayNotes.delay + increment, delayNotes.notes)
            increment = 0
            result.append(newNotes)
    return result


def adjust(noteseq: NoteSequence, adjustments: str) -> NoteSequence:
    adjustmentDict = __parseAdjustments(adjustments)
    return __apply_adjustments(noteseq, adjustmentDict)


def transpose(noteseq: NoteSequence, keyboard: Keyboard) -> NoteSequence:
    noteset = get_notes(noteseq)
    transposition = keyboard.calculate_transposition(noteset)
    return __apply_transposition(noteseq, transposition)


def autofit(noteseq: NoteSequence, keyboard: Keyboard, transposition: int) -> NoteSequence:
    noteset = get_notes(noteseq)
    print(f"Notes: {sorted(noteset)}")

    noteseq = __apply_transposition(noteseq, transposition)
    noteset = get_notes(noteseq)
    print(f"Transposed: {sorted(noteset)}")

    adjustments = keyboard.calculate_adjustments(noteset)
    return __apply_adjustments(noteseq, adjustments)


def write_midi(noteseq: NoteSequence, outfile):
    ticks_per_beat = 1000
    us_per_tick = 100000
    mid = MidiFile(ticks_per_beat=ticks_per_beat)
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(Message('program_change', program=11, time=0))
    track.append(MetaMessage('set_tempo', tempo=us_per_tick))

    # Default ticks/beat is 480, with 500000 us/beat
    TICKS_PER_SECOND = second2tick(1, ticks_per_beat, us_per_tick)
    # print(f"Ticks per second: {TICKS_PER_SECOND}")
    VELOCITY = 75
    NOTE_LENGTH = 500
    off_queue = deque([])

    def pop_until(until, elapsed):
        while len(off_queue) > 0 and off_queue[0].time <= until:
            nxt = off_queue.popleft()
            track.append(Message('note_off', note=nxt.note, velocity=0, time=nxt.time - elapsed))
            elapsed = nxt.time
        return elapsed

    elapsed = 0
    for notes in noteseq:
        timestamp = elapsed + round(notes.delay * TICKS_PER_SECOND)
        elapsed = pop_until(timestamp, elapsed)
        for note in notes.notes:
            track.append(Message('note_on', note=note, velocity=VELOCITY, time=timestamp - elapsed))
            elapsed = timestamp
            off_queue.append(SimpleNamespace(note=note, time=timestamp + NOTE_LENGTH))

    pop_until(sys.maxsize, elapsed)

    mid.save(outfile)
