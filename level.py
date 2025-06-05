# level.py
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.image.load("assets/platform.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (width, height))
        self.rect = self.image.get_rect(topleft=(x, y))

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.image.load("assets/wall.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (width, height))
        self.rect = self.image.get_rect(topleft=(x, y))




def create_level():
    platforms = pygame.sprite.Group()
    walls = pygame.sprite.Group()

    # --- Platforms (horizontal) ---
    platform_data = [
        (0, 680, 1280, 40),
        (80, 600, 180, 20),
        (1020, 600, 180, 20),
        (570, 460, 120, 20),
        (570, 340, 120, 20),
        (570, 220, 120, 20),
        (250, 480, 100, 20),
        (930, 480, 100, 20),
        (370, 360, 100, 20),
        (810, 360, 100, 20),
        (150, 240, 100, 20),
        (1030, 240, 100, 20),
        (590, 60, 100, 20),
    ]

    for x, y, w, h in platform_data:
        platforms.add(Platform(x, y, w, h))

    # --- Walls (vertical) ---
    wall_data = [
        # Middle towers
        (480, 400, 40, 120),
        (760, 400, 40, 120),
        (480, 280, 40, 120),
        (760, 280, 40, 120),
        (480, 160, 40, 120),
        (760, 160, 40, 120),

        # Map boundary walls (left/right)
        (0, 0, 20, SCREEN_HEIGHT),  # Left wall
        (SCREEN_WIDTH - 20, 0, 20, SCREEN_HEIGHT),  # Right wall

        #extra visual floor edge walls
        (0, SCREEN_HEIGHT - 60, 40, 60),
        (SCREEN_WIDTH - 40, SCREEN_HEIGHT - 60, 40, 60),
    ]

    for x, y, w, h in wall_data:
        walls.add(Wall(x, y, w, h))

    return platforms, walls