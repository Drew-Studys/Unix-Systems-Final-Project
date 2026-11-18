
import pygame
import sqlite3
import json
import sys
from pathlib import Path

# ----------------------------------------
# CONFIGURATION
# ----------------------------------------

WIDTH = 960
HEIGHT = 700
FPS = 60

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_DIR / "data" / "arcade.db"
SESSION_PATH = PROJECT_DIR / "data" / "active_player.json"

# Colors - match other arcade screens
BACKGROUND = (15, 23, 42)
PANEL = (30, 41, 59)
BUTTON = (51, 65, 85)
SELECTED = (37, 99, 235)
WHITE = (255, 255, 255)
GRAY = (148, 163, 184)
CYAN = (103, 232, 249)
GREEN = (74, 222, 128)
RED = (248, 113, 113)

# Joystick and keyboard controls
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

VISIBLE_GAMES = 4


# ----------------------------------------
# DATABASE FUNCTIONS
# ----------------------------------------

def get_active_player():
    """Load the player selected through login.py."""

    if not SESSION_PATH.exists():
        return None

    try:
        with open(SESSION_PATH, "r", encoding="utf-8") as file:
            session = json.load(file)

        if not isinstance(session, dict):
            return None

        if session.get("guest") is True:
            return {
                "id": None,
                "username": "GUEST",
                "created_at": None,
                "guest": True
            }

        player_id = session.get("id")

        if type(player_id) is not int:
            return None

        if not DATABASE_PATH.exists():
            return None

        with sqlite3.connect(DATABASE_PATH) as conn:
            row = conn.execute(
                """
                SELECT id, username, created_at
                FROM players
                WHERE id = ?
                """,
                (player_id,)
            ).fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "username": row[1],
            "created_at": row[2],
            "guest": False
        }

    except (
        OSError,
        ValueError,
        TypeError,
        sqlite3.Error
    ):
        return None


def table_exists(conn, table_name):
    """Check whether a table has been created."""

    result = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,)
    ).fetchone()

    return result is not None


def get_player_statistics(player):
    """
    Load statistics from SQLite.

    The games, scores, and achievements tables
    will be created during backend development.

    Until then, return empty statistics.
    """

    statistics = {
        "games_played": 0,
        "achievements": 0,
        "personal_bests": []
    }

    if player is None:
        return statistics

    if player.get("guest"):
        return statistics

    if not DATABASE_PATH.exists():
        return statistics

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:

            # --------------------------------
            # GAME SCORES
            # --------------------------------

            if (
                table_exists(conn, "games")
                and table_exists(conn, "scores")
            ):

                # Count recorded game results
                result = conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM scores
                    WHERE player_id = ?
                    """,
                    (player["id"],)
                ).fetchone()

                statistics["games_played"] = result[0]

                # Get personal best for each game
                rows = conn.execute(
                    """
                    SELECT
                        games.game_name,
                        MAX(scores.score) AS best_score
                    FROM scores
                    JOIN games
                        ON scores.game_id = games.id
                    WHERE scores.player_id = ?
                    GROUP BY games.id, games.game_name
                    ORDER BY games.game_name
                    """,
                    (player["id"],)
                ).fetchall()

                statistics["personal_bests"] = [
                    {
                        "game": row[0],
                        "score": row[1]
                    }
                    for row in rows
                ]

            # --------------------------------
            # ACHIEVEMENTS
            # --------------------------------

            if table_exists(conn, "achievements"):

                result = conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM achievements
                    WHERE player_id = ?
                    """,
                    (player["id"],)
                ).fetchone()

                statistics["achievements"] = result[0]

    except sqlite3.Error as error:
        print("Statistics database error:", error)

    return statistics


# ----------------------------------------
# PROFILE SCREEN
# ----------------------------------------

