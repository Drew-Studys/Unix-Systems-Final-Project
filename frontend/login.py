import pygame
import subprocess
import sys
from pathlib import Path

# ----------------------------------------
# CONFIGURATION
# ----------------------------------------

WIDTH = 960
HEIGHT = 700
FPS = 60

PROJECT_DIR = Path(__file__).resolve().parent.parent
REGISTER_PATH = Path(__file__).resolve().parent / "register.py"
MAIN_PATH = Path(__file__).resolve().parent / "main.py"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from backend import players as player_backend

BACKGROUND = (15, 23, 42)
PANEL = (30, 41, 59)
SELECTED = (37, 99, 235)
WHITE = (255, 255, 255)
GRAY = (148, 163, 184)
CYAN = (103, 232, 249)
GREEN = (74, 222, 128)
RED = (248, 113, 113)

ROW_HEIGHT = 64
ROW_GAP = 10
VISIBLE_ROWS = 5
LIST_TOP = 205
LIST_X = 200
LIST_WIDTH = 560

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

SELECT_KEYS = (
    pygame.K_RETURN,
    pygame.K_KP_ENTER,
    pygame.K_5,
    pygame.K_KP5
)

SUCCESS_DELAY = 1000


# ----------------------------------------
# DATABASE
# ----------------------------------------

def get_players():
    try:
        player_backend.initialize_players()
        accounts = player_backend.get_all_accounts()
        accounts.sort(key=lambda account: account["id"])
        return accounts, ""

    except Exception as error:
        print("Could not load player accounts:", error)
        return [], "Could not load player accounts."


# ----------------------------------------
# LOGIN SCREEN
# ----------------------------------------

