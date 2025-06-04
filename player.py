# player.py
import pygame
from settings import *
import math

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path, controls):
        super().__init__()
        self.walk_frames = self.load_walk_frames(image_path)
        self.animation_index = 0
        self.animation_speed = 0.2  # lower = slower animation
        self.facing_right = True

        self.image = self.walk_frames[0]  # start with first frame
        self.rect = self.image.get_rect(topleft=(x, y))
        self.rect = self.image.get_rect(topleft=(x, y))

        self.can_dash = True
        self.dash_cooldown = 0  # frames
        self.dash_distance = 100
        self.dash_cooldown_max = FPS * 2  # 2 seconds
        self.controls = controls
        self.dash_key = controls.get("dash", None)



        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False
        self.jump_count = 0
        self.max_jumps = 2
        self.jump_key_held = False
        self.controls = controls

        self.lives = 3
        self.respawn_timer = 0
        self.alive = True
        self.spawn_point = pygame.Vector2(x, y)

        self.max_ammo = 3
        self.ammo = self.max_ammo
        self.ammo_cooldown = 180  # 3 seconds at 60 FPS
        self.ammo_timer = 0

    def load_walk_frames(self, image_path):
        import os
        folder = os.path.dirname(image_path)
        frames = []
        for i in range(4):  # number of frames you have
            path = f"{folder}/walk_{i}.png"
            frame = pygame.image.load(path).convert_alpha()
            frame = pygame.transform.scale(frame, (50, 75))  # adjust to match your game
            frames.append(frame)
        return frames

    def handle_input(self, keys):
        self.velocity.x = 0

        if self.dash_key and keys[self.dash_key] and self.can_dash:
            direction = 1 if self.facing_right else -1
            max_dash = self.dash_distance

            step = 5 * direction  # how much to test per check (small step)
            moved = 0

            for _ in range(0, abs(max_dash), abs(step)):
                test_rect = self.rect.move(step, 0)
                if any(test_rect.colliderect(obj.rect) for obj in self.collision_blocks):
                    break
                self.rect = test_rect
                moved += step

            if moved != 0:
                self.can_dash = False
                self.dash_cooldown = self.dash_cooldown_max

        if keys[self.controls["left"]]:
            self.velocity.x = -PLAYER_SPEED
        if keys[self.controls["right"]]:
            self.velocity.x = PLAYER_SPEED

        if keys[self.controls["jump"]]:
            if not self.jump_key_held and self.jump_count < self.max_jumps:
                self.velocity.y = JUMP_SPEED
                self.jump_count += 1
                self.jump_key_held = True
        else:
            self.jump_key_held = False

    def apply_gravity(self):
        self.velocity.y += GRAVITY
        if self.velocity.y > 10:
            self.velocity.y = 10

    def update(self, platforms, keys):
        self.collision_blocks = platforms

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        else:
            self.can_dash = True

        if not self.alive:
            self.respawn_timer -= 1
            self.image.set_alpha(0)  # ✅ hide before return
            if self.respawn_timer <= 0:
                self.respawn()
            return

        self.handle_input(keys)
        self.apply_gravity()
        self.rect.x += self.velocity.x
        self.collide_horizontal(platforms)
        self.rect.y += self.velocity.y
        self.collide_vertical(platforms)

        self.image.set_alpha(255)  # ✅ fully visible if alive

        if self.ammo < self.max_ammo:
            self.ammo_timer -= 1
            if self.ammo_timer <= 0:
                self.ammo += 1
                if self.ammo < self.max_ammo:
                    self.ammo_timer = self.ammo_cooldown

        if self.velocity.x != 0:
            self.animation_index += self.animation_speed
            if self.animation_index >= len(self.walk_frames):
                self.animation_index = 0
            frame = self.walk_frames[int(self.animation_index)]

            if self.velocity.x < 0:
                self.facing_right = False
                frame = pygame.transform.flip(frame, True, False)
            elif self.velocity.x > 0:
                self.facing_right = True

            self.image = frame
            self.rect = self.image.get_rect(center=self.rect.center)

        else:
            idle_frame = self.walk_frames[0]
            if not self.facing_right:
                idle_frame = pygame.transform.flip(idle_frame, True, False)

            self.image = idle_frame
            self.rect = self.image.get_rect(center=self.rect.center)

    def collide_horizontal(self, platforms):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.x > 0:
                    self.rect.right = platform.rect.left
                elif self.velocity.x < 0:
                    self.rect.left = platform.rect.right

    def collide_vertical(self, platforms):
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity.y = 0
                    self.on_ground = True
                    self.jump_count = 0  # ✅ Reset jump count on landing
                elif self.velocity.y < 0:
                    self.rect.top = platform.rect.bottom
                    self.velocity.y = 0

    def respawn(self):
        self.rect.topleft = self.spawn_point
        self.velocity = pygame.Vector2(0, 0)
        self.alive = True

    def try_shoot(self):
        if self.ammo > 0 and self.alive:
            self.ammo -= 1
            self.ammo_timer = self.ammo_cooldown
            return True
        return False

    def get_gun_angle(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - self.rect.centerx
        dy = mouse_y - self.rect.centery
        return -math.degrees(math.atan2(dy, dx))

    def get_data(self):
        return{
            "x": self.rect.x,
            "y": self.rect.y,
            "lives": self.lives,
            "ammo": self.ammo,
            "image": self.animation_index,
            "facing_right": self.facing_right,
            "gun_angle": self.get_gun_angle(),
            "alive": self.alive,
            "respawn_timer": self.respawn_timer,
            "can_dash": self.can_dash

        }
