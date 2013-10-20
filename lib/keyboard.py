from pygame.locals import *
import sys

KEYBOARD_MAPPING = {
    K_KP0: 0x0,
    K_KP1: 0x1,
    K_KP2: 0x2,
    K_KP3: 0x3,
    K_KP4: 0x4,
    K_KP5: 0x5,
    K_KP6: 0x6,
    K_KP7: 0x7,
    K_KP8: 0x8,
    K_KP9: 0x9,
    K_a: 0xA,
    K_z: 0xB,
    K_e: 0xC,
    K_q: 0xD,
    K_s: 0xE,
    K_d: 0xF
}


class Keyboard(object):

    def __init__(self, event_loop):
        self.key_state = None
        self.event_loop = event_loop

    def get_key_state(self):
        return self.key_state

    def update_key(self, event):
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                sys.exit()

            if event.key in KEYBOARD_MAPPING.keys():
                self.key_state = KEYBOARD_MAPPING[event.key]

        elif event.type == KEYUP:
            self.key_state = None

