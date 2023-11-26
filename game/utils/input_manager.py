import pygame


class InputManager:
    def __init__(self):
        self.mouse_state = pygame.mouse.get_pressed()
        self.prev_mouse_state = self.mouse_state
        self.mouse_pos = pygame.mouse.get_pos()
        self.prev_mouse_pos = self.mouse_pos
        self.keys = pygame.key.get_pressed()
        self.prev_keys = self.keys

    def update(self):
        self.prev_mouse_state = self.mouse_state
        self.mouse_state = pygame.mouse.get_pressed()
        self.prev_mouse_pos = self.mouse_pos
        self.mouse_pos = pygame.mouse.get_pos()
        self.prev_keys = self.keys
        self.keys = pygame.key.get_pressed()

    @property
    def is_mouse_clicked(self):
        return self.mouse_state[0] and not self.prev_mouse_state[0]

    @property
    def is_mouse_holding(self):
        return self.mouse_state[0]

    @property
    def is_user_inputted(self):
        return (
                self.mouse_state[0] and not self.prev_mouse_state[0] or
                self.keys[pygame.K_x] and not self.prev_keys[pygame.K_x] or
                self.keys[pygame.K_z] and not self.prev_keys[pygame.K_z]
        )

    @property
    def is_user_holding(self):
        return (
                self.mouse_state[0] or
                self.keys[pygame.K_x] or
                self.keys[pygame.K_z]
        )
