"""The food entity and its placement on free grid cells."""

import random

from config import GRID_HEIGHT, GRID_WIDTH

Position = tuple[int, int]


class Food:
    """A single piece of food sitting on one grid cell."""

    def __init__(self, position: Position | None = None) -> None:
        """Create food at `position`, or off-board (None) until first spawn."""
        self.position: Position | None = position

    def respawn(
        self,
        occupied: set[Position],
        grid_size: tuple[int, int] = (GRID_WIDTH, GRID_HEIGHT),
        rng: random.Random | None = None,
    ) -> bool:
        """Place food on a uniformly random free cell.

        `rng` is injectable so placement is deterministic under test. Returns
        True if a cell was found, or False when the board is full (in which
        case the position is cleared).
        """
        width, height = grid_size
        free = [
            (x, y)
            for x in range(width)
            for y in range(height)
            if (x, y) not in occupied
        ]
        if not free:
            self.position = None
            return False

        chooser = rng if rng is not None else random
        self.position = chooser.choice(free)
        return True
