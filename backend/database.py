
import sqlite3
from pathlib import Path

# ----------------------------------------
# CONFIGURATION
# ----------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
DATABASE_PATH = DATA_DIR / "arcade.db"


# ----------------------------------------
# DATABASE CONNECTION
# ----------------------------------------

def get_connection():
    """
    Connect to our arcade database.

    Enable foreign keys and make database
    rows accessible by column name.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# ----------------------------------------
# DATABASE INITIALIZATION
# ----------------------------------------

def initialize_database():
    """
    Create missing tables without deleting
    existing accounts or saved information.
    """

    with get_connection() as conn:

        # PLAYERS
        # Matches our existing register.py table.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # GAMES
        conn.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_name TEXT NOT NULL UNIQUE COLLATE NOCASE
            )
        """)

        # SCORES
        # Every completed game can create a new score.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                game_id INTEGER NOT NULL,
                score INTEGER NOT NULL
                    CHECK (score >= 0),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (player_id)
                    REFERENCES players(id),

                FOREIGN KEY (game_id)
                    REFERENCES games(id)
            )
        """)

        # ACHIEVEMENTS
        # Stores achievements earned by players.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                achievement_name TEXT NOT NULL,
                unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (player_id)
                    REFERENCES players(id),

                UNIQUE(player_id, achievement_name)
            )
        """)

        # Indexes improve score lookup performance.
        conn.execute("""
            CREATE INDEX IF NOT EXISTS
                idx_scores_player_game
            ON scores(player_id, game_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
                idx_scores_game_score
            ON scores(game_id, score DESC)
        """)


# ----------------------------------------
# PLAYER FUNCTIONS
# ----------------------------------------

def get_all_players():
    """Return all registered player accounts."""

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, username, created_at
            FROM players
            ORDER BY username COLLATE NOCASE
        """).fetchall()

    return [dict(row) for row in rows]


def get_player(player_id):
    """Find one player using their ID."""

    with get_connection() as conn:
        row = conn.execute("""
            SELECT id, username, created_at
            FROM players
            WHERE id = ?
        """, (player_id,)).fetchone()

    return dict(row) if row else None


def create_player(username):
    """Create a new registered player."""

    username = username.strip().upper()

    if not username:
        raise ValueError("Username cannot be empty.")

    if len(username) > 16:
        raise ValueError(
            "Username cannot exceed 16 characters."
        )

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO players (username)
            VALUES (?)
        """, (username,))

        return cursor.lastrowid


# ----------------------------------------
# GAME FUNCTIONS
# ----------------------------------------

def add_game(game_name):
    """
    Add a new game.

    If the game already exists, return its ID
    instead of creating a duplicate.
    """

    game_name = game_name.strip()

    if not game_name:
        raise ValueError("Game name cannot be empty.")

    with get_connection() as conn:

        conn.execute("""
            INSERT OR IGNORE INTO games (game_name)
            VALUES (?)
        """, (game_name,))

        row = conn.execute("""
            SELECT id
            FROM games
            WHERE game_name = ? COLLATE NOCASE
        """, (game_name,)).fetchone()

        return row["id"]


def get_all_games():
    """Return all available games."""

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, game_name
            FROM games
            ORDER BY game_name COLLATE NOCASE
        """).fetchall()

    return [dict(row) for row in rows]


def get_game(game_id):
    """Find a game using its ID."""

    with get_connection() as conn:
        row = conn.execute("""
            SELECT id, game_name
            FROM games
            WHERE id = ?
        """, (game_id,)).fetchone()

    return dict(row) if row else None


# ----------------------------------------
# SCORE FUNCTIONS
# ----------------------------------------

def save_score(player_id, game_id, score):
    """
    Save the result of one completed game.

    Each result is stored separately so we
    can calculate personal bests and total
    games played later.

    Guest scores are not saved.
    """

    if player_id is None:
        return None

    if isinstance(score, bool) or not isinstance(
        score, int
    ):
        raise ValueError("Score must be an integer.")

    if score < 0:
        raise ValueError("Score cannot be negative.")

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO scores (
                player_id,
                game_id,
                score
            )
            VALUES (?, ?, ?)
        """, (player_id, game_id, score))

        return cursor.lastrowid


