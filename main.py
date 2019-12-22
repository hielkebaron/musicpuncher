import argparse
import os
import sys

if os.getenv("MOCK_PIGPIO"):
    sys.modules['pigpio'] = __import__('pigpio_mock')

from musicpuncher.keyboard import Keyboard
from musicpuncher.runner import punch


def run():
    # initiate the parser with a description
    parser = argparse.ArgumentParser(description='Controls the Music Puncher')
    parser.add_argument('file', metavar='FILE', type=str, help='midi file to punch')
    parser.add_argument("-a", "--address", help="address of the Music Puncher (defaults to 'localhost')",
                        default="localhost")
    parser.add_argument("-p", "--port", help="port of the pigpio daemon (defaults to 8888)", type=int, default=8888)
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("--no-act", help="write commands to stdout but don't control an actual punching machine",
                        action="store_true")
    parser.add_argument("--timed",
                        help="implies --no-act, but emulates some processing time so web can be tested more easily",
                        action="store_true")
    parser.add_argument("--adjust", help="Adjust notes. Example: --adjust '32+,99--' will replace 32 by 44"
                                         " (+ one octave) and 99 by 75 (- two octaves)", default='')
    parser.add_argument("-o", "--out", help="Write the resulting midi to the given midi file instead of punching it")
    args = parser.parse_args()

    #                    c   d   e   f   g   a   b   c   d   e   f   g   a   b   c
    keyboard = Keyboard([48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72])

    #                    c   d   g   a   b   c   d   e   f   f+  g   g+  a   a+  b   c   c+  d   d+  e   f   f+  g   g+  a   a+   b   c   d   e
    # keyboard = Keyboard(
    #     [48, 50, 55, 57, 59, 60, 62, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84,
    #      86, 88])

    punch(args.file, args.adjust, args.out, keyboard, address=args.address, port=args.port)


run()
