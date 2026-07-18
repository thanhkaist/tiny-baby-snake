"""Cartoon rendering with juice: particles, screen shake, pop-ups, transitions.

Scene content is drawn to an off-screen canvas, then composited to the display
with a shake offset so effects can rattle the whole frame. The "look" lives in
fx/draw.py; the "feel" (particles, camera) lives in fx/particles.py & camera.py.
"""

import math

import pygame

from config import (
    BONUS_POINTS,
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
from engine.achievements import ACHIEVEMENTS
from engine.game import Game
from engine.modes import MODES
from engine.powerups import SPECS
from engine.profile import SETTING_FIELDS
from fx import draw
from fx.camera import Camera
from fx.particles import ParticleSystem
from fx.theme import DEFAULT_THEME, SKINS, Skin, Theme, skin_by_key


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
        self._toasts: list[dict] = []
        self._eat_pulse = 0.0
        self._prev_state = None
        self._fade = 0.0

    def apply_profile(self, profile) -> None:
        """Adopt the profile's selected skin and shake preference."""
        self.skin = skin_by_key(profile.selected_skin)
        self.camera.enabled = profile.settings.screen_shake

    # --- Effects lifecycle --------------------------------------------------

    def spawn_events(self, game: Game) -> None:
        """React to one tick's game events by spawning matching effects."""
        for ach in game.new_achievements:
            self._toasts.append({"title": "Achievement!", "name": ach.name,
                                 "life": 3.2, "max": 3.2})
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
            elif event is SoundEvent.BONUS:
                self.particles.emit_burst(*head, self.theme.food_bonus, count=26, speed=280)
                self._popups.append(
                    {"text": f"+{BONUS_POINTS}", "x": head[0], "y": head[1] - CELL_SIZE,
                     "life": 1.0, "max": 1.0, "color": self.theme.food_bonus})
                self.camera.shake(0.32)
            elif event is SoundEvent.POWERUP:
                self.particles.emit_burst(*head, (255, 255, 255), count=26, speed=260)
                self.camera.shake(0.26)
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
        for toast in self._toasts:
            toast["life"] -= dt
        self._toasts = [t for t in self._toasts if t["life"] > 0]

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
        elif game.state is GameState.SETTINGS:
            self._draw_settings(game)
        elif game.state is GameState.SKINS:
            self._draw_skins(game)
        elif game.state is GameState.STATS:
            self._draw_stats(game)
        elif game.state is GameState.INFO:
            self._draw_info()
        else:
            self._draw_board()
            self._draw_walls(game)
            self._draw_portals(game)
            self._draw_food(game)
            self._draw_bonus(game)
            self._draw_powerup(game)
            self._draw_snake(game, alpha)
            self._draw_hud(game)
            self._draw_effects(game)
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
        self._draw_toasts()
        pygame.display.flip()

    def _draw_toasts(self) -> None:
        """Slide-in achievement toasts, top-right of the screen."""
        for i, toast in enumerate(self._toasts):
            appear = min(1.0, (toast["max"] - toast["life"]) * 4)
            fade = min(1.0, toast["life"])
            w, h = 240, 54
            x = self.screen.get_width() - int(w * appear) - 10
            y = 56 + i * (h + 8)
            panel = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(panel, (*self.theme.accent, int(240 * fade)),
                             panel.get_rect(), border_radius=12)
            title = self._font_subtitle.render(toast["title"], True, self.theme.text)
            name = self._font_hud.render(toast["name"], True, self.theme.text_light)
            panel.blit(title, (14, 6))
            panel.blit(name, (14, 26))
            panel.set_alpha(int(255 * fade))
            self.screen.blit(panel, (x, y))

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

    def _draw_bonus(self, game: Game) -> None:
        if game.bonus_pos is None:
            return
        draw.food(
            self.canvas, self._cell_rect(game.bonus_pos).center,
            int(CELL_SIZE * 0.42), self.theme, self._now(), bonus=True,
        )

    def _draw_powerup(self, game: Game) -> None:
        if game.powerup_pos is None or game.powerup_kind is None:
            return
        spec = SPECS[game.powerup_kind]
        rect = self._cell_rect(game.powerup_pos).inflate(-3, -3)
        pygame.draw.rect(self.canvas, self.theme.text_light, rect.inflate(4, 4), border_radius=9)
        pygame.draw.rect(self.canvas, spec.color, rect, border_radius=8)
        letter = draw.outline_text(
            self._font_hud, spec.letter, self.theme.text_light, self.theme.text, 2)
        self.canvas.blit(letter, letter.get_rect(center=rect.center))

    def _draw_effects(self, game: Game) -> None:
        """Small badges for active timed power-ups, bottom-left of the board."""
        x = 12
        y = self.canvas.get_height() - 32
        for kind in game.effects:
            spec = SPECS[kind]
            badge = pygame.Rect(x, y, 26, 26)
            pygame.draw.rect(self.canvas, self.theme.text_light, badge.inflate(4, 4),
                             border_radius=8)
            pygame.draw.rect(self.canvas, spec.color, badge, border_radius=7)
            letter = self._font_subtitle.render(spec.letter, True, self.theme.text_light)
            self.canvas.blit(letter, letter.get_rect(center=badge.center))
            x += 34

    def _draw_snake(self, game: Game, alpha: float) -> None:
        positions = game.snake.interpolated_positions(alpha, game.grid_size)
        centers = [self._cell_center(fx, fy) for fx, fy in positions]
        draw.snake(
            self.canvas, centers, self._radius, self.skin, self.theme,
            game.snake.direction.value, self._now(),
            head_scale=1.0 + 0.45 * self._eat_pulse,
            max_link=CELL_SIZE * 1.5,
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
            GameState.GAME_OVER: ("Game Over", "Enter or R to play again · Esc for menu"),
            GameState.WON: ("You Win!", "Enter or R to play again · Esc for menu"),
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

    def _draw_settings(self, game) -> None:
        title = draw.outline_text(
            self._font_title, "Settings", self.skin.light, self.skin.outline, 3)
        self._blit_centered(title, 74)
        top, row_h = 160, 74
        panel_w = self.canvas.get_width() - 90
        for i, (key, label) in enumerate(SETTING_FIELDS):
            selected = i == game.settings_index
            y = top + i * row_h
            panel = pygame.Rect((self.canvas.get_width() - panel_w) // 2, y, panel_w, row_h - 16)
            draw.rounded_shadow_panel(
                self.canvas, panel, self.theme.accent if selected else self.theme.ui_panel,
                self.theme.ui_panel_shadow, radius=14)
            name = self._font_menu.render(
                label, True, self.theme.text_light if selected else self.theme.text)
            self.canvas.blit(name, (panel.x + 20, panel.centery - name.get_height() // 2))
            value = getattr(game.profile.settings, key)
            if key == "screen_shake":
                text = "On" if value else "Off"
                v = self._font_menu.render(text, True, self.theme.text_light if selected else self.theme.text)
                self.canvas.blit(v, (panel.right - v.get_width() - 20,
                                     panel.centery - v.get_height() // 2))
            else:
                self._volume_bar(panel, value)
        hint = draw.outline_text(
            self._font_subtitle, "Up/Down select · Left/Right change · Esc back",
            self.theme.text, self.theme.text_light, 2)
        self._blit_centered(hint, self.canvas.get_height() - 28)

    def _volume_bar(self, panel: pygame.Rect, value: float) -> None:
        bar = pygame.Rect(panel.right - 190, panel.centery - 9, 170, 18)
        pygame.draw.rect(self.canvas, self.theme.ui_panel_shadow, bar, border_radius=9)
        fill = bar.copy()
        fill.width = max(9, int(bar.width * value))
        pygame.draw.rect(self.canvas, self.skin.light, fill, border_radius=9)

    def _draw_skins(self, game) -> None:
        title = draw.outline_text(
            self._font_title, "Skins", self.skin.light, self.skin.outline, 3)
        self._blit_centered(title, 74)
        cols = 3
        cell_w, cell_h = 150, 150
        gap = 20
        grid_w = cols * cell_w + (cols - 1) * gap
        x0 = (self.canvas.get_width() - grid_w) // 2
        y0 = 150
        for i, skin in enumerate(SKINS):
            r, c = divmod(i, cols)
            x = x0 + c * (cell_w + gap)
            y = y0 + r * (cell_h + gap)
            card = pygame.Rect(x, y, cell_w, cell_h)
            unlocked = skin.key in game.profile.unlocked_skins
            selected_cursor = i == game.skins_index
            equipped = skin.key == game.profile.selected_skin
            border = self.theme.accent if selected_cursor else self.theme.ui_panel_shadow
            pygame.draw.rect(self.canvas, border, card.inflate(8, 8), border_radius=16)
            pygame.draw.rect(self.canvas, self.theme.ui_panel, card, border_radius=14)
            # Mini snake swatch.
            centers = [(card.centerx - 24, card.centery - 6), (card.centerx, card.centery - 6),
                       (card.centerx + 24, card.centery - 6)]
            draw.snake(self.canvas, centers, 16, skin, self.theme, (1, 0), self._now())
            name = self._font_subtitle.render(skin.name, True, self.theme.text)
            self.canvas.blit(name, name.get_rect(center=(card.centerx, card.bottom - 24)))
            if equipped:
                tag = self._font_subtitle.render("Equipped", True, self.theme.accent)
                self.canvas.blit(tag, tag.get_rect(center=(card.centerx, card.top + 16)))
            if not unlocked:
                veil = pygame.Surface(card.size, pygame.SRCALPHA)
                veil.fill((30, 34, 48, 150))
                lock = self._font_menu.render("Locked", True, self.theme.text_light)
                veil.blit(lock, lock.get_rect(center=(cell_w // 2, cell_h // 2)))
                self.canvas.blit(veil, card.topleft)
        hint = draw.outline_text(
            self._font_subtitle, "Arrows to move · Enter to equip · Esc back",
            self.theme.text, self.theme.text_light, 2)
        self._blit_centered(hint, self.canvas.get_height() - 28)

    def _draw_stats(self, game) -> None:
        title = draw.outline_text(
            self._font_title, "Stats", self.skin.light, self.skin.outline, 3)
        self._blit_centered(title, 64)
        s = game.profile.stats
        rows = [
            ("Games played", s["games_played"]),
            ("Food eaten", s["total_food"]),
            ("Best length", s["best_length"]),
            ("Power-ups grabbed", s["powerups_grabbed"]),
            ("Total score", s["total_score"]),
        ]
        y = 128
        for label, value in rows:
            lab = self._font_hud.render(label, True, self.theme.text)
            val = self._font_hud.render(str(value), True, self.theme.text_light)
            self.canvas.blit(lab, (60, y))
            self.canvas.blit(val, (self.canvas.get_width() - 60 - val.get_width(), y))
            y += 34
        head = draw.outline_text(
            self._font_menu, "Achievements", self.skin.light, self.skin.outline, 2)
        self.canvas.blit(head, (60, y + 6))
        y += 52
        for ach in ACHIEVEMENTS:
            got = ach.id in game.profile.achievements
            color = self.theme.text if got else self.theme.text_dim
            mark = "*" if got else "-"
            line = self._font_subtitle.render(f"{mark} {ach.name} — {ach.description}", True, color)
            self.canvas.blit(line, (60, y))
            y += 26
        hint = draw.outline_text(
            self._font_subtitle, "Esc to go back", self.theme.text, self.theme.text_light, 2)
        self._blit_centered(hint, self.canvas.get_height() - 24)

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
