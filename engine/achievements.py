"""Achievement definitions and evaluation (pure data, no pygame).

Achievements are checked at the end of a game against a small context plus the
running profile stats. Some grant a snake skin when earned.
"""

from dataclasses import dataclass
from typing import Callable

from engine.profile import Profile


@dataclass(frozen=True)
class Context:
    """A snapshot of the just-finished game for achievement checks."""

    profile: Profile
    mode_key: str
    score: int
    length: int
    seconds: float
    won: bool


@dataclass(frozen=True)
class Achievement:
    """One earnable badge, optionally unlocking a skin."""

    id: str
    name: str
    description: str
    check: Callable[[Context], bool]
    skin: str | None = None


ACHIEVEMENTS: tuple[Achievement, ...] = (
    Achievement("first_meal", "First Meal", "Eat your very first food",
                lambda c: c.profile.stats["total_food"] >= 1),
    Achievement("sweet_tooth", "Sweet Tooth", "Eat 50 food in total",
                lambda c: c.profile.stats["total_food"] >= 50),
    Achievement("century", "Century", "Score 100 in a single game",
                lambda c: c.score >= 100, skin="sky"),
    Achievement("high_roller", "High Roller", "Score 300 in a single game",
                lambda c: c.score >= 300, skin="sunset"),
    Achievement("long_boi", "Long Boi", "Grow to length 20",
                lambda c: c.length >= 20, skin="candy"),
    Achievement("adventurer", "Adventurer", "Clear Adventure mode",
                lambda c: c.won and c.mode_key == "adventure"),
    Achievement("zen_master", "Zen Master", "Spend 2 minutes in Zen",
                lambda c: c.mode_key == "zen" and c.seconds >= 120, skin="shadow"),
    Achievement("speed_demon", "Speed Demon", "Reach length 30 in Classic",
                lambda c: c.mode_key == "classic" and c.length >= 30),
    Achievement("veteran", "Veteran", "Play 10 games",
                lambda c: c.profile.stats["games_played"] >= 10),
)


def newly_unlocked(context: Context) -> list[Achievement]:
    """Grant any newly earned achievements (and their skins). Returns them."""
    earned: list[Achievement] = []
    for ach in ACHIEVEMENTS:
        if ach.id in context.profile.achievements:
            continue
        if ach.check(context):
            context.profile.achievements.add(ach.id)
            if ach.skin:
                context.profile.unlock_skin(ach.skin)
            earned.append(ach)
    return earned
