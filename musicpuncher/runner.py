from time import time

from .keyboard import Keyboard
from .music import parse_midi, adjust, autotranspose, write_midi, print_notes, autofit, consolidate
from .music_puncher import MusicPuncher
from .webserver import WebServer


def punch(file: str, adjustments: str, transpose_autofit: int, puncher_config, outfile: str = None):
    keyboard = Keyboard(puncher_config['keyboard'])

    notes = parse_midi(filename=file)
    # print("\nParsed:")
    # print_notes(notes)

    notes = adjust(notes, adjustments)
    # print("\nAdjusted:")
    # print_notes(notes)

    # FIXME Implement autofit, autotranspose and transposition the same as in webserver.py
    # if transpose_autofit != None:
    #     notes = autofit(notes, keyboard, transpose_autofit)
    # else:
    #     notes = transpose(notes, keyboard)
    # print("\nAutofitted/transposed:")
    # print_notes(notes)

    notes = consolidate(notes)
    # print("\nConsolidated:")
    # print_notes(notes)

    if outfile:
        write_midi(notes, filename=outfile)
    else:
        puncher = MusicPuncher(puncher_config, keyboard)
        start_time = time()
        try:
            puncher.run(notes)
        except KeyboardInterrupt:
            print("Interrupted!")
            pass
        end_time = time()
        print(f"Done in {round(end_time - start_time)} seconds")


def calibrate(puncher_config):
    keyboard = Keyboard(puncher_config['keyboard'])
    puncher = MusicPuncher(puncher_config, keyboard)
    puncher.calibrate()


def serve(puncher_config):
    keyboard = Keyboard(puncher_config['keyboard'])
    puncher = MusicPuncher(puncher_config, keyboard)
    config = puncher_config['webserver']
    WebServer(keyboard, puncher, config).run()
