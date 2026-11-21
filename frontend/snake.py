
import pygame
import random
import sys
from pathlib import Path

# ----------------------------------------
# PROJECT IMPORTS
# ----------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from backend import players
from backend import scores


# ----------------------------------------
# CONFIGURATION
# ----------------------------------------

WIDTH = 960
HEIGHT = 700
FPS = 60

CELL_SIZE = 24
COLUMNS = 24
ROWS = 18

BOARD_WIDTH = COLUMNS * CELL_SIZE
BOARD_HEIGHT = ROWS * CELL_SIZE

BOARD_X = (WIDTH - BOARD_WIDTH) // 2
BOARD_Y = 160

MOVE_DELAY = 125
POINTS_PER_FOOD = 100

# Arcade interface colors
BACKGROUND = (15, 23, 42)
PANEL = (30, 41, 59)
WHITE = (255, 255, 255)
GRAY = (148, 163, 184)
CYAN = (103, 232, 249)
GREEN = (74, 222, 128)
RED = (248, 113, 113)

# Google Snake-inspired colors
GRASS_LIGHT = (170, 215, 81)
GRASS_DARK = (162, 209, 73)

SNAKE_BLUE = (71, 117, 235)
SNAKE_HEAD = (79, 125, 242)
SNAKE_OUTLINE = (57, 98, 207)

APPLE_RED = (231, 62, 57)
APPLE_HIGHLIGHT = (255, 142, 130)
APPLE_STEM = (108, 77, 46)
APPLE_LEAF = (59, 150, 67)

EYE_WHITE = (255, 255, 255)
EYE_BLACK = (31, 42, 58)

# Keyboard and arcade controls
UP_KEYS = (
    pygame.K_UP,
    pygame.K_8,
    pygame.K_KP8
)

DOWN_KEYS = (
    pygame.K_DOWN,
    pygame.K_2,
    pygame.K_KP2
)

LEFT_KEYS = (
    pygame.K_LEFT,
    pygame.K_4,
    pygame.K_KP4
)

RIGHT_KEYS = (
    pygame.K_RIGHT,
    pygame.K_6,
    pygame.K_KP6
)

SELECT_KEYS = (
    pygame.K_RETURN,
    pygame.K_KP_ENTER,
    pygame.K_5,
    pygame.K_KP5
)

DIRECTIONS = {
    "UP": (0, -1),
    "DOWN": (0, 1),
    "LEFT": (-1, 0),
    "RIGHT": (1, 0)
}


# ----------------------------------------
# SNAKE GAME
# ----------------------------------------

