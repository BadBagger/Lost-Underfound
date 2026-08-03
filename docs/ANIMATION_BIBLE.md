# Lost & Underfound — Animation Bible

Adapted from the Department of Impossible Complaints project's Animation Bible. The
rules below are unchanged in substance — only the character examples are swapped for
this project's own cast (Pip, Bramble, Grommet, Scuttle, Old Bottlecap). This is
carried over specifically because it worked: treat it as a binding production rule
from day one, not something to relax for a "smaller" or "cuter" game.

**This is a binding production rule.** A sequence is not animation because it has a
high frame count. Every non-held frame must deliberately lead from the preceding
action to the next one. Near-identical generated images that only flicker are
rejected, even if they play at 24 fps.

## The golden review test

Review each action both at speed and one frame at a time. For every transition, a
reviewer must be able to name the visible change: weight shifting, a foot travelling,
a hand preparing, a coat catching up, a face reacting, or an object moving. If the
only visible difference is image noise, framing drift, or a tiny redraw variation, it
is not an in-between; reject it.

Held frames are allowed only when they have a timing purpose: a beat before a reveal,
a weighted landing, a readable reaction, or a deliberate pause. They are never
padding.

## The twelve principles, applied here

1. **Squash and stretch** — Use drawn deformation to show material and weight while
   preserving volume: when an element widens, it must shorten by a corresponding
   amount. A bottle-cap coin can compress under Grommet's footstep; Bramble's fur can
   flex. Never fake life by scaling the whole character up and down.
2. **Anticipation** — Show the preparation before the primary action: Bramble lifts a
   stamp before it lands, Pip shifts onto the back foot before walking, Scuttle
   crouches before a fast scuttle-dash.
3. **Staging** — The action, actor, camera, dialogue, and hotspots must read at a
   glance. Scene dialogue is placed beside the speaker and never covers their face,
   body, or the needed interaction.
4. **Straight-ahead action and pose-to-pose** — Start with readable key poses, then
   author the in-betweens that connect them. Do not ask an image generator to create a
   batch of unrelated almost-identical poses and call the result a cycle.
5. **Follow-through and overlapping action** — Loose parts do not stop at the same
   time as the body. Bramble's ears, Grommet's loose stitching, Pip's shoelaces trail
   the torso by one or more frames, then settle.
6. **Slow in and slow out** — Space poses closer together as an action begins and
   ends, and farther apart through the middle. Frame count follows the action's
   weight and comic timing; 24 fps alone proves nothing.
7. **Arcs** — Hands, heads, and thrown or carried objects travel through believable
   curved paths rather than mechanically straight lines.
8. **Secondary action** — Add supporting motion without hiding the main idea: a
   whisker twitch, a stack-of-bottlecaps wobble after Old Bottlecap sets one down, a
   dust-mote drift while Bramble writes.
9. **Timing** — Choose the number and spacing of cels to communicate mass, intent,
   speed, and humor. Grommet's slow lumbering step gets a long prepared weight-shift;
   Scuttle's dash may need only a few purposeful cels.
10. **Exaggeration** — Push key poses enough to be readable and funny, while retaining
    each character's weight and the scene's perspective.
11. **Solid drawing** — Keep the character's construction, lighting, scale, foot
    contact, and camera perspective stable across every cel. An actor must not grow,
    shrink, float, or change anatomy because frames were generated separately.
12. **Appeal** — Poses should be clear, expressive, and worth watching even with sound
    muted. The scene should feel like an inhabited cartoon, not portraits placed over
    a background.

## Walk-cycle contract

A walk begins as a planned action, not a frame quota. At minimum, author a readable
alternating sequence:

`left contact → left recoil/down → left passing → left high point → right contact → right recoil/down → right passing → right high point → loop-safe return`

The exact number of cels is decided by the spacing needed for that action. Additional
cels must make a visible, intentional contribution to the step; they may not repeat a
pose with only incidental redraw changes.

For Pip, legs, hips, shoulders, and any carried/worn secondary elements must
participate. Each foot has a clear contact/passing/off-ground role. The torso leads
the step; loose elements lag and settle. The foot anchor stays on the scene's walk
plane, the engine supplies the contact shadow, and perspective scale changes only
with floor position — not with the animation frame. The same contract applies to
Scuttle's multi-legged scuttle-cycle, adapted for however many legs are actually
authored to move.

## Turnaround contract

When a walk-plane actor reverses horizontal travel, they must complete a short
in-place turnaround before the new walk cycle starts. The head and eyes lead, a foot
pivots, shoulders and hips follow, then any loose elements swing through and settle.
Reversing by immediately mirroring a walking sprite is rejected: it creates a visible
snap or backward walk.

## Scene-character contract

**A background plate is fixed.** A scene character is an isolated actor layer,
composited into a stable camera view and clipped or occluded by the real desk,
window, chair, or foreground furniture. Animating a resident character must never
swap, regenerate, or otherwise alter the whole room. The result must be that the
actor lives in the room — not that a different room appears behind them every few
frames.

Fixed characters (for example, Old Bottlecap at a toll gate) receive a passive
role-based loop even when the player is not talking to them, and talk/reaction
actions interrupt and resume that loop naturally.

### Smear-frame rule

A smear is a single, intentionally distorted transition cel for an unusually fast
motion. It is not a motion-blur filter and it is never a substitute for an
in-between. Use it only at a fast, sudden motion — Scuttle's dash, a stamp
descent/impact, a recoil — with solid readable drawings immediately before and after.
Preserve the performer's anchored head/torso while the moving limb, tool, or prop
stretches along its arc; restore normal volume on the next solid cel. Do not use a
smear for idle, dialogue, a hold, or ordinary walking.

All motion remains subordinate to scene staging. Background and prop motion — dust
motes, distant light shifts, background creatures, machinery — can make a room feel
alive, but it must not distract from the current player action.

## Required approval evidence

Before a new animation is called playable or published as final, provide:

- A labelled contact sheet showing the key-pose purpose of every cel.
- A normal-speed loop and a half-speed loop reviewed for at least two complete cycles.
- A mobile capture confirming stable scale, anchored feet, and a shadow directly under
  the actor.
- A check that dialogue and UI do not cover the speaking character or the current
  interaction.
- Explicit review of the primary motion plus secondary motion; no crossfade, blur, or
  duplicated imagery may be used to conceal missing action. A deliberate one-cel smear
  is allowed only under the Smear-frame rule above.
- Both the `frames` and `cast-scale` checks from `tools/check_registration.py` passing
  (see `docs/CODEX_BUILD_PROMPT.md`) — no sheet is "final" while either is red.

## Current status

No character sheets have been authored yet. This section gets filled in as sheets are
produced and reviewed — record each sheet's name, its approval state
(provisional/rejected/final), and why, the same way the reference project tracked its
walk-sheet history.
