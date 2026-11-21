import sqlite3
from pathlib import Path
import sys

# ----------------------------------------
# PROJECT IMPORTS
# ----------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from backend import database
from backend import players


# ----------------------------------------
# ACHIEVEMENT REQUIREMENTS
# ----------------------------------------

FIRST_GAME = 1
GETTING_STARTED = 10
ARCADE_VETERAN = 50

HIGH_SCORE = 1000
SCORE_MASTER = 10000


# ----------------------------------------
# GET ACTIVE PLAYER
# ----------------------------------------

def get_current_player():
    """
    Return the currently selected player.

    Guest players do not have permanent
    scores or achievements.
    """

    return players.get_active_player()


# ----------------------------------------
# CHECK ACHIEVEMENTS
# ----------------------------------------

def check_achievements(player_id, game_id, score):
    """
    Check achievements after saving a score.

    Returns a list of newly unlocked
    achievement names.
    """

    unlocked = []

    games_played = database.get_games_played(player_id)

    # Complete first game
    if games_played >= FIRST_GAME:
        if database.unlock_achievement(
            player_id, "First Steps"
        ):
            unlocked.append("First Steps")

    # Complete 10 games
    if games_played >= GETTING_STARTED:
        if database.unlock_achievement(
            player_id, "Getting Started"
        ):
            unlocked.append("Getting Started")

    # Complete 50 games
    if games_played >= ARCADE_VETERAN:
        if database.unlock_achievement(
            player_id, "Arcade Veteran"
        ):
            unlocked.append("Arcade Veteran")

    # Score at least 1,000 points
    if score >= HIGH_SCORE:
        if database.unlock_achievement(
            player_id, "High Scorer"
        ):
            unlocked.append("High Scorer")

    # Score at least 10,000 points
    if score >= SCORE_MASTER:
        if database.unlock_achievement(
            player_id, "Score Master"
        ):
            unlocked.append("Score Master")

    # Reach first place in a game
    leaderboard = database.get_leaderboard(
        game_id, limit=1
    )

    if leaderboard:
        first_place = leaderboard[0]

        if first_place["player_id"] == player_id:
            if database.unlock_achievement(
                player_id, "Champion"
            ):
                unlocked.append("Champion")

    return unlocked


# ----------------------------------------
# RECORD GAME SCORE
# ----------------------------------------

def record_game_score(game_name, score):
    """
    Save a score for the currently active
    registered player.

    Returns a dictionary containing the
    result and any unlocked achievements.

    Game scores must be nonnegative integers.
    Higher scores are considered better.
    """

    database.initialize_database()

    player = get_current_player()

    # Nobody is logged in
    if player is None:
        return {
            "success": False,
            "message": "No player is currently selected."
        }

    # Guests do not save scores
    if player.get("guest", False):
        return {
            "success": False,
            "message": "Guest scores are not saved."
        }

    # Validate game name
    if not isinstance(game_name, str):
        return {
            "success": False,
            "message": "Invalid game name."
        }

    game_name = game_name.strip()

    if not game_name:
        return {
            "success": False,
            "message": "Game name cannot be empty."
        }

    # Validate score
    if type(score) is not int or score < 0:
        return {
            "success": False,
            "message": "Score must be a nonnegative integer."
        }

    player_id = player["id"]

    try:
        # Create game if it is not in database
        game_id = database.add_game(game_name)

        # Record previous personal best
        previous_best = database.get_personal_best(
            player_id, game_id
        )

        # Save new score
        score_id = database.save_score(
            player_id,
            game_id,
            score
        )

        # Get updated personal best
        personal_best = database.get_personal_best(
            player_id, game_id
        )

        # Determine if a new record was set
        new_record = (
            previous_best is None
            or score > previous_best
        )

        # Calculate games played
        games_played = database.get_games_played(
            player_id
        )

        # Check for achievements
        unlocked = check_achievements(
            player_id,
            game_id,
            score
        )

        return {
            "success": True,
            "message": "Game score saved successfully!",
            "score_id": score_id,
            "player": player["username"],
            "game": game_name,
            "score": score,
            "personal_best": personal_best,
            "new_record": new_record,
            "games_played": games_played,
            "achievements": unlocked
        }

    except (sqlite3.Error, ValueError) as error:
        print("Score error:", error)

        return {
            "success": False,
            "message": "Could not save the game score."
        }


# ----------------------------------------
# DISPLAY GAME RESULTS
# ----------------------------------------

def print_game_result(result):
    """
    Print the result of recording a score.
    """

    print()
    print("IUP ARCADE - GAME RESULTS")
    print("--------------------------------")

    if not result["success"]:
        print(result["message"])
        print("--------------------------------")
        return

    print(f"Player: {result['player']}")
    print(f"Game: {result['game']}")
    print(f"Score: {result['score']:,}")

    print(
        f"Personal Best: "
        f"{result['personal_best']:,}"
    )

    print(f"Games Played: {result['games_played']}")

    if result["new_record"]:
        print("NEW PERSONAL BEST!")

    if result["achievements"]:
        print()
        print("NEW ACHIEVEMENTS!")

        for achievement in result["achievements"]:
            print(f"- {achievement}")

    print("--------------------------------")


# ----------------------------------------
# MANUAL SCORE ENTRY FOR TESTING
# ----------------------------------------

def test_score_entry():
    """
    Manually record a score to test our
    backend before connecting actual games.

    Scores entered here are saved for real.
    """

    database.initialize_database()

    player = get_current_player()

    print()
    print("IUP ARCADE - SCORE TEST")
    print("--------------------------------")

    if player is None:
        print("No active player selected.")
        print("Select a player through login.py first.")
        return

    print(f"Current Player: {player['username']}")

    if player.get("guest", False):
        print("Guest scores are not saved.")
        return

    print()

    game_name = input("Enter game name: ").strip()

    if not game_name:
        print("Game name cannot be empty.")
        return

    score_text = input("Enter score: ").strip()

    try:
        score = int(score_text)
    except ValueError:
        print("Please enter a whole number.")
        return

    if score < 0:
        print("Score cannot be negative.")
        return

    print()
    print(f"Player: {player['username']}")
    print(f"Game: {game_name}")
    print(f"Score: {score:,}")

    confirm = input(
        "Save this score to the database? (y/n): "
    ).strip().lower()

    if confirm != "y":
        print("Score was not saved.")
        return

    result = record_game_score(game_name, score)

    print_game_result(result)


# ----------------------------------------
# MAIN
# ----------------------------------------

if __name__ == "__main__":
    test_score_entry()