PyChip8: A Chip-8 emulator written for Python 3
===============================================

This is a simple Chip-8 interpreter written in Python 3.
The graphics renderer, the event loop and user input are based on pygame.

### Requirements:
 - Python 3.2+
 - Pygame 1.9.2+ for Linux, 1.9.1+ for Windows


### Usage ###
    pychip8.py [-h] [options] program

    A CHIP-8 Interpreter emulator

    positional arguments:

      program               path to ch8 program file to execute

    optional arguments:

      -h, --help            show this help message and exit
      -dp, --debug-pygame   display debug output from pygame event_loop and
                            renderer
      -dc, --debug-chip8    display debug output from CHIP-8 emulator
      -fr FREQUENCY, --frequency FREQUENCY
                            CHIP-8 VM clock frequency (defaults to 1.76Mhz)