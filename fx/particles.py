"""A lightweight particle system for bursts, poofs, and confetti.

`update()` is pure math (no pygame) so it can be unit-tested; `draw()` renders
the live particles. Positions are in the renderer's canvas pixel space.
"""

import math
import random
from dataclasses import dataclass

import pygame
import pygame.gfxdraw

Color = tuple[int, int, int]


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    color: Color
    gravity: float
    drag: float = 0.9


class ParticleSystem:
    """Owns and advances a pool of particles."""

    def __init__(self) -> None:
        self.particles: list[Particle] = []

    def __len__(self) -> int:
        return len(self.particles)

    def emit_burst(
        self,
        x: float,
        y: float,
        color: Color,
        count: int = 16,
        speed: float = 220.0,
        size: float = 6.0,
        gravity: float = 520.0,
        life: float = 0.55,
    ) -> None:
        """Spray particles outward in all directions (e.g. eating food)."""
        for _ in range(count):
            ang = random.uniform(0, 2 * math.pi)
            sp = speed * random.uniform(0.35, 1.0)
            self.particles.append(
                Particle(
                    x, y, math.cos(ang) * sp, math.sin(ang) * sp,
                    life, life, size * random.uniform(0.6, 1.2), color, gravity,
                )
            )

    def emit_confetti(
        self, x: float, y: float, colors: tuple[Color, ...], count: int = 40
    ) -> None:
        """Fling colourful confetti up and out (level clear / win)."""
        for _ in range(count):
            ang = random.uniform(-math.pi * 0.9, -math.pi * 0.1)  # upward arc
            sp = random.uniform(160, 380)
            self.particles.append(
                Particle(
                    x, y, math.cos(ang) * sp, math.sin(ang) * sp,
                    random.uniform(0.8, 1.5), 1.5,
                    random.uniform(5, 9), random.choice(colors), 640.0, 0.94,
                )
            )

    def update(self, dt: float) -> None:
        """Advance every particle and drop the dead ones."""
        for p in self.particles:
            p.vx *= p.drag
            p.vy = p.vy * p.drag + p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.life -= dt
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surface: pygame.Surface, offset: tuple[float, float] = (0.0, 0.0)) -> None:
        """Render particles, fading and shrinking as they age."""
        ox, oy = offset
        for p in self.particles:
            frac = max(0.0, min(1.0, p.life / p.max_life))
            r = max(1, int(p.size * frac))
            cx, cy = int(p.x + ox), int(p.y + oy)
            alpha = int(255 * frac)
            pygame.gfxdraw.filled_circle(surface, cx, cy, r, (*p.color, alpha))
