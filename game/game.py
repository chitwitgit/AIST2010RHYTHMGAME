import pygame
import random
from pattern_manager import PatternManager
from pygame import mixer
from utils import notedetection
from utils.youtubeDL import download_youtube_audio
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

        self.pattern_manager = PatternManager(self.screen_width, self.screen_height, self.fps, self.seed, difficulty=1)
        self.background = None
        self.game_started = False
        self.previous_mouse_clicked = False

    def _init(self, seed=None):
        random.seed(seed)
        output_path = os.path.join("data", "audio")
        output_name = "akari3.mp3"
        # output_name = "akari2.mp3"

        filename = os.path.join(output_path, output_name)
        is_from_youtube = not os.path.exists(filename)
        if is_from_youtube:
            # youtube_url = "https://www.youtube.com/watch?v=yXMPAMKUVgY"
            # youtube_url = "https://www.youtube.com/watch?v=tbK7JxFDOOg"
            youtube_url = "https://www.youtube.com/watch?v=2c_lHmkOq0E"
            # youtube_url = "https://www.youtube.com/watch?v=HMGetv40FkI"
            # youtube_url = "https://www.youtube.com/watch?v=FYAIgqIpR08"
            download_youtube_audio(youtube_url, output_path, output_name)
        else:
            print("File already exists. Skipping download.")
        music_data = notedetection.process_audio(filename)
        if self.window is None:
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode((self.screen_width, self.screen_height))
            mixer.music.load(filename)
            mixer.music.set_volume(0.8)
        if is_from_youtube:
            os.remove(filename)
        if self.clock is None:
            self.clock = pygame.time.Clock()
        pygame.mouse.set_visible(False)  # hides the cursor and will draw a better cursor
        win = pygame.Surface((self.screen_width, self.screen_height))
        win.fill((0, 0, 0))
        self.cursor_img = pygame.image.load('data/images/cursor.png').convert_alpha()
        self.cursor_img_rect = self.cursor_img.get_rect()
        self.cursor_pressed_img = pygame.image.load('data/images/cursor_pressed.png').convert_alpha()
        self.cursor_pressed_img_rect = self.cursor_pressed_img.get_rect()
        self.pattern_manager.generate_map(music_data)
        self.pattern_manager.prerender_patterns(win)
        if self.background is None:
            background = pygame.image.load("data/images/furina.jpg").convert()
            self.background = pygame.transform.smoothscale(background, (self.screen_width, self.screen_height))

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

    def reset(self, seed=None, options=None):
        random.seed(seed)
        return

    def step(self, action=None):
        if self.game_started:
            self.steps += 1
            self.pattern_manager.update_patterns(self.steps, self.previous_mouse_clicked)
            self.previous_mouse_clicked = pygame.mouse.get_pressed()[0]


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
        # rendering objects
        self.pattern_manager.render_patterns(win, self.steps)
        if pygame.mouse.get_pressed()[0]:
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
