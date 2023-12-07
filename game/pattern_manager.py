import random

import pygame

from utils.patterns import *
from itertools import groupby


class PatternManager:
    def __init__(self, screen_width, screen_height, fps, seed, difficulty, approach_rate, tempo):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.fps = fps
        self.stroke_width = 5
        self.seed = seed
        self.tempo = tempo
        self.beat_duration = 60 / self.tempo

        self.patterns = []
        self.pattern_queue = None
        self.queue_length = 12
        self.difficulty = difficulty
        self.approach_rate = approach_rate

        # difficulty dependent variables such as circle size and approach rate
        self.radius = 80 - (difficulty - 1) * 5
        self.lifetime = 150 - approach_rate * 8

        self.last_onset_time = 0
        self.last_circle_position = np.array([self.screen_width / 2, self.screen_height / 2])

        # game boundaries
        self.x_range = (self.radius * 5, screen_width - self.radius * 5)
        self.y_range = (self.radius * 2, self.screen_height - self.radius * 2)

    def generate_map(self, music_data):
        onset_times, onset_durations, onset_bars, *_ = music_data
        onset_time_frames = [int(i * self.fps) for i in onset_times]
        onset_duration_frames = [int(i * self.fps) for i in onset_durations]
        # print(onset_time_frames)
        # print(onset_duration_frames)
        # print(onset_bars)
        # self.generate_random_patterns(100)
        self.generate_patterns(onset_time_frames, onset_duration_frames, onset_bars)
        self.pattern_queue = self.patterns[:self.queue_length]
        return

    # This is NOT a primitive approach
    def generate_patterns(self, onset_time_frames, onset_duration_frames, onset_bars):
        # make the seed dependent on the input audio in some way
        seed_add = sum(onset_duration_frames)
        random.seed(self.seed + seed_add)
        np.random.seed(self.seed + seed_add)

        # preprocess the lists, so they are zipped according to their bar numbers
        zipped_data = [(time, duration, bar) for time, duration, bar
                       in zip(onset_time_frames, onset_duration_frames, onset_bars)]
        grouped_data = [list(group) for key, group in groupby(zipped_data, key=lambda x: x[2])]
        onset_time_frames = [[item[0] for item in group] for group in grouped_data]
        onset_duration_frames = [[item[1] for item in group] for group in grouped_data]
        # print(onset_time_frames)
        # print(onset_duration_frames)
        # print(onset_bars)

        # distances for each circle of a pattern and for each pattern depends on the difficulty
        circle_distance = 20 + 50 * self.difficulty
        pattern_distance = 800 + 15 * self.difficulty
        bottom_left_corner = np.array([self.x_range[0], self.y_range[0]])
        top_left_corner = np.array([self.x_range[0], self.y_range[1]])
        bottom_right_corner = np.array([self.x_range[1], self.y_range[0]])
        top_right_corner = np.array([self.x_range[1], self.y_range[1]])
        min_circle_distance = np.linalg.norm(top_right_corner - bottom_left_corner) / 2 - 50
        for onset_times, onset_durations in zip(onset_time_frames, onset_duration_frames):
            # compute the position of first circle of the current pattern/bar
            circle_position = None

            max_possible_distance = max(np.linalg.norm(bottom_right_corner - self.last_circle_position),
                                        np.linalg.norm(top_right_corner - self.last_circle_position),
                                        np.linalg.norm(bottom_left_corner - self.last_circle_position),
                                        np.linalg.norm(top_left_corner - self.last_circle_position))
            if max_possible_distance < pattern_distance:
                while circle_position is None or np.linalg.norm(
                        circle_position - self.last_circle_position) != min_circle_distance:
                    # Generate a random angle in radians
                    angle = np.random.uniform(0, 2 * np.pi)

                    # Calculate the coordinates for the circle_position
                    delta_x = min_circle_distance * np.cos(angle)
                    delta_y = min_circle_distance * np.sin(angle)
                    x_coord = np.clip(self.last_circle_position[0] + delta_x, *self.x_range)
                    y_coord = np.clip(self.last_circle_position[1] + delta_y, *self.y_range)

                    # Check if the Euclidean distance is within the desired range
                    if np.linalg.norm(np.array([x_coord, y_coord]) - self.last_circle_position) == min_circle_distance:
                        circle_position = np.array([x_coord, y_coord])
                        self.last_circle_position = circle_position
                        break
            else:
                while circle_position is None or np.linalg.norm(
                        circle_position - self.last_circle_position) != pattern_distance:
                    # Generate a random angle in radians
                    angle = np.random.uniform(0, 2 * np.pi)

                    # Calculate the coordinates for the circle_position
                    delta_x = pattern_distance * np.cos(angle)
                    delta_y = pattern_distance * np.sin(angle)
                    x_coord = np.clip(self.last_circle_position[0] + delta_x, *self.x_range)
                    y_coord = np.clip(self.last_circle_position[1] + delta_y, *self.y_range)

                    # Check if the Euclidean distance is within the desired range
                    if np.linalg.norm(np.array([x_coord, y_coord]) - self.last_circle_position) == pattern_distance:
                        circle_position = np.array([x_coord, y_coord])
                        self.last_circle_position = circle_position
                        break
            for onset_time, onset_duration in zip(onset_times, onset_durations):
                max_possible_distance = max(np.linalg.norm(bottom_right_corner - self.last_circle_position),
                                            np.linalg.norm(top_right_corner - self.last_circle_position),
                                            np.linalg.norm(bottom_left_corner - self.last_circle_position),
                                            np.linalg.norm(top_left_corner - self.last_circle_position))
                if max_possible_distance < circle_distance:
                    while np.linalg.norm(circle_position - self.last_circle_position) != min_circle_distance:
                        # Generate a random angle in radians
                        angle = np.random.uniform(0, 2 * np.pi)

                        # Calculate the coordinates for the circle_position
                        delta_x = min_circle_distance * np.cos(angle)
                        delta_y = min_circle_distance * np.sin(angle)
                        x_coord = np.clip(self.last_circle_position[0] + delta_x, *self.x_range)
                        y_coord = np.clip(self.last_circle_position[1] + delta_y, *self.y_range)

                        # Check if the Euclidean distance is within the desired range
                        if np.linalg.norm(
                                np.array([x_coord, y_coord]) - self.last_circle_position) == min_circle_distance:
                            circle_position = np.array([x_coord, y_coord])
                            self.generate_object(onset_time, onset_duration, circle_position)
                            self.last_circle_position = circle_position
                            break
                else:
                    while circle_position is None or np.linalg.norm(
                            circle_position - self.last_circle_position) != circle_distance:
                        # Generate a random angle in radians
                        angle = np.random.uniform(0, 2 * np.pi)

                        # Calculate the coordinates for the circle_position
                        delta_x = circle_distance * np.cos(angle)
                        delta_y = circle_distance * np.sin(angle)
                        x_coord = np.clip(self.last_circle_position[0] + delta_x, *self.x_range)
                        y_coord = np.clip(self.last_circle_position[1] + delta_y, *self.y_range)

                        # Check if the Euclidean distance is within the desired range
                        if np.linalg.norm(np.array([x_coord, y_coord]) - self.last_circle_position) == circle_distance:
                            circle_position = np.array([x_coord, y_coord])
                            self.generate_object(onset_time, onset_duration, circle_position)
                            self.last_circle_position = circle_position
                            break

    def generate_object(self, onset_time, onset_duration, circle_position):
        if onset_time - self.last_onset_time < 10:
            return
        self.last_onset_time = onset_time
        if onset_duration <= self.beat_duration * self.fps * 4:
            pattern_type = "TapPattern"
            t = onset_time
            starting_t = t
            ending_t = t + self.beat_duration * self.fps
        else:
            pattern_type = random.choice(["Line", "CubicBezier", "Arc"])
            t = onset_time
            starting_t = t
            ending_t = t + onset_duration / 16
            length = 100 / (self.beat_duration * self.fps) * onset_duration / 8

        color = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))
        if pattern_type == "TapPattern":
            position = circle_position
            tap = TapPattern(position, self.radius, self.stroke_width, color, t, self.lifetime, self.approach_rate)
            self.add_pattern(tap)
        elif pattern_type == "Line":
            position1 = circle_position
            position2 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
            line = Line(self.radius, self.stroke_width, position1, position2, color, starting_t, ending_t,
                        self.lifetime, self.approach_rate, length=length)
            self.add_pattern(line)
            self.last_onset_time = ending_t
        elif pattern_type == "CubicBezier":
            position1 = circle_position
            position2 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
            position3 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
            position4 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
            curve = CubicBezier(self.radius, self.stroke_width, position1, position2, position3, position4, color,
                                starting_t, ending_t, self.lifetime, self.approach_rate, length=length)
            self.add_pattern(curve)
            self.last_onset_time = ending_t
        else:
            position1 = circle_position
            position2 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
            # curve radius must be longer than half the distance between position 1 and position 2
            dist = np.linalg.norm(position1 - position2)
            curve_radius = random.uniform(dist / 1.7, dist / 1.05)
            curve_radius *= random.choice([-1, 1])  # negative curve radius inverts the curve direction
            curve = Arc(self.radius, self.stroke_width, position1, position2, curve_radius, color, starting_t,
                        ending_t, self.lifetime, self.approach_rate, length=length)
            self.add_pattern(curve)
            self.last_onset_time = ending_t

    def add_pattern(self, pattern):
        self.patterns.append(pattern)

    def remove_pattern(self, pattern):
        self.patterns.remove(pattern)

    def prerender_patterns(self, win):
        for pattern in self.patterns:
            pattern.prerender(win)

    def update_patterns(self, t, input_manager):
        score_earned = 0
        for pattern in self.pattern_queue:
            temp_score, clicked = pattern.update(t, input_manager)
            score_earned += temp_score
            if clicked:
                break
        return score_earned

    def render_patterns(self, win, t):
        flag = True
        for pattern in self.pattern_queue:
            if pattern.render(win, t):  # past its lifetime
                pattern = self.pattern_queue[0]
                isHit = pattern.pressed
                self.patterns = self.patterns[1:]
                self.pattern_queue = self.pattern_queue[1:]
                if self.queue_length < len(self.patterns):
                    self.pattern_queue.append(self.patterns[self.queue_length])
                flag = isHit and pattern.score > 0
        return flag

    def hot_load_caches(self):
        surf = pygame.Surface((self.screen_width, self.screen_height))
        example_t = self.lifetime * 3  # at the middle
        for t in range(example_t * 2):
            # Calculate the transparency based on the t value and lifetime
            time_difference = t - example_t
            interpolation_factor = min(abs(time_difference) / (self.lifetime / 2), 1)
            alpha = round(255 * (1 - interpolation_factor))

            alpha = int(max(0, min(alpha, 255)))  # Clamp alpha between 0 and 255
            if alpha == 0:
                continue
            if alpha < 255:
                apply_alpha(surf, alpha)
            relative_time_difference = time_difference / self.lifetime
            draw_approach_circle(surf, (self.screen_width // 2, self.screen_height // 2),
                                 relative_time_difference, self.radius + self.stroke_width,
                                 self.stroke_width, self.approach_rate)
            draw_clicked_circle(surf, (self.screen_width // 2, self.screen_height // 2),
                                relative_time_difference, self.radius + self.stroke_width,
                                self.stroke_width)