class ProfileScreen:

    def __init__(self):

        pygame.init()
        pygame.joystick.init()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

        pygame.display.set_caption(
            "IUP Arcade - Player Profile"
        )

        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont(
            "arial", 52, bold=True
        )

        self.heading_font = pygame.font.SysFont(
            "arial", 30, bold=True
        )

        self.font = pygame.font.SysFont(
            "arial", 26, bold=True
        )

        self.small_font = pygame.font.SysFont(
            "arial", 20
        )

        self.player = get_active_player()
        self.statistics = get_player_statistics(self.player)

        self.running = True

        # Personal best scrolling
        self.scroll_offset = 0

        # Back button
        self.back_button = pygame.Rect(
            330, 635, 300, 48
        )

        # Initialize USB joysticks
        self.joysticks = []

        for index in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(index)
            joystick.init()
            self.joysticks.append(joystick)

        self.last_joystick_move = 0
        self.joystick_delay = 180

    # ------------------------------------
    # DRAW TEXT
    # ------------------------------------

    def draw_text(self, text, font, color, center):

        surface = font.render(text, True, color)

        rect = surface.get_rect(center=center)

        self.screen.blit(surface, rect)

    # ------------------------------------
    # DRAW BACKGROUND
    # ------------------------------------

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
    # DRAW HEADER
    # ------------------------------------

    def draw_header(self):

        self.draw_text(
            "IUP ARCADE",
            self.title_font,
            CYAN,
            (WIDTH // 2, 65)
        )

        self.draw_text(
            "PLAYER PROFILE",
            self.heading_font,
            WHITE,
            (WIDTH // 2, 125)
        )

        pygame.draw.line(
            self.screen,
            CYAN,
            (130, 165),
            (830, 165),
            2
        )

    # ------------------------------------
    # PLAYER INFORMATION
    # ------------------------------------

    def draw_player_information(self):

        if self.player is None:

            self.draw_text(
                "NO PLAYER SELECTED",
                self.heading_font,
                RED,
                (WIDTH // 2, 230)
            )

            self.draw_text(
                "Please log in before viewing a profile.",
                self.small_font,
                GRAY,
                (WIDTH // 2, 275)
            )

            return

        username = self.player["username"]

        # Avatar circle
        pygame.draw.circle(
            self.screen,
            PANEL,
            (280, 235),
            48
        )

        pygame.draw.circle(
            self.screen,
            CYAN,
            (280, 235),
            48,
            3
        )

        initial = username[0] if username else "?"

        self.draw_text(
            initial,
            self.title_font,
            CYAN,
            (280, 235)
        )

        # Username
        self.draw_text(
            username,
            self.heading_font,
            WHITE,
            (550, 220)
        )

        # Account creation date
        if self.player.get("guest"):

            member_text = "Guest Session"

        else:

            created = self.player.get("created_at")

            if created:
                member_text = "Member Since: " + str(created)[:10]
            else:
                member_text = "Member Since: Unknown"

        self.draw_text(
            member_text,
            self.small_font,
            GRAY,
            (550, 260)
        )

    # ------------------------------------
    # STATISTIC BOXES
    # ------------------------------------

    def draw_stat_box(self, x, y, title, value):

        rect = pygame.Rect(
            x, y, 190, 76
        )

        pygame.draw.rect(
            self.screen,
            PANEL,
            rect,
            border_radius=10
        )

        pygame.draw.rect(
            self.screen,
            BUTTON,
            rect,
            2,
            border_radius=10
        )

        self.draw_text(
            str(value),
            self.heading_font,
            CYAN,
            (x + 95, y + 28)
        )

        self.draw_text(
            title,
            self.small_font,
            GRAY,
            (x + 95, y + 57)
        )

    def draw_statistics(self):

        if self.player is None:
            return

        stats = self.statistics

        self.draw_stat_box(
            165, 300,
            "GAMES PLAYED",
            stats["games_played"]
        )

        self.draw_stat_box(
            385, 300,
            "ACHIEVEMENTS",
            stats["achievements"]
        )

        self.draw_stat_box(
            605, 300,
            "PERSONAL BESTS",
            len(stats["personal_bests"])
        )

    # ------------------------------------
    # PERSONAL BESTS
    # ------------------------------------

    def draw_personal_bests(self):

        if self.player is None:
            return

        self.draw_text(
            "PERSONAL BESTS BY GAME",
            self.font,
            WHITE,
            (WIDTH // 2, 412)
        )

        bests = self.statistics["personal_bests"]

        if not bests:

            self.draw_text(
                "No game scores recorded yet.",
                self.small_font,
                GRAY,
                (WIDTH // 2, 500)
            )

            self.draw_text(
                "Play a supported game to set a record!",
                self.small_font,
                CYAN,
                (WIDTH // 2, 535)
            )

            return

        visible = bests[
            self.scroll_offset:
            self.scroll_offset + VISIBLE_GAMES
        ]

        for index, game in enumerate(visible):

            y = 440 + index * 46

            rect = pygame.Rect(
                180, y, 600, 40
            )

            pygame.draw.rect(
                self.screen,
                PANEL,
                rect,
                border_radius=8
            )

            game_name = str(game["game"])
            best_score = game["score"]

            # Game names on the left
            name_surface = self.small_font.render(
                game_name, True, WHITE
            )

            # Keep long names inside the row
            if name_surface.get_width() > 360:
                while (
                    len(game_name) > 1
                    and self.small_font.size(
                        game_name + "..."
                    )[0] > 360
                ):
                    game_name = game_name[:-1]

                game_name += "..."

                name_surface = self.small_font.render(
                    game_name, True, WHITE
                )

            self.screen.blit(
                name_surface,
                (200, y + 10)
            )

            # Best score on the right
            if isinstance(best_score, (int, float)):
                score_text = f"{best_score:,}"
            else:
                score_text = str(best_score)

            score_surface = self.small_font.render(
                score_text, True, CYAN
            )

            score_rect = score_surface.get_rect(
                right=760,
                centery=y + 20
            )

            self.screen.blit(
                score_surface,
                score_rect
            )

        if len(bests) > VISIBLE_GAMES:

            self.draw_text(
                f"Showing {self.scroll_offset + 1}-"
                f"{self.scroll_offset + len(visible)} "
                f"of {len(bests)} games",
                self.small_font,
                GRAY,
                (WIDTH // 2, 622)
            )

    # ------------------------------------
    # SCROLLING
    # ------------------------------------

    def scroll_games(self, direction):

        bests = self.statistics["personal_bests"]

        max_offset = max(
            0,
            len(bests) - VISIBLE_GAMES
        )

        self.scroll_offset = max(
            0,
            min(
                self.scroll_offset + direction,
                max_offset
            )
        )

    def joystick_scroll(self, direction):

        now = pygame.time.get_ticks()

        if now - self.last_joystick_move >= self.joystick_delay:

            self.scroll_games(direction)

            self.last_joystick_move = now

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
        self.draw_player_information()
        self.draw_statistics()
        self.draw_personal_bests()
        self.draw_back_button()

        pygame.display.flip()

    # ------------------------------------
    # EVENT HANDLING
    # ------------------------------------

    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    self.running = False

                elif event.key in SELECT_KEYS:
                    self.running = False

                elif event.key in UP_KEYS:
                    self.scroll_games(-1)

                elif event.key in DOWN_KEYS:
                    self.scroll_games(1)

            elif event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:

                    if self.back_button.collidepoint(
                        event.pos
                    ):
                        self.running = False

                elif event.button == 4:
                    self.scroll_games(-1)

                elif event.button == 5:
                    self.scroll_games(1)

            elif event.type == pygame.MOUSEWHEEL:

                self.scroll_games(-event.y)

            elif event.type == pygame.JOYHATMOTION:

                dx, dy = event.value

                if dy > 0:
                    self.joystick_scroll(-1)

                elif dy < 0:
                    self.joystick_scroll(1)

            elif event.type == pygame.JOYAXISMOTION:

                if event.axis == 1:

                    if event.value > 0.8:
                        self.joystick_scroll(1)

                    elif event.value < -0.8:
                        self.joystick_scroll(-1)

            elif event.type == pygame.JOYBUTTONDOWN:

                if event.button == 0:
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

    profile = ProfileScreen()
    profile.run()

    sys.exit(0)
