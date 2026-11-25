# One Off Stax — specification

**One Off Stax** (`STAX.COM`, tagline STACK FAST) is a single-player falling-block puzzle game for the
**OO-1**: a W65C02S at 7.16 MHz running **OODOS**, a CP/M 3-style OS. It draws, plays sound, reads input and keeps
time only through **OOLIB**, OODOS's game services (BDOS functions 80–83 and the linked library `oolib.lib`), never
by touching that hardware itself. The play follows modern guideline mechanics: a 7-bag, SRS rotation, hold, a ghost
and lock delay. Ten jobs (levels) each have their own backdrop and their own song, faster every job, then an endless
overtime. The program ends with `JMP WBOOT`, which also hands every OOLIB resource back.

Written 2026-11-20 against the OO-1 repo (`jeffersonjhunt/6502`) at branch `feat/video-640` `8bf169f1`: OODOS 0.12,
OOLIB interface version 13, video card revision 2 with layer type 7 ("direct 640"). The plan is [PLAN.md](PLAN.md);
the screens are in [mockups/](mockups/); the art, audio and the scripts that make them are in [art/](art/),
[audio/](audio/) and [tools/](tools/).

**For the coding agent.** This is its own repo, `games/stax` beside the OO-1 repo, built against
`../../6502` the way OO-Amp (`../../ooamp`) is: read its Makefile before writing this one. In the OO-1 repo read
`AGENTS.md` first and follow it. Where this spec and the OO-1 repo's books disagree, the books win; where a book is
silent, trust the code. Your references are the OODOS Programmer's Guide (`docs/oodos-programmers-guide/`, chapter 8
for OOLIB, chapter 7 for each BDOS function), the OO-1 Technical Reference (`docs/oo1-technical-reference/`,
chapter 6 for video and 7 for sound) and `hw/video640.md`. Write 6502 assembly for ca65/ld65. Work through
[PLAN.md](PLAN.md)'s units in order, under the `sdlc` skill (see [CLAUDE.md](CLAUDE.md)). If you need something
OOLIB doesn't offer, stop and ask the owner rather than reaching for the hardware.

