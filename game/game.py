import pygame
import random
from pattern_manager import PatternManager
from pygame import mixer
from utils import notedetection
from utils.youtubeDL import download_youtube_audio
import os


class GameScene:
    def __init__(self):
        self.screen_width = 450
        self.screen_height = 800

        self.window = None
        self.clock = None
        self.steps = 0
        self.real_time_steps = 0
        self.fps = 60
        self.seed = 77777777
        self.points = 0
        self.currentScene = 0

        self.pattern_manager = PatternManager(self.screen_width, self.screen_height, self.fps, self.seed, difficulty=1)
        self.background = None
        self.game_started = False

    def _init(self, seed=None):
        random.seed(seed)
        output_path = "data/audio"
        output_name = "furina.mp3"

        filename = os.path.join(output_path, output_name)
        is_from_youtube = not os.path.exists(filename)
        if is_from_youtube:
            youtube_url = "https://www.youtube.com/watch?v=yXMPAMKUVgY"
            download_youtube_audio(youtube_url, output_path, output_name)
        else:
            print("File already exists. Skipping download.")

        if self.window is None:
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode((self.screen_width, self.screen_height))
            mixer.music.load(filename)
            mixer.music.set_volume(0.8)
        if self.clock is None:
            self.clock = pygame.time.Clock()
        win = pygame.Surface((self.screen_width, self.screen_height))
        win.fill((0, 0, 0))
        music_data = notedetection.process_audio(filename)
        if is_from_youtube:
            os.remove(filename)
        self.pattern_manager.generate_map(music_data)
        self.pattern_manager.prerender_patterns(win)
        if self.background is None:
            background = pygame.image.load("data/images/furina.jpg").convert_alpha()
            self.background = pygame.transform.smoothscale(background, (self.screen_width, self.screen_height))

    def run(self, seed=None):
        self._init(seed)
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            self.step()
            if not self.game_started and self.clock.get_fps() > 1:
                mixer.music.play()  # Start music playback
                self.game_started = True
            if self.game_started and (not mixer.music.get_busy()):
                running = False  # Stop the game loop when music finishes playing
            self.render()
        self.close()

    def reset(self, seed=None, options=None):
        random.seed(seed)
        return

    def step(self, action=None):
        if self.game_started:
            self.steps += 1

    def render(self):
        fps = self.clock.get_fps()
        print("Actual FPS:", fps)
        if fps and self.game_started:
            self.real_time_steps += self.fps / fps
        return self._render_frame(False)

    def _render_frame(self, terminated):
        if terminated:
            _ = 1  # do something

        self.sync_game_and_music()

        win = pygame.Surface((self.screen_width, self.screen_height))
        win.blit(self.background, (0, 0))
        # win.fill((0, 0, 0))  # Fill the surface with black color
        # rendering objects
        self.pattern_manager.render_patterns(win, self.steps)
        # render window buffer to screen
        self.window.blit(win, win.get_rect())
        pygame.event.pump()
        pygame.display.update()
        self.clock.tick(self.fps)

    def sync_game_and_music(self):
        # sync up game steps and music
        if self.game_started and abs(self.real_time_steps - self.steps) > 1.1:
            if 0 <= (self.real_time_steps - self.steps) <= 3:
                self.steps += 1  # try to speed up the game step to keep up
            elif 0 <= (self.steps - self.real_time_steps) <= 3:
                self.steps -= 1  # slow down the game steps to follow the music
            else:
                elapsed_time = self.steps / self.fps
                mixer.music.set_pos(elapsed_time)
                self.real_time_steps = self.steps

    def close(self):
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()


def main():
    game = GameScene()
    game.run()


if __name__ == '__main__':
    main()
