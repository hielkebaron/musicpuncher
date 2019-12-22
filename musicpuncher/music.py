import re
import sys
from collections import deque
from types import SimpleNamespace
from typing import List, Set

from mido import MidiFile, MidiTrack, Message

from .keyboard import Keyboard

MIN_VELOCITY = 20  # PPP


class DelayNotes(object):
    def __init__(self, delay: float, notes: List[int]):
        self.delay = delay
        self.notes = notes


NoteSequence = List[DelayNotes]


def get_notes(notes: NoteSequence) -> Set[int]:
    noteset = set()
    for tuple in notes:
        noteset.update(tuple.notes)
    return noteset


def parse_midi(filename: str) -> NoteSequence:
    """Returns a list of (timedelta, notelist) tuples"""
    notes = []
    with MidiFile(filename) as mid:
        notes_on = set()
        delta = 0
        for msg in mid:
            if (msg.type == 'note_on' or msg.type == 'note_off') and msg.time != 0:
                if len(notes_on) > 0:
                    notes.append(DelayNotes(delta, list(notes_on)))
                    delta = 0
                delta += msg.time
                notes_on.clear()
            if msg.type == 'note_on' and msg.velocity >= MIN_VELOCITY:
                notes_on.add(msg.note)
    return notes


def print_notes(noteseq: NoteSequence):
    for notes in noteseq:
        print(f"{notes.delay}: {notes.notes}")


def __parseAdjustments(adjustments: str):
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


def adjust(noteseq: NoteSequence, adjustments: str):
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


def transpose(noteseq: NoteSequence, keyboard: Keyboard):
    noteset = get_notes(noteseq)
    transposition = keyboard.calculate_transposition(noteset)

    for notes in noteseq:
        newnotes = set()
        for note in notes.notes:
            newnotes.add(note + transposition)
        notes.notes = newnotes

    print(f"Notes: {sorted(noteset)}")
    print(f"Transposed by {transposition}")


def write_midi(noteseq: NoteSequence, outfile):
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(Message('program_change', program=11, time=0))

    TICKS_PER_SECOND = 1000
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
