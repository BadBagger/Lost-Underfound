# Bramble Rig Pipeline

Bramble is an off-manifold character: a lint/dustball clerk with no reliable
base-model anatomy prior. Diffusion and LoRA may help create an approved
canonical design, but final animation must be deterministic.

## Decision

Do not generate Bramble runtime animation as independent diffusion frames.

Use ComfyUI/LoRA/reference editing only for:

- canonical Bramble identity sheets
- expression and mouth-shape source art
- clean actor-only part source on transparent or keyable backgrounds

Use a deterministic rig, Live2D/Spine/Rive/DragonBones/Blender NPR, or an
equivalent pinned-part pipeline for:

- idle breathing
- blink
- talk
- hand gestures
- inspect/reaction beats

The rig output can still be exported as PNG frame sequences for AGS, but each
frame must come from the same source parts and pivots.

## Required Part Library

All Bramble parts share one coordinate space and one desk contact guide. The
counter line is not part of the character art; AGS or the room mask occludes the
lower body.

Minimum parts before animation:

- `body_base.png` - full dustball mass, including lower construction
- `body_squash.png` - compressed breathing/talk accent shape
- `body_stretch.png` - lifted breathing/talk accent shape
- `eyes_open.png`
- `eyes_half.png`
- `eyes_closed.png`
- `brows_neutral.png`
- `brows_worried.png`
- `brows_proud.png`
- `mouth_closed.png`
- `mouth_small_open.png`
- `mouth_wide_open.png`
- `mouth_oo.png`
- `mouth_frown.png`
- `hand_left_rest.png`
- `hand_left_point.png`
- `hand_right_rest.png`
- `hand_right_handoff.png`

Optional but preferred:

- `lint_overlay_front.png`
- `spectacles.png`
- `bow_tie.png`
- `shadow_reference.png` for QA only, not baked into runtime frames

## Pivot Rules

- Every part is authored on the same canvas size.
- Every part declares a pivot in `art/rigs/bramble/manifest.json`.
- Body variants share the same root pivot.
- Eye, brow, mouth, spectacles, and bow tie pivots remain attached to the body
  coordinate system, not re-centered per image.
- Hands may rotate/translate from pivots, but their source PNGs must not be
  cropped differently per state.
- No part may include the desk, chair, bell, ledger, room, speech UI, or baked
  cast shadow.

## Animation States

Author these as rig timelines, then export to AGS views/frames:

- `idle`: 24-frame timeline, looping, low-amplitude body breath, blink timed
  independently, no whole-body scaling.
- `talk`: 48-frame timeline, looping phrase-safe, body/eyes/brows participate,
  mouth driven by discrete mouth parts.
- `greeting`: 36-frame non-looping gesture, notice -> straighten -> clerk pose.
- `handoff`: 36-frame non-looping gesture, hand reaches above counter line and
  returns.
- `wrongAction`: 30-frame non-looping correction/wag.

Dense exported frame counts are allowed only because a rig creates controlled
in-betweens. The same registration/full-construction QA still applies after
export.

## QA Gate

Run:

```powershell
npm.cmd run qa:rig:bramble
npm.cmd run engine:export:bramble
npm.cmd run qa:engine:bramble
npm.cmd run qa:engine:characters
```

The gate verifies:

- required parts exist before `parts-ready` or `animation-ready`
- all parts use the same canvas
- no part touches the canvas edge
- every required part has a declared pivot
- no forbidden scene terms appear in part filenames
- exported frames match deterministic render hashes
- exported dense frames are not duplicate cels pretending to be animation
- Bramble mouth cue data has a consolidated `visemes/index.json`
- the shared character engine-export gate accepts Bramble alongside Pip,
  Old Bottlecap, and Scuttle

If this gate fails, Bramble is not animation-ready.

`engine:export:bramble` and `qa:engine:bramble` are compatibility wrappers over
the shared Act 1 character export/check tools. Do not add a Bramble-only export
path that can drift from the rest of the cast.

## Engine Export

The finished Bramble runtime package is exported to:

- `art/engine-export/bramble/bramble.engine.json`
- `art/engine-export/bramble/bramble_idle.png`
- `art/engine-export/bramble/bramble_talk.png`
- `art/engine-export/bramble/bramble_greeting.png`
- `art/engine-export/bramble/bramble_handoff.png`
- `art/engine-export/bramble/bramble_wrongAction.png`
- `art/engine-export/bramble/bramble_mouth_visemes.png`

Import each strip as evenly divided 320x260 RGBA frames. The AGS-facing view
names are declared in `bramble.engine.json`. The talk strip is the body/brow
base; `bramble_mouth_visemes.png` supplies the X/A/B/C/D/E/F mouth overlays for
Rhubarb-style cue tracks or AGS talk-mouth timing.

## Current Source Mode

The current Bramble export is `separated-body-and-part-sheet-source`:

- one high-quality keyed canonical body image supplies the painterly identity
- the deterministic renderer supplies breathing, blink, lint shimmer, gesture
  offsets, and separate mouth overlay visemes
- QA contact sheets include the body loops and runtime mouth-overlay alignment
- clean body-only dust mass
- separate eyes, brows, spectacles, bow tie, mouth visemes, and hand poses
- all parts on the same 1024x1024 canvas with the existing pivots
- no desk, chair, counter, bell, ledger, room, UI, or speech art in any part

This is the finished repo-native Bramble character model for Act 1. Future
Live2D/Spine work may replace the renderer, but it must export the same states,
anchors, visemes, and QA evidence before it can replace this package.
