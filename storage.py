"""Persistence, tolerant of a missing or corrupt file.

Holds the legacy plain-int high-score reader (still used to migrate old saves)
and generic JSON load/save for the player profile.
"""

import json
from typing import Any


def load_json(path: str, default: Any) -> Any:
    """Read JSON from `path`, returning `default` if absent or unreadable."""
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return default


def save_json(path: str, data: Any) -> None:
    """Write `data` as JSON to `path`, ignoring write failures."""
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
    except OSError:
        pass


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
