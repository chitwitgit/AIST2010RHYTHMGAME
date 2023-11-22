import pygame
import numpy as np
import random
from pattern_manager import PatternManager
from pygame import mixer
from utils import notedetection
from utils.youtubeDL import download_youtube_audio
from utils.input_manager import InputManager
import os
import sys
from cmdargs import args


if args.youtube is not None:
    youtube_link = args.youtube
else:
    youtube_link = "https://www.youtube.com/watch?v=HFPBd_mQYhg"
    youtube_link = "https://www.youtube.com/watch?v=fnAy9nlRuZs"
    # youtube_link = "https://www.youtube.com/watch?v=vS_a8Edde8k"
    # youtube_link = "https://www.youtube.com/watch?v=xtfXl7TZTac"
    # youtube_link = "https://www.youtube.com/watch?v=dWYSPKowfAU"

if args.tempo is not None:
    given_tempo = args.tempo
else:
    given_tempo = 130
if args.difficulty is not None:
    difficulty = args.difficulty
else:
    difficulty = 8  # usually (0, 10]
if args.ar is not None:
    approach_rate = args.ar
else:
    approach_rate = 10  # must be >0, usually [1, 10]


class Game:
    def __init__(self):
        self.game_scene = None
        self.pause_scene = None
        self.current_scene = None
        self.menu_scene = None
        self.screen_width = 800
        self.screen_height = 450
        self.data = {
            'difficulty': difficulty,
            'score': 0,
            'approach_rate': approach_rate,
            'combo': 0,
            'highest_combo': 0,
            'perfect_count': 0,
            'miss_count': 0,
        }
        pygame.init()
        pygame.display.init()
        self.window = pygame.display.set_mode((self.screen_width, self.screen_height),
                                              pygame.HWSURFACE | pygame.DOUBLEBUF)

        self.game_scene = GameScene(self.window, self.data)
        self.pause_scene = PauseScene(self.window, None)
        self.current_scene = self.game_scene
        self.menu_scene = MenuScene(self.window, self.data)


    def run(self, seed=None):
        running = True
        while running:
            #state = self.current_scene.run(seed)
            self.menu()
            state = self.current_scene.run(seed)
            if state == "Pause":
                self.pause_game()
            if state == "Resume":
                self.resume_game()
            if state == "Menu":
                self.menu()
            if state == "Stop Game":
                self.close()
                running = False
            if state == "End":  # add end screen if needed
                self.close()
                running = False

    def pause_game(self):
        self.current_scene = self.pause_scene
        self.pause_scene.paused_screen = self.game_scene.window_buffer

    def resume_game(self):
        self.current_scene = self.game_scene

    def menu(self):
        self.current_scene = self.menu_scene

    def close(self):
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()


