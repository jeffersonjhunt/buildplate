# OOE Build Plate — working here

A falling-block game for the OO-1, `BUILDPLT.COM`. The spec is [spec.md](spec.md), the units of work are
[PLAN.md](PLAN.md), the screens are [mockups/](mockups/). Start with the spec, then the OO-1 repo's `AGENTS.md`.

## Where things are

- **This repo:** `games/buildplate` in the workspace (`/home/codemonkey/workspace/games/buildplate` in the
  container, `/Users/jhunt/Source/Edda/games/buildplate` on the Mac). Origin: the Gitea server,
  `ssh://git@git.tworivers:2222/jeffersonjhunt/buildplate.git` (web <https://git.tworivers:9443>). GitHub and
  CodeCommit are only ever mirrors, never the origin.
- **The OO-1 repo:** `../../6502` (`jeffersonjhunt/6502`). The game needs OODOS 0.12 (OOLIB interface 13: direct
  640, `GB_DIRECT`, `DM_VFILLW`), on its branch `feat/video-640` until that merges. Build against a checkout of that
  branch through the Makefile's `SIX`; never commit to the OO-1 repo from here, and never write into its build
  directories (build OODOS and the emulator into this repo's `build/`, as OO-Amp does).
- **The model to copy:** OO-Amp, `../../ooamp`: a program in its own repo built against `../6502`, its Makefile,
  `cfg/`, `test/` and `tools/`.
- **If the game needs something OODOS or OOLIB doesn't have,** write a request in the OO-1 repo's style (OO-Amp's
  `OODOS-*-REQUEST.md` files are the pattern), put it in `reference/`, and stop for the owner. Don't patch the OO-1
  repo from this one.

## How to work

- **One worktree a unit:** `games/buildplate.worktrees/<unit>` on a branch `feat/<unit>` (`feat/b0-scaffold`, ...).
  Never work on `main`. The owner merges.
- **Generated assets are made by `tools/`,** never edited by hand: change the script and run it again. The mockups
  are generated too (`tools/ooe_mock640.py`); the game's drawing must stay the same design, so draw the UI sheet
  from the same code.
- **Large files:** the songs' reference renders are MP3s; don't commit WAV renders of the songs, `.SCR` screens or
  build output (they are rebuilt). Effect WAVs are small and stay.
- **Python** for tools: run as `python3 -I`; their requirements are in `tools/requirements.txt`.
- **No Digital Research text or code**, no trademarked names or art, and every tune, picture and sound original.

## SDLC

The lifecycle is the **`sdlc` skill** (`code-monkeys/007/skills/sdlc`). Each unit of [PLAN.md](PLAN.md) is tier
`undeployed`: it builds files verified in the emulator and ships nothing to a runtime, as OO-Amp's milestones were.
The campaign's own state (its survey) is in `.sdlc/campaign.json`; a unit's state is `.sdlc-state.json` at its
worktree's root (gitignored).

<!-- sdlc:begin -->
release.merge_by: host
verify.require_negative: true
<!-- sdlc:end -->

Both are the skill's defaults, pinned so a change to the defaults can't move this project.

### What `verify` means here

- **The emulator is the target.** A test that doesn't boot OODOS in the emulator and run the game proves the
  engine, not the game. Both are needed.
- **Prove each check can fail:** plant the fault (a wrong pixel in the sheet, a changed note, a broken kick entry)
  and see the test catch it.
- **A pixel test that compares nothing fails.** Check the region's size and that it isn't all one colour.
- **Build from clean** (`make clean test`) before claiming a unit: the tools' outputs and OODOS's build are in
  `build/`, and a stale file passes tests it shouldn't.
- **Worktrees omit gitignored files.** If a test skips there for want of one, that is a failure to report, not a
  pass.
- **On any test failure: stop,** write down what failed and the fix you propose, and ask before changing code or
  tests.
