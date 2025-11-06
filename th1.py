# dino.py
# Simple Dinosaur Jump game using Pygame
# Controls:
#   Space - jump
#   R     - restart after game over
#   Esc   - exit

import pygame
import random
import sys

# ---------- Settings ----------
WIDTH, HEIGHT = 800, 300
FPS = 60

GROUND_Y = HEIGHT - 50
DINO_X = 50

# Dino physics
GRAVITY = 0.8
JUMP_VELOCITY = -14

# Obstacle settings
OBSTACLE_MIN_GAP = 400
OBSTACLE_MAX_GAP = 900
OBSTACLE_SPEED_START = 6
SPEED_INCREMENT_EVERY = 100  # increase speed every N score points
SPEED_INCREMENT_AMOUNT = 0.5

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DINO_COLOR = (30, 144, 255)
OBSTACLE_COLOR = (120, 120, 120)
GROUND_COLOR = (100, 100, 100)

# ---------- Initialize pygame ----------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Khủng long nhảy - Dino Jump")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)
big_font = pygame.font.SysFont(None, 48)

# ---------- Game objects ----------
class Dino:
    def __init__(self):
        self.x = DINO_X
        self.width = 44
        self.height = 44
        self.y = GROUND_Y - self.height
        self.vel_y = 0
        self.on_ground = True
        # For simple animation (leg up/down)
        self.step = 0

    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_VELOCITY
            self.on_ground = False

    def update(self):
        self.vel_y += GRAVITY
        self.y += self.vel_y

        if self.y >= GROUND_Y - self.height:
            self.y = GROUND_Y - self.height
            self.vel_y = 0
            self.on_ground = True

        # animation step
        if self.on_ground:
            self.step = (self.step + 1) % 20
        else:
            self.step = 0

    def draw(self, surf):
        # body
        pygame.draw.rect(surf, DINO_COLOR, (self.x, int(self.y), self.width, self.height), border_radius=6)
        # eye
        eye_x = self.x + int(self.width * 0.7)
        eye_y = int(self.y + self.height * 0.25)
        pygame.draw.circle(surf, WHITE, (eye_x, eye_y), 4)
        pygame.draw.circle(surf, BLACK, (eye_x, eye_y), 2)
        # legs (simple animation)
        if self.on_ground and self.step < 10:
            # left leg back, right leg front
            pygame.draw.rect(surf, DINO_COLOR, (self.x + 6, self.y + self.height, 10, 6))
            pygame.draw.rect(surf, DINO_COLOR, (self.x + 28, self.y + self.height, 12, 10))
        elif self.on_ground and self.step >= 10:
            pygame.draw.rect(surf, DINO_COLOR, (self.x + 6, self.y + self.height, 12, 10))
            pygame.draw.rect(surf, DINO_COLOR, (self.x + 28, self.y + self.height, 10, 6))
        else:
            # in air, legs tucked
            pygame.draw.rect(surf, DINO_COLOR, (self.x + 18, self.y + self.height - 6, 10, 6))

    def get_rect(self):
        return pygame.Rect(self.x, int(self.y), self.width, self.height)

class Obstacle:
    def __init__(self, x, kind="cactus", speed=OBSTACLE_SPEED_START):
        self.x = x
        self.speed = speed
        self.kind = kind
        if kind == "cactus":
            self.width = random.choice([20, 25, 30])
            self.height = random.choice([30, 40, 45])
        elif kind == "bird":
            self.width = 34
            self.height = 24
            # birds can have variable heights
            self.alt = random.choice([GROUND_Y - 100, GROUND_Y - 140])
        else:
            self.width = 30
            self.height = 40

        self.y = GROUND_Y - self.height if kind != "bird" else self.alt

        # for bird wing flap animation
        self.wing = 0

    def update(self):
        self.x -= self.speed
        if self.kind == "bird":
            self.wing = (self.wing + 1) % 20

    def draw(self, surf):
        if self.kind == "cactus":
            pygame.draw.rect(surf, OBSTACLE_COLOR, (int(self.x), self.y, self.width, self.height), border_radius=4)
            # small arms
            pygame.draw.rect(surf, OBSTACLE_COLOR, (int(self.x) - 3, self.y + 8, 6, 6))
            pygame.draw.rect(surf, OBSTACLE_COLOR, (int(self.x) + self.width - 3, self.y + 14, 6, 6))
        elif self.kind == "bird":
            # body
            body_y = self.y
            pygame.draw.rect(surf, OBSTACLE_COLOR, (int(self.x), body_y, self.width, self.height), border_radius=6)
            # wing (simple flap)
            if self.wing < 10:
                pygame.draw.polygon(surf, OBSTACLE_COLOR, [(self.x+6, body_y+6), (self.x-6, body_y+12), (self.x+6, body_y+18)])
            else:
                pygame.draw.polygon(surf, OBSTACLE_COLOR, [(self.x+28, body_y+6), (self.x+40, body_y+12), (self.x+28, body_y+18)])
        else:
            pygame.draw.rect(surf, OBSTACLE_COLOR, (int(self.x), self.y, self.width, self.height))

    def off_screen(self):
        return self.x + self.width < -50

    def get_rect(self):
        return pygame.Rect(int(self.x), self.y, self.width, self.height)

