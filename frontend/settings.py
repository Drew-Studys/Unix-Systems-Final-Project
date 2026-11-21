
import json
import sys
from pathlib import Path

import pygame


# ----------------------------------------
# CONFIGURATION
# ----------------------------------------

WIDTH = 960
HEIGHT = 700
FPS = 60

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
SETTINGS_PATH = DATA_DIR / "settings.json"

BACKGROUND = (15, 23, 42)
PANEL = (30, 41, 59)
BUTTON = (51, 65, 85)
SELECTED = (37, 99, 235)

WHITE = (255, 255, 255)
GRAY = (148, 163, 184)
CYAN = (103, 232, 249)
GREEN = (74, 222, 128)
RED = (248, 113, 113)

UP_KEYS = (pygame.K_UP, pygame.K_8, pygame.K_KP8)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_2, pygame.K_KP2)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_4, pygame.K_KP4)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_6, pygame.K_KP6)

SELECT_KEYS = (
    pygame.K_RETURN,
    pygame.K_KP_ENTER,
    pygame.K_5,
    pygame.K_KP5,
)

DEFAULT_SETTINGS = {
    "menu_volume": 70,
    "sound_effects": True,
    "show_control_hints": True,
    "fullscreen": False,
}

MENU_ITEMS = [
    "Menu Volume",
    "Sound Effects",
    "Show Control Hints",
    "Fullscreen",
    "Reset to Defaults",
    "Back",
]


# ----------------------------------------
# SETTINGS FILE FUNCTIONS
# ----------------------------------------

def load_settings():
    """
    Load saved settings.

    If the file does not exist or is invalid,
    return the default settings.
    """

    settings = DEFAULT_SETTINGS.copy()

    if not SETTINGS_PATH.exists():
        return settings

    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as file:
            saved = json.load(file)

        if not isinstance(saved, dict):
            return settings

        volume = saved.get("menu_volume")

        if type(volume) is int and 0 <= volume <= 100:
            settings["menu_volume"] = volume

        for name in (
            "sound_effects",
            "show_control_hints",
            "fullscreen",
        ):
            value = saved.get(name)

            if type(value) is bool:
                settings[name] = value

    except (OSError, ValueError, TypeError):
        print("Could not read settings. Using defaults.")

    return settings


