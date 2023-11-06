import numpy as np
import pygame
import random
from pygame import mixer
from abc import ABC, abstractmethod


class Sprite(ABC):
    @abstractmethod
    def _move(self):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def render(self):
        pass


class Game:
    def __init__(self):
        self.screen_width = 500
        self.screen_height = 800

        self.window = None
        self.clock = None
        self.steps = 0
        self.fps = 60

        self.points = 0
        self.currentScene = 0

    def reset(self, seed=None, options=None):
        random.seed(seed)
        return

    def step(self, action):
        self.steps += 1
        return

    def render(self):
        return self._render_frame(False)

    def _render_frame(self, terminated):
        if self.window is None:
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode((self.screen_width, self.screen_height))
            mixer.music.load("")
            mixer.music.set_volume(0.8)
            mixer.music.play(-1)
        if self.clock is None:
            self.clock = pygame.time.Clock()
        if terminated:
            _ = 1  # do something
        win = pygame.Surface((self.screen_width, self.screen_height))
        background = pygame.image.load("").convert_alpha()
        background = pygame.transform.scale(background, (self.screen_width, self.screen_height))
        win.blit(background, (0, 0))
        # rendering objects

        # render window buffer to screen
        self.window.blit(win, win.get_rect())
        pygame.event.pump()
        pygame.display.update()
        self.clock.tick(self.fps)

    def close(self):
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()