def get_personal_best(player_id, game_id):
    """
    Return a player's highest score
    for a specific game.
    """

    with get_connection() as conn:
        row = conn.execute("""
            SELECT MAX(score) AS best_score
            FROM scores
            WHERE player_id = ?
              AND game_id = ?
        """, (player_id, game_id)).fetchone()

    return row["best_score"]


def get_player_personal_bests(player_id):
    """
    Return a player's personal best
    for every game they've played.
    """

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                games.id AS game_id,
                games.game_name,
                MAX(scores.score) AS best_score
            FROM scores
            JOIN games
                ON scores.game_id = games.id
            WHERE scores.player_id = ?
            GROUP BY games.id, games.game_name
            ORDER BY games.game_name COLLATE NOCASE
        """, (player_id,)).fetchall()

    return [dict(row) for row in rows]


def get_leaderboard(game_id, limit=100):
    """
    Rank players by their personal best
    for a specific game.
    """

    if not isinstance(limit, int) or limit < 1:
        raise ValueError("Limit must be positive.")

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                players.id AS player_id,
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
            LIMIT ?
        """, (game_id, limit)).fetchall()

    leaderboard = []

    for index, row in enumerate(rows):
        leaderboard.append({
            "rank": index + 1,
            "player_id": row["player_id"],
            "username": row["username"],
            "best_score": row["best_score"]
        })

    return leaderboard


def get_games_played(player_id):
    """Count recorded game results for a player."""

    with get_connection() as conn:
        row = conn.execute("""
            SELECT COUNT(*) AS total
            FROM scores
            WHERE player_id = ?
        """, (player_id,)).fetchone()

    return row["total"]


# ----------------------------------------
# ACHIEVEMENT FUNCTIONS
# ----------------------------------------

def unlock_achievement(player_id, achievement_name):
    """
    Award an achievement to a player.

    An achievement can only be unlocked
    once by each player.
    """

    if player_id is None:
        return False

    achievement_name = achievement_name.strip()

    if not achievement_name:
        raise ValueError(
            "Achievement name cannot be empty."
        )

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT OR IGNORE INTO achievements (
                player_id,
                achievement_name
            )
            VALUES (?, ?)
        """, (player_id, achievement_name))

        return cursor.rowcount > 0


def get_player_achievements(player_id):
    """Return achievements earned by a player."""

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                id,
                achievement_name,
                unlocked_at
            FROM achievements
            WHERE player_id = ?
            ORDER BY unlocked_at DESC, id DESC
        """, (player_id,)).fetchall()

    return [dict(row) for row in rows]


def get_achievement_count(player_id):
    """Count achievements earned by a player."""

    with get_connection() as conn:
        row = conn.execute("""
            SELECT COUNT(*) AS total
            FROM achievements
            WHERE player_id = ?
        """, (player_id,)).fetchone()

    return row["total"]


# ----------------------------------------
# DATABASE SUMMARY
# ----------------------------------------

def print_database_summary():
    """Show the current state of our database."""

    with get_connection() as conn:

        tables = [
            "players",
            "games",
            "scores",
            "achievements"
        ]

        print("\nIUP ARCADE DATABASE")
        print("------------------------------")

        for table in tables:
            row = conn.execute(
                f"SELECT COUNT(*) AS total FROM {table}"
            ).fetchone()

            print(f"{table}: {row['total']} records")

        print("------------------------------")
        print(f"Database: {DATABASE_PATH}")


# ----------------------------------------
# MAIN
# ----------------------------------------

if __name__ == "__main__":

    initialize_database()

    print("Database initialized successfully!")

    print_database_summary()
