"""sidtrack: a small two-SID tracker for One Off Stax's music.

A song is instruments + patterns + sections. Every 1/60 s frame the engine writes SID
registers, as a .sid play routine would, and two reSIDfp 8580s render the result
(SID A left, SID B right).

Voices are "A0".."A2" and "B0".."B2". Pattern tokens, one per 16th:
  note      C4, F#2, Bb3       '~' prefix slides from the previous note, '!' suffix accents
  chord     A4:m7              played as an arpeggio (see Inst.arp)
  -         tie (hold the previous note)
  .         nothing new
  drums     k kick, s snare, c clap, h hat, o open hat, m metal, t/T toms, r riser, x crash
"""
import math
import wave
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from pyresidfp import SoundInterfaceDevice
from pyresidfp._pyresidfp import ChipModel

CLOCK, RATE, TICK = 1_022_727, 44100, 60
GATE, SYNC, RING = 1, 2, 4
TRI, SAW, PULSE, NOISE = 16, 32, 64, 128
LP, BP, HP = 0x10, 0x20, 0x40

CHORDS = {
    "m": [0, 3, 7], "M": [0, 4, 7], "m7": [0, 3, 7, 10], "M7": [0, 4, 7, 11], "7": [0, 4, 7, 10],
    "m8": [0, 3, 7, 12], "M8": [0, 4, 7, 12], "5": [0, 7, 12], "sus": [0, 5, 7], "m9": [0, 3, 7, 10, 14],
    "add9": [0, 4, 7, 14], "o": [0, 12], "m6": [0, 3, 7, 9], "sus4": [0, 5, 7, 12],
}


def midi(n):
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    p, i = names[n[0]], 1
    while i < len(n) and n[i] in "#b":
        p += 1 if n[i] == "#" else -1
        i += 1
    return 12 * (int(n[i:]) + 1) + p


def freq_reg(m):
    f = 440.0 * 2 ** ((m - 69) / 12)
    return max(0, min(0xFFFF, int(round(f * 16777216 / CLOCK))))


@dataclass
class Inst:
    wave: int = PULSE
    ad: int = 0x09
    sr: int = 0x80
    pw: int = 0x800
    pwm: Optional[tuple] = None        # (depth, period seconds)
    gate: Optional[int] = None         # frames the gate stays on, None = to the end of the note
    vib: Optional[tuple] = None        # (delay frames, depth cents, rate Hz)
    arp: str = "fast"                  # chords: "fast" (1 frame a tone), "slow" (2), "16th", "16th-ud"
    arp_phase: int = 0
    slide: int = 5                     # frames a '~' slide takes
    sync: Optional[tuple] = None       # (ratio start, ratio end, frames): hard sync to the previous voice
    ring: Optional[float] = None       # ring-modulate with the previous voice at this pitch ratio
    acid: Optional[tuple] = None       # (peak, accent peak, decay frames): per-note filter envelope
    formant: Optional[list] = None     # cutoffs cycled per note: a filtered "vocoder" lead
    hr: bool = True                    # hard restart
    octave: int = 0
    detune: float = 0.0                # cents


