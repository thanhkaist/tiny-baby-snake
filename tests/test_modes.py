"""Tests for game modes and mode selection."""

import random

from config import Direction, GameState
from engine.game import Game
from engine.modes import ADVENTURE, CLASSIC, MAZE, MODES, TIME_ATTACK, ZEN
from engine.snake import Snake


def _game(tmp_path, mode=ADVENTURE) -> Game:
    return Game(
        rng=random.Random(0), high_score_path=str(tmp_path / "hs.txt"), mode=mode
    )


def test_default_mode_is_adventure(tmp_path) -> None:
    game = _game(tmp_path)
    assert game.mode is ADVENTURE
    game.reset()
    assert game.level.name == "Open Field"  # Adventure level 1


def test_classic_does_not_clear_levels(tmp_path) -> None:
    game = _game(tmp_path, CLASSIC)
    game.reset()
    game.score = 1000  # far past any Adventure threshold
    hx, hy = game.snake.head
    game.food.position = (hx + 1, hy)
    game.update()
    assert game.state is GameState.RUNNING  # endless, never "clears"


def test_classic_speed_ramps_with_length(tmp_path) -> None:
    game = _game(tmp_path, CLASSIC)
    game.reset()
    base = game.speed
    for _ in range(6):
        game.snake.grow()
        game.snake.move()
    assert game.speed > base


def test_zen_never_dies_on_self_collision(tmp_path) -> None:
    game = _game(tmp_path, ZEN)
    game.reset()
    game.food.position = None
    # A tight loop that would normally be a self-collision.
    game.snake = Snake(start=(10, 10), direction=Direction.RIGHT, length=5)
    for d in (Direction.UP, Direction.LEFT, Direction.DOWN):
        game.set_direction(d)
        game.update()
    assert game.state is GameState.RUNNING


def test_maze_walls_kill(tmp_path) -> None:
    game = _game(tmp_path, MAZE)
    game.reset()
    assert game.level.walls  # maze has walls
    # Drop the head next to a wall and step into it.
    wall = next(iter(game.level.walls))
    game.snake = Snake(start=(wall[0] - 1, wall[1]), direction=Direction.RIGHT, length=1)
    game.food.position = None
    game.update()
    assert game.state is GameState.GAME_OVER


def test_time_attack_ends_when_time_runs_out(tmp_path) -> None:
    game = _game(tmp_path, TIME_ATTACK)
    game.reset()
    assert game.time_left == 60.0
    # Fast-forward the tick counter to just past the limit.
    game.ticks = int(TIME_ATTACK.time_limit * TIME_ATTACK.base_speed)
    game.food.position = None
    game.update()
    assert game.state is GameState.GAME_OVER


def test_mode_select_navigation_and_start(tmp_path) -> None:
    game = _game(tmp_path)
    game.state = GameState.MODE_SELECT
    game.mode_index = 0
    game.mode_menu_move(1)
    assert game.mode_index == 1
    game.mode_menu_move(-5)  # clamps
    assert game.mode_index == 0
    game.mode_menu_move(len(MODES) + 5)  # clamps to last
    assert game.mode_index == len(MODES) - 1
    game.mode_menu_select()
    assert game.state is GameState.RUNNING
    assert game.mode is MODES[-1]
