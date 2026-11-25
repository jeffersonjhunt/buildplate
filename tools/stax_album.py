"""One Off Stax: ten songs, one per job, each in its own style (synthpop, French house, industrial,
robot rock, acid, TRON-like, ...). All melodies are original. Rendered on two emulated 8580 SIDs."""
import sys
from pathlib import Path

import stax_music as theme
from sidtrack import (BP, LP, NOISE, PULSE, SAW, TRI, Inst, Song, bars, held, play, render, rhythm)

K4 = "k . . . k . . . k . . . k . . ."
REST = ". " * 15 + "."


def rep(p, n):
    return " ".join([p] * n)


def mel(lines):
    return " ".join(l.replace("=", "-") for l in lines)


SONGS = []

# ---------------------------------------------------------------- 1  First Shift: bright synthpop
s = Song("First Shift", 1, 116, style="Bright early-80s synthpop: bouncing octave bass, bell arpeggios, echoing lead")
s.insts = dict(
    bass=Inst(PULSE, ad=0x08, sr=0x70, pw=0x300),
    bass_long=Inst(PULSE, ad=0x2A, sr=0xA9, pw=0x400),
    lead=Inst(PULSE, ad=0x09, sr=0xA9, pw=0x600, pwm=(0x300, 2.0), vib=(14, 18, 5.5)),
    echo=Inst(PULSE, ad=0x0A, sr=0x56, pw=0x300, vib=(14, 14, 5.5)),
    bells=Inst(PULSE, ad=0x05, sr=0x53, pw=0x200, arp="16th"),
)
BASS1 = "A1 . A2 . A1 A1 A2 . A1 . A2 . A1 A1 A2 G2"
PA, PB = [0, -4, 3, -2, 0, -4, 3, -5], [5, 0, -5, 0, 5, -4, -2, -5]
BELLS_A = held("A4:m8", "F4:M8", "C5:M8", "G4:M8", "A4:m8", "F4:M8", "C5:M8", "E4:M8")
BELLS_B = held("D5:m8", "A4:m8", "E4:M8", "A4:m8", "D5:m8", "F4:M8", "G4:M8", "E4:M8")
DR1 = rep("k . . . s . . . k . k . s . . .", 7) + " k . . . s . . . k . s s s . t T"
HAT8, HAT16 = "h . h . h . h . h . h . h . h .", "h h o h h h o h h h o h h h o h"
s.filt = dict(B=dict(mode=LP, res=9, route=["B0"], cut=0x700))
s.section("intro", 4, {"A0": (BASS1, "bass", PA[:4]), "A2": (K4, "kit:pop"), "B0": (BELLS_A, "bells"), "B2": (HAT8, "kit:pop")},
          filt=dict(B=dict(cut=("ramp", 0x100, 0x600))))
s.section("A", 8, {"A0": (BASS1, "bass", PA), "A1": (mel(theme.MEL_A), "lead"), "A2": (DR1, "kit:pop"), "B0": (BELLS_A, "bells"),
                   "B1": ("echo", "A1", 3, 0, "echo"), "B2": (HAT8, "kit:pop")}, filt=dict(B=dict(cut=0x700)))
s.section("B", 8, {"A0": (BASS1, "bass", PB), "A1": (mel(theme.MEL_B), "lead"), "A2": (DR1, "kit:pop"), "B0": (BELLS_B, "bells"),
                   "B1": ("echo", "A1", 3, 0, "echo"), "B2": (HAT16, "kit:pop")})
s.section("break", 4, {"A0": (held("A1", "F1", "C2", "G1"), "bass_long"), "B0": (BELLS_A, "bells")},
          filt=dict(B=dict(cut=("ramp", 0x700, 0x180))))
s.section("A2", 8, {"A0": (BASS1, "bass", PA), "A1": (mel(theme.MEL_A), "lead"), "A2": (DR1, "kit:pop"), "B0": (BELLS_A, "bells"),
                    "B1": ("echo", "A1", 3, 0, "echo"), "B2": (HAT16, "kit:pop")}, filt=dict(B=dict(cut=0x7FF)))
SONGS.append(s)

