from time import time

from .keyboard import Keyboard
from .music import parse_midi, adjust, transpose, write_midi, print_notes, autofit, consolidate
from .music_puncher import MusicPuncher
from .webserver import WebServer


def punch(file: str, adjustments: str, transpose_autofit: int, puncher_config, outfile: str = None,
          address: str = 'localhost', port: int = 8888):
    keyboard = Keyboard(puncher_config['keyboard'])

    notes = parse_midi(filename=file)
    # print("\nParsed:")
    # print_notes(notes)

    notes = adjust(notes, adjustments)
    # print("\nAdjusted:")
    # print_notes(notes)

    if transpose_autofit != None:
        notes = autofit(notes, keyboard, transpose_autofit)
    else:
        notes = transpose(notes, keyboard)
    # print("\nAutofitted/transposed:")
    # print_notes(notes)

    notes = consolidate(notes)
    # print("\nConsolidated:")
    # print_notes(notes)

    if outfile:
        write_midi(notes, filename=outfile)
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


def serve(puncher_config, address: str = 'localhost', port: int = 8888):
    keyboard = Keyboard(puncher_config['keyboard'])
    puncher = MusicPuncher(puncher_config, keyboard, address=address, port=port)
    WebServer(keyboard, puncher).run()
