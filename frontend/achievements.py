
import pygame
import sys
import sqlite3
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

BACKGROUND = (15, 23, 42)
PANEL = (30, 41, 59)
BUTTON = (51, 65, 85)
SELECTED = (37, 99, 235)

WHITE = (255, 255, 255)
GRAY = (148, 163, 184)
CYAN = (103, 232, 249)
GREEN = (74, 222, 128)
GOLD = (250, 204, 21)
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

BACK_KEYS = (
    pygame.K_ESCAPE,
    pygame.K_RETURN,
    pygame.K_KP_ENTER,
    pygame.K_5,
    pygame.K_KP5
)

VISIBLE_ACHIEVEMENTS = 5

# ----------------------------------------
# ACHIEVEMENT DEFINITIONS
# ----------------------------------------

# These are the available achievements.
#
# An achievement is only marked unlocked
# when it exists in the SQLite database.
#
# Automatic unlocking will be added later
# when we integrate game score tracking.

ACHIEVEMENTS = [
    {
        "name": "First Steps",
        "description": "Complete your first game."
    },
    {
        "name": "Getting Started",
        "description": "Complete 10 games."
    },
    {
        "name": "Arcade Veteran",
        "description": "Complete 50 games."
    },
    {
        "name": "High Scorer",
        "description": "Earn 1,000 points in one game."
    },
    {
        "name": "Score Master",
        "description": "Earn 10,000 points in one game."
    },
    {
        "name": "Champion",
        "description": "Reach first place on a leaderboard."
    }
]


# ----------------------------------------
# DATABASE FUNCTIONS
# ----------------------------------------

def get_current_player():
    """
    Load the currently selected player
    from our player management backend.
    """

    try:
        return players.get_active_player()

    except (sqlite3.Error, OSError):
        return None


def get_unlocked_achievements(player):
    """
    Retrieve the player's achievements
    from the SQLite database.

    Guests do not have saved achievements.
    """

    if player is None or player.get("guest", False):
        return {}

    player_id = player.get("id")

    if player_id is None:
        return {}

    try:
        records = database.get_player_achievements(
            player_id
        )

        return {
            record["achievement_name"]: record["unlocked_at"]
            for record in records
        }

    except sqlite3.Error as error:
        print("Error loading achievements:", error)
        return {}


# ----------------------------------------
# ACHIEVEMENTS SCREEN
# ----------------------------------------

