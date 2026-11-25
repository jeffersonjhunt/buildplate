"""One Off Stax: title/background music, an original tune for the OO-1's two SIDs.

A small tracker writes SID registers once a frame (60 Hz, NTSC, as a .sid's play
routine would), and two reSIDfp 8580s render them, SID A left and SID B right.
"""
import math
import sys
import wave
from pathlib import Path

import numpy as np
from pyresidfp import SoundInterfaceDevice
from pyresidfp._pyresidfp import ChipModel

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "audio")
CLOCK = 1_022_727
RATE = 44100
TICK = 60          # play calls a second
STEP = 6           # ticks a 16th: 150 BPM

GATE, SYNC, RING, TEST = 1, 2, 4, 8
TRI, SAW, PULSE, NOISE = 16, 32, 64, 128


def midi(n):
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    p = names[n[0]]
    i = 1
    if n[i] == "#":
        p += 1
        i += 1
    elif n[i] == "b":
        p -= 1
        i += 1
    return 12 * (int(n[i:]) + 1) + p


def freq_reg(m, cents=0.0):
    f = 440.0 * 2 ** ((m - 69 + cents / 100.0) / 12)
    return max(0, min(0xFFFF, int(round(f * 16777216 / CLOCK))))


# ---------------------------------------------------------------- the score
# One bar = 16 sixteenths. Tokens: a note, '=' hold, '.' release.
CHORDS = {
    "Am": ("A", ["A3", "C4", "E4"]), "F": ("F", ["F3", "A3", "C4"]), "C": ("C", ["C4", "E4", "G4"]),
    "G": ("G", ["G3", "B3", "D4"]), "E": ("E", ["E3", "G#3", "B3"]), "Dm": ("D", ["D4", "F4", "A4"]),
}

PROG_A = ["Am", "F", "C", "G", "Am", "F", "C", "E"]
PROG_B = ["Dm", "Am", "E", "Am", "Dm", "F", "G", "E"]

MEL_A = [
    "A4 = = C5 = E5 = = D5 = C5 = B4 = A4 =",
    "F4 = = A4 = C5 = = A4 = G4 = F4 = = =",
    "E4 = = G4 = C5 = = E5 = D5 = C5 = = =",
    "D5 = = = B4 = G4 = = = A4 = B4 = = =",
    "A4 = C5 = E5 = A5 = = = G5 = E5 = = =",
    "F5 = = E5 = C5 = = A4 = = = C5 = D5 =",
    "E5 = = = G5 = = = E5 = D5 = C5 = = =",
    "B4 = = = G#4 = = = B4 = = = E5 = = .",
]
MEL_B = [
    "D5 = D5 = F5 = = A5 = = G5 = F5 = E5 =",
    "E5 = = = C5 = = = A4 = = = . . . .",
    "G#4 = B4 = E5 = = = G#5 = = = E5 = = =",
    "A5 = = = = = = = E5 = C5 = A4 = = =",
    "F5 = = = E5 = D5 = A4 = = = D5 = F5 =",
    "A5 = = = G5 = F5 = C5 = = = F5 = = =",
    "G5 = = = F5 = D5 = B4 = = = D5 = G5 =",
    "G#5 = = = = = = = B5 = = = = = = .",
]
REST_BAR = ". . . . . . . . . . . . . . . ."

# drums: k kick, s snare, h hat, o open hat
DR_INTRO = "k . h . k . h . k . h . k . h h"
DR_MAIN = "k . h . s . k h k . h . s . h o"
DR_FILL = "k . h . s . k h s . s s s . s s"

# song: (progression, melody, drums, arp on, bass on)
SONG = []
for i, c in enumerate(PROG_A[:4]):                       # intro: bass, drums, arp creeps in
    SONG.append((c, REST_BAR, DR_INTRO if i < 3 else DR_FILL, i >= 2, True))
for i, c in enumerate(PROG_A):                           # A
    SONG.append((c, MEL_A[i], DR_MAIN if i != 7 else DR_FILL, True, True))
for i, c in enumerate(PROG_B):                           # B
    SONG.append((c, MEL_B[i], DR_MAIN if i != 7 else DR_FILL, True, True))
for i, c in enumerate(PROG_A):                           # A again, then it loops
    SONG.append((c, MEL_A[i], DR_MAIN if i != 7 else DR_FILL, True, True))