**Depends on OODOS 0.12.** Layer type 7, `GB_DIRECT` and `DM_VFILLW` are on the OO-1 repo's `feat/video-640`
branch, built in the emulator and not yet merged to `main`. Until they are, build against a checkout of that branch
(the Makefile's `SIX` variable), and require interface version 13 at startup.

## Goals

- Responsive guideline play locked to the video frame (59.94 Hz), one logic step a frame.
- A deterministic engine: the same seed and the same per-frame input give the same game.
- Engine code that calls no BDOS function and touches no hardware, so it can be tested on its own.
- The look of the mockups, pixel for pixel, and the sound of the reference renders.

## Non-goals (v1)

- Multiplayer, networking, USB gamepads (controller 4 isn't supported by OODOS yet), a 40-line sprint mode.
- Do **not** use the trademarked name "Tetris", its logo, or official music or art. Every tile, picture, sound and
  tune is original, made by the scripts in [tools/](tools/).

## Rules the OO-1 repo enforces

- **Calling the BDOS:** `JSR BDOS` (`$0203`), the function number in Y, a byte in A, a word in A (low) and X (high),
  results in A or A/X. Y isn't kept and the flags come back as they were before the call, so test A. Use
  `oodos.inc`'s names, never bare numbers.
- **Program shape:** a `.COM` starting with `OODOS_HEADER`, loaded and run at `$0300`. Its zero page is `$00–$EF`;
  `$F0–$FF` belongs to RSXs.
- **65C816 rules** (`oodos/tools/rules.py`, which fails the build): no `RMB`, `SMB`, `BBR` or `BBS`; zero-page
  variables only through zero-page operands, never by absolute address or a 16-bit pointer to them; the stack only
  through stack instructions (no `TSX` then `LDA $0103,X`); the BDOS only through `$0203`.
- **The W1 contract** (`oodos/tools/w1.py`): while OOLIB's graphics library is linked, no code, data or BSS may sit
  in `$4000–$7FFF`. Usable memory is `$0300–$3FFF` (15.6 KB) and `$8000–$BFFC` (16 KB).
- **What OODOS owns** and the game leaves alone: interrupts and vectors, the DMA channels, the north bridge's windows,
  the sound card's 6510 (except through function 82 and the `.sid` library), the VIA's ACR, IER, IFR and timer 1, and
  every video register (OOLIB writes them).
- **ld65's warnings are fatal**, as in OO-Amp's and OODOS's builds.
- **No Digital Research text or code** anywhere in the program or its comments.

## Deliverables

| What | Made by | Notes |
| --- | --- | --- |
| `STAX.COM` | ca65/ld65, linked with `oolib.lib` | through OODOS's rules gate and `w1.py`, as OO-Amp's Makefile does |
| `STAX.OGX` | `mkasset.py direct640` + `sprites` + `combine` | the UI sheet (blocks, frame corners, logo, title name, stamps) and the sprite images |
| `src/font.inc`, `src/sheet.inc` | `tools/mkuisheet.py` | the game's face as a 4 KB `GX_FONT` font, and the sheet's coordinates |
| `TITLE.OGX`, `BG01.OGX` … `BG10.OGX` | `mkasset.py direct640` | one 640×480 picture each: the title's, and each job's at play brightness |
| `JOB01.SID` … `JOB10.SID` | `tools/mksid.py` + a 6502 play routine | two-SID PSID tunes, one per job |
| `STAX.WAV` | `tools/mkwaves.py` | the sixteen effects laid out for the ES5503's wave RAM, with their table |
| `HISCORE.DAT`, `SETTINGS.DAT` | the game | one 128-byte record each; absent means defaults |
| a card image | `make webcard`, as OO-Amp's | every file above on one drive, for the emulator's web UI |

## Game rules

The rules are normative: where this section and another disagree, this one wins.

### Board

- Playfield is 10 columns × 40 rows. Rows 0–19 are visible; rows 20–39 are a hidden buffer above.
- Coordinates: `x` 0–9 left to right, `y` 0 at the **bottom**, increasing upward. Rendering flips y.
- Each cell is empty or holds a piece type (for color).

### Pieces

Seven tetrominoes, each defined by 4 cell offsets per rotation state (0, R, 2, L) in a 4×4 box (3×3 for J, L, S, T, Z). Use the standard SRS shapes and spawn orientations.

| Piece | Base (RGB444) | Light | Dark | Spawn orientation |
| --- | --- | --- | --- | --- |
| I | `$2CD` | `$8EF` | `$177` | Flat, horizontal |
| O | `$FA0` | `$FE8` | `$950` | 2×2 |
| T | `$A4E` | `$D9F` | `$517` | Flat side down, point up |
| S | `$4C4` | `$AF9` | `$162` | Flat |
| Z | `$F42` | `$F98` | `$821` | Flat |
| J | `$46F` | `$ABF` | `$128` | Flat, nub top-left |
| L | `$C50` | `$FA6` | `$620` | Flat, nub top-right |

- Spawn: piece box centered horizontally (I and O at columns 3–6, others at columns 3–5), bottom of the piece on row 20 (just above the visible field). Immediately attempt to drop one row if the space is free.

### Randomizer

- 7-bag: shuffle all 7 pieces (Fisher–Yates), deal them in order, refill when empty. Pick each index with rejection sampling from PRNG bytes so there is no modulo bias.
- PRNG: 16-bit xorshift (state must never be 0). Seed it from the event area's frame counter (`EV_FRAMES`) at the moment the player presses Start (force nonzero). After seeding, logic never reads hardware for randomness.
- Show the next 5 pieces in a preview queue.

### Movement and rotation

- Left / right shift one column if all target cells are empty and in bounds.
- Rotation uses the **Super Rotation System (SRS)** with the standard wall-kick tables: one table for J, L, S, T, Z and a separate table for I. O does not rotate (or rotates in place with no kicks).
- On rotate, try the 5 kick offsets in order; take the first that fits. If none fit, rotation fails silently.
- Include clockwise, counter-clockwise, and 180° rotation (180° uses no kicks in v1, just a fit test).
- The agent must encode the SRS kick tables as data constants and unit-test each entry.

### Gravity and dropping

- All timing is counted in video frames, fixed at **59.94 Hz**; `FRAME_HZ` is 60 for table generation.
- Gravity uses an **8.16 fixed-point** rows-per-frame accumulator (3 bytes): add the job's speed every frame; move down one row per whole unit carried. This handles both slow jobs and jobs faster than 1 row per frame.
- Speeds are 10 points taken from the guideline curve (seconds per row = `(0.8 - (L - 1) × 0.007) ^ (L - 1)` at guideline level L), so every job is clearly faster than the last. Generate the table with `tools/gentables.py`; never type it by hand.

  | Job | Guideline level | Frames per row | Rows per second |
  | --- | --- | --- | --- |
  | 1 | 1 | 60 | 1.0 |
  | 2 | 2 | 47.6 | 1.3 |
  | 3 | 3 | 37.1 | 1.6 |
  | 4 | 4 | 28.4 | 2.1 |
  | 5 | 6 | 15.7 | 3.8 |
  | 6 | 8 | 8.1 | 7.4 |
  | 7 | 10 | 3.9 | 15 |
  | 8 | 12 | 1.7 | 35 |
  | 9 | 14 | 0.68 | 88 |
  | 10 and overtime | 15 | 0.42 | 143 |
- Soft drop: 20× current gravity, but no slower than gravity and capped at 1 row per frame unless gravity is already faster. Awards 1 point per row.
- Hard drop: piece moves instantly to the lowest valid position and locks immediately. Awards 2 points per row.
- Ghost piece: show where the piece would land on hard drop.

### Locking

- When the piece cannot move down, start a lock delay of `LOCK_FRAMES` = 30 frames (0.5 s).
- Successful move or rotation resets the lock timer ("move reset"), up to **15 resets per piece**. After 15, the next ground contact locks without delay. The reset counter clears only when the piece reaches a new lowest row.
- On lock: write the 4 cells into the board, clear lines, score, spawn the next piece.

### Hold

- Hold key swaps the active piece with the held piece (or with the next queue piece if hold is empty).
- Held piece returns in spawn orientation. Hold can be used once per piece; it re-enables on lock.

### Line clears

- After lock, remove every full row and shift rows above downward. The 6-frame flash is the renderer's; game logic never waits for it.

### Scoring

Base points are multiplied by the current job number (the job before the clear; in overtime 11, 12, …).

| Action | Points |
| --- | --- |
| Single | 100 × job |
| Double | 300 × job |
| Triple | 500 × job |
| Four lines | 800 × job |
| T-spin (no lines) | 400 × job |
| T-spin single | 800 × job |
| T-spin double | 1200 × job |
| T-spin triple | 1600 × job |
| Back-to-back bonus | × 1.5 on a four-line or T-spin line clear that follows another such clear |
| Combo | 50 × combo count × job (combo counts consecutive locks that clear lines, starting at 0) |
| Perfect clear (board empty after clear) | Optional in v1 |
| Soft drop | 1 per row |
| Hard drop | 2 per row |

**6502 implementation:** keep score as 4-byte packed BCD (8 digits) and lines as 2-byte BCD so the HUD needs no binary-to-decimal conversion. Multiply by the job with repeated BCD addition; the multiplier stops at 99 (the job number shown keeps counting). Store back-to-back values (four-line 1200, T-spin single 1200, double 1800, triple 2400) in their own BCD table instead of computing × 1.5. Bracket BCD math with `SED`/`CLD`, and never call the BDOS or the library inside it.

**Score ceiling:** points with no line clear (zero-line T-spins, drop points) are unbounded, so only the 99,999,999 cap limits the score. For reference, line clears alone at the moment the 100th line clears (end of job 10, started at job 1): about 660,000 in theory (every clear a back-to-back T-spin single), about 165,000 for back-to-back four-line clears every time, and 50,000–80,000 for good play, plus combos and drop points.

**T-spin detection (3-corner rule):** the last successful action was a rotation of a T piece, and at least 3 of the 4 diagonal corners of the T's 3×3 box are occupied (walls and floor count as occupied). Mini T-spins are out of scope for v1.

### Jobs (levels)

- Levels are **JOBs 1–10**, each with its own backdrop and its own song. Start at job 1 (selectable 1–10 on the title screen).
- The next job starts every **10 lines** (tunable constant `LINES_PER_JOB`, in case it feels rushed).
- **Overtime** after job 10: the game never ends on its own. Speed, backdrop and song stay at job 10's; the job number keeps counting (11, 12, …) and keeps raising the score multiplier; and every 10 lines the lock delay shrinks by 2 frames, from 30 down to a floor of 12.
- The score is 8 BCD digits and **stops at 99,999,999**; it never rolls over. Lines (LAYERS) stop at 9,999.

### Game over

- **Block out:** a newly spawned piece overlaps existing blocks.
- **Lock out:** a piece locks entirely above the visible field (all cells at y ≥ 20).

## Controls and input

Input comes from OOLIB's **event area** (layout 2, BDOS function 80's `FT_OPEN` with a 256-byte area). OODOS keeps a bitmap of every key held (`EV_KEYS`, one bit per USB HID usage), a queue of key presses and releases, and four controllers, all updated from its interrupts. The game reads them with plain loads once a frame, so held keys, releases, DAS and ARR all work exactly. Do not read the keyboard with BDOS function 6 during play: the console's cooked keys would arrive as well and every key would be seen twice.

| Action | Keyboard default (HID usage) | Joystick (controller 1) |
| --- | --- | --- |
| Move left | ← (`$50`) | `CB_LEFT` |
| Move right | → (`$4F`) | `CB_RIGHT` |
| Soft drop | ↓ (`$51`) | `CB_DOWN` |
| Hard drop | Space (`$2C`) | `CB_UP` |
| Rotate clockwise | ↑ (`$52`), X (`$1B`) | `CB_FIRE` |
| Rotate counter-clockwise | Z (`$1D`) | — |
| Rotate 180° | A (`$04`) | — |
| Hold | C (`$06`), Left Shift (`$E1`) | — |
| Pause / resume | Esc (`$29`), P (`$13`) | — |
| Restart (from pause or game over) | R (`$15`) | — |
| Quit to OODOS (from title, pause or game over) | Q (`$14`) | — |

### Reading input (`input.s`)

- Once a frame, build a 2-byte **held-action mask** from `EV_KEYS` (usage *u* is bit *u* AND 7 of byte `EV_KEYS + u/8`) OR'd with controller 1's `EC_BITS` (`EV_CTL` + 0). Edge-detect against last frame's mask for rotate, hard drop, hold and pause.
- Drain the event queue every frame (`EV_QTAIL` up to `EV_QHEAD`): key presses that came and went within one frame are still seen there, so a quick tap of rotate is never lost. Also hand every `EK_SOUND` event to the sound module (see Sound).
- **DAS:** `DAS_FRAMES` = 10 (167 ms) before auto-repeat. **ARR:** `ARR_FRAMES` = 2; 0 means jump to the wall. Both adjustable in settings (DAS 3–18, ARR 0–6 frames).
- When left and right are both held, the most recently pressed one wins. DAS charge carries across piece spawns.
- A key held when the area was opened isn't in `EV_KEYS` until it is released and pressed again; that's fine at the title screen.
- Key remapping in settings stores HID usages, not ASCII.

### Console mode

- At startup, read the console mode with BDOS function 109 (`C_MODE`, A/X = `$FFFF`), then set it with bits 3 and 1 (`$000A`) added so ^C doesn't end the game and ^S doesn't freeze it. Restore the saved mode before every exit. Break (Pause key) still stops any program; that is OODOS's and is fine.
- Text entry outside play (none in v1) would use the event queue too, not function 6.

## Architecture

Three layers with one-way dependencies: **platform → engine → render**. The engine is pure 6502 code that touches
only its own RAM and zero page and makes no BDOS or library call, so it can be tested alone. Only `platform/` and
`render/` call the BDOS or OOLIB.

### Repo layout

```
CLAUDE.md, README.md     how to work here; what this is
spec.md, PLAN.md         this spec; the units of work
Makefile                 (unit B0) after ../../ooamp/Makefile: SIX ?= ../../6502
cfg/                     (B0) the ld65 config(s)
src/
  stax.s             entry, init, main loop, clean exit
  game.inc               constants, state offsets, sprite and sheet coordinates
  platform/frame.s       event area, FT_WAIT, catch-up
  platform/input.s       EV_KEYS + controller 1 -> held mask, queue drain, DAS/ARR
  platform/sound.s       JOBnn.SID by the .sid library, ES5503 effects
  platform/files.s       STAX.OGX, the .SCR screens, the .SID and .WAV files, HISCORE/SETTINGS
  engine/pieces.s        shape tables
  engine/srs.s           kick tables + rotate
  engine/rng.s           xorshift16 + 7-bag
  engine/board.s         collision, place, line clear
  engine/score.s         BCD score, combo, B2B, T-spin
  engine/game.s          game_step: one frame of logic
  render/screen.s        the two buffers, the draw list, the flip
  render/draw.s          cells, panels, text, the well's row shift, sprites, screens
player/                  (B8) the 6502 PSID play routine, assembled into each JOBnn.SID
mockups/                 the screens, pixel exact; mockups/README.md indexes them
art/                     source pictures: the ten backdrops and the title
audio/                   reference renders: the ten songs (MP3) and the sixteen effects (WAV)
tools/                   the scripts that made every picture and sound, and those the build adds
test/                    engine tests and the CcpRig game tests
reference/               the owner's answers and pointers into the OO-1 repo
```

### Memory: the 6502 side

The whole image plus BSS fits in `$0300–$3FFF` (15.6 KB) with OODOS's stock `com.cfg`. If it grows past that, add
a second memory area at `$8000–$BFFC` in this repo's cfg; nothing may land in `$4000–$7FFF`, buffers included.

| Item | Size | Notes |
| --- | --- | --- |
| Zero page | ≤ 32 bytes of the program's own | plus the library's (`GXP`/`GXQ`/`GXT` 6, `SID_ZP` 2, and whatever else the linked modules bring); all in `$00–$EF` |
| Event area | 256 bytes | layout 2, page-aligned; must not cross a 16 KB window boundary |
| Board | 640 bytes | 40 rows × 16-byte stride (10 used + 6 pad), `index = y × 16 + x`; 0 empty, 1–7 the piece type |
| Row fill counts | 40 bytes | cells filled a row; a row is full at 10, so line checks never scan cells |
| Piece tables | 224 bytes | 7 pieces × 4 rotations × 4 (dx, dy), signed bytes |
| SRS kick tables | 160 bytes | 2 tables × 8 transitions × 5 tests × (dx, dy) |
| Game state | ~64 bytes | below |
| Draw list | ≤ 1 KB | the frame's draw operations, replayed on the other buffer (see Video) |
| Font | 4 KB | `GX_FONT`'s 256 × 8×16 characters: the game's face as glyph halves (see Text) |
| SID tune buffer | the largest tune | read before `SID_PLAY` sends it to the card; reused |
| Staging | 4 KB | `GX_STAGE`, physical `$BF000` (bank B) by default, not in the TPA |

### Game state fields

| Field | Bytes | Meaning |
| --- | --- | --- |
| `act_type`, `act_rot`, `act_x`, `act_y` | 4 | active piece (x, y signed; y up from the bottom) |
| `lock_timer`, `lock_resets`, `lowest_y` | 3 | lock delay; `lock_timer` `$FF` when not grounded |
| `last_was_rot`, `last_kick` | 2 | T-spin detection |
| `grav_accum` | 3 | 8.16 fixed point |
| `hold`, `hold_used` | 2 | `hold` 0 when empty |
| `queue[6]`, `bag[7]`, `bag_left` | 14 | next pieces and the current bag |
| `rng` | 2 | xorshift16 |
| `score` (BCD 4), `lines` (BCD 2), `job` (BCD 1), `lock_frames` | 8 | job counts on past 10 in overtime |
| `combo`, `b2b` | 2 | `combo` `$FF` means none |
| `status` | 1 | title / jobcard / countdown / playing / paused / over |
| `events` | 2 | flags `game_step` sets this frame: lock, clear count, T-spin, B2B, new job, game over, hold, hard drop |

### Engine API

- `game_init`: A the start job, `rng` seeded. Clears the board, fills the bag and the queue.
- `game_step`: the held-action and pressed-this-frame masks in zero page. Runs one frame: input, then gravity, then
  lock delay. Sets `events` and marks dirty rows.
- Render and sound read `events` and the state fields above, nothing else of the engine's.

### Timing and the main loop

- The game installs **no interrupt handler** and touches no interrupt register. Time is the event area's frame
  counter.
- **Startup:** `FT_INFO` (function 80, X = 0): interface version **13 or higher** with `OA_FRAME`, `OA_INPUT`,
  `OA_SOUND` and `OA_DMA` set, and a revision 2 video card; otherwise print why with function 9 and exit. Open the
  256-byte event area (`FT_OPEN`), set `ES_NOQUEUE`, set the console mode, `GX_INIT` with the area, allocate the two
  screens, load `STAX.OGX`, start the title.
- **Main loop:** apply the frame's draw list to the back buffer → `GX_FLIP` if anything was drawn, else `FT_WAIT`
  (either way the loop runs once a vertical blank) → `GX_SPRSHOW` → read input → `game_step` → effects → replay last
  frame's list on the new back buffer. Compare `EV_FRAMES`' low byte with the last frame handled; if frames were
  missed, run `game_step` again with the same input, up to 3 catch-up steps, so the speed stays tied to real time.
- **Frame budget:** about 119,400 cycles, less OODOS's interrupts (~412 a frame for a layout-2 area, more with the
  vertical-blank copies). `game_step`'s worst case under 25,000. Drawing takes what is left; work that doesn't fit is
  carried to the next frame, in order (see the draw list).
