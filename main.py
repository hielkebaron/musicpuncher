import argparse

from musicpuncher.keyboard import Keyboard
from musicpuncher.pigpio_adapter import PiGPIOPuncherAdapter
from musicpuncher.runner import punch


def run():
    # initiate the parser with a description
    parser = argparse.ArgumentParser(description='Controls the Music Puncher')
    parser.add_argument('file', metavar='FILE', type=str, help='midi file to punch')
    parser.add_argument("--address", "-a", help="address of the Music Puncher (defaults to 'localhost')",
                        default="localhost")
    parser.add_argument("--port", "-p", help="port of the pigpio daemon (defaults to 8888", type=int, default=8888)
    args = parser.parse_args()

    #                    c   d   e   f   g   a   b   c   d   e   f   g   a   b   c
    keyboard = Keyboard([48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72])

    adapter = PiGPIOPuncherAdapter(keyboard, address=args.address, port=args.port)

    punch(args.file, adapter)

run()