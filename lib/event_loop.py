# -*- coding: utf-8 -*-
import pygame
from pygame.locals import *

pygame.init()


class EventLoop(object):
    def __init__(self, frequency=None):
        self.clock = pygame.time.Clock()
        self.keyboard = None
        self.frequency = frequency or 1000*1000

    def set_keyboard(self, keyboard):
        self.keyboard = keyboard

    def set_debug(self, debug):
        pass

    def tick(self):
        assert(self.keyboard is not None)

        for event in pygame.event.get():
            if event.type in [KEYDOWN, KEYUP]:
                self.keyboard.update_key(event)

        return self.clock.tick(self.frequency)