- No frame or tick hooks in v1. If one is ever added it keeps chapter 8's hook rules.
- **Exit** (Quit, a fatal error, a failed check): `SID_STOP`, stop and `SN_RELEASE` the ES5503, restore the console
  mode, `FT_CLOSE`, `JMP WBOOT`. The warm boot also restores the console video, frees the vertical-blank slots and
  releases every sound part, so a crash still leaves a usable console.

### State flow

`title` → `jobcard` (2 s) → `countdown` (3 s) → `playing` ⇄ `paused`; `playing` → `jobcard` at each new job up to
10; `playing` → `over` on block out or lock out; `over` or `paused` → `title` on Restart; Quit from `title`,
`paused` or `over` exits to OODOS.

## Video

The screen is **one direct 640 layer, double-buffered**: layer 0 of type 7 (`GB_DIRECT`), 640×480, a `$0RGB` word a
pixel, no palette, shown from one of two screens in card memory and swapped by `GX_FLIP` at the vertical blank. Layer
1 is off. The falling piece and its ghost are **sprites**, so a move or a rotation changes only the sprite table,
never a screen. All drawing goes through OOLIB and function 83; the game writes no video register.

### What the card gives (OO-1 Technical Reference chapter 6, `hw/video640.md`)

- **Direct 640:** a pixel is a little-endian word `$0RGB`, byte 0 `GGGGBBBB`, byte 1 `0000RRRR`, the palette entry's
  layout. `$8000` (bit 15) is transparent, `$0000` opaque black; bits 12–14 are written 0. Rows are packed, 1,280
  bytes; a screen is 614,400 bytes, 2,400 card pages.
