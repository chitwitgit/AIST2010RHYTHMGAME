import pygame
import numpy as np
import random
from pattern_manager import PatternManager
from pygame import mixer
from utils import notedetection
from utils.youtubeDL import download_youtube_audio
from utils.input_manager import InputManager
import os


class GameScene:
    def __init__(self):
        self.screen_width = 800
        self.screen_height = 450

        self.window = None
        self.clock = None
        self.steps = 0
        self.real_time_steps = 0
        self.fps = 60
        self.seed = 777
        self.points = 0
        self.currentScene = 0
        self.mode = "debug"
        self.debug_colors = None
        self.click_sound_effect = None

        self.pattern_manager = PatternManager(self.screen_width, self.screen_height, self.fps, self.seed, difficulty=1)
        self.background = None
        self.game_started = False

    def _init(self, seed=None):
        random.seed(seed)
        output_path = os.path.join("data", "audio")
        # output_name = "furina.mp3"
        output_name = "akari2.mp3"

        filename = os.path.join(output_path, output_name)
        is_from_youtube = not os.path.exists(filename)
        if is_from_youtube:
            # youtube_url = "https://www.youtube.com/watch?v=yXMPAMKUVgY"
            # youtube_url = "https://www.youtube.com/watch?v=tbK7JxFDOOg"
            # youtube_url = "https://www.youtube.com/watch?v=i0K40f-6mLs"
            # youtube_url = "https://www.youtube.com/watch?v=GyP1EWjS2rM"
            youtube_url = "https://www.youtube.com/watch?v=kagoEGKHZvU"
            # youtube_url = "https://www.youtube.com/watch?v=HMGetv40FkI"
            # youtube_url = "https://www.youtube.com/watch?v=FYAIgqIpR08"
            download_youtube_audio(youtube_url, output_path, output_name)
        else:
            print("File already exists. Skipping download.")
        self.music_data = notedetection.process_audio(filename)
        if self.window is None:
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode((self.screen_width, self.screen_height),
                                                  pygame.HWSURFACE | pygame.DOUBLEBUF)
            mixer.music.load(filename)
            mixer.music.set_volume(0.8)
        if is_from_youtube:
            os.remove(filename)
        if self.clock is None:
            self.clock = pygame.time.Clock()
        self.input_manager = InputManager()
        pygame.mouse.set_visible(False)  # hides the cursor and will draw a cursor for playing rhythm game
        win = pygame.Surface((self.screen_width, self.screen_height))
        win.fill((0, 0, 0))
        self.cursor_img = pygame.image.load('data/images/cursor.png').convert_alpha()
        self.cursor_img_rect = self.cursor_img.get_rect()
        self.cursor_pressed_img = pygame.image.load('data/images/cursor_pressed.png').convert_alpha()
        self.cursor_pressed_img_rect = self.cursor_pressed_img.get_rect()
        self.pattern_manager.generate_map(self.music_data)
        self.pattern_manager.prerender_patterns(win)
        if self.background is None:
            background = pygame.image.load("data/images/furina.jpg").convert()
            self.background = pygame.transform.smoothscale(background, (self.screen_width, self.screen_height))
        if self.mode == "debug":
            self.debug_mode_setup()

    def debug_mode_setup(self):
        onset_times, onset_durations = self.music_data
        self.onset_time_frames = [int(i * self.fps) for i in onset_times]
        self.onset_duration_frames = [int(i * self.fps) for i in onset_durations]
        self.debug_colors = [
            (0, 0, 0)
            for _ in range(max([onset_time + onset_duration for onset_time, onset_duration
                                in zip(self.onset_time_frames, self.onset_duration_frames)]))
        ]
        for onset_time, onset_duration in zip(self.onset_time_frames, self.onset_duration_frames):
            if onset_duration > self.fps * 4:  # ignore meaningless ones (>4 seconds)
                continue
            for t in range(onset_duration):
                color = min((onset_duration - t) / 2, 240)
                self.debug_colors[onset_time+t] = (color, color, color)
        self.click_sound_effect = mixer.Sound('data/audio/sound_effects/click.wav')


    def run(self, seed=None):
        self._init(seed)
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            self.step()
            if not self.game_started and self.clock.get_fps() > 1:
                mixer.music.play()  # Start music playback
                self.game_started = True
            if self.game_started and (not mixer.music.get_busy()):
                running = False  # Stop the game loop when music finishes playing
            self.render()
        self.close()

    def restart(self, seed=None, options=None):
        random.seed(seed)
        return

    def step(self, action=None):
        if self.game_started:
            self.input_manager.update()
            self.steps += 1
            self.pattern_manager.update_patterns(self.steps, self.input_manager)

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
        # win.blit(self.background, (0, 0))
        win.fill((0, 0, 0))  # Fill the surface with black color
        if self.mode == "debug":
            rect = pygame.Rect(0, 0, 100, 100)  # Create a rectangle for the top left corner
            pygame.draw.rect(win, self.debug_colors[self.steps], rect)  # Fill the rectangle according to the onsets
            if self.steps in self.onset_time_frames:
                self.click_sound_effect.play()
        # rendering objects
        self.pattern_manager.render_patterns(win, self.steps)
        if self.input_manager.is_user_holding:
            self.cursor_pressed_img_rect.center = pygame.mouse.get_pos()  # update position
            win.blit(self.cursor_pressed_img, self.cursor_pressed_img_rect)  # draw the cursor
        else:
            self.cursor_img_rect.center = pygame.mouse.get_pos()  # update position
            win.blit(self.cursor_img, self.cursor_img_rect)  # draw the cursor
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