KITS = {
    # each hit: (AD, SR, [(wave, freq or (from, to), gate, frames), ...])
    "house": {
        "k": (0x0A, 0x00, [(NOISE, 0x3800, 1, 1), (TRI, (0x1A00, 0x0280), 1, 14)]),
        "c": (0x09, 0x00, [(NOISE, 0x2600, 1, 1), (NOISE, 0x2600, 0, 1), (NOISE, 0x2400, 1, 1), (NOISE, 0x2400, 0, 1), (NOISE, 0x2200, 1, 3)]),
        "s": (0x09, 0x00, [(NOISE, 0x3400, 1, 1), (PULSE, 0x1300, 1, 1), (NOISE, 0x2800, 1, 4)]),
        "h": (0x02, 0x00, [(NOISE, 0xE800, 1, 2)]),
        "o": (0x07, 0x00, [(NOISE, 0xE000, 1, 4)]),
    },
    "pop": {
        "k": (0x08, 0x00, [(NOISE, 0x3000, 1, 1), (TRI, (0x1400, 0x0500), 1, 7)]),
        "s": (0x0A, 0x00, [(NOISE, 0x3800, 1, 1), (PULSE, 0x1600, 1, 1), (NOISE, 0x3000, 1, 5)]),
        "c": (0x09, 0x00, [(NOISE, 0x2800, 1, 1), (NOISE, 0x2800, 0, 1), (NOISE, 0x2800, 1, 3)]),
        "h": (0x02, 0x00, [(NOISE, 0xF000, 1, 2)]),
        "o": (0x06, 0x00, [(NOISE, 0xE800, 1, 4)]),
        "t": (0x0A, 0x00, [(TRI, (0x1600, 0x0A00), 1, 8)]),
        "T": (0x0A, 0x00, [(TRI, (0x0E00, 0x0600), 1, 9)]),
    },
    "industrial": {
        "k": (0x09, 0x00, [(NOISE, 0x2400, 1, 1), (TRI, (0x1000, 0x0300), 1, 9)]),
        "s": (0x0B, 0x00, [(NOISE, 0x4000, 1, 1), (PULSE, 0x0E00, 1, 2), (NOISE, 0x1E00, 1, 6)]),
        "m": (0x0B, 0x00, [(TRI | RING, 0x5600, 1, 2), (TRI | RING, 0x3A00, 1, 4)]),
        "h": (0x03, 0x00, [(NOISE, 0xC000, 1, 2)]),
        "o": (0x07, 0x00, [(NOISE, 0xB800, 1, 4)]),
        "c": (0x0A, 0x00, [(NOISE, 0x2000, 1, 1), (NOISE, 0x2000, 0, 1), (NOISE, 0x1C00, 1, 4)]),
    },
    "rock": {
        "k": (0x09, 0x00, [(NOISE, 0x2800, 1, 1), (TRI, (0x1200, 0x0380), 1, 9)]),
        "s": (0x0B, 0x00, [(NOISE, 0x3C00, 1, 1), (PULSE, 0x1000, 1, 2), (NOISE, 0x2C00, 1, 7)]),
        "h": (0x03, 0x00, [(NOISE, 0xD800, 1, 2)]),
        "o": (0x08, 0x00, [(NOISE, 0xD000, 1, 5)]),
        "c": (0x0A, 0x00, [(NOISE, 0x2600, 1, 1), (NOISE, 0x2600, 0, 1), (NOISE, 0x2400, 1, 4)]),
    },
    "stomp": {
        "k": (0x0A, 0x00, [(NOISE, 0x1C00, 1, 1), (TRI, (0x0C00, 0x0280), 1, 12)]),
        "c": (0x0B, 0x00, [(NOISE, 0x2200, 1, 1), (NOISE, 0x2200, 0, 1), (NOISE, 0x2000, 1, 1), (NOISE, 0x2000, 0, 1), (NOISE, 0x1E00, 1, 5)]),
        "h": (0x04, 0x00, [(NOISE, 0xA800, 1, 3)]),
        "o": (0x07, 0x00, [(NOISE, 0xA000, 1, 5)]),
    },
}
COMMON = {
    "x": (0x0C, 0x00, [(NOISE, 0xF000, 1, 3)]),
}


def parse(pat):
    toks = pat.split()
    if len(toks) % 16:
        raise ValueError(f"pattern of {len(toks)} steps: {pat[:60]}")
    ev, i = [], 0
    while i < len(toks):
        t = toks[i]
        if t in ".-":
            i += 1
            continue
        L = 1
        while i + L < len(toks) and toks[i + L] == "-":
            L += 1
        ev.append((i, L, t))
        i += 1
    return len(toks), ev


def note_token(t):
    slide = t.startswith("~")
    t = t.lstrip("~")
    acc = t.endswith("!")
    t = t.rstrip("!")
    if ":" in t:
        n, c = t.split(":")
        root = midi(n)
        notes = [root + o for o in CHORDS[c]]
    else:
        notes = [midi(t)]
    return notes, slide, acc


