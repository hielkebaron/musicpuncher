from time import time

from .keyboard import Keyboard
from .music import parse_midi, adjust, transpose, write_midi
from .music_puncher import MusicPuncher


def punch(file: str, adjustments: str, puncher_config, outfile: str = None,
          address: str = 'localhost', port: int = 8888):
    keyboard = Keyboard(puncher_config['keyboard'])
    notes = parse_midi(file)
    adjust(notes, adjustments)
    transpose(notes, keyboard)
    # print_notes(notes)

    if not outfile == None:
        write_midi(notes, outfile)
    else:
        puncher = MusicPuncher(puncher_config, keyboard, notes, address=address, port=port)
        start_time = time()
        puncher.run()
        end_time = time()
        print(f"Done in {round(end_time - start_time)} seconds")