class AchievementsScreen:

    def __init__(self):

        pygame.init()
        pygame.joystick.init()

        database.initialize_database()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

        pygame.display.set_caption(
            "IUP Arcade - Achievements"
        )

        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont(
            "arial", 50, bold=True
        )

        self.heading_font = pygame.font.SysFont(
            "arial", 29, bold=True
        )

        self.font = pygame.font.SysFont(
            "arial", 24, bold=True
        )

        self.small_font = pygame.font.SysFont(
            "arial", 19
        )

        self.tiny_font = pygame.font.SysFont(
            "arial", 16
        )

        self.player = get_current_player()

        self.unlocked = get_unlocked_achievements(
            self.player
        )

        self.scroll_position = 0
        self.running = True

        self.back_button = pygame.Rect(
            330, 595, 300, 55
        )

        self.last_joystick_move = 0
        self.joystick_delay = 180

        self.joysticks = []

        for index in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(index)
            joystick.init()
            self.joysticks.append(joystick)

    # ------------------------------------
    # REFRESH ACHIEVEMENTS
    # ------------------------------------

    def refresh_data(self):

        self.player = get_current_player()

        self.unlocked = get_unlocked_achievements(
            self.player
        )

    # ------------------------------------
    # DRAWING HELPERS
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

    def draw_background(self):

        self.screen.fill(BACKGROUND)

        border = pygame.Rect(
            35,
            35,
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

        self.draw_text(
            "ACHIEVEMENTS",
            self.heading_font,
            WHITE,
            (WIDTH // 2, 120)
        )

        if self.player is None:
            player_name = "NO PLAYER SELECTED"

        else:
            player_name = self.player["username"]

        self.draw_text(
            f"PLAYER: {player_name}",
            self.small_font,
            GRAY,
            (WIDTH // 2, 157)
        )

    # ------------------------------------
    # PROGRESS BAR
    # ------------------------------------

    def draw_progress(self):

        total = len(ACHIEVEMENTS)

        unlocked_count = sum(
            1
            for achievement in ACHIEVEMENTS
            if achievement["name"] in self.unlocked
        )

        progress = (
            unlocked_count / total
            if total > 0
            else 0
        )

        self.draw_text(
            f"{unlocked_count} / {total} UNLOCKED",
            self.small_font,
            CYAN,
            (WIDTH // 2, 190)
        )

        bar_background = pygame.Rect(
            190, 211, 580, 9
        )

        pygame.draw.rect(
            self.screen,
            BUTTON,
            bar_background,
            border_radius=5
        )

        filled_width = int(
            bar_background.width * progress
        )

        if filled_width > 0:
            filled_rect = pygame.Rect(
                bar_background.x,
                bar_background.y,
                filled_width,
                bar_background.height
            )

            pygame.draw.rect(
                self.screen,
                GREEN,
                filled_rect,
                border_radius=5
            )

    # ------------------------------------
    # ACHIEVEMENT CARDS
    # ------------------------------------

    def draw_achievement_cards(self):

        end = min(
            self.scroll_position
            + VISIBLE_ACHIEVEMENTS,
            len(ACHIEVEMENTS)
        )

        visible = ACHIEVEMENTS[
            self.scroll_position:end
        ]

        for index, achievement in enumerate(visible):

            y = 239 + index * 66

            rect = pygame.Rect(
                135, y, 690, 60
            )

            unlocked = (
                achievement["name"]
                in self.unlocked
            )

            pygame.draw.rect(
                self.screen,
                PANEL,
                rect,
                border_radius=10
            )

            if unlocked:
                pygame.draw.rect(
                    self.screen,
                    GREEN,
                    rect,
                    2,
                    border_radius=10
                )

            # Status symbol
            symbol_rect = pygame.Rect(
                151, y + 10, 40, 40
            )

            pygame.draw.rect(
                self.screen,
                (22, 78, 99) if unlocked else BUTTON,
                symbol_rect,
                border_radius=8
            )

            self.draw_text(
                "✓" if unlocked else "X",
                self.font,
                GREEN if unlocked else GRAY,
                symbol_rect.center
            )

            # Achievement name
            name_surface = self.font.render(
                achievement["name"],
                True,
                WHITE
            )

            self.screen.blit(
                name_surface,
                (208, y + 7)
            )

            # Achievement description
            description_surface = (
                self.small_font.render(
                    achievement["description"],
                    True,
                    GRAY
                )
            )

            self.screen.blit(
                description_surface,
                (208, y + 35)
            )

            # Unlock status
            status = (
                "UNLOCKED"
                if unlocked
                else "LOCKED"
            )

            self.draw_text(
                status,
                self.tiny_font,
                GREEN if unlocked else GRAY,
                (757, y + 30)
            )

        # Scroll indicator
        if len(ACHIEVEMENTS) > VISIBLE_ACHIEVEMENTS:

            self.draw_text(
                f"{self.scroll_position + 1}-"
                f"{end} OF {len(ACHIEVEMENTS)}",
                self.tiny_font,
                GRAY,
                (WIDTH // 2, 578)
            )

    # ------------------------------------
    # BACK BUTTON
    # ------------------------------------

    def draw_back_button(self):

        pygame.draw.rect(
            self.screen,
            SELECTED,
            self.back_button,
            border_radius=10
        )

        pygame.draw.rect(
            self.screen,
            CYAN,
            self.back_button,
            2,
            border_radius=10
        )

        self.draw_text(
            "BACK",
            self.font,
            WHITE,
            self.back_button.center
        )

    # ------------------------------------
    # DRAW SCREEN
    # ------------------------------------

    def draw(self):

        self.draw_background()
        self.draw_header()
        self.draw_progress()
        self.draw_achievement_cards()
        self.draw_back_button()

        self.draw_text(
            "8 / 2: Scroll    5: Back    ESC: Back",
            self.small_font,
            GRAY,
            (WIDTH // 2, 670)
        )

        pygame.display.flip()

    # ------------------------------------
    # SCROLLING
    # ------------------------------------

    def move_selection(self, direction):

        max_scroll = max(
            0,
            len(ACHIEVEMENTS)
            - VISIBLE_ACHIEVEMENTS
        )

        self.scroll_position = max(
            0,
            min(
                self.scroll_position + direction,
                max_scroll
            )
        )

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

                if event.key in BACK_KEYS:
                    self.running = False

                elif event.key in UP_KEYS:
                    self.move_selection(-1)

                elif event.key in DOWN_KEYS:
                    self.move_selection(1)

                elif event.key == pygame.K_r:
                    self.refresh_data()

            elif event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:

                    if self.back_button.collidepoint(
                        event.pos
                    ):
                        self.running = False

            elif event.type == pygame.MOUSEWHEEL:

                self.move_selection(-event.y)

            elif event.type == pygame.JOYHATMOTION:

                dx, dy = event.value

                if dy > 0:
                    self.joystick_move(-1)

                elif dy < 0:
                    self.joystick_move(1)

            elif event.type == pygame.JOYAXISMOTION:

                if event.axis == 1:

                    if event.value > 0.8:
                        self.joystick_move(1)

                    elif event.value < -0.8:
                        self.joystick_move(-1)

            elif event.type == pygame.JOYBUTTONDOWN:

                if event.button in (0, 1):
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

    achievements = AchievementsScreen()
    achievements.run()

    sys.exit(0)