# ---------------------------------------------------------------- 2  Warm-Up: filtered French house
s = Song("Warm-Up", 2, 120, style="Filtered French house: four-on-the-floor, pumping chord loop under a sweeping filter")
s.insts = dict(
    bass=Inst(SAW, ad=0x08, sr=0x60, gate=5),
    stab=Inst(SAW, ad=0x06, sr=0x50, arp="fast"),
    pad=Inst(PULSE, ad=0x8A, sr=0xA8, pw=0x800, pwm=(0x500, 3.0), arp="slow"),
    lead=Inst(PULSE, ad=0x08, sr=0x96, pw=0x500, pwm=(0x200, 1.2), vib=(20, 12, 6)),
)
CH2 = ["D4:m7", "D4:m7", "Bb3:M7", "C4:add9"]
STAB2 = rhythm(". . X - . X - . . . X - . X . X", *CH2)
BASS2 = "D2 . D3 . . D2 D3 . D2 . D3 . C3 . D3 ."
LEAD2 = bars("A4 - . A4 . C5 - . D5 . C5 . A4 - . .", "G4 - . G4 . A4 - . F4 - E4 - D4 - . .")
HAT2, HAT2I = ". . o . c . o . . . o . c . o .", ". . o . . . o . . . o . . . o ."
BUILD = bars("c . . . c . . . c . . . c . . .", "c . . . c . . . c . c . c . c .",
             "c . c . c . c . c . c . c . c .", "c c c c c c c c c c c c c c c c")
RISER4 = "r" + " -" * 63
s.filt = dict(B=dict(mode=LP, res=13, route=["B0"], cut=0x300))
s.section("intro1", 4, {"A2": (K4, "kit:house"), "B0": (STAB2, "stab")},
          filt=dict(B=dict(cut=("ramp", 0x080, 0x2A0))), pump=dict(B=6))
s.section("intro2", 4, {"A2": (K4, "kit:house"), "A1": (HAT2I, "kit:house"), "B0": (STAB2, "stab")},
          filt=dict(B=dict(cut=("ramp", 0x2A0, 0x380))), pump=dict(B=6))
s.section("A", 8, {"A0": (BASS2, "bass", [0, 0, -4, -2]), "A1": (HAT2, "kit:house"), "A2": (K4, "kit:house"), "B0": (STAB2, "stab")},
          filt=dict(B=dict(cut=("lfo", 0x380, 0x150, 4))), pump=dict(B=7))
s.section("B", 8, {"A0": (BASS2, "bass", [0, 0, -4, -2]), "A1": (HAT2, "kit:house"), "A2": (K4, "kit:house"), "B0": (STAB2, "stab"),
                   "B1": (held(*CH2), "pad"), "B2": (LEAD2, "lead")}, filt=dict(B=dict(cut=0x600)), pump=dict(B=7))
s.section("break", 4, {"B0": (STAB2, "stab"), "B1": (held(*CH2), "pad"), "B2": (LEAD2, "lead")},
          filt=dict(B=dict(cut=("ramp", 0x600, 0x0A0))))
s.section("build", 4, {"A1": (BUILD, "kit:house"), "A2": (RISER4, "kit:house"), "B0": (STAB2, "stab")},
          filt=dict(B=dict(cut=("ramp", 0x0A0, 0x700))))
s.section("drop", 8, {"A0": (BASS2, "bass", [0, 0, -4, -2]), "A1": (HAT2, "kit:house"), "A2": (K4, "kit:house"), "B0": (STAB2, "stab"),
                      "B1": (held(*CH2), "pad"), "B2": (LEAD2, "lead")}, filt=dict(B=dict(cut=0x7A0)), pump=dict(B=8))
SONGS.append(s)

