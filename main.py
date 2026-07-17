"""Entry point: wires input, game core, and rendering into a thin loop."""

import pygame

from config import (
    FPS,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    WINDOW_WIDTH,
    Direction,
    GameState,
    Intent,
)
from game import Game
from input_handler import InputHandler
from renderer import Renderer


def _apply_intent(intent: tuple, game: Game) -> bool:
    """Act on one decoded intent; return False to request quitting.

    The same intent means different things per state — arrows steer during
    play but navigate the menu, and Esc backs out of the info screen rather
    than quitting.
    """
    action, payload = intent

    if action is Intent.QUIT:
        if game.state is GameState.INFO:
            game.back_to_menu()
            return True
        return False

    if action is Intent.MOVE:
        if game.state is GameState.MENU:
            if payload is Direction.UP:
                game.menu_move(-1)
            elif payload is Direction.DOWN:
                game.menu_move(1)
        else:
            game.set_direction(payload)

    elif action is Intent.CONFIRM:
        if game.state is GameState.MENU:
            game.menu_select()
        elif game.state is GameState.INFO:
            game.back_to_menu()
        elif game.state is GameState.LEVEL_CLEARED:
            game.advance_level()
        elif game.state in (GameState.GAME_OVER, GameState.WON):
            game.reset()

    elif action is Intent.TOGGLE_PAUSE:
        if game.state in (GameState.RUNNING, GameState.PAUSED):
            game.toggle_pause()

    elif action is Intent.RESTART:
        if game.state is not GameState.INFO:
            game.reset()

    return True


def main() -> None:
    """Initialize pygame and run the game loop until the player quits."""
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    game = Game()
    renderer = Renderer(screen)
    handler = InputHandler()

    running = True
    while running:
        for intent in handler.process(pygame.event.get()):
            if not _apply_intent(intent, game):
                running = False
        game.update()
        renderer.draw(game)
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
