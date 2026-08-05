# Spec: Rhubarb Lip-Sync Integration

## Why this, and how it relates to the Bible's Talk-loop contract

`ANIMATION_BIBLE.md`'s "Talk-loop contract" already fixes the "she keeps lifting her
arm in a loop while talking" problem — gesture-then-settle phasing, ping-pong
instead of a hard snap, timing jitter, and a real gesture pool as the long-term fix.
**That contract is about the body — this spec is about the face, and they compose,
they don't replace each other.** Real-audio-driven mouth shapes fix the specific
"her mouth doesn't match what she's saying" problem, which the Talk-loop contract
doesn't touch on its own. Do both — this spec's runtime playback section explicitly
treats the mouth layer as an independent track from whatever the Talk-loop contract
is doing with the rest of the body, the same way that contract already calls for
"independent secondary layers such as blinks... that do not repeat in lockstep with
the mouth/hand gesture."

## What Rhubarb actually does (verified against source, not assumed)

[Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync) is a free,
**MIT-licensed** CLI (fully commercial-use permitted, no tier/attribution
restriction — unlike the ElevenLabs voice audio, this part of the pipeline has zero
licensing caveat to track). It takes an audio file and outputs a timed sequence of
mouth-shape codes:

```
rhubarb -o output.json -f json --dialogFile line.txt --extendedShapes GHX voice.ogg
```

- **Input**: WAV or **Ogg Vorbis** directly — every voice file in this pipeline is
  already mono OGG Vorbis, so there is no conversion step needed before running it.
- **`--dialogFile`**: a plain-text transcript of the line improves recognition
  accuracy. Every recorded line already has its exact text sitting in
  `CHAPTER_01_DIALOGUE.json` / `ACT_01_DIALOGUE.json` — this is a free accuracy win
  already available, not something to go author separately.
- **Output** (JSON): a `mouthCues` array of `{ start, end, value }` in seconds, e.g.
  `{ "start": 0.05, "end": 0.27, "value": "D" }`.
- **Shape codes**: 6 basic (A closed/P-B-M, B slightly-open-teeth-together, C
  open-vowel, D wide-open-vowel, E rounded-vowel, F puckered/W-OW) plus 3 optional
  extended (G teeth-on-lip for F/V, H tongue-raised for L, X idle/rest). Extended
  shapes need more source art per character but read noticeably better on
  consonant-heavy lines — use them for named recurring characters (Pip, Mara, Quire),
  skip them for one-off bit-part voices if art budget is tight.

## Art requirement — new, and it's real character art, not a shortcut

Each character that gets lip-sync needs a small **mouth-shape sprite set**, layered
independently from the base head/idle art so the mouth can swap shapes without
regenerating the whole face every frame: minimum the 6 basic shapes, ideally +GHX.
This is a new authored sheet, and it is still governed by everything already
established for character art — it needs its own `registration.json` (same canvas,
same anchor point relative to the head, so swapping the mouth layer never shifts or
resizes anything) and must pass `check_registration.py frames` before use. Lip-sync
does not get a pass on registration discipline just because it's driven by data
instead of hand-timed like the gesture loops.

## Build-time pipeline

A batch script (same style as `check_registration.py`, same place it would live —
`tools/`):

1. For every voice line in a chapter/act's dialogue manifest that has real recorded
   audio (`audio_filename` set, per the existing manifest shape), write its `text`
   to a temp `.txt` file and run `rhubarb` against the matching `.ogg`, with
   `--dialogFile` pointed at that text.
2. Save the resulting JSON as a sidecar next to the audio — e.g.
   `act01-001-pip-cold-open-landing.mouthcues.json` alongside
   `act01-001-pip-cold-open-landing.ogg`.
3. **Completeness check**, same pattern already used for the audio manifests in
   this project: every voiced line has a matching sidecar file, flag any that don't
   (a failed Rhubarb run, a missing transcript) rather than silently shipping a line
   with no mouth data.
4. Re-run this whenever a line's audio is regenerated (ElevenLabs free-tier
   redo, a paid-tier re-record, a swap to real VO) — the sidecar is derived data,
   never hand-edited, always regenerate rather than patch.

## Runtime playback

When a line starts:

1. Load that line's `mouthCues` array (already known in full before playback
   starts — no need to poll or stream).
2. Build a one-time sequence of timed mouth-shape swaps from the cue list — the
   same `delayedCall`-chaining pattern already used for the turnaround animation
   (`turnTo()` in `main.ts`) is the right mechanism here too: schedule each cue's
   shape swap at its `start` time relative to when audio playback begins, don't poll
   audio position every render tick.
3. On the swap, set only the mouth-layer sprite's texture/frame to the shape's art
   — the rest of the character (body, gesture loop, everything from the earlier
   talk-animation fix) keeps playing independently. The mouth layer and the gesture
   loop are two separate, uncoupled animation tracks composited together, same
   principle as the Animation Bible's existing "independent secondary layer" idea
   for blinks — this is that same idea, just driven by real audio data instead of a
   generic timer.
4. On line end, return the mouth layer to its `X` (idle/rest) shape.

## Scope note

This is worth building once, generically, in whatever shared tooling repo houses
`check_registration.py` — every character in every project that has recorded voice
benefits from it, and re-deriving it per project would repeat the exact "copy drift"
problem the shared Animation Bible repo already exists to prevent.