# ---------------------------------------------------------------- 3  Conveyor: industrial synthpop
s = Song("Conveyor", 3, 122, style="Industrial synthpop: 16th sequencer bass, clanging metal percussion, brass stabs")
s.insts = dict(
    seq=Inst(SAW, ad=0x07, sr=0x40, gate=3),
    stab=Inst(SAW, ad=0x09, sr=0x00, arp="fast"),
    lead=Inst(PULSE, ad=0x2A, sr=0x9A, pw=0x500, vib=(24, 20, 4.8)),
    pad=Inst(TRI, ad=0xAA, sr=0xBA, arp="slow"),
)
SEQ3 = "E2 E2 E3 E2 B1 E2 E3 E2 E2 E2 E3 E2 G2 E2 D3 E2"
METAL = bars(". . . . . . m . . . . . . m . .", "m . . . . . m . . m . . . . . .")
DR3 = rep("k . . k s . . . k . k . s . . k", 7) + " k . . k s . . . k . s . s s s s"
STAB3 = rhythm("X - . . . . X - . . . . X . . .", "E4:m", "E4:m", "C4:M", "D4:M")
LEAD3 = bars("B4 - - - - - G4 - A4 - B4 - - - . .", "D5 - - - B4 - - - A4 - G4 - E4 - - -",
             "E4 - G4 - - - E4 - G4 - C5 - - - B4 -", "A4 - - - - - - - F#4 - - - D4 - . .",
             "B4 - - - - - G4 - A4 - B4 - - - E5 -", "D5 - - - B4 - - - A4 - G4 - A4 - B4 -",
             "C5 - - - B4 - - - G4 - E4 - - - G4 -", "F#4 - - - - - - - - - - - . . . .")
HAT3 = "h . h h h . h h h . h h h . o ."
s.filt = dict(A=dict(mode=LP, res=11, route=["A0"], cut=0x380), B=dict(mode=LP, res=5, route=["B0"], cut=0x500))
s.section("intro", 4, {"A0": (SEQ3, "seq", [0, 0, -4, -2]), "A1": (METAL, "kit:industrial")},
          filt=dict(A=dict(cut=("ramp", 0x150, 0x380))))
s.section("A", 8, {"A0": (SEQ3, "seq", [0, 0, -4, -2]), "A1": (METAL, "kit:industrial"), "A2": (DR3, "kit:industrial"),
                   "B0": (STAB3, "stab"), "B2": (HAT3, "kit:industrial")}, filt=dict(A=dict(cut=("lfo", 0x380, 0x180, 2))))
s.section("B", 8, {"A0": (SEQ3, "seq", [0, 0, -4, -2]), "A1": (METAL, "kit:industrial"), "A2": (DR3, "kit:industrial"),
                   "B0": (STAB3, "stab"), "B1": (LEAD3, "lead"), "B2": (HAT3, "kit:industrial")})
s.section("break", 4, {"A1": (METAL, "kit:industrial"), "B0": (held("E3:m", "E3:m", "C3:M", "D3:M"), "pad"), "B1": (LEAD3, "lead")},
          filt=dict(B=dict(cut=0x7FF)))
s.section("A2", 8, {"A0": (SEQ3, "seq", [0, 0, -4, -2]), "A1": (METAL, "kit:industrial"), "A2": (DR3, "kit:industrial"),
                    "B0": (STAB3, "stab"), "B1": (LEAD3, "lead"), "B2": (HAT3, "kit:industrial")}, filt=dict(B=dict(cut=0x500)))
SONGS.append(s)

# ---------------------------------------------------------------- 4  Night Shift: melancholic synth drive
s = Song("Night Shift", 4, 124, style="Melancholic late-80s synth drive: pulsing 8th bass, slow pads, glassy bells, long sighing lead")
s.insts = dict(
    bass=Inst(PULSE, ad=0x06, sr=0x50, pw=0x600, gate=4),
    bells=Inst(TRI, ad=0x04, sr=0x44, arp="16th-ud"),
    pad=Inst(PULSE, ad=0x99, sr=0xBA, pw=0x400, pwm=(0x300, 4.0), arp="slow"),
    lead=Inst(PULSE, ad=0x3A, sr=0xAB, pw=0x700, vib=(30, 22, 5.0)),
)
BASS4 = "C2 . C2 . C2 . C2 . C2 . C2 . C2 . C3 ."
BELLS4 = held("C5:m8", "Ab4:M8", "Eb5:M8", "Bb4:M8")
PAD4 = held("C4:m", "Ab3:M", "Eb4:M", "Bb3:M")
LEAD4 = bars("G4 - - - - - - - Eb5 - - - D5 - C5 -", "C5 - - - - - - - - - - - Ab4 - Bb4 -",
             "G4 - - - - - - - Bb4 - - - G4 - Eb4 -", "F4 - - - - - - - - - - - . . . .",
             "G4 - - - - - - - G5 - - - F5 - Eb5 -", "Eb5 - - - - - C5 - - - - - Ab4 - C5 -",
             "Bb4 - - - - - - - G4 - - - Bb4 - D5 -", "C5 - - - - - - - - - - - - - . .")