class GameScene:
    def __init__(self, window, data):
        self.screen_width = 800
        self.screen_height = 450

        self.window = window
        self.clock = None
        self.steps = 0
        self.real_time_steps = 0
        self.fps = 60
        self.seed = 777
        self.color = (255, 255, 255)
        self.font = pygame.font.Font(None, 32)
        self.data = data
        self.combo_text = "Combo: {}".format(self.data['combo'])
        self.combo_label = self.font.render(self.combo_text, True, (255, 255, 255))
        self.combo_label_rect = self.combo_label.get_rect()
        self.combo_label_rect.bottomleft = (10, self.screen_height - 10)
        self.score_text = "Score: {}".format(self.data['score'])
        self.score_label = self.font.render(self.score_text, True, (255, 255, 255))
        self.score_label_rect = self.score_label.get_rect()
        self.score_label_rect.topright = (self.screen_width - 10, 10)

        self.tap_sound_effect = mixer.Sound('data/audio/sound_effects/normal-hitnormal.ogg')
        self.tap_sound_effect.set_volume(0.3)   # set volume

        self.audio_file_full_path = None
        self.pattern_manager = None
        self.mode = "debug x"
        self.debug_colors = None
        self.click_sound_effect = None
        self.music_data = None
        self.background = None
        self.game_started = False
        self.paused = False

        self.input_manager = InputManager()
        self.cursor_img = None
        self.cursor_img_rect = None
        self.cursor_pressed_img = None
        self.cursor_pressed_img_rect = None

        self.pattern_manager = PatternManager(self.screen_width, self.screen_height, self.fps, self.seed,
                                              difficulty=self.data["difficulty"],
                                              approach_rate=self.data["approach_rate"])
        self.window_buffer = None

        self.initialize()

    def initialize(self):
        random.seed(self.seed)
        self.load_assets(keep_files=True, use_new_files=True)   # if you want to try a new song
        # self.load_assets(keep_files=True, use_new_files=False)  # if same song which has been downloaded

        if self.clock is None:
            self.clock = pygame.time.Clock()
        pygame.mouse.set_visible(False)  # hides the cursor and will draw a cursor for playing rhythm game
        win = pygame.Surface((self.screen_width, self.screen_height))
        win.fill((0, 0, 0))
        self.pattern_manager.generate_map(self.music_data)
        self.pattern_manager.prerender_patterns(win)
        if self.mode == "debug":
            self.debug_mode_setup()

    def load_assets(self, keep_files=True, use_new_files=False):
        file_path = os.path.join("data", "audio")
        file_name = "audio.mp3"
        self.audio_file_full_path = os.path.join(file_path, file_name)
        onset_times_file = os.path.join("data", "onset_times.npy")
        onset_durations_file = os.path.join("data", "onset_durations.npy")
        onset_bars_file = os.path.join("data", "onset_bars.npy")
        tempo_file = os.path.join("data", "tempo.npy")

        if use_new_files:
            if os.path.exists(self.audio_file_full_path):
                os.remove(self.audio_file_full_path)

            if os.path.exists(onset_times_file):
                os.remove(onset_times_file)

            if os.path.exists(onset_durations_file):
                os.remove(onset_durations_file)

            if os.path.exists(onset_bars_file):
                os.remove(onset_bars_file)

            if os.path.exists(tempo_file):
                os.remove(tempo_file)

        is_from_youtube = not os.path.exists(self.audio_file_full_path)
        if is_from_youtube:
            youtube_url = youtube_link
            download_youtube_audio(youtube_url, file_path, file_name)
        else:
            print("File already exists. Skipping download.")
        self.cursor_img = pygame.image.load('data/images/cursor.png').convert_alpha()
        self.cursor_img_rect = self.cursor_img.get_rect()
        self.cursor_pressed_img = pygame.image.load('data/images/cursor_pressed.png').convert_alpha()
        self.cursor_pressed_img_rect = self.cursor_pressed_img.get_rect()
        if self.background is None:
            background = pygame.image.load("data/images/furina.jpg").convert()
            self.background = pygame.transform.smoothscale(background, (self.screen_width, self.screen_height))

        if os.path.exists(onset_times_file) and os.path.exists(onset_durations_file) and os.path.exists(
                onset_bars_file) and os.path.exists(tempo_file):
            onset_times = np.load(onset_times_file)
            onset_durations = np.load(onset_durations_file)
            onset_bars = np.load(onset_bars_file)
            tempo = np.load(tempo_file)
            self.music_data = onset_times, onset_durations, int(tempo)
        else:
            self.music_data = notedetection.process_audio(self.audio_file_full_path, tempo=given_tempo)
            onset_times, onset_durations, onset_bars, tempo = self.music_data
            tempo = np.array([tempo])
        mixer.music.load(self.audio_file_full_path)
        mixer.music.set_volume(0.8)

        if keep_files:
            np.save(onset_times_file, onset_times)
            np.save(onset_durations_file, onset_durations)
            np.save(onset_bars_file, onset_bars)
            np.save(tempo_file, tempo)
        else:
            os.remove(self.audio_file_full_path)

            if os.path.exists(onset_times_file):
                os.remove(onset_times_file)

            if os.path.exists(onset_durations_file):
                os.remove(onset_durations_file)

            if os.path.exists(onset_bars_file):
                os.remove(onset_bars_file)

    def debug_mode_setup(self):
        onset_times, onset_durations, *_ = self.music_data
        self.onset_time_frames = [int(i * self.fps) for i in onset_times]
        self.onset_duration_frames = [int(i * self.fps) for i in onset_durations]
        self.debug_maximum_t = max([onset_time + onset_duration for onset_time, onset_duration
                                    in zip(self.onset_time_frames, self.onset_duration_frames)]) + 1
        self.debug_colors = [
            (0, 0, 0)
            for _ in range(self.debug_maximum_t)
        ]
        for onset_time, onset_duration in zip(self.onset_time_frames, self.onset_duration_frames):
            if onset_duration > self.fps * 0.5:  # ignore onsets > 0.5s
                self.debug_colors[onset_time] = (240, 240, 240)
                continue
            for t in range(onset_duration):
                color = min((onset_duration - t) * 480, 240)
                self.debug_colors[onset_time + t] = (color, color, color)
        self.click_sound_effect = mixer.Sound('data/audio/sound_effects/click.wav')

    def run(self, seed=None):
        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
        while True:
            pygame.event.pump()  # Process pending events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "Stop Game"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.paused = True
            if not self.paused:
                self.step()
                if not self.game_started and self.clock.get_fps() > 1:
                    mixer.music.play()  # Start music playback
                    self.game_started = True
                if self.game_started and (not mixer.music.get_busy()):
                    return "End"  # Stop the game loop when music finishes playing
                self.render()
            else:
                pygame.mixer.music.pause()
                return "Pause"

    def restart(self, seed=None, options=None):
        random.seed(seed)
        return

    def step(self, action=None):
        if self.game_started:
            self.input_manager.update()
            self.steps += 1
            score = self.data["score"]
            temp_score = self.pattern_manager.update_patterns(self.steps, self.input_manager)
            score += temp_score
            if temp_score >= 10:
                combo = self.data['combo']
                combo += 1
                self.data['combo'] = combo
                perfect_count = self.data['perfect_count']
                perfect_count += 1
                self.data['perfect_count'] = perfect_count
                #print(f"Perfect Count: {perfect_count}")
                self.tap_sound_effect.play()
            self.data["score"] = score

    def render(self):
        fps = self.clock.get_fps()
        # print("Actual FPS:", fps)
        if fps and self.game_started:
            self.real_time_steps += self.fps / fps

        self.sync_game_and_music()
        win = pygame.Surface((self.screen_width, self.screen_height))
        self.window_buffer = pygame.Surface((self.screen_width, self.screen_height))
        # win.blit(self.background, (0, 0))
        win.fill((0, 0, 0))  # Fill the surface with black color
        self.window_buffer.fill((0, 0, 0))
        if self.mode == "debug":
            rect = pygame.Rect(0, 0, 100, 100)  # Create a rectangle for the top left corner
            if self.steps < self.debug_maximum_t:
                pygame.draw.rect(win, self.debug_colors[self.steps], rect)  # Fill the rectangle according to the onsets
            if self.steps in self.onset_time_frames:
                self.click_sound_effect.play()
        # rendering objects
        isMissed = not self.pattern_manager.render_patterns(win, self.steps)
        if isMissed:
            if self.data["combo"] > self.data["highest_combo"]:
                self.data["highest_combo"] = self.data["combo"]
            self.data["combo"] = 0
            miss_count = self.data["miss_count"]
            miss_count += 1
            self.data["miss_count"] = miss_count
        self.window_buffer.blit(win, (0, 0))
        if self.input_manager.is_user_holding:
            self.cursor_pressed_img_rect.center = pygame.mouse.get_pos()  # update position
            win.blit(self.cursor_pressed_img, self.cursor_pressed_img_rect)  # draw the cursor
        else:
            self.cursor_img_rect.center = pygame.mouse.get_pos()  # update position
            win.blit(self.cursor_img, self.cursor_img_rect)  # draw the cursor

        # print cumulative score and combo
        self.score_text = "Score: {}".format(self.data['score'])
        self.score_label = self.font.render(self.score_text, True, (255, 255, 255))
        self.score_label_rect = self.score_label.get_rect()
        self.score_label_rect.topright = (self.screen_width - 10, 10)
        win.blit(self.score_label, self.score_label_rect)
        self.combo_text = "Combo: {}".format(self.data['combo'])
        self.combo_label = self.font.render(self.combo_text, True, (255, 255, 255))
        self.combo_label_rect = self.combo_label.get_rect()
        self.combo_label_rect.bottomleft = (10, self.screen_height - 10)
        win.blit(self.combo_label, self.combo_label_rect)

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


