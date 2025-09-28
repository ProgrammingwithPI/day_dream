import pygame
import sys
import math
import random

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wave-Based Enemy Shooting Game")
pygame.mixer.init()
shoot_sound = pygame.mixer.Sound("shoot.wav")
death_sound = pygame.mixer.Sound("death.wav")

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
damage_adder=0 
clock = pygame.time.Clock()
FPS = 60
e_size_mod=1
player_x, player_y = WIDTH // 2, HEIGHT // 2
player_radius = 15
player_speed = 5
size_b=8
b_speed=7
player_lives = 25

# Weapon availability
laser = False
shotgun = True
exploding_b = True

SAFE_SPAWN_DISTANCE = 150
stars_pos = [[random.randint(0, WIDTH), random.randint(0, HEIGHT)] for _ in range(100)]
original_width, original_height = 31, 53

# Scaling factor
scale_factor = 5
scaled_width = original_width * scale_factor
scaled_height = original_height * scale_factor

sacrifice_images = []
for i in range(1, 10):
    img = pygame.image.load(f"{i}.png").convert_alpha()
    img = pygame.transform.scale(img, (scaled_width, scaled_height))
    sacrifice_images.append(img)
def draw_laser_and_hit(cursorx, cursory, playerx, playery):
    global score
    pygame.draw.line(screen, WHITE, (playerx, playery), (cursorx, cursory), 15)
    enemies_to_remove = []
    circle_enemies_to_remove = []
    octagon_enemies_to_remove = []

    for enemy in enemies:
        enemy_rect = enemy.get_hitbox()
        if enemy_rect.clipline((playerx, playery, cursorx, cursory)):
            enemies_to_remove.append(enemy)

    for c_enemy in circle_enemies:
        c_enemy_rect = pygame.Rect(c_enemy.x - c_enemy.radius, c_enemy.y - c_enemy.radius,
                                   c_enemy.radius * 2, c_enemy.radius * 2)
        if c_enemy_rect.clipline((playerx, playery, cursorx, cursory)):
            circle_enemies_to_remove.append(c_enemy)

    for o_enemy in octagon_enemies:
        o_enemy_rect = pygame.Rect(o_enemy.x - o_enemy.radius, o_enemy.y - o_enemy.radius,
                                   o_enemy.radius * 2, o_enemy.radius * 2)
        if o_enemy_rect.clipline((playerx, playery, cursorx, cursory)):
            octagon_enemies_to_remove.append(o_enemy)

    for e in enemies_to_remove:
        death_sound.play()
        if e in enemies:
            enemies.remove(e)
            score += 1
    for ce in circle_enemies_to_remove:
        death_sound.play()
        if ce in circle_enemies:
            circle_enemies.remove(ce)
            score += 1
    for oe in octagon_enemies_to_remove:
        death_sound.play()
        if oe in octagon_enemies:
            octagon_enemies.remove(oe)
            score += 2

