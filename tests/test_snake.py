"""Tests for the Snake entity."""

from config import Direction
from snake import Snake


def test_moves_in_each_direction() -> None:
    for direction, (dx, dy) in [
        (Direction.UP, (0, -1)),
        (Direction.DOWN, (0, 1)),
        (Direction.LEFT, (-1, 0)),
        (Direction.RIGHT, (1, 0)),
    ]:
        snake = Snake(start=(5, 5), direction=direction, length=1)
        snake.move((10, 10))
        assert snake.head == (5 + dx, 5 + dy)


def test_wraps_on_all_four_edges() -> None:
    grid = (10, 10)
    cases = [
        (Direction.RIGHT, (9, 5), (0, 5)),
        (Direction.LEFT, (0, 5), (9, 5)),
        (Direction.DOWN, (5, 9), (5, 0)),
        (Direction.UP, (5, 0), (5, 9)),
    ]
    for direction, start, expected in cases:
        snake = Snake(start=start, direction=direction, length=1)
        snake.move(grid)
        assert snake.head == expected


def test_growth_retains_tail_for_one_tick() -> None:
    snake = Snake(start=(5, 5), direction=Direction.RIGHT, length=3)
    snake.grow()
    snake.move((20, 20))
    assert snake.length == 4  # tail kept once
    snake.move((20, 20))
    assert snake.length == 4  # and only once


def test_reversal_is_rejected() -> None:
    snake = Snake(start=(5, 5), direction=Direction.RIGHT, length=3)
    snake.set_direction(Direction.LEFT)
    snake.move((20, 20))
    assert snake.direction is Direction.RIGHT
    assert snake.head == (6, 5)


def test_two_turns_in_one_tick_cannot_reverse() -> None:
    # Moving right, the player fires UP then LEFT within a single tick. LEFT is
    # a reversal of the committed direction and must be rejected even though a
    # turn (UP) is already buffered — otherwise the snake would fold onto its
    # own neck. The guard checks the committed direction, not the pending one.
    snake = Snake(start=(5, 5), direction=Direction.RIGHT, length=3)
    snake.set_direction(Direction.UP)
    snake.set_direction(Direction.LEFT)  # reversal of committed RIGHT
    snake.move((20, 20))
    assert snake.direction is Direction.UP
    assert snake.head == (5, 4)


def test_self_collision_detected() -> None:
    # A tight square loop brings the head back onto the body.
    snake = Snake(start=(5, 5), direction=Direction.RIGHT, length=5)
    assert not snake.collides_with_self()
    snake.set_direction(Direction.UP)
    snake.move((20, 20))
    snake.set_direction(Direction.LEFT)
    snake.move((20, 20))
    snake.set_direction(Direction.DOWN)
    snake.move((20, 20))
    assert snake.collides_with_self()