- **Card memory:** the program's part is 6,144 pages (1.5 MB). Take each screen on 16 KB (an alignment of 64 pages).
  A direct 640 row straddles a 16 KB slot at rows 12, 25, 38 and 51 of every 64: the library maps each pixel by its
  own address, but code that writes along a row through `GX_VMAP`'s window maps the next page itself.
- **Sprites** keep their 320×240 grid, each sprite pixel shown 2×2, and their colours are palette indices
  (`GX_PALINIT` gives them a palette). 64 entries, 32 a line, 8/16/32/64 pixels, 4 or 8 bits, depth 1–3. Over a
  direct 640 layer 0, depth 2 and 3 draw in front; use depth 3.
- **Costs, measured on the branch:** a whole direct 640 screen filled by `GX_FRECT` 0.116 s; `GX_PLOT` 498 cycles; a
  600 KB part loaded by `GX_ASSET` 0.67 s.

### Card memory plan

| What | Pages | Notes |
| --- | --- | --- |
| Screen A | 2,400 | `GX_VALLOC`, 16 KB aligned |
| Screen B | 2,400 | the same |
| UI sheet | ≤ 900 | `STAX.OGX`'s direct 640 part: 640 wide, ≤ 180 rows |
| Sprite images | 16 | eight 8×8 4-bit images, 256 bytes each as `mkasset.py` pads them |
| Palette, sprite table | 4 | `GX_PALINIT`, `GX_SPRINIT` |
| Free | ≥ 420 | of 6,144 |

