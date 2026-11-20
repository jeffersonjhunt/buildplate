# tools

The scripts that make every picture and sound in this repo, and (from unit B2 on) those the build adds. Python 3,
run as `python3 -I`; `pip install -r tools/requirements.txt` (Pillow, NumPy, pyresidfp). Everything is seeded, so a
run rebuilds the same bytes.

```
python3 -I tools/mkreference.py           # art/backdrops/, mockups/png/, audio/sfx/
python3 -I tools/mkreference.py --songs   # and audio/songs/ (needs ffmpeg)
```

| Script | Makes |
| --- | --- |
| `mkreference.py` | runs the others into the repo's folders; the job card |
| `ooe_mock640.py` | the design: palette, the 5×7 face, the OOE mark, the blocks (`block_cells`, 8×8 doubled), panels, every screen, five backdrops, `to444` (RGB444 with 4×4 ordered dither) |
| `ooe_mock.py` | the first draft at 320×240; still the source of the glyphs, piece shapes, noise and dither helpers that `ooe_mock640.py` imports |
| `bp_backdrops.py` | the other five backdrops (shipyard, ice planet, twin suns, neon city, black hole) |
| `sidtrack.py` | the two-SID tracker: `play(song)` returns every 1/60 s frame's SID register writes; `render()` plays them through two reSIDfp 8580s |
| `bp_album.py` | the ten songs, as data for `sidtrack.py` |
| `bp_music.py` | job 1's theme melody (`MEL_A`, `MEL_B`), which `bp_album.py` uses; also the first draft's tracker |
| `bp_sfx.py` | the sixteen effects as ES5503 samples |

To come, per [../PLAN.md](../PLAN.md): `gentables.py` (B4, the gravity table), `mkuisheet.py` (B2, the UI sheet,
font and sprite images), `mkscreens.py` (B7, the `.SCR` screens), `mksid.py` (B8, the PSID tunes) and `mkwaves.py`
(B9, `BUILDPLT.WAV`).

`sidtrack.play()` is the golden reference for the music: the 6502 play routine must produce the same SID
registers, frame for frame.
