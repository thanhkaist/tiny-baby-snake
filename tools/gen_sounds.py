"""Procedurally synthesize the game's sound effects and music (numpy).

Run with `python tools/gen_sounds.py`. Uses additive harmonics + ADSR
envelopes for a warmer, more polished chiptune feel than plain square waves.
Outputs 16-bit mono WAVs to assets/sounds/.
"""

import os
import wave

import numpy as np

RATE = 44100

# Note frequencies (equal temperament).
NOTES = {
    "C3": 130.81, "E3": 164.81, "G3": 196.00, "A3": 220.00,
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.00,
    "A4": 440.00, "B4": 493.88, "C5": 523.25, "D5": 587.33, "E5": 659.25,
    "F5": 698.46, "G5": 783.99, "A5": 880.00, "C6": 1046.50,
}


def adsr(n: int, a=0.01, d=0.06, s=0.6, r=0.12) -> np.ndarray:
    """An attack/decay/sustain/release envelope of length n samples."""
    a_n, d_n, r_n = int(a * RATE), int(d * RATE), int(r * RATE)
    s_n = max(0, n - a_n - d_n - r_n)
    env = np.concatenate([
        np.linspace(0, 1, a_n, False) if a_n else np.array([]),
        np.linspace(1, s, d_n, False) if d_n else np.array([]),
        np.full(s_n, s),
        np.linspace(s, 0, r_n, False) if r_n else np.array([]),
    ])
    if len(env) < n:
        env = np.concatenate([env, np.zeros(n - len(env))])
    return env[:n]


def tone(freq, dur, harmonics=(1.0, 0.45, 0.22, 0.1), vol=0.5,
         vib_rate=0.0, vib_depth=0.0, env=None) -> np.ndarray:
    """A tone built from harmonics, enveloped."""
    t = np.linspace(0, dur, int(dur * RATE), False)
    wave = np.zeros_like(t)
    vib = vib_depth * np.sin(2 * np.pi * vib_rate * t) if vib_rate else 0.0
    for i, amp in enumerate(harmonics, 1):
        wave += amp * np.sin(2 * np.pi * freq * i * t + vib)
    wave /= sum(harmonics)
    e = env if env is not None else adsr(len(t))
    return wave * e * vol


def sweep(f0, f1, dur, vol=0.5, vib_rate=0.0, vib_depth=0.0) -> np.ndarray:
    """A tone gliding f0 -> f1."""
    n = int(dur * RATE)
    t = np.linspace(0, dur, n, False)
    freqs = np.linspace(f0, f1, n)
    phase = np.cumsum(2 * np.pi * freqs / RATE)
    vib = vib_depth * np.sin(2 * np.pi * vib_rate * t) if vib_rate else 0.0
    return np.sin(phase + vib) * adsr(n, a=0.01, d=0.05, s=0.7, r=0.06) * vol


def seq(*parts) -> np.ndarray:
    return np.concatenate(parts) if parts else np.array([])


def chord(freqs, dur, vol=0.4, **kw) -> np.ndarray:
    out = sum(tone(f, dur, vol=vol, **kw) for f in freqs)
    return out / max(1, len(freqs)) * 1.4


def mix(*parts) -> np.ndarray:
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[: len(p)] += p
    return out


def n(name):
    return NOTES[name]


def write_wav(path, samples) -> None:
    peak = np.max(np.abs(samples)) or 1.0
    if peak > 1.0:
        samples = samples / peak
    data = np.clip(samples, -1, 1)
    pcm = (data * 32767).astype("<i2")
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())


def build() -> dict[str, np.ndarray]:
    pluck = dict(harmonics=(1.0, 0.5, 0.25), env=None)
    return {
        "menu_move": tone(n("A4"), 0.05, harmonics=(1, 0.3), vol=0.25),
        "select": seq(tone(n("G4"), 0.06, vol=0.3, **pluck),
                      tone(n("C5"), 0.1, vol=0.32, **pluck)),
        "eat": tone(n("C5"), 0.09, harmonics=(1, 0.6, 0.3), vol=0.4,
                    env=adsr(int(0.09 * RATE), a=0.002, d=0.04, s=0.2, r=0.04)),
        "bonus": seq(tone(n("C5"), 0.07, vol=0.4), tone(n("E5"), 0.07, vol=0.4),
                     tone(n("G5"), 0.07, vol=0.4), tone(n("C6"), 0.16, vol=0.45)),
        "powerup": mix(sweep(400, 1200, 0.28, vol=0.35, vib_rate=18, vib_depth=6),
                       chord([n("C5"), n("E5"), n("G5")], 0.28, vol=0.2)),
        "teleport": sweep(300, 1300, 0.22, vol=0.4, vib_rate=30, vib_depth=40),
        "level_cleared": seq(tone(n("C5"), 0.09, vol=0.4), tone(n("E5"), 0.09, vol=0.4),
                             tone(n("G5"), 0.09, vol=0.4), tone(n("C6"), 0.2, vol=0.46)),
        "game_over": seq(tone(n("G4"), 0.15, harmonics=(1, 0.4, 0.2), vol=0.35),
                         tone(n("E4"), 0.15, harmonics=(1, 0.4, 0.2), vol=0.35),
                         tone(n("C4"), 0.34, harmonics=(1, 0.4, 0.2), vol=0.35)),
        "win": seq(tone(n("C5"), 0.1, vol=0.4), tone(n("E5"), 0.1, vol=0.4),
                   tone(n("G5"), 0.1, vol=0.4), tone(n("C6"), 0.12, vol=0.45),
                   tone(n("G5"), 0.1, vol=0.4), tone(n("C6"), 0.3, vol=0.5)),
        "achievement": seq(chord([n("C5"), n("E5")], 0.1, vol=0.35),
                           chord([n("G5"), n("C6")], 0.26, vol=0.4)),
        "menu_music": _music(
            [("C3", ["C4", "E4", "G4"]), ("G3", ["B4", "D5", "G4"]),
             ("A3", ["A4", "C5", "E4"]), ("F4", ["F4", "A4", "C5"])], beat=0.34),
        "game_music": _music(
            [("C3", ["C4", "E4", "G4"]), ("A3", ["A4", "C5", "E4"]),
             ("F4", ["F4", "A4", "C5"]), ("G3", ["G4", "B4", "D5"])], beat=0.22),
    }


def _music(progression, beat) -> np.ndarray:
    """A gentle looping bed: a bass note + a shimmering arpeggio per chord."""
    out = []
    for bass, arp in progression:
        bass_wave = tone(n(bass), beat * len(arp), harmonics=(1, 0.3), vol=0.16,
                         env=adsr(int(beat * len(arp) * RATE), a=0.02, d=0.1, s=0.7, r=0.2))
        arp_wave = seq(*[tone(n(note), beat, harmonics=(1, 0.4, 0.15), vol=0.11)
                         for note in arp])
        out.append(mix(bass_wave, arp_wave))
    return seq(*out)


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(os.path.dirname(here), "assets", "sounds")
    os.makedirs(out_dir, exist_ok=True)
    for stem, samples in build().items():
        path = os.path.join(out_dir, f"{stem}.wav")
        write_wav(path, samples)
        print(f"wrote {path} ({len(samples) / RATE:.2f}s)")


if __name__ == "__main__":
    main()
