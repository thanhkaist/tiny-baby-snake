# Tiny Baby Snake

A classic Snake game built with Python and pygame. Steer a growing snake around
a wrapping grid, eat food to score, and try not to run into your own tail.

## Features

- Start menu with a "How to Play" screen
- Wrap-around edges — leave one side, reappear on the opposite side
- Score tracking with a high score persisted between sessions
- Pause / resume and restart
- Arrow-key or WASD controls
- Core game logic decoupled from pygame, so it runs and unit-tests headlessly

## Setup

Requires Python 3 and pygame.

```bash
python3 -m venv venv
venv/bin/pip install pygame
```

## Play

```bash
venv/bin/python main.py
```

**Controls**

| Key | Action |
|---|---|
| Arrow keys / WASD | Steer (or navigate the menu) |
| Enter | Select menu option / restart after game over |
| P or Space | Pause / resume |
| R | Restart |
| Esc | Quit (or back out of the info screen) |

## Tests

```bash
venv/bin/pip install pytest
venv/bin/python -m pytest tests/ -v
```

The core modules (`game`, `snake`, `food`, `storage`) import no pygame, so the
suite runs without a display.

## Layout

| File | Responsibility |
|---|---|
| `main.py` | Entry point + game loop |
| `game.py` | Game state and update logic |
| `snake.py` | Snake entity |
| `food.py` | Food entity |
| `storage.py` | High-score persistence |
| `renderer.py` | Drawing to the pygame surface |
| `input_handler.py` | Keyboard events → game intents |
| `config.py` | Constants and shared enums |
| `tests/` | Unit tests |
