import pygame

SCALE = 10
WHITE = pygame.Color(255, 255, 255)
BLACK = pygame.Color(0, 0, 0)

BEEP_SOUND_FILE = 'resources/beep.wav'


class Renderer(object):

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.surface = pygame.display.set_mode(
            (self.width * SCALE, self.height * SCALE))
        self.surface.fill(WHITE)

        pygame.mixer.init(44100)
        self.sound = pygame.mixer.Sound(BEEP_SOUND_FILE)

    def refresh(self, display):
        for i, p in enumerate(display):
            scaled_x = (i % self.width) * SCALE
            scaled_y = (i // self.width) * SCALE
            color = p == 1 and WHITE or BLACK

            pygame.draw.rect(self.surface,
                             color,
                             (scaled_x, scaled_y, SCALE, SCALE))

        pygame.display.update()

    def beep(self):
        self.sound.play()
