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
        self.direction = self._pending_direction
        width, height = grid_size
        dx, dy = self.direction.value
        x, y = self.head
        self.body.insert(0, ((x + dx) % width, (y + dy) % height))

        if self._pending_growth > 0:
            self._pending_growth -= 1
        else:
            self.body.pop()

    def collides_with_self(self) -> bool:
        """Whether the head shares a cell with any other part of the body."""
        return self.head in self.body[1:]
