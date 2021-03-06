import argparse
import os
import sys
from shutil import copyfile

import yaml

if os.getenv("MOCK_PIGPIO") == 'true':
    sys.modules['pigpio'] = __import__('pigpio_mock')

from musicpuncher.runner import punch, calibrate, serve


def run():
    if not os.path.isfile('config.yaml'):
        copyfile('example_config.yaml', 'config.yaml')
        print('Created config.yaml, please review, adjust where necessary and restart the application')

    # initiate the parser with a description
    parser = argparse.ArgumentParser(description='Controls the Music Puncher')
    parser.add_argument("--adjust", help="Adjust notes. Example: --adjust '32+,99--' will replace 32 by 44"
                                         " (+ one octave) and 99 by 75 (- two octaves)", default='')
    parser.add_argument("--autofit", help="Transposes with given value and auto-adjust notes if possible", type=int)
    parser.add_argument("-o", "--out", help="Write the resulting midi to the given midi file instead of punching it")

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('file', metavar='FILE', nargs='?', type=str, help='midi file to punch')

    group.add_argument("--calibrate", action='store_true',
                       help="Punches a hole on the first and last row, feeds 2 seconds and punches again")

    group.add_argument('--serve', action='store_true',
                       help="Starts the webserver")

    args = parser.parse_args()

    with open(r'config.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    puncher_config = config['music-puncher']

    if args.calibrate:
        calibrate(puncher_config)
    elif args.serve:
        serve(puncher_config)
    else:
        punch(args.file, args.adjust, args.autofit, puncher_config, outfile=args.out)


run()