DR4 = rep("k . . . s . . . k . . k s . . .", 7) + " k . . . s . . . t . t . T . T ."
s.filt = dict(B=dict(mode=LP, res=6, route=["B0", "B1"], cut=0x700))
s.section("intro", 8, {"B0": (BELLS4, "bells"), "B1": (PAD4, "pad")}, filt=dict(B=dict(cut=("ramp", 0x200, 0x700))))
s.section("verse", 8, {"A0": (BASS4, "bass", [0, -4, 3, -2]), "A1": (DR4, "kit:pop"), "A2": (HAT8, "kit:pop"),
                       "B0": (BELLS4, "bells"), "B1": (PAD4, "pad")}, filt=dict(B=dict(cut=0x700)))
s.section("chorus", 8, {"A0": (BASS4, "bass", [0, -4, 3, -2]), "A1": (DR4, "kit:pop"), "A2": (HAT8, "kit:pop"),
                        "B0": (BELLS4, "bells"), "B1": (PAD4, "pad"), "B2": (LEAD4, "lead")})
s.section("break", 4, {"B1": (PAD4, "pad"), "B2": (LEAD4, "lead")}, filt=dict(B=dict(cut=0x500)))
s.section("chorus2", 8, {"A0": (BASS4, "bass", [0, -4, 3, -2]), "A1": (DR4, "kit:pop"), "A2": (HAT16, "kit:pop"),
                         "B0": (BELLS4, "bells"), "B1": (PAD4, "pad"), "B2": (LEAD4, "lead")}, filt=dict(B=dict(cut=0x7FF)))
SONGS.append(s)

# ---------------------------------------------------------------- 5  Overclock: robot rock
s = Song("Overclock", 5, 126, style="Robot rock: snarling hard-sync riff, stomping beat, filter 'vocoder' call and response")
s.insts = dict(
    bass=Inst(SAW, ad=0x09, sr=0x80),
    sync=Inst(SAW, ad=0x09, sr=0xA9, sync=(1.0, 3.2, 22)),
    robot=Inst(PULSE, ad=0x06, sr=0x99, pw=0x300, formant=[0x520, 0x1E0, 0x3C0, 0x6A0, 0x2A0]),
)
RIFF5 = bars("G3 - . G3 Bb3 - . G3 C4 - Bb3 - G3 - F3 -", "G3 - . G3 Bb3 - . G3 D4 - C4 - Bb3 - C4 -")
ROBOT5 = bars("D5 - D5 - . . Bb4 - C5 - - - . . . .", "D5 - D5 - . . F5 - D5 - - - . . . .", REST, REST)
DR5 = rep("k . . . s . . . k . k . s . . .", 7) + " k . s . k . s . s s s s s s s s"
HAT5 = "h . h . h . h . h . h . h . o ."
s.filt = dict(B=dict(mode=BP, res=14, route=["B2"], cut=0x400))
s.section("intro", 4, {"B1": (RIFF5, "sync")})
s.section("A", 8, {"A0": (RIFF5, "bass", [-24]), "A1": (DR5, "kit:rock"), "A2": (HAT5, "kit:rock"), "B1": (RIFF5, "sync")})
s.section("B", 8, {"A0": (RIFF5, "bass", [-24, -28, -24, -26]), "A1": (DR5, "kit:rock"), "A2": (HAT5, "kit:rock"),
                   "B1": (RIFF5, "sync", [0, -4, 0, -2]), "B2": (ROBOT5, "robot")})
s.section("break", 4, {"A1": (DR5, "kit:rock"), "B2": (ROBOT5, "robot")})
s.section("A2", 8, {"A0": (RIFF5, "bass", [-24, -24, -28, -26]), "A1": (DR5, "kit:rock"), "A2": (HAT5, "kit:rock"),
                    "B1": (RIFF5, "sync", [0, 0, -4, -2]), "B2": (ROBOT5, "robot")})
