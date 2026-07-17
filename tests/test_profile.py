"""Tests for the player profile, per-mode scores, and achievements."""

import random

from engine.achievements import Context, newly_unlocked
from engine.game import Game
from engine.modes import ADVENTURE, CLASSIC
from engine.profile import Profile
from storage import save_high_score


def test_profile_round_trips(tmp_path) -> None:
    path = str(tmp_path / "profile.json")
    p = Profile()
    p.high_scores["classic"] = 250
    p.stats["total_food"] = 42
    p.achievements.add("century")
    p.unlocked_skins.add("sky")
    p.selected_skin = "sky"
    p.settings.music_volume = 0.2
    p.save(path)

    loaded = Profile.load(path)
    assert loaded.best("classic") == 250
    assert loaded.stats["total_food"] == 42
    assert "century" in loaded.achievements
    assert "sky" in loaded.unlocked_skins
    assert loaded.selected_skin == "sky"
    assert loaded.settings.music_volume == 0.2


def test_load_tolerates_missing_and_migrates_legacy(tmp_path) -> None:
    assert Profile.load(str(tmp_path / "nope.json")).best("classic") == 0
    legacy = str(tmp_path / "highscore.txt")
    save_high_score(legacy, 99)
    migrated = Profile.load(str(tmp_path / "profile.json"), legacy_high_score_path=legacy)
    assert migrated.best("adventure") == 99


def test_record_game_updates_stats_and_best() -> None:
    p = Profile()
    assert p.record_game("classic", 120, length=15, food=12, powerups=2) is True
    assert p.best("classic") == 120
    assert p.stats["games_played"] == 1
    assert p.stats["total_food"] == 12
    assert p.stats["best_length"] == 15
    # A lower score doesn't beat the best.
    assert p.record_game("classic", 50, length=8, food=5, powerups=0) is False
    assert p.best("classic") == 120


def test_per_mode_high_scores_are_independent(tmp_path) -> None:
    path = str(tmp_path / "p.json")
    game = Game(rng=random.Random(0), high_score_path=path, mode=CLASSIC)
    game.reset()
    game.score = 200
    game._finalize(won=False)
    assert game.profile.best("classic") == 200
    assert game.profile.best("adventure") == 0


def test_century_achievement_unlocks_sky_skin() -> None:
    p = Profile()
    p.stats["total_food"] = 10  # so first_meal also fires
    ctx = Context(p, "classic", score=140, length=12, seconds=30, won=False)
    earned = {a.id for a in newly_unlocked(ctx)}
    assert "century" in earned
    assert "sky" in p.unlocked_skins
    # Already-earned achievements don't fire again.
    assert newly_unlocked(ctx) == []


def test_game_emits_new_achievements_on_finish(tmp_path) -> None:
    game = Game(rng=random.Random(0), high_score_path=str(tmp_path / "p.json"), mode=CLASSIC)
    game.reset()
    game.score = 160
    game.foods_eaten = 16
    game._finalize(won=False)
    ids = {a.id for a in game.new_achievements}
    assert "century" in ids
    assert "sky" in game.profile.unlocked_skins
