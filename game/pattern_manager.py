import numpy as np
import pygame
import random
from pygame import mixer
from abc import ABC, abstractmethod
import math
from patterns import *

class PatternManager:
    def __init__(self):
        self.patterns = []

    def add_pattern(self, pattern):
        self.patterns.append(pattern)

    def remove_pattern(self, pattern):
        self.patterns.remove(pattern)

    def render_patterns(self, win):
        for pattern in self.patterns:
            pattern.render(win)