There's no room for a third screen, so a backdrop is loaded straight into the screen that isn't showing (see Jobs).

### The double buffer and the draw list

Every change to the picture is a **draw operation** appended to the frame's list: copy a cell or a glyph from the
sheet, fill a rectangle, draw text, shift the well's rows, load a screen. Each frame the loop applies the new list
to the back buffer, flips, then replays the same list on the other buffer (now the back) before the next frame's
operations, so both screens always converge to the same picture. Operations are never reordered or dropped; a list
too long for the frame continues in the next, in order, and the flip waits until a frame's list is fully applied, so
a half-drawn frame is never shown. Frames with no operations skip the flip and wait with `FT_WAIT`.

### Drawing primitives

- **Cells and pieces of the sheet:** `GX_BCOPY` copies only within one bitmap, so copy from the sheet with function
  83's card-to-card copy (`DM_VCOPY`), a row a call, as `GX_BCOPY` does inside the library: a 16×16 cell is 16 copies
  of 32 bytes. Check whether `DM_VCOPY` takes a source and destination step; if it does, a cell is one call.
- **Fills:** `GX_FRECT` with a word colour (`DM_VFILLW`, or `DM_VFILL` when both bytes are equal).
- **Text:** the game's face is a 5×7 design drawn 2× in a 16×16 cell. Make it a `GX_FONT` font of 8×16 characters,
  each glyph as two characters (its left and right halves), and draw with `GX_TEXT` in a word colour (`GX_FGH:GX_FG`)
  over a transparent background. The 2× title name and the stamps are pictures on the sheet, not text.
- **The well's rows** after a line clear: one `GX_BCOPY` of the well above the cleared rows, down by 16 × n pixels.
  The library copies rows overlapping downward from the last, so it moves correctly. Then copy the empty-row strip
  into the top n rows.
- **Measure** each primitive in the emulator in unit B2 and record the cycles in `hw/` notes or the PR: the plan
  above assumes a 16-copy cell is a few thousand cycles and a full well shift fits in the 6-frame flash.

### The UI sheet (`STAX.OGX`)

One direct 640 PNG, `art/ui-sheet.png`, drawn by `tools/mkuisheet.py` from the mockup generator's code (unit B2), at
most 640×180, then `mkasset.py direct640`, plus the sprite images by `mkasset.py sprites`, joined by `combine`. It
holds, at coordinates `tools/mkuisheet.py` also writes to `src/sheet.inc`:

- the seven block cells, a grey block, the flash cell, the empty well cell and the hidden-sliver cell, 16×16 each;
- the empty well row (160×16) for clears and pause;
- the panels' rounded corners (8×8, the four of each colour used);
- the OOE mark at its two sizes (40 and 16 px tall), ONE OFF at 3×, STAX at 8× with its shadow, ONE OFF STAX at 2× for
  the header, and the two stamps (STACK FAST, NEW HI SHIFT).

