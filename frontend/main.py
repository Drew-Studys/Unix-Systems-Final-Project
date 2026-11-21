
import pygame
import subprocess
import sys
from pathlib import Path

# ----------------------------------------
# PROJECT IMPORTS
# ----------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from backend import database
from backend import players


# ----------------------------------------
# CONFIGURATION
# ----------------------------------------

WIDTH = 960
HEIGHT = 700
FPS = 60

FRONTEND_DIR = Path(__file__).resolve().parent

LOGIN_PATH = FRONTEND_DIR / "login.py"
PROFILE_PATH = FRONTEND_DIR / "profiles.py"
LEADERBOARD_PATH = FRONTEND_DIR / "leaderboard_screen.py"
ACHIEVEMENTS_PATH = FRONTEND_DIR / "achievements.py"
SETTINGS_PATH = FRONTEND_DIR / "settings.py"
SNAKE_PATH = FRONTEND_DIR / "snake.py"

BACKGROUND = (15, 23, 42)
PANEL = (30, 41, 59)
SELECTED = (37, 99, 235)

WHITE = (255, 255, 255)
GRAY = (148, 163, 184)
CYAN = (103, 232, 249)
GREEN = (74, 222, 128)
RED = (248, 113, 113)

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

MENU_ITEMS = [
    "PLAY GAMES",
    "PLAYER PROFILE",
    "LEADERBOARDS",
    "ACHIEVEMENTS",
    "SETTINGS",
    "SWITCH PLAYER"
]

GAME_ITEMS = [
    "SNAKE",
    "BACK TO MAIN MENU"
]

ROW_HEIGHT = 58
ROW_GAP = 9
LIST_TOP = 195
LIST_X = 190
LIST_WIDTH = 580


# ----------------------------------------
# MAIN ARCADE SCREEN
# ----------------------------------------