# ---------------------------------------------------------------- the player
class Writes:
    def __init__(self, frames):
        self.f = [[] for _ in range(frames)]

    def __call__(self, frame, chip, reg, val):
        self.f[frame].append((chip, reg, val & 0xFF))


def voice_regs(chip, v):
    base = 7 * v
    return base


def play(song):
    frames = len(song) * 16 * STEP + 120
    w = Writes(frames)

    def setfreq(fr, chip, v, reg16):
        b = 7 * v
        w(fr, chip, b + 0, reg16 & 0xFF)
        w(fr, chip, b + 1, reg16 >> 8)

    def setpw(fr, chip, v, pw):
        b = 7 * v
        w(fr, chip, b + 2, pw & 0xFF)
        w(fr, chip, b + 3, (pw >> 8) & 0x0F)

    def adsr(fr, chip, v, ad, sr):
        b = 7 * v
        w(fr, chip, b + 5, ad)
        w(fr, chip, b + 6, sr)

    def ctrl(fr, chip, v, c):
        w(fr, chip, 7 * v + 4, c)

    # global setup at frame 0
    # SID A: v0 bass (filtered), v1 lead, v2 drums.  SID B: v0 arp, v1 lead echo, v2 pad.
    w(0, 0, 0x17, 0xB1)            # resonance 11, filter voice 1
    w(0, 0, 0x18, 0x1F)            # low-pass, volume 15
    w(0, 1, 0x17, 0x61)            # resonance 6, filter voice 1 (arp)
    w(0, 1, 0x18, 0x1F)
    adsr(0, 0, 0, 0x08, 0xA4)      # bass: plucky
    setpw(0, 0, 0, 0x600)
    adsr(0, 0, 1, 0x27, 0xA8)      # lead
    adsr(0, 0, 2, 0x09, 0x00)      # drums, reset per hit
    adsr(0, 1, 0, 0x06, 0x63)      # arp
    setpw(0, 1, 0, 0x300)
    adsr(0, 1, 1, 0x48, 0x88)      # echo
    adsr(0, 1, 2, 0xA8, 0xBA)      # pad: slow
    setpw(0, 1, 1, 0x800)

    lead_note = None
    lead_start = 0
    echo_q = []

    for bar, (chord, mel, drums, arp_on, bass_on) in enumerate(song):
        root, tones = CHORDS[chord]
        rootm = midi(root + "2")
        mtoks = mel.split()
        dtoks = drums.split()
        f0 = bar * 16 * STEP + 2
        # pad: one long chord third per bar
        if bar >= 4:
            setfreq(f0, 1, 2, freq_reg(midi(tones[1]) - 12))
            ctrl(f0, 1, 2, TRI | GATE)
            ctrl(f0 + 16 * STEP - 3, 1, 2, TRI)
        for s in range(16):
            fr = f0 + s * STEP
            # ---- bass: pumping 8ths, root / octave, with 16th pickups
            if bass_on:
                pat = [0, None, 0, 12, None, 0, 12, None, 0, None, 0, 12, None, 0, 12, 7]
                p = pat[s]
                if p is not None:
                    setfreq(fr, 0, 0, freq_reg(rootm + p))
                    ctrl(fr, 0, 0, SAW | GATE)
                    ctrl(fr + STEP - 2, 0, 0, SAW)
            # ---- lead
            t = mtoks[s]
            if t == ".":
                if lead_note is not None:
                    ctrl(fr, 0, 1, PULSE)
                lead_note = None
            elif t != "=":
                m = midi(t)
                ctrl(fr - 1, 0, 1, PULSE)          # gate off a frame before: clean retrigger
                setfreq(fr, 0, 1, freq_reg(m))
                ctrl(fr, 0, 1, PULSE | GATE)
                lead_note, lead_start = m, fr
                echo_q.append((fr + 3 * STEP // 2, m))
            # ---- drums on SID A voice 3
            d = dtoks[s]
            if d != ".":
                if d == "k":
                    adsr(fr, 0, 2, 0x08, 0x00)
                    seq = [(NOISE, 0x2000), (TRI, 0x0C00), (TRI, 0x0900), (TRI, 0x0700), (TRI, 0x0560), (TRI, 0x0440), (TRI, 0x0380)]
                elif d == "s":
                    adsr(fr, 0, 2, 0x09, 0x00)
                    seq = [(NOISE, 0x3000), (PULSE, 0x1400), (NOISE, 0x2400), (NOISE, 0x2000), (NOISE, 0x1C00), (NOISE, 0x1A00)]
                    setpw(fr, 0, 2, 0x800)
                elif d == "h":
                    adsr(fr, 0, 2, 0x03, 0x00)
                    seq = [(NOISE, 0xF000), (NOISE, 0xF000)]
                else:  # open hat
                    adsr(fr, 0, 2, 0x06, 0x00)
                    seq = [(NOISE, 0xE800)] * 4
                ctrl(fr - 1, 0, 2, 0)
                for k, (wave_, fq) in enumerate(seq):
                    setfreq(fr + k, 0, 2, fq)
                    ctrl(fr + k, 0, 2, wave_ | GATE)
                ctrl(fr + len(seq), 0, 2, seq[-1][0])
            # ---- arp: chord tones a frame each, retriggered every 8th
            if arp_on and s % 2 == 0:
                ctrl(fr - 1, 1, 0, PULSE)
                for k in range(STEP * 2):
                    m = midi(tones[k % 3]) + (12 if (s // 4) % 2 else 0)
                    setfreq(fr + k, 1, 0, freq_reg(m))
                ctrl(fr, 1, 0, PULSE | GATE)
                ctrl(fr + STEP * 2 - 3, 1, 0, PULSE)
        # per-frame modulation across the bar
        for k in range(16 * STEP):
            fr = f0 + k
            g = fr / TICK
            # bass filter sweep and lead PWM
            cut = int(0x280 + 0x200 * (0.5 + 0.5 * math.sin(g * 2 * math.pi / 6.4)))
            w(fr, 0, 0x15, cut & 7)
            w(fr, 0, 0x16, cut >> 3)
            acut = int(0x380 + 0x300 * (0.5 + 0.5 * math.sin(g * 2 * math.pi / 3.2 + 1)))
            w(fr, 1, 0x15, acut & 7)
            w(fr, 1, 0x16, acut >> 3)
            setpw(fr, 0, 1, int(0x500 + 0x500 * (0.5 + 0.5 * math.sin(g * 2 * math.pi / 2.0))))
            setpw(fr, 1, 0, int(0x200 + 0x300 * (0.5 + 0.5 * math.sin(g * 2 * math.pi / 1.3))))
            if lead_note is not None and fr - lead_start > 14:  # delayed vibrato
                depth = min(1.0, (fr - lead_start - 14) / 20) * 22
                setfreq(fr, 0, 1, freq_reg(lead_note, depth * math.sin(fr * 2 * math.pi * 6 / TICK)))
    # echo voice: the lead an 8th + a 16th late, an octave down, softer
    for fr, m in echo_q:
        if fr + 1 < frames:
            ctrl(fr - 1, 1, 1, PULSE)
            setfreq(fr, 1, 1, freq_reg(m - 12, 6))
            ctrl(fr, 1, 1, PULSE | GATE)
            ctrl(fr + STEP * 2, 1, 1, PULSE)
    return w.f


def render(frames, path):
    chips = [SoundInterfaceDevice(model=ChipModel.MOS8580, clock_frequency=CLOCK, sampling_frequency=RATE) for _ in range(2)]
    for c in chips:
        c._sid.clock(CLOCK // 5)
    chans = [[], []]
    cyc = CLOCK / TICK
    for f, ws in enumerate(frames):
        for chip, reg, val in ws:
            chips[chip]._sid.write(reg, val)
        n = int(round(cyc * (f + 1))) - int(round(cyc * f))
        for c in range(2):
            chans[c] += chips[c]._sid.clock(n)
    n = min(map(len, chans))
    st = np.stack([np.array(chans[0][:n]), np.array(chans[1][:n])], axis=1).astype(np.float32)
    st -= st.mean(axis=0)
    # light crossfeed so headphones don't hear two chips hard-panned
    mix = np.stack([st[:, 0] + 0.3 * st[:, 1], st[:, 1] + 0.3 * st[:, 0]], axis=1)
    # fade the last 2 s
    fade = int(2 * RATE)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    mix = mix / np.abs(mix).max() * 0.89 * 32767
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(mix.astype(np.int16).tobytes())
    return n / RATE


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    secs = render(play(SONG), OUT / "stax-theme.wav")
    print(f"theme: {secs:.1f} s, {len(SONG)} bars")