def bars(*chunks):
    """Join pattern strings bar by bar."""
    return " ".join(chunks)


def held(*chords):
    """One chord or note held a whole bar each: held('A4:m8', 'F4:M8')."""
    return " ".join(c + " -" * 15 for c in chords)


def rhythm(r, *chords):
    """Repeat a 16-step rhythm with X replaced by each bar's chord or note."""
    return " ".join(r.replace("X", c) for c in chords)


@dataclass
class Song:
    title: str
    job: int
    bpm: float
    swing: float = 0.0
    insts: dict = field(default_factory=dict)
    sections: list = field(default_factory=list)
    filt: dict = field(default_factory=dict)       # song default per chip
    style: str = ""

    def section(self, name, nbars, voices, filt=None, pump=None, transpose=0):
        self.sections.append(dict(name=name, bars=nbars, voices=voices, filt=filt or {}, pump=pump or {}, transpose=transpose))


VOICES = ["A0", "A1", "A2", "B0", "B1", "B2"]


def compose(song):
    """Sections -> per-voice event lists, steps counted in 16ths from the song's start."""
    events = {v: [] for v in VOICES}
    sec_spans = []
    step0 = 0
    for sec in song.sections:
        n = sec["bars"] * 16
        sec_spans.append((step0, step0 + n, sec))
        later = []
        for v, spec in sec["voices"].items():
            if spec[0] == "echo":
                later.append((v, spec))
                continue
            pat, inst = spec[0], spec[1]
            trans = spec[2] if len(spec) > 2 else [0]
            plen, pev = parse(pat)
            reps = math.ceil(n / plen)
            for r in range(reps):
                tr = trans[r % len(trans)]
                for (s, L, t) in pev:
                    st = r * plen + s
                    if st >= n:
                        break
                    L = min(L, n - st)
                    if inst.startswith("kit:"):
                        events[v].append(dict(step=step0 + st, len=L, drum=t, kit=inst[4:]))
                    else:
                        notes, slide, acc = note_token(t)
                        sh = tr + sec["transpose"] + song.insts[inst].octave * 12
                        events[v].append(dict(step=step0 + st, len=L, notes=[x + sh for x in notes], slide=slide, acc=acc, inst=inst))
        for v, (_, src, delay, tr, inst) in later:
            for e in events[src]:
                if step0 <= e["step"] < step0 + n and "notes" in e:
                    st = e["step"] + delay
                    if st < step0 + n:
                        events[v].append(dict(step=st, len=min(e["len"], step0 + n - st), notes=[x + tr for x in e["notes"]],
                                              slide=False, acc=False, inst=inst))
        step0 += n
    for v in VOICES:
        events[v].sort(key=lambda e: e["step"])
    return events, sec_spans, step0


