import random
from utils.patterns import *
from itertools import groupby


class PatternManager:
    def __init__(self, screen_width, screen_height, fps, seed, difficulty, approach_rate):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.fps = fps
        self.stroke_width = 5
        self.seed = seed

        self.patterns = []
        self.pattern_queue = None
        self.queue_length = 12
        self.difficulty = difficulty
        self.approach_rate = approach_rate

        # difficulty dependent variables such as circle size and approach rate
        self.radius = 50 - (difficulty - 1) * 2.5
        self.lifetime = 150 - approach_rate * 8

        self.last_onset_time = 0
        self.last_circle_position = np.array([self.screen_width / 2, self.screen_height / 2])

        # game boundaries
        self.x_range = (100, 700)
        self.y_range = (50, 400)

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

        # preprocess the lists so they are zipped according to their bar numbers
        zipped_data = [(time, duration, bar) for time, duration, bar
                       in zip(onset_time_frames, onset_duration_frames, onset_bars)]
        grouped_data = [list(group) for key, group in groupby(zipped_data, key=lambda x: x[2])]
        onset_time_frames = [[item[0] for item in group] for group in grouped_data]
        onset_duration_frames = [[item[1] for item in group] for group in grouped_data]
        # print(onset_time_frames)
        # print(onset_duration_frames)
        # print(onset_bars)

        # distances for each circle of a pattern and for each pattern depends on the difficulty
        circle_distance = 80 + 25 * self.difficulty
        pattern_distance = 300 + 15 * self.difficulty
        circle_position = np.array([self.screen_width/2, self.screen_height/2])
        for onset_times, onset_durations in zip(onset_time_frames, onset_duration_frames):
            # compute the position of first circle of the current pattern/bar
            angle = np.random.uniform(0, 2 * np.pi)
            rand_pattern_distance = np.random.uniform(150, pattern_distance)

            # calculate the coordinates for first_position
            delta_x = rand_pattern_distance * np.cos(angle)
            delta_y = rand_pattern_distance * np.sin(angle)
            x_coord = np.clip(self.last_circle_position[0] + delta_x, self.x_range[0], self.x_range[1])
            y_coord = np.clip(self.last_circle_position[1] + delta_y, self.y_range[0], self.y_range[1])

            # update circle position
            circle_position = np.array([x_coord, y_coord])
            self.last_circle_position = circle_position
            for onset_time, onset_duration in zip(onset_times, onset_durations):
                # generate a random direction for patterns to move
                angle = np.random.uniform(0, 2 * np.pi)
                rand_circle_distance = np.random.uniform(100, circle_distance)

                # calculate the coordinates for first_position
                delta_x = rand_circle_distance * np.cos(angle)
                delta_y = rand_circle_distance * np.sin(angle)
                x_coord = np.clip(self.last_circle_position[0] + delta_x, self.x_range[0], self.x_range[1])
                y_coord = np.clip(self.last_circle_position[1] + delta_y, self.y_range[0], self.y_range[1])

                # update circle position
                circle_position = np.array([x_coord, y_coord])
                self.generate_object(onset_time, onset_duration, circle_position)
                self.last_circle_position = circle_position

    def generate_object(self, onset_time, onset_duration, circle_position):
        if onset_time - self.last_onset_time < 10:
            return
        self.last_onset_time = onset_time
        pattern_type = random.choice(["TapPattern", "TapPattern", "TapPattern", "TapPattern", "TapPattern",
                                      "TapPattern", "TapPattern", "TapPattern", "TapPattern", "TapPattern",
                                      "TapPattern", "TapPattern", "TapPattern", "TapPattern", "TapPattern",
                                      "Line", "CubicBezier", "Arc"])
        t = onset_time
        starting_t = t
        ending_t = t + min(max(onset_duration, self.fps / 2),
                           self.fps)  # hard code clamp duration to half second to one second
        color = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))
        if pattern_type == "TapPattern":
            position = circle_position
            tap = TapPattern(position, self.radius, self.stroke_width, color, t, self.lifetime, self.approach_rate)
            self.add_pattern(tap)
        elif pattern_type == "Line":
            position1 = circle_position
            position2 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
            line = Line(self.radius, self.stroke_width, position1, position2, color, starting_t, ending_t,
                        self.lifetime, self.approach_rate, length=100)
            self.add_pattern(line)
            self.last_onset_time = ending_t
        elif pattern_type == "CubicBezier":
            position1 = circle_position
            position2 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
            position3 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
            position4 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
            curve = CubicBezier(self.radius, self.stroke_width, position1, position2, position3, position4, color,
                                starting_t, ending_t, self.lifetime, self.approach_rate, length=100)
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
                        ending_t, self.lifetime, self.approach_rate, length=100)
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