SONGS.append(s)

# ---------------------------------------------------------------- 6  Hot Bed: disco house
s = Song("Hot Bed", 6, 128, style="Disco house: octave-bounce bass, offbeat chord stabs pumping to the kick, twin arpeggio solo")
s.insts = dict(
    bass=Inst(SAW, ad=0x07, sr=0x50, gate=4),
    stab=Inst(PULSE, ad=0x06, sr=0x40, pw=0x600, arp="fast"),
    lead=Inst(SAW, ad=0x08, sr=0xA9, vib=(16, 15, 5.8)),
    echo=Inst(PULSE, ad=0x0A, sr=0x66, pw=0x300),
    arp1=Inst(PULSE, ad=0x04, sr=0x84, pw=0x500, arp="16th-ud"),
    arp2=Inst(TRI, ad=0x04, sr=0x84, arp="16th-ud", arp_phase=2),
)
BASS6 = "F#1 F#2 . F#2 F#1 F#2 . F#2 F#1 F#2 . F#2 F#1 F#2 E2 F#2"
CH6 = ["F#4:m7", "D4:M7", "E4:M", "C#4:m7"]
STAB6 = rhythm(". . X . . . X - . . X . . . X -", *CH6)
LEAD6 = bars("C#5 - . C#5 . E5 - . F#5 - . E5 . C#5 - .", "B4 - . B4 . C#5 - . A4 - - - . . . .")
s.filt = dict(B=dict(mode=LP, res=12, route=["B0"], cut=0x5A0))
s.section("intro", 4, {"A2": (K4, "kit:house"), "A1": (HAT2I, "kit:house"), "B0": (STAB6, "stab")},
          filt=dict(B=dict(cut=("ramp", 0x100, 0x450))), pump=dict(B=6))
s.section("A", 8, {"A0": (BASS6, "bass", [0, -4, -2, -5]), "A1": (HAT2, "kit:house"), "A2": (K4, "kit:house"), "B0": (STAB6, "stab"),
                   "B1": (LEAD6, "lead"), "B2": ("echo", "B1", 3, 0, "echo")}, filt=dict(B=dict(cut=0x5A0)), pump=dict(B=7))
s.section("B", 8, {"A0": (BASS6, "bass", [0, -4, -2, -5]), "A1": (HAT2, "kit:house"), "A2": (K4, "kit:house"), "B0": (STAB6, "stab"),
                   "B1": (held("F#5:m8", "D5:M8", "E5:M8", "C#5:m8"), "arp1"),
                   "B2": (held("F#4:m8", "D4:M8", "E4:M8", "C#4:m8"), "arp2")},
          filt=dict(B=dict(cut=("lfo", 0x500, 0x200, 4))), pump=dict(B=7))
s.section("break", 4, {"B0": (STAB6, "stab"), "B1": (LEAD6, "lead")}, filt=dict(B=dict(cut=("ramp", 0x5A0, 0x0C0))))
s.section("A2", 8, {"A0": (BASS6, "bass", [0, -4, -2, -5]), "A1": (HAT2, "kit:house"), "A2": (K4, "kit:house"), "B0": (STAB6, "stab"),
                    "B1": (LEAD6, "lead"), "B2": ("echo", "B1", 3, 0, "echo")}, filt=dict(B=dict(cut=0x700)), pump=dict(B=8))
SONGS.append(s)

