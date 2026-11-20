# audio

Reference sound for OOE Build Plate, made by [../tools/](../tools/) (`mkreference.py`).

- `songs/jobNN-<title>.mp3`: the ten songs, one per job, rendered from `tools/bp_album.py` by `tools/sidtrack.py`
  through two emulated 8580 SIDs (SID A left, SID B right). They are the reference for how `JOBnn.SID` must sound;
  the exact reference is `sidtrack.play()`'s register writes. Styles, tempos and keys are in
  [../spec.md](../spec.md), "Jobs: backdrops and songs".
- `sfx/<effect>.wav`: the sixteen effects for the ES5503, 8-bit unsigned at 20,000 Hz, every byte 1–255 (a 0 halts
  an oscillator; `mkwaves.py` adds it when it lays them out in wave RAM). About 112 KB in all.
