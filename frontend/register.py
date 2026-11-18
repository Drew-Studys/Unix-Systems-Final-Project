
import pygame
import sqlite3
import sys
from pathlib import Path

# ----------------------------------------
# CONFIGURATION
# ----------------------------------------

WIDTH = 960
HEIGHT = 700
FPS = 60
MAX_USERNAME_LENGTH = 16

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_DIR / "data" / "arcade.db"

BACKGROUND = (15, 23, 42)
PANEL = (30, 41, 59)
BUTTON = (51, 65, 85)
SELECTED = (37, 99, 235)
WHITE = (255, 255, 255)
GRAY = (148, 163, 184)
CYAN = (103, 232, 249)
GREEN = (74, 222, 128)
RED = (248, 113, 113)

KEYS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
KEYS += ["SPACE", "DELETE", "CREATE", "BACK"]

COLUMNS = 10
KEY_WIDTH = 80
KEY_HEIGHT = 65
KEY_GAP = 8

GRID_WIDTH = COLUMNS * (KEY_WIDTH + KEY_GAP) - KEY_GAP
GRID_X = (WIDTH - GRID_WIDTH) // 2
GRID_Y = 275

# Regular numbers, numpad numbers, and arrow keys
MOVE_KEYS = {
    pygame.K_LEFT: (-1, 0),
    pygame.K_4: (-1, 0),
    pygame.K_KP4: (-1, 0),

    pygame.K_RIGHT: (1, 0),
    pygame.K_6: (1, 0),
    pygame.K_KP6: (1, 0),

    pygame.K_UP: (0, -1),
    pygame.K_8: (0, -1),
    pygame.K_KP8: (0, -1),

    pygame.K_DOWN: (0, 1),
    pygame.K_2: (0, 1),
    pygame.K_KP2: (0, 1),
}

SELECT_KEYS = (
    pygame.K_RETURN,
    pygame.K_KP_ENTER,
    pygame.K_5,
    pygame.K_KP5,
)


# ----------------------------------------
# DATABASE
# ----------------------------------------

def initialize_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def create_player(username):
    username = username.strip()

    if not username:
        return False, "Please enter a username."

    if len(username) > MAX_USERNAME_LENGTH:
        return False, "Username is too long."

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.execute(
                "INSERT INTO players (username) VALUES (?)",
                (username,)
            )

        return True, f"Player {username} created successfully!"

    except sqlite3.IntegrityError:
        return False, "That username already exists."

    except sqlite3.Error:
        return False, "Database error. Please try again."


# ----------------------------------------
# REGISTRATION SCREEN
# ----------------------------------------

