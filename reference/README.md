# reference

- [owner-answers-2026-11-20.md](owner-answers-2026-11-20.md): the owner's answers on driving the USB keyboard from
  `CcpRig`, `mkasset.py`'s layouts and `combine`, and playing effects on the ES5503. Written against the 6502 repo's
  `main` `ae8b59d9`; spec.md folds them in. Its parts about 8×8 tile layers predate the move to direct 640.
- The design document this spec grew from: "One Off Stax for the OO-1 — Implementation Spec"
  (<https://claude.ai/artifact/GF7kAbj5z5XYM21NJLk7cT>). [../spec.md](../spec.md) replaces it; edit the spec here.
- The mockup canvas: <https://claude.ai/artifact/49iQcyFDEBNBNhvGoxN83x> (copied into [../mockups/](../mockups/)).

In the OO-1 repo (`../../6502`, branch `feat/video-640` until it merges):

| What | Where |
| --- | --- |
| How to work there | `AGENTS.md` |
| Direct 640 (layer type 7): the owner's decisions, the definition, costs as built | `hw/video640.md` |
| Video, the card | `docs/oo1-technical-reference/06-video.md`, "Bitmap 640 and direct 640" |
| Sound, the card (SIDs, 6510, ES5503) | `docs/oo1-technical-reference/07-sound.md` |
| OOLIB: event area, graphics library, `.sid` library, sound parts, loading | `docs/oodos-programmers-guide/08-game-services.md` |
| BDOS functions 80–83 | `docs/oodos-programmers-guide/07-function-reference.md` |
| OOLIB's calls and equates | `oodos/include/oolib.inc` |
| The asset tool | `oodos/tools/mkasset.py` (`direct640`, `sprites`, `combine`, `check`) |
| The test rig | `emulator/test/host/oodos_rig.h`; examples `test_gwbasic_gfx.cpp`, `test_oodos_sound.cpp`, `test_oodos_pb.cpp` |
| A program built against the OO-1 repo from its own | `../../ooamp` (Makefile, `cfg/`, `test/`, `tools/`) |
