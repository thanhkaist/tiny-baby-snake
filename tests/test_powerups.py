"""Tests for power-ups and bonus food."""

import random

from config import BONUS_EVERY, BONUS_POINTS, POINTS_PER_FOOD, POWERUP_SPAWN_TICKS, Direction
from engine.game import Game
from engine.modes import ADVENTURE, CLASSIC, MAZE
from engine.powerups import SHRINK_AMOUNT, PowerUpKind
from engine.snake import Snake


def _game(tmp_path, mode=CLASSIC, seed=0) -> Game:
    game = Game(rng=random.Random(seed), high_score_path=str(tmp_path / "hs.txt"), mode=mode)
    game.reset()
    return game


def test_slow_halves_speed(tmp_path) -> None:
    game = _game(tmp_path)
    base = game.speed
    game.effects[PowerUpKind.SLOW] = 30
    assert game.speed == base * 0.5


def test_double_doubles_food_points(tmp_path) -> None:
    game = _game(tmp_path)
    game.effects[PowerUpKind.DOUBLE] = 30
    hx, hy = game.snake.head
    game.food.position = (hx + 1, hy)
    before = game.score
    game.update()
    assert game.score - before == POINTS_PER_FOOD * 2


def test_shrink_removes_segments(tmp_path) -> None:
    game = _game(tmp_path)
    game.snake = Snake(start=(10, 10), direction=Direction.RIGHT, length=6)
    game._activate_powerup(PowerUpKind.SHRINK)
    assert game.snake.length == 6 - SHRINK_AMOUNT


def test_ghost_prevents_wall_death(tmp_path) -> None:
    game = _game(tmp_path, mode=MAZE)
    wall = next(iter(game.level.walls))
    game.snake = Snake(start=(wall[0] - 1, wall[1]), direction=Direction.RIGHT, length=1)
    game.food.position = None
    game.effects[PowerUpKind.GHOST] = 30
    game.update()
    assert game.state.value == "running"  # walked through the wall


def test_magnet_pulls_food_toward_head(tmp_path) -> None:
    game = _game(tmp_path)
    game.snake = Snake(start=(5, 5), direction=Direction.RIGHT, length=1)
    game.food.position = (10, 5)
    game.effects[PowerUpKind.MAGNET] = 30
    game.update()
    assert game.food.position[0] < 10  # tugged closer on the x axis


def test_effects_expire(tmp_path) -> None:
    game = _game(tmp_path)
    game.food.position = None
    game.effects[PowerUpKind.SLOW] = 2
    game.update()
    assert PowerUpKind.SLOW in game.effects
    game.update()
    assert PowerUpKind.SLOW not in game.effects


def test_bonus_spawns_and_can_be_collected(tmp_path) -> None:
    game = _game(tmp_path)
    game.snake = Snake(start=(5, 5), direction=Direction.RIGHT, length=1)
    game.foods_eaten = BONUS_EVERY - 1
    game.food.position = (6, 5)  # eating this trips the bonus spawn
    game.update()
    assert game.bonus_pos is not None
    # Collect it directly.
    game.bonus_pos = (game.snake.head[0] + 1, game.snake.head[1])
    game.food.position = None
    game.set_direction(Direction.RIGHT)
    before = game.score
    game.update()
    assert game.score - before >= BONUS_POINTS


def test_powerup_spawns_after_interval(tmp_path) -> None:
    game = _game(tmp_path)
    game.food.position = None  # no eating, just let the timer run
    for _ in range(POWERUP_SPAWN_TICKS + 2):
        game.update()
    assert game.powerup_pos is not None
    assert game.powerup_kind is not None


def test_adventure_has_no_powerups(tmp_path) -> None:
    game = _game(tmp_path, mode=ADVENTURE)
    game.food.position = None
    for _ in range(POWERUP_SPAWN_TICKS + 20):
        game.update()
    assert game.powerup_pos is None
    assert game.bonus_pos is None
