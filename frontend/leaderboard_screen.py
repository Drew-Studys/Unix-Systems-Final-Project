
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

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_DIR / "data" / "arcade.db"

# Match existing frontend colors
BACKGROUND = (15, 23, 42)
PANEL = (30, 41, 59)
BUTTON = (51, 65, 85)
SELECTED = (37, 99, 235)
WHITE = (255, 255, 255)
GRAY = (148, 163, 184)
CYAN = (103, 232, 249)
GREEN = (74, 222, 128)
RED = (248, 113, 113)
GOLD = (250, 204, 21)
SILVER = (203, 213, 225)
BRONZE = (205, 127, 50)

# Keyboard / arcade controls
UP_KEYS = (pygame.K_UP, pygame.K_8, pygame.K_KP8)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_2, pygame.K_KP2)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_4, pygame.K_KP4)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_6, pygame.K_KP6)

SELECT_KEYS = (
    pygame.K_RETURN,
    pygame.K_KP_ENTER,
    pygame.K_5,
    pygame.K_KP5
)

VISIBLE_GAMES = 5
VISIBLE_SCORES = 6

# ----------------------------------------
# DATABASE FUNCTIONS
# ----------------------------------------

def table_exists(conn, table_name):
    result = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,)
    ).fetchone()

    return result is not None


def get_games():
    """
    Retrieve games from the SQLite database.

    Expected table:
        games(id, game_name)
    """

    if not DATABASE_PATH.exists():
        return [], "No games have been added yet."

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:

            if not table_exists(conn, "games"):
                return [], "No games have been added yet."

            rows = conn.execute(
                """
                SELECT id, game_name
                FROM games
                ORDER BY game_name COLLATE NOCASE
                """
            ).fetchall()

        games = [
            {"id": row[0], "name": row[1]}
            for row in rows
        ]

        return games, ""

    except sqlite3.Error:
        return [], "Unable to load games from database."


def get_leaderboard(game_id):
    """
    Retrieve each player's best score for a game.

    Expected tables:
        players(id, username)
        scores(player_id, game_id, score)
    """

    if not DATABASE_PATH.exists():
        return [], "Score database not found."

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:

            required_tables = ["players", "games", "scores"]

            for table in required_tables:
                if not table_exists(conn, table):
                    return [], "No scores recorded for this game yet."

            rows = conn.execute(
                """
                SELECT
                    players.id,
                    players.username,
                    MAX(scores.score) AS best_score
                FROM scores
                JOIN players
                    ON scores.player_id = players.id
                WHERE scores.game_id = ?
                GROUP BY players.id, players.username
                ORDER BY
                    best_score DESC,
                    players.username COLLATE NOCASE ASC
                """,
                (game_id,)
            ).fetchall()

        leaderboard = []

        for index, row in enumerate(rows):
            leaderboard.append({
                "rank": index + 1,
                "player_id": row[0],
                "username": row[1],
                "score": row[2]
            })

        return leaderboard, ""

    except sqlite3.Error:
        return [], "Unable to load leaderboard."


# ----------------------------------------
# LEADERBOARD SCREEN
# ----------------------------------------

