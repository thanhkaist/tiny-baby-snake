"""Resource path resolution that works both from source and when frozen.

PyInstaller unpacks bundled data to a temp dir exposed as ``sys._MEIPASS``;
reading assets through ``resource_path`` keeps the game working either way.
"""

import os
import sys


def resource_path(relative: str) -> str:
    """Absolute path to a bundled resource (assets), source or frozen."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)
