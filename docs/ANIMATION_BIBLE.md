# Animation Bible - Lost & Underfound

> **Source of truth: [`BadBagger/Animation-Bible`](https://github.com/BadBagger/Animation-Bible).**
> This file is a synced local copy of that repo's `ANIMATION_BIBLE.md`, kept here so
> Codex (and anyone else working in this repo) has the rules on hand without needing
> cross-repo access. **Do not edit the rules below directly** - if a rule needs to
> change, change it upstream in `Animation-Bible`, then re-sync this file. The
> "Current status" section at the bottom is this project's own and is not synced.

A binding animation production rulebook for 2D character-animation game projects.
Project-agnostic on purpose — port this file into a new project's `docs/` as-is, then
adapt only the illustrative examples to that project's own cast if you want, never the
rules themselves.

Proven across two productions: originated on Department of Impossible Complaints
(a noir bureaucracy adventure), carried forward unchanged in substance into Lost &
Underfound (a Humongous Entertainment-style kids' adventure). The rules held for both
tones — that's the point of keeping them here instead of re-deriving them per project.

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

Every point-and-click room starts as a layered production asset, not a single poster.
The minimum stack is: background plate, environment layers, midground interactable
props, actor planes/slots, foreground occlusion, and hotspot masks. A desk character
must be designed as `desk back/wall -> actor body/hands/tools -> desk front
occluder`, not as a full-room animation patch. A gate character must be designed as
`gate back/frame -> actor -> gate bars/front latch`. If the room has to be
regenerated because one character moves, the scene source is wrong.

Each room should declare its layer contract in code or an engine manifest before new
character animation is bound. The contract names which actors live on contact-Y
sorted walk planes, which actors are fixed slots, which foreground layers occlude
them, and which object-shaped hotspot masks sit above broad surfaces. Broad
rectangular hotspots are temporary scaffolding only; production hotspots are reviewed
against the final scene plate.

## Talk-loop contract

Do not run one short six-frame talk gesture as an identical infinite treadmill for a
whole voice line. That reads as a game loop, not performance.

When only one short talk sheet exists, the engine must phase it:

- play the full gesture once, preferably as a ping-pong arc rather than a hard
  last-frame-to-first-frame snap;
- drop into a lower-amplitude settle loop using a small neutral/mid-pose subset for
  the middle of the line;
- for longer lines, re-trigger the full gesture near a phrase change or ending beat;
- vary frame holds slightly so every repeat does not land on the same metronomic
  timing;
- never use crossfade, blur, or repeated near-identical cels to disguise a missing
  gesture.

This is a code-side mitigation, not a replacement for art direction. The long-term
fix for repeated performance content is a real gesture pool: multiple registered
short talk/reaction clips per character, plus independent secondary layers such as
blinks, small eye shifts, breathing, or idle sway that do not repeat in lockstep with
the mouth/hand gesture.

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
   Pair this with a staged visible-size review: a counter, window, vehicle, or
   foreground-occluded actor can be mathematically correct as a full-body equivalent
   and still read wrong in the actual composite. Important actor pairings need a
   project-specific visible-ratio test or review note.
5. **A visual QA page before anything is called playable.**
   `tools/check_registration.py frames <sheet>/registration.json --onion-skin out.png`
   overlays every frame of a sheet on top of each other, aligned by anchor. If feet,
   head, or the contact anchor visibly jumps between frames, this is where it gets
   caught — not after it ships as a visible glitch.
6. **Animate last, not first.** 24fps timing, in-betweens, and smear frames only get
   added once a sheet has passed registration/normalization/cast-scale/QA. More
   frames on top of ungoverned registration only produces more visible drift, not
   better animation.

## Known failure definitions

These are hard rejects, even if the loop looks busy at full speed:

- **Scale drift:** an actor grows or shrinks from frame to frame while standing,
  talking, idling, or walking on the same floor position. Perspective size may change
  only when the actor's world position changes intentionally.
- **Location drift:** the actor's feet, root, counter-contact point, or furniture
  anchor slides around inside the sheet while the engine position stays fixed.
- **Detached or duplicate parts:** a spare hand, arm, hat, head, or second partial
  actor appears because a generated frame carried unwanted remnants. Quarantine the
  cel; do not hide it with speed.
- **Whole-room swap:** a resident character animation changes walls, desks, props,
  lights, windows, or the camera plate. Scene characters animate as isolated actor
  layers only.
- **Fake in-between:** a frame has the same pose as the previous frame with only
  redraw shimmer, texture noise, or tiny clothing flicker. More of these frames makes
  the animation worse, not smoother.
- **Baked contact shadow:** a frame contains its own shadow that fails to stay under
  the actor's actual root/contact point. Shadows belong to the engine or to a
  separately registered shadow layer.
- **Canvas-bottom shadow error:** an actor sheet has transparent padding below the
  feet, but the runtime treats the canvas bottom as the foot-contact point. The
  shadow then sits under empty padding instead of under the boots. Register the
  authored contact baseline and offset the sprite so the actor root is the real
  contact point.
- **Per-frame rescue crop:** a single broken cel is fixed by changing its crop,
  origin, display size, or offset differently from the rest of the sheet. Re-pad or
  redraw the art instead; every allowed cel shares the same registration contract.

## Furniture and counter actor QA

Counter, desk, booth, gate, and window actors require extra discipline because bad
layering reads immediately as pasted-on.

Before a furniture-anchored actor is admitted:

- Confirm the background plate has the actor removed or neutralized; the room cannot
  change between frames.
- Define the furniture contact/occlusion line in writing before drawing frames.
- Prove the actor's registered root/bounds physically cross the foreground
  occlusion band in the final composed scene. A counter mask that exists but does
  not overlap the actor is decorative, not functional.
- Keep torso and lower body behind the furniture mask.
- Put only the required active hands, tools, papers, or stamps above the writing or
  work surface.
- Confirm every action has named key poses: anticipation, contact/impact, follow
  through, settle, return to idle.
- Use smear frames only for fast tool movement, such as a stamp strike or pen flick;
  never for a held writing pose or ordinary dialogue.
- Review one frozen frame from every action with the UI visible. If the body covers
  the counter wrong, clips off the edge, overhangs the window, or hides behind the
  wrong layer, reject the sheet before motion review.

## Hard gate

**A frame that does not pass both `check_registration.py frames` and
`check_registration.py cast-scale` does not get merged into the game.** This is not
advisory — wire both checks into CI or, at minimum, a documented pre-merge checklist,
so every character sheet in every project that adopts this Bible goes through them
before shipping.

## Bug-to-Bible rule

When a project hits an animation, registration, staging, UI-occlusion, or
scene-compositing bug and the team finds a fix, the work is not considered fully
closed until the reusable lesson is added back to this Bible.

Do not copy project-specific drama into the shared rulebook. Generalize the learning
so the next project can use it:

- **Symptom:** what the viewer saw, such as scale drift, floating feet, a duplicate
  limb, a full-room flicker, dialogue covering a speaker, or a counter actor clipping
  through furniture.
- **Root cause:** what actually caused it, such as independent frame generation,
  wrong visible-body fraction, per-frame crop rescue, stale actor dimensions, missing
  occlusion masks, or UI placement that ignored staging.
- **Rule:** the production constraint that would have prevented it.
- **QA check:** the test, overlay, contact sheet, mobile capture, or review artifact
  that proves the bug cannot quietly return.
- **Adoption note:** which active project docs, templates, scripts, or CI checks need
  the new rule ported back into them.

If the fix only lives in code, memory, chat, or a single project branch, the lesson is
not captured. The Bible is the durable memory. Future projects should inherit the
rule before they repeat the mistake.

## Required approval evidence

Before a new animation is called playable or published as final, provide:

- A labelled contact sheet showing the key-pose purpose of every cel.
- A normal-speed loop and a half-speed loop reviewed for at least two complete cycles.
- A mobile capture confirming stable scale, anchored feet, and a shadow directly under
  the actor.
- A check that dialogue and UI do not cover the speaking character or the current
  interaction.
- A scene-composite still for every resident/furniture-anchored actor, proving the
  actor lives behind/in front of the correct furniture layers and does not overhang,
  clip, or drift.
- For generated art, a statement that the room/background was not regenerated as part
  of the character animation pass.
- Explicit review of the primary motion plus secondary motion; no crossfade, blur, or
  duplicated imagery may be used to conceal missing action. A deliberate one-cel smear
  is allowed only under the Smear-frame rule above.
- Both `check_registration.py` checks passing — no sheet is "final" while either is
  red.

## Adopting this in a new project

1. Copy `ANIMATION_BIBLE.md` (this file) into the new project's `docs/` unchanged.
2. Copy `tools/check_registration.py` into the new project.
3. Author a `registration.json` per character sheet and a project-wide
   `cast_scale.json` for the full roster — see `templates/` in this repo for annotated
   examples and the schema documented in the script's own docstring.
4. Add a "Current status" section to the project's own copy of this file (or a
   sibling doc) tracking each sheet's name and approval state
   (provisional/rejected/final) as it's produced — that history is project-specific
   and does not belong in this shared repo.
5. Wire the hard gate into CI or a pre-merge checklist before any character art is
   treated as final.

## Current status

Project-specific, not synced from upstream. This section records each sheet's name,
approval state (provisional/rejected/final), and why as sheets are produced and
reviewed. Act 1 has provisional production sheets wired into the playable scene; they
remain provisional until final human review accepts the required motion, mobile,
composite, and dialogue-staging evidence.

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

### Act 1 production visual pass

Act 1 now has a provisional production visual pass under `art/act01-production/`.
These sheets pass registration and cast-scale, include onion skins/contact sheets/loop
captures, and are wired into the playable Act 1 scene. They are still marked
provisional because final human approval requires reviewing the evidence listed above.

| Sheet | Actor type | State | Evidence |
|---|---|---|---|
| `art/act01-production/characters/pip/walk` | walk-plane | provisional-production/pass | 9-role walk-cycle contract sheet; `npm run qa:prod:pip-walk` passes. |
| `art/act01-production/characters/pip/idle` | walk-plane | provisional-production/pass | Alive held idle; `npm run qa:prod:pip-idle` passes. |
| `art/act01-production/characters/pip/dust-reach` | walk-plane | provisional-production/pass | Anticipation/reach/found reaction; `npm run qa:prod:pip-dust` passes. |
| `art/act01-production/characters/pip/toll-paid` | walk-plane | provisional-production/pass | Relief/excitement reaction; `npm run qa:prod:pip-toll` passes. |
| `art/act01-production/characters/bramble/idle` | furniture-anchored | provisional-production/pass | Desk-fixed layered work loop; `npm run qa:prod:bramble-idle` passes. |
| `art/act01-production/characters/bramble/talk` | furniture-anchored | provisional-production/pass | Talk loop that interrupts idle; `npm run qa:prod:bramble-talk` passes. |
| `art/act01-production/characters/old-bottlecap/idle` | furniture-anchored | provisional-production/pass | Slow heavy rock loop; `npm run qa:prod:bottlecap-idle` passes. |
| `art/act01-production/characters/old-bottlecap/toll-refused` | furniture-anchored | provisional-production/pass | Small deadpan head-shake; `npm run qa:prod:bottlecap-refused` passes. |
| `art/act01-production/characters/old-bottlecap/toll-paid` | furniture-anchored | provisional-production/pass | Button take/inspect/approval beat; `npm run qa:prod:bottlecap-paid` passes. |
| `art/act01-production/characters/scuttle/dash` | walk-plane | provisional-production/pass | Solid pre/post poses plus one smear cel; `npm run qa:prod:scuttle-dash` passes. |
| `art/act01-production/props/dust-clump-reveal` | furniture-anchored prop | provisional-production/pass | Squash/stretch reveal; `npm run qa:prod:dust` passes. |
| `art/act01-production/props/grate-open` | furniture-anchored prop | provisional-production/pass | Mechanical lift/open frames; `npm run qa:prod:grate` passes. |

`npm run qa:cast` passes against the full declared cast at 220 px/world unit with Act
1 production sheets for Pip, Bramble, Scuttle, and Old Bottlecap, and the existing
Grommet placeholder.