class LeaderboardScreen:

    def __init__(self):
        pygame.init()
        pygame.joystick.init()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

        pygame.display.set_caption(
            "IUP Arcade - Leaderboards"
        )

        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont(
            "arial", 52, bold=True
        )

        self.heading_font = pygame.font.SysFont(
            "arial", 30, bold=True
        )

        self.font = pygame.font.SysFont(
            "arial", 25, bold=True
        )

        self.small_font = pygame.font.SysFont(
            "arial", 20
        )

        self.games = []
        self.game_error = ""

        self.leaderboard = []
        self.score_error = ""

        self.selected_game_index = 0
        self.game_scroll = 0
        self.score_scroll = 0

        # "games" or "scores"
        self.mode = "games"
        self.running = True

        self.clickable_games = []

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

        self.refresh_games()

    # ------------------------------------
    # LOAD DATA
    # ------------------------------------

    def refresh_games(self):
        self.games, self.game_error = get_games()

        if self.games:
            self.selected_game_index = min(
                self.selected_game_index,
                len(self.games) - 1
            )
        else:
            self.selected_game_index = 0

        self.game_scroll = 0

    def select_game(self):
        if not self.games:
            return

        game = self.games[self.selected_game_index]

        self.leaderboard, self.score_error = get_leaderboard(
            game["id"]
        )

        self.score_scroll = 0
        self.mode = "scores"

    # ------------------------------------
    # DRAWING HELPERS
    # ------------------------------------

    def draw_text(self, text, font, color, center):
        surface = font.render(str(text), True, color)
        rect = surface.get_rect(center=center)
        self.screen.blit(surface, rect)

    def draw_fitted_text(
        self, text, font, color, x, center_y, max_width
    ):
        text = str(text)

        if font.size(text)[0] > max_width:
            while (
                len(text) > 1
                and font.size(text + "...")[0] > max_width
            ):
                text = text[:-1]

            text += "..."

        surface = font.render(text, True, color)

        self.screen.blit(
            surface,
            (x, center_y - surface.get_height() // 2)
        )

    def draw_background(self):
        self.screen.fill(BACKGROUND)

        border = pygame.Rect(
            35, 35, WIDTH - 70, HEIGHT - 70
        )

        pygame.draw.rect(
            self.screen, PANEL, border, 3,
            border_radius=15
        )

    def draw_header(self):
        self.draw_text(
            "IUP ARCADE",
            self.title_font,
            CYAN,
            (WIDTH // 2, 70)
        )

        self.draw_text(
            "LEADERBOARDS",
            self.heading_font,
            WHITE,
            (WIDTH // 2, 135)
        )

        pygame.draw.line(
            self.screen, CYAN,
            (130, 175), (830, 175), 2
        )

    def draw_back_button(self, label):
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
            label,
            self.font,
            WHITE,
            self.back_button.center
        )

    # ------------------------------------
    # GAME SELECTION MENU
    # ------------------------------------

    def draw_game_menu(self):
        self.clickable_games = []

        self.draw_text(
            "SELECT A GAME",
            self.font,
            WHITE,
            (WIDTH // 2, 215)
        )

        if not self.games:
            message = (
                self.game_error
                or "No games have been added yet."
            )

            self.draw_text(
                message,
                self.small_font,
                GRAY,
                (WIDTH // 2, 345)
            )

            self.draw_text(
                "Games will appear when added to SQLite.",
                self.small_font,
                CYAN,
                (WIDTH // 2, 385)
            )

        else:
            # Keep highlighted game visible
            if self.selected_game_index < self.game_scroll:
                self.game_scroll = self.selected_game_index

            if (
                self.selected_game_index
                >= self.game_scroll + VISIBLE_GAMES
            ):
                self.game_scroll = (
                    self.selected_game_index - VISIBLE_GAMES + 1
                )

            end = min(
                self.game_scroll + VISIBLE_GAMES,
                len(self.games)
            )

            for visible_index, index in enumerate(
                range(self.game_scroll, end)
            ):
                game = self.games[index]

                y = 255 + visible_index * 62

                rect = pygame.Rect(
                    190, y, 580, 54
                )

                selected = (
                    index == self.selected_game_index
                )

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

                self.draw_fitted_text(
                    game["name"],
                    self.font,
                    WHITE,
                    rect.x + 25,
                    rect.centery,
                    rect.width - 50
                )

                self.clickable_games.append(
                    (rect, index)
                )

            if len(self.games) > VISIBLE_GAMES:
                self.draw_text(
                    f"GAME {self.selected_game_index + 1}"
                    f" OF {len(self.games)}",
                    self.small_font,
                    GRAY,
                    (WIDTH // 2, 575)
                )

        self.draw_back_button("BACK")

        self.draw_text(
            "8 / 2: Move   5: Select   Mouse: Click",
            self.small_font,
            GRAY,
            (WIDTH // 2, 670)
        )

    # ------------------------------------
    # SCORE RANKINGS
    # ------------------------------------

    def draw_score_menu(self):
        if not self.games:
            return

        game = self.games[self.selected_game_index]

        self.draw_fitted_text(
            game["name"].upper(),
            self.font,
            CYAN,
            190,
            210,
            580
        )

        # Column headings
        self.draw_text(
            "RANK",
            self.small_font,
            GRAY,
            (245, 255)
        )

        self.draw_text(
            "PLAYER",
            self.small_font,
            GRAY,
            (475, 255)
        )

        self.draw_text(
            "BEST SCORE",
            self.small_font,
            GRAY,
            (715, 255)
        )

        if not self.leaderboard:
            self.draw_text(
                self.score_error
                or "No scores recorded for this game yet.",
                self.small_font,
                GRAY,
                (WIDTH // 2, 375)
            )

        else:
            visible_scores = self.leaderboard[
                self.score_scroll:
                self.score_scroll + VISIBLE_SCORES
            ]

            for visible_index, player in enumerate(
                visible_scores
            ):
                y = 290 + visible_index * 47

                rect = pygame.Rect(
                    180, y, 600, 42
                )

                pygame.draw.rect(
                    self.screen,
                    PANEL,
                    rect,
                    border_radius=8
                )

                rank = player["rank"]

                if rank == 1:
                    rank_color = GOLD
                elif rank == 2:
                    rank_color = SILVER
                elif rank == 3:
                    rank_color = BRONZE
                else:
                    rank_color = WHITE

                self.draw_text(
                    f"#{rank}",
                    self.small_font,
                    rank_color,
                    (245, y + 21)
                )

                self.draw_fitted_text(
                    player["username"],
                    self.small_font,
                    WHITE,
                    330,
                    y + 21,
                    270
                )

                score = player["score"]

                if isinstance(score, (int, float)):
                    score_text = f"{score:,}"
                else:
                    score_text = str(score)

                self.draw_text(
                    score_text,
                    self.small_font,
                    CYAN,
                    (710, y + 21)
                )

            if len(self.leaderboard) > VISIBLE_SCORES:
                self.draw_text(
                    f"Showing {self.score_scroll + 1}-"
                    f"{self.score_scroll + len(visible_scores)}"
                    f" of {len(self.leaderboard)} players",
                    self.small_font,
                    GRAY,
                    (WIDTH // 2, 582)
                )

        self.draw_back_button("BACK TO GAMES")

        self.draw_text(
            "8 / 2: Scroll   5: Back   ESC: Back",
            self.small_font,
            GRAY,
            (WIDTH // 2, 670)
        )

    # ------------------------------------
    # MAIN DRAW
    # ------------------------------------

    def draw(self):
        self.draw_background()
        self.draw_header()

        if self.mode == "games":
            self.draw_game_menu()
        else:
            self.draw_score_menu()

        pygame.display.flip()

    # ------------------------------------
    # NAVIGATION
    # ------------------------------------

    def move_selection(self, direction):
        if self.mode == "games":

            if self.games:
                self.selected_game_index = (
                    self.selected_game_index + direction
                ) % len(self.games)

        else:
            max_scroll = max(
                0,
                len(self.leaderboard) - VISIBLE_SCORES
            )

            self.score_scroll = max(
                0,
                min(
                    self.score_scroll + direction,
                    max_scroll
                )
            )

    def select_option(self):
        if self.mode == "games":
            self.select_game()
        else:
            self.mode = "games"

    def go_back(self):
        if self.mode == "scores":
            self.mode = "games"
        else:
            self.running = False

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
                    self.go_back()

                elif key in UP_KEYS:
                    self.move_selection(-1)

                elif key in DOWN_KEYS:
                    self.move_selection(1)

                elif key in LEFT_KEYS:
                    if self.mode == "games":
                        self.move_selection(-1)

                elif key in RIGHT_KEYS:
                    if self.mode == "games":
                        self.move_selection(1)

                elif key in SELECT_KEYS:
                    self.select_option()

            elif event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:

                    if self.back_button.collidepoint(event.pos):
                        self.go_back()

                    elif self.mode == "games":
                        for rect, index in self.clickable_games:
                            if rect.collidepoint(event.pos):
                                self.selected_game_index = index
                                self.select_game()
                                break

            elif event.type == pygame.MOUSEWHEEL:
                if self.mode == "scores":
                    self.move_selection(-event.y)

            elif event.type == pygame.JOYHATMOTION:
                dx, dy = event.value

                if dy > 0:
                    self.joystick_move(-1)
                elif dy < 0:
                    self.joystick_move(1)

                elif dx and self.mode == "games":
                    self.joystick_move(dx)

            elif event.type == pygame.JOYAXISMOTION:

                if event.axis == 1:
                    if event.value > 0.8:
                        self.joystick_move(1)
                    elif event.value < -0.8:
                        self.joystick_move(-1)

                elif event.axis == 0 and self.mode == "games":
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
    leaderboard = LeaderboardScreen()
    leaderboard.run()
    sys.exit(0)
