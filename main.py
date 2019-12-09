import sys
from mido import MidiFile

MIN_VELOCITY = 20  # PPP

class DebugTarget(object):
    def reset(self):
        print('* reset *')

    def move(self, delta_tone, delta_time):
        print(f"move({delta_tone}, {delta_time})")

    def punch(self):
        print(f"punch")


class MusicPuncher(object):
    def __init__(self, target):
        self.target = target

    def reset(self):
        self.target.reset()
        self.head = 0

    def punch(self, delta, notes):
        if len(notes) == 0:
            self.target.move(0, delta)
        else:
            note_list = sorted(notes)
            if abs(self.head - note_list[0]) > abs(self.head - note_list[-1]):
                note_list.reverse()
            for note in note_list:
                delta_tone = note - self.head
                self.target.move(delta_tone, delta)
                self.target.punch()
                self.head = note
                delta = 0


def process(target, filename):
    mid = MidiFile(filename)
    puncher = MusicPuncher(target)
    puncher.reset()

    notes_on = set()
    delta = 0.0
    for msg in mid:
        if not msg.is_meta:
            if msg.type == 'note_on' and msg.velocity >= MIN_VELOCITY:
                notes_on.add(msg.note)
            if (msg.type == 'note_on' or msg.type == 'note_off') and msg.time != 0:
                puncher.punch(delta, notes_on)
                delta = msg.time
                notes_on.clear()

process(DebugTarget(), sys.argv[1])
