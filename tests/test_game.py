"""Tests for the Game core."""

import random

from config import Direction, GameState
from engine.game import Game
from engine.snake import Snake


def _game(tmp_path, seed: int = 0) -> Game:
    """A running Game with a deterministic rng and a throwaway high-score file.

    The game boots into the menu, so start a round for these play-focused tests.
    """
    path = str(tmp_path / "highscore.txt")
    game = Game(rng=random.Random(seed), high_score_path=path)
    game.reset()
    return game


def test_eating_increments_score_and_length(tmp_path) -> None:
    game = _game(tmp_path)
    # Place food directly ahead of the head so the next tick eats it.
    head_x, head_y = game.snake.head
    game.food.position = (head_x + 1, head_y)
    start_length = game.snake.length

    game.update()  # moves onto the food and schedules growth
    assert game.score == 10
    assert game.state is GameState.RUNNING

    game.food.position = None  # don't eat again on the next tick
    game.update()  # deferred growth now materializes
    assert game.snake.length == start_length + 1


def test_self_collision_ends_game(tmp_path) -> None:
    game = _game(tmp_path)
    game.food.position = None  # keep food out of the way
    # A length-3 snake can't fold onto itself in a tight loop; use one long
    # enough that a full square turn brings the head back onto the body.
    game.snake = Snake(start=(10, 10), direction=Direction.RIGHT, length=5)
    game.set_direction(Direction.UP)
    game.update()
    game.set_direction(Direction.LEFT)
    game.update()
    game.set_direction(Direction.DOWN)
    game.update()
    assert game.state is GameState.GAME_OVER


def test_update_is_noop_while_paused(tmp_path) -> None:
    game = _game(tmp_path)
    game.food.position = None
    game.toggle_pause()
    before = list(game.snake.body)
    game.update()
    assert game.snake.body == before
    assert game.state is GameState.PAUSED


def test_reset_restores_state_and_keeps_high_score(tmp_path) -> None:
    game = _game(tmp_path)
    game.score = 50
    game.high_score = 80
    game.state = GameState.GAME_OVER

    game.reset()

    assert game.score == 0
    assert game.state is GameState.RUNNING
    assert game.high_score == 80


def test_high_score_persists_across_instances(tmp_path) -> None:
    path = str(tmp_path / "highscore.txt")
    game = Game(rng=random.Random(0), high_score_path=path)
    game.score = 120
    game._record_high_score()

    reloaded = Game(rng=random.Random(0), high_score_path=path)
    assert reloaded.high_score == 120
