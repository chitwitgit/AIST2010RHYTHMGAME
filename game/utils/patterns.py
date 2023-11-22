import numpy as np
import pygame
import pygame.gfxdraw
from abc import ABC, abstractmethod
from functools import lru_cache


@lru_cache(maxsize=None)  # cache commonly used operations to speed up performance
def create_alpha_surface(size, alpha):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill((255, 255, 255, alpha))
    return surf


def apply_alpha(surf, alpha):
    tmp = create_alpha_surface(surf.get_size(), alpha)
    frame = surf.copy()
    frame.blit(tmp, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return frame


@lru_cache(maxsize=None)
def circle_surface(color, color_inner, thickness, stroke_width, scaling_factor):
    surface_size = max((int(thickness * scaling_factor) + 1), 1) * 2
    surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
    pygame.draw.circle(surface, color,
                       (surface_size // 2, surface_size // 2),
                       thickness * scaling_factor)
    pygame.draw.circle(surface, color_inner,
                       (surface_size // 2, surface_size // 2),
                       (thickness * scaling_factor - stroke_width))
    return surface


def draw_approach_circle(win, point, relative_time_difference, thickness, stroke_width, approach_rate):
    approach_constant = 100 / approach_rate
    if abs(relative_time_difference) >= approach_constant:
        return
    else:
        scaling_factor = 1 + (410 - (approach_rate - 1) * 40) * (-relative_time_difference) / approach_constant
    alpha = (
        255 - 255 * 1 / approach_constant ** 2 * relative_time_difference ** 2
        if relative_time_difference < 0
        else 255 - 255 * 1 / np.cbrt(approach_constant) * np.cbrt(relative_time_difference)
    )
    alpha = min(max(alpha, 0), 255)
    circle = circle_surface((255, 255, 255, alpha), (0, 0, 0, 0),
                            thickness, stroke_width, scaling_factor)
    rect = circle.get_rect(center=point)
    win.blit(circle, rect)


def draw_clicked_circle(win, point, relative_time_difference, thickness, stroke_width):
    if abs(relative_time_difference) >= 0.3:
        return
    scaling_factor = np.cbrt(1 + 8 * relative_time_difference)
    alpha = 255 - 255 * 1 / np.cbrt(0.3) * np.cbrt(relative_time_difference)
    alpha = min(max(alpha, 0), 255)
    circle = circle_surface((255, 255, 255, alpha), (0, 0, 0, 0),
                            thickness, stroke_width, scaling_factor)
    rect = circle.get_rect(center=point)
    win.blit(circle, rect)


class TapPattern:
    def __init__(self, point, radius, stroke_width, color, t, lifetime, approach_rate):
        self.point = point
        self.color = color
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + stroke_width
        self.t = t
        self.lifetime = lifetime
        self._prerendered_frame = None
        self.pressed = False
        self.press_time = 0
        self.starting_point = point
        self.ending_point = point
        self.approach_rate = approach_rate
        self.score = 0

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

    def update(self, t, input_manager):
        mouse_clicked = self.check_mouse(t, input_manager)
        if mouse_clicked:
            time_difference = t - self.t
            relative_time_difference = time_difference / 120
            rounded_relative_time_difference = np.around(relative_time_difference, 2)
            score = 100 * min(max(1.4 - 10 * abs(rounded_relative_time_difference), 0), 1)
            score = np.around(score / 10, 0) * 10  # round to nearest ten
            self.score += score
            return score
        return 0

    def check_mouse(self, t, input_manager):
        if self.pressed:
            return False
        time_difference = t - self.t
        relative_time_difference = time_difference / self.lifetime
        if -0.4 < relative_time_difference < 0.2:  # allow for early clicks but don't register clicks that are too late
            # Get the current mouse position
            mouse_pos = input_manager.mouse_pos
            is_inside_circle = np.linalg.norm(np.asarray(mouse_pos) - self.point) < self.thickness
            if is_inside_circle and input_manager.is_user_inputted:  # inside the circle and is new input
                self.pressed = True
                self.press_time = t
                return True
        return False

    def render(self, win, t):
        if self.pressed:
            return self.render_based_on_pressed(win, t)
        if self._prerendered_frame is None:
            self.prerender(win)

        # Calculate the transparency based on the t value and lifetime
        time_difference = t - self.t
        interpolation_factor = min(abs(time_difference) / (self.lifetime / 2), 1)
        alpha = round(255 * (1 - interpolation_factor))

        alpha = max(0, min(alpha, 255))  # Clamp alpha between 0 and 255
        if alpha == 0:
            return t >= self.t
        if alpha < 255:
            frame = apply_alpha(self._prerendered_frame, alpha)
            win.blit(frame, (0, 0))
        else:
            win.blit(self._prerendered_frame, (0, 0))
        # render more stuff here if needed

        self.render_based_on_time(win, t)
        return False

    def render_based_on_time(self, win, t):
        time_difference = t - self.t
        relative_time_difference = time_difference / self.lifetime
        draw_approach_circle(win, self.point, relative_time_difference, self.thickness, self.stroke_width, self.approach_rate)

    def render_based_on_pressed(self, win, t):
        time_difference = t - self.press_time
        relative_time_difference = time_difference / self.lifetime
        draw_clicked_circle(win, self.point, relative_time_difference, self.thickness, self.stroke_width)
        font = pygame.font.Font(None, 25)  # Font for the countdown numbers
        countdown_text = font.render(str(int(self.score)), True, (255, 255, 255))
        countdown_text_rect = countdown_text.get_rect(center=self.point)
        win.blit(countdown_text, countdown_text_rect)

        return abs(relative_time_difference) > 0.6


class SliderPattern(ABC):
    def __init__(self, radius, stroke_width, starting_point, ending_point, color, vertices, vertices_outer, starting_t,
                 ending_t, lifetime, approach_rate):
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
        self.pressed = False
        self.press_time = 0
        self.approach_rate = approach_rate
        self.score = 0
        self.last_pressed = None

    @abstractmethod
    def _compute_coordinate(self, t):
        pass

    @abstractmethod
    def _compute_vertices(self, width):
        pass

    def update(self, t, input_manager):
        already_pressed = self.pressed
        mouse_clicked = self.check_mouse(t, input_manager)
        if mouse_clicked:
            if not already_pressed:
                time_difference = t - self.starting_t
                relative_time_difference = time_difference / 120
                rounded_relative_time_difference = np.around(relative_time_difference, 2)
                score = 100 * min(max(1.4 - 10 * abs(rounded_relative_time_difference), 0), 1)
                score = np.around(score / 10, 0) * 10  # round to nearest ten
                self.score += score
                return score
            else:
                # only add scores for sliding during the sliding time
                if self.starting_t <= t <= self.ending_t:
                    score = 2
                    self.score += score

                    total_time = self.ending_t - self.starting_t
                    p = (t - self.starting_t) / total_time
                    p = max(0, min(p, 1))  # clamp
                    self.last_pressed = self._compute_coordinate(p)
                    return score
        return 0

    def check_mouse(self, t, input_manager):
        if self.pressed:
            mouse_pos = input_manager.mouse_pos
            # more lenient on the position for sliding
            is_inside_circle = np.linalg.norm(np.asarray(mouse_pos) - self.starting_point) < self.thickness * 2
            if is_inside_circle and input_manager.is_user_holding:  # inside the circle and is clicking
                return True
            else:
                return False
        time_difference = t - self.starting_t
        relative_time_difference = time_difference / self.lifetime
        if abs(relative_time_difference) < 0.3:
            # Get the current mouse position
            mouse_pos = input_manager.mouse_pos
            is_inside_circle = np.linalg.norm(np.asarray(mouse_pos) - self.starting_point) < self.thickness
            if is_inside_circle and input_manager.is_user_inputted:  # inside the circle and is clicking
                self.pressed = True
                self.press_time = t
                return True
        return False

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
        frame = apply_alpha(self._prerendered_frame, alpha)
        win.blit(frame, (0, 0))
        self.render_based_on_time(win, t)
        self.render_based_on_pressed(win, t)
        return False

    def render_based_on_time(self, win, t):
        if t <= self.ending_t:
            if self.pressed:
                self.draw_tracing_circle(win, t, hollow=False)
            else:
                self.draw_tracing_circle(win, t, hollow=True)

        if not self.pressed:
            time_difference = t - self.starting_t
            relative_time_difference = time_difference / self.lifetime
            draw_approach_circle(win, self.starting_point, relative_time_difference, self.thickness, self.stroke_width,
                                 self.approach_rate)

    def render_based_on_pressed(self, win, t):
        if not self.pressed:
            return
        time_difference = t - self.press_time
        relative_time_difference = time_difference / self.lifetime
        draw_clicked_circle(win, self.starting_point, relative_time_difference, self.thickness, self.stroke_width)
        font = pygame.font.Font(None, 25)
        countdown_text = font.render(str(int(self.score)), True, (255, 255, 255))

        if self.last_pressed is None:
            self.last_pressed = self.starting_point
        countdown_text_rect = countdown_text.get_rect(center=tuple(self.last_pressed))
        win.blit(countdown_text, countdown_text_rect)
        return abs(relative_time_difference) > 0.6

    def draw_tracing_circle(self, win, t, hollow=False):
        total_time = self.ending_t - self.starting_t
        p = (t - self.starting_t) / total_time
        p = max(0, min(p, 1))  # clamp
        pos = self._compute_coordinate(p)
        pos = pos.flatten()

        center_color = (0, 0, 0, 0) if hollow else (255, 255, 255, 150)
        circle = circle_surface((255, 255, 255, 255), center_color,
                                self.thickness, self.stroke_width, 1)

        # to prevent some weird runtime errors formed by weird floating point ops
        pos = np.clip(pos, -2147483648, 2147483647)

        rect = circle.get_rect(center=pos)
        win.blit(circle, rect)


class Line(SliderPattern):
    def __init__(self, radius, stroke_width, P0, P1, color, starting_t, ending_t, lifetime, approach_rate, length=-1):
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + self.stroke_width
        self.color = color
        self.P0 = P0
        self.P1 = P1
        vec = self.P1 - self.P0
        self.length = np.linalg.norm(vec)
        if length > 0:
            scale_ratio = length / self.length  # scale up/down the line to match the intended length
            self.P1 = self.P0 + vec * scale_ratio
        self.normal = self._compute_normal()

        self.vertices = self._compute_vertices(self.radius)
        self.vertices_outer = self._compute_vertices(self.thickness)
        self.approach_rate = approach_rate
        super().__init__(radius, stroke_width, self.P0, self.P1, color, self.vertices, self.vertices_outer, starting_t,
                         ending_t, lifetime, self.approach_rate)

    def __repr__(self):
        return f"LineSlider(radius={self.radius}, stroke_width={self.stroke_width}, P0={self.P0}, P1={self.P1}, " \
               f"color={self.color}, starting_t={self.starting_t}, ending_t={self.ending_t}, " \
               f"lifetime={self.lifetime})"

    def _compute_coordinate(self, t):
        return (1 - t) * self.P0 + t * self.P1

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
    def __init__(self, radius, stroke_width, P0, P1, P2, P3, color, starting_t, ending_t, lifetime, approach_rate, length=-1):
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + self.stroke_width
        self.color = color
        dist1 = np.linalg.norm(P1 - P0)
        dist2 = np.linalg.norm(P2 - P1)
        dist3 = np.linalg.norm(P3 - P2)

        self.P0 = P0
        self.P1 = P1
        self.P2 = P2
        self.P3 = P3

        self.N = int((dist1 + dist2 + dist3) / 2)  # number of sampling segments for bezier curve
        self.ts = np.linspace(0, 1, self.N)

        self.points = self._compute_points()
        self.segment_lengths = np.linalg.norm(np.diff(self.points, axis=0), axis=1)
        self.length = np.sum(self.segment_lengths)
        if length > 0:
            vec1 = P1 - P0
            vec2 = P2 - P0
            vec3 = P3 - P0
            scale_ratio = length / self.length  # scale up/down the line to match the intended length
            self.P1 = self.P0 + vec1 * scale_ratio
            self.P2 = self.P0 + vec2 * scale_ratio
            self.P3 = self.P0 + vec3 * scale_ratio
            self.points = self._compute_points()  # recalculate the points
        self.subdivide_curve(accuracy=0.2)
        self.accumulated_lengths = np.cumsum(self.segment_lengths)
        self.normals = self._compute_normals()
        self.vertices = self._compute_vertices(self.radius)
        self.vertices_outer = self._compute_vertices(self.thickness)
        self.approach_rate = approach_rate
        super().__init__(radius, stroke_width, self.P0, self.P3, color, self.vertices, self.vertices_outer, starting_t,
                         ending_t, lifetime, self.approach_rate)

    def __repr__(self):
        return f"CubicBezierSlider(radius={self.radius}, stroke_width={self.stroke_width}, P0={self.P0}, " \
               f"P1={self.P1}, P2={self.P2}, P3={self.P3}, color={self.color}, " \
               f"starting_t={self.starting_t}, ending_t={self.ending_t}, lifetime={self.lifetime}, no. points = {self.N})"

    def _compute_coordinate(self, t):
        target_length = t * self.length
        if target_length <= 0:
            return self._compute_point_helper(0.0)
        elif target_length >= self.length:
            return self._compute_point_helper(1.0)

        index = np.searchsorted(self.accumulated_lengths, target_length) - 1
        segment_start_length = self.accumulated_lengths[index]
        segment_length = self.segment_lengths[index]
        segment_progress = (target_length - segment_start_length) / segment_length
        t = self.ts[index] * segment_progress + self.ts[index + 1] * (1 - segment_progress)  # interpolate t value
        return self._compute_point_helper(t)

    def _compute_point_helper(self, t):
        return ((1 - t) ** 3 * self.P0.reshape((2, 1)) + 3 * (1 - t) ** 2 * t * self.P1.reshape((2, 1))
                + 3 * (1 - t) * t ** 2 * self.P2.reshape((2, 1)) + t ** 3 * self.P3.reshape((2, 1)))

    def _compute_points(self):
        t = np.linspace(0, 1, self.N)
        self.ts = t
        points = self._compute_point_helper(t)
        return np.transpose(points)

    def _compute_normals(self):
        t = self.ts
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

    def _subdivide_curve(self, points, ts, accuracy):
        point1 = points[0]
        t1 = ts[0]
        new_points = [points[0]]
        new_ts = [ts[0]]
        finished = True
        for point, t in zip(points[1:], ts[1:]):
            point2 = point
            t2 = t
            mid_pt = (point1 + point2) / 2
            mid_t = (t1 + t2) / 2
            actual_point = np.asarray(self._compute_point_helper(mid_t).flatten())
            if np.linalg.norm(mid_pt - actual_point) > accuracy:
                #  insert point between the points
                new_points.append(actual_point)
                new_ts.append(mid_t)
                # print(f"subdivided point {mid_pt}")
                finished = False
            new_points.append(point)
            new_ts.append(t)
            point1 = point
            t1 = t
        if not finished:
            new_points, new_ts = list(self._subdivide_curve(np.array(new_points), np.array(new_ts), accuracy))
        return np.asarray(new_points), np.asarray(new_ts)

    def subdivide_curve(self, accuracy):
        self.points, self.ts = self._subdivide_curve(self.points, self.ts, accuracy)


class Arc(SliderPattern):
    def __init__(self, radius, stroke_width, starting_point, ending_point, curve_radius, color, starting_t, ending_t,
                 lifetime, approach_rate, length=-1):
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + self.stroke_width
        self.color = color
        self.starting_point = starting_point
        self.ending_point = ending_point

        self.curve_radius = curve_radius
        self._compute_arc()
        self.length = self.curve_radius * (self.end_angle - self.start_angle)
        if length > 0:
            vec = ending_point - starting_point
            scale_ratio = length / self.length  # scale up/down the line to match the intended length
            self.ending_point = self.starting_point + vec * scale_ratio
            self.curve_radius = self.curve_radius * scale_ratio
            self._compute_arc()  # recalculate the arc

        # number of sampling segments (increases as angle difference increases)
        self.N = abs(int(curve_radius * (self.end_angle - self.start_angle) / 15)) + 2
        self.ts = np.linspace(0, 1, self.N)

        self.points = self._compute_points()
        self.subdivide_curve(accuracy=0.2)

        self.normals = self._compute_normals()
        self.vertices = self._compute_vertices(self.radius)
        self.vertices_outer = self._compute_vertices(self.thickness)
        self.approach_rate = approach_rate
        super().__init__(radius, stroke_width, self.starting_point, self.ending_point, color, self.vertices,
                         self.vertices_outer, starting_t, ending_t, lifetime, self.approach_rate)

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
        vec0 = self.starting_point - self.centre
        vec1 = self.ending_point - self.centre
        self.start_angle = np.arctan2(vec0[1], vec0[0])
        self.end_angle = np.arctan2(vec1[1], vec1[0])

    def _compute_coordinate(self, t):
        t = np.asarray(t)

        angle = self.start_angle + (self.end_angle - self.start_angle) * t
        cis = np.array([np.cos(angle), np.sin(angle)]).T
        return cis * abs(self.curve_radius) + self.centre

    def _compute_points(self):
        t = np.linspace(0, 1, self.N)
        self.ts = t
        return self._compute_coordinate(t)

    def _compute_normals(self):
        t = self.ts
        angles = self.start_angle + (self.end_angle - self.start_angle) * t
        dx_dt = -np.sin(angles)
        dy_dt = np.cos(angles)
        return np.column_stack((-dy_dt, dx_dt))

    def _compute_vertices(self, width):
        vertices1 = self.points + width * self.normals
        vertices2 = self.points - width * self.normals
        return np.concatenate((vertices1, vertices2[::-1]), axis=0)

    def _subdivide_curve(self, points, ts, accuracy):
        point1 = points[0]
        t1 = ts[0]
        new_points = [points[0]]
        new_ts = [ts[0]]
        finished = True
        for point, t in zip(points[1:], ts[1:]):
            point2 = point
            t2 = t
            mid_pt = (point1 + point2) / 2
            mid_t = (t1 + t2) / 2
            actual_point = np.asarray(self._compute_coordinate(mid_t).flatten())
            if np.linalg.norm(mid_pt - actual_point) > accuracy:
                #  insert point between the points
                new_points.append(actual_point)
                new_ts.append(mid_t)
                print(f"subdivided point {mid_pt}")
                finished = False
            new_points.append(point)
            new_ts.append(t)
            point1 = point
            t1 = t
        if not finished:
            new_points, new_ts = list(self._subdivide_curve(np.array(new_points), np.array(new_ts), accuracy))
        return np.asarray(new_points), np.asarray(new_ts)

    def subdivide_curve(self, accuracy):
        self.points, self.ts = self._subdivide_curve(self.points, self.ts, accuracy)