### Blocks and sprites

- A block is an **8×8 design shown doubled** (`block_cells()` in `tools/ooe_mock640.py`): light edge top-left, dark
  edge bottom-right, an upper and a lower face, a white glint. Locked blocks are the same design copied from the
  sheet, so a piece looks the same falling and locked.
- Sprites 0–3: the active piece, an 8×8 4-bit image, depth 3, palette group of its piece (colours 1 light, 2 upper
  face, 3 lower face, 4 dark, 5 white). Sprites 4–7: the ghost, the dotted-edge image, same group. A screen pixel
  (x, y) is sprite position (x / 2, y / 2): a cell at well column c, visible row r is at (120 + 8c, 48 + 8r).
- `GX_SPRPOS`/`GX_SPRATTR` into the shadow table, `GX_SPRSHOW` once a frame. Hide with depth 0. No `GX_COLL`.

### Screen layout (pixels; a cell is 16×16, the grid 40×30)

| Part | Where | Contents |
| --- | --- | --- |
| Header | y 0–31 | OOE mark, ONE OFF STAX, HI and the high score |
| Well | frame (224,64)–(415,431); playfield (240,96)–(399,415); sliver y 80–95 | 10 × 20 cells; the sliver shows the hidden row just above |
| HOLD | (32,80)–(207,159) | the held piece |
| SHIFT | (32,176)–(207,367) | OUTPUT (score), JOB, LAYERS (lines) |
| Callout | (32,384)–(207,431) | action text, only while it shows |
| NEXT | (432,80)–(607,351) | five pieces in 64×32 slots from y 96, 48 apart |
| Footer | y 448–479 | key hints |
| Backdrop | everywhere else | the job's picture |

Colours (RGB444): panel `$111`, well `$211`, grid dot `$322`, frame line `$443`, label `$998`, text `$EDD`, accent
`$C50`, value `$FA0`, alert `$F42`, flash `$FFF`. The pieces are in Game rules. [mockups/](mockups/) has every screen
pixel for pixel, with its coordinates and colours.

### Drawing rules

- On lock: the piece's 4 cells. On line clear: the flash (the cleared rows filled `$FFF`) for 6 frames, then the row
  shift. Logic never waits for either.
- HUD: redraw OUTPUT, JOB and LAYERS only when `events` says they changed; BCD nibbles map straight to glyphs.
- Callout ("TRIPLE", "T-SPIN DOUBLE", "QUAD B2B", "COMBO 3") cleared after 60 frames.
- Pause: the well filled with empty rows, HOLD and NEXT cleared, sprites 0–7 hidden (no pause-scumming); all
  redrawn on resume after the countdown.
- Game over: the stack turns grey a row every 2 frames from the bottom (grey cells from the sheet), then the LINE
  STOP box.

### Screens

| Screen | Contents |
| --- | --- |
| Title | `TITLE.SCR` (the grid horizon at full brightness), the title plate: OOE mark, ONE OFF, STAX, the STACK FAST stamp; menu START JOB, JOB 01–10, SETTINGS, QUIT; HI SHIFT |
| Job card | the job's backdrop with a band (y 340–431): JOB and its number, the song's title, the backdrop's name, the speed; 120 frames, any key skips |
| Countdown | 3-2-1 over the well, 60 frames each; also after resume |
| Pause (LINE HOLD) | as Drawing rules; RESUME, RESTART, SETTINGS, QUIT |
| Game over (LINE STOP) | box (212,148)–(427,340): OUTPUT, JOB, LAYERS, NEW HI SHIFT if earned; R restart, Q quit |
| Settings | DAS, ARR, ghost, music, music volume, effects, backdrops on/off, keys; saved to `SETTINGS.DAT` |

### Art direction

- **The name:** One Off Stax. STAX is said "stacks"; ONE OFF is the maker's name, the same as the OO-1's. The title
  sets ONE OFF small over a big amber STAX; the header spells it out at text size.
- **OOE brand:** the OOE mark (two rounded-square Os and three bars) from the logo; colours
  from the OOE site, rounded to 12 bits; the red rubber stamp from the boot splash's VINTAGE FAST, used only for the
  tagline and NEW HI SHIFT.
- **Mid-80s:** one monoline face with cut corners, all caps; thin rounded 1-pixel frames with the label cut into the
  top edge; 4×4 ordered dither instead of smooth gradients; nothing anti-aliased.
- **Shop-floor words:** SHIFT, OUTPUT, JOB, LAYERS, LINE HOLD, LINE STOP, HI SHIFT.

## Jobs: backdrops and songs

Each job has its own backdrop and song; overtime keeps job 10's.

| Job | Song | Style | BPM | Key | Backdrop |
| --- | --- | --- | --- | --- | --- |
| 1 | First Shift | bright synthpop: octave bass, bell arpeggios, echoing lead | 116 | A minor | Moonbase |
| 2 | Warm-Up | filtered French house: pumping chord loop under a sweeping filter | 120 | D minor | Gas giant |
| 3 | Conveyor | industrial synthpop: 16th sequencer bass, metal percussion, brass stabs | 122 | E minor | Orbital station |
| 4 | Night Shift | melancholic synth drive: pulsing bass, slow pads, glassy bells | 124 | C minor | Ice planet aurora |
| 5 | Overclock | robot rock: hard-sync riff, filter "vocoder" call and response | 126 | G minor | Orbital shipyard |
| 6 | Hot Bed | disco house: octave-bounce bass, pumping stabs, twin arpeggio solo | 128 | F♯ minor | Twin-sun desert |
| 7 | Toolpath | dark digital epic: 16th saw arpeggio, resonant sweep, power stabs | 132 | B minor | Derelict freighter |
| 8 | Spindle Speed | swung bluesy stomp: claps, pentatonic riff, gritty sync lead | 136 | C♯ minor | Neon city |
| 9 | Thermal Runaway | acid house: squelching resonant bass with slides and accents, risers | 142 | E♭ minor | Grid horizon |
| 10 | Max Feed Rate | anthem finale: racing arpeggios, soaring lead, key change at the end | 150 | F minor | Black hole |

