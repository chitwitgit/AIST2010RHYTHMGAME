import pygame


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

        self.surface = self.font.render(self.text, True, color)
        self.rect = self.surface.get_rect(center=self.coords)

    def set_text(self, text):
        self.text = text

    @property
    # Check if mouse is hovering over the button
    def hover(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def render(self, surf):
        if self.hover:
            color = self.hover_color
        elif self.selected:
            color = self.selected_color
        else:
            color = self.color

        label_surface = self.font.render(self.text, True, color)
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
        self.rect = label_rect
        surf.blit(label_surface, label_rect)

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False

    # Detect clicks on the button
    def is_clicked(self, input_manager):
        if self.rect.collidepoint(input_manager.mouse_pos) and input_manager.is_mouse_clicked:
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