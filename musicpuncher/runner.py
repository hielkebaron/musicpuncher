from time import time

from .keyboard import Keyboard
from .music import parse_midi, adjust, transpose, write_midi, print_notes
from .music_puncher import MusicPuncher


def punch(file: str, adjustments: str, puncher_config, outfile: str = None,
          address: str = 'localhost', port: int = 8888):
    keyboard = Keyboard(puncher_config['keyboard'])
    notes = parse_midi(file)
    adjust(notes, adjustments)
    transpose(notes, keyboard)
    # print_notes(notes)

    if outfile:
        write_midi(notes, outfile)
    else:
        puncher = MusicPuncher(puncher_config, keyboard, address=address, port=port)
        start_time = time()
        try:
            puncher.run(notes)
        except KeyboardInterrupt:
            print("Interrupted!")
            pass
        end_time = time()
        print(f"Done in {round(end_time - start_time)} seconds")

def calibrate(puncher_config, address: str = 'localhost', port: int = 8888):
    keyboard = Keyboard(puncher_config['keyboard'])
    puncher = MusicPuncher(puncher_config, keyboard, address=address, port=port)
    puncher.calibrate()
