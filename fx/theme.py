"""Cartoon colour themes and snake skins.

Pure data (RGB tuples) plus a couple of small helpers. No pygame import, so
themes can be referenced from tests too.
"""

from dataclasses import dataclass

Color = tuple[int, int, int]


@dataclass(frozen=True)
class Skin:
    """A snake's colour scheme."""

    key: str
    name: str
    light: Color  # top / highlight of the body
    dark: Color  # underside / shade
    outline: Color  # cartoon outline
    belly: Color  # lighter belly band


@dataclass(frozen=True)
class Theme:
    """The full cartoon palette for a play session."""

    # Background gradient
    bg_top: Color = (150, 214, 255)
    bg_bottom: Color = (196, 238, 220)
    # Board (checkerboard "grass")
    board_light: Color = (170, 224, 130)
    board_dark: Color = (156, 214, 118)
    board_edge: Color = (120, 180, 96)
    board_shadow: Color = (86, 132, 74)
    # Food (apple)
    food_body: Color = (240, 84, 92)
    food_outline: Color = (150, 40, 52)
    food_highlight: Color = (255, 190, 190)
    food_leaf: Color = (120, 200, 96)
    food_stem: Color = (128, 90, 60)
    food_bonus: Color = (255, 206, 70)
    food_bonus_outline: Color = (196, 140, 24)
    # Walls (blocky, slightly 3D)
    wall_top: Color = (146, 120, 100)
    wall_side: Color = (110, 88, 72)
    wall_outline: Color = (74, 58, 46)
    # Eyes / tongue
    eye_white: Color = (255, 255, 255)
    eye_pupil: Color = (40, 44, 52)
    tongue: Color = (232, 92, 120)
    # UI
    text: Color = (60, 66, 84)
    text_light: Color = (255, 255, 255)
    text_dim: Color = (120, 132, 150)
    ui_panel: Color = (255, 255, 255)
    ui_panel_shadow: Color = (150, 170, 160)
    accent: Color = (255, 176, 60)


# Snake skins. The first is the default; the rest are unlockable in P5.
SKINS: tuple[Skin, ...] = (
    Skin("classic", "Sprout", (126, 217, 87), (74, 158, 62), (44, 96, 40), (196, 240, 150)),
    Skin("sky", "Blue Berry", (96, 180, 240), (52, 120, 190), (30, 74, 128), (176, 220, 255)),
    Skin("sunset", "Mango", (255, 168, 78), (226, 110, 52), (150, 66, 30), (255, 214, 150)),
    Skin("candy", "Bubblegum", (240, 130, 200), (200, 84, 158), (132, 44, 100), (255, 194, 232)),
    Skin("shadow", "Midnight", (120, 128, 150), (72, 78, 100), (38, 42, 58), (176, 184, 208)),
)

DEFAULT_THEME = Theme()


def skin_by_key(key: str) -> Skin:
    """Return the skin with `key`, falling back to the default."""
    for skin in SKINS:
        if skin.key == key:
            return skin
    return SKINS[0]


def lerp_color(a: Color, b: Color, t: float) -> Color:
    """Blend two colours by fraction `t` (0..1)."""
    return (
        round(a[0] + (b[0] - a[0]) * t),
        round(a[1] + (b[1] - a[1]) * t),
        round(a[2] + (b[2] - a[2]) * t),
    )
