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
from engine.levels import LEVELS, Level, build_portal_map
from engine.modes import DEFAULT_MODE, MODES, Mode
from engine.snake import Snake
from storage import load_high_score, save_high_score


class Game:
    """Snake game state and the rules that advance it."""

    def __init__(
        self,
        grid_size: tuple[int, int] = (GRID_WIDTH, GRID_HEIGHT),
        rng: random.Random | None = None,
        high_score_path: str = HIGH_SCORE_FILE,
        mode: Mode = DEFAULT_MODE,
    ) -> None:
        """Set up a fresh game.

        `rng` and `high_score_path` are injectable so tests stay deterministic
        and never touch the real save file. `mode` selects the ruleset;
        Adventure by default.
        """
        self.grid_size = grid_size
        self._rng = rng if rng is not None else random.Random()
        self._high_score_path = high_score_path
        self.high_score = load_high_score(high_score_path)
        self.mode = mode
        self.menu_index = 0
        self.mode_index = 0
        self.events: list[SoundEvent] = []  # sound events emitted this tick
        self._new_round()
        self.state = GameState.MENU

    def _new_round(self) -> None:
        """Set up a fresh round for the current mode, without changing state."""
        self.score = 0
        self.ticks = 0
        if self.mode.uses_levels:
            self._load_level(0)
        else:
            self._apply_level(self.mode.board)

    def _load_level(self, index: int) -> None:
        """Load Adventure level `index`: snake, portals, food. Keeps score."""
        self.level_index = index
        self._apply_level(LEVELS[index])

    def _apply_level(self, level: Level) -> None:
        """Place the snake, portals, and food for `level`."""
        self.level = level
        self.portal_map = build_portal_map(level)
        self.snake = Snake(start=level.start, direction=level.start_dir)
        self.food = Food()
        self.food_timer = 0
        if not self.mode.uses_levels:
            self.level_index = 0
        self._respawn_food()

    def _respawn_food(self) -> bool:
        """Place food on a free cell, avoiding the snake, walls, and portals."""
        occupied = self.snake.occupied_cells() | self.level.blocked_cells()
        return self.food.respawn(occupied, self.grid_size, self._rng)

    @property
    def is_final_level(self) -> bool:
        """Whether the current Adventure level is the last one."""
        return self.level_index >= len(LEVELS) - 1

    @property
    def speed(self) -> float:
        """Current logic ticks per second, ramping with length if the mode asks."""
        base = self.mode.base_speed
        if self.mode.speed_ramp:
            base += (self.snake.length - 3) * 0.35
        return max(4.0, min(self.mode.max_speed, base))

    @property
    def time_left(self) -> float | None:
        """Seconds remaining in a timed mode, else None."""
        if self.mode.time_limit is None:
            return None
        return max(0.0, self.mode.time_limit - self.ticks / self.mode.base_speed)

    def reset(self) -> None:
        """Start a new round in play, keeping the loaded high score."""
        self._new_round()
        self.state = GameState.RUNNING

    def start_mode(self, mode: Mode) -> None:
        """Switch to `mode` and begin a fresh round in play."""
        self.mode = mode
        self.reset()

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
            self.state = GameState.MODE_SELECT
        else:
            self.state = GameState.INFO

    def mode_menu_move(self, delta: int) -> None:
        """Move the mode-select cursor, clamped to the available modes."""
        if self.state is not GameState.MODE_SELECT:
            return
        self.mode_index = max(0, min(len(MODES) - 1, self.mode_index + delta))

    def mode_menu_select(self) -> None:
        """Start the highlighted mode."""
        if self.state is GameState.MODE_SELECT:
            self.start_mode(MODES[self.mode_index])

    def back_to_menu(self) -> None:
        """Return to the main menu from the info or mode-select screen."""
        if self.state in (GameState.INFO, GameState.MODE_SELECT):
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

        self.ticks += 1
        if self.time_left is not None and self.time_left <= 0:
            self.state = GameState.GAME_OVER
            self.events.append(SoundEvent.GAME_OVER)
            self._record_high_score()
            return

        self.snake.move(self.grid_size)

        # A portal whisks the head to its paired hole before any collision test.
        partner = self.portal_map.get(self.snake.head)
        if partner is not None:
            self.snake.teleport_head(partner)
            self.events.append(SoundEvent.TELEPORT)

        hit_wall = self.mode.walls_kill and self.snake.head in self.level.walls
        hit_self = self.mode.self_kill and self.snake.collides_with_self()
        if hit_wall or hit_self:
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

        # Adventure clears the level once its target score is reached.
        if self.mode.uses_levels and self.score >= self.level.advance_score:
            self._record_high_score()
            if self.is_final_level:
                self.state = GameState.WON
                self.events.append(SoundEvent.WIN)
            else:
                self.state = GameState.LEVEL_CLEARED
                self.events.append(SoundEvent.LEVEL_CLEARED)
            return

        if not self._respawn_food():
            # Board full: a win in every mode.
            self.state = GameState.WON
            self.events.append(SoundEvent.WIN)
            self._record_high_score()

    def _record_high_score(self) -> None:
        """Persist the score if it beats the stored best."""
        if self.score > self.high_score:
            self.high_score = self.score
            save_high_score(self._high_score_path, self.high_score)
