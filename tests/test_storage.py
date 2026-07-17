"""Tests for high-score persistence."""

from storage import load_high_score, save_high_score


def test_round_trip(tmp_path) -> None:
    path = str(tmp_path / "highscore.txt")
    save_high_score(path, 250)
    assert load_high_score(path) == 250


def test_missing_file_returns_zero(tmp_path) -> None:
    assert load_high_score(str(tmp_path / "nope.txt")) == 0


def test_corrupt_file_returns_zero(tmp_path) -> None:
    path = tmp_path / "highscore.txt"
    path.write_text("not a number")
    assert load_high_score(str(path)) == 0
