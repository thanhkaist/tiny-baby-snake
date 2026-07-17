# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec — bundles audio assets into a one-file executable.

Build with:  pyinstaller tiny-baby-snake.spec --noconfirm
Output:      dist/tiny-baby-snake
"""

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[("assets/sounds", "assets/sounds")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=["numpy", "PIL", "pytest"],  # dev-only, keep the binary lean
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="tiny-baby-snake",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    onefile=True,
)