# ---------------------------------------------------------------- 7  Toolpath: dark arpeggio epic
s = Song("Toolpath", 7, 132, style="Dark digital epic: relentless 16th saw arpeggio under a resonant sweep, brass pads, power stabs")
s.insts = dict(
    arpbass=Inst(SAW, ad=0x06, sr=0x50, gate=3),
    pad=Inst(SAW, ad=0xA9, sr=0xCA, arp="slow"),
    stab=Inst(SAW, ad=0x0B, sr=0x00, arp="fast"),
    lead=Inst(SAW, ad=0x5A, sr=0xBA, vib=(36, 25, 4.5)),
)
ARP7 = "B1 B2 F#2 B2 B1 B2 F#2 B2 B1 B2 F#2 B2 B1 B2 A2 B2"
PAD7 = held("B3:m", "B3:m", "G3:M", "F#3:M")
STAB7 = rhythm("X - - - . . . . . . . . . . . .", "B2:5", "B2:5", "G2:5", "F#2:5")
LEAD7 = bars("F#4 - - - - - - - - - - - B4 - - -", "C#5 - - - D5 - - - C#5 - - - B4 - - -",
             "D5 - - - - - - - - - - - E5 - - -", "C#5 - - - - - - - A#4 - - - - - - -",
             "F#5 - - - - - - - E5 - - - D5 - - -", "C#5 - - - D5 - - - E5 - - - F#5 - - -",
             "G5 - - - - - - - F#5 - - - E5 - - -", "F#5 - - - - - - - - - - - - - - -")
HAT7 = "h h h h c h h h h h h h c h h c"
s.filt = dict(A=dict(mode=LP, res=14, route=["A0"], cut=0x450))
s.section("intro", 8, {"A0": (ARP7, "arpbass", [0, 0, -4, -5]), "B0": (PAD7, "pad")}, filt=dict(A=dict(cut=("ramp", 0x080, 0x420))))
s.section("drop", 8, {"A0": (ARP7, "arpbass", [0, 0, -4, -5]), "A1": (HAT7, "kit:house"), "A2": (K4, "kit:house"),
                      "B0": (PAD7, "pad"), "B1": (STAB7, "stab")}, filt=dict(A=dict(cut=("lfo", 0x450, 0x200, 2))))
s.section("B", 8, {"A0": (ARP7, "arpbass", [0, 0, -4, -5]), "A1": (HAT7, "kit:house"), "A2": (K4, "kit:house"),
                   "B0": (PAD7, "pad"), "B1": (STAB7, "stab"), "B2": (LEAD7, "lead")})
s.section("break", 4, {"A0": (ARP7, "arpbass", [0, 0, -4, -5]), "B0": (PAD7, "pad")}, filt=dict(A=dict(cut=("ramp", 0x450, 0x0C0))))
s.section("drop2", 8, {"A0": (ARP7, "arpbass", [0, 0, -4, -5]), "A1": (HAT7, "kit:house"), "A2": (K4, "kit:house"),
                       "B0": (PAD7, "pad"), "B1": (STAB7, "stab"), "B2": (LEAD7, "lead")},
          filt=dict(A=dict(cut=("lfo", 0x5A0, 0x200, 1))))
SONGS.append(s)

# ---------------------------------------------------------------- 8  Spindle Speed: swung stomp
s = Song("Spindle Speed", 8, 136, swing=0.55, style="Swung bluesy stomp: handclaps and boots, pentatonic riff, gritty sync lead")
s.insts = dict(
    bass=Inst(SAW, ad=0x08, sr=0x90),
    sync=Inst(PULSE, ad=0x08, sr=0xA9, pw=0x600, sync=(1.0, 2.2, 14)),
    drone=Inst(PULSE, ad=0x9A, sr=0xBA, pw=0x300, pwm=(0x200, 5.0), arp="slow"),
)
RIFF8 = bars("C#2 - . C#2 E2 - F#2 - . . G#2 - F#2 - E2 -", "C#2 - . C#2 E2 - F#2 - G#2 - B2 - G#2 - F#2 -")
LEAD8 = bars("G#4 - - - . . . . E4 - F#4 - G#4 - . .", "B4 - - - G#4 - - - F#4 - E4 - C#4 - - -",
             "G#4 - - - . . . . B4 - C#5 - B4 - . .", "G#4 - - - F#4 - E4 - F#4 - - - . . . .",
             "C#5 - - - . . . . B4 - G#4 - B4 - . .", "C#5 - - - E5 - - - C#5 - B4 - G#4 - - -",
             "G#4 - - - . . . . B4 - C#5 - B4 - . .", "C#4 - - - - - - - . . . . . . . .")
