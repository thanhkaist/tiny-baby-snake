"""Render marketing media: still screenshots and an animated gameplay GIF.

Run headless with the offscreen SDL driver:
  SDL_VIDEODRIVER=offscreen SDL_AUDIODRIVER=dummy python tools/gen_media.py

Outputs into assets/ for the README.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random  # noqa: E402

import pygame  # noqa: E402
from PIL import Image  # noqa: E402

from config import WINDOW_HEIGHT, WINDOW_WIDTH, Direction, GameState  # noqa: E402
from engine.game import Game  # noqa: E402
from engine.modes import CLASSIC  # noqa: E402
from renderer import Renderer  # noqa: E402

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def _steer_toward_food(game: Game) -> None:
    hx, hy = game.snake.head
    if game.food.position is None:
        return
    fx, fy = game.food.position
    d = game.snake.direction
    if hy != fy and d not in (Direction.UP, Direction.DOWN):
        game.set_direction(Direction.DOWN if fy > hy else Direction.UP)
    elif hx != fx and d not in (Direction.LEFT, Direction.RIGHT):
        game.set_direction(Direction.RIGHT if fx > hx else Direction.LEFT)


def _frame(screen: pygame.Surface, scale: float = 0.62) -> Image.Image:
    raw = pygame.image.tostring(screen, "RGB")
    img = Image.frombytes("RGB", screen.get_size(), raw)
    return img.resize((int(img.width * scale), int(img.height * scale)))


def screenshot(screen, renderer, game, name, frames=24) -> None:
    for _ in range(frames):
        renderer.update(1 / 60)
        renderer.draw(game)
    pygame.image.save(screen, os.path.join(ASSETS, name))
    print("wrote", name)


def gameplay_gif(screen, renderer, game, name="gameplay.gif") -> None:
    game.start_mode(CLASSIC)
    images: list[Image.Image] = []
    step = 1.0 / game.speed
    acc = 0.0
    for i in range(360):
        acc += 1 / 60
        while acc >= step:
            _steer_toward_food(game)
            game.update()
            renderer.spawn_events(game)
            acc -= step
            step = 1.0 / game.speed
        renderer.update(1 / 60)
        renderer.draw(game)
        if i % 3 == 0:  # ~20 fps
            images.append(_frame(screen))
    images[0].save(
        os.path.join(ASSETS, name), save_all=True, append_images=images[1:],
        duration=50, loop=0, optimize=True,
    )
    print("wrote", name, f"({len(images)} frames)")


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    game = Game(rng=random.Random(7), high_score_path=os.path.join(ASSETS, "_media.json"))
    renderer = Renderer(screen)

    game.state = GameState.MENU
    screenshot(screen, renderer, game, "menu.png")
    game.state = GameState.MODE_SELECT
    screenshot(screen, renderer, game, "mode_select.png")
    game.start_mode(CLASSIC)
    for _ in range(6):
        _steer_toward_food(game)
        game.update()
    screenshot(screen, renderer, game, "gameplay.png")

    gameplay_gif(screen, renderer, game)
    if os.path.exists(os.path.join(ASSETS, "_media.json")):
        os.remove(os.path.join(ASSETS, "_media.json"))
    pygame.quit()


if __name__ == "__main__":
    main()
