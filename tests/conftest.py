"""Test bootstrap: make the project importable and force headless SDL.

Setting the dummy drivers here means a bare ``pytest`` runs without a display
or audio device (e.g. in CI), no env vars required.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
