"""Persistence for the high score, tolerant of a missing or bad file."""


def load_high_score(path: str) -> int:
    """Read the saved high score, returning 0 if absent or unreadable."""
    try:
        with open(path, encoding="utf-8") as handle:
            return int(handle.read().strip())
    except (OSError, ValueError):
        return 0


def save_high_score(path: str, score: int) -> None:
    """Write `score` to `path`, silently ignoring write failures."""
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(str(int(score)))
    except OSError:
        pass