class RegisterScreen:

    def __init__(self):
        pygame.init()
        pygame.joystick.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("IUP Arcade - Register")

        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont(
            "arial", 52, bold=True
        )
        self.font = pygame.font.SysFont(
            "arial", 26, bold=True
        )
        self.small_font = pygame.font.SysFont("arial", 20)

        self.username = ""
        self.selected_index = 0
        self.message = ""
        self.message_color = WHITE
        self.running = True

        self.last_joystick_move = 0
        self.joystick_delay = 180

        self.key_rects = []

        for index in range(len(KEYS)):
            row = index // COLUMNS
            column = index % COLUMNS

            x = GRID_X + column * (KEY_WIDTH + KEY_GAP)
            y = GRID_Y + row * (KEY_HEIGHT + KEY_GAP)

            self.key_rects.append(
                pygame.Rect(x, y, KEY_WIDTH, KEY_HEIGHT)
            )

        self.joysticks = []

        for index in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(index)
            joystick.init()
            self.joysticks.append(joystick)

    # ------------------------------------
    # DRAWING
    # ------------------------------------

    def draw_text(self, text, font, color, center):
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=center)
        self.screen.blit(surface, rect)

    def draw(self):
        self.screen.fill(BACKGROUND)

        self.draw_text(
            "IUP ARCADE",
            self.title_font,
            CYAN,
            (WIDTH // 2, 65)
        )

        self.draw_text(
            "CREATE NEW PLAYER",
            self.font,
            WHITE,
            (WIDTH // 2, 125)
        )

        input_rect = pygame.Rect(190, 165, 580, 65)

        pygame.draw.rect(
            self.screen,
            PANEL,
            input_rect,
            border_radius=10
        )

        pygame.draw.rect(
            self.screen,
            CYAN,
            input_rect,
            2,
            border_radius=10
        )

        self.draw_text(
            self.username + "_",
            self.font,
            WHITE,
            input_rect.center
        )

        self.draw_text(
            f"{len(self.username)}/{MAX_USERNAME_LENGTH}",
            self.small_font,
            GRAY,
            (WIDTH // 2, 248)
        )

        for index, key in enumerate(KEYS):
            rect = self.key_rects[index]
            is_selected = index == self.selected_index

            color = SELECTED if is_selected else BUTTON

            pygame.draw.rect(
                self.screen,
                color,
                rect,
                border_radius=8
            )

            if is_selected:
                pygame.draw.rect(
                    self.screen,
                    CYAN,
                    rect,
                    2,
                    border_radius=8
                )

            font = self.small_font if len(key) > 2 else self.font

            self.draw_text(
                key,
                font,
                WHITE,
                rect.center
            )

        if self.message:
            self.draw_text(
                self.message,
                self.small_font,
                self.message_color,
                (WIDTH // 2, 600)
            )

        self.draw_text(
            "Arrows / 8 2 4 6: Move",
            self.small_font,
            GRAY,
            (WIDTH // 2, 645)
        )

        self.draw_text(
            "Enter / 5 / Mouse: Select",
            self.small_font,
            GRAY,
            (WIDTH // 2, 672)
        )

        pygame.display.flip()

    # ------------------------------------
    # NAVIGATION
    # ------------------------------------

    def move_selection(self, dx, dy):
        row = self.selected_index // COLUMNS
        column = self.selected_index % COLUMNS

        row = (row + dy) % 4
        column = (column + dx) % COLUMNS

        self.selected_index = row * COLUMNS + column

    def joystick_move(self, dx, dy):
        now = pygame.time.get_ticks()

        if now - self.last_joystick_move >= self.joystick_delay:
            self.move_selection(dx, dy)
            self.last_joystick_move = now

    # ------------------------------------
    # SELECT KEY
    # ------------------------------------

    def select_key(self, key):
        self.message = ""

        if key == "DELETE":
            self.username = self.username[:-1]

        elif key == "SPACE":
            if self.username and len(self.username) < MAX_USERNAME_LENGTH:
                self.username += " "

        elif key == "CREATE":
            success, message = create_player(self.username)

            self.message = message
            self.message_color = GREEN if success else RED

            if success:
                self.username = ""

        elif key == "BACK":
            self.running = False

        else:
            if len(self.username) < MAX_USERNAME_LENGTH:
                self.username += key

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

                # Check controls BEFORE entering characters
                elif key in MOVE_KEYS:
                    dx, dy = MOVE_KEYS[key]
                    self.move_selection(dx, dy)

                elif key in SELECT_KEYS:
                    self.select_key(KEYS[self.selected_index])

                elif key == pygame.K_BACKSPACE:
                    self.select_key("DELETE")

                # Normal typing still works for letters
                # and other non-control numbers
                elif event.unicode and event.unicode.isascii():
                    character = event.unicode.upper()

                    if character in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                        self.select_key(character)

                    elif character in "01379":
                        self.select_key(character)

                    elif character == " ":
                        self.select_key("SPACE")

            # Mouse clicking still works
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:

                    for index, rect in enumerate(self.key_rects):
                        if rect.collidepoint(event.pos):
                            self.selected_index = index
                            self.select_key(KEYS[index])
                            break

            # Physical USB joystick support
            elif event.type == pygame.JOYHATMOTION:
                dx, dy = event.value

                if dx:
                    self.joystick_move(dx, 0)

                if dy:
                    self.joystick_move(0, -dy)

            elif event.type == pygame.JOYAXISMOTION:
                if event.axis == 0:
                    if event.value > 0.8:
                        self.joystick_move(1, 0)

                    elif event.value < -0.8:
                        self.joystick_move(-1, 0)

                elif event.axis == 1:
                    if event.value > 0.8:
                        self.joystick_move(0, 1)

                    elif event.value < -0.8:
                        self.joystick_move(0, -1)

            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:
                    self.select_key(KEYS[self.selected_index])

                elif event.button == 1:
                    self.select_key("DELETE")

    # ------------------------------------
    # MAIN LOOP
    # ------------------------------------

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    initialize_database()

    registration = RegisterScreen()
    registration.run()

    sys.exit(0)
