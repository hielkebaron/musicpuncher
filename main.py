import argparse
import os
import sys

import yaml

if os.getenv("MOCK_PIGPIO") == 'true':
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
    parser.add_argument("--adjust", help="Adjust notes. Example: --adjust '32+,99--' will replace 32 by 44"
                                         " (+ one octave) and 99 by 75 (- two octaves)", default='')
    parser.add_argument("-o", "--out", help="Write the resulting midi to the given midi file instead of punching it")
    args = parser.parse_args()

    with open(r'config.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    puncher_config = config['music-puncher']
    punch(args.file, args.adjust, puncher_config, address=args.address, port=args.port, outfile = args.out)


run()