# ---------- Helper functions ----------
def draw_ground(surf, offset):
    # ground line
    pygame.draw.rect(surf, GROUND_COLOR, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    # simple moving ticks to give motion
    tick_w = 20
    for i in range(-1, WIDTH // tick_w + 2):
        x = (i * tick_w + offset) % (tick_w * 2)  # simple parallax
        pygame.draw.rect(surf, BLACK, (x, GROUND_Y + 30, 6, 6))

def show_text_center(surf, text, y, fontobj, color=BLACK):
    img = fontobj.render(text, True, color)
    rect = img.get_rect(center=(WIDTH // 2, y))
    surf.blit(img, rect)

# ---------- Game loop ----------
def run_game():
    dino = Dino()
    obstacles = []
    spawn_x = WIDTH + 100
    score = 0
    high_score = 0
    speed = OBSTACLE_SPEED_START
    ground_offset = 0
    game_over = False

    # Pre-spawn first obstacle after a short delay
    next_obstacle_at = WIDTH + random.randint(300, 700)

    while True:
        dt = clock.tick(FPS) / 1000.0  # seconds per frame (not heavily used)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if not game_over and event.key == pygame.K_SPACE:
                    dino.jump()
                if game_over and event.key == pygame.K_r:
                    # restart
                    return  # return to main to start a fresh game

        if not game_over:
            # update dino
            dino.update()

            # update obstacles
            for ob in obstacles:
                ob.speed = speed
                ob.update()

            # remove off-screen
            obstacles = [ob for ob in obstacles if not ob.off_screen()]

            # spawn new obstacle when needed
            if len(obstacles) == 0 or (obstacles[-1].x < next_obstacle_at):
                kind = random.choices(["cactus", "cactus", "cactus", "bird"], weights=[70, 70, 70, 30])[0]
                gap = random.randint(OBSTACLE_MIN_GAP, OBSTACLE_MAX_GAP)
                new_x = WIDTH + gap / 2
                obstacles.append(Obstacle(new_x, kind=kind, speed=speed))
                # set next spawn threshold
                next_obstacle_at = WIDTH + random.randint(350, 800)

            # collision check
            dino_rect = dino.get_rect()
            for ob in obstacles:
                if dino_rect.colliderect(ob.get_rect()):
                    game_over = True
                    if score > high_score:
                        high_score = score
                    break

            # scoring: increment by time, faster when speed higher
            score += 1  # each frame ~1, scale feels ok; you can tweak

            # speed increase with score
            speed = OBSTACLE_SPEED_START + (score // SPEED_INCREMENT_EVERY) * SPEED_INCREMENT_AMOUNT

            # ground offset for visual
            ground_offset -= speed
            ground_offset %= 40

        # ---------- Draw ----------
        screen.fill(WHITE)

        # draw dino and obstacles
        for ob in obstacles:
            ob.draw(screen)

        dino.draw(screen)

        # draw ground
        draw_ground(screen, ground_offset)

        # HUD / Score
        score_text = f"Score: {score}"
        score_img = font.render(score_text, True, BLACK)
        screen.blit(score_img, (WIDTH - 150, 10))
        hs_img = font.render(f"High: {high_score}", True, BLACK)
        screen.blit(hs_img, (WIDTH - 150, 32))

        if game_over:
            show_text_center(screen, "GAME OVER", HEIGHT // 2 - 10, big_font)
            show_text_center(screen, "Nhấn R để chơi lại  •  Esc để thoát", HEIGHT // 2 + 30, font)

        pygame.display.flip()

# ---------- Main ----------
def main():
    while True:
        run_game()

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
