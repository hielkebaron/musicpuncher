from .keyboard import Keyboard
from .music import parse_midi, adjust, transpose, write_midi
from .pigpio_puncher import PiGPIOPuncher


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
