import numpy as np
import pygame
import random
from pygame import mixer
from abc import ABC, abstractmethod
import math


class Sprite(ABC):
    @abstractmethod
    def _move(self):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def render(self, win):
        pass


class Pattern(Sprite):
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.init_x = x

    def _move(self):
        # Move the ball randomly up or down
        direction = random.choice([-1, 1])
        self.y += direction * 5

    def update(self):
        self._move()

    @abstractmethod
    def render(self, win):
        pass


class Point(Pattern):
    def __init__(self, x, y, radius, stroke_width, color):
        super().__init__(x, y, color)
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + stroke_width

    def render(self, win):
        # Create a surface with higher resolution for supersampling
        width, height = win.get_size()
        ss_factor = 4  # Increase this value for higher quality antialiasing
        sup_width = width * ss_factor
        sup_height = height * ss_factor
        sup_surface = pygame.Surface((sup_width, sup_height), pygame.SRCALPHA)

        pygame.draw.circle(win, self.color, (self.x * ss_factor, self.y * ss_factor), self.thickness)
        pygame.draw.circle(win, (0, 0, 0), (self.x * ss_factor, self.y * ss_factor), self.radius)

        # Downsample the supersampled surface to the original size with antialiasing
        downsampled_surface = pygame.transform.smoothscale(sup_surface, (width, height))

        # Draw the downsampled surface onto the window
        win.blit(downsampled_surface, (0, 0))


class Line(Pattern):
    def __init__(self, x, y, radius, stroke_width, P0, P1, color):
        super().__init__(x, y, color)
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + stroke_width
        self.P0 = P0
        self.P1 = P1
        self.normal = self._compute_normal()

        self.vertices = self._compute_vertices(self.radius)
        self.vertices_outer = self._compute_vertices(self.thickness)

    def _compute_coordinate(self, t):
        return t * self.P0 + (1 - t) * self.P1

    def _compute_normal(self):
        direction = self.P1 - self.P0
        normal = np.array([-direction[1], direction[0]])
        return normal / np.linalg.norm(normal)

    def _compute_vertices(self, width):
        vertex1 = self.P0 + width * self.normal
        vertex2 = self.P1 + width * self.normal
        vertex3 = self.P1 - width * self.normal
        vertex4 = self.P0 - width * self.normal
        return np.array([vertex1, vertex2, vertex3, vertex4])

    def render(self, win):
        # Create a surface with higher resolution for supersampling
        width, height = win.get_size()
        ss_factor = 4  # Increase this value for higher quality antialiasing
        sup_width = width * ss_factor
        sup_height = height * ss_factor
        sup_surface = pygame.Surface((sup_width, sup_height), pygame.SRCALPHA)

        # Render the pattern on the supersampled surface
        P0Scaled = self.P0 * ss_factor
        P1Scaled = self.P1 * ss_factor
        pygame.draw.circle(sup_surface, self.color,
                           P0Scaled,
                           self.thickness * ss_factor)
        pygame.draw.circle(sup_surface, self.color,
                           P1Scaled,
                           self.thickness * ss_factor)

        pygame.draw.circle(sup_surface, (0, 0, 0, 0),
                           P0Scaled,
                           self.radius * ss_factor)
        pygame.draw.circle(sup_surface, (0, 0, 0, 0),
                           P1Scaled,
                           self.radius * ss_factor)

        pygame.draw.polygon(sup_surface, self.color,
                            self.vertices_outer * ss_factor, 0)

        pygame.draw.polygon(sup_surface, (0, 0, 0, 0),
                            self.vertices * ss_factor, 0)

        # Downsample the supersampled surface to the original size with antialiasing
        downsampled_surface = pygame.transform.smoothscale(sup_surface, (width, height))

        # Draw the downsampled surface onto the window
        win.blit(downsampled_surface, (0, 0))


