# One Off Stax

A falling-block puzzle game for the OO-1 microcomputer: a W65C02S running OODOS, with a 640×480 direct-colour
screen, two SIDs and an ES5503. Ten jobs, each with its own backdrop and song, getting faster, then endless
overtime. Tagline: STACK FAST.

**Status:** specified, not yet built. Everything here is the input for building it.

| Where | What |
| --- | --- |
| [spec.md](spec.md) | the specification |
| [PLAN.md](PLAN.md) | the units of work, B0–B11 |
| [CLAUDE.md](CLAUDE.md) | how to work here (for people and agents) |
| [mockups/](mockups/) | every screen, pixel for pixel, with coordinates and colours |
| [art/](art/) | the ten backdrops and the title's |
| [audio/](audio/) | the ten songs (reference renders) and the sixteen effects |
| [tools/](tools/) | the scripts that made all of it |
| [reference/](reference/) | the owner's answers and pointers into the OO-1 repo |

Builds against the OO-1 repo (`../../6502`), OODOS 0.12 or later.