class ArcadeMainScreen:

    def __init__(self):

        pygame.init()
        pygame.joystick.init()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

        pygame.display.set_caption(
            "IUP Arcade - Main Menu"
        )

        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont(
            "arial", 52, bold=True
        )

        self.heading_font = pygame.font.SysFont(
            "arial", 26, bold=True
        )

        self.font = pygame.font.SysFont(
            "arial", 25, bold=True
        )

        self.small_font = pygame.font.SysFont(
            "arial", 19
        )

        self.player = players.get_active_player()

        self.selected_index = 0
        self.game_selected_index = 0

        self.mode = "main"
        self.running = True

        self.message = ""
        self.message_color = WHITE

        self.clickable_rects = []

        self.last_joystick_move = 0
        self.joystick_delay = 180

        self.joysticks = []

        for index in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(index)
            joystick.init()
            self.joysticks.append(joystick)

    # ------------------------------------
    # DRAWING HELPERS
    # ------------------------------------

    def draw_text(self, text, font, color, center):

        surface = font.render(
            str(text), True, color
        )

        rect = surface.get_rect(center=center)

        self.screen.blit(surface, rect)

    def draw_background(self):

        self.screen.fill(BACKGROUND)

        border = pygame.Rect(
            35, 35,
            WIDTH - 70,
            HEIGHT - 70
        )

        pygame.draw.rect(
            self.screen,
            PANEL,
            border,
            3,
            border_radius=15
        )

    # ------------------------------------
    # HEADER
    # ------------------------------------

    def draw_header(self):

        self.draw_text(
            "IUP ARCADE",
            self.title_font,
            CYAN,
            (WIDTH // 2, 65)
        )

        if self.mode == "main":
            heading = "MAIN MENU"
        else:
            heading = "SELECT A GAME"

        self.draw_text(
            heading,
            self.heading_font,
            WHITE,
            (WIDTH // 2, 125)
        )

        if self.player is not None:
            username = self.player["username"]
        else:
            username = "NO PLAYER"

        self.draw_text(
            f"CURRENT PLAYER: {username}",
            self.small_font,
            GREEN,
            (WIDTH // 2, 165)
        )

    # ------------------------------------
    # MENU BUTTONS
    # ------------------------------------

    def draw_menu(self):

        self.clickable_rects = []

        if self.mode == "main":
            items = MENU_ITEMS
            selected = self.selected_index
        else:
            items = GAME_ITEMS
            selected = self.game_selected_index

        for index, item in enumerate(items):

            y = LIST_TOP + index * (
                ROW_HEIGHT + ROW_GAP
            )

            rect = pygame.Rect(
                LIST_X,
                y,
                LIST_WIDTH,
                ROW_HEIGHT
            )

            is_selected = index == selected

            color = (
                SELECTED if is_selected else PANEL
            )

            pygame.draw.rect(
                self.screen,
                color,
                rect,
                border_radius=10
            )

            if is_selected:
                pygame.draw.rect(
                    self.screen,
                    CYAN,
                    rect,
                    2,
                    border_radius=10
                )

            self.draw_text(
                item,
                self.font,
                WHITE,
                rect.center
            )

            self.clickable_rects.append(
                (rect, index)
            )

    # ------------------------------------
    # FOOTER
    # ------------------------------------

    def draw_footer(self):

        if self.message:
            self.draw_text(
                self.message,
                self.small_font,
                self.message_color,
                (WIDTH // 2, 610)
            )

        self.draw_text(
            "Arrows / 8 2 4 6: Move",
            self.small_font,
            GRAY,
            (WIDTH // 2, 645)
        )

        if self.mode == "main":
            instructions = (
                "Enter / 5 / Mouse: Select    ESC: Exit"
            )
        else:
            instructions = (
                "Enter / 5 / Mouse: Select    ESC: Back"
            )

        self.draw_text(
            instructions,
            self.small_font,
            GRAY,
            (WIDTH // 2, 672)
        )

    # ------------------------------------
    # DRAW SCREEN
    # ------------------------------------

    def draw(self):

        self.draw_background()
        self.draw_header()
        self.draw_menu()
        self.draw_footer()

        pygame.display.flip()

    # ------------------------------------
    # NAVIGATION
    # ------------------------------------

    def move_selection(self, direction):

        if self.mode == "main":

            self.selected_index = (
                self.selected_index + direction
            ) % len(MENU_ITEMS)

        else:

            self.game_selected_index = (
                self.game_selected_index + direction
            ) % len(GAME_ITEMS)

        self.message = ""

    def joystick_move(self, direction):

        now = pygame.time.get_ticks()

        if (
            now - self.last_joystick_move
            >= self.joystick_delay
        ):

            self.move_selection(direction)
            self.last_joystick_move = now

    # ------------------------------------
    # GAME SELECTION MENU
    # ------------------------------------

    def open_game_menu(self):

        self.mode = "games"
        self.game_selected_index = 0
        self.message = ""

    def return_to_main_menu(self):

        self.mode = "main"
        self.message = ""

    # ------------------------------------
    # OPEN OTHER SCREENS
    # ------------------------------------

    def open_screen(self, file_path):

        if not file_path.exists():
            self.message = (
                f"{file_path.name} was not found."
            )
            self.message_color = RED
            return False

        success = False

        try:
            pygame.display.iconify()

            command = [
                sys.executable,
                str(file_path)
            ]

            # Prevent login.py from opening
            # another copy of main.py.
            if file_path == LOGIN_PATH:
                command.append("--select-only")

            subprocess.run(
                command,
                cwd=str(PROJECT_DIR),
                check=True
            )

            success = True

        except (
            OSError,
            subprocess.CalledProcessError
        ) as error:

            print("Error opening screen:", error)

            self.message = (
                f"Could not open {file_path.name}."
            )

            self.message_color = RED

        finally:

            self.screen = pygame.display.set_mode(
                (WIDTH, HEIGHT)
            )

            pygame.display.set_caption(
                "IUP Arcade - Main Menu"
            )

            pygame.event.clear()

        return success

    # ------------------------------------
    # LAUNCH SNAKE
    # ------------------------------------

    def launch_snake(self):

        success = self.open_screen(SNAKE_PATH)

        if success:
            self.return_to_main_menu()

            self.message = "Returned from Snake."
            self.message_color = GREEN

    # ------------------------------------
    # SWITCH PLAYER
    # ------------------------------------

    def switch_player(self):

        success, message = players.logout_player()

        if not success:
            self.message = message
            self.message_color = RED
            return

        self.player = None

        self.open_screen(LOGIN_PATH)

        self.player = players.get_active_player()

        if self.player is None:
            self.running = False

        else:
            self.message = (
                f"Welcome, {self.player['username']}!"
            )
            self.message_color = GREEN

    # ------------------------------------
    # SELECT OPTION
    # ------------------------------------

    def select_option(self):

        self.message = ""

        if self.mode == "games":

            if self.game_selected_index == 0:
                self.launch_snake()

            elif self.game_selected_index == 1:
                self.return_to_main_menu()

            return

        if self.selected_index == 0:
            self.open_game_menu()

        elif self.selected_index == 1:
            self.open_screen(PROFILE_PATH)

        elif self.selected_index == 2:
            self.open_screen(LEADERBOARD_PATH)

        elif self.selected_index == 3:
            self.open_screen(ACHIEVEMENTS_PATH)

        elif self.selected_index == 4:
            self.open_screen(SETTINGS_PATH)

        elif self.selected_index == 5:
            self.switch_player()

    # ------------------------------------
    # GO BACK
    # ------------------------------------

    def go_back(self):

        if self.mode == "games":
            self.return_to_main_menu()

        else:
            self.running = False

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
                    self.go_back()

                elif key in UP_KEYS:
                    self.move_selection(-1)

                elif key in DOWN_KEYS:
                    self.move_selection(1)

                elif key in LEFT_KEYS:
                    self.move_selection(-1)

                elif key in RIGHT_KEYS:
                    self.move_selection(1)

                elif key in SELECT_KEYS:
                    self.select_option()

            elif event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:

                    for rect, index in self.clickable_rects:

                        if rect.collidepoint(event.pos):

                            if self.mode == "main":
                                self.selected_index = index
                            else:
                                self.game_selected_index = index

                            self.select_option()
                            break

            elif event.type == pygame.JOYHATMOTION:

                dx, dy = event.value

                if dy > 0:
                    self.joystick_move(-1)

                elif dy < 0:
                    self.joystick_move(1)

                elif dx > 0:
                    self.joystick_move(1)

                elif dx < 0:
                    self.joystick_move(-1)

            elif event.type == pygame.JOYAXISMOTION:

                if event.axis == 1:

                    if event.value > 0.8:
                        self.joystick_move(1)

                    elif event.value < -0.8:
                        self.joystick_move(-1)

                elif event.axis == 0:

                    if event.value > 0.8:
                        self.joystick_move(1)

                    elif event.value < -0.8:
                        self.joystick_move(-1)

            elif event.type == pygame.JOYBUTTONDOWN:

                if event.button == 0:
                    self.select_option()

                elif event.button == 1:
                    self.go_back()

    # ------------------------------------
    # MAIN LOOP
    # ------------------------------------

    def run(self):

        while self.running:

            self.handle_events()
            self.draw()

            self.clock.tick(FPS)

        pygame.quit()


# ----------------------------------------
# START PROGRAM
# ----------------------------------------

if __name__ == "__main__":

    database.initialize_database()

    # Open login if no player is selected.
    if players.get_active_player() is None:

        subprocess.run(
            [
                sys.executable,
                str(LOGIN_PATH),
                "--select-only"
            ],
            cwd=str(PROJECT_DIR),
            check=False
        )

    # Open menu after a player is selected.
    if players.get_active_player() is not None:

        arcade = ArcadeMainScreen()
        arcade.run()

    else:
        print("No player selected. Arcade menu closed.")

    sys.exit(0)
