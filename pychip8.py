#!/usr/bin/env python3

"""
pychip8.py: A simple (read crappy and poorly optimized) CHIP-8 interpreter emulator
for Python 3. The emulator uses pygame for display, events and user input.

Thanks to Alexander Dickson <alex@alexanderdickson.com> which javascript
emulator served as reference for this project.
"""
import logging
import argparse
import sys

from lib import chip8, event_loop, renderer, keyboard

__author__ = 'Sébastien Volle'
__copyright__ = 'Copyright 2013, Sébastien Volle'
__credits__ = ['Sébastien Volle', 'Alexander Dickson']
__version__ = "0.1.0"
__maintainer__ = 'Sébastien Volle'
__email__ = 'sebastien.volle@gmail.com'


def main(args):
    ev = event_loop.EventLoop(args.frequency or chip8.CLOCK_FREQUENCY)
    kb = keyboard.Keyboard(ev)
    ev.set_keyboard(kb)
    rd = renderer.Renderer(chip8.DISPLAY_WIDTH, chip8.DISPLAY_HEIGHT)
    vm = chip8.Chip8(ev, kb, rd)

    logger = logging.getLogger(__name__)
    logger.setLevel('INFO')
    ch = logging.StreamHandler(sys.stdout)
    logger.addHandler(ch)

    if args.debug_pygame:
        ev.set_debug(True)
    if args.debug_chip8:
        vm.set_debug(True)

    vm.load(args.program)
    logger.info('Emulation started. Press Escape to quit')
    vm.start()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='A CHIP-8 Interpreter emulator')

    parser.add_argument('program', type=str,
                        help='path to ch8 program file to execute')
    parser.add_argument('-dp', '--debug-pygame', action='store_true',
                        help='display debug output from pygame event_loop\
                         and renderer')
    parser.add_argument('-dc', '--debug-chip8', action='store_true',
                        help='display debug output from CHIP-8 emulator')
    parser.add_argument('-fr', '--frequency', type=float,
                        help='CHIP-8 VM clock frequency (defaults to 1.76Mhz)')

    main(parser.parse_args())