### Backdrops

- Masters are `art/backdrops/*.png`, 640×480 RGB444 with 4×4 ordered dither, drawn by `tools/ooe_mock640.py` and
  `tools/stax_backdrops.py` (seeded, so they rebuild the same). The build (`tools/mkscreens.py`, unit B7) writes each
  job's at play brightness (75%) as `BGnn.SCR`, and the grid horizon at full brightness as `TITLE.SCR`.
- A `.SCR` file is a raw screen: 614,400 bytes, the card's words in order, no header, so it loads straight into a
  screen's pages: `DM_LOAD` into the staging area and `DM_VWRITE` to the screen, piece by piece, as `GX_ASSET` does.
  Use `mkasset.py direct640`'s pixel conversion for it (or its part's bytes), so there is one conversion.
- **Job change:** the last line of a job clears; gravity stops. Load the new `BGnn.SCR` into the back screen (about
  0.7 s; the old picture stays up), copy it to the other screen with `DM_VCOPY`, draw the job card's band on the
  back screen and flip to it. Start the new song. During the card, draw the play screen (panels, well, HUD,
  previews) on the other screen; when the card ends, flip to it and copy it back over the card's screen, so both
  are the play screen again. Then the countdown.
- Ten `.SCR` files and the title's are about 6.6 MB on the drive.

### Songs

- `JOB01.SID` … `JOB10.SID`: two-SID PSID tunes (SID B at `$D420`), NTSC, a play call each 1/60 s. The song data
  is `tools/stax_album.py`, played by `tools/sidtrack.py`, a two-SID tracker whose `play(song)` returns every frame's
  register writes; the renders in [audio/songs/](audio/songs/) are those writes through two reSIDfp 8580s.
- Unit B8 writes the real thing: `tools/mksid.py` turns a song into a compact data block, and `player/` a 6502 play
  routine for the card's 6510 that turns the block back into the same register writes. The test: run each PSID's
  play routine for its whole length (in the emulator's 6510 and SIDs, or a 6502 simulator with a SID register
  trap) and compare each frame's resulting SID registers with `sidtrack.play()`'s. They must match frame for frame.
- The tracker's techniques, all of which the play routine must reproduce: hard restart; hard sync and ring
  modulation against a silent partner voice; a per-note resonant filter envelope with slides and accents (acid); a
  filter "vocoder" (band-pass cutoff stepped a note); per-section filter ramps and LFOs; volume pumping on the beat;
  chord arpeggios at 1 or 2 frames a tone, or a tone a 16th; vibrato; pulse-width modulation; swing; echo voices;
  and drum kits as per-frame waveform and pitch recipes.
- The play routine runs on the card's 6510 at about 1 MHz: about 17,000 cycles a frame. Precompute what can be
  (frequency tables, LFO tables, envelope tables) in `mksid.py`, and measure the worst frame.
- The chips' model is a jumper on the card. The renders assume 8580s; on 6581s the filter sounds different.

## Sound

OODOS splits the sound card into parts a program claims with function 82: the **6510 and SIDs** (`SC_6510`), the
**stream** (`SC_STREAM`) and the **ES5503** (`SC_DOC`). The game uses the first for music and the third for effects.

- **Music:** read `JOBnn.SID` into a buffer, then `SID_PARSE`, `SID_PLAN`, `SID_PLAY` (library module `sid.s`;
  `SID_PLAY` claims the 6510 itself). The 6510 plays it with no CPU time from the game. Call `PB_BEGIN` with
  `PB_SID` after it starts. A new job: `SID_STOP`, then the next tune.
- **Mailbox flood:** a SID player sends a mailbox byte a play call, which would fill the event queue and lose keys.
  Right after `FT_OPEN`, set `ES_NOQUEUE` in `EV_SFLAGS` (+115).
- **Pause, resume, volume:** `PB_PAUSE`, `PB_RESUME` (the 6510 held where it is), `PB_VOLUME` for the setting.
  `SID_STOP` on game over and exit.
- **Effects on the ES5503.** OOLIB has no effects player: the game owns the chip and writes its oscillators from the
  main CPU.
  1. **Claim** with `SN_CLAIM` and `SC_DOC`. Refused without a revision 2 sound card or while another program or
     RSX holds it: then run without effects.
  2. **Load** `STAX.WAV` once with `SN_WAVE` (8-bit samples by DMA into the 128 KB wave RAM). `tools/mkwaves.py`
     (unit B9) lays the sixteen samples out in the power-of-two tables the chip reads, on matching boundaries (check
     Technical Reference chapter 7, "Revision 2", for the rule), and writes `src/waves.inc`: each effect's address,
     table size, frequency and volume.
  3. **Play** an effect by writing one oscillator's registers through `DOCCTL`, `DOCDATA`, `DOCADDR` and `DOCBANK`:
     wave address and table size, frequency, volume, then its control register in **one-shot** mode, so it stops at
     the sample's end.
  4. **Release** with `SN_RELEASE` on exit.