def play(song):
    events, spans, total_steps = compose(song)
    fps16 = 900.0 / song.bpm

    def F(step):
        b = step * fps16
        if song.swing and step % 4 in (2, 3):
            b += song.swing * fps16
        return int(round(b)) + 3

    total = F(total_steps) + 150
    W = [[] for _ in range(total + 4)]
    cut_override = [[None, None] for _ in range(total + 4)]

    def w(fr, chip, reg, val):
        if 0 <= fr < len(W):
            W[fr].append((chip, reg, int(val) & 0xFF))

    def setfreq(fr, c, v, r):
        w(fr, c, 7 * v, r & 0xFF)
        w(fr, c, 7 * v + 1, (r >> 8) & 0xFF)

    def setpw(fr, c, v, pw):
        w(fr, c, 7 * v + 2, pw & 0xFF)
        w(fr, c, 7 * v + 3, (pw >> 8) & 0x0F)

    def ctrl(fr, c, v, x):
        w(fr, c, 7 * v + 4, x)

    def adsr(fr, c, v, ad, sr):
        w(fr, c, 7 * v + 5, ad)
        w(fr, c, 7 * v + 6, sr)

    for vname in VOICES:
        c, v = (0 if vname[0] == "A" else 1), int(vname[1])
        master = (v + 2) % 3
        evs = events[vname]
        for k, e in enumerate(evs):
            fs, fe = F(e["step"]), F(e["step"] + e["len"])
            nxt = evs[k + 1] if k + 1 < len(evs) else None
            if "drum" in e:
                kit = KITS[e["kit"]]
                ad, sr, seq = kit.get(e["drum"]) or COMMON.get(e["drum"]) or (None, None, None)
                if e["drum"] == "r":   # riser: noise climbing for the event's length
                    n = max(4, fe - fs)
                    ctrl(fs - 1, c, v, 0)
                    adsr(fs - 1, c, v, 0x90, 0xF0)
                    for i in range(n):
                        setfreq(fs + i, c, v, int(0x0500 * (0xF000 / 0x0500) ** (i / n)))
                        ctrl(fs + i, c, v, NOISE | GATE)
                    ctrl(fs + n, c, v, NOISE)
                    continue
                if seq is None:
                    continue
                ctrl(fs - 1, c, v, 0)
                adsr(fs - 1, c, v, ad, sr)
                f = fs
                for (wv, fq, g, nfr) in seq:
                    for i in range(nfr):
                        if isinstance(fq, tuple):
                            a, b = fq
                            r = int(a * (b / a) ** ((i + 1) / nfr))
                        else:
                            r = fq
                        setfreq(f, c, v, r)
                        ctrl(f, c, v, wv | (GATE if g else 0))
                        f += 1
                ctrl(f, c, v, seq[-1][0])
                continue
            ins = song.insts[e["inst"]]
            legato_in = e["slide"] and k > 0 and "notes" in evs[k - 1] and F(evs[k - 1]["step"] + evs[k - 1]["len"]) >= fs
            legato_out = nxt is not None and nxt.get("slide") and F(nxt["step"]) <= fe
            wave_bits = ins.wave | (SYNC if ins.sync else 0) | (RING if ins.ring else 0)
            if not legato_in:
                if ins.hr:
                    ctrl(fs - 2, c, v, wave_bits)
                    adsr(fs - 2, c, v, 0x00, 0x00)
                adsr(fs - 1, c, v, ins.ad, ins.sr)
                if ins.sync or ins.ring:
                    ctrl(fs, c, master, 0)
            gate_end = fe - 1 if not legato_out else fe
            if ins.gate:
                gate_end = min(gate_end, fs + ins.gate)
            prev_m = evs[k - 1]["notes"][0] if legato_in else None
            notes = e["notes"]
            for f in range(fs, fe):
                t = f - fs
                if len(notes) > 1:
                    if ins.arp == "fast":
                        idx = t + ins.arp_phase
                    elif ins.arp == "slow":
                        idx = t // 2 + ins.arp_phase
                    else:
                        idx = int(t / fps16) + ins.arp_phase
                    if ins.arp == "16th-ud" and len(notes) > 2:
                        cyc = notes + notes[-2:0:-1]
                        m = cyc[idx % len(cyc)]
                    else:
                        m = notes[idx % len(notes)]
                else:
                    m = notes[0]
                if prev_m is not None and t < ins.slide:
                    m = prev_m + (m - prev_m) * (t / ins.slide)
                cents = ins.detune
                if ins.vib and t > ins.vib[0]:
                    ramp = min(1.0, (t - ins.vib[0]) / 20)
                    cents += ins.vib[1] * ramp * math.sin(2 * math.pi * ins.vib[2] * f / TICK)
                mm = m + cents / 100
                if ins.sync:
                    r0, r1, n = ins.sync
                    ratio = r0 + (r1 - r0) * min(1.0, t / n)
                    setfreq(f, c, master, freq_reg(mm))
                    setfreq(f, c, v, freq_reg(mm + 12 * math.log2(ratio)))
                elif ins.ring:
                    setfreq(f, c, master, freq_reg(mm + 12 * math.log2(ins.ring)))
                    setfreq(f, c, v, freq_reg(mm))
                else:
                    setfreq(f, c, v, freq_reg(mm))
                pw = ins.pw
                if ins.pwm:
                    pw = int(ins.pw + ins.pwm[0] * math.sin(2 * math.pi * f / (TICK * ins.pwm[1])))
                setpw(f, c, v, max(0x080, min(0xF7F, pw)))
                if ins.acid:
                    peak = ins.acid[1] if e["acc"] else ins.acid[0]
                    cut_override[f][c] = ("add", peak * math.exp(-t / ins.acid[2]))
                if ins.formant:
                    cut_override[f][c] = ("set", ins.formant[k % len(ins.formant)])
            if not legato_in:
                ctrl(fs, c, v, wave_bits | GATE)
            if gate_end < fe or not legato_out:
                ctrl(gate_end, c, v, wave_bits)

    # chip-level: filter, routing, volume pumping, per section
    state = {0: dict(song.filt.get("A", {})), 1: dict(song.filt.get("B", {}))}
    for (s0, s1, sec) in spans:
        f0, f1 = F(s0), F(s1)
        for ci, cn in ((0, "A"), (1, "B")):
            if cn in sec["filt"]:
                state[ci] = dict(state[ci], **sec["filt"][cn])
            st = state[ci]
            mode = st.get("mode", 0)
            res = st.get("res", 0)
            route = sum(1 << int(r[1]) for r in st.get("route", []))
            w(f0, ci, 0x17, (res << 4) | route)
            cut = st.get("cut", 0x400)
            pump = sec["pump"].get(cn, 0)
            beat = 4 * fps16
            for f in range(f0, f1):
                p = (f - f0) / max(1, f1 - f0)
                if isinstance(cut, tuple) and cut[0] == "ramp":
                    cv = cut[1] + (cut[2] - cut[1]) * p
                elif isinstance(cut, tuple) and cut[0] == "lfo":
                    period = cut[3] * 16 * fps16
                    cv = cut[1] + cut[2] * math.sin(2 * math.pi * (f - f0) / period)
                else:
                    cv = cut
                ov = cut_override[f][ci]
                if ov:
                    cv = cv + ov[1] if ov[0] == "add" else ov[1]
                cv = int(max(0, min(2047, cv)))
                w(f, ci, 0x15, cv & 7)
                w(f, ci, 0x16, cv >> 3)
                vol = 15
                if pump:
                    ph = ((f - F(s0)) % beat) / beat
                    vol = int(round(15 - pump * max(0.0, 1 - ph / 0.5) ** 1.6))
                w(f, ci, 0x18, mode | vol)
    return W


def render(frames, path, crossfeed=0.45, fade_s=2.5):
    chips = [SoundInterfaceDevice(model=ChipModel.MOS8580, clock_frequency=CLOCK, sampling_frequency=RATE) for _ in range(2)]
    for c in chips:
        c._sid.clock(CLOCK // 5)
    ch = [[], []]
    cyc = CLOCK / TICK
    for f, ws in enumerate(frames):
        for c, r, v in ws:
            chips[c]._sid.write(r, v)
        n = int(round(cyc * (f + 1))) - int(round(cyc * f))
        for c in range(2):
            ch[c] += chips[c]._sid.clock(n)
    n = min(map(len, ch))
    st = np.stack([np.array(ch[0][:n]), np.array(ch[1][:n])], axis=1).astype(np.float32)
    st -= st.mean(axis=0)
    a = st / (np.abs(st).max(axis=0) + 1e-9)       # balance the two chips
    mix = np.stack([a[:, 0] + crossfeed * a[:, 1], a[:, 1] + crossfeed * a[:, 0]], axis=1)
    fade = int(fade_s * RATE)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    mix = mix / np.abs(mix).max() * 0.89 * 32767
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(mix.astype(np.int16).tobytes())
    return n / RATE
