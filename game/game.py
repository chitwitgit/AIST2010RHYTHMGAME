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
    def render(self, win):
        pass


class Ball(Sprite):
    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color

    def _move(self):
        # Move the ball randomly up or down
        direction = random.choice([-1, 1])
        self.y += direction * 5

    def update(self):
        self._move()

    def render(self, win):
        pygame.draw.circle(win, self.color, (self.x, self.y), self.radius)


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

        self.ball = Ball(250, 400, 50, (255, 0, 0))

    def reset(self, seed=None, options=None):
        random.seed(seed)
        return

    def step(self, action):
        self.steps += 1
        self.ball.update()

    def render(self):
        return self._render_frame(False)

    def _render_frame(self, terminated):
        if self.window is None:
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode((self.screen_width, self.screen_height))
            # mixer.music.load("")
            # mixer.music.set_volume(0.8)
            # mixer.music.play(-1)
        if self.clock is None:
            self.clock = pygame.time.Clock()
        if terminated:
            _ = 1  # do something
        win = pygame.Surface((self.screen_width, self.screen_height))
        # background = pygame.image.load("").convert_alpha()
        # background = pygame.transform.scale(background, (self.screen_width, self.screen_height))
        # win.blit(background, (0, 0))
        win.fill((0, 0, 0))  # Fill the surface with black color
        # rendering objects
        self.ball.render(win)
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
    game = Game()
    game.render()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        game.step(0)
        game.render()

    game.close()


if __name__ == '__main__':
    main()
