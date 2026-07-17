"""The snake entity: body, movement, growth, and self-collision."""

from config import GRID_HEIGHT, GRID_WIDTH, INITIAL_SNAKE_LENGTH, Direction

Position = tuple[int, int]


class Snake:
    """A snake on a wrapping grid, stored head-first."""

    def __init__(
        self,
        start: Position | None = None,
        direction: Direction = Direction.RIGHT,
        length: int = INITIAL_SNAKE_LENGTH,
    ) -> None:
        """Create a snake of `length` cells extending behind `start`.

        Defaults to the middle of the grid, heading right.
        """
        if length < 1:
            raise ValueError("length must be at least 1")
        if start is None:
            start = (GRID_WIDTH // 2, GRID_HEIGHT // 2)

        dx, dy = direction.value
        x, y = start
        self.body: list[Position] = [
            ((x - dx * i) % GRID_WIDTH, (y - dy * i) % GRID_HEIGHT)
            for i in range(length)
        ]
        self.direction = direction
        self._pending_direction = direction
        self._pending_growth = 0
        # Snapshot of the body before the last move, for render interpolation.
        self.prev_body: list[Position] = list(self.body)

    @property
    def head(self) -> Position:
        """The cell the snake's head occupies."""
        return self.body[0]

    @property
    def length(self) -> int:
        """How many cells the snake currently occupies."""
        return len(self.body)

    def occupied_cells(self) -> set[Position]:
        """Every cell covered by the snake."""
        return set(self.body)

    def set_direction(self, direction: Direction) -> None:
        """Queue a turn for the next move, ignoring reversals.

        The turn is buffered rather than applied immediately so that two
        keypresses within one tick cannot combine into a reversal.
        """
        if direction is self.direction.opposite:
            return
        self._pending_direction = direction

    def grow(self) -> None:
        """Keep the tail on the next move, extending the snake by one cell."""
        self._pending_growth += 1

    def move(self, grid_size: tuple[int, int] = (GRID_WIDTH, GRID_HEIGHT)) -> None:
        """Advance one cell, wrapping around the edges of the grid."""
        self.prev_body = list(self.body)  # snapshot for interpolation
        self.direction = self._pending_direction
        width, height = grid_size
        dx, dy = self.direction.value
        x, y = self.head
        self.body.insert(0, ((x + dx) % width, (y + dy) % height))

        if self._pending_growth > 0:
            self._pending_growth -= 1
        else:
            self.body.pop()

    def interpolated_positions(
        self,
        alpha: float,
        grid_size: tuple[int, int] = (GRID_WIDTH, GRID_HEIGHT),
    ) -> list[tuple[float, float]]:
        """Segment centre positions eased `alpha` (0..1) from prev to current.

        Each segment slides from its own previous cell to its current one. When
        a segment jumped more than one cell (an edge wrap or a portal), it snaps
        to the current cell instead of streaking across the board.
        """
        width, height = grid_size
        positions: list[tuple[float, float]] = []
        for i, (cx, cy) in enumerate(self.body):
            px, py = self.prev_body[i] if i < len(self.prev_body) else (cx, cy)
            if abs(cx - px) > 1 or abs(cy - py) > 1:
                positions.append((float(cx), float(cy)))  # wrapped/teleported: snap
            else:
                positions.append((px + (cx - px) * alpha, py + (cy - py) * alpha))
        return positions

    def teleport_head(self, dest: Position) -> None:
        """Relocate the head to `dest`, as when entering a portal.

        The rest of the body is left where it is, so the snake emerges from the
        paired portal while its trail stays behind — the classic wormhole look.
        """
        self.body[0] = dest

    def collides_with_self(self) -> bool:
        """Whether the head shares a cell with any other part of the body."""
        return self.head in self.body[1:]
