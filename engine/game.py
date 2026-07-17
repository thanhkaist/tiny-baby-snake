"""The game core: owns state and advances one tick at a time.

This module imports no pygame, so it can be constructed and driven in a
headless test process with no display.
"""

import random

from config import (
    BONUS_EVERY,
    BONUS_LIFETIME,
    BONUS_POINTS,
    GRID_HEIGHT,
    GRID_WIDTH,
    HIGH_SCORE_FILE,
    MENU_INFO,
    MENU_OPTIONS,
    MENU_PLAY,
    MENU_SETTINGS,
    MENU_SKINS,
    MENU_STATS,
    POINTS_PER_FOOD,
    POWERUP_LIFETIME,
    POWERUP_SPAWN_TICKS,
    Direction,
    GameState,
    SoundEvent,
)
from engine.achievements import Context, newly_unlocked
from engine.food import Food
from engine.levels import LEVELS, Level, build_portal_map
from engine.modes import DEFAULT_MODE, MODES, Mode
from engine.powerups import SHRINK_AMOUNT, SPECS, PowerUpKind
from engine.profile import SETTING_FIELDS, Profile
from engine.snake import Snake
from fx.theme import SKINS  # pure data (no pygame); safe for the core

Position = tuple[int, int]


class Game:
    """Snake game state and the rules that advance it."""

    def __init__(
        self,
        grid_size: tuple[int, int] = (GRID_WIDTH, GRID_HEIGHT),
        rng: random.Random | None = None,
        high_score_path: str = HIGH_SCORE_FILE,
        mode: Mode = DEFAULT_MODE,
        profile: Profile | None = None,
    ) -> None:
        """Set up a fresh game.

        `rng` and `high_score_path` are injectable so tests stay deterministic
        and never touch the real save file (the path holds the JSON profile).
        `mode` selects the ruleset; Adventure by default.
        """
        self.grid_size = grid_size
        self._rng = rng if rng is not None else random.Random()
        self._profile_path = high_score_path
        self.profile = profile if profile is not None else Profile.load(
            high_score_path, legacy_high_score_path=high_score_path
        )
        self.mode = mode
        self.high_score = self.profile.best(mode.key)
        self.menu_index = 0
        self.mode_index = 0
        self.settings_index = 0
        self.skins_index = 0
        self.events: list[SoundEvent] = []  # sound events emitted this tick
        self.new_achievements: list = []  # earned this tick (for toasts)
        self.powerups_grabbed = 0
        self._new_round()
        self.state = GameState.MENU

    def _new_round(self) -> None:
        """Set up a fresh round for the current mode, without changing state."""
        self.score = 0
        self.ticks = 0
        self.powerups_grabbed = 0
        self.new_achievements = []
        if self.mode.uses_levels:
            self._load_level(0)
        else:
            self._apply_level(self.mode.board)

    def _load_level(self, index: int) -> None:
        """Load Adventure level `index`: snake, portals, food. Keeps score."""
        self.level_index = index
        self._apply_level(LEVELS[index])

    def _apply_level(self, level: Level) -> None:
        """Place the snake, portals, food, and reset power-up state."""
        self.level = level
        self.portal_map = build_portal_map(level)
        self.snake = Snake(start=level.start, direction=level.start_dir)
        self.food = Food()
        self.food_timer = 0
        if not self.mode.uses_levels:
            self.level_index = 0
        # Power-ups & bonus food (endless modes).
        self.foods_eaten = 0
        self.bonus_pos: Position | None = None
        self.bonus_timer = 0
        self.powerup_kind: PowerUpKind | None = None
        self.powerup_pos: Position | None = None
        self.powerup_timer = 0
        self.powerup_spawn_counter = 0
        self.effects: dict[PowerUpKind, int] = {}
        self._respawn_food()

    def _occupied(self, include_food: bool = True) -> set[Position]:
        """All cells nothing new should spawn on."""
        cells = self.snake.occupied_cells() | self.level.blocked_cells()
        if include_food and self.food.position is not None:
            cells.add(self.food.position)
        if self.bonus_pos is not None:
            cells.add(self.bonus_pos)
        if self.powerup_pos is not None:
            cells.add(self.powerup_pos)
        return cells

    def _respawn_food(self) -> bool:
        """Place food on a free cell, avoiding everything else on the board."""
        return self.food.respawn(self._occupied(include_food=False), self.grid_size, self._rng)

    def _random_free_cell(self) -> Position | None:
        """A uniformly random empty cell, or None if the board is full."""
        blocked = self._occupied()
        width, height = self.grid_size
        free = [
            (x, y) for x in range(width) for y in range(height) if (x, y) not in blocked
        ]
        return self._rng.choice(free) if free else None

    @property
    def ghost_active(self) -> bool:
        """Whether the Ghost power-up is currently suppressing collisions."""
        return PowerUpKind.GHOST in self.effects

    @property
    def score_multiplier(self) -> int:
        """Points multiplier from the Double power-up."""
        return 2 if PowerUpKind.DOUBLE in self.effects else 1

    @property
    def is_final_level(self) -> bool:
        """Whether the current Adventure level is the last one."""
        return self.level_index >= len(LEVELS) - 1

    @property
    def speed(self) -> float:
        """Logic ticks per second: ramps with length, halved while slowed."""
        base = self.mode.base_speed
        if self.mode.speed_ramp:
            base += (self.snake.length - 3) * 0.35
        base = max(4.0, min(self.mode.max_speed, base))
        if PowerUpKind.SLOW in self.effects:
            base *= 0.5
        return base

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
        self.high_score = self.profile.best(mode.key)
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
        """Activate the highlighted menu option, opening its screen."""
        if self.state is not GameState.MENU:
            return
        target = {
            MENU_PLAY: GameState.MODE_SELECT,
            MENU_SKINS: GameState.SKINS,
            MENU_SETTINGS: GameState.SETTINGS,
            MENU_STATS: GameState.STATS,
            MENU_INFO: GameState.INFO,
        }[MENU_OPTIONS[self.menu_index]]
        if target is GameState.SKINS:
            self._sync_skin_cursor()
        self.state = target

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
        """Return to the main menu from any secondary screen."""
        if self.state in (
            GameState.INFO, GameState.MODE_SELECT, GameState.SETTINGS,
            GameState.SKINS, GameState.STATS,
        ):
            self.state = GameState.MENU

    # --- Settings screen ----------------------------------------------------

    def settings_move(self, delta: int) -> None:
        """Move the settings row cursor."""
        if self.state is not GameState.SETTINGS:
            return
        self.settings_index = max(0, min(len(SETTING_FIELDS) - 1, self.settings_index + delta))

    def settings_adjust(self, delta: int) -> None:
        """Change the selected setting; saves the profile."""
        if self.state is not GameState.SETTINGS:
            return
        key, _label = SETTING_FIELDS[self.settings_index]
        settings = self.profile.settings
        if key == "screen_shake":
            settings.screen_shake = not settings.screen_shake
        else:
            value = getattr(settings, key) + delta * 0.1
            setattr(settings, key, max(0.0, min(1.0, round(value, 2))))
        self.profile.save(self._profile_path)

    # --- Skins screen -------------------------------------------------------

    def _sync_skin_cursor(self) -> None:
        """Point the skin cursor at the currently selected skin."""
        keys = [s.key for s in SKINS]
        self.skins_index = keys.index(self.profile.selected_skin) if (
            self.profile.selected_skin in keys) else 0

    def skins_move(self, delta: int) -> None:
        """Move the skin cursor."""
        if self.state is not GameState.SKINS:
            return
        self.skins_index = max(0, min(len(SKINS) - 1, self.skins_index + delta))

    def skins_select(self) -> bool:
        """Select the highlighted skin if unlocked. Returns True on success."""
        if self.state is not GameState.SKINS:
            return False
        skin = SKINS[self.skins_index]
        if skin.key not in self.profile.unlocked_skins:
            return False
        self.profile.selected_skin = skin.key
        self.profile.save(self._profile_path)
        return True

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
        self.new_achievements = []
        if self.state is not GameState.RUNNING:
            return

        self.ticks += 1
        if self.time_left is not None and self.time_left <= 0:
            self.state = GameState.GAME_OVER
            self.events.append(SoundEvent.GAME_OVER)
            self._finalize(won=False)
            return

        self._tick_effects()
        self.snake.move(self.grid_size)

        # A portal whisks the head to its paired hole before any collision test.
        partner = self.portal_map.get(self.snake.head)
        if partner is not None:
            self.snake.teleport_head(partner)
            self.events.append(SoundEvent.TELEPORT)

        if not self.ghost_active:
            hit_wall = self.mode.walls_kill and self.snake.head in self.level.walls
            hit_self = self.mode.self_kill and self.snake.collides_with_self()
            if hit_wall or hit_self:
                self.state = GameState.GAME_OVER
                self.events.append(SoundEvent.GAME_OVER)
                self._finalize(won=False)
                return

        if self.snake.head == self.food.position:
            self._eat_food()
        elif self.level.food_ttl is not None:
            # Uneaten food teleports once its welcome runs out.
            self.food_timer += 1
            if self.food_timer >= self.level.food_ttl:
                self._respawn_food()
                self.food_timer = 0

        if self.mode.powerups:
            self._apply_magnet()
            self._update_bonus()
            self._update_powerup()

    def _tick_effects(self) -> None:
        """Count down active timed effects and drop the expired ones."""
        for kind in list(self.effects):
            self.effects[kind] -= 1
            if self.effects[kind] <= 0:
                del self.effects[kind]

    def _apply_magnet(self) -> None:
        """While Magnet is active, tug the food one cell toward the head."""
        if PowerUpKind.MAGNET not in self.effects or self.food.position is None:
            return
        fx, fy = self.food.position
        hx, hy = self.snake.head
        step_x = (hx > fx) - (hx < fx)
        step_y = (hy > fy) - (hy < fy)
        blocked = self._occupied(include_food=False)
        if abs(hx - fx) >= abs(hy - fy) and step_x:
            target = (fx + step_x, fy)
        elif step_y:
            target = (fx, fy + step_y)
        else:
            return
        if target not in blocked:
            self.food.position = target

    def _update_bonus(self) -> None:
        """Handle collecting or expiring the bonus food."""
        if self.bonus_pos is None:
            return
        if self.snake.head == self.bonus_pos:
            self.snake.grow()
            self.score += BONUS_POINTS * self.score_multiplier
            self.events.append(SoundEvent.BONUS)
            self.bonus_pos = None
            return
        self.bonus_timer -= 1
        if self.bonus_timer <= 0:
            self.bonus_pos = None

    def _update_powerup(self) -> None:
        """Spawn, collect, or expire the on-board power-up."""
        if self.powerup_pos is not None and self.snake.head == self.powerup_pos:
            self._activate_powerup(self.powerup_kind)
            self.powerup_pos = None
            self.powerup_kind = None
            return

        if self.powerup_pos is not None:
            self.powerup_timer -= 1
            if self.powerup_timer <= 0:
                self.powerup_pos = None
                self.powerup_kind = None
            return

        # None on board: count toward the next spawn.
        self.powerup_spawn_counter += 1
        if self.powerup_spawn_counter >= POWERUP_SPAWN_TICKS:
            self.powerup_spawn_counter = 0
            cell = self._random_free_cell()
            if cell is not None:
                self.powerup_kind = self._rng.choice(list(PowerUpKind))
                self.powerup_pos = cell
                self.powerup_timer = POWERUP_LIFETIME

    def _activate_powerup(self, kind: PowerUpKind) -> None:
        """Apply a picked-up power-up's effect."""
        self.events.append(SoundEvent.POWERUP)
        self.powerups_grabbed += 1
        spec = SPECS[kind]
        if kind is PowerUpKind.SHRINK:
            keep = max(2, self.snake.length - SHRINK_AMOUNT)
            self.snake.body = self.snake.body[:keep]
            self.snake.prev_body = self.snake.prev_body[:keep]
        elif spec.timed:
            self.effects[kind] = spec.duration

    def _eat_food(self) -> None:
        """Grow, score, and either clear the level or lay out the next food."""
        self.snake.grow()
        self.score += POINTS_PER_FOOD * self.score_multiplier
        self.food_timer = 0
        self.foods_eaten += 1
        self.events.append(SoundEvent.EAT)

        # Adventure clears the level once its target score is reached.
        if self.mode.uses_levels and self.score >= self.level.advance_score:
            if self.is_final_level:
                self.state = GameState.WON
                self.events.append(SoundEvent.WIN)
                self._finalize(won=True)
            else:
                self.state = GameState.LEVEL_CLEARED
                self.events.append(SoundEvent.LEVEL_CLEARED)
                self._record_high_score()
            return

        # In power-up modes, every few foods drops a timed bonus.
        if self.mode.powerups and self.bonus_pos is None and self.foods_eaten % BONUS_EVERY == 0:
            cell = self._random_free_cell()
            if cell is not None:
                self.bonus_pos = cell
                self.bonus_timer = BONUS_LIFETIME

        if not self._respawn_food():
            # Board full: a win in every mode.
            self.state = GameState.WON
            self.events.append(SoundEvent.WIN)
            self._finalize(won=True)

    def _record_high_score(self) -> None:
        """Persist the score to the profile if it beats the mode's best."""
        if self.score > self.high_score:
            self.high_score = self.score
            self.profile.high_scores[self.mode.key] = self.high_score
            self.profile.save(self._profile_path)

    def _finalize(self, won: bool) -> None:
        """Record a finished game: high score, lifetime stats, achievements."""
        self._record_high_score()
        self.profile.record_game(
            self.mode.key, self.score, self.snake.length,
            self.foods_eaten, self.powerups_grabbed,
        )
        context = Context(
            self.profile, self.mode.key, self.score, self.snake.length,
            self.ticks / self.mode.base_speed, won,
        )
        self.new_achievements = newly_unlocked(context)
        if self.new_achievements:
            self.events.append(SoundEvent.ACHIEVEMENT)
        self.profile.save(self._profile_path)
