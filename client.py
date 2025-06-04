import pygame
import pickle
import settings
from level import create_level
from player import Player
from bullet import Bullet
import socket
import protocol
import math

class GameClient:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.pro = protocol.Protocol(self.client_socket)
        self.running = True
        self.game_over = False
        self.winner = None
        self.load_assets()
        self.setup_game()
        self.enemy_frame = 0
        self.enemy_bullets_data = []




    def connect_to_server(self):
        try:
            self.client_socket.connect((settings.SERVER_IP, settings.PORT))
            self.player_id = self.pro.get_data().decode()
            print(f"Connected to server as Player {self.player_id}")

            print("Waiting for a second player...")
            start_signal = self.pro.get_data().decode()
            if start_signal != "start":
                print("Unexpected server response. Exiting.")
                self.running = False
                return
            else:
                print("Both players connected. Game starting!")
                self.connected = True

            pygame.init()
            pygame.mouse.set_visible(False)
            self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

            self.clock = pygame.time.Clock()
            pygame.display.set_caption(f"Platform Duel-{self.player_id}")

            if self.player_id == "0":
                self.local_player = Player(150, 100, "assets/player1/walk_0.png",
                                           {"left": pygame.K_a, "right": pygame.K_d, "jump": pygame.K_w,
                                            "dash": pygame.K_LSHIFT})
                self.local_player.name = "Player 1"
                self.enemy_player = Player(1050, 100, "assets/player2/walk_0.png",
                                           {"left": pygame.K_a, "right": pygame.K_d, "jump": pygame.K_w,
                                            "dash": pygame.K_LSHIFT})
                self.enemy_player.name = "Player 2"
                self.enemy_player.gun_angle = 0
            elif self.player_id == "1":
                self.local_player = Player(1050, 100, "assets/player2/walk_0.png",
                                           {"left": pygame.K_a, "right": pygame.K_d, "jump": pygame.K_w,
                                            "dash": pygame.K_LSHIFT})
                self.local_player.name = "Player 2"
                self.enemy_player = Player(150, 100, "assets/player1/walk_0.png",
                                           {"left": pygame.K_a, "right": pygame.K_d, "jump": pygame.K_w,
                                            "dash": pygame.K_LSHIFT})
                self.enemy_player.name = "Player 1"
                self.enemy_player.gun_angle = 0


        except Exception as e:
            print(f"Failed to connect to server: {e}")
            self.running = False

    def send_and_receive_data(self):
        player_data = self.local_player.get_data()
        bullet_data = [b.get_data() for b in self.bullets]
        player_data["bullets"] = bullet_data

        # 🔁 Send game over info if it happened
        if self.game_over:
            player_data["game_over"] = self.winner

        self.pro.send_data(pickle.dumps(player_data))

        # Receive enemy data as a flat dictionary
        enemy_data = pickle.loads(self.pro.get_data())

        if enemy_data == "quit":
            print("Opponent quit. Exiting game.")
            pygame.quit()
            exit()

        if len(enemy_data) != 0:
            self.enemy_player.rect.y = enemy_data["y"]
            self.enemy_player.rect.x = enemy_data["x"]
            self.enemy_player.lives = enemy_data["lives"]
            self.enemy_player.ammo = enemy_data["ammo"]
            self.enemy_frame = enemy_data["image"]
            self.enemy_player.facing_right = enemy_data["facing_right"]
            self.enemy_player.gun_angle = enemy_data["gun_angle"]
            self.enemy_bullets_data = enemy_data.get("bullets", [])
            self.enemy_player.can_dash = enemy_data.get("can_dash", True)
            self.enemy_player.alive = enemy_data.get("alive", True)
            self.enemy_player.respawn_timer = enemy_data.get("respawn_timer", 0)
            if "game_over" in enemy_data and not self.game_over:
                self.winner = enemy_data["game_over"]
                self.game_over = True



    def load_assets(self):
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        pygame.display.set_caption("Platform Duel")
        self.heart_img = pygame.transform.scale(pygame.image.load("assets/heart.png").convert_alpha(), (20, 20))
        self.bullet_img = pygame.transform.scale(pygame.image.load("assets/bullet_icon.png").convert_alpha(), (20, 20))
        self.bullet_projectile = pygame.transform.scale(pygame.image.load("assets/bullet_projectile.png").convert_alpha(), (20, 20))
        self.background = pygame.transform.scale(pygame.image.load("assets/jungle_bg.png").convert(), (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        self.cursor_img = pygame.transform.scale(pygame.image.load("assets/cursor.png").convert_alpha(), (48, 48))
        self.gun_img = pygame.transform.scale(pygame.image.load("assets/gun.png").convert_alpha(), (70, 28))
        self.dash_icon_ready = pygame.transform.scale(pygame.image.load("assets/dash_ready.png").convert_alpha(), (40, 40))
        self.dash_icon_cooldown = pygame.transform.scale(pygame.image.load("assets/dash_cooldown.png").convert_alpha(), (40, 40))

    def setup_game(self):
        self.platforms, self.walls = create_level()
        self.bullets = pygame.sprite.Group()

    def set_winner(self, player):
        self.game_over = True
        self.winner = player.name

    def handle_events(self):
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if not self.game_over:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.local_player.try_shoot():
                        mouse_pos = pygame.mouse.get_pos()
                        bullet = Bullet(self.local_player.rect.centerx, self.local_player.rect.centery, mouse_pos, self.local_player, self.bullet_projectile, self.set_winner, self.player_id)
                        self.bullets.add(bullet)
            else:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.reset_game()

    def reset_game(self):
        self.local_player.lives = 3
        self.local_player.respawn()
        self.local_player.rect.topleft = (150, 100)
        self.bullets.empty()
        self.game_over = False
        self.winner = None

    def update(self):
        if not self.game_over:
            keys = pygame.key.get_pressed()

            # Only update local player if they're alive
            if self.local_player.alive:
                self.local_player.update(self.platforms.sprites() + self.walls.sprites(), keys)

            self.bullets.update()

            # Check collisions from local bullets to local player (if accidentally shot)
            for bullet in self.bullets:
                bullet.check_collision(self.local_player, int(self.player_id),
                                       self.platforms.sprites() + self.walls.sprites())

            # Check collisions from enemy bullets
            for b_data in self.enemy_bullets_data:
                bullet_rect = pygame.Rect(b_data["x"], b_data["y"], 20, 20)
                if bullet_rect.colliderect(self.local_player.rect) and self.local_player.alive:
                    self.local_player.lives -= 1
                    if self.local_player.lives <= 0:
                        self.set_winner(self.enemy_player)
                    self.local_player.alive = False
                    self.local_player.respawn_timer = settings.FPS * 2

            # Handle local player respawn
            if not self.local_player.alive:
                self.local_player.respawn_timer -= 1
                if self.local_player.respawn_timer <= 0:
                    self.local_player.respawn()

            # Handle enemy player respawn
            if not self.enemy_player.alive:
                self.enemy_player.respawn_timer -= 1
                if self.enemy_player.respawn_timer <= 0:
                    self.enemy_player.respawn()


    def sync_enemy_bullets(self, bullet_data_list):
        self.enemy_bullets = pygame.sprite.Group()
        for bd in bullet_data_list:
            bullet = Bullet(
                bd["x"], bd["y"], bd["target"],
                self.enemy_player,  # enemy is the shooter
                self.bullet_projectile,
                self.set_winner
            )
            self.enemy_bullets.add(bullet)

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.platforms.draw(self.screen)
        self.walls.draw(self.screen)
        self.bullets.draw(self.screen)
        for b_data in self.enemy_bullets_data:
            self.screen.blit(self.bullet_projectile, (b_data["x"], b_data["y"]))
        frame = self.enemy_player.walk_frames[int(self.enemy_frame)]
        if not self.enemy_player.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        self.enemy_player.image = frame


        if self.local_player.alive:
            self.screen.blit(self.local_player.image, (self.local_player.rect.x, self.local_player.rect.y))
            self.draw_gun(self.screen, self.local_player, self.gun_img, True)
            self.draw_lives(self.local_player)
            self.draw_ammo(self.local_player)
            self.draw_dash_icon(self.local_player)

        if self.enemy_player.alive:
            self.screen.blit(self.enemy_player.image, (self.enemy_player.rect.x, self.enemy_player.rect.y))
            self.draw_gun(self.screen, self.enemy_player, self.gun_img, False)
            self.draw_lives(self.enemy_player)
            self.draw_ammo(self.enemy_player)
            self.draw_dash_icon(self.enemy_player)
        self.draw_cursor()

        if self.game_over:
            self.draw_game_over()

        pygame.display.flip()

    def draw_cursor(self):
        x, y = pygame.mouse.get_pos()
        self.screen.blit(self.cursor_img, (x - self.cursor_img.get_width() // 2, y - self.cursor_img.get_height() // 2))

    def draw_lives(self, player):
        if not player.alive:
            return
        width = self.heart_img.get_width()
        spacing = 4
        total = player.lives * (width + spacing) - spacing
        start_x = player.rect.centerx - total // 2
        y = player.rect.top - 30
        for i in range(player.lives):
            self.screen.blit(self.heart_img, (start_x + i * (width + spacing), y))

    def draw_ammo(self, player):
        if not player.alive:
            return
        spacing = 4
        width = self.bullet_img.get_width()
        total = player.max_ammo * (width + spacing) - spacing
        start_x = player.rect.centerx - total // 2
        y = player.rect.top - 55
        for i in range(player.ammo):
            self.screen.blit(self.bullet_img, (start_x + i * (width + spacing), y))
        if player.ammo < player.max_ammo:
            bar_width = 40
            bar_height = 5
            fill = int(bar_width * (1 - (player.ammo_timer / player.ammo_cooldown)))
            bar_x = player.rect.centerx - bar_width // 2
            bar_y = player.rect.bottom + 10
            pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(self.screen, (0, 200, 0), (bar_x, bar_y, fill, bar_height))

    def draw_dash_icon(self, player):
        icon = self.dash_icon_ready if player.can_dash else self.dash_icon_cooldown
        x = player.rect.left - icon.get_width() + 5
        y = player.rect.centery - icon.get_height() // 2
        self.screen.blit(icon, (x, y))

    def draw_game_over(self):
        font = pygame.font.SysFont("arial", 50)
        small_font = pygame.font.SysFont("arial", 30)

        win_text = font.render(f"{self.winner} Wins!", True, (255, 0, 0))
        win_rect = win_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(win_text, win_rect)

        # Button dimensions
        button_width, button_height = 200, 50
        spacing = 30
        center_x = settings.SCREEN_WIDTH // 2

        # Quit Button
        quit_rect = pygame.Rect(center_x - button_width // 2, settings.SCREEN_HEIGHT // 2 + button_height + spacing,
                                button_width, button_height)
        pygame.draw.rect(self.screen, (200, 0, 0), quit_rect)
        quit_text = small_font.render("Quit", True, (0, 0, 0))
        quit_text_rect = quit_text.get_rect(center=quit_rect.center)
        self.screen.blit(quit_text, quit_text_rect)

        # Handle clicks
        mouse_pos = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()[0]

        if click:
            if quit_rect.collidepoint(mouse_pos):
                pygame.time.delay(200)
                self.pro.send_data("quit".encode())  # Notify server
                pygame.quit()
                exit()

    def draw_gun(self, surface, player, image, is_local):
        if not player.alive:
            return

        player_center = player.rect.center
        angle = player.get_gun_angle() if is_local else player.gun_angle

        rotated_gun = pygame.transform.rotate(image, angle)

        offset_x = 20 if player.facing_right else -20
        offset_y = 15
        gun_pos = (player_center[0] + offset_x, player_center[1] + offset_y)

        gun_rect = rotated_gun.get_rect(center=gun_pos)
        surface.blit(rotated_gun, gun_rect.topleft)

    def run(self):
        self.connect_to_server()
        while self.running:
            self.clock.tick(settings.FPS)
            self.handle_events()
            self.send_and_receive_data()
            self.update()
            self.draw()
        pygame.quit()

if __name__ == '__main__':
    GameClient().run()
