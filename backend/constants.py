"""
Application constants for LineupBoss backend.
"""

# Position constants
POSITIONS = ["Pitcher", "Catcher", "1B", "2B", "3B", "SS", "LF", "RF", "LC", "RC", "Bench"]
INFIELD = ["Pitcher", "1B", "2B", "3B", "SS"]
OUTFIELD = ["Catcher", "LF", "RF", "LC", "RC"]
BENCH = ["Bench"]

# Game constants
MAX_INNINGS = 9
DEFAULT_INNINGS = 6

# API constants
API_PREFIX = "/api"
JWT_EXPIRES = 30 * 24 * 60 * 60  # 30 days in seconds

# Error messages
ERRORS = {
    "AUTH_REQUIRED": "Authentication required",
    "INVALID_CREDENTIALS": "Invalid email or password",
    "EMAIL_EXISTS": "Email already registered",
    "USER_NOT_FOUND": "User not found",
    "TEAM_NOT_FOUND": "Team not found",
    "PLAYER_NOT_FOUND": "Player not found",
    "GAME_NOT_FOUND": "Game not found",
    "UNAUTHORIZED": "You do not have permission to access this resource",
    "SERVER_ERROR": "An unexpected error occurred",
    "VALIDATION_ERROR": "Invalid input data"
}