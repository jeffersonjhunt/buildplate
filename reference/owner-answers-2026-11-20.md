# Answers to questions.md

Written 2026-11-20 from the 6502 repo at main `ae8b59d9`. Paths below are in that repo.

## 1. Can CcpRig send key events, so tests work without a keyboard?

Yes. `emulator/test/host/oodos_rig.h` has two helpers, and the USB card can also be driven directly.

- **`r.type("...")`** sends characters on the serial console, each offered until taken. It's good for typing at
  `A>`, but it's characters only: no key-up, no arrows.
- **`r.type_usb("...")`** presses keys on the emulated USB keyboard: down, 20 ms, up, 20 ms. It handles letters,
  digits, space, Return, Delete and Ctrl-letters.

A game needs held keys and arrows, which `type_usb` doesn't map, so drive the card itself:

```cpp
UsbCard *usb = r.machine->usb_card();
usb->key(0x4F, true);    // right arrow (HID usage) down
r.run(ms(200));          // held for 200 ms of emulated time
usb->key(0x4F, false);   // up
```

- **The arrows** are HID usages `0x4F` right, `0x50` left, `0x51` down and `0x52` up. Space is `0x2C`.
- **What the game sees:** the same as from a real keyboard. Through OOLIB's event area, each key change goes into
  the queue, and the held-keys map has one bit per HID usage (Programmer's Guide, chapter 8, "The keyboard").
- **Exact timing:** `usb->queue_key(usage, down)` reports changes no faster than the keyboard's 8 ms polling, as
  real hardware would.
- **Other input** on `UsbCard`: `set_game_buttons`, `set_paddle`, `mouse_move`, `mouse_to` and `mouse_buttons`.

`emulator/test/host/test_gwbasic_gfx.cpp` uses the same rig to run a program and read what it drew, which is a
model for a game test that presses keys and then checks the screen.

## 2. Does mkasset.py support this layout?

> 8×8, 4-bit tile layer giving 40×30 cells; eight sprites for the active piece and its ghost; one format 4 asset
> file, loaded with `GX_ASSET`.

**Yes,** with one flag for the tiles, and the new `combine` command for the single file.

### The tiles: give `--map 64`

```
python3 -I oodos/tools/mkasset.py tiles board.png BOARD.OGX --tile 8 --bpp 4 --map 64
```

- **The map width:** a 40-cell-wide picture needs `--map 64`. The default map is 32 wide, and without the flag the
  tool refuses with "40 x 30 tiles: the map is 32 x 64 at most". 30 rows fit the default height of 32.
- **The output:** a palette, the tiles (each distinct tile stored once, up to 1,024) and the map.
- **Colours:** at 4 bits there are 16, with colour 0 transparent where the layer allows it. `--quantize` reduces a
  picture with more.

### The sprites

```
python3 -I oodos/tools/mkasset.py sprites pieces.png PIECES.OGX --size 8x8 --bpp 4
```

- **Sizes:** sprites are 8, 16, 32 or 64 pixels a side, up to 64 images in a sheet, read left to right and then
  down. A pixel with alpha under 128 becomes 0, which is transparent.
- **The table:** `--table` adds a sprite table, but only as a test layout that shows the images in a row. A game
  normally sets its eight sprites' entries itself (position, image, depth, palette offset).

### One file: `combine` (new)

```
python3 -I oodos/tools/mkasset.py combine GAME.OGX BOARD.OGX PIECES.OGX
```

`combine` puts the parts of several asset files into one, in order, so the game loads everything with one
`GX_ASSET` call. On the layout above it produces:

```
part 1: palette, CONFIG $00, page any, 512 bytes
part 2: tiles,   CONFIG $22, page any, 256 bytes
part 3: map,     CONFIG $22, page any, 4096 bytes
part 4: sprites, CONFIG $00, page any, 2048 bytes
```

Its rules:

- **Palettes:** a palette identical, byte for byte, to one already taken is left out. Palettes that differ are all
  kept, in order, and the tool says "N different palettes kept".
- **Sprites:** at most one sprite-images part and one sprite table, and a table only with its images. `GX_ASSET`
  places the table relative to the one images part.
- **Placement:** parts placed at fixed card pages must not overlap.
- **Size:** at most 7 parts in the file.
- **Checking:** `python3 -I oodos/tools/mkasset.py check GAME.OGX` lists the parts.

**Status:** `combine` is on the 6502 branch `feat/mkasset-combine` (commit `6c4725ba`), with checks in
`oodos/test/check_mkasset.py`. It isn't on main until it passes the gate and the owner says to merge.

### Palettes

Each `tiles` and `sprites` run builds its own palette from its own picture, in the order colours first appear. So
the same colour number can mean different colours in the two files.

- **Simplest:** draw both pictures from one shared 16-colour set, so the palettes come out identical; `combine` then
  keeps one.
- **Otherwise:** a 4-bit sprite's colour is its palette offset × 16 plus the pixel (Technical Reference, chapter 6,
  sprite entry byte 7), so sprites can use a separate group of 16 entries.
