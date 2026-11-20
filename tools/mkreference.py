"""Make every reference picture and sound in this repo from the scripts beside it.

    python3 -I tools/mkreference.py              # art/, mockups/png/ and audio/sfx/ (about a minute)
    python3 -I tools/mkreference.py --songs      # also audio/songs/ (MP3s, needs ffmpeg; a few minutes)

Everything is seeded, so a run rebuilds the same files. Outputs, relative to the repo root:

    art/backdrops/jobNN-<name>.png   the ten backdrops (640x480 RGB444) and title-grid-horizon.png
    mockups/png/screen-*.png         the screens, pixel exact
    audio/sfx/<effect>.wav           the sixteen effects, 8-bit unsigned at 20,000 Hz, no trailing 0
    audio/songs/jobNN-<title>.mp3    the songs rendered on two reSIDfp 8580s (with --songs)
"""
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from PIL import Image, ImageDraw  # noqa: E402

import bp_backdrops  # noqa: E402
import ooe_mock640 as m  # noqa: E402

# job -> (backdrop name, its generator)
JOBS = [
    ("moonbase", m.bg_moonbase), ("gas-giant", m.bg_gas_giant), ("orbital-station", m.bg_station),
    ("ice-aurora", bp_backdrops.bg_ice_aurora), ("shipyard", bp_backdrops.bg_shipyard),
    ("twin-suns", bp_backdrops.bg_twin_suns), ("derelict", m.bg_derelict), ("neon-city", bp_backdrops.bg_neon_city),
    ("grid-horizon", m.bg_grid_horizon), ("black-hole", bp_backdrops.bg_black_hole),
]
SONG_TITLES = ["First Shift", "Warm-Up", "Conveyor", "Night Shift", "Overclock", "Hot Bed", "Toolpath",
               "Spindle Speed", "Thermal Runaway", "Max Feed Rate"]
BACKDROP_NAMES = ["MOONBASE", "GAS GIANT", "ORBITAL STATION", "ICE PLANET", "ORBITAL SHIPYARD",
                  "TWIN-SUN DESERT", "DERELICT", "NEON CITY", "GRID HORIZON", "BLACK HOLE"]
SPEEDS = ["1.0", "1.3", "1.6", "2.1", "3.8", "7.4", "15", "35", "88", "143"]


def job_card(bg, job):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 340, 639, 431], fill=m.PANEL)
    d.line([0, 340, 639, 340], fill=m.ORANGE)
    d.line([0, 431, 639, 431], fill=m.ORANGE)
    m.text(img, 40, 356, "JOB", m.DIM)
    m.text(img, 40, 374, f"{job:02d}", m.AMBER, scale=5, shadow=m.ORANGE)
    m.text(img, 176, 358, SONG_TITLES[job - 1].upper(), m.BONE, scale=3)
    m.text(img, 176, 394, BACKDROP_NAMES[job - 1], m.DIM)
    m.text(img, 176, 412, f"{SPEEDS[job - 1]} ROWS/S   10 LAYERS", m.DIM)
    m.ooe_mark(img, 600 - m.mark_w(16), 356, 16, m.BONE)
    return m.to444(img)


def pictures():
    art = ROOT / "art" / "backdrops"
    png = ROOT / "mockups" / "png"
    art.mkdir(parents=True, exist_ok=True)
    png.mkdir(parents=True, exist_ok=True)
    bgs = {}
    for i, (name, f) in enumerate(JOBS, 1):
        b = m.to444(f())
        bgs[name] = b
        b.save(art / f"job{i:02d}-{name}.png")
        print(f"art/backdrops/job{i:02d}-{name}.png")
    bgs["grid-horizon"].save(art / "title-grid-horizon.png")
    screens = {
        "title": m.scr_title(bgs["grid-horizon"]),
        "play": m.scr_play(bgs["gas-giant"], action=[("T-SPIN", m.AMBER), ("DOUBLE", m.BONE)]),
        "play-clear": m.scr_play(bgs["orbital-station"], active=("I", 0, 0, 0), flash_rows=(17, 18),
                                 action=[("QUAD", m.AMBER), ("B2B", m.ORANGE)]),
        "pause": m.scr_pause(bgs["moonbase"]),
        "gameover": m.scr_gameover(bgs["derelict"]),
        "settings": m.scr_settings(bgs["grid-horizon"]),
    }
    for k, s in screens.items():
        m.to444(s).save(png / f"screen-{k}.png")
        print(f"mockups/png/screen-{k}.png")
    job_card(bgs["shipyard"], 5).save(png / "screen-jobcard.png")
    print("mockups/png/screen-jobcard.png")


def effects():
    import bp_sfx
    out = ROOT / "audio" / "sfx"
    out.mkdir(parents=True, exist_ok=True)
    for name, f in bp_sfx.EFFECTS:
        u = bp_sfx.to_doc(f())
        bp_sfx.save_wav8(out / f"{name}.wav", u[:-1])
    print(f"audio/sfx/: {len(bp_sfx.EFFECTS)} effects")


def songs():
    import bp_album
    import sidtrack
    out = ROOT / "audio" / "songs"
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for s in bp_album.SONGS:
            stem = f"job{s.job:02d}-{s.title.lower().replace(' ', '-')}"
            wav = Path(tmp) / f"{stem}.wav"
            sidtrack.render(sidtrack.play(s), wav)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-b:a", "160k",
                            "-metadata", f"title={s.title}", "-metadata", "album=OOE Build Plate",
                            "-metadata", f"track={s.job}", str(out / f"{stem}.mp3")], check=True)
            print(f"audio/songs/{stem}.mp3")


if __name__ == "__main__":
    pictures()
    effects()
    if "--songs" in sys.argv[1:]:
        songs()