class SnakeGame:

    def __init__(self):

        pygame.init()
        pygame.joystick.init()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

        pygame.display.set_caption(
            "IUP Arcade - Snake"
        )

        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont(
            "arial", 48, bold=True
        )

        self.heading_font = pygame.font.SysFont(
            "arial", 34, bold=True
        )

        self.font = pygame.font.SysFont(
            "arial", 25, bold=True
        )

        self.small_font = pygame.font.SysFont(
            "arial", 19
        )

        self.player = players.get_active_player()

        self.running = True

        self.joysticks = []

        for index in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(index)
            joystick.init()
            self.joysticks.append(joystick)

        self.last_axis_move = 0
        self.axis_delay = 180

        self.reset_game()

    # ------------------------------------
    # RESET GAME
    # ------------------------------------

    def reset_game(self):

        center_x = COLUMNS // 2
        center_y = ROWS // 2

        self.snake = [
            (center_x, center_y),
            (center_x - 1, center_y),
            (center_x - 2, center_y)
        ]

        self.direction = "RIGHT"
        self.next_direction = "RIGHT"

        self.score = 0
        self.apples_eaten = 0

        self.started = False
        self.paused = False
        self.game_over = False
        self.won = False

        self.score_saved = False
        self.result = None

        self.last_move = pygame.time.get_ticks()

        self.create_food()

    # ------------------------------------
    # CREATE APPLE
    # ------------------------------------

    def create_food(self):

        available = []

        occupied = set(self.snake)

        for x in range(COLUMNS):
            for y in range(ROWS):

                position = (x, y)

                if position not in occupied:
                    available.append(position)

        if available:
            self.food = random.choice(available)

        else:
            self.food = None
            self.won = True
            self.end_game()

    # ------------------------------------
    # CHANGE SNAKE DIRECTION
    # ------------------------------------

    def change_direction(self, new_direction):

        if self.game_over or self.paused:
            return

        current_dx, current_dy = DIRECTIONS[
            self.direction
        ]

        new_dx, new_dy = DIRECTIONS[
            new_direction
        ]

        # Cannot reverse directly into the body
        if (
            current_dx + new_dx == 0
            and current_dy + new_dy == 0
        ):
            return

        self.next_direction = new_direction

        if not self.started:
            self.started = True
            self.last_move = pygame.time.get_ticks()

    # ------------------------------------
    # MOVE SNAKE
    # ------------------------------------

    def move_snake(self):

        if not self.started:
            return

        if self.paused or self.game_over:
            return

        self.direction = self.next_direction

        dx, dy = DIRECTIONS[self.direction]

        head_x, head_y = self.snake[0]

        new_head = (
            head_x + dx,
            head_y + dy
        )

        x, y = new_head

        # Wall collision
        if (
            x < 0
            or x >= COLUMNS
            or y < 0
            or y >= ROWS
        ):
            self.end_game()
            return

        eating = new_head == self.food

        # Tail moves away unless snake is eating
        if eating:
            body = self.snake
        else:
            body = self.snake[:-1]

        # Body collision
        if new_head in body:
            self.end_game()
            return

        self.snake.insert(0, new_head)

        if eating:

            self.score += POINTS_PER_FOOD
            self.apples_eaten += 1

            self.create_food()

        else:
            self.snake.pop()

    # ------------------------------------
    # END GAME AND SAVE SCORE
    # ------------------------------------

    def end_game(self):

        if self.game_over:
            return

        self.game_over = True

        if self.score_saved:
            return

        self.score_saved = True

        self.result = scores.record_game_score(
            "Snake",
            self.score
        )

        if self.result["success"]:

            print(
                f"Snake score saved: {self.score}"
            )

            if self.result["new_record"]:
                print("New personal best!")

            for achievement in self.result["achievements"]:
                print(
                    "Achievement unlocked:",
                    achievement
                )

        else:
            print(self.result["message"])

    # ------------------------------------
    # PAUSE GAME
    # ------------------------------------

    def toggle_pause(self):

        if not self.started or self.game_over:
            return

        self.paused = not self.paused

        if not self.paused:
            self.last_move = pygame.time.get_ticks()

    # ------------------------------------
    # TEXT HELPER
    # ------------------------------------

    def draw_text(
        self,
        text,
        font,
        color,
        center
    ):

        surface = font.render(
            str(text),
            True,
            color
        )

        rect = surface.get_rect(
            center=center
        )

        self.screen.blit(surface, rect)

    # ------------------------------------
    # HEADER
    # ------------------------------------

    def draw_header(self):

        self.screen.fill(BACKGROUND)

        self.draw_text(
            "IUP ARCADE - SNAKE",
            self.title_font,
            CYAN,
            (WIDTH // 2, 45)
        )

        if self.player is None:
            username = "NO PLAYER"
        else:
            username = self.player["username"]

        self.draw_text(
            f"PLAYER: {username}",
            self.small_font,
            GREEN,
            (WIDTH // 2, 94)
        )

        # Score panel
        score_rect = pygame.Rect(
            BOARD_X,
            115,
            BOARD_WIDTH,
            40
        )

        pygame.draw.rect(
            self.screen,
            PANEL,
            score_rect,
            border_radius=8
        )

        self.draw_text(
            f"SCORE: {self.score:,}",
            self.font,
            WHITE,
            (WIDTH // 2 - 110, 135)
        )

        self.draw_text(
            f"APPLES: {self.apples_eaten}",
            self.small_font,
            CYAN,
            (WIDTH // 2 + 135, 135)
        )

    # ------------------------------------
    # GREEN CHECKERBOARD
    # ------------------------------------

    def draw_board(self):

        # Draw checkerboard tiles
        for row in range(ROWS):
            for column in range(COLUMNS):

                if (row + column) % 2 == 0:
                    color = GRASS_LIGHT
                else:
                    color = GRASS_DARK

                rect = pygame.Rect(
                    BOARD_X + column * CELL_SIZE,
                    BOARD_Y + row * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )

                pygame.draw.rect(
                    self.screen,
                    color,
                    rect
                )

        # Draw apple and snake
        self.draw_apple()
        self.draw_snake()

    # ------------------------------------
    # GOOGLE-STYLE APPLE
    # ------------------------------------

    def draw_apple(self):

        if self.food is None:
            return

        food_x, food_y = self.food

        center_x = (
            BOARD_X
            + food_x * CELL_SIZE
            + CELL_SIZE // 2
        )

        center_y = (
            BOARD_Y
            + food_y * CELL_SIZE
            + CELL_SIZE // 2
        )

        # Apple shadow
        pygame.draw.circle(
            self.screen,
            (174, 71, 49),
            (center_x, center_y + 2),
            10
        )

        # Apple body
        pygame.draw.circle(
            self.screen,
            APPLE_RED,
            (center_x, center_y),
            10
        )

        # Apple highlight
        pygame.draw.circle(
            self.screen,
            APPLE_HIGHLIGHT,
            (center_x - 3, center_y - 4),
            3
        )

        # Stem
        pygame.draw.line(
            self.screen,
            APPLE_STEM,
            (center_x, center_y - 8),
            (center_x + 1, center_y - 13),
            3
        )

        # Leaf
        pygame.draw.ellipse(
            self.screen,
            APPLE_LEAF,
            (
                center_x + 1,
                center_y - 14,
                9,
                5
            )
        )

    # ------------------------------------
    # ROUNDED SNAKE
    # ------------------------------------

    def draw_snake(self):

        # Draw body first, then head
        for index in range(
            len(self.snake) - 1, -1, -1
        ):

            x, y = self.snake[index]

            center_x = (
                BOARD_X
                + x * CELL_SIZE
                + CELL_SIZE // 2
            )

            center_y = (
                BOARD_Y
                + y * CELL_SIZE
                + CELL_SIZE // 2
            )

            is_head = index == 0

            if is_head:
                color = SNAKE_HEAD
            else:
                color = SNAKE_BLUE

            # Connect segments for a smooth snake
            if index < len(self.snake) - 1:

                next_x, next_y = self.snake[index + 1]

                next_center_x = (
                    BOARD_X
                    + next_x * CELL_SIZE
                    + CELL_SIZE // 2
                )

                next_center_y = (
                    BOARD_Y
                    + next_y * CELL_SIZE
                    + CELL_SIZE // 2
                )

                if x == next_x:

                    top = min(
                        center_y,
                        next_center_y
                    )

                    connector = pygame.Rect(
                        center_x - 10,
                        top,
                        20,
                        abs(center_y - next_center_y)
                    )

                else:

                    left = min(
                        center_x,
                        next_center_x
                    )

                    connector = pygame.Rect(
                        left,
                        center_y - 10,
                        abs(center_x - next_center_x),
                        20
                    )

                pygame.draw.rect(
                    self.screen,
                    color,
                    connector
                )

            # Rounded snake segment
            pygame.draw.circle(
                self.screen,
                color,
                (center_x, center_y),
                11
            )

            if is_head:
                self.draw_eyes(
                    center_x,
                    center_y
                )

    # ------------------------------------
    # SNAKE EYES
    # ------------------------------------

    def draw_eyes(self, center_x, center_y):

        direction = self.direction

        if direction == "RIGHT":
            eyes = [
                (center_x + 5, center_y - 5),
                (center_x + 5, center_y + 5)
            ]

        elif direction == "LEFT":
            eyes = [
                (center_x - 5, center_y - 5),
                (center_x - 5, center_y + 5)
            ]

        elif direction == "UP":
            eyes = [
                (center_x - 5, center_y - 5),
                (center_x + 5, center_y - 5)
            ]

        else:
            eyes = [
                (center_x - 5, center_y + 5),
                (center_x + 5, center_y + 5)
            ]

        for eye_x, eye_y in eyes:

            pygame.draw.circle(
                self.screen,
                EYE_WHITE,
                (eye_x, eye_y),
                4
            )

            pygame.draw.circle(
                self.screen,
                EYE_BLACK,
                (eye_x, eye_y),
                2
            )

    # ------------------------------------
    # GAME OVER / PAUSE OVERLAY
    # ------------------------------------

    def draw_overlay(self, heading, lines):

        overlay = pygame.Surface(
            (BOARD_WIDTH, BOARD_HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill((15, 23, 42, 220))

        self.screen.blit(
            overlay,
            (BOARD_X, BOARD_Y)
        )

        center_y = (
            BOARD_Y + BOARD_HEIGHT // 2
        )

        self.draw_text(
            heading,
            self.heading_font,
            CYAN,
            (WIDTH // 2, center_y - 85)
        )

        for index, line in enumerate(lines):

            self.draw_text(
                line,
                self.small_font,
                WHITE,
                (
                    WIDTH // 2,
                    center_y - 25 + index * 33
                )
            )

    # ------------------------------------
    # GAME STATUS
    # ------------------------------------

    def draw_status(self):

        if not self.started:

            self.draw_overlay(
                "READY TO PLAY?",
                [
                    "Eat apples to grow your snake",
                    "Avoid the walls and your own body",
                    "Press a direction to start"
                ]
            )

        elif self.paused:

            self.draw_overlay(
                "PAUSED",
                [
                    "Press P or 5 to resume"
                ]
            )

        elif self.game_over:

            heading = (
                "YOU WIN!"
                if self.won
                else "GAME OVER"
            )

            lines = [
                f"Final Score: {self.score:,}"
            ]

            if self.result is not None:

                if self.result["success"]:

                    if self.result["new_record"]:
                        lines.append(
                            "NEW PERSONAL BEST!"
                        )
                    else:
                        lines.append("Score saved!")

                    unlocked = self.result["achievements"]

                    if unlocked:
                        lines.append(
                            f"{len(unlocked)} achievement(s) unlocked!"
                        )

                else:
                    lines.append(
                        self.result["message"]
                    )

            lines.append(
                "Press 5 / Enter to play again"
            )

            lines.append(
                "Press ESC to return"
            )

            self.draw_overlay(
                heading,
                lines
            )

    # ------------------------------------
    # FOOTER
    # ------------------------------------

    def draw_footer(self):

        self.draw_text(
            "8: UP    2: DOWN    4: LEFT    6: RIGHT",
            self.small_font,
            GRAY,
            (WIDTH // 2, 625)
        )

        self.draw_text(
            "P / 5: Pause    ESC: Exit",
            self.small_font,
            WHITE,
            (WIDTH // 2, 660)
        )

    # ------------------------------------
    # DRAW SCREEN
    # ------------------------------------

    def draw(self):

        self.draw_header()
        self.draw_board()
        self.draw_status()
        self.draw_footer()

        pygame.display.flip()

    # ------------------------------------
    # SELECT BUTTON
    # ------------------------------------

    def select_button(self):

        if self.game_over:
            self.reset_game()

        elif self.started:
            self.toggle_pause()

    # ------------------------------------
    # JOYSTICK AXIS
    # ------------------------------------

    def joystick_axis(self, direction):

        now = pygame.time.get_ticks()

        if (
            now - self.last_axis_move
            >= self.axis_delay
        ):

            self.change_direction(direction)
            self.last_axis_move = now

    # ------------------------------------
    # EVENT HANDLING
    # ------------------------------------

    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:

                key = event.key

                if key == pygame.K_ESCAPE:
                    self.running = False

                elif key in UP_KEYS:
                    self.change_direction("UP")

                elif key in DOWN_KEYS:
                    self.change_direction("DOWN")

                elif key in LEFT_KEYS:
                    self.change_direction("LEFT")

                elif key in RIGHT_KEYS:
                    self.change_direction("RIGHT")

                elif key == pygame.K_p:
                    self.toggle_pause()

                elif key in SELECT_KEYS:
                    self.select_button()

            elif event.type == pygame.JOYHATMOTION:

                dx, dy = event.value

                if dy > 0:
                    self.change_direction("UP")

                elif dy < 0:
                    self.change_direction("DOWN")

                elif dx < 0:
                    self.change_direction("LEFT")

                elif dx > 0:
                    self.change_direction("RIGHT")

            elif event.type == pygame.JOYAXISMOTION:

                if event.axis == 0:

                    if event.value > 0.8:
                        self.joystick_axis("RIGHT")

                    elif event.value < -0.8:
                        self.joystick_axis("LEFT")

                elif event.axis == 1:

                    if event.value > 0.8:
                        self.joystick_axis("DOWN")

                    elif event.value < -0.8:
                        self.joystick_axis("UP")

            elif event.type == pygame.JOYBUTTONDOWN:

                if event.button == 0:
                    self.select_button()

                elif event.button == 1:
                    self.running = False

    # ------------------------------------
    # MAIN LOOP
    # ------------------------------------

    def run(self):

        while self.running:

            self.handle_events()

            now = pygame.time.get_ticks()

            if (
                self.started
                and not self.paused
                and not self.game_over
                and now - self.last_move >= MOVE_DELAY
            ):

                self.move_snake()
                self.last_move = now

            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


# ----------------------------------------
# START GAME
# ----------------------------------------

if __name__ == "__main__":

    game = SnakeGame()
    game.run()

    sys.exit(0)
