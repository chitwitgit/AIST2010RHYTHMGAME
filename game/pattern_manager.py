import random
from utils.patterns import *


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
        self.approach_rate = approach_rate

        # difficulty dependent variables such as circle size and approach rate
        self.radius = 50 - (difficulty - 1) * 2.5
        self.lifetime = 245 - approach_rate * 17.5

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

    # This is a primitive approach
    def generate_patterns(self, onset_time_frames, onset_duration_frames, onset_bars):
        # make the seed dependent on the input audio in some way
        seed_add = sum(onset_duration_frames)
        random.seed(self.seed + seed_add)
        last_onset_time = 0
        for onset_time, onset_duration in zip(onset_time_frames, onset_duration_frames):
            if onset_time - last_onset_time < 10:
                continue
            last_onset_time = onset_time
            pattern_type = random.choice(["TapPattern", "TapPattern", "TapPattern", "TapPattern", "TapPattern",
                                          "Line", "CubicBezier", "Arc"])
            t = onset_time
            starting_t = t
            ending_t = t + min(max(onset_duration, self.fps / 2),
                               self.fps)  # hard code clamp duration to half second to one second
            color = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))
            if pattern_type == "TapPattern":
                position = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                tap = TapPattern(position, self.radius, self.stroke_width, color, t, self.lifetime, self.approach_rate)
                self.add_pattern(tap)
            elif pattern_type == "Line":
                position1 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                position2 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                line = Line(self.radius, self.stroke_width, position1, position2, color, starting_t, ending_t,
                            self.lifetime, self.approach_rate, length=100)
                self.add_pattern(line)
                last_onset_time = ending_t
            elif pattern_type == "CubicBezier":
                position1 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                position2 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                position3 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                position4 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                curve = CubicBezier(self.radius, self.stroke_width, position1, position2, position3, position4, color,
                                    starting_t, ending_t, self.lifetime, self.approach_rate, length=100)
                self.add_pattern(curve)
                last_onset_time = ending_t
            else:
                position1 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                position2 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                # curve radius must be longer than half the distance between position 1 and position 2
                dist = np.linalg.norm(position1 - position2)
                curve_radius = random.uniform(dist / 1.7, dist / 1.05)
                curve_radius *= random.choice([-1, 1])  # negative curve radius inverts the curve direction
                curve = Arc(self.radius, self.stroke_width, position1, position2, curve_radius, color, starting_t,
                            ending_t, self.lifetime, self.approach_rate, length=100)
                self.add_pattern(curve)
                last_onset_time = ending_t

    def generate_random_patterns(self, n):
        t = 60
        random.seed(self.seed)
        for _ in range(n):
            pattern_type = random.choice(["TapPattern", "Line", "CubicBezier", "Arc"])
            color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
            if pattern_type == "TapPattern":
                position = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                tap = TapPattern(position, self.radius, self.stroke_width, color, t, self.lifetime, self.approach_rate)
                self.add_pattern(tap)
            elif pattern_type == "Line":
                starting_t = t
                duration = random.uniform(30, 60)
                ending_t = t + duration
                t += duration
                position1 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                position2 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                line = Line(self.radius, self.stroke_width, position1, position2, color, starting_t, ending_t,
                            self.lifetime)
                self.add_pattern(line)
            elif pattern_type == "CubicBezier":
                starting_t = t
                duration = random.uniform(30, 60)
                ending_t = t + duration
                t += duration
                position1 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                position2 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                position3 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                position4 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                curve = CubicBezier(self.radius, self.stroke_width, position1, position2, position3, position4, color,
                                    starting_t, ending_t, self.lifetime)
                self.add_pattern(curve)
            else:
                starting_t = t
                duration = random.uniform(30, 60)
                ending_t = t + duration
                t += duration
                position1 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                position2 = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                # curve radius must be longer than half the distance between position 1 and position 2
                dist = np.linalg.norm(position1 - position2)
                curve_radius = random.uniform(dist / 1.7, dist / 1.05)
                curve = Arc(self.radius, self.stroke_width, position1, position2, curve_radius, color, starting_t,
                            ending_t, self.lifetime)
                self.add_pattern(curve)
            t += random.uniform(0, 240)

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
            score_earned += pattern.update(t, input_manager)
        return score_earned

    def render_patterns(self, win, t):
        for pattern in self.pattern_queue:
            if pattern.render(win, t):  # past its lifetime
                self.patterns = self.patterns[1:]
                self.pattern_queue = self.pattern_queue[1:]
                if self.queue_length < len(self.patterns):
                    self.pattern_queue.append(self.patterns[self.queue_length])
