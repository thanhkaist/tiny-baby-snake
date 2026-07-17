# Project: Snake Game

## Stack
- Python 3, pygame

## Conventions
- Follow PEP 8. Use type hints on all functions.
- Separate concerns: game logic, rendering, and input handling in distinct modules/classes.
- No magic numbers — use named constants (grid size, colors, FPS) in a config section.
- Add docstrings to classes and public methods.
- Keep the main loop thin; delegate to methods.

## Structure
- main.py        # entry point + game loop
- game.py        # Game state, update logic
- snake.py       # Snake entity
- food.py        # Food entity
- config.py      # constants

## Testing
- Write logic in a way that core mechanics (movement, collision, growth) can be unit-tested without a display.
