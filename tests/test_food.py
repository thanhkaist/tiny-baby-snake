"""Tests for the Food entity."""

import random

from engine.food import Food


def test_never_spawns_on_snake() -> None:
    grid = (4, 4)
    occupied = {(x, y) for x in range(4) for y in range(3)}  # all but the last row
    rng = random.Random(1234)
    food = Food()
    for _ in range(50):
        assert food.respawn(occupied, grid, rng) is True
        assert food.position not in occupied
        assert food.position[1] == 3  # only the free row remains


def test_returns_false_on_full_board() -> None:
    grid = (3, 3)
    occupied = {(x, y) for x in range(3) for y in range(3)}
    food = Food(position=(0, 0))
    assert food.respawn(occupied, grid, random.Random(0)) is False
    assert food.position is None


def test_placement_is_deterministic_under_seed() -> None:
    grid = (8, 8)
    occupied: set[tuple[int, int]] = set()
    a, b = Food(), Food()
    a.respawn(occupied, grid, random.Random(42))
    b.respawn(occupied, grid, random.Random(42))
    assert a.position == b.position
