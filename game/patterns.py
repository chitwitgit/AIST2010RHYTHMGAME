import numpy as np
import pygame
import random
from abc import ABC, abstractmethod


class TapPattern():
    def __init__(self, x, y, radius, stroke_width, color):
        self.x = x
        self.y = y
        self.color = color
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


class SliderPattern(ABC):
    def __init__(self, radius, stroke_width, starting_point, ending_point, color, vertices):
        self.starting_point = starting_point
        self.ending_point = ending_point
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + stroke_width
        self.color = color
        self.vertices = vertices


    @abstractmethod
    def _compute_coordinate(self, t):
        pass

    @abstractmethod
    def _compute_vertices(self, width):
        pass

    def render(self, win):
        # Create a surface with higher resolution for supersampling
        width, height = win.get_size()
        ss_factor = 4  # Increase this value for higher quality antialiasing
        sup_width = width * ss_factor
        sup_height = height * ss_factor
        sup_surface = pygame.Surface((sup_width, sup_height), pygame.SRCALPHA)

        # Render the pattern on the supersampled surface
        start_scaled = self.starting_point * ss_factor
        end_scaled = self.ending_point * ss_factor
        pygame.draw.circle(sup_surface, self.color,
                           start_scaled,
                           self.thickness * ss_factor)
        pygame.draw.circle(sup_surface, self.color,
                           end_scaled,
                           self.thickness * ss_factor)

        pygame.draw.circle(sup_surface, (0, 0, 0, 0),
                           start_scaled,
                           self.radius * ss_factor)
        pygame.draw.circle(sup_surface, (0, 0, 0, 0),
                           end_scaled,
                           self.radius * ss_factor)

        pygame.draw.polygon(sup_surface, self.color,
                            self.vertices_outer * ss_factor, 0)

        pygame.draw.polygon(sup_surface, (0, 0, 0, 0),
                            self.vertices * ss_factor, 0)

        # Downsample the supersampled surface to the original size with antialiasing
        downsampled_surface = pygame.transform.smoothscale(sup_surface, (width, height))

        # Draw the downsampled surface onto the window
        win.blit(downsampled_surface, (0, 0))


class Line(SliderPattern):
    def __init__(self, radius, stroke_width, P0, P1, color):
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + self.stroke_width
        self.color = color
        self.P0 = P0
        self.P1 = P1
        self.normal = self._compute_normal()

        self.vertices = self._compute_vertices(self.radius)
        self.vertices_outer = self._compute_vertices(self.thickness)
        super().__init__(radius, stroke_width, P0, P1, color, self.vertices)

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


class CubicBezier(SliderPattern):
    def __init__(self, radius, stroke_width, P0, P1, P2, P3, color):
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + self.stroke_width
        self.color = color
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
        super().__init__(radius, stroke_width, P0, P3, color, self.vertices)

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


class Arc(SliderPattern):
    def __init__(self, radius, stroke_width, P0, P1, curve_radius, color):
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + self.stroke_width
        self.color = color
        self.P0 = P0
        self.P1 = P1

        self.curve_radius = curve_radius
        self._compute_arc()

        # number of sampling segments (increases as angle difference increases)
        N = int(10 * abs(self.end_angle - self.start_angle))
        self.N = N

        self.points = self._compute_points()
        self.normals = self._compute_normals()
        self.vertices = self._compute_vertices(self.radius)
        self.vertices_outer = self._compute_vertices(self.thickness)
        super().__init__(radius, stroke_width, P0, P1, color, self.vertices)

    def _compute_arc(self):
        vec = self.P1 - self.P0
        base_length = np.linalg.norm(vec)
        angle = 2 * np.arcsin(base_length / 2 / self.curve_radius)  # angle of the sector/ corresponding to the arc P0P1
        mid_pt = (self.P0 + self.P1) / 2
        height = self.curve_radius * np.cos(angle / 2)  # of isosceles triangle
        normal = np.array([-vec[1], vec[0]])
        normalized_normal = normal / np.linalg.norm(normal)
        self.centre = mid_pt + normalized_normal * height  # centre of circle
        vec0 = self.P0 - self.centre
        vec1 = self.P1 - self.centre
        self.start_angle = np.arctan2(vec0[1], vec0[0])
        self.end_angle = np.arctan2(vec1[1], vec1[0])

    def _compute_coordinate(self, t):
        if isinstance(t, (int, float)):
            t = np.array([t])  # Convert single value to a 1-element array

        angle = self.start_angle + (self.end_angle - self.start_angle) * t
        cis = np.array([np.cos(angle), np.sin(angle)]).T
        point = cis * self.curve_radius + self.centre

        return point

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
