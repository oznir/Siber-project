import pygame
from settings import *

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_pos, owner, image, set_winner, source_id):
        super().__init__()
        self.image = pygame.transform.scale(image, (20, 20))
        self.rect = self.image.get_rect(center=(x, y))
        direction = pygame.Vector2(target_pos[0] - x, target_pos[1] - y)
        self.velocity = direction.normalize() * 10 if direction.length() != 0 else pygame.Vector2(0, 0)
        self.owner = owner
        self.set_winner = set_winner
        self.target_pos = target_pos
        self.source_id = int(source_id)

    def update(self):
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y

        # Remove if off screen
        if (
            self.rect.right < 0 or self.rect.left > SCREEN_WIDTH
            or self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT
        ):
            self.kill()

    def check_collision(self, player, player_id, platforms):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                self.kill()
                return

        # Only hit enemy (don't hit the player that shot the bullet)
        if self.rect.colliderect(player.rect) and self.source_id != player_id:
            self.kill()
            player.lives -= 1
            if player.lives <= 0:
                self.set_winner(player)
            player.alive = False
            player.respawn_timer = FPS * 2

    def get_data(self):
        return {
            "x": self.rect.x,
            "y": self.rect.y,
            "target": self.target_pos,
            "source_id": self.source_id
        }