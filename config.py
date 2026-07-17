"""Constants and shared value types for the Snake game."""

from enum import Enum

# Grid
GRID_WIDTH = 24
GRID_HEIGHT = 24
CELL_SIZE = 24

WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE + 48  # extra band for the score bar
HUD_HEIGHT = 48

# Timing. Logic advances at a fixed rate (the snake's speed in cells/second);
# rendering runs faster and interpolates between logic ticks for smoothness.
FPS = 10  # base logic ticks per second
RENDER_FPS = 60
MAX_STEPS_PER_FRAME = 5  # clamp so a stall can't spiral into a burst of updates

# Snake
INITIAL_SNAKE_LENGTH = 3

# Scoring
POINTS_PER_FOOD = 10
HIGH_SCORE_FILE = "highscore.txt"

# Power-ups & bonus food (endless modes). Timings are in logic ticks.
BONUS_EVERY = 4  # spawn a bonus after this many normal foods
BONUS_LIFETIME = 50  # ticks a bonus stays before vanishing
BONUS_POINTS = 50
POWERUP_SPAWN_TICKS = 90  # ticks between power-up spawn attempts
POWERUP_LIFETIME = 75  # ticks a power-up stays on the board

# Colors (R, G, B)
COLOR_BACKGROUND = (18, 20, 28)
COLOR_GRID = (28, 31, 42)
COLOR_SNAKE_HEAD = (126, 217, 87)
COLOR_SNAKE_BODY = (79, 168, 60)
COLOR_FOOD = (232, 84, 84)
COLOR_FOOD_WARNING = (240, 190, 74)  # food tint when it's about to teleport
COLOR_WALL = (70, 78, 104)
COLOR_HUD_BACKGROUND = (12, 13, 18)
COLOR_TEXT = (226, 230, 240)
COLOR_TEXT_DIM = (138, 146, 168)
COLOR_OVERLAY = (0, 0, 0, 180)

# Portal hues, cycled one per pair.
COLOR_PORTALS = (
    (86, 180, 233),
    (204, 121, 167),
    (240, 228, 66),
)

# Typography
FONT_NAME = "freesansbold.ttf"
FONT_SIZE_HUD = 20
FONT_SIZE_TITLE = 44
FONT_SIZE_SUBTITLE = 18

WINDOW_TITLE = "Tiny Baby Snake"


class Direction(Enum):
    """A unit step on the grid, in (dx, dy) with y growing downward."""

    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def opposite(self) -> "Direction":
        """Return the direction pointing the other way."""
        dx, dy = self.value
        return Direction((-dx, -dy))


class GameState(Enum):
    """Which phase of play the game is currently in."""

    MENU = "menu"
    MODE_SELECT = "mode_select"
    INFO = "info"
    RUNNING = "running"
    PAUSED = "paused"
    LEVEL_CLEARED = "level_cleared"
    GAME_OVER = "game_over"
    WON = "won"


class Intent(Enum):
    """A player instruction, decoded from raw input."""

    MOVE = "move"
    CONFIRM = "confirm"
    TOGGLE_PAUSE = "toggle_pause"
    TOGGLE_MUTE = "toggle_mute"
    RESTART = "restart"
    QUIT = "quit"


class SoundEvent(Enum):
    """A gameplay moment worth a sound. Values are the WAV file stems."""

    MENU_MOVE = "menu_move"
    SELECT = "select"
    EAT = "eat"
    BONUS = "bonus"
    POWERUP = "powerup"
    TELEPORT = "teleport"
    LEVEL_CLEARED = "level_cleared"
    GAME_OVER = "game_over"
    WIN = "win"


# Audio
SOUND_DIR = "assets/sounds"
MUSIC_VOLUME = 0.35
SFX_VOLUME = 0.8


# Main menu
MENU_START = "Start Game"
MENU_INFO = "How to Play"
MENU_OPTIONS = (MENU_START, MENU_INFO)

# How-to-play screen: each line is one row of body text.
INFO_LINES = (
    "Steer with the Arrow keys or W A S D.",
    "Eat the red food to grow and score +10 each.",
    "The edges wrap around — leave one side,",
    "reappear on the opposite side.",
    "Don't run into your own tail or the walls.",
    "Reach the target score to clear a level.",
    "Later levels add walls, food that teleports",
    "if you dawdle, and portals that whisk you across.",
    "",
    "P or Space — pause    R — restart    Esc — quit / back",
    "M — mute / unmute sound",
    "",
    "Your best score is saved between sessions.",
)

COLOR_MENU_SELECTED = COLOR_SNAKE_HEAD
FONT_SIZE_MENU = 28
FONT_SIZE_BODY = 20