STOMP = "k . . . c . . . k . k . c . . ."
TAMB = "h . h . h . h . h . h . h . o ."
s.section("intro", 4, {"A1": (STOMP, "kit:stomp")})
s.section("A", 8, {"A0": (RIFF8, "bass"), "A1": (STOMP, "kit:stomp"), "A2": (TAMB, "kit:stomp")})
s.section("B", 8, {"A0": (RIFF8, "bass", [0, 0, -4, -2]), "A1": (STOMP, "kit:stomp"), "A2": (TAMB, "kit:stomp"),
                   "B1": (LEAD8, "sync"), "B2": (held("C#3:5", "C#3:5", "A2:5", "B2:5"), "drone")})
s.section("break", 4, {"A1": (STOMP, "kit:stomp"), "B1": (RIFF8, "sync", [24])})
s.section("A2", 8, {"A0": (RIFF8, "bass", [0, 0, -4, -2]), "A1": (STOMP, "kit:stomp"), "A2": (TAMB, "kit:stomp"),
                    "B1": (LEAD8, "sync"), "B2": (held("C#3:5", "C#3:5", "A2:5", "B2:5"), "drone")})
SONGS.append(s)

# ---------------------------------------------------------------- 9  Thermal Runaway: acid house
s = Song("Thermal Runaway", 9, 142, style="Acid house: squelching resonant bassline with slides and accents, screaming lead, risers")
s.insts = dict(
    acid=Inst(SAW, ad=0x09, sr=0x80, acid=(0x380, 0x620, 9), slide=4),
    stab=Inst(PULSE, ad=0x07, sr=0x00, pw=0x400, arp="fast"),
    lead=Inst(SAW, ad=0x18, sr=0xBA, vib=(18, 30, 6.5)),
)
ACID9 = bars("Eb2 Eb2! . Eb3 Eb2 . ~Gb2 Eb2 Eb2! . Bb2 ~Eb3! Eb2 . ~Db3 Eb2",
             "Eb2 . Eb3! Eb2 . Gb2 ~Ab2! Eb2 Eb2 . Db3! . Bb2 ~Eb3 Eb2 Gb2!")
HAT9 = "h h o h h h o h h h o h h h o h"
STAB9 = rhythm("X - . . . . . . . . . . . . . .", "Eb4:m", "Eb4:m", "B3:M", "Db4:M")
LEAD9 = bars("Bb5 - - - - - - - Gb5 - - - Bb5 - Db6 -", "Eb6 - - - - - - - Db6 - - - Bb5 - - -",
             "Gb5 - - - - - Ab5 - Bb5 - - - Gb5 - Eb5 -", "F5 - - - - - - - - - - - . . . .",
             "Bb5 - - - - - - - Gb5 - - - Bb5 - Db6 -", "Eb6 - - - - - - - Db6 - - - Bb5 - - -",
             "Gb5 - - - - - Ab5 - Bb5 - - - Db6 - Bb5 -", "Eb5 - - - - - - - - - - - . . . .")
CRASH = "x . . . . . . . . . . . . . . ." + (" " + REST) * 7
s.filt = dict(A=dict(mode=LP, res=15, route=["A0"], cut=0x0C0))
s.section("intro", 4, {"A0": (ACID9, "acid"), "A2": (K4, "kit:house")})
s.section("A", 8, {"A0": (ACID9, "acid"), "A1": (HAT9, "kit:house"), "A2": (K4, "kit:house")},
          filt=dict(A=dict(cut=("ramp", 0x0C0, 0x300))))
s.section("B", 8, {"A0": (ACID9, "acid", [0, -4, 0, -2]), "A1": (HAT9, "kit:house"), "A2": (K4, "kit:house"),
                   "B0": (STAB9, "stab"), "B2": (LEAD9, "lead")}, filt=dict(A=dict(cut=("lfo", 0x300, 0x100, 2))))
s.section("break", 4, {"A0": (ACID9, "acid")}, filt=dict(A=dict(cut=("ramp", 0x300, 0x650))))
s.section("rise", 4, {"A0": (ACID9, "acid"), "A1": (BUILD, "kit:house"), "B1": (RISER4, "kit:house")}, filt=dict(A=dict(cut=0x650)))
s.section("drop", 8, {"A0": (ACID9, "acid", [0, -4, 0, -2]), "A1": (HAT9, "kit:house"), "A2": (K4, "kit:house"),
                      "B0": (STAB9, "stab"), "B1": (CRASH, "kit:house"), "B2": (LEAD9, "lead")},
          filt=dict(A=dict(cut=("lfo", 0x3A0, 0x180, 1))))
