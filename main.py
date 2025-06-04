# main.py
import pygame
from settings import *
from level import create_level
from player import Player
from bullet import Bullet
import math

pygame.init()
pygame.mouse.set_visible(False)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Platform Duel")

heart_img = pygame.image.load("assets/heart.png").convert_alpha()
heart_img = pygame.transform.scale(heart_img, (20, 20))  # Resize if needed

bullet_img = pygame.image.load("assets/bullet_icon.png").convert_alpha()
bullet_img = pygame.transform.scale(bullet_img, (20, 20))

bullet_projectile = pygame.image.load("assets/bullet_projectile.png").convert_alpha()
bullet_projectile = pygame.transform.scale(bullet_projectile, (20, 20))

background = pygame.image.load("assets/jungle_bg.png").convert()
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))

cursor_img = pygame.image.load("assets/cursor.png").convert_alpha()
cursor_img = pygame.transform.scale(cursor_img, (48, 48))  # or (48, 48)

gun_img = pygame.image.load("assets/gun.png").convert_alpha()
gun_img = pygame.transform.scale(gun_img, (70, 28))

dash_icon_ready = pygame.transform.scale(pygame.image.load("assets/dash_ready.png").convert_alpha(), (40, 40))
dash_icon_cooldown = pygame.transform.scale(pygame.image.load("assets/dash_cooldown.png").convert_alpha(), (40, 40))

clock = pygame.time.Clock()

# Load map and platforms
platforms, walls = create_level()

# Create two players
player1 = Player(100, 100, "assets/player1/walk_0.png", {"left": pygame.K_a, "right": pygame.K_d, "jump": pygame.K_w, "dash": pygame.K_LSHIFT})
player1.name = "Player 1"
player2 = Player(800, 100, "assets/player2/walk_0_2.png", {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "jump": pygame.K_UP})
player2.name = "Player 2"
players = pygame.sprite.Group(player1, player2)

game_over = False
winner = None

# Bullet group
bullets = pygame.sprite.Group()

def set_winner(player):
    global game_over, winner
    game_over = True
    winner = player.name

def draw_end_menu(screen, winner):
    font = pygame.font.SysFont("arial", 50)
    button_font = pygame.font.SysFont("arial", 30)

    # Background
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # Winner text
    text = font.render(f"{winner} Wins!", True, (255, 255, 255))
    screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)))

    # Buttons
    mouse = pygame.mouse.get_pos()

    restart_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2, 200, 50)
    quit_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 70, 200, 50)

    # Draw buttons with hover effect
    for button, label in [(restart_button, "Restart"), (quit_button, "Quit")]:
        color = (180, 180, 180) if button.collidepoint(mouse) else (100, 100, 100)
        pygame.draw.rect(screen, color, button)
        text_surface = button_font.render(label, True, (255, 255, 255))
        screen.blit(text_surface, text_surface.get_rect(center=button.center))

    return restart_button, quit_button

def draw_dash_icon(screen, player, ready_img, cooldown_img):
    icon = ready_img if player.can_dash else cooldown_img
    x = player.rect.left - icon.get_width() +5  # 10 pixels to the left
    y = player.rect.centery - icon.get_height() // 2  # vertically centered
    screen.blit(icon, (x, y))


def draw_lives(surface, player, heart_img):
    if not player.alive:
        return  # Don't draw hearts when player is dead

    heart_width = heart_img.get_width()
    spacing = 4  # small gap between hearts

    total_width = player.lives * (heart_width + spacing) - spacing
    start_x = player.rect.centerx - total_width // 2
    y = player.rect.top - 30

    for i in range(player.lives):
        x = start_x + i * (heart_width + spacing)
        surface.blit(heart_img, (x, y))

