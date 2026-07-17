"""Rendering of a Game onto a pygame surface. Reads state, never mutates it."""

import pygame

from config import (
    CELL_SIZE,
    COLOR_BACKGROUND,
    COLOR_FOOD,
    COLOR_FOOD_WARNING,
    COLOR_GRID,
    COLOR_HUD_BACKGROUND,
    COLOR_MENU_SELECTED,
    COLOR_OVERLAY,
    COLOR_PORTALS,
    COLOR_SNAKE_BODY,
    COLOR_SNAKE_HEAD,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_WALL,
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
    GameState,
)
from engine.game import Game


class Renderer:
    """Draws the game to a surface, offsetting the board below the HUD."""

    def __init__(self, surface: pygame.Surface) -> None:
        """Bind the renderer to a target surface and load fonts."""
        self.surface = surface
        self._font_hud = pygame.font.Font(FONT_NAME, FONT_SIZE_HUD)
        self._font_title = pygame.font.Font(FONT_NAME, FONT_SIZE_TITLE)
        self._font_subtitle = pygame.font.Font(FONT_NAME, FONT_SIZE_SUBTITLE)
        self._font_menu = pygame.font.Font(FONT_NAME, FONT_SIZE_MENU)
        self._font_body = pygame.font.Font(FONT_NAME, FONT_SIZE_BODY)

    def draw(self, game: Game, alpha: float = 1.0) -> None:
        """Paint one full frame; `alpha` interpolates the snake between ticks."""
        if game.state is GameState.MENU:
            self._draw_menu(game)
        elif game.state is GameState.INFO:
            self._draw_info()
        else:
            self.surface.fill(COLOR_BACKGROUND)
            self._draw_grid()
            self._draw_walls(game)
            self._draw_portals(game)
            self._draw_food(game)
            self._draw_snake(game, alpha)
            self._draw_hud(game)
            self._draw_overlay(game)
        pygame.display.flip()

    def _blit_centered(self, surface: pygame.Surface, y: int) -> None:
        """Blit `surface` horizontally centered at vertical position `y`."""
        self.surface.blit(surface, surface.get_rect(center=(self.surface.get_width() // 2, y)))

    def _draw_menu(self, game: Game) -> None:
        """Draw the landing screen with the selectable options."""
        self.surface.fill(COLOR_BACKGROUND)
        center_x = self.surface.get_width() // 2

        title = self._font_title.render(WINDOW_TITLE, True, COLOR_SNAKE_HEAD)
        self._blit_centered(title, self.surface.get_height() // 4)

        first_y = self.surface.get_height() // 2
        for index, option in enumerate(MENU_OPTIONS):
            selected = index == game.menu_index
            color = COLOR_MENU_SELECTED if selected else COLOR_TEXT_DIM
            label = f"> {option} <" if selected else option
            item = self._font_menu.render(label, True, color)
            self._blit_centered(item, first_y + index * 48)

        hint = self._font_subtitle.render(
            "Arrows to choose · Enter to select · Esc to quit", True, COLOR_TEXT_DIM
        )
        self._blit_centered(hint, self.surface.get_height() - 40)

    def _draw_info(self) -> None:
        """Draw the how-to-play screen."""
        self.surface.fill(COLOR_BACKGROUND)

        title = self._font_title.render("How to Play", True, COLOR_SNAKE_HEAD)
        self._blit_centered(title, 70)

        line_height = FONT_SIZE_BODY + 12
        block_height = line_height * len(INFO_LINES)
        y = (self.surface.get_height() - block_height) // 2 + 20
        for line in INFO_LINES:
            rendered = self._font_body.render(line, True, COLOR_TEXT)
            self._blit_centered(rendered, y)
            y += line_height

        hint = self._font_subtitle.render(
            "Enter or Esc to go back", True, COLOR_TEXT_DIM
        )
        self._blit_centered(hint, self.surface.get_height() - 36)

    def _cell_rect(self, cell: tuple[int, int]) -> pygame.Rect:
        """Pixel rectangle for a grid cell, shifted down past the HUD."""
        x, y = cell
        return pygame.Rect(
            x * CELL_SIZE, HUD_HEIGHT + y * CELL_SIZE, CELL_SIZE, CELL_SIZE
        )

    def _draw_grid(self) -> None:
        """Draw faint grid lines over the playfield."""
        for gx in range(GRID_WIDTH + 1):
            x = gx * CELL_SIZE
            pygame.draw.line(
                self.surface, COLOR_GRID, (x, HUD_HEIGHT), (x, self.surface.get_height())
            )
        for gy in range(GRID_HEIGHT + 1):
            y = HUD_HEIGHT + gy * CELL_SIZE
            pygame.draw.line(
                self.surface, COLOR_GRID, (0, y), (self.surface.get_width(), y)
            )

    def _draw_walls(self, game: Game) -> None:
        """Draw the current level's walls."""
        for cell in game.level.walls:
            pygame.draw.rect(self.surface, COLOR_WALL, self._cell_rect(cell))

    def _draw_portals(self, game: Game) -> None:
        """Draw each portal pair as a ringed cell in its own hue."""
        for index, (a, b) in enumerate(game.level.portals):
            color = COLOR_PORTALS[index % len(COLOR_PORTALS)]
            for cell in (a, b):
                pygame.draw.rect(self.surface, color, self._cell_rect(cell), width=4)
                pygame.draw.rect(
                    self.surface, color, self._cell_rect(cell).inflate(-14, -14)
                )

    def _draw_food(self, game: Game) -> None:
        """Draw the food, flashing a warning tint when it's about to teleport."""
        if game.food.position is None:
            return
        color = COLOR_FOOD
        ttl = game.level.food_ttl
        if ttl is not None and game.food_timer >= ttl * 0.6:
            color = COLOR_FOOD_WARNING
        pygame.draw.rect(
            self.surface, color, self._cell_rect(game.food.position).inflate(-4, -4)
        )

    def _cell_rect_f(self, fx: float, fy: float) -> pygame.Rect:
        """Pixel rectangle for a fractional grid position (for interpolation)."""
        return pygame.Rect(
            round(fx * CELL_SIZE),
            round(HUD_HEIGHT + fy * CELL_SIZE),
            CELL_SIZE,
            CELL_SIZE,
        )

    def _draw_snake(self, game: Game, alpha: float = 1.0) -> None:
        """Draw the snake at its interpolated position, head highlighted."""
        positions = game.snake.interpolated_positions(alpha, game.grid_size)
        for index, (fx, fy) in enumerate(positions):
            color = COLOR_SNAKE_HEAD if index == 0 else COLOR_SNAKE_BODY
            pygame.draw.rect(self.surface, color, self._cell_rect_f(fx, fy).inflate(-2, -2))

    def _draw_hud(self, game: Game) -> None:
        """Draw the score bar across the top."""
        bar = pygame.Rect(0, 0, self.surface.get_width(), HUD_HEIGHT)
        self.surface.fill(COLOR_HUD_BACKGROUND, bar)

        score = self._font_hud.render(f"Score {game.score}", True, COLOR_TEXT)
        self.surface.blit(score, (12, (HUD_HEIGHT - score.get_height()) // 2))

        level = self._font_hud.render(
            f"Lv {game.level_index + 1}  {game.level.name}", True, COLOR_MENU_SELECTED
        )
        self.surface.blit(
            level,
            (
                (self.surface.get_width() - level.get_width()) // 2,
                (HUD_HEIGHT - level.get_height()) // 2,
            ),
        )

        best = self._font_hud.render(f"Best {game.high_score}", True, COLOR_TEXT_DIM)
        self.surface.blit(
            best,
            (
                self.surface.get_width() - best.get_width() - 12,
                (HUD_HEIGHT - best.get_height()) // 2,
            ),
        )

    def _draw_overlay(self, game: Game) -> None:
        """Draw the pause / level-cleared / game-over / win overlay."""
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
        veil.fill(COLOR_OVERLAY)
        self.surface.blit(veil, (0, 0))

        center_x = self.surface.get_width() // 2
        center_y = self.surface.get_height() // 2

        title = self._font_title.render(title_text, True, COLOR_TEXT)
        self.surface.blit(
            title, title.get_rect(center=(center_x, center_y - 20))
        )
        subtitle = self._font_subtitle.render(subtitle_text, True, COLOR_TEXT_DIM)
        self.surface.blit(
            subtitle, subtitle.get_rect(center=(center_x, center_y + 24))
        )
