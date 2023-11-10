import numpy as np
import pygame
import random
from pygame import mixer
from abc import ABC, abstractmethod
from patterns import Point, Line, CubicBezier, Arc

class GameScene:
    def __init__(self):
        self.screen_width = 500
        self.screen_height = 800

        self.window = None
        self.clock = None
        self.steps = 0
        self.fps = 60

        self.points = 0
        self.currentScene = 0

        self.ball = Point(250, 400, 50, 5, (255, 0, 0))
        P0 = np.array([100, 300])
        P1 = np.array([200, 200])
        P2 = np.array([300, 220])
        P3 = np.array([350, 300])
        self.curve1 = CubicBezier(250, 300, 20, 5, P0, P1, P2, P3, (255, 100, 255))
        self.curve2 = Arc(250, 300, 20, 5, 0, 1, 100, (0, 0, 255))
        self.line = Line(250, 300, 20, 5, P0, P1, (0, 255, 0))

    def _init(self, seed=None):
        random.seed(seed)
        if self.window is None:
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode((self.screen_width, self.screen_height))
            # mixer.music.load("")
            # mixer.music.set_volume(0.8)
            # mixer.music.play(-1)
        if self.clock is None:
            self.clock = pygame.time.Clock()

    def run(self, seed=None):
        self._init(seed)
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            self.step(0)
            self.render()
        self.close()

    def reset(self, seed=None, options=None):
        random.seed(seed)
        return

    def step(self, action):
        self.steps += 1
        # self.ball.update()
        # self.curve.update()

    def render(self):
        return self._render_frame(False)

    def _render_frame(self, terminated):
        if terminated:
            _ = 1  # do something
        win = pygame.Surface((self.screen_width, self.screen_height))
        # background = pygame.image.load("").convert_alpha()
        # background = pygame.transform.scale(background, (self.screen_width, self.screen_height))
        # win.blit(background, (0, 0))
        win.fill((0, 0, 0))  # Fill the surface with black color
        # rendering objects
        # self.ball.render(win)
        self.curve1.render(win)
        self.curve2.render(win)
        self.line.render(win)
        # render window buffer to screen
        self.window.blit(win, win.get_rect())
        pygame.event.pump()
        pygame.display.update()
        self.clock.tick(self.fps)

    def close(self):
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()


def main():
    game = GameScene()
    game.run()


if __name__ == '__main__':
    main()
