"""Build Plate: sound effects as ES5503 wave RAM samples.

8-bit unsigned, 1..255 (a 0 byte halts the oscillator, so it only ends a sample),
20,000 Hz. Each effect is synthesised from numbers, with a shop-floor flavour:
servos, presses, print heads.
"""
import math
import sys
import wave
from pathlib import Path

import numpy as np

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "audio")
SR = 20000
rng = np.random.default_rng(7)


def t(sec):
    return np.arange(int(sec * SR)) / SR


def env(n, a=0.002, d=None, curve=4.0):
    """Attack then exponential decay over n samples."""
    x = np.arange(n) / SR
    att = np.clip(x / max(a, 1e-6), 0, 1)
    dec = np.exp(-curve * x / (x[-1] + 1e-9)) if d is None else np.exp(-x / d)
    return att * dec


def sq(phase, duty=0.5):
    return np.where((phase % 1.0) < duty, 1.0, -1.0)


def tone(freqs, wave_="sq", duty=0.5):
    """freqs: per-sample frequency array."""
    ph = np.cumsum(freqs) / SR
    if wave_ == "sq":
        return sq(ph, duty)
    if wave_ == "tri":
        return 2 * np.abs(2 * (ph % 1) - 1) - 1
    if wave_ == "saw":
        return 2 * (ph % 1) - 1
    return np.sin(2 * np.pi * ph)


