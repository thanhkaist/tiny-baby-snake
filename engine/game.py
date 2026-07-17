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
    SoundEvent,
)
from engine.food import Food
from engine.levels import LEVELS, build_portal_map
from engine.snake import Snake
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
        self.events: list[SoundEvent] = []  # sound events emitted this tick
        self._new_round()
        self.state = GameState.MENU

    def _new_round(self) -> None:
        """Set up a fresh game at the first level, without changing state."""
        self.score = 0
        self._load_level(0)

    def _load_level(self, index: int) -> None:
        """Load level `index`: place the snake, portals, and food. Keeps score."""
        self.level_index = index
        self.level = LEVELS[index]
        self.portal_map = build_portal_map(self.level)
        self.snake = Snake(start=self.level.start, direction=self.level.start_dir)
        self.food = Food()
        self.food_timer = 0
        self._respawn_food()

    def _respawn_food(self) -> bool:
        """Place food on a free cell, avoiding the snake, walls, and portals."""
        occupied = self.snake.occupied_cells() | self.level.blocked_cells()
        return self.food.respawn(occupied, self.grid_size, self._rng)

    @property
    def is_final_level(self) -> bool:
        """Whether the current level is the last one."""
        return self.level_index >= len(LEVELS) - 1

    def reset(self) -> None:
        """Start a new round in play, keeping the loaded high score."""
        self._new_round()
        self.state = GameState.RUNNING

    def advance_level(self) -> None:
        """Move to the next level after clearing one, keeping the score."""
        if self.state is not GameState.LEVEL_CLEARED:
            return
        self._load_level(self.level_index + 1)
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
        """Advance the game by one tick, collecting any sound events."""
        self.events = []
        if self.state is not GameState.RUNNING:
            return

        self.snake.move(self.grid_size)

        # A portal whisks the head to its paired hole before any collision test.
        partner = self.portal_map.get(self.snake.head)
        if partner is not None:
            self.snake.teleport_head(partner)
            self.events.append(SoundEvent.TELEPORT)

        if self.snake.head in self.level.walls or self.snake.collides_with_self():
            self.state = GameState.GAME_OVER
            self.events.append(SoundEvent.GAME_OVER)
            self._record_high_score()
            return

        if self.snake.head == self.food.position:
            self._eat_food()
        elif self.level.food_ttl is not None:
            # Uneaten food teleports once its welcome runs out.
            self.food_timer += 1
            if self.food_timer >= self.level.food_ttl:
                self._respawn_food()
                self.food_timer = 0

    def _eat_food(self) -> None:
        """Grow, score, and either clear the level or lay out the next food."""
        self.snake.grow()
        self.score += POINTS_PER_FOOD
        self.food_timer = 0
        self.events.append(SoundEvent.EAT)

        if self.score >= self.level.advance_score:
            self._record_high_score()
            if self.is_final_level:
                self.state = GameState.WON
                self.events.append(SoundEvent.WIN)
            else:
                self.state = GameState.LEVEL_CLEARED
                self.events.append(SoundEvent.LEVEL_CLEARED)
            return

        if not self._respawn_food():
            self.state = GameState.WON
            self.events.append(SoundEvent.WIN)
            self._record_high_score()

    def _record_high_score(self) -> None:
        """Persist the score if it beats the stored best."""
        if self.score > self.high_score:
            self.high_score = self.score
            save_high_score(self._high_score_path, self.high_score)