SONGS.append(s)

# ---------------------------------------------------------------- 10  Max Feed Rate: anthem finale
s = Song("Max Feed Rate", 10, 150, style="Anthem finale: driving octave bass, racing arpeggios, soaring lead, key change up for the last section")
s.insts = dict(
    bass=Inst(SAW, ad=0x06, sr=0x50, gate=3),
    arp=Inst(PULSE, ad=0x04, sr=0x74, pw=0x400, pwm=(0x200, 1.5), arp="16th"),
    lead=Inst(PULSE, ad=0x09, sr=0xAA, pw=0x600, pwm=(0x300, 1.8), vib=(16, 20, 6)),
    echo=Inst(SAW, ad=0x0A, sr=0x77),
)
BASS10 = "F1 F2 F1 F2 F1 F2 F1 F2 F1 F2 F1 F2 F1 F2 Eb2 F2"
ARP10 = held("F5:m8", "Db5:M8", "Ab4:M8", "Eb5:M8")
LEAD10 = bars("C5 - - - Ab4 - - - F4 - - - G4 - Ab4 -", "Ab4 - - - - - - - F4 - Ab4 - Bb4 - C5 -",
              "Eb5 - - - C5 - - - Ab4 - - - Bb4 - C5 -", "Bb4 - - - - - - - G4 - - - . . . .",
              "C5 - - - F5 - - - Eb5 - - - C5 - Ab4 -", "Db5 - - - - - - - C5 - Bb4 - Ab4 - F4 -",
              "Ab4 - - - C5 - - - Eb5 - - - F5 - G5 -", "G5 - - - - - - - - - - - . . . .")
HAT10 = "h h h h c h h h h h h h c h h h"
HAT10X = "x . h h c h h h h h h h c h h h " + rep(HAT10, 7)
s.filt = dict(B=dict(mode=LP, res=10, route=["B0"], cut=0x700))
s.section("intro", 4, {"A2": (RISER4, "kit:house"), "B0": (ARP10, "arp")}, filt=dict(B=dict(cut=("ramp", 0x150, 0x600))))
s.section("A", 8, {"A0": (BASS10, "bass", [0, -4, 3, -2]), "A1": (HAT10, "kit:house"), "A2": (K4, "kit:house"), "B0": (ARP10, "arp")},
          filt=dict(B=dict(cut=0x700)), pump=dict(B=5))
s.section("B", 8, {"A0": (BASS10, "bass", [0, -4, 3, -2]), "A1": (HAT10, "kit:house"), "A2": (K4, "kit:house"), "B0": (ARP10, "arp"),
                   "B1": (LEAD10, "lead"), "B2": ("echo", "B1", 2, -12, "echo")}, pump=dict(B=5))
s.section("break", 4, {"B0": (ARP10, "arp"), "B1": (LEAD10, "lead"), "B2": ("echo", "B1", 2, -12, "echo")},
          filt=dict(B=dict(cut=("ramp", 0x700, 0x200))))
s.section("lift", 8, {"A0": (BASS10, "bass", [0, -4, 3, -2]), "A1": (HAT10X, "kit:house"), "A2": (K4, "kit:house"), "B0": (ARP10, "arp"),
                      "B1": (LEAD10, "lead"), "B2": ("echo", "B1", 2, -12, "echo")},
          filt=dict(B=dict(cut=0x7FF)), pump=dict(B=6), transpose=2)
SONGS.append(s)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "album")
    out.mkdir(parents=True, exist_ok=True)
    only = set(int(a) for a in sys.argv[2:]) if len(sys.argv) > 2 else None
    for s in SONGS:
        if only and s.job not in only:
            continue
        name = f"job{s.job:02d}-{s.title.lower().replace(' ', '-')}"
        secs = render(play(s), out / f"{name}.wav")
        nbars = sum(x["bars"] for x in s.sections)
        print(f"job {s.job:2d} {s.title:16s} {s.bpm:5.0f} BPM {nbars} bars {secs:5.1f} s")
