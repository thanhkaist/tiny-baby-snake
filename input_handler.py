"""Translation of raw pygame events into game intents."""

import pygame

from config import Direction, Intent

_KEY_TO_DIRECTION = {
    pygame.K_UP: Direction.UP,
    pygame.K_w: Direction.UP,
    pygame.K_DOWN: Direction.DOWN,
    pygame.K_s: Direction.DOWN,
    pygame.K_LEFT: Direction.LEFT,
    pygame.K_a: Direction.LEFT,
    pygame.K_RIGHT: Direction.RIGHT,
    pygame.K_d: Direction.RIGHT,
}


class InputHandler:
    """Decodes pygame events, keeping key constants out of the game core."""

    def process(self, events: list[pygame.event.Event]) -> list[tuple]:
        """Map a batch of events to (Intent, payload) pairs.

        The payload is a Direction for MOVE intents and None otherwise.
        """
        intents: list[tuple] = []
        for event in events:
            if event.type == pygame.QUIT:
                intents.append((Intent.QUIT, None))
            elif event.type == pygame.KEYDOWN:
                intents.append(self._decode_key(event.key))
        return [intent for intent in intents if intent is not None]

    def _decode_key(self, key: int) -> tuple | None:
        """Map a single key code to an intent, or None if unbound."""
        if key in _KEY_TO_DIRECTION:
            return (Intent.MOVE, _KEY_TO_DIRECTION[key])
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return (Intent.CONFIRM, None)
        if key in (pygame.K_p, pygame.K_SPACE):
            return (Intent.TOGGLE_PAUSE, None)
        if key == pygame.K_m:
            return (Intent.TOGGLE_MUTE, None)
        if key == pygame.K_r:
            return (Intent.RESTART, None)
        if key == pygame.K_ESCAPE:
            return (Intent.QUIT, None)
        return None
