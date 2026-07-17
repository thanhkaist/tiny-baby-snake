"""Game modes: strategy data that parameterizes the Game core.

Pure data (no pygame). A Mode says where the board comes from, how fast the
snake goes, what kills it, and how a round ends. The Game reads these flags;
Adventure is the default so existing behaviour is unchanged.
"""

from dataclasses import dataclass

from engine.levels import Level, block, hline, vline

Position = tuple[int, int]

# A wide-open board with no walls; its advance score is unreachable so
# threshold-based level clearing never fires in endless modes.
OPEN_BOARD = Level(name="", advance_score=10**9)

# A moderate maze that keeps the centre spawn corridor clear.
_MAZE_WALLS = frozenset(
    hline(4, 2, 9) | hline(4, 14, 21)
    | hline(19, 2, 9) | hline(19, 14, 21)
    | vline(4, 6, 9) | vline(4, 14, 17)
    | vline(19, 6, 9) | vline(19, 14, 17)
    | block(9, 8, 10, 9) | block(13, 8, 14, 9)
    | block(9, 14, 10, 15) | block(13, 14, 14, 15)
)
MAZE_BOARD = Level(name="Maze", advance_score=10**9, walls=_MAZE_WALLS)


@dataclass(frozen=True)
class Mode:
    """One playable mode."""

    key: str
    name: str
    tagline: str
    uses_levels: bool = False  # Adventure-style level progression
    board: Level = OPEN_BOARD  # fixed board when not using level progression
    time_limit: float | None = None  # seconds (Time Attack)
    walls_kill: bool = True
    self_kill: bool = True
    speed_ramp: bool = False  # speed up as the snake grows
    base_speed: float = 10.0  # logic ticks per second
    max_speed: float = 20.0


ADVENTURE = Mode(
    "adventure", "Adventure", "Clear five levels of walls & portals.",
    uses_levels=True, base_speed=10.0,
)
CLASSIC = Mode(
    "classic", "Classic", "Endless. Gets faster as you grow.",
    board=OPEN_BOARD, speed_ramp=True, base_speed=9.0,
)
TIME_ATTACK = Mode(
    "time_attack", "Time Attack", "Score as much as you can in 60 seconds.",
    board=OPEN_BOARD, time_limit=60.0, base_speed=11.0,
)
ZEN = Mode(
    "zen", "Zen", "Relax — no walls, no dying.",
    board=OPEN_BOARD, walls_kill=False, self_kill=False, base_speed=7.0,
)
MAZE = Mode(
    "maze", "Maze", "Thread the needle through a maze.",
    board=MAZE_BOARD, base_speed=10.0,
)

MODES: tuple[Mode, ...] = (ADVENTURE, CLASSIC, TIME_ATTACK, ZEN, MAZE)
DEFAULT_MODE = ADVENTURE


def mode_by_key(key: str) -> Mode:
    """Return the mode with `key`, or the default."""
    for mode in MODES:
        if mode.key == key:
            return mode
    return DEFAULT_MODE