- **Check how the palette part reaches the card's palette.** `GX_ASSET` loads every part into card memory and
  checks it, but this answer hasn't traced how a palette part is then applied. See `oodos/lib/gxasset.s` and the
  Programmer's Guide, chapter 8 ("Loading", "Assets", "The library").

## 3. How should the game drive the ES5503 for sound effects?

OOLIB lets a program own the chip and fills its wave RAM; the program then plays effects by writing the oscillator
registers itself. There's no effects player for the ES5503 in OOLIB.

The reference is the Programmer's Guide, chapter 8: "Sound", then "The ES5503". The registers are in the Technical
Reference, chapter 7, "Revision 2".

### Steps

1. **Claim the chip.** Call function 82 with `SN_CLAIM` and `SC_DOC`. It's refused without a revision 2 sound card,
   or while another program or RSX holds the chip. Fall back to the SIDs or to silence.
2. **Load the samples once.** `SN_WAVE` copies 8-bit samples from memory into the chip's 128 KB of wave RAM by DMA.
   Keep a table of each effect's start, size and pitch. A load that would run past the end of wave RAM is refused.
3. **Play an effect.** Write one oscillator's registers through `DOCCTL`, `DOCDATA`, `DOCADDR` and `DOCBANK`:
   - its wave address and table size;
   - its frequency;
   - its volume;
   - its control register, in one-shot mode so it stops by itself at the end of the sample.

   With 32 oscillators, give each kind of effect its own (line clear, drop, rotate, and so on) so effects don't cut
   each other off.
4. **Optional: a hook.** `SN_DOCHOOK` sets a routine OODOS calls when an oscillator finishes, to chain or repeat
   effects. It runs with interrupts masked, so keep it short.
   - **On entry:** the ports are set up for the chip's registers, and the oscillator number is in bits 1–5 of a
     zero-page byte you name.
   - **On return:** OODOS restores `DOCCTL`, `DOCADDR` and `DOCBANK`, so a `DOCCTL` change made in the hook is
     undone. To stop sound from the hook, halt oscillators through their own control registers (`$A0` + the
     number, bit 0).
5. **Release it.** Call `SN_RELEASE` when the game ends. The warm boot also stops the chip and releases it if the
   game exits without doing so.

### Things that will bite

- **The PCM/MP3 stream and the ES5503 can't run at the same time.** If the game streams music, put the effects on the
  SIDs instead.
- **The clean split is music on the SIDs, effects on the ES5503.** OOLIB's music driver (`MU_INIT`, `MU_NOTE`,
  `MU_INSTR`, ...) plays notes on the SIDs from the card's 6510, so it doesn't compete with the ES5503, and the SIDs
  can always play alongside it.
- **Don't program the card's 6510 yourself** for effects. AGENTS.md makes it OODOS's (the music driver uses it).
  Drive the claimed ES5503 from the main CPU as above.
- **Where to trigger effects:** from the main loop, or from the tick hook (`FT_TICKHOOK`) if they must be timed.
  Starting one is a handful of port writes, so keep it out of drawing loops.

**Working code to read:** `emulator/test/host/test_oodos_sound.cpp` and `test_oodos_pb.cpp`. They claim the chip,
load wave RAM and set the hook.