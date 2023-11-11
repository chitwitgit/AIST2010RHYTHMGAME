import numpy as np
import pygame
import random
from patterns import TapPattern, Line, CubicBezier, Arc
from pattern_manager import PatternManager


class GameScene:
    def __init__(self):
        self.screen_width = 800
        self.screen_height = 600

        self.window = None
        self.clock = None
        self.steps = 0
        self.fps = 60
        self.seed = 77777777
        self.points = 0
        self.currentScene = 0

        self.pattern_manager = PatternManager(self.screen_width, self.screen_height, self.seed)

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

    def render(self):
        fps = self.clock.get_fps()
        print("Actual FPS:", fps)
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
        # self.pattern_manager.prerender_patterns(win)
        self.pattern_manager.render_patterns(win, self.steps)
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
