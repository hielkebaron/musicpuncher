from .music import parse_midi, adjust, transpose, write_midi
from .keyboard import Keyboard
from .pigpio_adapter import PiGPIOPuncher

# class MidiProcessor(object):
#
#     def __init__(self, notes: NoteSequence, adapter):
#         self.notes = notes
#         self.adapter = adapter
#
#     def process(self):
#         self.adapter.reset()
#         self.last_note = 0  # we remember last note so we can optimize the order
#
#         for tuple in self.notes:
#             self.__punch(tuple.delay, tuple.notes)
#
#     def __punch(self, delay, notes):
#         if len(notes) == 0:
#             self.adapter.move(delay=delay)
#         else:
#             note_list = sorted(notes)
#             if abs(self.last_note - note_list[0]) > abs(self.last_note - note_list[-1]):
#                 note_list.reverse()
#             for note in note_list:
#                 self.adapter.move(note=note, delay=delay)
#                 self.adapter.punch()
#                 self.last_note = note
#                 delay = 0




def punch(file: str, adjustments: str, outfile: str, keyboard: Keyboard, address: str = 'localhost', port: int = 8888):
    notes = parse_midi(file)
    adjust(notes, adjustments)
    transpose(notes, keyboard)
    # print_notes(notes)

    if not outfile == None:
        write_midi(notes, outfile)
    else:
        puncher = PiGPIOPuncher(keyboard, notes, address=address, port=port)
        puncher.run()
        # processor = MidiProcessor(notes, adapter)
        # processor.process()
