# Mockups

Every screen of One Off Stax, rendered pixel for pixel for screen type 7 (direct 640: 640×480, RGB444) by
`tools/ooe_mock640.py`, through `tools/mkreference.py`. Change the script, not the PNGs.

| Screen | PNG | Board (notes, coordinates, colours) |
| --- | --- | --- |
| Title | [png/screen-title.png](png/screen-title.png) | [Title.dc.html](Title.dc.html) |
| Job card | [png/screen-jobcard.png](png/screen-jobcard.png) | [JobCard.dc.html](JobCard.dc.html) |
| Play | [png/screen-play.png](png/screen-play.png) | [Play.dc.html](Play.dc.html) |
| Play, line clear | [png/screen-play-clear.png](png/screen-play-clear.png) | [PlayClear.dc.html](PlayClear.dc.html) |
| Pause (LINE HOLD) | [png/screen-pause.png](png/screen-pause.png) | [Pause.dc.html](Pause.dc.html) |
| Game over (LINE STOP) | [png/screen-gameover.png](png/screen-gameover.png) | [GameOver.dc.html](GameOver.dc.html) |
| Settings | [png/screen-settings.png](png/screen-settings.png) | [Settings.dc.html](Settings.dc.html) |
| The ten jobs' backdrops | [../art/backdrops/](../art/backdrops/) | [Backdrops.dc.html](Backdrops.dc.html) |
| Name, palette, art direction | [png/names.png](png/names.png) (the first draft's title plates) | [Main.dc.html](Main.dc.html) |

The `.dc.html` boards and `canvas.json` are a copy of the design canvas "One Off Stax — Screen Mockups"
(<https://claude.ai/artifact/49iQcyFDEBNBNhvGoxN83x>), with their images pointed at this repo's files. Read them for
their notes; open the PNGs for the pixels. Where a note and [../spec.md](../spec.md) disagree, the spec wins.

Things the mockups show that a reader might miss:

- A block is an 8×8 design shown doubled, the same for the falling piece (a sprite) and locked cells.
- Text is one 5×7 face drawn 2× in 16×16 cells (5× and 4× for the job number and the title's name).
- The backdrop shows only between the panels, dimmed to 75%; the job card shows each one before its job.
