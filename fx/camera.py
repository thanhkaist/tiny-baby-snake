"""Screen shake and full-screen colour flashes.

`update()` is pure; the draw helpers touch pygame. Shake uses a decaying
"trauma" value squared, which feels punchy without being nauseating.
"""

import random

import pygame

Color = tuple[int, int, int]


class Camera:
    """A shake + flash controller for the whole frame."""

    def __init__(self, max_offset: int = 14, decay: float = 1.6) -> None:
        self.trauma = 0.0
        self.max_offset = max_offset
        self.decay = decay
        self.enabled = True  # honours the player's screen-shake setting
        self._flashes: list[list] = []  # [color, remaining, duration, peak_alpha]

    def shake(self, amount: float) -> None:
        """Add trauma (0..1); stacks up to a full shake."""
        self.trauma = min(1.0, self.trauma + amount)

    def flash(self, color: Color, duration: float = 0.3, peak_alpha: int = 130) -> None:
        """Queue a fading full-screen colour wash."""
        self._flashes.append([color, duration, duration, peak_alpha])

    def update(self, dt: float) -> None:
        """Decay trauma and advance flashes."""
        self.trauma = max(0.0, self.trauma - self.decay * dt)
        for f in self._flashes:
            f[1] -= dt
        self._flashes = [f for f in self._flashes if f[1] > 0]

    def offset(self) -> tuple[int, int]:
        """Current shake offset in pixels (0,0 when calm or disabled)."""
        amount = self.trauma * self.trauma
        if amount <= 0 or not self.enabled:
            return (0, 0)
        return (
            int(random.uniform(-1, 1) * self.max_offset * amount),
            int(random.uniform(-1, 1) * self.max_offset * amount),
        )

    def draw_flash(self, surface: pygame.Surface) -> None:
        """Blit any active colour flashes over the frame."""
        for color, remaining, duration, peak in self._flashes:
            alpha = int(peak * (remaining / duration))
            if alpha <= 0:
                continue
            wash = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            wash.fill((*color, alpha))
            surface.blit(wash, (0, 0))
