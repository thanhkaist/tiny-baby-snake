"""Cartoon rendering of a Game onto a pygame surface.

Owns layout and state-to-screen mapping; the actual "look" of the snake, food,
walls, and text lives in fx/draw.py so the style can evolve in one place.
"""

import pygame

from config import (
    CELL_SIZE,
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
    WINDOW_TITLE,
    COLOR_PORTALS,
    GameState,
)
from engine.game import Game
from fx import draw
from fx.theme import DEFAULT_THEME, SKINS, Skin, Theme


class Renderer:
    """Draws the game to a surface in a playful cartoon style."""

    def __init__(
        self, surface: pygame.Surface, theme: Theme = DEFAULT_THEME, skin: Skin = SKINS[0]
    ) -> None:
        """Bind the renderer to a target surface and load fonts."""
        self.surface = surface
        self.theme = theme
        self.skin = skin
        self._font_hud = pygame.font.Font(FONT_NAME, FONT_SIZE_HUD)
        self._font_title = pygame.font.Font(FONT_NAME, FONT_SIZE_TITLE)
        self._font_subtitle = pygame.font.Font(FONT_NAME, FONT_SIZE_SUBTITLE)
        self._font_menu = pygame.font.Font(FONT_NAME, FONT_SIZE_MENU)
        self._font_body = pygame.font.Font(FONT_NAME, FONT_SIZE_BODY)
        self._radius = int(CELL_SIZE * 0.46)

    @property
    def board_rect(self) -> pygame.Rect:
        """Pixel rectangle of the playfield (below the HUD band)."""
        return pygame.Rect(0, HUD_HEIGHT, GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE)

    def _now(self) -> float:
        """Seconds since start, for idle animations."""
        return pygame.time.get_ticks() / 1000.0

    def draw(self, game: Game, alpha: float = 1.0) -> None:
        """Paint one full frame; `alpha` interpolates the snake between ticks."""
        draw.vertical_gradient(self.surface, self.theme.bg_top, self.theme.bg_bottom)
        if game.state is GameState.MENU:
            self._draw_menu(game)
        elif game.state is GameState.INFO:
            self._draw_info()
        else:
            self._draw_board()
            self._draw_walls(game)
            self._draw_portals(game)
            self._draw_food(game)
            self._draw_snake(game, alpha)
            self._draw_hud(game)
            self._draw_overlay(game)
        pygame.display.flip()

    # --- Layout helpers -----------------------------------------------------

    def _blit_centered(self, surf: pygame.Surface, y: int) -> None:
        self.surface.blit(surf, surf.get_rect(center=(self.surface.get_width() // 2, y)))

    def _cell_rect(self, cell: tuple[int, int]) -> pygame.Rect:
        x, y = cell
        return pygame.Rect(x * CELL_SIZE, HUD_HEIGHT + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

    def _cell_center(self, fx: float, fy: float) -> tuple[int, int]:
        return (
            round((fx + 0.5) * CELL_SIZE),
            round(HUD_HEIGHT + (fy + 0.5) * CELL_SIZE),
        )

    # --- Playfield ----------------------------------------------------------

    def _draw_board(self) -> None:
        board = self.board_rect
        draw.rounded_shadow_panel(
            self.surface, board, self.theme.board_edge, self.theme.board_shadow, radius=18
        )
        inner = board.inflate(-8, -8)
        draw.checkerboard(
            self.surface, inner, CELL_SIZE, self.theme.board_light, self.theme.board_dark
        )

    def _draw_walls(self, game: Game) -> None:
        for cell in game.level.walls:
            draw.wall(self.surface, self._cell_rect(cell), self.theme)

    def _draw_portals(self, game: Game) -> None:
        for index, (a, b) in enumerate(game.level.portals):
            color = COLOR_PORTALS[index % len(COLOR_PORTALS)]
            for cell in (a, b):
                rect = self._cell_rect(cell)
                draw.portal(self.surface, rect.center, self._radius, color, self._now())

    def _draw_food(self, game: Game) -> None:
        if game.food.position is None:
            return
        rect = self._cell_rect(game.food.position)
        draw.food(self.surface, rect.center, int(CELL_SIZE * 0.4), self.theme, self._now())

    def _draw_snake(self, game: Game, alpha: float) -> None:
        positions = game.snake.interpolated_positions(alpha, game.grid_size)
        centers = [self._cell_center(fx, fy) for fx, fy in positions]
        draw.snake(
            self.surface,
            centers,
            self._radius,
            self.skin,
            self.theme,
            game.snake.direction.value,
            self._now(),
        )

    # --- HUD & overlays -----------------------------------------------------

    def _pill(self, text: str, font: pygame.font.Font) -> pygame.Surface:
        """A rounded white badge holding sticker text."""
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
        self.surface.blit(score, (10, (HUD_HEIGHT - score.get_height()) // 2))

        level = self._pill(f"Lv {game.level_index + 1}  {game.level.name}", self._font_hud)
        self.surface.blit(
            level,
            ((self.surface.get_width() - level.get_width()) // 2,
             (HUD_HEIGHT - level.get_height()) // 2),
        )

        best = self._pill(f"Best {game.high_score}", self._font_hud)
        self.surface.blit(
            best,
            (self.surface.get_width() - best.get_width() - 10,
             (HUD_HEIGHT - best.get_height()) // 2),
        )

    def _draw_overlay(self, game: Game) -> None:
        messages = {
            GameState.PAUSED: ("Paused", "Press P or Space to resume"),
            GameState.LEVEL_CLEARED: (
                f"Level {game.level_index + 1} Complete!",
                "Press Enter for the next level",
            ),
            GameState.GAME_OVER: ("Game Over", "Press Enter or R to play again"),
            GameState.WON: ("You Win!", "Press Enter or R to play again"),
        }
        if game.state not in messages:
            return
        title_text, subtitle_text = messages[game.state]

        veil = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        veil.fill((20, 24, 40, 150))
        self.surface.blit(veil, (0, 0))

        cx = self.surface.get_width() // 2
        cy = self.surface.get_height() // 2
        title = draw.outline_text(
            self._font_title, title_text, self.theme.accent, self.theme.text_light, 3
        )
        self.surface.blit(title, title.get_rect(center=(cx, cy - 24)))
        subtitle = draw.outline_text(
            self._font_subtitle, subtitle_text, self.theme.text_light, self.theme.text, 2
        )
        self.surface.blit(subtitle, subtitle.get_rect(center=(cx, cy + 28)))

    # --- Menu & info --------------------------------------------------------

    def _draw_menu(self, game: Game) -> None:
        cx = self.surface.get_width() // 2
        title = draw.outline_text(
            self._font_title, WINDOW_TITLE, self.skin.light, self.skin.outline, 3
        )
        self._blit_centered(title, self.surface.get_height() // 4)

        first_y = self.surface.get_height() // 2
        for index, option in enumerate(MENU_OPTIONS):
            selected = index == game.menu_index
            font = self._font_menu
            if selected:
                label = draw.outline_text(font, f"> {option} <", self.theme.accent,
                                          self.theme.text_light, 3)
            else:
                label = draw.outline_text(font, option, self.theme.text_light,
                                          self.theme.text_dim, 2)
            self._blit_centered(label, first_y + index * 52)

        hint = draw.outline_text(
            self._font_subtitle,
            "Arrows to choose · Enter to select · Esc to quit",
            self.theme.text, self.theme.text_light, 2,
        )
        self._blit_centered(hint, self.surface.get_height() - 40)

    def _draw_info(self) -> None:
        title = draw.outline_text(
            self._font_title, "How to Play", self.skin.light, self.skin.outline, 3
        )
        self._blit_centered(title, 70)

        line_height = FONT_SIZE_BODY + 12
        y = (self.surface.get_height() - line_height * len(INFO_LINES)) // 2 + 20
        for line in INFO_LINES:
            if line:
                rendered = draw.outline_text(
                    self._font_body, line, self.theme.text, self.theme.text_light, 2
                )
                self._blit_centered(rendered, y)
            y += line_height

        hint = draw.outline_text(
            self._font_subtitle, "Enter or Esc to go back",
            self.theme.text, self.theme.text_light, 2,
        )
        self._blit_centered(hint, self.surface.get_height() - 36)