def noise(n, hold=1):
    x = rng.uniform(-1, 1, (n + hold - 1) // hold)
    return np.repeat(x, hold)[:n]


def lowpass(x, fc):
    a = math.exp(-2 * math.pi * fc / SR)
    y = np.zeros_like(x)
    p = 0.0
    for i, v in enumerate(x):
        p = (1 - a) * v + a * p
        y[i] = p
    return y


def glide(f0, f1, n, exp=True):
    if exp:
        return f0 * (f1 / f0) ** (np.arange(n) / max(1, n - 1))
    return np.linspace(f0, f1, n)


def note(m):
    return 440 * 2 ** ((m - 69) / 12)


def cat(*parts, gap=0.0):
    out = []
    for p in parts:
        out.append(p)
        if gap:
            out.append(np.zeros(int(gap * SR)))
    return np.concatenate(out)


def mix_at(base, part, at):
    i = int(at * SR)
    end = i + len(part)
    if end > len(base):
        base = np.concatenate([base, np.zeros(end - len(base))])
    base[i:end] += part
    return base


# ---------------------------------------------------------------- effects
def fx_move():
    n = int(0.035 * SR)
    click = noise(n, 2) * env(n, 0.0005, 0.004)
    blip = tone(np.full(n, 1800.0), "sq", 0.25) * env(n, 0.0005, 0.006) * 0.5
    return click * 0.6 + blip


def fx_rotate():
    n = int(0.075 * SR)
    f = glide(520, 1250, n)
    return tone(f, "sq", 0.3) * env(n, 0.001, 0.03) * 0.8 + noise(n, 3) * env(n, 0.0005, 0.008) * 0.25


def fx_hold():
    a = tone(np.full(int(0.045 * SR), note(76)), "sq", 0.5) * env(int(0.045 * SR), 0.001, 0.02)
    b = tone(np.full(int(0.06 * SR), note(71)), "sq", 0.5) * env(int(0.06 * SR), 0.001, 0.025)
    return cat(a, b) * 0.7


def fx_hard_drop():
    n1 = int(0.11 * SR)
    whoosh = lowpass(noise(n1), 3000) * np.linspace(0.2, 1, n1) * 1.6
    whoosh *= np.linspace(1, 0.4, n1)
    n2 = int(0.22 * SR)
    thud = tone(glide(140, 38, n2), "sin") * env(n2, 0.0005, 0.07)
    clank = noise(int(0.03 * SR), 1) * env(int(0.03 * SR), 0.0002, 0.006) * 0.6
    out = mix_at(whoosh, thud, 0.10)
    out = mix_at(out, clank, 0.10)
    return out


def fx_lock():
    """A press clamping down: inharmonic partials, short."""
    n = int(0.16 * SR)
    x = np.zeros(n)
    for f, a, d in ((523, 1.0, 0.05), (1371, 0.6, 0.03), (2210, 0.4, 0.02), (3190, 0.25, 0.012)):
        x += a * tone(np.full(n, f), "sin") * env(n, 0.0003, d)
    x += noise(n, 1) * env(n, 0.0002, 0.004) * 0.7
    return x * 0.6


def arp(notes, step=0.055, duty=0.5, tail=0.12):
    out = np.zeros(0)
    for i, m in enumerate(notes):
        last = i == len(notes) - 1
        n = int((step + (tail if last else 0)) * SR)
        p = tone(np.full(n, note(m)), "sq", duty) * env(n, 0.001, 0.06 if not last else 0.12)
        p += 0.5 * tone(np.full(n, note(m + 12)), "sq", 0.25) * env(n, 0.001, 0.03)
        out = mix_at(out, p, i * step)
    return out


def fx_clear(lines):
    base = [69, 72, 76, 81, 84]  # A minor, up
    notes = base[: 2 + lines]
    x = arp(notes) * 0.7
    n = int(0.25 * SR)
    sparkle = noise(n, 1) * env(n, 0.001, 0.05) * 0.25
    sparkle = sparkle - lowpass(sparkle, 4000)  # keep the fizz on top
    return mix_at(x, sparkle, 0.02)


def fx_quad():
    n = int(0.25 * SR)
    sweep = tone(glide(180, 1600, n), "saw") * np.linspace(0.3, 1, n) * 0.6
    stab = np.zeros(int(0.45 * SR))
    for m in (69, 72, 76, 81):  # Am stab, wide
        stab += tone(np.full(len(stab), note(m)), "sq", 0.4) * env(len(stab), 0.001, 0.16) * 0.35
    zap_n = int(0.3 * SR)
    zap = tone(glide(3200, 220, zap_n), "sq", 0.5) * env(zap_n, 0.001, 0.12) * 0.45
    out = mix_at(sweep, stab, 0.24)
    out = mix_at(out, zap, 0.26)
    return out


def fx_tspin():
    n = int(0.42 * SR)
    lfo = np.sin(2 * np.pi * 18 * t(n / SR))
    f = glide(300, 900, n) * (1 + 0.25 * lfo)
    x = tone(f, "sq", 0.3) * env(n, 0.002, 0.2) * 0.7
    x += tone(f * 1.5, "tri") * env(n, 0.002, 0.15) * 0.4
    return x


def fx_level_up():
    """New job: a fanfare over a print head ratcheting across."""
    notes = [69, 73, 76, 81, 85, 88]  # A major, up: the line levels up
    x = arp(notes, step=0.075, duty=0.4, tail=0.35) * 0.6
    n = int(0.6 * SR)
    rat = np.zeros(n)
    for k in range(0, n, int(0.025 * SR)):
        m = min(n - k, int(0.006 * SR))
        rat[k:k + m] += noise(m, 1) * np.linspace(1, 0, m)
    rat = rat * 0.25
    return mix_at(x, rat, 0.0)


def fx_game_over():
    """Line stop: the machine powers down, stutters and thunks."""
    n = int(1.0 * SR)
    f = glide(420, 32, n)
    stut = (np.floor(t(n / SR) * 14) % 2 == 0).astype(float) * 0.5 + 0.5
    x = tone(f, "sq", 0.5) * np.linspace(1, 0.35, n) * stut * 0.6
    x += tone(f / 2, "tri") * np.linspace(0.8, 0.2, n) * 0.4
    m = int(0.35 * SR)
    thunk = tone(glide(90, 30, m), "sin") * env(m, 0.0005, 0.1)
    thunk += noise(m, 2) * env(m, 0.0003, 0.01) * 0.5
    return mix_at(x, thunk, 0.98)


def fx_count():
    n = int(0.12 * SR)
    return tone(np.full(n, note(69)), "sq", 0.5) * env(n, 0.001, 0.06)


def fx_go():
    n = int(0.35 * SR)
    return tone(np.full(n, note(81)), "sq", 0.5) * env(n, 0.001, 0.17) + 0.4 * tone(np.full(n, note(93)), "sq", 0.25) * env(n, 0.001, 0.08)


def fx_menu():
    n = int(0.03 * SR)
    return tone(np.full(n, 1320.0), "sq", 0.5) * env(n, 0.0005, 0.01) * 0.6


def fx_select():
    a = tone(np.full(int(0.05 * SR), note(81)), "sq", 0.5) * env(int(0.05 * SR), 0.001, 0.03)
    b = tone(np.full(int(0.09 * SR), note(88)), "sq", 0.5) * env(int(0.09 * SR), 0.001, 0.05)
    return cat(a, b) * 0.6


EFFECTS = [
    ("move", fx_move), ("rotate", fx_rotate), ("hold", fx_hold), ("hard-drop", fx_hard_drop),
    ("lock", fx_lock), ("single", lambda: fx_clear(1)), ("double", lambda: fx_clear(2)),
    ("triple", lambda: fx_clear(3)), ("quad", fx_quad), ("t-spin", fx_tspin),
    ("new-job", fx_level_up), ("line-stop", fx_game_over), ("count", fx_count), ("go", fx_go),
    ("menu-move", fx_menu), ("menu-select", fx_select),
]


def to_doc(x):
    """Normalise to 8-bit unsigned 1..255, centre 128, and end with the 0 that halts the oscillator."""
    x = x / (np.abs(x).max() + 1e-9) * 0.95
    u = np.clip(np.round(x * 127 + 128), 1, 255).astype(np.uint8)
    return np.concatenate([u, [0]]).astype(np.uint8)


def save_wav8(path, u):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(SR)
        w.writeframes(u.tobytes())


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    reel = np.zeros(0)
    t0 = 0.4
    marks = []
    blob = bytearray()
    table = []
    for name, f in EFFECTS:
        u = to_doc(f())
        save_wav8(OUT / f"sfx-{name}.wav", u[:-1])
        table.append((name, len(blob), len(u)))
        blob += u.tobytes()
        x = (u[:-1].astype(np.float32) - 128) / 128
        marks.append((name, t0))
        reel = mix_at(reel, x * 0.8, t0)
        t0 += len(x) / SR + 0.7
    (OUT / "BLOCKS-WAV.bin").write_bytes(bytes(blob))
    reel = np.concatenate([reel, np.zeros(int(0.4 * SR))])
    save_wav8(OUT / "sfx-reel.wav", np.clip(np.round(reel * 127 + 128), 1, 255).astype(np.uint8))
    total = len(blob)
    print(f"wave RAM: {total} bytes of 131072 ({total / 1310.72:.0f}%)")
    for (name, off, ln), (_, at) in zip(table, marks):
        print(f"{at:6.2f}s  {name:12s} offset ${off:05X}  {ln:6d} bytes  {ln / SR * 1000:5.0f} ms")
