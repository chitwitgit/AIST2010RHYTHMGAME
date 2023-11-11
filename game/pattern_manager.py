import numpy as np
import pygame
import random
from pygame import mixer
from abc import ABC, abstractmethod
import math
from patterns import *

import numpy as np


class PatternManager:
    def __init__(self, screen_width, screen_height, seed):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.radius = 20
        self.stroke_width = 5
        self.lifetime = 120
        random.seed(seed)

        self.patterns = []
        self.generate_random_patterns(100)
        self.pattern_queue = self.patterns[:8]
        self.queue_number = 8

    def generate_random_patterns(self, n):
        t = 60
        for i in range(n):
            pattern_type = random.choice(["TapPattern", "Line", "CubicBezier", "Arc"])
            color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
            if pattern_type == "TapPattern":
                position = np.array([random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)])
                tap = TapPattern(position, self.radius, self.stroke_width, color, t, self.lifetime)
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
                curve_radius = random.uniform(dist / 1.7,  dist/ 1.05)
                curve = Arc(self.radius, self.stroke_width, position1, position2, curve_radius, color, starting_t,
                            ending_t, self.lifetime)
                self.add_pattern(curve)
            t += random.uniform(60, 240)

    def add_pattern(self, pattern):
        self.patterns.append(pattern)

    def remove_pattern(self, pattern):
        self.patterns.remove(pattern)

    """def prerender_patterns(self, win):
        for pattern in self.patterns:
            pattern.prerender(win)"""

    def render_patterns(self, win, t):
        for pattern in self.pattern_queue:
            if pattern.render(win, t):  # past its lifetime
                self.patterns = self.patterns[1:]
                self.pattern_queue = self.pattern_queue[1:]
                self.pattern_queue.append(self.patterns[self.queue_number])
