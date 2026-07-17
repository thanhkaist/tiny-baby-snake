"""Cartoon drawing primitives: rounded snake, googly eyes, bouncy fruit, walls.

These take a target surface and pixel coordinates so the renderer stays in
charge of layout. Kept separate from the renderer so the "look" lives in one
place and can evolve independently.
"""

import math

import pygame
import pygame.gfxdraw

from fx.theme import Skin, Theme, lerp_color

Color = tuple[int, int, int]


def _aa_circle(surface: pygame.Surface, cx: int, cy: int, r: int, color: Color) -> None:
    """A filled, anti-aliased circle."""
    if r <= 0:
        return
    pygame.gfxdraw.filled_circle(surface, cx, cy, r, color)
    pygame.gfxdraw.aacircle(surface, cx, cy, r, color)


def vertical_gradient(surface: pygame.Surface, top: Color, bottom: Color) -> None:
    """Fill the whole surface with a smooth top-to-bottom gradient."""
    h = surface.get_height()
    w = surface.get_width()
    for y in range(h):
        t = y / max(1, h - 1)
        pygame.draw.line(surface, lerp_color(top, bottom, t), (0, y), (w, y))


def rounded_shadow_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: Color,
    shadow: Color,
    radius: int = 18,
    shadow_offset: int = 6,
) -> None:
    """A rounded rectangle with a soft drop shadow below it."""
    shadow_rect = rect.move(0, shadow_offset)
    pygame.draw.rect(surface, shadow, shadow_rect, border_radius=radius)
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def checkerboard(
    surface: pygame.Surface,
    board: pygame.Rect,
    cell: int,
    light: Color,
    dark: Color,
    radius: int = 18,
) -> None:
    """Draw a soft two-tone grass checkerboard clipped to a rounded board."""
    board_surf = pygame.Surface(board.size, pygame.SRCALPHA)
    cols = board.width // cell + 1
    rows = board.height // cell + 1
    for gy in range(rows):
        for gx in range(cols):
            color = light if (gx + gy) % 2 == 0 else dark
            pygame.draw.rect(board_surf, color, (gx * cell, gy * cell, cell, cell))
    mask = pygame.Surface(board.size, pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
    board_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(board_surf, board.topleft)


def snake(
    surface: pygame.Surface,
    centers: list[tuple[int, int]],
    radius: int,
    skin: Skin,
    theme: Theme,
    heading: tuple[int, int],
    t: float,
    head_scale: float = 1.0,
) -> None:
    """Draw a rounded, gradient snake with a googly-eyed head.

    `centers` are pixel centres head-first; `heading` is the head's (dx, dy).
    `head_scale` lets callers squash-and-stretch the head (juice).
    """
    if not centers:
        return

    def stroke(rad: int, colorer) -> None:
        # Draw tail-to-head so the head sits on top; connect with thick joints.
        for i in range(len(centers) - 1, -1, -1):
            cx, cy = centers[i]
            frac = i / max(1, len(centers) - 1)
            color = colorer(frac)
            if i < len(centers) - 1:
                nx, ny = centers[i + 1]
                pygame.draw.line(surface, color, (cx, cy), (nx, ny), rad * 2)
            _aa_circle(surface, cx, cy, rad, color)

    # Cartoon outline, then the gradient body over it.
    stroke(radius + 3, lambda _f: skin.outline)
    stroke(radius, lambda f: lerp_color(skin.light, skin.dark, f))

    # A lighter belly highlight running along the top of each segment.
    for i, (cx, cy) in enumerate(centers):
        _aa_circle(surface, cx, cy - radius // 3, max(2, radius // 3), skin.belly)

    _snake_head(surface, centers[0], radius, skin, theme, heading, t, head_scale)


def _snake_head(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    skin: Skin,
    theme: Theme,
    heading: tuple[int, int],
    t: float,
    head_scale: float,
) -> None:
    """Eyes that look where the snake heads, plus a flicking tongue."""
    cx, cy = center
    hr = int(radius * 1.15 * head_scale)
    _aa_circle(surface, cx, cy, hr + 3, skin.outline)
    _aa_circle(surface, cx, cy, hr, lerp_color(skin.light, skin.dark, 0.0))

    dx, dy = heading
    # Perpendicular axis for the two eyes.
    px, py = -dy, dx
    eye_off = hr * 0.45
    fwd = hr * 0.34
    eye_r = max(3, int(hr * 0.42))
    pupil_r = max(2, int(eye_r * 0.52))
    for sign in (1, -1):
        ex = int(cx + dx * fwd + px * eye_off * sign)
        ey = int(cy + dy * fwd + py * eye_off * sign)
        _aa_circle(surface, ex, ey, eye_r, theme.eye_white)
        _aa_circle(surface, ex, ey, eye_r, theme.eye_white)
        # Pupil biased toward the heading.
        gx = int(ex + dx * eye_r * 0.4)
        gy = int(ey + dy * eye_r * 0.4)
        _aa_circle(surface, gx, gy, pupil_r, theme.eye_pupil)

    # Tongue flicks in and out over time.
    flick = max(0.0, math.sin(t * 6.0))
    if flick > 0.2 and (dx or dy):
        base_x = cx + dx * hr
        base_y = cy + dy * hr
        tip_x = base_x + dx * hr * 0.9 * flick
        tip_y = base_y + dy * hr * 0.9 * flick
        fork = hr * 0.28 * flick
        pygame.draw.line(surface, theme.tongue, (base_x, base_y), (tip_x, tip_y), 3)
        pygame.draw.line(
            surface, theme.tongue, (tip_x, tip_y), (tip_x + px * fork, tip_y + py * fork), 3
        )
        pygame.draw.line(
            surface, theme.tongue, (tip_x, tip_y), (tip_x - px * fork, tip_y - py * fork), 3
        )


def food(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    theme: Theme,
    t: float,
    bonus: bool = False,
) -> None:
    """A bouncy apple (or golden bonus) with a leaf, stem, and highlight."""
    cx, cy = center
    pulse = 1.0 + 0.08 * math.sin(t * 5.0)
    r = int(radius * pulse)
    body = theme.food_bonus if bonus else theme.food_body
    outline = theme.food_bonus_outline if bonus else theme.food_outline

    _aa_circle(surface, cx, cy, r + 2, outline)
    _aa_circle(surface, cx, cy, r, body)
    # Glossy highlight.
    _aa_circle(surface, cx - r // 3, cy - r // 3, max(2, r // 4), theme.food_highlight)
    # Stem + leaf.
    pygame.draw.line(surface, theme.food_stem, (cx, cy - r), (cx, cy - r - 5), 3)
    leaf = pygame.Rect(0, 0, r, r // 2)
    leaf.center = (cx + r // 3, cy - r - 2)
    pygame.draw.ellipse(surface, theme.food_leaf, leaf)


def wall(surface: pygame.Surface, rect: pygame.Rect, theme: Theme) -> None:
    """A chunky block with a lit top face and a cartoon outline."""
    pygame.draw.rect(surface, theme.wall_outline, rect, border_radius=5)
    inner = rect.inflate(-4, -4)
    pygame.draw.rect(surface, theme.wall_side, inner, border_radius=4)
    top = inner.copy()
    top.height = int(inner.height * 0.55)
    pygame.draw.rect(surface, theme.wall_top, top, border_radius=4)


def portal(
    surface: pygame.Surface, center: tuple[int, int], radius: int, color: Color, t: float
) -> None:
    """A pulsing swirl of concentric rings."""
    cx, cy = center
    for k in range(3):
        rr = int(radius - k * radius * 0.28 + math.sin(t * 4 + k) * 2)
        if rr > 1:
            pygame.gfxdraw.aacircle(surface, cx, cy, rr, color)
            pygame.gfxdraw.aacircle(surface, cx, cy, max(1, rr - 1), color)


def outline_text(
    font: pygame.font.Font,
    text: str,
    fill: Color,
    outline: Color,
    outline_w: int = 2,
) -> pygame.Surface:
    """Render sticker-style text: `fill` with a thick `outline` halo."""
    base = font.render(text, True, fill)
    edge = font.render(text, True, outline)
    w, h = base.get_size()
    out = pygame.Surface((w + outline_w * 2, h + outline_w * 2), pygame.SRCALPHA)
    for ox in range(-outline_w, outline_w + 1):
        for oy in range(-outline_w, outline_w + 1):
            if ox * ox + oy * oy <= outline_w * outline_w + 1:
                out.blit(edge, (ox + outline_w, oy + outline_w))
    out.blit(base, (outline_w, outline_w))
    return out