class LoginScreen:

    def __init__(self):
        pygame.init()
        pygame.joystick.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("IUP Arcade - Login")

        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont(
            "arial", 52, bold=True
        )

        self.font = pygame.font.SysFont(
            "arial", 26, bold=True
        )

        self.small_font = pygame.font.SysFont("arial", 20)

        self.players = []
        self.options = []
        self.selected_index = 0

        self.message = ""
        self.message_color = WHITE

        self.running = True
        self.logged_in = False
        self.active_player = None
        self.success_time = None

        self.clickable_rects = []

        self.last_joystick_move = 0
        self.joystick_delay = 180

        self.joysticks = []

        for index in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(index)
            joystick.init()
            self.joysticks.append(joystick)

        self.refresh_players()

    # ------------------------------------
    # LOAD PLAYERS
    # ------------------------------------

    def refresh_players(self):
        self.players, error = get_players()

        self.options = []

        for player in self.players:
            self.options.append({
                "type": "player",
                "label": player["username"],
                "player": player
            })

        self.options.append({
            "type": "register",
            "label": "+ CREATE NEW PLAYER"
        })

        self.options.append({
            "type": "guest",
            "label": "PLAY AS GUEST"
        })

        self.selected_index = min(
            self.selected_index,
            len(self.options) - 1
        )

        if error:
            self.message = error
            self.message_color = RED

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

        if self.logged_in:
            self.draw_success_screen()
        else:
            self.draw_login_screen()

        pygame.display.flip()

    def draw_login_screen(self):
        self.draw_text(
            "SELECT YOUR PLAYER",
            self.font,
            WHITE,
            (WIDTH // 2, 135)
        )

        self.draw_text(
            f"{len(self.players)} SAVED PLAYER(S)",
            self.small_font,
            GRAY,
            (WIDTH // 2, 175)
        )

        self.clickable_rects = []

        start = max(
            0,
            self.selected_index - VISIBLE_ROWS + 1
        )

        end = min(
            start + VISIBLE_ROWS,
            len(self.options)
        )

        for visible_index, index in enumerate(range(start, end)):
            option = self.options[index]

            y = LIST_TOP + visible_index * (
                ROW_HEIGHT + ROW_GAP
            )

            rect = pygame.Rect(
                LIST_X,
                y,
                LIST_WIDTH,
                ROW_HEIGHT
            )

            is_selected = index == self.selected_index
            color = SELECTED if is_selected else PANEL

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

            label = option["label"]

            if option["type"] == "player":
                label = "PLAYER: " + label

            self.draw_text(
                label,
                self.font,
                WHITE,
                rect.center
            )

            self.clickable_rects.append((rect, index))

        if len(self.options) > VISIBLE_ROWS:
            self.draw_text(
                "UP / DOWN TO SCROLL",
                self.small_font,
                GRAY,
                (WIDTH // 2, 592)
            )

        if self.message:
            self.draw_text(
                self.message,
                self.small_font,
                self.message_color,
                (WIDTH // 2, 625)
            )

        self.draw_text(
            "Arrow Keys / 8 & 2: Move",
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

    # ------------------------------------
    # SUCCESS SCREEN
    # ------------------------------------

    def draw_success_screen(self):
        username = self.active_player["username"]

        self.draw_text(
            "WELCOME!",
            self.title_font,
            GREEN,
            (WIDTH // 2, 230)
        )

        self.draw_text(
            username,
            self.title_font,
            WHITE,
            (WIDTH // 2, 310)
        )

        self.draw_text(
            "Player selected successfully!",
            self.font,
            CYAN,
            (WIDTH // 2, 390)
        )

        self.draw_text(
            "Your arcade session has been saved.",
            self.small_font,
            GRAY,
            (WIDTH // 2, 445)
        )

        self.draw_text(
            "Opening main menu...",
            self.small_font,
            WHITE,
            (WIDTH // 2, 560)
        )

    # ------------------------------------
    # NAVIGATION
    # ------------------------------------

    def move_selection(self, direction):
        if self.logged_in:
            return

        self.selected_index = (
            self.selected_index + direction
        ) % len(self.options)

        self.message = ""

    def choose_option(self):
        if self.logged_in:
            return

        option = self.options[self.selected_index]

        if option["type"] == "player":
            self.select_player(option["player"])

        elif option["type"] == "register":
            self.open_registration()

        elif option["type"] == "guest":
            self.select_guest()

    # ------------------------------------
    # ACCOUNT SELECTION
    # ------------------------------------

    def select_player(self, player):
        success, message, session = player_backend.login_player(
            player["id"]
        )

        if success:
            self.active_player = session
            self.logged_in = True
            self.success_time = pygame.time.get_ticks()

        else:
            self.message = message
            self.message_color = RED

    def select_guest(self):
        success, message, session = player_backend.login_guest()

        if success:
            self.active_player = session
            self.logged_in = True
            self.success_time = pygame.time.get_ticks()

        else:
            self.message = message
            self.message_color = RED

    # ------------------------------------
    # OPEN REGISTRATION
    # ------------------------------------

    def open_registration(self):
        if not REGISTER_PATH.exists():
            self.message = "register.py was not found."
            self.message_color = RED
            return

        try:
            pygame.display.iconify()

            subprocess.run(
                [sys.executable, str(REGISTER_PATH)],
                check=True
            )

            self.refresh_players()
            self.message = "Player list updated."
            self.message_color = GREEN

        except (OSError, subprocess.CalledProcessError):
            self.message = "Could not open registration."
            self.message_color = RED

        finally:
            self.screen = pygame.display.set_mode(
                (WIDTH, HEIGHT)
            )
            pygame.display.set_caption("IUP Arcade - Login")
            pygame.event.clear()

    # ------------------------------------
    # JOYSTICK
    # ------------------------------------

    def joystick_move(self, direction):
        now = pygame.time.get_ticks()

        if now - self.last_joystick_move >= self.joystick_delay:
            self.move_selection(direction)
            self.last_joystick_move = now

    # ------------------------------------
    # EVENTS
    # ------------------------------------

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                key = event.key

                if key == pygame.K_ESCAPE:
                    self.running = False

                elif not self.logged_in:

                    if key in UP_KEYS:
                        self.move_selection(-1)

                    elif key in DOWN_KEYS:
                        self.move_selection(1)

                    elif key in SELECT_KEYS:
                        self.choose_option()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not self.logged_in:

                    for rect, index in self.clickable_rects:
                        if rect.collidepoint(event.pos):
                            self.selected_index = index
                            self.choose_option()
                            break

            elif event.type == pygame.JOYHATMOTION:
                if not self.logged_in:
                    dx, dy = event.value

                    if dy > 0:
                        self.joystick_move(-1)

                    elif dy < 0:
                        self.joystick_move(1)

            elif event.type == pygame.JOYAXISMOTION:
                if not self.logged_in and event.axis == 1:

                    if event.value > 0.8:
                        self.joystick_move(1)

                    elif event.value < -0.8:
                        self.joystick_move(-1)

            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:
                    self.choose_option()

                elif event.button == 1:
                    self.running = False

    # ------------------------------------
    # MAIN LOOP
    # ------------------------------------

    def run(self):
        while self.running:
            self.handle_events()

            if self.logged_in and self.success_time is not None:
                elapsed = (
                    pygame.time.get_ticks() - self.success_time
                )

                if elapsed >= SUCCESS_DELAY:
                    self.running = False

            if self.running:
                self.draw()
                self.clock.tick(FPS)

        pygame.quit()


# ----------------------------------------
# START PROGRAM
# ----------------------------------------

if __name__ == "__main__":
    login = LoginScreen()
    login.run()

    # main.py uses --select-only when switching players.
    # In that case, return to the existing main menu.
    selection_only = "--select-only" in sys.argv

    if login.logged_in and not selection_only:

        if MAIN_PATH.exists():
            subprocess.run(
                [sys.executable, str(MAIN_PATH)],
                cwd=str(PROJECT_DIR),
                check=False
            )

        else:
            print("Could not find main.py.")

    sys.exit(0)