import os
import random

try:
    import pygame
except:
    import pip
    pip.main(['install', 'pygame'])
finally:
    import pygame

# Some helper functions and initializations. -----------

run = True
pygame.font.init()
pygame.joystick.init()


def load_image(name):
    return pygame.image.load(os.path.join("assets", name))


def collided(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None


# End of helper functions and initializations, start of
# Game parameters, feel free to change any. ------------

LEVEL = 1
LIVES = 5

FONT = pygame.font.SysFont("comicsans", 50)
LEVEL_UP_FONT = pygame.font.SysFont("comicsans", 100)
LOST_FONT = pygame.font.SysFont("comicsans", 100)
PAUSE_FONT = pygame.font.SysFont("comicsans", 100)

WIDTH, HEIGHT = 750, 750
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")

# Enemy ships
RED_SPACE_SHIP = load_image("pixel_ship_red_small.png")
GREEN_SPACE_SHIP = load_image("pixel_ship_green_small.png")
BLUE_SPACE_SHIP = load_image("pixel_ship_blue_small.png")

# Player ship
YELLOW_SPACE_SHIP = load_image("pixel_ship_yellow.png")
PLAYER_SPACE_SHIP = YELLOW_SPACE_SHIP

# Lasers
RED_LASER = load_image("pixel_laser_red.png")
GREEN_LASER = load_image("pixel_laser_green.png")
BLUE_LASER = load_image("pixel_laser_blue.png")

# Player laser
YELLOW_LASER = load_image("pixel_laser_yellow.png")

# TODO the way lasers are passed may be changed.
PLAYER_LASERS = [(YELLOW_LASER, 100)]
ENEMY_LASERS = [(RED_LASER, 10), (GREEN_LASER, 20), (BLUE_LASER, 30)]
ENEMY_SHIPS = [RED_SPACE_SHIP, GREEN_SPACE_SHIP, BLUE_SPACE_SHIP]

# Background
BG = pygame.transform.scale(load_image("background-black.png"), (WIDTH, HEIGHT))

FPS = 60

INIT_HEALTH = 100
INIT_ENEMY_COUNT = 10

INIT_ENEMY_VELOCITY = 1
PLAYER_LASER_VELOCITY = -5
ENEMY_LASER_VELOCITY = 5

SHOOT_COOLDOWN_PERIOD = FPS * 4
ENEMY_SHOOT_COOLDOWN_PERIOD = FPS * 2

SHIPS_COLLISION_DAMAGE = 50

CONTROLLER_SPEED_INCREMENT_FACTOR = 1.25

RANDOM_SHOOT_FACTOR = 5

CROWD_FACTOR = 2
ENEMY_INCREMENT_COUNT = int(INIT_ENEMY_COUNT / 2)
ENEMY_VELOCITY_INCREMENT = 0.5

SHIP_VELOCITY = 5
SHIP_WIDTH = PLAYER_SPACE_SHIP.get_width()
SHIP_HEIGHT = PLAYER_SPACE_SHIP.get_height()

LABELS_COLOR = (255, 255, 255)
LEVEL_UP_COLOR = (255, 255, 255)
PAUSE_COLOR = (255, 255, 255)
LOST_COLOR = (255, 255, 255)
HEALTH_BAR_BACKGROUND_COLOR = (255, 0, 0)
HEALTH_BAR_COLOR = (0, 255, 0)

HEALTH_BAR_OFFSET = 10
HEALTH_BAR_HEIGHT = 10
HEALTH_BAR_WIDTH = SHIP_WIDTH

LABELS_OFFSET = 10
PLAYER_SHIP_OFFSET = 30

LEVEL_UP_WAIT_TIME = 3

# if you wish to set it to non-zero, consider changing the logic.
LOST_WAIT_TIME = 0

# WIGGLES_PER_SECOND = 2
# WIGGLE_PERIOD = int(FPS / WIGGLES_PER_SECOND)
# SHIP_WIGGLE_X = int(5 / WIGGLES_PER_SECOND)
# SHIP_WIGGLE_Y = int(5 / WIGGLES_PER_SECOND)

# TODO these three lists may not be global
SHIPS_LIST = []
LASERS_LIST = []
ENEMY_LASERS_LIST = []


# End of game parameters -------------------------------

class XBoxController:
    buttons = 11

    def __init__(self, controller):
        self.controller = controller

    def button_pressed(self):

        if self.controller is None:
            return False

        for i in range(0, XBoxController.buttons):
            if self.controller.get_button(i) == 1:
                return True
        return False

    def shoot_pressed(self):

        if self.controller is None:
            return False

        # temp implementation.
        for i in range(1, XBoxController.buttons):
            if self.controller.get_button(i) == 1:
                return True

    def pause_pressed(self):

        if self.controller is None:
            return False

        return self.controller.get_button(0) == 1

    def x_value(self):

        if self.controller is None:
            return 0

        value = self.controller.get_axis(0)
        return value

    def y_value(self):

        if self.controller is None:
            return 0

        value = self.controller.get_axis(1)
        return value


class Laser:

    def __init__(self, laser_img, x, y, velocity, damage, laser_list):
        self.x = x
        self.y = y
        self.laser_img = laser_img
        self.velocity = velocity
        self.damage = damage
        self.laser_list = laser_list
        self.mask = pygame.mask.from_surface(self.laser_img)

    def get_width(self):
        return self.laser_img.get_width()

    def get_height(self):
        return self.laser_img.get_height()

    def draw(self):
        WIN.blit(self.laser_img, (self.x, self.y))

    def move(self):
        self.y += self.velocity
        if not (-self.get_height() <= self.y <= HEIGHT):
            self.laser_list.remove(self)


class Ship:
    def __init__(self, x, y, lasers, ship_img, health=INIT_HEALTH):
        self.x = x
        self.y = y
        self.lasers = lasers
        self.health = health
        self.ship_img = ship_img
        self.max_health = health
        self.last_shoot_ticks = 0
        self.mask = pygame.mask.from_surface(self.ship_img)

    def health_percentage(self):
        return self.health / self.max_health

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()

    def draw(self):
        WIN.blit(self.ship_img, (self.x, self.y))

    def damage(self, value):
        self.health -= value


class Player(Ship):

    def __init__(self, x, y, lasers, health=INIT_HEALTH):
        super().__init__(x, y, lasers, PLAYER_SPACE_SHIP, health)

    def draw(self):
        super().draw()
        health_bar_x = int(self.x)
        health_bar_y = self.y + self.get_height() + HEALTH_BAR_OFFSET
        pygame.draw.rect(WIN, HEALTH_BAR_BACKGROUND_COLOR,
                         (health_bar_x, health_bar_y, HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT))
        pygame.draw.rect(WIN, HEALTH_BAR_COLOR,
                         (health_bar_x, health_bar_y,
                          int(HEALTH_BAR_WIDTH * self.health_percentage()), HEALTH_BAR_HEIGHT))

    def move_x(self, value):
        self.x += value
        if self.x < -self.get_width() / 2:
            self.x = -int(self.get_width() / 2)
        if self.x > WIDTH - SHIP_WIDTH / 2:
            self.x = WIDTH - int(SHIP_WIDTH / 2)

    def move_y(self, value):
        self.y += value
        if self.y < 0:
            self.y = 0
        elif self.y > HEIGHT - SHIP_HEIGHT:
            self.y = HEIGHT - SHIP_HEIGHT

    def move_up(self, velocity):
        self.move_y(-velocity)

    def move_down(self, velocity):
        self.move_y(velocity)

    def move_right(self, velocity):
        self.move_x(velocity)

    def move_left(self, velocity):
        self.move_x(-velocity)

    def shoot(self, velocity):
        # TODO for now, only the first laser in the list will be shot.
        ticks = pygame.time.get_ticks()
        if ticks - self.last_shoot_ticks > SHOOT_COOLDOWN_PERIOD:
            LASERS_LIST.append(Laser(self.lasers[0][0], self.x, self.y, velocity, self.lasers[0][1], LASERS_LIST))
            self.last_shoot_ticks = ticks


class Enemy(Ship):

    def __init__(self, x, y, lasers, ship_img, velocity):
        super().__init__(x, y, lasers, ship_img)
        self.velocity = velocity

    def draw(self):
        WIN.blit(self.ship_img, (self.x, self.y))

    def move(self):
        self.y += self.velocity

    def shoot(self, laser, velocity):
        ticks = pygame.time.get_ticks()
        if ticks - self.last_shoot_ticks > ENEMY_SHOOT_COOLDOWN_PERIOD:
            ENEMY_LASERS_LIST.append(
                Laser(laser[0],
                      # At the center.
                      self.x - int(laser[0].get_width() / 2) + int(self.get_width() / 2),
                      self.y,
                      velocity,
                      laser[1],
                      ENEMY_LASERS_LIST
                      )
            )
            self.last_shoot_ticks = ticks

    def shoot_random(self, velocity):
        self.shoot(random.choice(self.lasers), velocity)


def main():
    # TODO consider changing places where nonlocal is used.

    didnt_lose = True
    level = LEVEL
    lives = LIVES
    clock = pygame.time.Clock()
    ship_velocity = SHIP_VELOCITY
    enemy_velocity = INIT_ENEMY_VELOCITY
    ship = Player(int((WIDTH - SHIP_WIDTH) / 2), HEIGHT - SHIP_HEIGHT - PLAYER_SHIP_OFFSET, PLAYER_LASERS[:])
    enemy_count = INIT_ENEMY_COUNT
    freeze_counter = 0
    in_pause = False
    keys_pressed = []
    events = []
    controller = XBoxController(None)
    if pygame.joystick.get_count() > 0:
        controller.controller = pygame.joystick.Joystick(0)

    # wiggle_counter = 0
    # def ship_wiggle(ship):
    #     nonlocal wiggle_counter
    #     if wiggle_counter == 0:
    #         ship.x += random.randrange(-SHIP_WIGGLE_X, SHIP_WIGGLE_X + 1)
    #         ship.y += random.randrange(-SHIP_WIGGLE_Y, SHIP_WIGGLE_Y + 1)
    #         wiggle_counter = WIGGLE_PERIOD
    #     else:
    #         wiggle_counter -= 1

    def draw_list(drawable_list):
        for drawable in drawable_list:
            drawable.draw()

    def draw_enemies():
        return draw_list(SHIPS_LIST)

    def draw_lasers():
        draw_list(LASERS_LIST)
        draw_list(ENEMY_LASERS_LIST)

    def update_lives():
        if ship.health <= 0:
            ship.health += INIT_HEALTH
            nonlocal lives
            lives -= 1

    def check_for_laser_collision():
        # TODO should be optimized.
        for laser in ENEMY_LASERS_LIST[:]:
            if collided(ship, laser):
                ENEMY_LASERS_LIST.remove(laser)
                ship.health -= laser.damage
                update_lives()

    def move_enemies():

        for enemy in SHIPS_LIST[:]:
            enemy.move()
            if enemy.y > HEIGHT:
                SHIPS_LIST.remove(enemy)
                nonlocal lives
                lives -= 1
                return

            # TODO should be optimized.
            for laser in LASERS_LIST[:]:
                if collided(enemy, laser):
                    LASERS_LIST.remove(laser)
                    enemy.health -= laser.damage
                if enemy.health <= 0:
                    SHIPS_LIST.remove(enemy)
                    return

            if collided(enemy, ship):
                ship.damage(SHIPS_COLLISION_DAMAGE)
                SHIPS_LIST.remove(enemy)
                update_lives()

    def move_lasers():
        for laser in LASERS_LIST[:]:
            laser.move()
        for laser in ENEMY_LASERS_LIST[:]:
            laser.move()

    def redraw_window():
        WIN.blit(BG, (0, 0))

        draw_enemies()
        draw_lasers()

        # ship is drawn under the labels.
        ship.draw()

        lives_label = FONT.render(f"lives: {lives}", True, LABELS_COLOR)
        level_label = FONT.render(f"level: {level}", True, LABELS_COLOR)

        WIN.blit(lives_label, (LABELS_OFFSET, LABELS_OFFSET))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - LABELS_OFFSET, LABELS_OFFSET))

        pygame.display.update()

    def move_player_keyboard():
        if keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]:
            ship.move_left(ship_velocity)
        if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
            ship.move_right(ship_velocity)
        if keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
            ship.move_down(ship_velocity)
        if keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]:
            ship.move_up(ship_velocity)

        check_for_laser_collision()

    def move_player_controller():
        ship.move_x(int(controller.x_value() * ship_velocity * CONTROLLER_SPEED_INCREMENT_FACTOR))
        ship.move_y(int(controller.y_value() * ship_velocity * CONTROLLER_SPEED_INCREMENT_FACTOR))
        check_for_laser_collision()

    def handle_events():

        for event in events:

            if event.type == pygame.QUIT:
                global run
                nonlocal didnt_lose
                unpause()
                didnt_lose = False
                run = False
                break

            if event.type == pygame.KEYDOWN:
                nonlocal freeze_counter
                freeze_counter = 0
                if event.key == pygame.K_SPACE:
                    unpause()
                elif event.key == pygame.K_p:
                    if in_pause:
                        unpause()
                    else:
                        pause_with_message()

            # TODO this is just a copy of the above block. find a better way..
            if controller.button_pressed():
                freeze_counter = 0
                if controller.shoot_pressed():
                    unpause()
                elif controller.pause_pressed():
                    if in_pause:
                        unpause()
                    else:
                        pause_with_message()

    def freeze(seconds):
        nonlocal freeze_counter
        freeze_counter = seconds * FPS

    def pause():
        nonlocal in_pause
        in_pause = True

    def unpause():
        nonlocal in_pause
        in_pause = False

    def print_message(message, font, color, period):
        label = font.render(message, True, color)
        WIN.blit(label, (int((WIDTH - label.get_width()) / 2), (HEIGHT - label.get_height()) / 2))
        pygame.display.update()
        if period == 0:
            pause()
        else:
            freeze(period)

    def pause_with_message():
        print_message("Paused", PAUSE_FONT, PAUSE_COLOR, 0)

    def spawn_enemies(count):
        # the enemy ships will be spawn at different negative (so that they're not visible)
        # heights so that they show at different times. not the most efficient way to do it
        # but it works for now.
        for i in range(count):
            ship_image = random.choice(ENEMY_SHIPS)
            SHIPS_LIST.append(
                Enemy(
                    random.randrange(0, WIDTH - ship_image.get_width()),
                    random.randrange(-int((enemy_count * ship_image.get_height()) / CROWD_FACTOR), 0),
                    ENEMY_LASERS,
                    ship_image,
                    enemy_velocity
                )
            )

    def level_up():
        if len(SHIPS_LIST) == 0 and didnt_lose:
            nonlocal level
            nonlocal enemy_count
            nonlocal enemy_velocity
            enemy_count = int(enemy_count + ENEMY_INCREMENT_COUNT)
            enemy_velocity = int(enemy_velocity + ENEMY_VELOCITY_INCREMENT)
            level += 1
            LASERS_LIST.clear()
            ENEMY_LASERS_LIST.clear()
            print_message("Level Up!", LEVEL_UP_FONT, LEVEL_UP_COLOR, LEVEL_UP_WAIT_TIME)
            spawn_enemies(enemy_count)  # will be spawned but not drawn until the freeze time is over.

    def lose():
        if lives == 0:
            print_message("You Lost...", LOST_FONT, LOST_COLOR, LOST_WAIT_TIME)
            nonlocal didnt_lose
            didnt_lose = False

    def shoot_player():
        if keys_pressed[pygame.K_SPACE] or controller.shoot_pressed():
            ship.shoot(PLAYER_LASER_VELOCITY)

    def shoot_enemies():
        for enemy in SHIPS_LIST:
            if not random.randrange(0, RANDOM_SHOOT_FACTOR * FPS):
                enemy.shoot_random(ENEMY_LASER_VELOCITY)

    # Initial spawn
    spawn_enemies(enemy_count)

    while didnt_lose:

        # functions that runs even during the freeze time.
        clock.tick(FPS)

        # TODO you may want to get the events inside the function itself.
        events = pygame.event.get()
        handle_events()

        if freeze_counter > 0:
            freeze_counter -= 1
            continue
        if in_pause:
            continue

        # functions that won't be called during the freeze time.
        keys_pressed = pygame.key.get_pressed()
        shoot_player()
        shoot_enemies()
        move_player_keyboard()
        move_player_controller()
        move_enemies()
        move_lasers()
        redraw_window()

        # functions after redraw_window()
        lose()
        level_up()

    SHIPS_LIST.clear()
    LASERS_LIST.clear()
    ENEMY_LASERS_LIST.clear()

    while in_pause:
        events = pygame.event.get()
        handle_events()


while run:
    main()
