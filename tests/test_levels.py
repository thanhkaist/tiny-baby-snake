"""Tests for level layouts and level progression."""

import random

import pytest

from config import GRID_HEIGHT, GRID_WIDTH, Direction, GameState
from engine.game import Game
from engine.levels import LEVELS, Level, build_portal_map
from engine.snake import Snake


def _game(tmp_path, seed: int = 0) -> Game:
    """A running Game with a deterministic rng and throwaway high-score file."""
    game = Game(rng=random.Random(seed), high_score_path=str(tmp_path / "hs.txt"))
    game.reset()
    return game


# --- Level data integrity ---------------------------------------------------


def test_walls_and_portals_are_in_bounds() -> None:
    for level in LEVELS:
        for x, y in level.blocked_cells():
            assert 0 <= x < GRID_WIDTH
            assert 0 <= y < GRID_HEIGHT


def test_start_and_initial_body_are_clear() -> None:
    for level in LEVELS:
        snake = Snake(start=level.start, direction=level.start_dir)
        blocked = level.blocked_cells()
        assert snake.occupied_cells().isdisjoint(blocked), level.name


def test_advance_scores_strictly_increase() -> None:
    scores = [level.advance_score for level in LEVELS]
    assert scores == sorted(scores)
    assert len(set(scores)) == len(scores)


def test_portal_map_is_symmetric() -> None:
    level = Level(name="t", advance_score=10, portals=(((1, 1), (5, 5)),))
    mapping = build_portal_map(level)
    assert mapping[(1, 1)] == (5, 5)
    assert mapping[(5, 5)] == (1, 1)


# --- Walls ------------------------------------------------------------------


def test_running_into_a_wall_ends_the_game(tmp_path) -> None:
    game = _game(tmp_path)
    # Put a wall directly ahead of the head and step into it.
    hx, hy = game.snake.head
    wall = (hx + 1, hy)
    game.level = Level(name="wall", advance_score=999, walls=frozenset({wall}))
    game.portal_map = build_portal_map(game.level)
    game.food.position = None
    game.update()
    assert game.state is GameState.GAME_OVER


def test_food_never_spawns_on_walls_or_portals(tmp_path) -> None:
    game = _game(tmp_path)
    # A tight level: fill most of the board with walls, leave a small free strip.
    walls = frozenset(
        (x, y)
        for x in range(GRID_WIDTH)
        for y in range(GRID_HEIGHT)
        if y < GRID_HEIGHT - 2
    )
    game.snake = Snake(start=(1, GRID_HEIGHT - 1), direction=Direction.RIGHT, length=1)
    game.level = Level(
        name="tight",
        advance_score=999,
        walls=walls,
        portals=(((0, GRID_HEIGHT - 1), (GRID_WIDTH - 1, GRID_HEIGHT - 1)),),
    )
    blocked = game.level.blocked_cells() | game.snake.occupied_cells()
    for _ in range(60):
        assert game._respawn_food() is True
        assert game.food.position not in blocked


# --- Portals ----------------------------------------------------------------


def test_head_teleports_through_portal(tmp_path) -> None:
    game = _game(tmp_path)
    game.snake = Snake(start=(5, 5), direction=Direction.RIGHT, length=3)
    exit_cell = (15, 15)
    game.level = Level(
        name="portal",
        advance_score=999,
        portals=(((6, 5), exit_cell),),  # head steps onto (6,5) next tick
    )
    game.portal_map = build_portal_map(game.level)
    game.food.position = None
    game.update()
    assert game.snake.head == exit_cell
    assert game.snake.direction is Direction.RIGHT


# --- Teleporting food -------------------------------------------------------


def test_uneaten_food_teleports_after_ttl(tmp_path) -> None:
    game = _game(tmp_path)
    game.snake = Snake(start=(1, 1), direction=Direction.DOWN, length=1)
    game.level = Level(name="ttl", advance_score=999, food_ttl=3)
    game.food.position = (20, 20)  # far from the snake's path
    positions = set()
    for _ in range(3):  # ttl reached on the 3rd tick
        game.update()
        positions.add(game.food.position)
    assert (20, 20) not in positions or len(positions) > 1
    assert game.food.position != (20, 20)


# --- Progression ------------------------------------------------------------


def test_reaching_threshold_clears_level(tmp_path) -> None:
    game = _game(tmp_path)  # level 0, advance at 50
    game.score = 40
    hx, hy = game.snake.head
    game.food.position = (hx + 1, hy)
    game.update()  # +10 -> 50, clears level 0
    assert game.state is GameState.LEVEL_CLEARED
    assert game.level_index == 0


def test_advance_level_loads_next_and_keeps_score(tmp_path) -> None:
    game = _game(tmp_path)
    game.state = GameState.LEVEL_CLEARED
    game.score = 50
    game.advance_level()
    assert game.state is GameState.RUNNING
    assert game.level_index == 1
    assert game.level is LEVELS[1]
    assert game.score == 50
    # Snake reset to the new level's clear start.
    assert game.snake.occupied_cells().isdisjoint(game.level.blocked_cells())


def test_clearing_final_level_wins(tmp_path) -> None:
    game = _game(tmp_path)
    game._load_level(len(LEVELS) - 1)
    game.state = GameState.RUNNING
    game.score = LEVELS[-1].advance_score - 10
    hx, hy = game.snake.head
    game.food.position = (hx + 1, hy)
    game.update()
    assert game.state is GameState.WON


def test_reset_returns_to_first_level(tmp_path) -> None:
    game = _game(tmp_path)
    game._load_level(2)
    game.reset()
    assert game.level_index == 0
    assert game.state is GameState.RUNNING
    assert game.score == 0