- **Effects:** move, rotate, hold, hard drop, lock, single, double, triple, quad, T-spin, new job, line stop, count,
  go, menu move, menu select ([audio/sfx/](audio/sfx/), made by `tools/stax_sfx.py`: 8-bit unsigned at 20,000 Hz,
  every byte 1–255, since a 0 byte halts an oscillator; 112 KB in all). The countdown is "count" three times and
  "go". Each kind has its own oscillator (the chip has 32) so effects never cut each other off. At most one new
  effect a frame, from the main loop, highest priority first: line stop > quad/T-spin > new job > clears > lock >
  hard drop > rotate > hold > move.
- **Don'ts:** no `SN_DOCHOOK` in v1; don't program the 6510 for effects; don't use the stream (it can't run with the
  ES5503); don't use the music library (`MU_*`), which claims the 6510 too.
- **Read first:** `emulator/test/host/test_oodos_sound.cpp` and `test_oodos_pb.cpp` claim the chip, load wave RAM
  and set the hook.

## Files

- `STAX.OGX` by `GX_ASSET` at startup; the `.SCR` screens by `DM_LOAD`/`DM_VWRITE`; the `.SID` and
  `STAX.WAV` by ordinary file reads (or `DM_LOAD` for speed) into a buffer outside `$4000–$7FFF`, then
  `SID_PLAY` / `SN_WAVE`.
- Missing or bad `STAX.OGX` or `TITLE.SCR`: restore the console, print one line with function 9, exit. A missing
  backdrop: a plain `$111` screen. A missing `.SID` or `.WAV`: no music or no effects.
- `HISCORE.DAT` (the top score, BCD) and `SETTINGS.DAT` (one record), read at startup, written on change.

## Testing and acceptance

The OO-1's cards are emulated, not built, so **the emulator is the target**. The game is done when the engine tests
and the `CcpRig` game tests pass, the build's rules gate and `w1.py` pass with no ld65 warnings, the music's
register test passes for all ten songs, and the manual checks below pass in the emulator.

### Engine tests

Each is a small ca65 program linked with the engine modules alone, run headless; it sets up state, calls a routine,
checks the result and exits 0 or a failure code. Run them the way the OO-1 repo runs its own (`CcpRig` `.COM`s or
sim65; decide in B3 after reading `emulator/test/host/`).

- **Pieces:** each of 7 × 4 rotations has exactly 4 cells matching the SRS shapes.
- **SRS:** every kick entry; I kicks against both walls; a T kicking into a T-slot.
- **7-bag / RNG:** each bag holds each piece once; the same seed gives the same sequence; xorshift never reaches 0.
- **Collision:** walls, floor, blocks; hidden rows are valid; pad columns 10–15 are never written.
- **Line clears:** 1–4 lines, non-adjacent rows; fill counts right after shifting.
- **Scoring:** every row of the table, BCD carry across 8 digits and the stop at 99,999,999, combos, B2B, the job
  multiplier from before the clear.
- **T-spin:** the 3-corner rule both ways; a T that moved last is not a T-spin.
- **Timing:** gravity at jobs 1, 7 and 10 over N frames; lock at 30; the 15-reset cap; overtime's lock delay.
- **Hold**, **game over** (block out, lock out), and a **replay**: a seed and a per-frame input log give a golden
  checksum.

### Game tests in the emulator

- `CcpRig` (`emulator/test/host/oodos_rig.h`): `put_m()` puts the game's files on `M:`, `cmd()` runs it. Model the
  tests on `emulator/test/host/test_gwbasic_gfx.cpp`, which runs a program and reads what it drew.
- **Keys through the emulated USB card**, which the game sees as a real keyboard:

  ```cpp
  UsbCard *usb = r.machine->usb_card();
  usb->key(0x4F, true);   // right arrow down
  r.run(ms(200));         // held 200 ms: DAS then ARR
  usb->key(0x4F, false);  // up
  ```

  `usb->queue_key(usage, down)` where the keyboard's 8 ms polling matters; `set_game_buttons` for the joystick.
- **Pixels:** read the shown screen from card memory and compare regions with the mockups' PNGs: the title plate,
  the panels and the well's frame must match exactly (they are drawn by the same code); a cell in the well must be
  the block design. A test that compares nothing fails.
- **Required:** title shown; a game starts with its job card; hold right and the piece reaches the wall (the sprite
  table); hard drop and the well's pixels; pause blanks the well; Q returns to `A>`; `STAX.OGX` missing gives
  the error line and a clean `A>`; and `STAX /T`, a built-in replay through the real program that prints the
  final score and the state's checksum, against golden values.

### Manual checks (emulator)

- [ ] It loads, finds its files and shows the title; each job's card shows its backdrop and its song starts.
- [ ] Quit returns to `A>` with the console readable; `^C` and `^S` don't interrupt play; the console mode is back.
- [ ] Ending by Break leaves a clean console after OODOS boots again.
- [ ] No tearing or flicker: piece, ghost, redrawn rows, row shifts, job changes.
- [ ] DAS 10 / ARR 2 slides; ARR 0 jumps to the wall; a quick tap of rotate is never lost.
- [ ] The joystick on controller 1 plays the game.
- [ ] Ghost and hard drop always agree; a piece slides along the floor for 15 resets, then locks.
- [ ] Music pauses with the game and stops on exit; no key is lost while it plays.
- [ ] Effects play on a revision 2 sound card; the game runs without one.
- [ ] High score and settings survive a restart.

## Open questions for the owner

- Ten backdrops plus the title are about 6.6 MB on the drive. Fine, or should backdrops share one file per two jobs?
- Should the job card show the backdrop at full brightness? That needs a second file per job (another 6 MB) or a
  second load during the card.
- The renders assume 8580 SIDs. Which chips will the board have?
- When will `feat/video-640` merge? Until then the game builds against that branch.
