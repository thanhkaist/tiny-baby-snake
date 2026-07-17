"""Level definitions and layout helpers.

Pure data with no pygame, so the game core stays headless-testable. Each level
describes its walls, optional teleport portals, and food behaviour; the walls
are built from small geometric helpers rather than hand-drawn maps so every
cell is guaranteed in-bounds.
"""

from dataclasses import dataclass, field

from config import GRID_HEIGHT, GRID_WIDTH, Direction

Position = tuple[int, int]
Portal = tuple[Position, Position]


def hline(y: int, x0: int, x1: int) -> set[Position]:
    """A horizontal wall segment on row `y` from column `x0` to `x1`."""
    return {(x, y) for x in range(x0, x1 + 1)}


def vline(x: int, y0: int, y1: int) -> set[Position]:
    """A vertical wall segment on column `x` from row `y0` to `y1`."""
    return {(x, y) for y in range(y0, y1 + 1)}


def block(x0: int, y0: int, x1: int, y1: int) -> set[Position]:
    """A filled rectangle of walls spanning the given corners (inclusive)."""
    return {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}


@dataclass(frozen=True)
class Level:
    """One level's layout and rules."""

    name: str
    advance_score: int  # cumulative score that clears this level
    walls: frozenset[Position] = field(default_factory=frozenset)
    portals: tuple[Portal, ...] = ()
    food_ttl: int | None = None  # ticks before uneaten food teleports; None = static
    start: Position | None = None  # snake start cell (None = grid centre)
    start_dir: Direction = Direction.RIGHT

    def portal_cells(self) -> set[Position]:
        """Every cell occupied by a portal endpoint."""
        return {cell for pair in self.portals for cell in pair}

    def blocked_cells(self) -> set[Position]:
        """Cells food must avoid: walls plus portal endpoints."""
        return set(self.walls) | self.portal_cells()


def build_portal_map(level: Level) -> dict[Position, Position]:
    """Map each portal endpoint to the partner it teleports to."""
    mapping: dict[Position, Position] = {}
    for a, b in level.portals:
        mapping[a] = b
        mapping[b] = a
    return mapping


def _walls(*groups: set[Position]) -> frozenset[Position]:
    """Union several wall groups into a single frozen set."""
    combined: set[Position] = set()
    for group in groups:
        combined |= group
    return frozenset(combined)


# A clear zone around the centre is kept free of walls in every level so the
# snake always spawns and starts moving safely.
LEVELS: tuple[Level, ...] = (
    Level(
        name="Open Field",
        advance_score=50,
    ),
    Level(
        name="Pillars",
        advance_score=120,
        walls=_walls(
            block(4, 4, 6, 6),
            block(17, 4, 19, 6),
            block(4, 17, 6, 19),
            block(17, 17, 19, 19),
        ),
    ),
    Level(
        name="Corridors",
        advance_score=200,
        walls=_walls(
            hline(5, 3, 10),
            hline(5, 14, 20),
            hline(18, 3, 10),
            hline(18, 14, 20),
            vline(5, 8, 15),
            vline(18, 8, 15),
        ),
    ),
    Level(
        name="Shifting Feast",
        advance_score=300,
        walls=_walls(
            block(9, 3, 14, 4),
            block(9, 19, 14, 20),
            block(3, 9, 4, 14),
            block(19, 9, 20, 14),
        ),
        food_ttl=25,
    ),
    Level(
        name="Wormholes",
        advance_score=420,
        walls=_walls(
            block(10, 6, 13, 7),
            block(10, 16, 13, 17),
            vline(6, 10, 13),
            vline(17, 10, 13),
        ),
        portals=(((2, 2), (21, 21)),),
        food_ttl=22,
    ),
)
