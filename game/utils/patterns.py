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
def circle_surface(color, color_inner, thickness, stroke_width, scaling_factor=1):
    """
    Creates a pygame surface containing a antialiased hollow circle with radius "thickness" and a stroke width
    The circle size will be scaled by the variable "scaling_factor"
    Written in a way that maximises cache hit rates
    :param color: Color of the circle
    :param color_inner: Color of the circle inside the stroke_width, set to transparent color for hollow circle
    :param thickness: Radius of whole circle, before scaling factor
    :param stroke_width: Stroke width of the outer band
    :param scaling_factor: Scales the size of circle by this factor, including this controllable variable improves cache
    hit rates
    :return: Pygame circle surface with the circle drawn
    """
    surface_size = max((int(thickness * scaling_factor) + 1), 1) * 2
    ss_factor = 4
    sup_width = surface_size * ss_factor
    sup_height = surface_size * ss_factor
    sup_surface = pygame.Surface((sup_width, sup_height), pygame.SRCALPHA)

    pygame.draw.circle(sup_surface, color,
                       (sup_width // 2, sup_height // 2),
                       thickness * scaling_factor * ss_factor)
    pygame.draw.circle(sup_surface, color_inner,
                       (sup_width // 2, sup_height // 2),
                       (thickness * scaling_factor - stroke_width) * ss_factor)

    # Downsample the supersampled surface to the original size with antialiasing
    downsampled_surface = pygame.transform.smoothscale(sup_surface, (surface_size, surface_size))
    return downsampled_surface


def draw_approach_circle(win, point, relative_time_difference, thickness, stroke_width, approach_rate):
    """
    Draws approach circle for a pattern
    :param win: Pygame surface to draw on
    :param point: Centre of the approach circle
    :param relative_time_difference: Calculated by the time difference between the starting time and current time
    divided by the lifetime of the pattern
    :param thickness: Thickness of the pattern
    :param stroke_width: Stroke width of the pattern
    :param approach_rate: Approach rate of game
    """
    approach_variable = 1.5 + 1.2 * np.cbrt(approach_rate)  # tune this to control how fast the approach circle comes in
    approach_constant = 1 / approach_variable
    if relative_time_difference > approach_constant:
        return

    size_factor = 1.2 # tune this to control size of approach circle
    scaling_factor = 1 - size_factor * approach_variable * relative_time_difference

    alpha = (
        # show up quickly
        255 + 255 * 1 / pow(approach_constant, 2.4) * pow(abs(relative_time_difference), 2.4)
        if relative_time_difference < 0
        # fade out quickly to reduce clutter
        else 255 - 255 * 1 / np.sqrt(approach_constant) * np.sqrt(relative_time_difference)
    )
    alpha = int(min(max(alpha, 0), 255))  # clamp
    if alpha == 0:
        return
    circle = circle_surface((255, 255, 255, alpha), (0, 0, 0, 0),
                            thickness, stroke_width, scaling_factor)
    rect = circle.get_rect(center=point)
    win.blit(circle, rect)


def draw_clicked_circle(win, point, relative_time_difference, thickness, stroke_width):
    """
        Draws clicked circle for a pattern
        :param win: Pygame surface to draw on
        :param point: Centre of the clicked circle
        :param relative_time_difference: Calculated by the time difference between the current time and clicked time
        divided by the lifetime of the pattern
        :param thickness: Thickness of the pattern
        :param stroke_width: Stroke width of the pattern
        """
    if relative_time_difference >= 0.3 or relative_time_difference < 0:
        return
    scaling_factor = np.sqrt(1 + 8 * relative_time_difference)
    alpha = 255 - 255 * 1 / np.cbrt(0.3) * np.cbrt(relative_time_difference)
    alpha = min(max(alpha, 0), 255)
    circle = circle_surface((255, 255, 255, alpha), (0, 0, 0, 0),
                            thickness, stroke_width, scaling_factor)
    rect = circle.get_rect(center=point)
    win.blit(circle, rect)


class TapPattern:
    def __init__(self, point, radius, stroke_width, color, t, lifetime, approach_rate):
        """
        Constructor for the tap pattern class
        :param point: Position of the tap pattern (x, y)
        :param radius: Radius of the inner circle
        :param stroke_width: Stroke width for the pattern
        :param color: Color as (R, G, B)
        :param t: Intended click time in frames
        :param lifetime: Determines how long the patterns fades in and fades out before and after its intended time
        :param approach_rate: Approach rate
        """
        self.point = point
        self.color = color
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + stroke_width
        self.t = t
        self.lifetime = lifetime
        self._prerendered_frame = None  # Use prerendering to accelerate real time performance
        self.pressed = False
        self.press_time = 0
        self.starting_point = point
        self.ending_point = point
        self.approach_rate = approach_rate
        self.score = 0

    def __repr__(self):
        return f"TapPattern(point={self.point}, radius={self.radius}, stroke_width={self.stroke_width}, " \
               f"color={self.color}, t={self.t}, lifetime={self.lifetime})"

    def update(self, t, input_manager):
        """
        Updates the pattern for a step
        :param t: current time (in frames)
        :param input_manager: input manager defined in input_manager.py
        :return: a tuple of score gained from the pattern, and a boolean indicating that if pattern was clicked
        """
        mouse_clicked = self.check_mouse(t, input_manager)
        if mouse_clicked:
            time_difference = t - self.t
            relative_time_difference = time_difference / 120
            rounded_relative_time_difference = np.around(relative_time_difference, 2)

            # calculate score
            tolerance = 1.4  # 1 = strict, full marks only at the perfect frame, higher for more lenient timing
            score = 100 * min(max(tolerance - 10 * abs(rounded_relative_time_difference), 0), 1)
            score = np.around(score / 10, 0) * 10  # round to nearest ten
            self.score += score
            return score, True
        return 0, False

    def check_mouse(self, t, input_manager):
        """
        Check if the pattern is newly clicked at this moment
        :param t: current time (in frames)
        :param input_manager: input manager defined in input_manager.py
        :return: boolean of whether the pattern is newly clicked
        """

        if self.pressed:  # already clicked, ignore
            return False

        time_difference = t - self.t
        relative_time_difference = time_difference / 120
        if abs(relative_time_difference) < 0.3:  # in the valid window
            # Get the current mouse position
            mouse_pos = input_manager.mouse_pos
            is_inside_circle = np.linalg.norm(np.asarray(mouse_pos) - self.point) < self.thickness
            if is_inside_circle and input_manager.is_user_inputted:  # inside the circle and is new input
                self.pressed = True  # update state
                self.press_time = t  # save the time when the pattern was clicked
                return True
        return False

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
        if self.pressed:
            return self.render_based_on_pressed(win, t)
        if self._prerendered_frame is None:
            self.prerender(win)

        # Calculate the transparency based on the t value and lifetime
        time_difference = t - self.t
        interpolation_factor = min(abs(time_difference) / (self.lifetime / 2), 1)
        alpha = round(255 * (1 - interpolation_factor))

        alpha = int(max(0, min(alpha, 255)))  # Clamp alpha between 0 and 255

        # Render the pattern on the screen using the prerendered frame and applying the alpha value
        if alpha == 0:
            return t >= self.t
        if alpha < 255:
            frame = apply_alpha(self._prerendered_frame, alpha)
            win.blit(frame, (0, 0))
        else:
            win.blit(self._prerendered_frame, (0, 0))

        self.render_based_on_time(win, t)
        return False

    def render_based_on_time(self, win, t):
        """
        Draw approach circle
        """
        time_difference = t - self.t
        relative_time_difference = time_difference / self.lifetime
        draw_approach_circle(win, self.point, relative_time_difference, self.thickness, self.stroke_width,
                             self.approach_rate)

    def render_based_on_pressed(self, win, t):
        """
        Draw clicked circle and display score of the pattern
        """
        time_difference = t - self.press_time
        relative_time_difference = time_difference / self.lifetime
        draw_clicked_circle(win, self.point, relative_time_difference, self.thickness, self.stroke_width)
        font = pygame.font.Font(None, 25)  # Font for the score numbers
        score_text = font.render(str(int(self.score)), True, (255, 255, 255))
        score_text_rect = score_text.get_rect(center=self.point)
        win.blit(score_text, score_text_rect)

        return abs(relative_time_difference) > 0.6


class SliderPattern(ABC):
    def __init__(self, radius, stroke_width, starting_point, ending_point, color, vertices, vertices_outer, starting_t,
                 ending_t, lifetime, approach_rate):
        """
        Base class for a slider pattern, containing universal methods like update, render and prerender
        Slider Patterns can take a length parameter that will automatically scale parameters and the whole curve
        to adjust to the length
        :param radius: Radius of inner area
        :param stroke_width: Stroke width for the pattern
        :param starting_point: Starting point for the pattern
        :param ending_point: Ending point for the pattern
        :param color: Color as (R, G, B)
        :param vertices: Stores the vertices for the inner polygon for rendering (computed using normal extrusion)
        :param vertices_outer: Stores the vertices for the outer polygon for rendering (computed using normal extrusion)
        :param starting_t: Starting time (in frames) to click the pattern
        :param ending_t: Ending time (in frames)
        :param lifetime: Determines how long the patterns fades in and fades out before and after its intended time
        :param approach_rate: Approach rate
        """
        self.starting_point = starting_point
        self.ending_point = ending_point
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + stroke_width
        self.color = color
        self.vertices = vertices
        self.vertices_outer = vertices_outer
        self.starting_t = starting_t
        self.ending_t = int(ending_t)
        self.lifetime = lifetime
        self._prerendered_frame = None  # Use prerendering to accelerate real time performance
        self.pressed = False
        self.press_time = 0
        self.approach_rate = approach_rate
        self.score = 0
        self.last_pressed = None

    @abstractmethod
    def _compute_coordinate(self, t):
        # Calculates the coordinate along the curve with a t value
        pass

    @abstractmethod
    def _compute_vertices(self, width):
        # Calculates the vertices using normal extrusion
        pass

    def update(self, t, input_manager):
        """
        Updates the pattern for a step
        :param t: current time (in frames)
        :param input_manager: input manager defined in input_manager.py
        :return: a tuple of score gained from the pattern, and a boolean indicating that if pattern was clicked
        """
        already_pressed = self.pressed
        mouse_clicked = self.check_mouse(t, input_manager)
        if mouse_clicked:
            if not already_pressed:
                time_difference = t - self.starting_t
                relative_time_difference = time_difference / 120
                rounded_relative_time_difference = np.around(relative_time_difference, 2)

                # calculate score
                tolerance = 1.4  # 1 = strict, full marks only at the perfect frame, higher for more lenient timing
                score = 100 * min(max(tolerance - 10 * abs(rounded_relative_time_difference), 0), 1)
                score = np.around(score / 10, 0) * 10  # round to nearest ten
                self.score += score
                return score, True
            else:
                # only add scores for sliding during the sliding time
                if self.starting_t <= t <= self.ending_t:
                    # add 2 to the score for every frame that the user is holding
                    score = 2
                    self.score += score

                    # Save the last pressed location for displaying score
                    total_time = self.ending_t - self.starting_t
                    p = (t - self.starting_t) / total_time
                    p = max(0, min(p, 1))  # clamp
                    self.last_pressed = self._compute_coordinate(p)
                    return score, True
        return 0, False

    def check_mouse(self, t, input_manager):
        """
        Check the pattern with user input with 3 cases:
        1. If the pattern has never been clicked and is newly clicked
        2. If the player is sliding and holding around the pattern
        3. If the player is not interacting with the pattern
        :param t: current time (in frames)
        :param input_manager: input manager defined in input_manager.py
        :return: boolean of whether the user is interacting with the pattern in cases 1 and 2
        """
        if self.pressed:  # Already pressed, check if user is sliding the pattern
            total_time = self.ending_t - self.starting_t
            p = (t - self.starting_t) / total_time
            p = max(0, min(p, 1))  # clamp
            pos = self._compute_coordinate(p)  # Compute the current position the user has to hold down in
            mouse_pos = input_manager.mouse_pos
            # more lenient on the position for sliding
            is_inside_circle = np.linalg.norm(np.asarray(mouse_pos) - pos.flatten()) < self.thickness * 2
            if is_inside_circle and input_manager.is_user_holding:  # inside the circle and is clicking
                return True
            else:
                return False
        # Check if the user is clicking on the pattern
        time_difference = t - self.starting_t
        relative_time_difference = time_difference / 120
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

        # Scale the points according to the supersampling factor
        start_scaled = self.starting_point * ss_factor
        end_scaled = self.ending_point * ss_factor

        # Draw circles around the starting and ending points
        pygame.draw.circle(sup_surface, self.color,
                           start_scaled,
                           self.thickness * ss_factor)
        pygame.draw.circle(sup_surface, self.color,
                           end_scaled,
                           self.thickness * ss_factor)

        # Draw the polygons computed by normal extrusion to draw the path from the starting to the ending point
        pygame.draw.polygon(sup_surface, self.color,
                            self.vertices_outer * ss_factor, 0)

        # Draw the inner polygons and circles to hollow out the pattern
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

        alpha = int(max(0, min(alpha, 255)))  # Clamp alpha between 0 and 255
        if alpha == 0:
            return t >= self.ending_t
        if alpha == 0:
            return t >= self.t
        if alpha < 255:
            frame = apply_alpha(self._prerendered_frame, alpha)
            win.blit(frame, (0, 0))
        else:
            win.blit(self._prerendered_frame, (0, 0))
        self.render_based_on_time(win, t)
        self.render_based_on_pressed(win, t)
        return False

    def render_based_on_time(self, win, t):
        """
        Draw tracing and approach circles
        """
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
        """
        Draw clicked circle and display score of the pattern
        """
        if not self.pressed:
            return
        time_difference = t - self.press_time
        relative_time_difference = time_difference / self.lifetime
        draw_clicked_circle(win, self.starting_point, relative_time_difference, self.thickness, self.stroke_width)
        font = pygame.font.Font(None, 25)
        score_text = font.render(str(int(self.score)), True, (255, 255, 255))

        if self.last_pressed is None:
            self.last_pressed = self.starting_point
        score_text_rect = score_text.get_rect(center=tuple(self.last_pressed))
        win.blit(score_text, score_text_rect)
        return abs(relative_time_difference) > 0.6

    def draw_tracing_circle(self, win, t, hollow=False):
        total_time = self.ending_t - self.starting_t
        p = (t - self.starting_t) / total_time
        p = max(0, min(p, 1))  # clamp
        pos = self._compute_coordinate(p)  # compute current position
        pos = pos.flatten()

        center_color = (0, 0, 0, 0) if hollow else (255, 255, 255, 150)
        circle = circle_surface((255, 255, 255, 255), center_color,
                                self.thickness, self.stroke_width, 1)

        # to prevent some weird runtime errors formed by weird floating point ops
        pos = np.clip(pos, -1e6, 1e6)
        rect = circle.get_rect(center=pos)
        win.blit(circle, rect)


class Line(SliderPattern):
    """
    Straight Line Pattern, PO = starting point, P1 = ending point
    """
    def __init__(self, radius, stroke_width, P0, P1, color, starting_t, ending_t, lifetime, approach_rate, length=-1):
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + self.stroke_width
        self.color = color
        self.P0 = P0
        self.P1 = P1

        # Compute the vector P0P1 to adjust length
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
        # Linear interpolation
        return (1 - t) * self.P0 + t * self.P1

    def _compute_normal(self):
        # Normal = -dx/dy
        direction = self.P1 - self.P0
        normal = np.array([-direction[1], direction[0]])
        return normal / np.linalg.norm(normal)  # normalize

    def _compute_vertices(self, width):
        # Simple rectangle polygon with normal extrusion
        vertex1 = self.P0 + width * self.normal
        vertex2 = self.P1 + width * self.normal
        vertex3 = self.P1 - width * self.normal
        vertex4 = self.P0 - width * self.normal
        return np.array([vertex1, vertex2, vertex3, vertex4])


class CubicBezier(SliderPattern):
    """
    A cubic Bezier spline curve pattern, P0 P1 P2 P3 are control points, P0 = starting point, P3 = ending point
    Since there is no analytical formula for a uniform-length/velocity interpolation across the curve,
    we save the points and t values and interpolate through the points
    """
    def __init__(self, radius, stroke_width, P0, P1, P2, P3, color, starting_t, ending_t, lifetime, approach_rate,
                 length=-1):
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + self.stroke_width
        self.color = color

        self.P0 = P0
        self.P1 = P1
        self.P2 = P2
        self.P3 = P3

        dist1 = np.linalg.norm(P1 - P0)
        dist2 = np.linalg.norm(P2 - P1)
        dist3 = np.linalg.norm(P3 - P2)
        self.N = int((dist1 + dist2 + dist3) / 2)  # number of sampling segments for bezier curve
        self.ts = np.linspace(0, 1, self.N)  # Save the t values for the points for interpolation

        self.points = self._compute_points()
        self.segment_lengths = np.linalg.norm(np.diff(self.points, axis=0), axis=1)
        self.length = np.sum(self.segment_lengths)  # total length
        if length > 0:
            vec1 = P1 - P0
            vec2 = P2 - P0
            vec3 = P3 - P0
            scale_ratio = length / self.length  # scale up/down the line to match the intended length
            self.P1 = self.P0 + vec1 * scale_ratio
            self.P2 = self.P0 + vec2 * scale_ratio
            self.P3 = self.P0 + vec3 * scale_ratio
            self.points = self._compute_points()  # recalculate the points
        self.subdivide_curve(accuracy=0.1)

        # Save accumulated lengths for interpolation
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
        """
        Rather than returning a simple analytic calculation of the bezier curve equation, we use interpolation to
        create the effect of it moving across the curve in a uniform speed
        :param t: A parameter or array of parameters from 0 to 1
        :return: a coordinate or a array of coordinates
        """
        target_length = t * self.length
        if target_length <= 0:
            return self._compute_point_helper(0.0)
        elif target_length >= self.length:
            return self._compute_point_helper(1.0)

        # search for the nearest point that is below the search length
        index = np.searchsorted(self.accumulated_lengths, target_length) - 1
        segment_start_length = self.accumulated_lengths[index]
        segment_length = self.segment_lengths[index]
        segment_progress = (target_length - segment_start_length) / segment_length
        t = self.ts[index] * segment_progress + self.ts[index + 1] * (1 - segment_progress)  # interpolate t value
        return self._compute_point_helper(t)

    def _compute_point_helper(self, t):
        """
        Unrolled formula for a cubic Bezier curve
        """
        return ((1 - t) ** 3 * self.P0.reshape((2, 1)) + 3 * (1 - t) ** 2 * t * self.P1.reshape((2, 1))
                + 3 * (1 - t) * t ** 2 * self.P2.reshape((2, 1)) + t ** 3 * self.P3.reshape((2, 1)))

    def _compute_points(self):
        """
        Compute the points for the curve py calculating the curve values across some values of t from 0 to 1
        :return: Array of points along the curve
        """
        t = np.linspace(0, 1, self.N)
        self.ts = t
        points = self._compute_point_helper(t)
        return np.transpose(points)

    def _compute_normal(self, t):
        """
        Computes the normal vector at value t, = -dx/dy
        :param t: A parameter or array of parameters from 0 to 1
        :return: Normal vector or array of normal vectors
        """
        dx_dt = 3 * (1 - t) ** 2 * (self.P1[0] - self.P0[0]) + 6 * (1 - t) * t * (
                self.P2[0] - self.P1[0]) + 3 * t ** 2 * (self.P3[0] - self.P2[0])
        dy_dt = 3 * (1 - t) ** 2 * (self.P1[1] - self.P0[1]) + 6 * (1 - t) * t * (
                self.P2[1] - self.P1[1]) + 3 * t ** 2 * (self.P3[1] - self.P2[1])
        magnitudes = np.sqrt(dx_dt ** 2 + dy_dt ** 2)
        return np.column_stack((-dy_dt / magnitudes, dx_dt / magnitudes))  # normalize

    def _compute_normals(self):
        """
        Computes the normals at the t values specified by self.ts
        :return: The array of normals
        """
        t = self.ts
        normals = self._compute_normal(t)
        return np.array(normals)

    def _compute_vertices(self, width):
        """
        Calculates vertices for normal extrusion
        :param width: How far to extrude the normals
        :return: Vertices
        """
        vertices1 = self.points + width * self.normals
        vertices2 = self.points - width * self.normals
        return np.concatenate((vertices1, vertices2[::-1]), axis=0)

    def _subdivide_curve(self, points, ts, accuracy):
        """
        Recursive function that add points in between the points until a certain level of accuracy is achieved
        :param points: Points on the curve
        :param ts: t values for the points
        :param accuracy: Desired accuracy, in pixels, and radians^-1
        :return: points and t values after subdivision
        """
        def normalize(vector):
            return vector / np.linalg.norm(vector)

        # First point and first t
        point1 = points[0]
        t1 = ts[0]
        new_points = [point1]
        new_ts = [t1]
        finished = True

        for point, t in zip(points[1:], ts[1:]):
            # Next point and next t
            point2 = point
            t2 = t

            mid_pt = (point1 + point2) / 2
            mid_t = (t1 + t2) / 2

            normal1 = normalize(self._compute_normal(t1).flatten())
            normal2 = normalize(self._compute_normal(t2).flatten())
            middle_normal = normalize(normal1 + normal2)
            actual_normal = normalize(self._compute_normal(mid_t).flatten())

            # Check the smoothness of the normals calculated
            dot_product_smooth = np.dot(normal1, normal2)
            angle_smooth = abs(np.arccos(np.clip(dot_product_smooth, -1, 1)))

            # Check the deviation between the interpolated normal and the actual normal
            dot_product_deviate = np.dot(middle_normal, actual_normal)
            angle_deviate = abs(np.arccos(np.clip(dot_product_deviate, -1, 1)))

            actual_point = np.asarray(self._compute_point_helper(mid_t).flatten())

            if (
                    np.linalg.norm(mid_pt - actual_point) > accuracy
                    or angle_smooth > accuracy / 2 / np.pi
                    or angle_deviate > accuracy / 2 / np.pi
            ):
                # Insert point between the points
                new_points.append(actual_point)
                new_ts.append(mid_t)
                finished = False

            new_points.append(point)
            new_ts.append(t)
            point1 = point
            t1 = t

        if not finished:  # continue the subdivision process
            new_points, new_ts = self._subdivide_curve(np.array(new_points), np.array(new_ts), accuracy)

        return np.asarray(new_points), np.asarray(new_ts)

    def subdivide_curve(self, accuracy):
        self.points, self.ts = self._subdivide_curve(self.points, self.ts, accuracy)


class Arc(SliderPattern):
    """
    An circular arc pattern, the program calculates the circle centre and starting/ending angles on the circle
    to compute the arc parametrically.
    """
    def __init__(self, radius, stroke_width, starting_point, ending_point, curve_radius, color, starting_t, ending_t,
                 lifetime, approach_rate, length=-1):
        """
        Curve Radius is the radius of the circle for the arc. The program will work out the parameters given
        the starting point, ending point and curve radius
        """
        self.radius = radius
        self.stroke_width = stroke_width
        self.thickness = radius + self.stroke_width
        self.color = color
        self.starting_point = starting_point
        self.ending_point = ending_point
        self.curve_radius = curve_radius

        self._compute_arc()  # compute the center of circle and starting/ending angle to parameterize the arc

        # Adjust curve length
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
        """
        Calculates the circle centre, starting and ending angle using geometry to parameterize the arc.
        The process involves the following steps:
        1. Calculate the base length between the starting and ending points.
        2. Determine the angle of the sector corresponding to the arc using the sine ratio.
        3. Find the midpoint between the starting and ending points.
        4. Compute the height of the isosceles triangle.
        5. Calculate the normal vector of the line connecting the points.
        6. Compute the circle center by stepping a length of height of isosceles triangle along the normal vector.
        7. Calculate the starting and ending angles using trigonometry.
        """

        # Step 1: Calculate base length
        vec = self.ending_point - self.starting_point
        base_length = np.linalg.norm(vec)

        # Step 2: Determine sector angle
        angle = 2 * np.arcsin(
            base_length / 2 / abs(self.curve_radius))  # angle of the sector/ corresponding to the arc P0P1

        # Step 3: Find midpoint
        mid_pt = (self.starting_point + self.ending_point) / 2

        # Step 4: Compute height of isosceles triangle
        height = self.curve_radius * np.cos(angle / 2)

        # Step 5: Calculate normal vector
        normal = np.array([-vec[1], vec[0]])
        normalized_normal = normal / np.linalg.norm(normal)

        # Step 7: Compute circle center
        self.centre = mid_pt + normalized_normal * height

        # Step 8: Calculate starting and ending angles
        vec0 = self.starting_point - self.centre
        vec1 = self.ending_point - self.centre
        self.start_angle = np.arctan2(vec0[1], vec0[0])
        self.end_angle = np.arctan2(vec1[1], vec1[0])

    def _compute_coordinate(self, t):
        """
        Calculates the point along the arc with parameter t ranging from 0-1
        Calculates the actual angle by linearly interpolating the starting and ending angles
        Then computes the point by the formula
        point = centre + r * (cos x, sin x)
        """
        t = np.asarray(t)

        angle = self.start_angle + (self.end_angle - self.start_angle) * t
        cis = np.array([np.cos(angle), np.sin(angle)]).T
        return cis * abs(self.curve_radius) + self.centre

    def _compute_points(self):
        """
        Compute the points for the curve py calculating the curve values across some values of t from 0 to 1
        :return: Array of points along the curve
        """
        t = np.linspace(0, 1, self.N)
        self.ts = t
        return self._compute_coordinate(t)

    def _compute_normals(self):
        """
        Computes the normal vector at value t, = -dx/dy
        :param t: A parameter or array of parameters from 0 to 1
        :return: Normal vector or array of normal vectors
        """
        t = self.ts
        angles = self.start_angle + (self.end_angle - self.start_angle) * t
        dx_dt = -np.sin(angles)
        dy_dt = np.cos(angles)
        return np.column_stack((-dy_dt, dx_dt))

    def _compute_vertices(self, width):
        """
        Calculates vertices for normal extrusion
        :param width: How far to extrude the normals
        :return: Vertices
        """
        vertices1 = self.points + width * self.normals
        vertices2 = self.points - width * self.normals
        return np.concatenate((vertices1, vertices2[::-1]), axis=0)

    def _subdivide_curve(self, points, ts, accuracy):
        """
        Recursive function that add points in between the points until a certain level of accuracy is achieved
        :param points: Points on the curve
        :param ts: t values for the points
        :param accuracy: Desired accuracy, in pixels
        :return: points and t values after subdivision
        """

        # First point and first t
        point1 = points[0]
        t1 = ts[0]
        new_points = [points[0]]
        new_ts = [ts[0]]
        finished = True

        for point, t in zip(points[1:], ts[1:]):
            # Next point and next t
            point2 = point
            t2 = t

            mid_pt = (point1 + point2) / 2
            mid_t = (t1 + t2) / 2

            actual_point = np.asarray(self._compute_coordinate(mid_t).flatten())

            if np.linalg.norm(mid_pt - actual_point) > accuracy:
                #  insert point between the points
                new_points.append(actual_point)
                new_ts.append(mid_t)
                finished = False

            new_points.append(point)
            new_ts.append(t)
            point1 = point
            t1 = t
        if not finished:  # Continue subdivision
            new_points, new_ts = list(self._subdivide_curve(np.array(new_points), np.array(new_ts), accuracy))
        return np.asarray(new_points), np.asarray(new_ts)

    def subdivide_curve(self, accuracy):
        self.points, self.ts = self._subdivide_curve(self.points, self.ts, accuracy)
