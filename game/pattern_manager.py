import random

from game.utils.patterns import *
from itertools import groupby


class PatternManager:
    """
    Pattern manager class generates patterns from musical data to form a map, keeps track of the list of patterns,
    and contains methods to easily operate on these patterns, like prerender, render and update.
    """
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

        # game boundaries for where the circle objects can be placed on the screen
        self.x_range = (self.radius * 5, screen_width - self.radius * 5)
        self.y_range = (self.radius * 2, self.screen_height - self.radius * 2)

    def generate_map(self, music_data):
        '''
        Generate objects/patterns and store in self.pattern_queue
        :param music_data: contains the timings, durations and bar numbers of the onsets
        :return: nothing
        '''
        onset_times, onset_durations, onset_bars, *_ = music_data
        onset_time_frames = [int(i * self.fps) for i in onset_times]
        onset_duration_frames = [int(i * self.fps) for i in onset_durations]
        self.generate_patterns(onset_time_frames, onset_duration_frames, onset_bars)
        self.pattern_queue = self.patterns[:self.queue_length]
        return

    def generate_patterns(self, onset_time_frames, onset_duration_frames, onset_bars):
        '''
        Determines the objects' locations on the screen according to their bar number and onset timings
        :param onset_time_frames: list of onset timings in frame number
        :param onset_duration_frames: list of  onset durations in frames
        :param onset_bars: list of bar numbers of all the onsets
        :return: nothing
        '''
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
                # which means there is no way to find the next object with the predetermined pattern distance
                # within the playable boundary
                while circle_position is None or np.linalg.norm(
                        circle_position - self.last_circle_position) != min_circle_distance:
                    # Generate a random angle in radians, repeat until a suitable direction is found
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
        '''
        Determine object type according to the onset duration and add to the pattern queue
        :param onset_time: onset timing for one note
        :param onset_duration: onset duration for one note
        :param circle_position: the note's circle position on the screen from generate_patterns
        :return: nothing
        '''
        # a little buffering in case detected onsets are too close to each other
        if onset_time - self.last_onset_time < 10:
            return
        self.last_onset_time = onset_time
        if onset_duration <= self.beat_duration * self.fps * 4:
            # choose circle object as the pattern type if the onset duration is short enough
            pattern_type = "TapPattern"
            t = onset_time
            starting_t = t
            ending_t = t + self.beat_duration * self.fps
        else:
            # choose slider object if the onset duration is long enough
            pattern_type = random.choice(["Line", "CubicBezier", "Arc"])
            t = onset_time
            starting_t = t
            ending_t = t + onset_duration / 16
            length = 100 / (self.beat_duration * self.fps) * onset_duration / 8

        # randomize circle color
        color = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))

        # add the pattern object to the pattern queue according to the previously determined object type
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
        """
        Updates the state of all patterns in the queue, and calculates the score earned from the patterns at frame t
        :param t: Time (in frames)
        :param input_manager: Input manager defined in game/utils/input_manager.py
        :return: Score earned at this frame
        """
        score_earned = 0
        for pattern in self.pattern_queue:
            temp_score, clicked = pattern.update(t, input_manager)
            score_earned += temp_score
            if clicked:
                break
        return score_earned

    def render_patterns(self, win, t):
        """
        Renders the patterns in the queue. If a pattern in the queue has past its lifetime, we delete it from the queue
        and load another one from the pattern list
        If a pattern "died", we check if it has been clicked and has a positive score, this is to return it to the
        main program to check for misses.
        :param win: Pygame surface to render on
        :param t: Time (in frames)
        :return: If no patterns have been missed (not clicked and zero marks)
        """
        flag = True
        for pattern in self.pattern_queue:
            isPastLifetime = pattern.render(win, t)
            if isPastLifetime:
                # Check if the pattern was missed
                pattern = self.pattern_queue[0]
                isHit = pattern.pressed
                flag = isHit and pattern.score > 0

                # Update queue and pattern list
                self.patterns = self.patterns[1:]
                self.pattern_queue = self.pattern_queue[1:]
                if self.queue_length < len(self.patterns):  # If not, all patterns have already been loaded to the queue
                    self.pattern_queue.append(self.patterns[self.queue_length])
        return flag

    def hot_load_caches(self):
        """
        Simulates rendering patterns, drawing approach circles, clicked circles and tracing circles
        across a period of time to hot load the cache so there are no cold misses at the beginning of the game
        which may lead to performance halts
        """
        surf = pygame.Surface((self.screen_width, self.screen_height))
        example_t = self.lifetime * 3  # at the middle
        for t in range(example_t * 2):
            # Simulate drawing patterns
            # Calculate the transparency based on the t value and lifetime
            time_difference = t - example_t
            interpolation_factor = min(abs(time_difference) / (self.lifetime / 2), 1)
            alpha = round(255 * (1 - interpolation_factor))

            alpha = int(max(0, min(alpha, 255)))  # Clamp alpha between 0 and 255
            if alpha == 0:
                continue
            if alpha < 255:
                apply_alpha(surf, alpha)

            # Draw other visual elements
            relative_time_difference = time_difference / self.lifetime

            draw_approach_circle(surf, (self.screen_width // 2, self.screen_height // 2),
                                 relative_time_difference, self.radius + self.stroke_width,
                                 self.stroke_width, self.approach_rate)
            draw_clicked_circle(surf, (self.screen_width // 2, self.screen_height // 2),
                                relative_time_difference, self.radius + self.stroke_width,
                                self.stroke_width)

        # Tracing circle
        center_color = (0, 0, 0, 0)
        center_color_hollow = (255, 255, 255, 150)
        circle_surface((255, 255, 255, 255), center_color,
                       self.radius + self.stroke_width, self.stroke_width, 1)
        circle_surface((255, 255, 255, 255), center_color_hollow,
                       self.radius + self.stroke_width, self.stroke_width, 1)