class PauseScene:
    def __init__(self, window, paused_screen):
        self.resume_selected = False
        self.window = window
        self.screen_width, self.screen_height = window.get_size()
        self.paused_screen = paused_screen
        self.input_manager = InputManager()
        self.clock = pygame.time.Clock()

        self.cursor_img = pygame.image.load('data/images/cursor.png').convert_alpha()
        self.cursor_img_rect = self.cursor_img.get_rect()
        self.cursor_pressed_img = pygame.image.load('data/images/cursor_pressed.png').convert_alpha()
        self.cursor_pressed_img_rect = self.cursor_pressed_img.get_rect()

    def run(self, seed=None):
        self.resume_selected = False
        while not self.resume_selected:
            self.input_manager.update()
            self.render()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "End"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.resume_selected = True
            if self.resume_selected:
                self.countdown()
                return "Resume"

    def render(self):
        win = pygame.Surface((self.screen_width, self.screen_height))
        win.blit(self.paused_screen, (0, 0))
        self._apply_whiteness(win)
        if self.input_manager.is_mouse_holding:
            self.cursor_pressed_img_rect.center = pygame.mouse.get_pos()  # update position
            win.blit(self.cursor_pressed_img, self.cursor_pressed_img_rect)  # draw the cursor
        else:
            self.cursor_img_rect.center = pygame.mouse.get_pos()  # update position
            win.blit(self.cursor_img, self.cursor_img_rect)  # draw the cursor
        self.window.blit(win, win.get_rect())
        pygame.event.pump()
        pygame.display.update()

    def countdown(self):
        font = pygame.font.Font(None, 100)  # Font for the countdown numbers
        countdown_time = 3
        fps = 60
        for i in range(countdown_time * fps):
            win = pygame.Surface((self.screen_width, self.screen_height))
            win.blit(self.paused_screen, (0, 0))
            countdown_text = font.render(str(countdown_time - i // fps), True, (255, 255, 255))
            countdown_text_rect = countdown_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            win.blit(countdown_text, countdown_text_rect)
            if self.input_manager.is_mouse_holding:
                self.cursor_pressed_img_rect.center = pygame.mouse.get_pos()  # update position
                win.blit(self.cursor_pressed_img, self.cursor_pressed_img_rect)  # draw the cursor
            else:
                self.cursor_img_rect.center = pygame.mouse.get_pos()  # update position
                win.blit(self.cursor_img, self.cursor_img_rect)  # draw the cursor
            self.window.blit(win, win.get_rect())
            pygame.event.pump()
            pygame.display.update()
            self.clock.tick(fps)

    @staticmethod
    def _apply_whiteness(win):
        whiteness = 100

        tmp = pygame.Surface(win.get_size())
        tmp.fill((whiteness, whiteness, whiteness))

        # Blit the temporary surface onto the original surface
        win.blit(tmp, (0, 0), special_flags=pygame.BLEND_RGB_ADD)


class MenuScene:
    def __init__(self, window, data):
        self.start_click = False
        self.window = window
        self.screen_width, self.screen_height = window.get_size()
        self.input_manager = InputManager()
        self.clock = pygame.time.Clock()

        self.data = data

        # Define label properties
        self.difficulty_label_text = "Difficulty:"
        self.approach_rate_label_text = "Approach Rate:"
        self.start_label_text = "START"
        self.menu_label_text = "MENU"
        self.label_font = pygame.font.Font(None, 36)
        self.label_color = (255, 255, 255)  # White color

        # Define button properties
        self.button_width, self.button_height = 30, 30
        self.button_margin = 5
        self.button_color = (0, 0, 0)
        self.button_font = pygame.font.Font(None, 30)
        self.button_text_color = (255, 255, 255)  # White color

        # Calculate total width for buttons and margins
        self.total_width = (self.button_width + self.button_margin) * 10 - self.button_margin
        self.start_x = 300
        self.difficulty_button_pos_y = (self.screen_height - self.button_height) // 3 + 25
        self.approach_rate_button_pos_y = (self.screen_height - self.button_height) // 3 * 2 - 25

        # Calculate label position
        self.difficulty_label_pos_x = self.start_x - self.label_font.size(self.difficulty_label_text)[0] - 10
        self.approach_rate_label_pos_x = self.start_x - self.label_font.size(self.approach_rate_label_text)[0] - 10
        self.difficulty_label_pos_y = (self.screen_height - self.label_font.size(self.difficulty_label_text)[1]) // 3 + 25
        self.approach_rate_label_pos_y = (self.screen_height - self.label_font.size(self.approach_rate_label_text)[1]) // 3 * 2 - 25

        self.cursor_img = pygame.image.load('data/images/cursor.png').convert_alpha()
        self.cursor_img_rect = self.cursor_img.get_rect()
        self.cursor_pressed_img = pygame.image.load('data/images/cursor_pressed.png').convert_alpha()
        self.cursor_pressed_img_rect = self.cursor_pressed_img.get_rect()

    def run(self, seed=None):
        while not self.start_click:
            self.input_manager.update()
            self.render()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "End"
            if self.start_click:
                return "Resume"

    def render(self):
        win = pygame.Surface((self.screen_width, self.screen_height))
        win.fill((0, 0, 0))

        # Menu button
        label_surface = self.label_font.render(self.menu_label_text, True, self.label_color)
        label_rect = label_surface.get_rect(center=(self.screen_width // 2, 100))
        win.blit(label_surface, label_rect)

        # Draw difficulty label
        label_surface = self.label_font.render(self.difficulty_label_text, True, self.label_color)
        label_rect = label_surface.get_rect(topleft=(self.difficulty_label_pos_x, self.difficulty_label_pos_y))
        win.blit(label_surface, label_rect)

        # Draw difficulty buttons
        for i in range(10):
            button_pos_x = self.start_x + (self.button_width + self.button_margin) * i
            button_rect = pygame.Rect(button_pos_x, self.difficulty_button_pos_y, self.button_width, self.button_height)
            pygame.draw.rect(win, self.button_color, button_rect)

            if button_rect.collidepoint(pygame.mouse.get_pos()):
                if self.input_manager.is_mouse_clicked:  # Left mouse button pressed
                    self.data['difficulty'] = i + 1

            button_text = str(i + 1)  # Button label from 1 to 10
            button_text_surface = self.button_font.render(button_text, True, self.button_text_color)
            button_text_rect = button_text_surface.get_rect(center=button_rect.center)
            win.blit(button_text_surface, button_text_rect)

        # Draw approach rate label
        label_surface = self.label_font.render(self.approach_rate_label_text, True, self.label_color)
        label_rect = label_surface.get_rect(topleft=(self.approach_rate_label_pos_x, self.approach_rate_label_pos_y))
        win.blit(label_surface, label_rect)

        # Draw approach rate buttons
        for i in range(10):
            button_pos_x = self.start_x + (self.button_width + self.button_margin) * i
            button_rect = pygame.Rect(button_pos_x, self.approach_rate_button_pos_y, self.button_width,
                                      self.button_height)
            pygame.draw.rect(win, self.button_color, button_rect)

            if button_rect.collidepoint(pygame.mouse.get_pos()):
                if self.input_manager.is_mouse_clicked:  # Left mouse button pressed
                    self.data['approach_rate'] = i + 1

            button_text = str(i + 1)  # Button label from 1 to 10
            button_text_surface = self.button_font.render(button_text, True, self.button_text_color)
            button_text_rect = button_text_surface.get_rect(center=button_rect.center)
            win.blit(button_text_surface, button_text_rect)

        # Start button
        button_surface = self.label_font.render(self.start_label_text, True, self.label_color)
        button_rect = button_surface.get_rect(bottomright=(self.screen_width - 25, self.screen_height - 25))
        win.blit(button_surface, button_rect)

        if button_rect.collidepoint(pygame.mouse.get_pos()):
            if self.input_manager.is_mouse_clicked:  # Left mouse button pressed
                self.start_click = True

        if self.input_manager.is_mouse_holding:
            self.cursor_pressed_img_rect.center = pygame.mouse.get_pos()  # update position
            win.blit(self.cursor_pressed_img, self.cursor_pressed_img_rect)  # draw the cursor
        else:
            self.cursor_img_rect.center = pygame.mouse.get_pos()  # update position
            win.blit(self.cursor_img, self.cursor_img_rect)  # draw the cursor

        self.window.blit(win, win.get_rect())
        pygame.event.pump()
        pygame.display.update()

def main():
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
