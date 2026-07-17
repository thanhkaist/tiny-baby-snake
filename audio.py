"""Sound playback for the game.

This is a boundary module (it owns pygame.mixer), kept out of the game core so
the core stays headless-testable. It degrades gracefully: if no audio device is
available, every method becomes a harmless no-op.
"""

import os

import pygame

from config import MUSIC_VOLUME, SFX_VOLUME, SOUND_DIR, SoundEvent


class SoundManager:
    """Loads and plays sound effects and background music."""

    def __init__(self, sound_dir: str = SOUND_DIR, enabled: bool = True) -> None:
        """Initialize the mixer and load sounds, tolerating audio failures."""
        self.available = False
        self.muted = False
        self._sounds: dict[SoundEvent, pygame.mixer.Sound] = {}
        self._music_path: str | None = None

        if not enabled:
            return
        try:
            pygame.mixer.init()
        except pygame.error:
            return  # no audio device — stay a no-op
        self.available = True

        for event in SoundEvent:
            path = os.path.join(sound_dir, f"{event.value}.wav")
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(SFX_VOLUME)
                self._sounds[event] = sound
            except (pygame.error, FileNotFoundError):
                pass

        music = os.path.join(sound_dir, "music.wav")
        if os.path.exists(music):
            self._music_path = music

    def apply_settings(self, settings) -> None:
        """Set music and SFX volumes from the profile's settings."""
        if not self.available:
            return
        master = settings.master_volume
        for sound in self._sounds.values():
            sound.set_volume(master * settings.sfx_volume)
        try:
            pygame.mixer.music.set_volume(master * settings.music_volume)
        except pygame.error:
            pass

    def play(self, event: SoundEvent) -> None:
        """Play one sound effect, unless muted or unavailable."""
        if not self.available or self.muted:
            return
        sound = self._sounds.get(event)
        if sound is not None:
            sound.play()

    def play_events(self, events: list[SoundEvent]) -> None:
        """Play a batch of sound events emitted by the game this tick."""
        for event in events:
            self.play(event)

    def start_music(self) -> None:
        """Begin looping the background music, if any is loaded."""
        if not self.available or self._music_path is None:
            return
        try:
            pygame.mixer.music.load(self._music_path)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1)
            if self.muted:
                pygame.mixer.music.pause()
        except pygame.error:
            pass

    def toggle_mute(self) -> bool:
        """Flip muting; pause/resume the music to match. Returns the new state."""
        self.muted = not self.muted
        if self.available:
            if self.muted:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()
        return self.muted
