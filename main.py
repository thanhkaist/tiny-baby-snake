"""Entry point: wires input, game core, and rendering into a thin loop."""

import pygame

from audio import SoundManager
from config import (
    MAX_STEPS_PER_FRAME,
    PROFILE_FILE,
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

    # Esc backs out of these screens to the main menu; from the menu itself
    # (or during play) it quits the game.
    back_states = (
        GameState.INFO, GameState.MODE_SELECT, GameState.SETTINGS,
        GameState.SKINS, GameState.STATS, GameState.GAME_OVER, GameState.WON,
    )

    if action is Intent.QUIT:
        if game.state in back_states:
            game.back_to_menu()
            return True
        return False

    if action is Intent.MOVE:
        if game.state is GameState.MENU:
            game.menu_move(-1 if payload is Direction.UP else 1
                           if payload is Direction.DOWN else 0)
            if payload in (Direction.UP, Direction.DOWN):
                audio.play(SoundEvent.MENU_MOVE)
        elif game.state is GameState.MODE_SELECT:
            if payload in (Direction.UP, Direction.DOWN):
                game.mode_menu_move(-1 if payload is Direction.UP else 1)
                audio.play(SoundEvent.MENU_MOVE)
        elif game.state is GameState.SETTINGS:
            if payload in (Direction.UP, Direction.DOWN):
                game.settings_move(-1 if payload is Direction.UP else 1)
                audio.play(SoundEvent.MENU_MOVE)
            elif payload in (Direction.LEFT, Direction.RIGHT):
                game.settings_adjust(-1 if payload is Direction.LEFT else 1)
                audio.play(SoundEvent.MENU_MOVE)
        elif game.state is GameState.SKINS:
            step = {Direction.LEFT: -1, Direction.RIGHT: 1,
                    Direction.UP: -3, Direction.DOWN: 3}.get(payload, 0)
            if step:
                game.skins_move(step)
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
        elif game.state is GameState.SKINS:
            if game.skins_select():
                audio.play(SoundEvent.SELECT)
        elif game.state in (GameState.INFO, GameState.SETTINGS, GameState.STATS):
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

    game = Game(high_score_path=PROFILE_FILE)
    renderer = Renderer(screen)
    handler = InputHandler()
    audio = SoundManager()
    audio.start_music()
    renderer.apply_profile(game.profile)
    audio.apply_settings(game.profile.settings)

    accumulator = 0.0

    running = True
    while running:
        dt = clock.tick(RENDER_FPS) / 1000.0
        for intent in handler.process(pygame.event.get()):
            if not _apply_intent(intent, game, audio):
                running = False

        # Reflect any profile changes (skin, volumes, shake) immediately.
        renderer.apply_profile(game.profile)
        audio.apply_settings(game.profile.settings)

        # Livelier music during play; calmer track in the menus.
        gameplay = game.state in (
            GameState.RUNNING, GameState.PAUSED, GameState.LEVEL_CLEARED)
        audio.play_music("game_music" if gameplay else "menu_music")

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
