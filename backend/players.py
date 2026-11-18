
import json
import sqlite3
from pathlib import Path

try:
    from . import database
except ImportError:
    import database


# ----------------------------------------
# CONFIGURATION
# ----------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
SESSION_PATH = DATA_DIR / "active_player.json"

MAX_USERNAME_LENGTH = 16


# ----------------------------------------
# INITIALIZATION
# ----------------------------------------

def initialize_players():
    """
    Make sure the arcade database exists.

    This does not delete existing players.
    """
    database.initialize_database()


# ----------------------------------------
# USERNAME VALIDATION
# ----------------------------------------

def validate_username(username):
    """
    Validate and normalize a username.

    Returns an uppercase username.
    Raises ValueError for invalid names.
    """

    if not isinstance(username, str):
        raise ValueError("Username must be text.")

    username = username.strip().upper()

    if not username:
        raise ValueError("Username cannot be empty.")

    if len(username) > MAX_USERNAME_LENGTH:
        raise ValueError(
            "Username cannot exceed 16 characters."
        )

    # Allow letters, numbers, and spaces.
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "

    for character in username:
        if character not in allowed:
            raise ValueError(
                "Username can only contain letters, "
                "numbers, and spaces."
            )

    return username


# ----------------------------------------
# ACCOUNT CREATION
# ----------------------------------------

def username_exists(username):
    """Check whether a username is already taken."""

    username = validate_username(username)

    with database.get_connection() as conn:
        row = conn.execute(
            """
            SELECT id
            FROM players
            WHERE username = ? COLLATE NOCASE
            """,
            (username,)
        ).fetchone()

    return row is not None


def create_account(username):
    """
    Create a player account.

    Returns:
        (True, message, player)
        (False, message, None)
    """

    try:
        username = validate_username(username)

        if username_exists(username):
            return (
                False,
                "That username already exists.",
                None
            )

        player_id = database.create_player(username)
        player = database.get_player(player_id)

        return (
            True,
            f"Player {username} created successfully!",
            player
        )

    except ValueError as error:
        return False, str(error), None

    except sqlite3.IntegrityError:
        return False, "That username already exists.", None

    except sqlite3.Error:
        return False, "Database error. Please try again.", None


# ----------------------------------------
# ACCOUNT LOOKUP
# ----------------------------------------

def get_all_accounts():
    """Return all registered player accounts."""

    return database.get_all_players()


def get_account_by_id(player_id):
    """Find a player using their database ID."""

    if type(player_id) is not int:
        return None

    return database.get_player(player_id)


def get_account_by_username(username):
    """Find a player using their username."""

    try:
        username = validate_username(username)
    except ValueError:
        return None

    with database.get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, username, created_at
            FROM players
            WHERE username = ? COLLATE NOCASE
            """,
            (username,)
        ).fetchone()

    return dict(row) if row else None


# ----------------------------------------
# ACTIVE PLAYER SESSION
# ----------------------------------------

def save_session(player):
    """
    Save the active player to JSON.

    Login.py and profiles.py use this file
    to identify the selected player.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    session = {
        "id": player["id"],
        "username": player["username"],
        "guest": player.get("guest", False)
    }

    # Write to a temporary file first.
    temporary_path = SESSION_PATH.with_suffix(".tmp")

    with open(
        temporary_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(session, file, indent=4)

    temporary_path.replace(SESSION_PATH)

    return session


# ----------------------------------------
# PLAYER LOGIN
# ----------------------------------------

def login_player(player_id):
    """
    Select an existing player.

    This is profile selection, not secure
    password-based authentication.
    """

    player = get_account_by_id(player_id)

    if player is None:
        return False, "Player account not found.", None

    try:
        session = save_session(player)

        return (
            True,
            f"Welcome back, {player['username']}!",
            session
        )

    except OSError:
        return False, "Could not save player session.", None


# ----------------------------------------
# GUEST LOGIN
# ----------------------------------------

def login_guest():
    """
    Start a guest session.

    Guests do not have a permanent
    player account in SQLite.
    """

    guest = {
        "id": None,
        "username": "GUEST",
        "guest": True
    }

    try:
        session = save_session(guest)

        return True, "Welcome, Guest!", session

    except OSError:
        return False, "Could not start guest session.", None


# ----------------------------------------
# GET CURRENT PLAYER
# ----------------------------------------

def get_active_player():
    """
    Return the currently selected player.

    For registered players, verify the
    account still exists in SQLite.
    """

    if not SESSION_PATH.exists():
        return None

    try:
        with open(
            SESSION_PATH,
            "r",
            encoding="utf-8"
        ) as file:
            session = json.load(file)

        if not isinstance(session, dict):
            return None

        if session.get("guest") is True:
            return {
                "id": None,
                "username": "GUEST",
                "guest": True,
                "created_at": None
            }

        player_id = session.get("id")

        if type(player_id) is not int:
            return None

        player = get_account_by_id(player_id)

        if player is None:
            return None

        player["guest"] = False

        return player

    except (
        OSError,
        ValueError,
        TypeError,
        sqlite3.Error
    ):
        return None


# ----------------------------------------
# PLAYER LOGOUT
# ----------------------------------------

def logout_player():
    """
    End the current player session.

    This does not delete the player's
    account or game statistics.
    """

    try:
        if SESSION_PATH.exists():
            SESSION_PATH.unlink()

        return True, "Player logged out successfully."

    except OSError:
        return False, "Could not log out player."


# ----------------------------------------
# DISPLAY ACCOUNT INFORMATION
# ----------------------------------------

def print_all_players():
    """Display all registered accounts."""

    players = get_all_accounts()

    print("\nIUP ARCADE - REGISTERED PLAYERS")
    print("--------------------------------")

    if not players:
        print("No registered players found.")

    else:
        for player in players:
            print(
                f"ID: {player['id']} | "
                f"Username: {player['username']} | "
                f"Created: {player['created_at']}"
            )

    print("--------------------------------")


def print_current_player():
    """Display the currently active player."""

    player = get_active_player()

    print("\nCURRENT ARCADE PLAYER")
    print("--------------------------------")

    if player is None:
        print("No active player session.")

    else:
        print(f"Username: {player['username']}")

        if player["guest"]:
            print("Account Type: Guest")
        else:
            print(f"Player ID: {player['id']}")
            print("Account Type: Registered")

    print("--------------------------------")


# ----------------------------------------
# MAIN
# ----------------------------------------

if __name__ == "__main__":

    initialize_players()

    print("Player management initialized successfully!")

    print_all_players()
    print_current_player()