def save_settings(settings):
    """
    Save preferences to data/settings.json.

    Use a temporary file to avoid replacing
    the existing settings with partial JSON.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    temporary_path = SETTINGS_PATH.with_suffix(".tmp")

    try:
        with open(
            temporary_path, "w", encoding="utf-8"
        ) as file:
            json.dump(settings, file, indent=4)

        temporary_path.replace(SETTINGS_PATH)
        return True

    except OSError as error:
        print("Could not save settings:", error)
        return False


# ----------------------------------------
# SETTINGS SCREEN
# ----------------------------------------

class SettingsScreen:

    def __init__(self):
        pygame.init()
        pygame.joystick.init()

        self.clock = pygame.time.Clock()
        self.settings = load_settings()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

        pygame.display.set_caption(
            "IUP Arcade - Settings"
        )

        self.title_font = pygame.font.SysFont(
            "arial", 50, bold=True
        )

        self.heading_font = pygame.font.SysFont(
            "arial", 30, bold=True
        )

        self.font = pygame.font.SysFont(
            "arial", 23, bold=True
        )

        self.small_font = pygame.font.SysFont(
            "arial", 19
        )

        self.selected_index = 0
        self.running = True

        self.status = "Changes are saved automatically."
        self.status_color = GRAY

        self.menu_rectangles = []

        self.last_joystick_move = 0
        self.joystick_delay = 180

        self.joysticks = []

        for index in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(index)
            joystick.init()
            self.joysticks.append(joystick)

        if self.settings["fullscreen"]:
            self.apply_fullscreen()

    # ------------------------------------
    # DISPLAY MODE
    # ------------------------------------

    def apply_fullscreen(self):
        """
        Apply fullscreen in this window.

        Other frontend screens will use this
        saved preference after integration.
        """

        try:
            flags = (
                pygame.FULLSCREEN
                if self.settings["fullscreen"]
                else 0
            )

            self.screen = pygame.display.set_mode(
                (WIDTH, HEIGHT), flags
            )

            return True

        except pygame.error as error:
            print("Display mode error:", error)

            self.settings["fullscreen"] = False

            self.screen = pygame.display.set_mode(
                (WIDTH, HEIGHT)
            )

            self.status = "Fullscreen not supported."
            self.status_color = RED

            return False

    # ------------------------------------
    # SAVE CHANGES
    # ------------------------------------

    def persist_settings(self):
        if save_settings(self.settings):
            self.status = "Settings saved successfully."
            self.status_color = GREEN
        else:
            self.status = "Unable to save settings."
            self.status_color = RED

    # ------------------------------------
    # DRAWING FUNCTIONS
    # ------------------------------------

    def draw_text(self, text, font, color, center):
        surface = font.render(str(text), True, color)
        rect = surface.get_rect(center=center)
        self.screen.blit(surface, rect)

    def draw_background(self):
        self.screen.fill(BACKGROUND)

        border = pygame.Rect(
            35, 35, WIDTH - 70, HEIGHT - 70
        )

        pygame.draw.rect(
            self.screen,
            PANEL,
            border,
            3,
            border_radius=15
        )

    def draw_header(self):
        self.draw_text(
            "IUP ARCADE",
            self.title_font,
            CYAN,
            (WIDTH // 2, 67)
        )

        self.draw_text(
            "SETTINGS",
            self.heading_font,
            WHITE,
            (WIDTH // 2, 127)
        )

        pygame.draw.line(
            self.screen,
            CYAN,
            (150, 168),
            (810, 168),
            2
        )

    def get_option_value(self, index):

        if index == 0:
            return f"{self.settings['menu_volume']}%"

        if index == 1:
            return (
                "ON"
                if self.settings["sound_effects"]
                else "OFF"
            )

        if index == 2:
            return (
                "ON"
                if self.settings["show_control_hints"]
                else "OFF"
            )

        if index == 3:
            return (
                "ON"
                if self.settings["fullscreen"]
                else "OFF"
            )

        return ""

    def draw_options(self):
        self.menu_rectangles = []

        for index, name in enumerate(MENU_ITEMS):

            y = 204 + index * 63

            rect = pygame.Rect(
                150, y, 660, 55
            )

            selected = index == self.selected_index

            color = SELECTED if selected else PANEL

            pygame.draw.rect(
                self.screen,
                color,
                rect,
                border_radius=10
            )

            if selected:
                pygame.draw.rect(
                    self.screen,
                    CYAN,
                    rect,
                    2,
                    border_radius=10
                )

            name_surface = self.font.render(
                name,
                True,
                WHITE
            )

            self.screen.blit(
                name_surface,
                (175, y + 14)
            )

            option_value = self.get_option_value(index)

            if option_value:
                value_surface = self.font.render(
                    option_value,
                    True,
                    CYAN if selected else GRAY
                )

                value_rect = value_surface.get_rect(
                    right=780,
                    centery=rect.centery
                )

                self.screen.blit(
                    value_surface,
                    value_rect
                )

            self.menu_rectangles.append(rect)

    def draw_footer(self):

        self.draw_text(
            self.status,
            self.small_font,
            self.status_color,
            (WIDTH // 2, 602)
        )

        self.draw_text(
            "8 / 2: Move    4 / 6: Change    5: Select",
            self.small_font,
            GRAY,
            (WIDTH // 2, 650)
        )

        self.draw_text(
            "ESC: Back",
            self.small_font,
            GRAY,
            (WIDTH // 2, 677)
        )

    def draw(self):
        self.draw_background()
        self.draw_header()
        self.draw_options()
        self.draw_footer()

        pygame.display.flip()

    # ------------------------------------
    # NAVIGATION
    # ------------------------------------

    def move_selection(self, direction):
        self.selected_index = (
            self.selected_index + direction
        ) % len(MENU_ITEMS)

    def change_option(self, direction):
        index = self.selected_index

        if index == 0:
            current = self.settings["menu_volume"]

            self.settings["menu_volume"] = max(
                0,
                min(100, current + direction * 10)
            )

            self.persist_settings()

        elif index == 1:
            self.settings["sound_effects"] = (
                not self.settings["sound_effects"]
            )

            self.persist_settings()

        elif index == 2:
            self.settings["show_control_hints"] = (
                not self.settings["show_control_hints"]
            )

            self.persist_settings()

        elif index == 3:
            self.settings["fullscreen"] = (
                not self.settings["fullscreen"]
            )

            if self.apply_fullscreen():
                self.persist_settings()
            else:
                self.persist_settings()

    def select_option(self):

        if self.selected_index <= 3:
            self.change_option(1)

        elif self.selected_index == 4:
            self.reset_settings()

        elif self.selected_index == 5:
            self.running = False

    def reset_settings(self):
        self.settings = DEFAULT_SETTINGS.copy()

        self.apply_fullscreen()
        self.persist_settings()

        if self.status_color == GREEN:
            self.status = "Default settings restored."

    def joystick_move(self, direction):
        now = pygame.time.get_ticks()

        if (
            now - self.last_joystick_move
            >= self.joystick_delay
        ):
            self.move_selection(direction)
            self.last_joystick_move = now

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
                    self.move_selection(-1)

                elif key in DOWN_KEYS:
                    self.move_selection(1)

                elif key in LEFT_KEYS:
                    self.change_option(-1)

                elif key in RIGHT_KEYS:
                    self.change_option(1)

                elif key in SELECT_KEYS:
                    self.select_option()

            elif event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:
                    for index, rect in enumerate(
                        self.menu_rectangles
                    ):
                        if rect.collidepoint(event.pos):
                            self.selected_index = index
                            self.select_option()
                            break

            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.move_selection(-1)
                elif event.y < 0:
                    self.move_selection(1)

            elif event.type == pygame.JOYHATMOTION:
                dx, dy = event.value

                if dy > 0:
                    self.joystick_move(-1)
                elif dy < 0:
                    self.joystick_move(1)

                elif dx != 0:
                    self.change_option(dx)

            elif event.type == pygame.JOYAXISMOTION:

                if event.axis == 1:
                    if event.value > 0.8:
                        self.joystick_move(1)
                    elif event.value < -0.8:
                        self.joystick_move(-1)

                elif event.axis == 0:
                    now = pygame.time.get_ticks()

                    if (
                        now - self.last_joystick_move
                        >= self.joystick_delay
                    ):
                        if event.value > 0.8:
                            self.change_option(1)
                        elif event.value < -0.8:
                            self.change_option(-1)

                        self.last_joystick_move = now

            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:
                    self.select_option()

                elif event.button == 1:
                    self.running = False

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
    screen = SettingsScreen()
    screen.run()
    sys.exit(0)
