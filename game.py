"""The game core: owns state and advances one tick at a time.

This module imports no pygame, so it can be constructed and driven in a
headless test process with no display.
"""

import random

from config import (
    GRID_HEIGHT,
    GRID_WIDTH,
    HIGH_SCORE_FILE,
    MENU_OPTIONS,
    MENU_START,
    POINTS_PER_FOOD,
    Direction,
    GameState,
)
from food import Food
from snake import Snake
from storage import load_high_score, save_high_score


class Game:
    """Snake game state and the rules that advance it."""

    def __init__(
        self,
        grid_size: tuple[int, int] = (GRID_WIDTH, GRID_HEIGHT),
        rng: random.Random | None = None,
        high_score_path: str = HIGH_SCORE_FILE,
    ) -> None:
        """Set up a fresh game.

        `rng` and `high_score_path` are injectable so tests stay deterministic
        and never touch the real save file.
        """
        self.grid_size = grid_size
        self._rng = rng if rng is not None else random.Random()
        self._high_score_path = high_score_path
        self.high_score = load_high_score(high_score_path)
        self.menu_index = 0
        self._new_round()
        self.state = GameState.MENU

    def _new_round(self) -> None:
        """Set up a fresh snake, food, and score without changing state."""
        self.snake = Snake()
        self.food = Food()
        self.food.respawn(self.snake.occupied_cells(), self.grid_size, self._rng)
        self.score = 0

    def reset(self) -> None:
        """Start a new round in play, keeping the loaded high score."""
        self._new_round()
        self.state = GameState.RUNNING

    def menu_move(self, delta: int) -> None:
        """Move the menu selection by `delta`, clamped to the options."""
        if self.state is not GameState.MENU:
            return
        self.menu_index = max(0, min(len(MENU_OPTIONS) - 1, self.menu_index + delta))

    def menu_select(self) -> None:
        """Activate the highlighted menu option."""
        if self.state is not GameState.MENU:
            return
        if MENU_OPTIONS[self.menu_index] == MENU_START:
            self.reset()
        else:
            self.state = GameState.INFO

    def back_to_menu(self) -> None:
        """Return to the main menu from the info screen."""
        if self.state is GameState.INFO:
            self.state = GameState.MENU

    def set_direction(self, direction: Direction) -> None:
        """Steer the snake, ignored unless the game is running."""
        if self.state is GameState.RUNNING:
            self.snake.set_direction(direction)

    def toggle_pause(self) -> None:
        """Flip between running and paused; a no-op once the game has ended."""
        if self.state is GameState.RUNNING:
            self.state = GameState.PAUSED
        elif self.state is GameState.PAUSED:
            self.state = GameState.RUNNING

    def update(self) -> None:
        """Advance the game by one tick."""
        if self.state is not GameState.RUNNING:
            return

        self.snake.move(self.grid_size)

        if self.snake.collides_with_self():
            self.state = GameState.GAME_OVER
            self._record_high_score()
            return

        if self.snake.head == self.food.position:
            self.snake.grow()
            self.score += POINTS_PER_FOOD
            placed = self.food.respawn(
                self.snake.occupied_cells(), self.grid_size, self._rng
            )
            if not placed:
                self.state = GameState.WON
                self._record_high_score()

    def _record_high_score(self) -> None:
        """Persist the score if it beats the stored best."""
        if self.score > self.high_score:
            self.high_score = self.score
            save_high_score(self._high_score_path, self.high_score)
