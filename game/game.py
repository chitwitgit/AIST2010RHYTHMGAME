import pygame
import numpy as np
import random
from pattern_manager import PatternManager
from pygame import mixer
from utils import notedetection
from utils.youtubeDL import download_youtube_audio
from utils.input_manager import InputManager
from utils.button import Button, Label
import os
from utils.settings import settings
from dataclasses import dataclass
import threading

youtube_link, seed, given_tempo, difficulty, approach_rate, mode, is_use_new_files, use_game_background = settings


# A dataclass storing some variables about the game
@dataclass
class GameData:
    difficulty: int  # Range: 1-10
    score: int
    approach_rate: int  # Range: 1-10
    combo: int  # Current combo count
    highest_combo: int  # Highest combo count
    perfect_count: int  # Number of perfect hits by the player
    miss_count: int  # Number of misses by the player


class Game:
    """
    The Game class manages the control flow of different scenes
    """
    def __init__(self):
        self.screen_width, self.screen_height = 1200, 675
        self.data = GameData(
            difficulty=difficulty,
            score=0,
            approach_rate=approach_rate,
            combo=0,
            highest_combo=0,
            perfect_count=0,
            miss_count=0
        )

        # Initialize Pygame
        pygame.init()
        pygame.display.init()
        self.window = pygame.display.set_mode((self.screen_width, self.screen_height),
                                              pygame.HWSURFACE | pygame.DOUBLEBUF)

        # Load the image for the cursor
        cursor_img_scale_factor = 1.5
        cursor_img = pygame.image.load('data/images/cursor.png').convert_alpha()
        cursor_img = pygame.transform.smoothscale(cursor_img, (
            int(cursor_img.get_width() * cursor_img_scale_factor),
            int(cursor_img.get_height() * cursor_img_scale_factor)))
        cursor_img_rect = cursor_img.get_rect()

        cursor_pressed_img = pygame.image.load('data/images/cursor_pressed.png').convert_alpha()
        cursor_pressed_img = pygame.transform.smoothscale(cursor_pressed_img, (
            int(cursor_pressed_img.get_width() * cursor_img_scale_factor),
            int(cursor_pressed_img.get_height() * cursor_img_scale_factor)))
        cursor_pressed_img_rect = cursor_pressed_img.get_rect()

        self.cursor_images = (cursor_img, cursor_img_rect, cursor_pressed_img, cursor_pressed_img_rect)

        # Declare game scenes
        self.menu_scene = MenuScene(self.window, self.data, self.cursor_images)
        self.current_scene = self.menu_scene
        self.game_scene = None
        self.pause_scene = None
        self.loading_scene = None
        self.ready_scene = None
        self.end_scene = None

    def run(self):
        running = True
        while running:
            state = self.current_scene.run()
            if state == "Pause":
                self.pause_game()
            if state == "Play":
                self.play_game()
            if state == "Resume":
                self.resume_game()
            if state == "Menu":
                self.menu()
            if state == "Loading Finished":
                self.confirm_ready()
            if state == "Stop Game":
                self.close()
                running = False  # break the loop
                print("Game Closed")
            if state == "End":
                self.end()
            if state == "Load":
                self.load()

    def pause_game(self):
        self.current_scene = self.pause_scene
        # obtain the last screen displayed and save it to paused scene
        self.pause_scene.paused_screen = self.game_scene.window_buffer

    def play_game(self):
        self.current_scene = self.game_scene

    def resume_game(self):
        self.play_game()

    def menu(self):
        self.menu_scene.start_click = False
        self.current_scene = self.menu_scene

    def end(self):
        # update highest combo value
        self.data.highest_combo = max(self.data.combo, self.data.highest_combo)
        self.end_scene.end_click = False
        self.current_scene = self.end_scene

    def load(self):
        # Once the settings are finalized, initialize the other scenes accordingly
        self.game_scene = GameScene(self.window, self.data, self.cursor_images)
        self.pause_scene = PauseScene(self.window, self.cursor_images)

        # assign expensive task to loading scene to run in a separate thread
        task = self.game_scene.run_expensive_operations
        self.loading_scene = LoadingScene(self.window, task, self.cursor_images)

        self.ready_scene = ReadyScene(self.window, self.cursor_images)
        self.end_scene = EndScene(self.window, self.data, self.cursor_images)
        self.current_scene = self.loading_scene

    def confirm_ready(self):
        self.current_scene = self.ready_scene

    def close(self):
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()


