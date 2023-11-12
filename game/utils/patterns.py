import numpy as np
import pygame
import pygame.gfxdraw
from abc import ABC, abstractmethod


def apply_alpha(alpha, win):
    tmp = pygame.Surface(win.get_size(), pygame.SRCALPHA)
    tmp.fill((255, 255, 255, alpha))
    frame = win.copy()
    frame.blit(tmp, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return frame


class TapPattern:
    def __init__(self, point, radius, stroke_width, color, t, lifetime):
        self.point = point
        self.color = color
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + stroke_width
        self.t = t
        self.lifetime = lifetime
        self._prerendered_frame = None

    def __repr__(self):
        return f"TapPattern(point={self.point}, radius={self.radius}, stroke_width={self.stroke_width}, " \
               f"color={self.color}, t={self.t}, lifetime={self.lifetime})"

    def prerender(self, win):
        if self._prerendered_frame is not None:
            return

        # Create a surface with higher resolution for supersampling
        width, height = win.get_size()
        ss_factor = 4  # Increase this value for higher quality antialiasing
        sup_width = width * ss_factor
        sup_height = height * ss_factor
        sup_surface = pygame.Surface((sup_width, sup_height), pygame.SRCALPHA)

        pygame.draw.circle(sup_surface, self.color, self.point * ss_factor, self.thickness * ss_factor)
        pygame.draw.circle(sup_surface, (0, 0, 0, 0), self.point * ss_factor, self.radius * ss_factor)

        # Downsample the supersampled surface to the original size with antialiasing
        downsampled_surface = pygame.transform.smoothscale(sup_surface, (width, height))

        self._prerendered_frame = downsampled_surface

    def render(self, win, t):
        if self._prerendered_frame is None:
            self.prerender(win)

        # Calculate the transparency based on the t value and lifetime
        time_difference = t - self.t
        interpolation_factor = min(abs(time_difference) / (self.lifetime / 2), 1)
        alpha = round(255 * (1 - interpolation_factor))

        alpha = max(0, min(alpha, 255))  # Clamp alpha between 0 and 255
        if alpha == 0:
            return t >= self.t
        frame = apply_alpha(alpha, self._prerendered_frame)
        win.blit(frame, (0, 0))
        # render more stuff here if needed

        if alpha >= 200:
            width, height = win.get_size()
            ss_factor = 2  # Increase this value for higher quality antialiasing
            sup_width = width * ss_factor
            sup_height = height * ss_factor
            sup_surface = pygame.Surface((sup_width, sup_height), pygame.SRCALPHA)
            pygame.draw.circle(sup_surface, (255, 130, 20),
                               self.point * ss_factor, (self.radius - self.stroke_width) * ss_factor)
            downsampled_surface = pygame.transform.smoothscale(sup_surface, (width, height))
            # Draw the downsampled surface onto the window
            win.blit(downsampled_surface, (0, 0))
        return False


class SliderPattern(ABC):
    def __init__(self, radius, stroke_width, starting_point,
                 ending_point, color, vertices, vertices_outer, starting_t, ending_t, lifetime):
        self.starting_point = starting_point
        self.ending_point = ending_point
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + stroke_width
        self.color = color
        self.vertices = vertices
        self.vertices_outer = vertices_outer
        self.starting_t = starting_t
        self.ending_t = ending_t
        self.lifetime = lifetime
        self._prerendered_frame = None

    @abstractmethod
    def _compute_coordinate(self, t):
        pass

    @abstractmethod
    def _compute_vertices(self, width):
        pass

    def prerender(self, win):
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

        pygame.draw.polygon(sup_surface, self.color,
                            self.vertices_outer * ss_factor, 0)

        pygame.draw.polygon(sup_surface, (0, 0, 0, 0),
                            self.vertices * ss_factor, 0)

        pygame.draw.circle(sup_surface, (0, 0, 0, 0),
                           start_scaled,
                           self.radius * ss_factor)
        pygame.draw.circle(sup_surface, (0, 0, 0, 0),
                           end_scaled,
                           self.radius * ss_factor)

        # Downsample the supersampled surface to the original size with antialiasing
        downsampled_surface = pygame.transform.smoothscale(sup_surface, (width, height))
        self._prerendered_frame = downsampled_surface

    def render(self, win, t):
        if self._prerendered_frame is None:
            self.prerender(win)

        # Calculate the transparency based on the t value and lifetime
        if self.starting_t <= t <= self.ending_t:
            alpha = 255
        else:
            time_difference = min(abs(self.starting_t - t), abs(t - self.ending_t))
            interpolation_factor = min(abs(time_difference) / (self.lifetime / 2), 1)
            alpha = round(255 * (1 - interpolation_factor))

        alpha = max(0, min(alpha, 255))  # Clamp alpha between 0 and 255
        if alpha == 0:
            return t >= self.ending_t
        frame = apply_alpha(alpha, self._prerendered_frame)
        win.blit(frame, (0, 0))

        if alpha >= 200 and self.starting_t <= t <= self.ending_t:
            width, height = win.get_size()
            ss_factor = 2  # Increase this value for higher quality antialiasing
            sup_width = width * ss_factor
            sup_height = height * ss_factor
            sup_surface = pygame.Surface((sup_width, sup_height), pygame.SRCALPHA)
            total_time = self.ending_t - self.starting_t
            p = (t - self.starting_t) / total_time
            p = max(0, min(p, 1)) # clamp
            pos = self._compute_coordinate(p) * ss_factor
            x, y = pos.flatten()
            pygame.draw.circle(sup_surface, (255, 130, 20),
                               (x, y), (self.radius - self.stroke_width) * ss_factor)
            downsampled_surface = pygame.transform.smoothscale(sup_surface, (width, height))
            # Draw the downsampled surface onto the window
            win.blit(downsampled_surface, (0, 0))

        return False


class Line(SliderPattern):
    def __init__(self, radius, stroke_width, P0, P1, color, starting_t, ending_t, lifetime):
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + self.stroke_width
        self.color = color
        self.P0 = P0
        self.P1 = P1
        self.normal = self._compute_normal()

        self.vertices = self._compute_vertices(self.radius)
        self.vertices_outer = self._compute_vertices(self.thickness)
        super().__init__(radius, stroke_width, P0, P1, color,
                         self.vertices, self.vertices_outer, starting_t, ending_t, lifetime)

    def __repr__(self):
        return f"LineSlider(radius={self.radius}, stroke_width={self.stroke_width}, P0={self.P0}, P1={self.P1}, " \
               f"color={self.color}, starting_t={self.starting_t}, ending_t={self.ending_t}, " \
               f"lifetime={self.lifetime})"

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
    def __init__(self, radius, stroke_width, P0, P1, P2, P3, color, starting_t, ending_t, lifetime):
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + self.stroke_width
        self.color = color
        dist1 = np.linalg.norm(P1 - P0)
        dist2 = np.linalg.norm(P2 - P1)
        dist3 = np.linalg.norm(P3 - P2)

        self.P0 = P0.reshape((2, 1))
        self.P1 = P1.reshape((2, 1))
        self.P2 = P2.reshape((2, 1))
        self.P3 = P3.reshape((2, 1))

        self.N = int((dist1 + dist2 + dist3) / 8)  # number of sampling segments for bezier curve

        self.points = self._compute_points()
        self.normals = self._compute_normals()
        self.vertices = self._compute_vertices(self.radius)
        self.vertices_outer = self._compute_vertices(self.thickness)
        super().__init__(radius, stroke_width, P0, P3, color,
                         self.vertices, self.vertices_outer, starting_t, ending_t, lifetime)

    def __repr__(self):
        return f"CubicBezierSlider(radius={self.radius}, stroke_width={self.stroke_width}, P0={self.P0}, " \
               f"P1={self.P1}, P2={self.P2}, P3={self.P3}, color={self.color}, " \
               f"starting_t={self.starting_t}, ending_t={self.ending_t}, lifetime={self.lifetime}, no. points = {self.N})"

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
    def __init__(self, radius, stroke_width, starting_point, ending_point, curve_radius, color, starting_t, ending_t,
                 lifetime):
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + self.stroke_width
        self.color = color
        self.starting_point = starting_point
        self.ending_point = ending_point

        self.curve_radius = curve_radius
        self._compute_arc()

        # number of sampling segments (increases as angle difference increases)
        self.N = abs(int(curve_radius * (self.end_angle - self.start_angle) / 15)) + 2

        self.points = self._compute_points()
        self.normals = self._compute_normals()
        self.vertices = self._compute_vertices(self.radius)
        self.vertices_outer = self._compute_vertices(self.thickness)
        super().__init__(radius, stroke_width, starting_point, ending_point, color,
                         self.vertices, self.vertices_outer, starting_t, ending_t, lifetime)

    def __repr__(self):
        return f"ArcSlider(radius={self.radius}, stroke_width={self.stroke_width}, starting_point={self.starting_point}, " \
               f"ending_point={self.ending_point}, curve_radius={self.curve_radius}, color={self.color}, " \
               f"starting_t={self.starting_t}, ending_t={self.ending_t}, lifetime={self.lifetime}, no. points = {self.N})"

    def _compute_arc(self):
        vec = self.ending_point - self.starting_point
        base_length = np.linalg.norm(vec)
        angle = 2 * np.arcsin(
            base_length / 2 / abs(self.curve_radius))  # angle of the sector/ corresponding to the arc P0P1
        mid_pt = (self.starting_point + self.ending_point) / 2
        height = self.curve_radius * np.cos(angle / 2)  # of isosceles triangle
        normal = np.array([-vec[1], vec[0]])
        normalized_normal = normal / np.linalg.norm(normal)
        self.centre = mid_pt + normalized_normal * height  # centre of circle
        vec0 = self.ending_point - self.centre
        vec1 = self.starting_point - self.centre
        self.start_angle = np.arctan2(vec0[1], vec0[0])
        self.end_angle = np.arctan2(vec1[1], vec1[0])

    def _compute_coordinate(self, t):
        t = np.asarray(t)

        angle = self.start_angle + (self.end_angle - self.start_angle) * t
        cis = np.array([np.cos(angle), np.sin(angle)]).T
        return cis * abs(self.curve_radius) + self.centre

    def _compute_points(self):
        t = np.linspace(0, 1, self.N)
        return self._compute_coordinate(t)

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
