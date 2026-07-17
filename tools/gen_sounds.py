"""Procedurally generate the game's sound effects and music as WAV files.

Run with `python tools/gen_sounds.py`. Uses only the standard library so the
audio assets can be regenerated anywhere without extra dependencies. Output
goes to `assets/sounds/`.
"""

import array
import math
import os
import wave

RATE = 44100
Sample = float


def _sine(freq: float, t: float) -> float:
    return math.sin(2.0 * math.pi * freq * t)


def _square(freq: float, t: float) -> float:
    return 1.0 if _sine(freq, t) >= 0.0 else -1.0


def tone(
    freq: float,
    dur: float,
    *,
    shape: str = "sine",
    vol: float = 0.5,
    attack: float = 0.005,
    release: float = 0.03,
) -> list[Sample]:
    """One enveloped tone. `shape` is 'sine' or 'square'."""
    n = int(dur * RATE)
    out: list[Sample] = []
    for i in range(n):
        t = i / RATE
        wave_fn = _square if shape == "square" else _sine
        env = min(1.0, i / (attack * RATE + 1e-9)) * min(
            1.0, (n - i) / (release * RATE + 1e-9)
        )
        out.append(wave_fn(freq, t) * env * vol)
    return out


def sweep(
    f0: float, f1: float, dur: float, *, shape: str = "sine", vol: float = 0.5
) -> list[Sample]:
    """A tone gliding from f0 to f1 over `dur` seconds."""
    n = int(dur * RATE)
    out: list[Sample] = []
    phase = 0.0
    for i in range(n):
        frac = i / n
        freq = f0 + (f1 - f0) * frac
        phase += 2.0 * math.pi * freq / RATE
        s = 1.0 if math.sin(phase) >= 0.0 else -1.0 if shape == "square" else math.sin(phase)
        env = min(1.0, i / (0.005 * RATE)) * min(1.0, (n - i) / (0.03 * RATE))
        out.append(s * env * vol)
    return out


def sequence(*parts: list[Sample]) -> list[Sample]:
    """Concatenate sound fragments end to end."""
    out: list[Sample] = []
    for part in parts:
        out.extend(part)
    return out


def mix(a: list[Sample], b: list[Sample]) -> list[Sample]:
    """Overlay two fragments, summing sample-by-sample."""
    n = max(len(a), len(b))
    out: list[Sample] = []
    for i in range(n):
        va = a[i] if i < len(a) else 0.0
        vb = b[i] if i < len(b) else 0.0
        out.append(va + vb)
    return out


def write_wav(path: str, samples: list[Sample]) -> None:
    """Write mono 16-bit PCM, clamping to avoid clipping artifacts."""
    clamped = (max(-1.0, min(1.0, s)) for s in samples)
    buf = array.array("h", (int(s * 32767) for s in clamped))
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(buf.tobytes())


# Note frequencies (equal temperament).
C4, D4, E4, F4, G4, A4, B4 = 261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88
C5, E5, G5, C6 = 523.25, 659.25, 783.99, 1046.50


def build() -> dict[str, list[Sample]]:
    """Return every sound keyed by its file stem."""
    return {
        "menu_move": tone(A4, 0.04, shape="square", vol=0.25),
        "select": sequence(
            tone(G4, 0.05, shape="square", vol=0.3),
            tone(C5, 0.08, shape="square", vol=0.3),
        ),
        "eat": sequence(
            tone(C5, 0.045, shape="square", vol=0.35),
            tone(G5, 0.05, shape="square", vol=0.35),
        ),
        "teleport": sweep(300.0, 1300.0, 0.22, shape="sine", vol=0.4),
        "level_cleared": sequence(
            tone(C5, 0.09, vol=0.4),
            tone(E5, 0.09, vol=0.4),
            tone(G5, 0.09, vol=0.4),
            tone(C6, 0.18, vol=0.45),
        ),
        "game_over": sequence(
            tone(G4, 0.14, shape="square", vol=0.35),
            tone(E4, 0.14, shape="square", vol=0.35),
            tone(C4, 0.30, shape="square", vol=0.35),
        ),
        "win": sequence(
            tone(C5, 0.10, vol=0.4),
            tone(E5, 0.10, vol=0.4),
            tone(G5, 0.10, vol=0.4),
            tone(C6, 0.12, vol=0.45),
            tone(G5, 0.10, vol=0.4),
            tone(C6, 0.28, vol=0.5),
        ),
        "music": _music_loop(),
    }


def _music_loop() -> list[Sample]:
    """A gentle repeating arpeggio bed, low in the mix."""
    pattern = [C4, E4, G4, E4, F4, A4, C5, A4, G4, B4, D4, B4, C4, G4, E4, G4]
    beat = 0.16
    out: list[Sample] = []
    for note in pattern:
        bass = tone(note / 2.0, beat, shape="sine", vol=0.14, release=0.05)
        lead = tone(note, beat, shape="sine", vol=0.10, release=0.05)
        out.extend(mix(bass, lead))
    return out


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
