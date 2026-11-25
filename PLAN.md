# One Off Stax — plan

The units of work, in order. Each is one branch in its own worktree, carried through the `sdlc` skill's phases
(see [CLAUDE.md](CLAUDE.md)), and merged by the owner before the next starts. "Done" is what the unit's
verification shows, not what was written. Where a unit says *measure*, record the number in the unit's PR or
commit message; where it says *ask*, stop and ask.

The spec is [spec.md](spec.md); where this plan and the spec disagree, the spec wins and the plan is fixed.

## B0 — Scaffold

- `Makefile` after `../../ooamp/Makefile`: `SIX ?= ../../6502` (a checkout of `feat/video-640` until it merges),
  OODOS and the emulator built into `build/` from `$(SIX)`'s sources and nothing written into `$(SIX)`; ca65 with
  OODOS's `include/` and `backplane.inc`; linked with `oolib.lib`; OODOS's 65C816 rules gate and `w1.py` over the
  image; ld65's warnings fatal; `make`, `make test`, `make webcard`, `make assets` (runs `tools/`).
- `src/stax.s`: checks `FT_INFO` for interface version 13 and the flags (spec, "Timing and the main loop"),
  prints one line with function 9 and ends with `JMP WBOOT`; prints why and exits on a failed check.
- `test/`: a `CcpRig` smoke test that runs it and reads the line; a negative test (FT_INFO patched to interface 12)
  that sees the refusal.
- **Done:** `make test` passes; the rules gate and `w1.py` run on the image and are seen to fail on a planted `SMB`
  and on a segment at `$4000`.

## B1 — Frame and input

- Event area (layout 2), `ES_NOQUEUE`, console mode, the `FT_WAIT` loop with catch-up, the held-action mask from
  `EV_KEYS` and controller 1, the queue drained, DAS/ARR; a debug line of held actions and the frame count.
- **Done:** a `CcpRig` test presses and holds keys through `UsbCard` and reads the expected masks, including a tap
  shorter than a frame.

## B2 — Video foundation

- `tools/mkuisheet.py`: the UI sheet, the sprite images, `src/sheet.inc` and the 4 KB font (`src/font.inc`), all
  drawn by `tools/ooe_mock640.py`'s code so the game and the mockups are one design. `STAX.OGX` by `mkasset.py`.
- `render/screen.s`: the two screens (16 KB aligned), the draw list, apply/flip/replay; the primitives: sheet copy
  by `DM_VCOPY`, `GX_FRECT`, `GX_TEXT`, the row shift by `GX_BCOPY`.
- Draw the play screen's static parts (header, panels, empty well, footer) over a plain backdrop.
- **Measure** a cell copy, a panel, a line of text, a full well shift.
- **Done:** a test reads the shown screen and matches the panels and well frame of `mockups/png/screen-play.png`
  exactly; the same test fails on a one-pixel change to the sheet.

## B3 — Engine core

- Pieces, board, fill counts, RNG and the 7-bag, collision. Decide how engine tests run (spec, "Engine tests").
- **Done:** the engine tests for pieces, bag/RNG and collision pass, and each is seen to fail on a planted fault.

## B4 — Movement

- Shifts, SRS rotation with the kick tables, gravity (the job table from `tools/gentables.py`), soft and hard drop,
  lock delay with the reset cap, hold.
- **Done:** their engine tests pass, with negative cases.

## B5 — Rules

- Line clears, BCD scoring with the 99,999,999 stop, T-spins, combo, B2B, jobs every 10 lines, overtime and its
  lock delay, block out and lock out. The replay test and its golden checksum.
- **Done:** the engine tests and the replay pass; the replay's checksum changes when one input frame changes.

## B6 — Play screen

- Sprites for the piece and the ghost; locked cells; HUD; HOLD and NEXT; the callout; the flash and the row shift;
  pause; game over's grey and LINE STOP. `STAX /T`.
- **Measure** the worst frame (hard drop, four-line clear, spawn) and the row shift's frames at job 10.
- **Done:** the game tests in spec.md ("Required") pass, except the job card's.

## B7 — Backdrops and jobs

- `tools/mkscreens.py`: `TITLE.SCR` and `BG01.SCR`–`BG10.SCR` from `art/backdrops/` (75% for play), by
  `mkasset.py direct640`'s conversion. Loading into the back screen; the job change and the job card as the spec
  orders them; the title screen.
- **Measure** a backdrop's load time.
- **Done:** a test plays through a job change and reads the card's band over the new backdrop, then the play screen
  over it on both screens.

## B8 — Music

- `tools/mksid.py` and `player/`: each song of `tools/stax_album.py` as a two-SID PSID with a 6502 play routine;
  `JOB01.SID`–`JOB10.SID`. Loading and playing them by the `.sid` library; pause, resume, volume, job changes.
- **Measure** the play routine's worst frame on the 6510 (about 17,000 cycles is the frame).
- **Done:** for all ten songs, every frame's SID registers from the play routine equal `sidtrack.play()`'s; one
  changed note in a song's data makes the test fail.

## B9 — Effects

- `tools/mkwaves.py`: `STAX.WAV` and `src/waves.inc` from `audio/sfx/`; the ES5503 claimed, loaded and played,
  one oscillator a kind, the priorities.
- **Done:** a test triggers each effect and reads its oscillator's registers; the game runs without the chip.

## B10 — Screens and files

- Title menu, settings and key remapping, `SETTINGS.DAT`, `HISCORE.DAT`, the countdown, quit and restart.
- **Done:** settings and the high score survive a restart in a test; a missing file is handled as the spec says.

## B11 — Acceptance

- The manual checks in spec.md, the card image (`make webcard`), the whole game played in the emulator's web UI.
- **Done:** every manual check ticked, with the owner.