class CubicBezier(Pattern):
    def __init__(self, x, y, radius, stroke_width, P0, P1, P2, P3, color):
        super().__init__(x, y, color)
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + stroke_width
        self.P0 = P0.reshape((2, 1))
        self.P1 = P1.reshape((2, 1))
        self.P2 = P2.reshape((2, 1))
        self.P3 = P3.reshape((2, 1))

        N = 25  # number of sampling segments for bezier curve
        self.N = N

        self.points = self._compute_points()
        self.normals = self._compute_normals()
        self.vertices = self._compute_vertices(self.radius)
        self.vertices_outer = self._compute_vertices(self.thickness)

    def _compute_coordinate(self, t):
        return (1 - t) ** 3 * self.P0 + 3 * (1 - t) ** 2 * t * self.P1 + 3 * (1 - t) * t ** 2 * self.P2 + t ** 3 * \
            self.P3

    def _compute_points(self):
        t = np.linspace(0, 1, self.N)
        points = self._compute_coordinate(t)
        return np.transpose(points)

    def _compute_normals(self):
        t = np.linspace(0, 1, self.N)
        dx_dt = 3 * (1 - t) ** 2 * (self.P1[0] - self.P0[0]) + 6 * (1 - t) * t * (
                self.P2[0] - self.P1[0]) + 3 * t ** 2 * (self.P3[0] - self.P2[0])
        dy_dt = 3 * (1 - t) ** 2 * (self.P1[1] - self.P0[1]) + 6 * (1 - t) * t * (
                self.P2[1] - self.P1[1]) + 3 * t ** 2 * (self.P3[1] - self.P2[1])
        magnitudes = np.sqrt(dx_dt ** 2 + dy_dt ** 2)
        return np.column_stack((-dy_dt / magnitudes, dx_dt / magnitudes))

    def _compute_vertices(self, width):
        vertices1 = self.points + width * self.normals
        vertices2 = self.points - width * self.normals
        return np.concatenate((vertices1, vertices2[::-1]), axis=0)

    def render(self, win):
        # Create a surface with higher resolution for supersampling
        width, height = win.get_size()
        ss_factor = 4  # Increase this value for higher quality antialiasing
        sup_width = width * ss_factor
        sup_height = height * ss_factor
        sup_surface = pygame.Surface((sup_width, sup_height), pygame.SRCALPHA)  # Create surface with alpha channel

        # Render the pattern on the supersampled surface
        P0Scaled = self.P0 * ss_factor
        P3Scaled = self.P3 * ss_factor
        P0Scaled = P0Scaled[0][0], P0Scaled[1][0]
        P3Scaled = P3Scaled[0][0], P3Scaled[1][0]
        pygame.draw.circle(sup_surface, self.color,
                           P0Scaled,
                           self.thickness * ss_factor)
        pygame.draw.circle(sup_surface, self.color,
                           P3Scaled,
                           self.thickness * ss_factor)

        pygame.draw.polygon(sup_surface, self.color,
                            self.vertices_outer * ss_factor, 0)

        pygame.draw.polygon(sup_surface, (0, 0, 0, 0),
                            self.vertices * ss_factor, 0)

        pygame.draw.circle(sup_surface, (0, 0, 0, 0),
                           P0Scaled,
                           self.radius * ss_factor)
        pygame.draw.circle(sup_surface, (0, 0, 0, 0),
                           P3Scaled,
                           self.radius * ss_factor)

        # Downsample the supersampled surface to the original size with antialiasing
        downsampled_surface = pygame.transform.smoothscale(sup_surface, (width, height))

        # Draw the downsampled surface onto the window
        win.blit(downsampled_surface, (0, 0))


class Arc(Pattern):
    def __init__(self, x, y, radius, stroke_width, start_angle, end_angle, curve_radius, color):
        super().__init__(x, y, color)
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + stroke_width
        self.start_angle = start_angle
        self.end_angle = end_angle

        self.curve_radius = curve_radius

        # number of sampling segments (increases as angle difference increases)
        N = int(10 * abs(end_angle - start_angle))
        self.N = N

        self.points = self._compute_points()
        self.normals = self._compute_normals()
        self.vertices = self._compute_vertices(self.radius)
        self.vertices_outer = self._compute_vertices(self.thickness)

    def _compute_coordinate(self, t):
        angle = self.start_angle + (self.end_angle - self.start_angle) * t
        x = self.x + self.curve_radius * np.cos(angle)
        y = self.y + self.curve_radius * np.sin(angle)
        return np.column_stack((x, y))

    def _compute_points(self):
        t = np.linspace(0, 1, self.N)
        points = self._compute_coordinate(t)
        return points

    def _compute_normals(self):
        t = np.linspace(0, 1, self.N)
        angles = self.start_angle + (self.end_angle - self.start_angle) * t
        dx_dt = -np.sin(angles)
        dy_dt = np.cos(angles)
        return np.column_stack((-dy_dt, dx_dt))

    def _compute_vertices(self, width):
        vertices1 = self.points + width * self.normals
        vertices2 = self.points - width * self.normals
        return np.concatenate((vertices1, vertices2[::-1]), axis=0)

    def render(self, win):
        # Create a surface with higher resolution for supersampling
        width, height = win.get_size()
        ss_factor = 4  # Increase this value for higher quality antialiasing
        sup_width = width * ss_factor
        sup_height = height * ss_factor
        sup_surface = pygame.Surface((sup_width, sup_height), pygame.SRCALPHA)  # Create surface with alpha channel

        # Render the pattern on the supersampled surface
        pygame.draw.circle(sup_surface, self.color,
                           self.points[0] * ss_factor,
                           self.thickness * ss_factor)
        pygame.draw.circle(sup_surface, self.color,
                           self.points[-1] * ss_factor,
                           self.thickness * ss_factor)

        pygame.draw.polygon(sup_surface, self.color,
                            self.vertices_outer * ss_factor, 0)

        pygame.draw.polygon(sup_surface, (0, 0, 0, 0),
                            self.vertices * ss_factor, 0)

        pygame.draw.circle(sup_surface, (0, 0, 0, 0),
                           self.points[0] * ss_factor,
                           self.radius * ss_factor)
        pygame.draw.circle(sup_surface, (0, 0, 0, 0),
                           self.points[-1] * ss_factor,
                           self.radius * ss_factor)

        # Downsample the supersampled surface to the original size with antialiasing
        downsampled_surface = pygame.transform.smoothscale(sup_surface, (width, height))

        # Draw the downsampled surface onto the window
        win.blit(downsampled_surface, (0, 0))
