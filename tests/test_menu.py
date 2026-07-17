"""Tests for the main-menu and info-screen state transitions."""

import random

from config import MENU_OPTIONS, GameState
from engine.game import Game


def _game(tmp_path) -> Game:
    return Game(rng=random.Random(0), high_score_path=str(tmp_path / "hs.txt"))


def test_starts_on_menu(tmp_path) -> None:
    game = _game(tmp_path)
    assert game.state is GameState.MENU
    assert game.menu_index == 0


def test_menu_navigation_is_clamped(tmp_path) -> None:
    game = _game(tmp_path)
    game.menu_move(-1)  # already at the top
    assert game.menu_index == 0
    game.menu_move(1)
    assert game.menu_index == 1
    game.menu_move(len(MENU_OPTIONS) + 5)  # can't go past the last option
    assert game.menu_index == len(MENU_OPTIONS) - 1


def test_selecting_start_opens_mode_select(tmp_path) -> None:
    game = _game(tmp_path)
    game.menu_index = 0  # "Start Game"
    game.menu_select()
    assert game.state is GameState.MODE_SELECT
    # Choosing a mode begins play.
    game.mode_menu_select()
    assert game.state is GameState.RUNNING
    assert game.score == 0


def test_selecting_info_and_returning(tmp_path) -> None:
    game = _game(tmp_path)
    game.menu_index = MENU_OPTIONS.index("How to Play")
    game.menu_select()
    assert game.state is GameState.INFO
    game.back_to_menu()
    assert game.state is GameState.MENU


def test_update_is_noop_on_menu_and_info(tmp_path) -> None:
    game = _game(tmp_path)
    before = list(game.snake.body)
    game.update()  # on MENU
    assert game.snake.body == before
    game.state = GameState.INFO
    game.update()
    assert game.snake.body == before


def test_menu_actions_ignored_off_menu(tmp_path) -> None:
    game = _game(tmp_path)
    game.reset()  # now RUNNING
    game.menu_move(1)
    game.menu_select()
    assert game.state is GameState.RUNNING