"""Player profile: settings, per-mode high scores, lifetime stats, unlocks.

Pure data persisted as JSON (no pygame). Tolerant of missing/partial saves so
the game always starts, even with an old or hand-edited file.
"""

from dataclasses import asdict, dataclass, field

from storage import load_high_score, load_json, save_json

DEFAULT_STATS = {
    "games_played": 0,
    "total_food": 0,
    "total_score": 0,
    "best_length": 0,
    "powerups_grabbed": 0,
}


@dataclass
class Settings:
    """Adjustable options, all persisted."""

    master_volume: float = 0.8
    music_volume: float = 0.5
    sfx_volume: float = 0.9
    screen_shake: bool = True


# Rows shown on the settings screen: (attribute, label).
SETTING_FIELDS = (
    ("master_volume", "Master Volume"),
    ("music_volume", "Music Volume"),
    ("sfx_volume", "SFX Volume"),
    ("screen_shake", "Screen Shake"),
)


@dataclass
class Profile:
    """Everything remembered about a player between sessions."""

    high_scores: dict[str, int] = field(default_factory=dict)
    stats: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_STATS))
    achievements: set[str] = field(default_factory=set)
    unlocked_skins: set[str] = field(default_factory=lambda: {"classic"})
    selected_skin: str = "classic"
    settings: Settings = field(default_factory=Settings)

    # --- Persistence --------------------------------------------------------

    @classmethod
    def load(cls, path: str, legacy_high_score_path: str | None = None) -> "Profile":
        """Load a profile, migrating a legacy high-score file if present."""
        data = load_json(path, None)
        if not isinstance(data, dict):
            profile = cls()
            if legacy_high_score_path:
                legacy = load_high_score(legacy_high_score_path)
                if legacy > 0:
                    profile.high_scores["adventure"] = legacy
            return profile
        stats = dict(DEFAULT_STATS)
        stats.update(data.get("stats", {}))
        return cls(
            high_scores=dict(data.get("high_scores", {})),
            stats=stats,
            achievements=set(data.get("achievements", [])),
            unlocked_skins=set(data.get("unlocked_skins", ["classic"])) or {"classic"},
            selected_skin=data.get("selected_skin", "classic"),
            settings=Settings(**{**asdict(Settings()), **data.get("settings", {})}),
        )

    def save(self, path: str) -> None:
        """Persist the profile to `path` as JSON."""
        save_json(path, {
            "high_scores": self.high_scores,
            "stats": self.stats,
            "achievements": sorted(self.achievements),
            "unlocked_skins": sorted(self.unlocked_skins),
            "selected_skin": self.selected_skin,
            "settings": asdict(self.settings),
        })

    # --- Queries & updates --------------------------------------------------

    def best(self, mode_key: str) -> int:
        """Best score recorded for a mode."""
        return self.high_scores.get(mode_key, 0)

    def record_game(
        self, mode_key: str, score: int, length: int, food: int, powerups: int
    ) -> bool:
        """Fold one finished game into the stats. Returns True on a new best."""
        self.stats["games_played"] += 1
        self.stats["total_food"] += food
        self.stats["total_score"] += score
        self.stats["powerups_grabbed"] += powerups
        self.stats["best_length"] = max(self.stats["best_length"], length)
        is_best = score > self.best(mode_key)
        if is_best:
            self.high_scores[mode_key] = score
        return is_best

    def unlock_skin(self, key: str) -> None:
        """Grant a skin."""
        self.unlocked_skins.add(key)
