# Animation Bible — Lost & Underfound

> **Source of truth: [`BadBagger/Animation-Bible`](https://github.com/BadBagger/Animation-Bible).**
> This file is a synced local copy of that repo's `ANIMATION_BIBLE.md`, kept here so
> Codex (and anyone else working in this repo) has the rules on hand without needing
> cross-repo access. **Do not edit the rules below directly** — if a rule needs to
> change, change it upstream in `Animation-Bible`, then re-sync this file. The
> "Current status" section at the bottom is this project's own and is not synced.

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
   amount. A stamped page can compress; a coat can flex; a stack of coins can
   compress under a footstep. Never fake life by scaling the whole character up and
   down.
2. **Anticipation** — Show the preparation before the primary action: a hand lifts a
   tool before it lands, a character shifts onto the back foot before walking, a hand
   hovers before opening a drawer.
3. **Staging** — The action, actor, camera, dialogue, and hotspots must read at a
   glance. Scene dialogue is placed beside the speaker and never covers their face,
   body, or the needed interaction.
4. **Straight-ahead action and pose-to-pose** — Start with readable key poses, then
   author the in-betweens that connect them. Do not ask an image generator to create a
   batch of unrelated almost-identical poses and call the result a cycle.
5. **Follow-through and overlapping action** — Loose parts do not stop at the same
   time as the body. Coat tails, sleeves, hair, ears, carried props, and loose
   stitching trail the torso by one or more frames, then settle.
6. **Slow in and slow out** — Space poses closer together as an action begins and
   ends, and farther apart through the middle. Frame count follows the action's
   weight and comic timing; 24 fps alone proves nothing.
7. **Arcs** — Hands, heads, bags, and thrown or carried objects travel through
   believable curved paths rather than mechanically straight lines.
8. **Secondary action** — Add supporting motion without hiding the main idea: a coat
   tail lag during a step, a wobble after an impact, an ambient head-bob or twitch
   while a fixed character performs their idle loop.
9. **Timing** — Choose the number and spacing of cels to communicate mass, intent,
   speed, and humor. A heavy action gets a prepared lift, impact, and settling beat; a
   quick glance may need only a few purposeful cels. A larger/heavier character's
   timing should read as heavier than a smaller/lighter one performing the same verb.
10. **Exaggeration** — Push key poses enough to be readable and funny, while
    retaining each character's weight and the scene's perspective.
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

For any freely-walking actor, legs, hips, shoulders, and any carried/worn secondary
elements must participate. Each foot has a clear contact/passing/off-ground role. The
torso leads the step; loose elements lag and settle. The foot anchor stays on the
scene's walk plane, the engine supplies the contact shadow, and perspective scale
changes only with floor position — never with the animation frame. This contract
applies regardless of leg count; a multi-legged actor adapts the same
contact/passing/off-ground logic across however many legs are actually authored to
move.

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
swap, regenerate, or otherwise alter the whole room. The result must be that the actor
lives in the room — not that a different room appears behind them every few frames.

Fixed/furniture-anchored characters receive a passive role-based idle loop even when
the player is not interacting with them — writing, tinkering, checking a result,
returning to the loop. Talk and reaction actions interrupt and resume that loop
naturally.

Any furniture-anchored or "windowed" character (behind a counter, desk, gate, or
similar) must use a layered rig, not a single loose full-body sprite composited over
the background:

- a fixed background plate with that character absent
- the character's body layer, composited behind the counter/furniture contact line
- a foreground occlusion mask (the counter/desk/gate edge) on top of the character's
  lower body
- hands/tools/props allowed to render above the contact surface as a separate top
  layer
- every frame in the rig shares one canvas, one origin, one contact guide — no
  per-frame crop or resize hacks, ever

### Smear-frame rule

A smear is a single, intentionally distorted transition cel for an unusually fast
motion. It is not a motion-blur filter and it is never a substitute for an
in-between. Use it only at a fast, sudden motion — a pen flick, a stamp
descent/impact, a recoil, a dash — with solid readable drawings immediately before and
after. Preserve the performer's anchored head/torso while the moving limb, tool,
sleeve, or paper stretches along its arc; restore normal volume on the next solid
cel. Do not use a smear for idle, dialogue, a hold, or ordinary walking.

All motion remains subordinate to scene staging. Background and prop motion —
creatures, lamps, rain, drifting objects, machines, indicator lights — can make a room
feel alive, but it must not distract from the current player action.

## Registration and normalization (the gate before animation)

Generated or hand-drawn frames are not finished sprites until they pass registration —
treat every sheet like a traditional animation cel set with real pegs, not a folder of
independently-generated images.

1. **Separate actor placement from animation art.** Placement (anchor point, display
   size, world position) is engine-controlled and fixed per actor. The frame sheet
   itself must never be resized or repositioned per-frame to compensate for bad
   source art — if a frame doesn't fit the shared anchor/scale, the frame is wrong,
   not the code.
2. **Registration guides per actor sheet.** Every character sheet needs an explicit,
   documented baseline: a feet/contact line for a freely-walking actor, a
   furniture-contact line for a fixed/anchored actor. Every frame in that sheet is
   authored or normalized against that same guide.
3. **A frame normalization step, not manual eyeballing.** Before any frame enters a
   game, run `tools/check_registration.py frames <sheet>/registration.json` — it
   verifies identical canvas size and identical contact/anchor point across every
   frame in a sheet, within tolerance. Reject or re-pad any frame that doesn't match.
4. **Cast-wide scale parity, checked, not eyeballed.** A cast can absolutely include
   characters of very different sizes on purpose — that's a design choice, not a bug.
   What must never happen by accident is source art authored at the wrong real-world
   scale relative to the rest of the cast. `tools/check_registration.py cast-scale
   <cast_scale.json>` verifies every character's measured source-art scale agrees with
   its director-declared proportion in the roster, catching accidental mis-scale
   without flagging intentional size differences.
5. **A visual QA page before anything is called playable.**
   `tools/check_registration.py frames <sheet>/registration.json --onion-skin out.png`
   overlays every frame of a sheet on top of each other, aligned by anchor. If feet,
   head, or the contact anchor visibly jumps between frames, this is where it gets
   caught — not after it ships as a visible glitch.
6. **Animate last, not first.** 24fps timing, in-betweens, and smear frames only get
   added once a sheet has passed registration/normalization/cast-scale/QA. More
   frames on top of ungoverned registration only produces more visible drift, not
   better animation.

## Hard gate

**A frame that does not pass both `check_registration.py frames` and
`check_registration.py cast-scale` does not get merged into the game.** This is not
advisory — wire both checks into CI or, at minimum, a documented pre-merge checklist,
so every character sheet in this project goes through them before shipping.

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
- Both `check_registration.py` checks passing — no sheet is "final" while either is
  red.

## Current status

Project-specific, not synced from upstream. No character sheets have been authored
yet. Record each sheet's name, its approval state (provisional/rejected/final), and
why, as sheets are produced and reviewed — Pip's walk cycle should be the first entry
here, per the build order in `docs/CODEX_BUILD_PROMPT.md`.

### Current sheet evidence

| Sheet | Actor type | State | Evidence |
|---|---|---|---|
| `art/qa-placeholder` | walk-plane fixture | provisional/pass | `npm run qa:placeholder` passes and writes `art/qa-placeholder/onion.png`. |
| `art/qa-broken` | walk-plane fixture | rejected/expected fail | Deliberately mismatched canvas and anchor drift; `npm run qa:broken` must fail and is not part of `npm test`. |
| `art/pip-walk` | walk-plane | provisional/pass | 9-role walk-cycle contract sheet; `npm run qa:pip` passes and writes `art/pip-walk/onion.png`. |
| `art/old-bottlecap-idle` | furniture-anchored | provisional/pass | Fixed-contact rig sheet; `npm run qa:bottlecap` passes and writes `art/old-bottlecap-idle/onion.png`. |
| `art/bramble-idle` | furniture-anchored | provisional/pass | Desk-fixed idle sheet for Act 1; `npm run qa:bramble` passes and writes `art/bramble-idle/onion.png`. |
| `art/scuttle-walk` | walk-plane | provisional/pass | Cameo-only scale/registration sheet; `npm run qa:scuttle` passes and writes `art/scuttle-walk/onion.png`. |
| `art/grommet-idle` | furniture-anchored placeholder | provisional/pass | Cast-scale placeholder only; not playable until Acts 2-3 get a script/design pass. |

`npm run qa:cast` passes against the full declared cast at 220 px/world unit. None of
these sheets are final production animation approval; final status still requires the
contact-sheet, normal/half-speed loop, mobile capture, dialogue-staging, and secondary
motion review evidence listed above.
