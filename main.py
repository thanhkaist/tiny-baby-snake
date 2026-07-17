"""Entry point: wires input, game core, and rendering into a thin loop."""

import pygame

from audio import SoundManager
from config import (
    MAX_STEPS_PER_FRAME,
    RENDER_FPS,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    WINDOW_WIDTH,
    Direction,
    GameState,
    Intent,
    SoundEvent,
)
from engine.game import Game
from input_handler import InputHandler
from renderer import Renderer


def _apply_intent(intent: tuple, game: Game, audio: SoundManager) -> bool:
    """Act on one decoded intent; return False to request quitting.

    The same intent means different things per state — arrows steer during
    play but navigate the menu, and Esc backs out of the info screen rather
    than quitting. UI sounds are played here; gameplay sounds come from
    `game.events` after each update.
    """
    action, payload = intent

    if action is Intent.QUIT:
        if game.state in (GameState.INFO, GameState.MODE_SELECT):
            game.back_to_menu()
            return True
        return False

    if action is Intent.MOVE:
        if game.state is GameState.MENU:
            if payload is Direction.UP:
                game.menu_move(-1)
                audio.play(SoundEvent.MENU_MOVE)
            elif payload is Direction.DOWN:
                game.menu_move(1)
                audio.play(SoundEvent.MENU_MOVE)
        elif game.state is GameState.MODE_SELECT:
            if payload is Direction.UP:
                game.mode_menu_move(-1)
                audio.play(SoundEvent.MENU_MOVE)
            elif payload is Direction.DOWN:
                game.mode_menu_move(1)
                audio.play(SoundEvent.MENU_MOVE)
        else:
            game.set_direction(payload)

    elif action is Intent.CONFIRM:
        if game.state is GameState.MENU:
            game.menu_select()
            audio.play(SoundEvent.SELECT)
        elif game.state is GameState.MODE_SELECT:
            game.mode_menu_select()
            audio.play(SoundEvent.SELECT)
        elif game.state is GameState.INFO:
            game.back_to_menu()
            audio.play(SoundEvent.SELECT)
        elif game.state is GameState.LEVEL_CLEARED:
            game.advance_level()
            audio.play(SoundEvent.SELECT)
        elif game.state in (GameState.GAME_OVER, GameState.WON):
            game.reset()
            audio.play(SoundEvent.SELECT)

    elif action is Intent.TOGGLE_PAUSE:
        if game.state in (GameState.RUNNING, GameState.PAUSED):
            game.toggle_pause()

    elif action is Intent.TOGGLE_MUTE:
        audio.toggle_mute()

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
    audio = SoundManager()
    audio.start_music()

    accumulator = 0.0

    running = True
    while running:
        dt = clock.tick(RENDER_FPS) / 1000.0
        for intent in handler.process(pygame.event.get()):
            if not _apply_intent(intent, game, audio):
                running = False

        # Advance logic in fixed steps, decoupled from the render rate. The
        # step shrinks as the mode's speed rises (e.g. Classic speeding up).
        step = 1.0 / game.speed
        accumulator += dt
        steps = 0
        while accumulator >= step and steps < MAX_STEPS_PER_FRAME:
            game.update()
            audio.play_events(game.events)
            renderer.spawn_events(game)  # particles/shake/pop-ups for this tick
            accumulator -= step
            steps += 1
        accumulator = min(accumulator, step)  # drop any backlog past the clamp

        renderer.update(dt)  # advance effect systems once per frame

        # Fraction toward the next tick, used to interpolate the snake.
        alpha = accumulator / step if game.state is GameState.RUNNING else 1.0
        renderer.draw(game, alpha)

    pygame.quit()


if __name__ == "__main__":
    main()