def draw_gun(surface, player, image):
    if not player.alive:
        return

    # Player center & mouse
    player_center = player.rect.center
    mouse_x, mouse_y = pygame.mouse.get_pos()

    # Calculate angle
    dx = mouse_x - player_center[0]
    dy = mouse_y - player_center[1]
    angle = -math.degrees(math.atan2(dy, dx))

    # Rotate image
    rotated_gun = pygame.transform.rotate(image, angle)

    # Offset gun position slightly to sit on the shoulder
    offset_x = 20
    offset_y = 15
    gun_pos = (player_center[0] + offset_x, player_center[1] + offset_y)

    # Adjust for rotated image size
    gun_rect = rotated_gun.get_rect(center=gun_pos)
    surface.blit(rotated_gun, gun_rect.topleft)

def draw_ammo(surface, player, bullet_img):
    if not player.alive:
        return

    spacing = 4
    bullet_width = bullet_img.get_width()
    total_width = player.max_ammo * (bullet_width + spacing) - spacing
    start_x = player.rect.centerx - total_width // 2
    y = player.rect.top - 55  # above hearts

    for i in range(player.ammo):
        x = start_x + i * (bullet_width + spacing)
        surface.blit(bullet_img, (x, y))

    # Draw reload bar if not full
    if player.ammo < player.max_ammo:
        bar_width = 40
        bar_height = 5
        fill_ratio = 1 - (player.ammo_timer / player.ammo_cooldown)
        filled = int(bar_width * fill_ratio)

        bar_x = player.rect.centerx - bar_width // 2
        bar_y = player.rect.bottom + 10

        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (0, 200, 0), (bar_x, bar_y, filled, bar_height))


def draw_game_over(screen, winner):
    font = pygame.font.SysFont("arial", 50)
    small_font = pygame.font.SysFont("arial", 30)

    win_text = font.render(f"{winner} Wins!", True, (255, 0, 0))
    restart_text = small_font.render("Press R to Restart", True, (255, 255, 255))

    win_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))

    screen.blit(win_text, win_rect)
    screen.blit(restart_text, restart_rect)

# Game loop
running = True
while running:
    clock.tick(FPS)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if not game_over:
            # Shoot on left mouse click
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if player1.try_shoot():
                    mouse_pos = pygame.mouse.get_pos()
                    bullet = Bullet(player1.rect.centerx, player1.rect.centery, mouse_pos, player1, bullet_projectile, set_winner)
                    bullets.add(bullet)
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                # Reset game
                player1.lives = 3
                player2.lives = 3
                player1.respawn()
                player2.respawn()
                player1.rect.topleft = (100, 100)
                player2.rect.topleft = (800, 100)
                bullets.empty()
                game_over = False
                winner = None

    # Update only if game is active
    if not game_over:
        players.update(platforms.sprites() + walls.sprites(), keys)
        bullets.update()
        for bullet in bullets:
            bullet.check_collision(players, platforms.sprites() + walls.sprites())

    # Draw
    screen.blit(background, (0, 0))
    platforms.draw(screen)
    walls.draw(screen)
    bullets.draw(screen)
    players.draw(screen)

    draw_lives(screen, player1, heart_img)
    draw_lives(screen, player2, heart_img)
    draw_ammo(screen, player1, bullet_img)
    draw_ammo(screen, player2, bullet_img)
    draw_gun(screen, player1, gun_img)
    draw_dash_icon(screen, player1, dash_icon_ready, dash_icon_cooldown)
    draw_dash_icon(screen, player2, dash_icon_ready, dash_icon_cooldown)

    # Draw cursor
    mouse_x, mouse_y = pygame.mouse.get_pos()
    screen.blit(cursor_img, (mouse_x - cursor_img.get_width() // 2, mouse_y - cursor_img.get_height() // 2))

    # Draw game over screen if needed
    if game_over:
        restart_btn, quit_btn = draw_end_menu(screen, winner)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if restart_btn.collidepoint(pygame.mouse.get_pos()):
                    # Reset game
                    player1.lives = 3
                    player2.lives = 3
                    player1.respawn()
                    player2.respawn()
                    player1.rect.topleft = (100, 100)
                    player2.rect.topleft = (800, 100)
                    bullets.empty()
                    game_over = False
                    winner = None
                elif quit_btn.collidepoint(pygame.mouse.get_pos()):
                    running = False

    pygame.display.flip()

pygame.quit()