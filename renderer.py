"""Cartoon rendering with juice: particles, screen shake, pop-ups, transitions.

Scene content is drawn to an off-screen canvas, then composited to the display
with a shake offset so effects can rattle the whole frame. The "look" lives in
fx/draw.py; the "feel" (particles, camera) lives in fx/particles.py & camera.py.
"""

import math

import pygame

from config import (
    CELL_SIZE,
    COLOR_PORTALS,
    FONT_NAME,
    FONT_SIZE_BODY,
    FONT_SIZE_HUD,
    FONT_SIZE_MENU,
    FONT_SIZE_SUBTITLE,
    FONT_SIZE_TITLE,
    GRID_HEIGHT,
    GRID_WIDTH,
    HUD_HEIGHT,
    INFO_LINES,
    MENU_OPTIONS,
    POINTS_PER_FOOD,
    WINDOW_TITLE,
    GameState,
    SoundEvent,
)
from engine.game import Game
from engine.modes import MODES
from fx import draw
from fx.camera import Camera
from fx.particles import ParticleSystem
from fx.theme import DEFAULT_THEME, SKINS, Skin, Theme


class Renderer:
    """Draws the game in a playful cartoon style, with effects."""

    def __init__(
        self, surface: pygame.Surface, theme: Theme = DEFAULT_THEME, skin: Skin = SKINS[0]
    ) -> None:
        self.screen = surface
        self.canvas = pygame.Surface(surface.get_size())
        self.theme = theme
        self.skin = skin
        self._font_hud = pygame.font.Font(FONT_NAME, FONT_SIZE_HUD)
        self._font_title = pygame.font.Font(FONT_NAME, FONT_SIZE_TITLE)
        self._font_subtitle = pygame.font.Font(FONT_NAME, FONT_SIZE_SUBTITLE)
        self._font_menu = pygame.font.Font(FONT_NAME, FONT_SIZE_MENU)
        self._font_body = pygame.font.Font(FONT_NAME, FONT_SIZE_BODY)
        self._radius = int(CELL_SIZE * 0.46)

        self.particles = ParticleSystem()
        self.camera = Camera()
        self._popups: list[dict] = []
        self._eat_pulse = 0.0
        self._prev_state = None
        self._fade = 0.0

    # --- Effects lifecycle --------------------------------------------------

    def spawn_events(self, game: Game) -> None:
        """React to one tick's game events by spawning matching effects."""
        head = self._cell_center(*game.snake.head)
        for event in game.events:
            if event is SoundEvent.EAT:
                self.particles.emit_burst(*head, self.theme.food_body, count=16)
                self._popups.append(
                    {"text": f"+{POINTS_PER_FOOD}", "x": head[0], "y": head[1] - CELL_SIZE,
                     "life": 0.8, "max": 0.8, "color": self.theme.accent}
                )
                self.camera.shake(0.18)
                self._eat_pulse = 1.0
            elif event is SoundEvent.TELEPORT:
                self.particles.emit_burst(*head, COLOR_PORTALS[0], count=20, speed=260)
                self.camera.shake(0.25)
            elif event is SoundEvent.GAME_OVER:
                self.particles.emit_burst(*head, self.skin.light, count=34, speed=300)
                self.camera.shake(0.75)
                self.camera.flash((255, 90, 90), 0.35)
            elif event in (SoundEvent.LEVEL_CLEARED, SoundEvent.WIN):
                cx = self.board_rect.centerx
                cy = self.board_rect.centery
                self.particles.emit_confetti(
                    cx, cy,
                    (self.theme.accent, self.skin.light, self.theme.food_body,
                     COLOR_PORTALS[0], self.theme.food_leaf),
                    count=70,
                )
                self.camera.flash((255, 255, 255), 0.4, peak_alpha=160)

    def update(self, dt: float) -> None:
        """Advance all effect systems once per frame."""
        self.particles.update(dt)
        self.camera.update(dt)
        self._eat_pulse = max(0.0, self._eat_pulse - dt * 4.0)
        self._fade = max(0.0, self._fade - dt * 3.0)
        for p in self._popups:
            p["y"] -= 42 * dt
            p["life"] -= dt
        self._popups = [p for p in self._popups if p["life"] > 0]

    # --- Frame --------------------------------------------------------------

    def draw(self, game: Game, alpha: float = 1.0) -> None:
        """Paint one full frame; `alpha` interpolates the snake between ticks."""
        if game.state is not self._prev_state:
            self._fade = 1.0
            self._prev_state = game.state

        draw.vertical_gradient(self.canvas, self.theme.bg_top, self.theme.bg_bottom)
        if game.state is GameState.MENU:
            self._draw_menu(game)
        elif game.state is GameState.MODE_SELECT:
            self._draw_mode_select(game)
        elif game.state is GameState.INFO:
            self._draw_info()
        else:
            self._draw_board()
            self._draw_walls(game)
            self._draw_portals(game)
            self._draw_food(game)
            self._draw_snake(game, alpha)
            self._draw_hud(game)
            self.particles.draw(self.canvas)
            self._draw_popups()
            self._draw_overlay(game)

        # Composite to the display with the shake offset, then flash + fade.
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.canvas, self.camera.offset())
        self.camera.draw_flash(self.screen)
        if self._fade > 0:
            veil = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            veil.fill((16, 20, 34, int(180 * self._fade)))
            self.screen.blit(veil, (0, 0))
        pygame.display.flip()

    # --- Layout helpers -----------------------------------------------------

    @property
    def board_rect(self) -> pygame.Rect:
        return pygame.Rect(0, HUD_HEIGHT, GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE)

    def _blit_centered(self, surf: pygame.Surface, y: int) -> None:
        self.canvas.blit(surf, surf.get_rect(center=(self.canvas.get_width() // 2, y)))

    def _cell_rect(self, cell: tuple[int, int]) -> pygame.Rect:
        x, y = cell
        return pygame.Rect(x * CELL_SIZE, HUD_HEIGHT + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

    def _cell_center(self, fx: float, fy: float) -> tuple[int, int]:
        return (round((fx + 0.5) * CELL_SIZE), round(HUD_HEIGHT + (fy + 0.5) * CELL_SIZE))

    def _now(self) -> float:
        return pygame.time.get_ticks() / 1000.0

    # --- Playfield ----------------------------------------------------------

    def _draw_board(self) -> None:
        board = self.board_rect
        draw.rounded_shadow_panel(
            self.canvas, board, self.theme.board_edge, self.theme.board_shadow, radius=18
        )
        draw.checkerboard(
            self.canvas, board.inflate(-8, -8), CELL_SIZE,
            self.theme.board_light, self.theme.board_dark,
        )

    def _draw_walls(self, game: Game) -> None:
        for cell in game.level.walls:
            draw.wall(self.canvas, self._cell_rect(cell), self.theme)

    def _draw_portals(self, game: Game) -> None:
        for index, (a, b) in enumerate(game.level.portals):
            color = COLOR_PORTALS[index % len(COLOR_PORTALS)]
            for cell in (a, b):
                draw.portal(
                    self.canvas, self._cell_rect(cell).center, self._radius, color, self._now()
                )

    def _draw_food(self, game: Game) -> None:
        if game.food.position is None:
            return
        draw.food(
            self.canvas, self._cell_rect(game.food.position).center,
            int(CELL_SIZE * 0.4), self.theme, self._now(),
        )

    def _draw_snake(self, game: Game, alpha: float) -> None:
        positions = game.snake.interpolated_positions(alpha, game.grid_size)
        centers = [self._cell_center(fx, fy) for fx, fy in positions]
        draw.snake(
            self.canvas, centers, self._radius, self.skin, self.theme,
            game.snake.direction.value, self._now(),
            head_scale=1.0 + 0.45 * self._eat_pulse,
        )

    # --- HUD & overlays -----------------------------------------------------

    def _pill(self, text: str, font: pygame.font.Font) -> pygame.Surface:
        label = draw.outline_text(font, text, self.theme.text, self.theme.text_light, 2)
        pad_x, pad_y = 16, 6
        pill = pygame.Surface(
            (label.get_width() + pad_x * 2, label.get_height() + pad_y * 2), pygame.SRCALPHA
        )
        pygame.draw.rect(
            pill, self.theme.ui_panel, pill.get_rect(), border_radius=pill.get_height() // 2
        )
        pill.blit(label, (pad_x, pad_y))
        return pill

    def _draw_hud(self, game: Game) -> None:
        score = self._pill(f"Score {game.score}", self._font_hud)
        self.canvas.blit(score, (10, (HUD_HEIGHT - score.get_height()) // 2))

        # Centre pill: the Adventure level, or a timer, or the mode name.
        if game.mode.uses_levels:
            center_text = f"Lv {game.level_index + 1}  {game.level.name}"
        elif game.time_left is not None:
            center_text = f"Time {int(game.time_left)}s"
        else:
            center_text = game.mode.name
        center = self._pill(center_text, self._font_hud)
        self.canvas.blit(
            center, ((self.canvas.get_width() - center.get_width()) // 2,
                     (HUD_HEIGHT - center.get_height()) // 2)
        )

        best = self._pill(f"Best {game.high_score}", self._font_hud)
        self.canvas.blit(
            best, (self.canvas.get_width() - best.get_width() - 10,
                   (HUD_HEIGHT - best.get_height()) // 2)
        )

    def _draw_popups(self) -> None:
        for p in self._popups:
            surf = draw.outline_text(
                self._font_hud, p["text"], p["color"], self.theme.text_light, 2
            )
            surf.set_alpha(int(255 * min(1.0, p["life"] / p["max"])))
            self.canvas.blit(surf, surf.get_rect(center=(int(p["x"]), int(p["y"]))))

    def _draw_overlay(self, game: Game) -> None:
        messages = {
            GameState.PAUSED: ("Paused", "Press P or Space to resume"),
            GameState.LEVEL_CLEARED: (
                f"Level {game.level_index + 1} Complete!", "Press Enter for the next level"),
            GameState.GAME_OVER: ("Game Over", "Press Enter or R to play again"),
            GameState.WON: ("You Win!", "Press Enter or R to play again"),
        }
        if game.state not in messages:
            return
        title_text, subtitle_text = messages[game.state]
        veil = pygame.Surface(self.canvas.get_size(), pygame.SRCALPHA)
        veil.fill((20, 24, 40, 150))
        self.canvas.blit(veil, (0, 0))
        cx, cy = self.canvas.get_width() // 2, self.canvas.get_height() // 2
        title = draw.outline_text(
            self._font_title, title_text, self.theme.accent, self.theme.text_light, 3)
        self.canvas.blit(title, title.get_rect(center=(cx, cy - 24)))
        subtitle = draw.outline_text(
            self._font_subtitle, subtitle_text, self.theme.text_light, self.theme.text, 2)
        self.canvas.blit(subtitle, subtitle.get_rect(center=(cx, cy + 28)))

    # --- Menu & info --------------------------------------------------------

    def _draw_menu(self, game: Game) -> None:
        title = draw.outline_text(
            self._font_title, WINDOW_TITLE, self.skin.light, self.skin.outline, 3)
        self._blit_centered(title, self.canvas.get_height() // 4)

        first_y = self.canvas.get_height() // 2
        for index, option in enumerate(MENU_OPTIONS):
            selected = index == game.menu_index
            if selected:
                label = draw.outline_text(
                    self._font_menu, f"> {option} <", self.theme.accent, self.theme.text_light, 3)
                scale = 1.0 + 0.06 * math.sin(self._now() * 6.0)  # springy bounce
                label = pygame.transform.rotozoom(label, 0, scale)
            else:
                label = draw.outline_text(
                    self._font_menu, option, self.theme.text_light, self.theme.text_dim, 2)
            self._blit_centered(label, first_y + index * 52)

        hint = draw.outline_text(
            self._font_subtitle, "Arrows to choose · Enter to select · Esc to quit",
            self.theme.text, self.theme.text_light, 2)
        self._blit_centered(hint, self.canvas.get_height() - 40)

    def _draw_mode_select(self, game: Game) -> None:
        title = draw.outline_text(
            self._font_title, "Choose a Mode", self.skin.light, self.skin.outline, 3)
        self._blit_centered(title, 74)

        top = 150
        row_h = 78
        panel_w = self.canvas.get_width() - 80
        for index, mode in enumerate(MODES):
            selected = index == game.mode_index
            y = top + index * row_h
            panel = pygame.Rect((self.canvas.get_width() - panel_w) // 2, y, panel_w, row_h - 14)
            fill = self.theme.accent if selected else self.theme.ui_panel
            draw.rounded_shadow_panel(
                self.canvas, panel, fill, self.theme.ui_panel_shadow, radius=16
            )
            name = draw.outline_text(
                self._font_menu, mode.name,
                self.theme.text_light if selected else self.theme.text,
                self.theme.text if selected else self.theme.text_light, 2,
            )
            self.canvas.blit(name, (panel.x + 20, panel.y + 8))
            tag = self._font_subtitle.render(mode.tagline, True,
                                             self.theme.text_light if selected else self.theme.text_dim)
            self.canvas.blit(tag, (panel.x + 20, panel.y + 40))

        hint = draw.outline_text(
            self._font_subtitle, "Arrows to choose · Enter to start · Esc to go back",
            self.theme.text, self.theme.text_light, 2)
        self._blit_centered(hint, self.canvas.get_height() - 30)

    def _draw_info(self) -> None:
        title = draw.outline_text(
            self._font_title, "How to Play", self.skin.light, self.skin.outline, 3)
        self._blit_centered(title, 70)
        line_height = FONT_SIZE_BODY + 12
        y = (self.canvas.get_height() - line_height * len(INFO_LINES)) // 2 + 20
        for line in INFO_LINES:
            if line:
                rendered = draw.outline_text(
                    self._font_body, line, self.theme.text, self.theme.text_light, 2)
                self._blit_centered(rendered, y)
            y += line_height
        hint = draw.outline_text(
            self._font_subtitle, "Enter or Esc to go back",
            self.theme.text, self.theme.text_light, 2)
        self._blit_centered(hint, self.canvas.get_height() - 36)
