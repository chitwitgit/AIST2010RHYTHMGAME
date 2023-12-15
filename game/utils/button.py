import pygame
from utils.input_manager import InputManager


class Button:
    def __init__(self, font, text, color, hover_color, selected_color, coords, pos):
        self.font = font
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.selected_color = selected_color
        self.coords = coords
        self.pos = pos
        self.selected = False
        self.input_manager = InputManager()

        self.surface = self.font.render(self.text, True, color)
        if self.pos == "center":
            label_rect = self.surface.get_rect(center=self.coords)
        elif self.pos == "topleft":
            label_rect = self.surface.get_rect(topleft=self.coords)
        elif self.pos == "topright":
            label_rect = self.surface.get_rect(topright=self.coords)
        elif self.pos == "bottomleft":
            label_rect = self.surface.get_rect(bottomleft=self.coords)
        else: # bottom right
            label_rect = self.surface.get_rect(bottomright=self.coords)
        self.rect = label_rect

    def set_text(self, text):
        self.text = text

    @property
    # Check if mouse is hovering over the button
    def hover(self):
        return self.rect.collidepoint(self.input_manager.mouse_pos)

    def render(self, surf):
        self.input_manager.update()
        if self.hover:
            color = self.hover_color
        elif self.selected:
            color = self.selected_color
        else:
            color = self.color
        self.surface = self.font.render(self.text, True, color)
        surf.blit(self.surface, self.rect)

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False

    # Detect clicks on the button
    @property
    def is_clicked(self):
        if self.rect.collidepoint(self.input_manager.mouse_pos) and self.input_manager.is_mouse_clicked:
            return True
        return False


class Label:
    def __init__(self, font, text, color, coords, pos):
        self.font = font
        self.color = color
        self.text = text
        self.coords = coords
        self.pos = pos

    def set_text(self, text):
        self.text = text

    def render(self, surf):
        label_surface = self.font.render(self.text, True, self.color)
        if self.pos == "center":
            label_rect = label_surface.get_rect(center=self.coords)
        elif self.pos == "topleft":
            label_rect = label_surface.get_rect(topleft=self.coords)
        elif self.pos == "topright":
            label_rect = label_surface.get_rect(topright=self.coords)
        elif self.pos == "bottomleft":
            label_rect = label_surface.get_rect(bottomleft=self.coords)
        elif self.pos == "bottomright":
            label_rect = label_surface.get_rect(bottomright=self.coords)

        surf.blit(label_surface, label_rect)