"""Tests for sound-event emission and the SoundManager.

The event-emission tests are pure (no pygame). The SoundManager tests force
SDL's dummy audio driver so they run without a real sound device.
"""

import os
import random

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402

from audio import SoundManager  # noqa: E402
from config import SOUND_DIR, Direction, GameState, SoundEvent  # noqa: E402
from engine.game import Game  # noqa: E402
from engine.levels import LEVELS, Level, build_portal_map  # noqa: E402
from engine.snake import Snake  # noqa: E402


def _game(tmp_path, seed: int = 0) -> Game:
    game = Game(rng=random.Random(seed), high_score_path=str(tmp_path / "hs.txt"))
    game.reset()
    return game


# --- Sound-event emission (pure) --------------------------------------------


def test_eating_emits_eat_event(tmp_path) -> None:
    game = _game(tmp_path)
    hx, hy = game.snake.head
    game.food.position = (hx + 1, hy)
    game.update()
    assert SoundEvent.EAT in game.events


def test_wall_collision_emits_game_over_event(tmp_path) -> None:
    game = _game(tmp_path)
    hx, hy = game.snake.head
    game.level = Level(name="w", advance_score=999, walls=frozenset({(hx + 1, hy)}))
    game.portal_map = build_portal_map(game.level)
    game.food.position = None
    game.update()
    assert SoundEvent.GAME_OVER in game.events


def test_clearing_level_emits_event(tmp_path) -> None:
    game = _game(tmp_path)  # level 0 advances at 50
    game.score = 40
    hx, hy = game.snake.head
    game.food.position = (hx + 1, hy)
    game.update()
    assert game.state is GameState.LEVEL_CLEARED
    assert SoundEvent.LEVEL_CLEARED in game.events
    assert SoundEvent.EAT in game.events


def test_winning_emits_win_event(tmp_path) -> None:
    game = _game(tmp_path)
    game._load_level(len(LEVELS) - 1)
    game.state = GameState.RUNNING
    game.score = LEVELS[-1].advance_score - 10
    hx, hy = game.snake.head
    game.food.position = (hx + 1, hy)
    game.update()
    assert game.state is GameState.WON
    assert SoundEvent.WIN in game.events


def test_portal_emits_teleport_event(tmp_path) -> None:
    game = _game(tmp_path)
    game.snake = Snake(start=(5, 5), direction=Direction.RIGHT, length=3)
    game.level = Level(name="p", advance_score=999, portals=(((6, 5), (15, 15)),))
    game.portal_map = build_portal_map(game.level)
    game.food.position = None
    game.update()
    assert SoundEvent.TELEPORT in game.events


def test_events_are_cleared_each_tick(tmp_path) -> None:
    game = _game(tmp_path)
    hx, hy = game.snake.head
    game.food.position = (hx + 1, hy)
    game.update()  # emits EAT
    assert game.events
    game.food.position = None
    game.update()  # quiet tick
    assert game.events == []


def test_no_events_while_paused(tmp_path) -> None:
    game = _game(tmp_path)
    game.toggle_pause()
    game.update()
    assert game.events == []


# --- SoundManager -----------------------------------------------------------


def test_disabled_manager_is_silent_noop() -> None:
    manager = SoundManager(enabled=False)
    assert manager.available is False
    # None of these should raise despite no mixer.
    manager.play(SoundEvent.EAT)
    manager.play_events([SoundEvent.EAT, SoundEvent.WIN])
    manager.start_music()


def test_disabled_manager_can_toggle_mute() -> None:
    manager = SoundManager(enabled=False)
    assert manager.toggle_mute() is True
    assert manager.toggle_mute() is False


def test_manager_loads_sounds_with_dummy_driver() -> None:
    manager = SoundManager(sound_dir=SOUND_DIR)
    if not manager.available:
        pytest.skip("no mixer available in this environment")
    # Every SoundEvent should have a loaded clip.
    for event in SoundEvent:
        assert event in manager._sounds
    manager.play(SoundEvent.EAT)  # must not raise
    assert manager.toggle_mute() is True
    manager.play(SoundEvent.EAT)  # muted: no-op, must not raise
    pygame.mixer.quit()