class GameScene:
    """
    Contains all the logic in the main gameplay loop
    """
    def __init__(self, window, data, cursor_images):
        self.screen_width, self.screen_height = window.get_size()

        self.window = window
        self.clock = None
        self.steps = 0
        # Stores number of real steps passed based on real time, used to correct for lag and sync up audio with game
        self.real_time_steps = 0

        self.fps = 60
        self.seed = seed

        self.color = (255, 255, 255)
        self.font = pygame.font.Font(None, 64)
        self.data = data
        self.combo_text = "Combo: {}".format(self.data.combo)
        self.combo_label = self.font.render(self.combo_text, True, (255, 255, 255))
        self.combo_label_rect = self.combo_label.get_rect()
        self.combo_label_rect.bottomleft = (10, self.screen_height - 10)
        self.score_text = "Score: {}".format(self.data.score)
        self.score_label = self.font.render(self.score_text, True, (255, 255, 255))
        self.score_label_rect = self.score_label.get_rect()
        self.score_label_rect.topright = (self.screen_width - 10, 10)

        self.cursor_images = cursor_images
        self.tap_sound_effect = mixer.Sound('data/audio/sound_effects/normal-hitnormal.ogg')
        self.tap_sound_effect.set_volume(0.3)  # set volume

        self.audio_file_full_path = None
        self.pattern_manager = None
        self.mode = mode
        self.debug_colors = None
        self.click_sound_effect = None
        self.music_data = None
        self.background = None
        self.game_started = False
        self.paused = False

        self.input_manager = InputManager()

        self.pattern_manager = PatternManager(self.screen_width, self.screen_height, self.fps, self.seed,
                                              difficulty=self.data.difficulty,
                                              approach_rate=self.data.approach_rate,
                                              tempo=given_tempo)
        self.window_buffer = pygame.Surface((self.screen_width, self.screen_height))

        random.seed(self.seed)
        if self.clock is None:
            self.clock = pygame.time.Clock()
        pygame.mouse.set_visible(False)  # hides the cursor and will draw a cursor for playing rhythm game

    def run_expensive_operations(self):
        """
        Collect all expensive tasks to pass to the loading scene to run in a separate thread
        """
        # set to True to skip downloading and processing
        self.load_assets(keep_files=True, use_new_files=is_use_new_files)

        win = pygame.Surface((self.screen_width, self.screen_height))
        win.fill((0, 0, 0))
        self.pattern_manager.generate_map(self.music_data)
        self.pattern_manager.hot_load_caches()
        self.pattern_manager.prerender_patterns(win)
        if self.mode == "debug":
            self.debug_mode_setup()

    def load_assets(self, keep_files=True, use_new_files=False):
        """
        Loads files for the audio and computed musical information
        :param keep_files: Saves the files to the disk when finished
        :param use_new_files: Deletes the saved files and use new ones, set to True if selecting a new song,
        False if load from existing files
        """

        file_path = os.path.join("data", "audio")
        file_name = "audio.mp3"
        self.audio_file_full_path = os.path.join(file_path, file_name)
        onset_times_file = os.path.join("data", "onset_times.npy")
        onset_durations_file = os.path.join("data", "onset_durations.npy")
        onset_bars_file = os.path.join("data", "onset_bars.npy")
        tempo_file = os.path.join("data", "tempo.npy")

        if use_new_files:
            # Remove all the existing files
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

        # Download audio from YouTube if there is no audio at the specified path
        is_from_youtube = not os.path.exists(self.audio_file_full_path)
        if is_from_youtube:
            youtube_url = youtube_link
            download_youtube_audio(youtube_url, file_path, file_name)
        else:
            print("File already exists. Skipping download.")

        # Set game background if desired
        if self.background is None and use_game_background:
            background = pygame.image.load("data/images/background.png").convert()
            """
            We compute the brightness value of the background image by calculating the root mean square (RMS) of all
            pixel color values. Our aim is to darken the image for minimal gameplay impact.
            
            1. We first convert the image to a numpy array, compute the mean pixel value across RGB channels for every
            pixel, then take the root mean square of those values
            
            If the computed brightness is greater than the target brightness, we darken the background image:

            2. Calculate the darken factor by dividing the target brightness by the computed brightness.
            3. Create a dark surface with the same size as the background image and fill it with a darkened pixel value.
            4. Blend the dark surface with the original background image.
            """
            background_array = pygame.surfarray.array3d(background)  # convert to numpy array
            pixel_mean_rgb_values = np.mean(background_array, axis=2)  # compute mean pixel brightness over rgb channels
            brightness = np.sqrt(np.mean(pixel_mean_rgb_values ** 2))  # compute rms pixel brightness
            brightness_target = 40
            # darken the background image
            if brightness > brightness_target:
                darken_factor = brightness_target / brightness
                pixel_value = int(255 * darken_factor)
                # Create a surface with the same size as the background image
                dark_surface = pygame.Surface(background.get_size()).convert_alpha()
                dark_surface.fill((pixel_value, pixel_value, pixel_value))
                background.blit(dark_surface, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            # Scale the background image to game screen size
            self.background = pygame.transform.smoothscale(background, (self.screen_width, self.screen_height))

        # Check for the existence of extracted and process musical data
        if os.path.exists(onset_times_file) and os.path.exists(onset_durations_file) and os.path.exists(
                onset_bars_file) and os.path.exists(tempo_file):
            onset_times = np.load(onset_times_file)
            onset_durations = np.load(onset_durations_file)
            onset_bars = np.load(onset_bars_file)
            tempo = np.load(tempo_file)
            self.music_data = onset_times, onset_durations, onset_bars, int(tempo[0])
        else:
            self.music_data = notedetection.process_audio(self.audio_file_full_path, tempo=given_tempo)
            onset_times, onset_durations, onset_bars, tempo = self.music_data
            tempo = np.array([tempo])

        # Load music from downloaded audio file
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

    def run(self):
        """
        Control flow of the main gameplay loop
        :return: Next state of the game
        """
        if self.paused:  # This handles the case where the game was resumed from a paused state
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
                        pygame.mixer.music.pause()
                        return "Pause"

            # Do not start playing the music or run game logic until fps stabilizes after initialization
            if not self.game_started and self.clock.get_fps() > 1:
                mixer.music.play()  # Start music playback
                self.game_started = True

            # Stop the game loop when music finishes playing
            if self.game_started and (not mixer.music.get_busy()):
                return "End"

            self.step()
            self.render()

    # Unused
    def restart(self, seed=None):
        random.seed(seed)
        return

    def step(self):
        """
        Main control function for game play
        """
        if self.game_started:
            self.input_manager.update()
            self.steps += 1
            score = self.data.score

            # Obtain the score at this step and update the status of patterns
            temp_score = self.pattern_manager.update_patterns(self.steps, self.input_manager)
            score += temp_score

            # Ignore points gained from sliders
            if temp_score >= 10:
                self.data.combo += 1
                self.data.perfect_count += 1
                self.tap_sound_effect.play()
            self.data.score = score

    def render(self):
        """
        Render all game elements based on current step in the game.
        We first obtain the real fps from the pygame Clock object method, which is typically a little bit lower
        than the fps set due to lag and overhead.
        We add the real_time_steps variable by the set fps (60) by the actual fps.
        So, the real_time_steps variable will be higher than the game steps when there is lag.
        We call the sync_game_and_music method to align the steps variable to the real_time_steps.
        """
        fps = self.clock.get_fps()
        # print("Actual FPS:", fps)
        if fps and self.game_started:  # avoid division by zero errors
            self.real_time_steps += self.fps / fps

        self.sync_game_and_music()

        win = pygame.Surface((self.screen_width, self.screen_height))
        if use_game_background:
            win.blit(self.background, (0, 0))  # Use loaded game background
        else:
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
        # Check misses by seeing when patterns expire (go past their rendering lifetime) and have not been clicked
        if isMissed:
            self.data.highest_combo = max(self.data.combo, self.data.highest_combo)
            self.data.combo = 0
            miss_count = self.data.miss_count
            miss_count += 1
            self.data.miss_count = miss_count

        """
        Save the window on the buffer before displaying the cursor on the screen,
        to save the screen if pause game 
        """
        self.window_buffer.blit(win, (0, 0))

        # Display the cursor image on the screen
        cursor_img, cursor_img_rect, cursor_pressed_img, cursor_pressed_img_rect = self.cursor_images
        if self.input_manager.is_user_holding:
            cursor_pressed_img_rect.center = pygame.mouse.get_pos()  # update position
            win.blit(cursor_pressed_img, cursor_pressed_img_rect)  # draw the cursor
        else:
            cursor_img_rect.center = pygame.mouse.get_pos()
            win.blit(cursor_img, cursor_img_rect)

        # print cumulative score and combo
        self.score_text = "Score: {}".format(self.data.score)
        self.score_label = self.font.render(self.score_text, True, (255, 255, 255))
        self.score_label_rect = self.score_label.get_rect()
        self.score_label_rect.topright = (self.screen_width - 10, 10)
        win.blit(self.score_label, self.score_label_rect)
        self.combo_text = "Combo: {}".format(self.data.combo)
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
        # sync up game steps and music if real_time_steps and steps deviate by more than 1 step
        if self.game_started and abs(self.real_time_steps - self.steps) > 1.1:
            if 0 <= (self.real_time_steps - self.steps) <= 3:
                self.steps += 1  # try to speed up the game step to keep up
            elif 0 <= (self.steps - self.real_time_steps) <= 3:
                self.steps -= 1  # slow down the game steps to follow the music
            else:
                # Force audio to readjust to game time if too much deviation
                elapsed_time = self.steps / self.fps
                mixer.music.set_pos(elapsed_time)
                self.real_time_steps = self.steps  # realign real_time_steps to the game steps

    def close(self):
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()


class PauseScene:
    """
    Contains all the logic in the game paused state
    """
    def __init__(self, window, cursor_images):
        self.quit_click = False
        self.resume_selected = False
        self.restart_click = False
        self.menu_click = False
        self.window = window
        self.screen_width, self.screen_height = window.get_size()
        self.paused_screen = None  # Stores the last screen displayed in the game
        self.input_manager = InputManager()
        self.clock = pygame.time.Clock()

        self.cursor_images = cursor_images

    def run(self):
        self.resume_selected = False
        while not self.resume_selected or not self.restart_click or not self.menu_click or not self.quit_click:
            self.input_manager.update()
            self.render()

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "End"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.resume_selected = True

            if self.resume_selected:
                self.countdown()
                return "Resume"
            elif self.restart_click:
                return "Load"
            elif self.menu_click:
                return "Menu"
            elif self.quit_click:
                return "End"

    def render(self):
        win = pygame.Surface((self.screen_width, self.screen_height))
        win.blit(self.paused_screen, (0, 0))  # Display the last screen displayed in game scene
        self._apply_whiteness(win)

        font = pygame.font.Font(None, 70)  # Font for the score numbers
        text_color = (0, 0, 0)  # Black color
        hover_color = (128, 240, 255)  # Neon Blue color
        selected_text_color = (245, 255, 120)  # Light Yellow color

        # Paused label
        paused_label = Label(font, "GAME PAUSED", text_color, (self.screen_width // 2, 100), "center")
        paused_label.render(win)

        # Quit button
        quit_button = Button(font, "QUIT", text_color, hover_color, selected_text_color, (self.screen_width - 25, 650),
                             "bottomright", self.input_manager)
        quit_button.render(win)

        if quit_button.is_clicked:
            self.quit_click = True
            quit_button.select()

        # Menu button
        menu_button = Button(font, "MENU", text_color, hover_color, selected_text_color, (25, 650), "bottomleft", self.input_manager)
        menu_button.render(win)

        if menu_button.is_clicked:
            self.menu_click = True
            menu_button.select()

        # Resume button
        resume_button = Button(font, "RESUME", text_color, hover_color, selected_text_color,
                               (self.screen_width // 2, 250), "center", self.input_manager)
        resume_button.render(win)

        if resume_button.is_clicked:
            self.resume_selected = True
            resume_button.select()

        # Restart button
        restart_button = Button(font, "RESTART", text_color, hover_color, selected_text_color,
                                (self.screen_width // 2, 400), "center", self.input_manager)
        restart_button.render(win)

        if restart_button.is_clicked:
            self.restart_click = True
            restart_button.select()

        # Display cursor image
        cursor_img, cursor_img_rect, cursor_pressed_img, cursor_pressed_img_rect = self.cursor_images
        if self.input_manager.is_mouse_holding:
            cursor_pressed_img_rect.center = pygame.mouse.get_pos()  # update position
            win.blit(cursor_pressed_img, cursor_pressed_img_rect)  # draw the cursor
        else:
            cursor_img_rect.center = pygame.mouse.get_pos()
            win.blit(cursor_img, cursor_img_rect)

        self.window.blit(win, win.get_rect())
        pygame.event.pump()
        pygame.display.update()

    def countdown(self):
        """
        Handles the resume countdown
        """
        font = pygame.font.Font(None, 150)  # Font for the countdown numbers
        countdown_time = 3
        fps = 60
        for i in range(countdown_time * fps):
            win = pygame.Surface((self.screen_width, self.screen_height))
            win.blit(self.paused_screen, (0, 0))
            countdown_label = Label(font, str(countdown_time - i // fps), (255, 255, 255),
                                    (self.screen_width // 2, self.screen_height // 2), "center")
            countdown_label.render(win)
            cursor_img, cursor_img_rect, cursor_pressed_img, cursor_pressed_img_rect = self.cursor_images
            if self.input_manager.is_mouse_holding:
                cursor_pressed_img_rect.center = pygame.mouse.get_pos()  # update position
                win.blit(cursor_pressed_img, cursor_pressed_img_rect)  # draw the cursor
            else:
                cursor_img_rect.center = pygame.mouse.get_pos()
                win.blit(cursor_img, cursor_img_rect)

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
    """
    Contains all the logic in the menu scene
    """
    def __init__(self, window, data, cursor_images):
        self.start_click = False
        self.window = window
        self.screen_width, self.screen_height = window.get_size()
        self.input_manager = InputManager()
        self.clock = pygame.time.Clock()

        self.data = data

        self.cursor_images = cursor_images

        # Define label properties
        self.difficulty_label_text = "Difficulty:"
        self.approach_rate_label_text = "Approach Rate:"
        self.start_label_text = "START"
        self.menu_label_text = "MENU"

        self.label_font = pygame.font.Font(None, 60)
        self.label_color = (255, 255, 255)  # White color

        # Define button properties
        self.button_width, self.button_height = 60, 60
        self.button_margin = 10
        self.button_color = (0, 0, 0)
        self.button_font = pygame.font.Font(None, 60)
        self.button_hover_color = (128, 240, 255) # Neon Blue color
        self.button_text_color = (255, 255, 255)  # White color
        self.button_selected_text_color = (245, 255, 120)  # Light Yellow color

        # Calculate total width for buttons and margins
        self.total_width = (self.button_width + self.button_margin) * 10 - self.button_margin
        self.start_x = 450
        self.difficulty_button_pos_y = (self.screen_height - self.button_height) // 3 + 75
        self.approach_rate_button_pos_y = (self.screen_height - self.button_height) // 3 * 2 - 20

        # Calculate label position
        self.difficulty_label_pos_x = self.start_x - self.label_font.size(self.difficulty_label_text)[0] - 20
        self.approach_rate_label_pos_x = self.start_x - self.label_font.size(self.approach_rate_label_text)[0] - 20
        self.difficulty_label_pos_y = (self.screen_height - self.label_font.size(self.difficulty_label_text)[
            1]) // 3 + 50
        self.approach_rate_label_pos_y = (self.screen_height - self.label_font.size(self.approach_rate_label_text)[
            1]) // 3 * 2 - 50

    def run(self):
        while not self.start_click:
            self.input_manager.update()
            self.render()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "Stop Game"
            if self.start_click:
                return "Load"

    def render(self):
        pygame.mouse.set_visible(False)  # hides the cursor and will draw a cursor for playing rhythm game

        win = pygame.Surface((self.screen_width, self.screen_height))
        win.fill((0, 0, 0))

        # Menu label
        menu_label = Label(self.label_font, self.menu_label_text, self.label_color, (self.screen_width // 2, 100),
                           "center")
        menu_label.render(win)

        # Draw difficulty label
        difficulty_label = Label(self.label_font, self.difficulty_label_text, self.label_color,
                                 (self.difficulty_label_pos_x, self.difficulty_label_pos_y), "topleft")
        difficulty_label.render(win)

        # Draw difficulty buttons
        for i in range(10):
            button_pos_x = self.start_x + 20 + (self.button_width + self.button_margin) * i
            button_text = str(i + 1)
            difficulty_button = Button(self.button_font, button_text, self.button_text_color, self.button_hover_color,
                                       self.button_selected_text_color, (button_pos_x, self.difficulty_button_pos_y),
                                       "center", self.input_manager)
            if difficulty_button.is_clicked:
                self.data.difficulty = i + 1

            if i + 1 == self.data.difficulty:
                difficulty_button.select()
            else:
                difficulty_button.deselect()

            difficulty_button.render(win)

        # Draw approach rate label
        approach_rate_label = Label(self.label_font, self.approach_rate_label_text, self.label_color,
                                 (self.approach_rate_label_pos_x, self.approach_rate_label_pos_y), "topleft")
        approach_rate_label.render(win)

        # Draw approach rate buttons
        for i in range(10):
            button_pos_x = self.start_x + 20 + (self.button_width + self.button_margin) * i
            button_text = str(i + 1)
            approach_rate_button = Button(self.button_font, button_text, self.button_text_color,
                                       self.button_hover_color, self.button_selected_text_color,
                                       (button_pos_x, self.approach_rate_button_pos_y), "center", self.input_manager)
            if approach_rate_button.is_clicked:
                self.data.approach_rate = i + 1

            if self.data.approach_rate != (i + 1):
                approach_rate_button.deselect()
            else:
                approach_rate_button.select()

            approach_rate_button.render(win)

        # Start button
        start_button = Button(self.button_font, self.start_label_text, self.button_text_color,
                                       self.button_hover_color, self.button_selected_text_color,
                                       (self.screen_width - 25, self.screen_height - 25), "bottomright", self.input_manager)

        start_button.render(win)

        if start_button.is_clicked:
            self.start_click = True
            start_button.select()

        cursor_img, cursor_img_rect, cursor_pressed_img, cursor_pressed_img_rect = self.cursor_images
        if self.input_manager.is_mouse_holding:
            cursor_pressed_img_rect.center = pygame.mouse.get_pos()  # update position
            win.blit(cursor_pressed_img, cursor_pressed_img_rect)  # draw the cursor
        else:
            cursor_img_rect.center = pygame.mouse.get_pos()
            win.blit(cursor_img, cursor_img_rect)

        self.window.blit(win, win.get_rect())
        pygame.event.pump()
        pygame.display.update()


class EndScene:
    """
    Contains all the logic in the end scene
    """
    def __init__(self, window, data, cursor_images):
        self.end_click = False
        self.menu_click = False
        self.window = window
        self.screen_width, self.screen_height = window.get_size()
        self.input_manager = InputManager()
        self.clock = pygame.time.Clock()

        self.data = data
        self.cursor_images = cursor_images

        self.game_over_label_text = "GAME OVER"
        self.perfect_count_label_text = "Perfect Count:"
        self.miss_count_label_text = "Miss Count:"
        self.highest_combo_label_text = "Highest Combo:"
        self.total_score_label_text = "Total Score:"
        self.end_label_text = "QUIT"
        self.menu_label_text = "MENU"
        self.label_font = pygame.font.Font(None, 72)
        self.label_color = (255, 255, 255)  # White color
        self.button_hover_color = (128, 240, 255)  # Neon Blue color
        self.button_text_color = (255, 255, 255)  # White color
        self.button_selected_text_color = (245, 255, 120)  # Light Yellow color

    def run(self):
        while not self.end_click or self.menu_click:
            self.input_manager.update()
            self.render()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "Stop Game"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "Stop Game"
            if self.end_click:
                return "Stop Game"
            elif self.menu_click:
                return "Menu"

    def render(self):
        pygame.mouse.set_visible(False)  # hides the cursor and will draw a cursor for playing rhythm game
        win = pygame.Surface((self.screen_width, self.screen_height))
        win.fill((0, 0, 0))

        # Set Game Over Label
        game_over_label = Label(self.label_font, self.game_over_label_text, self.label_color,
                                    (self.screen_width // 2, 100), "center")
        game_over_label.render(win)

        # Set Perfect Count Label
        perfect_count_label = Label(self.label_font, self.perfect_count_label_text, self.label_color,
                                (700, 200), "topright")
        perfect_count_label.render(win)

        perfect_count_value_label = Label(self.label_font, "{}".format(self.data.perfect_count), self.label_color,
                                    (750, 200), "topleft")
        perfect_count_value_label.render(win)

        # Set Miss Count Label
        miss_count_label = Label(self.label_font, self.miss_count_label_text, self.label_color,
                                    (700, 280), "topright")
        miss_count_label.render(win)

        miss_count_value_label = Label(self.label_font, "{}".format(self.data.miss_count), self.label_color,
                                          (750, 280), "topleft")
        miss_count_value_label.render(win)

        # Set Highest Combo Label
        highest_combo_label = Label(self.label_font, self.highest_combo_label_text, self.label_color,
                                 (700, 360), "topright")
        highest_combo_label.render(win)

        highest_combo_value_label = Label(self.label_font, "{}".format(self.data.highest_combo), self.label_color,
                                       (750, 360), "topleft")
        highest_combo_value_label.render(win)

        # Set Total Score Label
        total_score_label = Label(self.label_font, self.total_score_label_text, self.label_color,
                                    (700, 440), "topright")
        total_score_label.render(win)

        total_score_value_label = Label(self.label_font, "{}".format(self.data.score), self.label_color,
                                          (750, 440), "topleft")
        total_score_value_label.render(win)

        # End button
        end_button = Button(self.label_font, self.end_label_text, self.button_text_color,
                              self.button_hover_color, self.button_selected_text_color,
                            (self.screen_width - 25, 650), "bottomright", self.input_manager)

        end_button.render(win)

        if end_button.is_clicked:
            self.end_click = True
            end_button.select()

        # Restart button
        menu_button = Button(self.label_font, self.menu_label_text, self.button_text_color,
                            self.button_hover_color, self.button_selected_text_color,
                            (25, 650), "bottomleft", self.input_manager)

        menu_button.render(win)

        if menu_button.is_clicked:
            self.menu_click = True
            menu_button.select()

        cursor_img, cursor_img_rect, cursor_pressed_img, cursor_pressed_img_rect = self.cursor_images
        if self.input_manager.is_mouse_holding:
            cursor_pressed_img_rect.center = pygame.mouse.get_pos()  # update position
            win.blit(cursor_pressed_img, cursor_pressed_img_rect)  # draw the cursor
        else:
            cursor_img_rect.center = pygame.mouse.get_pos()
            win.blit(cursor_img, cursor_img_rect)

        self.window.blit(win, win.get_rect())
        pygame.event.pump()
        pygame.display.update()


class LoadingScene:
    """
    Contains all the logic in the loading scene
    """
    def __init__(self, window, task, cursor_images):
        self.window = window
        self.screen_width, self.screen_height = window.get_size()
        self.input_manager = InputManager()
        self.clock = pygame.time.Clock()
        self.cursor_images = cursor_images

        self.task = task
        self.task_done = threading.Event()  # Event for signaling task completion

    def run_task(self):
        self.task()
        self.task_done.set()

    def run(self):
        threading.Thread(target=self.run_task, daemon=True).start()
        while not self.task_done.is_set():
            self.input_manager.update()
            self.render()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "Stop Game"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "Stop Game"
        return "Loading Finished"

    def render(self):
        font = pygame.font.Font(None, 70)  # Font for the score numbers
        text_color = (255, 255, 255)
        loading_text = ["LOADING .", "LOADING ..", "LOADING ..."]
        i = 0
        while not self.task_done.is_set():  # loop for loading
            pygame.mouse.set_visible(False)  # hides the cursor and will draw a cursor for playing rhythm game
            win = pygame.Surface((self.screen_width, self.screen_height))
            win.fill((0, 0, 0))

            fps = 30
            if i//fps == 3:  # prevent overflow of index
                i = 0
            else:
                #Loading label
                loading_label = Label(font, loading_text[i//fps], text_color,
                                      (self.screen_width // 2, self.screen_height // 2), "center")
                loading_label.render(win)

            cursor_img, cursor_img_rect, cursor_pressed_img, cursor_pressed_img_rect = self.cursor_images
            if self.input_manager.is_mouse_holding:
                cursor_pressed_img_rect.center = pygame.mouse.get_pos()  # update position
                win.blit(cursor_pressed_img, cursor_pressed_img_rect)  # draw the cursor
            else:
                cursor_img_rect.center = pygame.mouse.get_pos()
                win.blit(cursor_img, cursor_img_rect)

            self.window.blit(win, win.get_rect())
            pygame.event.pump()
            pygame.display.update()
            self.clock.tick(60)
            i += 1


class ReadyScene:
    """
    Contains all the logic in the ready scene
    """
    def __init__(self, window, cursor_images):
        self.play_selected = False
        self.window = window
        self.screen_width, self.screen_height = window.get_size()
        self.input_manager = InputManager()
        self.clock = pygame.time.Clock()
        self.cursor_images = cursor_images

    def run(self):
        while not self.play_selected:
            self.input_manager.update()
            self.render()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "Stop Game"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "Stop Game"
        return "Play"

    def render(self):
        pygame.mouse.set_visible(False)  # hides the cursor and will draw a cursor for playing rhythm game
        win = pygame.Surface((self.screen_width, self.screen_height))
        win.fill((0, 0, 0))

        font = pygame.font.Font(None, 70)  # Font for the score numbers
        loading_text = "Are YOU Ready?"
        play_text = ">>> PLAY <<<"
        text_color = (255, 255, 255)  # White color
        hover_color = (128, 240, 255)  # Neon blue color
        selected_text_color = (245, 255, 120)  # Light yellow color

        # Loading Text
        loading_label = Label(font, loading_text, text_color,
                                  (self.screen_width // 2, self.screen_height // 2 - 100), "center")
        loading_label.render(win)

        # Play button
        play_button = Button(font, play_text, text_color,
                              hover_color, selected_text_color,
                              (self.screen_width // 2, self.screen_height // 2 + 100), "center", self.input_manager)

        play_button.render(win)

        if play_button.is_clicked:
            self.play_selected = True
            play_button.select()

        cursor_img, cursor_img_rect, cursor_pressed_img, cursor_pressed_img_rect = self.cursor_images
        if self.input_manager.is_mouse_holding:
            cursor_pressed_img_rect.center = pygame.mouse.get_pos()  # update position
            win.blit(cursor_pressed_img, cursor_pressed_img_rect)  # draw the cursor
        else:
            cursor_img_rect.center = pygame.mouse.get_pos()
            win.blit(cursor_img, cursor_img_rect)

        self.window.blit(win, win.get_rect())
        pygame.event.pump()
        pygame.display.update()
        self.clock.tick(60)


def main():
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