def show_sacrifice_screen(level):
    """
    Pauses the game, shows 'What do you sacrifice?' and 3 images based on level.
    For level 3, only 2 choices are available and shows a special text.
    Returns: 1, 2, or 3 depending on key pressed.
    """
    screen.fill(BLACK)

    title_font = pygame.font.SysFont(None, 72)
    text = title_font.render("What do you sacrifice?", True, WHITE)
    screen.blit(text, (WIDTH//2 - text.get_width()//2, 50))

    # Determine which images to show
    start_index = (level - 1) * 3
    end_index = min(start_index + 3, len(sacrifice_images))
    selected_imgs = sacrifice_images[start_index:end_index]

    # Level 3 has only 2 choices
    if level == 3:
        selected_imgs = selected_imgs[:2]

    # Draw images spaced evenly left-to-right
    spacing = 200
    total_width = len(selected_imgs) * 31 + (len(selected_imgs) - 1) * spacing
    x_start = (WIDTH//2 - total_width//2)-30
    y_pos = HEIGHT//2 - 53//2
    for i, img in enumerate(selected_imgs):
        screen.blit(img, (x_start + i * (31 + spacing), y_pos))

    # Special text for level 3
    if level == 3:
        info_font = pygame.font.SysFont(None, 18)
        info_text = info_font.render("Sacrifice exploding bullets and shotgun for laser? Press 1 to keep 2 to sacrifice.", True, WHITE)
        screen.blit(info_text, (WIDTH//2 - info_text.get_width()//2, y_pos - 40))

    pygame.display.flip()

    chosen = None
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1 and len(selected_imgs) >= 1:
                    chosen = 1
                    waiting = False
                elif event.key == pygame.K_2 and len(selected_imgs) >= 2:
                    chosen = 2
                    waiting = False
                elif event.key == pygame.K_3 and len(selected_imgs) >= 3:
                    chosen = 3
                    waiting = False
        pygame.time.delay(10)

    return chosen


def get_safe_spawn_position(size):
    while True:
        x = random.randint(0, WIDTH - size)
        y = random.randint(0, HEIGHT - size)
        dx = x - player_x
        dy = y - player_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist >= SAFE_SPAWN_DISTANCE:
            return x, y

class EnemyBullet:
    def __init__(self, x, y, bullet_speed, size, seeking=False):
        self.bullet_speed = bullet_speed
        self.x = x
        self.y = y
        self.size = size
        self.color = RED
        self.seeking = seeking
        self.range_left = 1000 if seeking else None
        self.update_direction()

    def update_direction(self):
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist != 0:
            self.dx = (dx / dist) * self.bullet_speed
            self.dy = (dy / dist) * self.bullet_speed
        else:
            self.dx, self.dy = 0, 0

    def move(self):
        global player_lives
        if self.seeking:
            self.update_direction()
            self.range_left -= 2
            if self.range_left <= 0:
                return True

        self.x += self.dx
        self.y += self.dy

        player_rect = pygame.Rect(player_x - player_radius, player_y - player_radius, player_radius * 2, player_radius * 2)
        bullet_rect = pygame.Rect(self.x, self.y, self.size, self.size)
        if player_rect.colliderect(bullet_rect):
            player_lives -= 1+damage_adder
            return True
        if self.x >= WIDTH or self.x <= 0 or self.y <= 0 or self.y >= HEIGHT:
            return True
        return False

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))

class Bullet:
    def __init__(self, x, y, target_x, target_y):
        self.x = x
        self.y = y
        self.radius = 5
        self.color = WHITE
        angle = math.atan2(target_y - y, target_x - x)
        self.speed = 10
        self.dx = math.cos(angle) * self.speed
        self.dy = math.sin(angle) * self.speed

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

class ExplodingBullet(Bullet):
    def __init__(self, x, y, target_x, target_y):
        super().__init__(x, y, target_x, target_y)
        self.color = (255, 165, 0)

    def on_hit(self, hit_enemy):
        explosion_x = hit_enemy.x
        explosion_y = hit_enemy.y
        for i in range(1, 3):
            pygame.draw.circle(screen, (255, 165, 0), (int(explosion_x), int(explosion_y)), 20 * i)
            pygame.display.update()
        enemies_to_remove = []
        for enemy in enemies:
            dis = math.sqrt(((enemy.x - explosion_x) ** 2) + ((enemy.y - explosion_y) ** 2))
            if dis <= 60:
                enemies_to_remove.append(enemy)
        for e in enemies_to_remove:
            if e in enemies:
                enemies.remove(e)

class Enemy:
    def __init__(self, speed=2, damage=1, is_triangle=False):
        self.size = 40*e_size_mod
        self.x, self.y = get_safe_spawn_position(self.size)
        self.color = RED
        self.speed = speed
        self.damage = damage+damage_adder
        self.is_triangle = is_triangle

    def move_toward_player(self, player_x, player_y):
        dx = player_x - (self.x + self.size / 2)
        dy = player_y - (self.y + self.size / 2)
        distance = math.sqrt(dx * dx + dy * dy)
        if distance != 0:
            self.x += (dx / distance) * self.speed
            self.y += (dy / distance) * self.speed

    def get_hitbox(self):
        if self.is_triangle:
            return pygame.Rect(self.x - self.size // 2, self.y - self.size, self.size, self.size)
        else:
            return pygame.Rect(self.x, self.y, self.size, self.size)

    def draw(self, screen):
        if self.is_triangle:
            points = [(self.x, self.y), (self.x + self.size // 2, self.y - self.size), (self.x - self.size // 2, self.y - self.size)]
            pygame.draw.polygon(screen, self.color, points)
        else:
            pygame.draw.rect(screen, self.color, (int(self.x), int(self.y), self.size, self.size))

class CircleEnemy:
    def __init__(self):
        self.radius = 20*e_size_mod
        self.x, self.y = get_safe_spawn_position(self.radius * 2)
        self.color = RED
        self.speed = 2
        self.shoot_timer = 0
        self.shoot_delay = 90  

    def move_toward_player(self, player_x, player_y):
        dx = player_x - self.x
        dy = player_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        if distance != 0:
            self.x += (dx / distance) * self.speed
            self.y += (dy / distance) * self.speed

    def update(self):
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_delay:
            enemy_bullets.append(EnemyBullet(self.x, self.y, b_speed, size_b-1))
            self.shoot_timer = 0

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

class OctagonEnemy:
    def __init__(self):
        self.radius = 25*e_size_mod
        self.x, self.y = get_safe_spawn_position(self.radius * 2)
        self.color = (255, 100, 100)
        self.speed = 1.5
        self.shoot_timer = 0
        self.shoot_delay = 120

    def move_toward_player(self, player_x, player_y):
        dx = player_x - self.x
        dy = player_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        if distance != 0:
            self.x += (dx / distance) * self.speed
            self.y += (dy / distance) * self.speed

    def update(self):
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_delay:
            enemy_bullets.append(EnemyBullet(self.x, self.y, b_speed-2, size_b, seeking=True))
            self.shoot_timer = 0

    def draw(self, screen):
        points = []
        for i in range(8):
            angle = math.pi / 4 * i
            px = self.x + self.radius * math.cos(angle)
            py = self.y + self.radius * math.sin(angle)
            points.append((px, py))
        pygame.draw.polygon(screen, self.color, points)
def show_enemy_intro(enemy_type, duration_ms=2000):
    """
    Draws a simple 'NEW FOE!' pause screen with a big preview and 1-2 bullets.
    duration_ms: how long to pause (milliseconds)
    """
    screen.fill(BLACK)
    title_font = pygame.font.SysFont(None, 72)
    text = title_font.render("NEW FOE!", True, WHITE)
    screen.blit(text, (WIDTH//2 - text.get_width()//2, 50))

    # preview + description
    if enemy_type == "triangle":
        pts = [(WIDTH//2, HEIGHT//2), (WIDTH//2+60, HEIGHT//2-120), (WIDTH//2-60, HEIGHT//2-120)]
        pygame.draw.polygon(screen, RED, pts)
        desc = ["Fast and dangerous", "Deals heavy damage"]
    elif enemy_type == "circle":
        pygame.draw.circle(screen, RED, (WIDTH//2, HEIGHT//2), 70)
        desc = ["Shoots bullets periodically"]
    elif enemy_type == "octagon":
        pts = []
        for i in range(8):
            angle = math.pi / 4 * i
            px = WIDTH//2 + 80 * math.cos(angle)
            py = HEIGHT//2 + 80 * math.sin(angle)
            pts.append((px, py))
        pygame.draw.polygon(screen, (255, 100, 100), pts)
        desc = ["Shoots homing bullets", "Slower but deadly"]
    else:
        return

    bullet_font = pygame.font.SysFont(None, 36)
    for i, line in enumerate(desc):
        bullet_text = bullet_font.render(f"• {line}", True, WHITE)
        screen.blit(bullet_text, (WIDTH//2 - bullet_text.get_width()//2, HEIGHT//2 + 120 + i*36))

    pygame.display.flip()
    pygame.time.wait(duration_ms)

bullets = []
enemy_bullets = []
enemies = [Enemy() for _ in range(5)]
circle_enemies = []
octagon_enemies = []
score = 0
wave = 1

font = pygame.font.SysFont(None, 36)
current_weapons = 0
shotgun_cooldown = 0  # added for shotgun cooldown

running = True
while running:
    screen.fill(BLACK)
    for star in stars_pos:
        pygame.draw.circle(screen, WHITE, (star[0], star[1]), 1)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        player_y -= player_speed
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        player_y += player_speed
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        player_x -= player_speed
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player_x += player_speed

    player_x = max(player_radius, min(WIDTH - player_radius, player_x))
    player_y = max(player_radius, min(HEIGHT - player_radius, player_y))

    mouse_x, mouse_y = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if current_weapons == 0:  # Normal bullet
                bullets.append(Bullet(player_x, player_y, mouse_x, mouse_y))
                shoot_sound.play()
            elif current_weapons == 1 and exploding_b:  # Exploding bullet
                bullets.append(ExplodingBullet(player_x, player_y, mouse_x, mouse_y))
                shoot_sound.play()
            elif current_weapons == 2 and shotgun:  # Shotgun
                if shotgun_cooldown == 0:
                    bullets.append(Bullet(player_x, player_y, mouse_x, mouse_y))
                    bullets.append(Bullet(player_x, player_y, mouse_x, mouse_y - 60))
                    bullets.append(Bullet(player_x, player_y, mouse_x, mouse_y + 60))
                    shoot_sound.play()
                    shotgun_cooldown = 20  # frames cooldown
            elif current_weapons == 3 and laser:
                draw_laser_and_hit(mouse_x, mouse_y, player_x, player_y)
                shoot_sound.play()
            elif laser:
                draw_laser_and_hit(mouse_x, mouse_y, player_x, player_y)
                shoot_sound.play()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Determine max weapon index based on unlocked weapons
                if laser and not exploding_b and not shotgun:
                    # Only normal (0) and laser (3) are available
                    if current_weapons == 0:
                        current_weapons = 3
                    else:
                        current_weapons = 0
                else:
                    # Normal cycling: 0->1->2->0 if laser not available
                    max_weapon = 3 if laser else 2
                    current_weapons += 1
                    if current_weapons > max_weapon:
                        current_weapons = 0


    if shotgun_cooldown > 0:
        shotgun_cooldown -= 1
    enemies_to_remove = []
    circle_enemies_to_remove = []
    octagon_enemies_to_remove = []
    bullets_to_remove = []

    # Bullet updates
    for bullet in bullets:
        bullet.move()
        bullet.draw(screen)
        if bullet.x < 0 or bullet.x > WIDTH or bullet.y < 0 or bullet.y > HEIGHT:
            bullets_to_remove.append(bullet)
            continue
        for enemy in enemies:
            if (enemy.x < bullet.x < enemy.x + enemy.size) and (enemy.y < bullet.y < enemy.y + enemy.size):
                if isinstance(bullet, ExplodingBullet):
                    bullet.on_hit(enemy)
                bullets_to_remove.append(bullet)
                enemies_to_remove.append(enemy)
                score += 1
                break
        for c_enemy in circle_enemies:
            if math.hypot(c_enemy.x - bullet.x, c_enemy.y - bullet.y) < c_enemy.radius:
                bullets_to_remove.append(bullet)
                circle_enemies_to_remove.append(c_enemy)
                score += 1
                break
        for o_enemy in octagon_enemies:
            if math.hypot(o_enemy.x - bullet.x, o_enemy.y - bullet.y) < o_enemy.radius:
                bullets_to_remove.append(bullet)
                octagon_enemies_to_remove.append(o_enemy)
                score += 2
                break

    for b in bullets_to_remove:
        if b in bullets:
            bullets.remove(b)

    # Enemy updates
    for enemy in enemies:
        enemy.move_toward_player(player_x, player_y)
        enemy.draw(screen)
        player_rect = pygame.Rect(player_x - player_radius, player_y - player_radius, player_radius * 2, player_radius * 2)
        enemy_rect = enemy.get_hitbox()
        if player_rect.colliderect(enemy_rect):
            player_lives -= enemy.damage
            enemies_to_remove.append(enemy)

    for enemy in enemies_to_remove:
        death_sound.play()
        if enemy in enemies:
            enemies.remove(enemy)

    for c_enemy in circle_enemies:
        c_enemy.move_toward_player(player_x, player_y)
        c_enemy.update()
        c_enemy.draw(screen)
        player_rect = pygame.Rect(player_x - player_radius, player_y - player_radius, player_radius * 2, player_radius * 2)
        c_enemy_rect = pygame.Rect(c_enemy.x - c_enemy.radius, c_enemy.y - c_enemy.radius, c_enemy.radius*2, c_enemy.radius*2)
        if player_rect.colliderect(c_enemy_rect):
            player_lives -= 1+damage_adder
            circle_enemies_to_remove.append(c_enemy)

    for c_enemy in circle_enemies_to_remove:
        if c_enemy in circle_enemies:
            circle_enemies.remove(c_enemy)

    for o_enemy in octagon_enemies:
        o_enemy.move_toward_player(player_x, player_y)
        o_enemy.update()
        o_enemy.draw(screen)
        if math.hypot(o_enemy.x - player_x, o_enemy.y - player_y) < o_enemy.radius + player_radius:
            player_lives -= 2+damage_adder
            octagon_enemies_to_remove.append(o_enemy)

    for o_enemy in octagon_enemies_to_remove:
        death_sound.play()
        if o_enemy in octagon_enemies:
            octagon_enemies.remove(o_enemy)

    for bullet in enemy_bullets[:]:
        if bullet.move():
            enemy_bullets.remove(bullet)
        else:
            bullet.draw(screen)

    # End game if lives <= 0
    if player_lives <= 0:
        running = False

    # Spawn new wave
    if not enemies and not circle_enemies and not octagon_enemies:
        wave += 1
        enemy_bullets = []
        for _ in range(5 + wave):
            if wave >= 9 and random.random() < 0.05:
                octagon_enemies.append(OctagonEnemy())
            elif wave >= 7 and random.random() < 0.1:
                circle_enemies.append(CircleEnemy())
            elif wave >= 5 and random.random() < 0.2:
                enemies.append(Enemy(speed=3, damage=3+damage_adder, is_triangle=True))
            else:
                enemies.append(Enemy())
        if wave==5:
            show_enemy_intro("triangle")
        if wave==7:
            show_enemy_intro("circle")
        if wave==9:
            show_enemy_intro("octagon")
        if wave % 4 == 0 and wave<16:  # every 4th wave
            sacrifice_level = wave // 4
            choice = show_sacrifice_screen(sacrifice_level)
            if sacrifice_level==1:
                if choice==1:
                    size_b+=4
                if choice==2:
                    e_size_mod+=1
                if choice==3:
                    b_speed += 5
            if sacrifice_level==2:
                if choice==1:
                    damage_adder=1
                if choice==2:
                    player_speed-=3
                if choice==3:
                    player_lives-=3
                    if player_lives<=0:
                        player_lives=1
            if sacrifice_level==3:
                if choice==2:
                    laser=True
                    exploding_b=False
                    shotgun=False
    pygame.draw.circle(screen, BLUE, (player_x, player_y), player_radius)
    lives_text = font.render(f"Lives: {player_lives}", True, WHITE)
    score_text = font.render(f"Score: {score}", True, WHITE)
    wave_text = font.render(f"Wave: {wave}", True, WHITE)
    screen.blit(lives_text, (10, 10))
    screen.blit(score_text, (10, 40))
    screen.blit(wave_text, (10, 70))

    pygame.display.flip()
    clock.tick(FPS)

# Game Over Screen
screen.fill(BLACK)
game_over_text = font.render("GAME OVER", True, RED)
final_score_text = font.render(f"Final Score: {score}", True, WHITE)
screen.blit(game_over_text, (WIDTH // 2 - 80, HEIGHT // 2 - 20))
screen.blit(final_score_text, (WIDTH // 2 - 90, HEIGHT // 2 + 20))
pygame.display.flip()
pygame.time.wait(3000)
pygame.quit()
sys.exit()
