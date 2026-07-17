# Changelog

## 2.0.0 — Pro Edition

A ground-up overhaul turning Tiny Baby Snake into a polished, professional game.

### Added
- **Smooth 60fps interpolated movement** — logic/render decoupling with a
  fixed-timestep loop; the snake glides between cells.
- **Playful cartoon art direction** — rounded gradient snake with googly eyes
  and a flicking tongue, grass checkerboard board, sticker text, five skins.
- **Juice** — particle bursts & confetti, screen shake, colour flashes,
  floating score pop-ups, squash-and-stretch, scene transitions.
- **Five game modes** — Adventure, Classic, Time Attack, Zen, Maze — with a
  card-based mode-select screen and mode-aware HUD.
- **Power-ups & bonus food** — Slow-Mo, Double, Ghost, Magnet, Shrink, and
  timed golden bonus fruit.
- **Persistent profile** — per-mode high scores, lifetime stats, achievements
  (with slide-in toasts), and unlockable skins; migrates the old high score.
- **Settings screen** — master/music/SFX volume and screen-shake toggle.
- **Stats & Skins screens** and an expanded main menu.
- **Richer procedural audio** — numpy synthesis (harmonics + ADSR), new SFX
  (bonus, power-up, achievement), and separate menu/gameplay music.
- **Packaging & CI** — PyInstaller one-file build, GitHub Actions test matrix
  (Python 3.11–3.13), `pyproject.toml`/requirements, media generators.

### Changed
- Restructured into a pygame-free `engine/` core plus `fx/` presentation.
- Test suite grown from 17 to 74 headless tests.

## 1.x
- Classic Snake with a start menu, five Adventure levels (walls, portals,
  teleporting food), procedural sound effects, and a persisted high score.
