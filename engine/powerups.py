"""Power-up definitions and specs (pure data, no pygame).

Power-ups spawn on the board in the endless modes; grabbing one applies a
timed effect (or an instant one, for Shrink). The Game reads these specs.
"""

from dataclasses import dataclass
from enum import Enum

Color = tuple[int, int, int]


class PowerUpKind(Enum):
    """The kinds of power-up that can appear."""

    SLOW = "slow"
    DOUBLE = "double"
    SHRINK = "shrink"
    GHOST = "ghost"
    MAGNET = "magnet"


@dataclass(frozen=True)
class PowerUpSpec:
    """Static description of a power-up."""

    kind: PowerUpKind
    name: str
    letter: str
    color: Color
    duration: int  # ticks the effect lasts; 0 = instant
    timed: bool


SPECS: dict[PowerUpKind, PowerUpSpec] = {
    PowerUpKind.SLOW: PowerUpSpec(
        PowerUpKind.SLOW, "Slow-Mo", "S", (96, 170, 240), 60, True),
    PowerUpKind.DOUBLE: PowerUpSpec(
        PowerUpKind.DOUBLE, "Double", "x2", (255, 200, 64), 80, True),
    PowerUpKind.GHOST: PowerUpSpec(
        PowerUpKind.GHOST, "Ghost", "G", (188, 150, 240), 55, True),
    PowerUpKind.MAGNET: PowerUpSpec(
        PowerUpKind.MAGNET, "Magnet", "M", (86, 200, 190), 60, True),
    PowerUpKind.SHRINK: PowerUpSpec(
        PowerUpKind.SHRINK, "Shrink", "-", (240, 130, 200), 0, False),
}

SHRINK_AMOUNT = 3  # segments removed by a Shrink pickup
