# Spec: Dynamic Baseline Depth Sorting

Companion implementation spec for `ANIMATION_BIBLE.md`'s "layered point-and-click
scene stack" and "Furniture and counter actor QA" sections. Those sections establish
the principle — rooms declare a layer contract naming "which actors live on
contact-Y sorted walk planes," and furniture-anchored actors must "prove the
actor's registered root/bounds physically cross the foreground occlusion band."
This spec is the concrete algorithm and data model that makes contact-Y sorting a
real, general system instead of a principle every project re-implements by hand.

## Problem this replaces

Every scene-occlusion case in the existing projects is currently hand-solved with a
fixed `setDepth()` call. `department-impossible-complaints/src/main.ts` sets Quire's
sprite to a hardcoded `setDepth(2)`, the protagonist's container to
`setDepth(3 + y / 100)` (a partial, ad hoc Y-based nudge), and furniture-anchored
NPCs generally to a fixed constant. This is exactly the class of bug the Bible's
"Furniture and counter actor QA" section now checks for by hand, per frame, per
review — this spec's job is to make the check pass structurally instead of by
review discipline alone.

Established adventure-game tools (Adventure Game Studio, PowerQuest) solve this with
one general mechanism: **every renderable thing in a scene has a baseline, and draw
order is baseline order.** Build this once, and the counter-clip bug class becomes
structurally impossible instead of something a reviewer has to catch by eye.

## Data model

Extend the scene data format (in `department-impossible-complaints` this is
`scene-data.ts`'s `SceneDefinition`; in any project adopting this fresh, the
equivalent scene/room definition) with a `walkBehinds` array:

```ts
type WalkBehind = {
  id: string;
  mask: string;          // path to an alpha-mask image cut from the background plate,
                          // OR a polygon (see "mask formats" below)
  baseline: number;       // the Y-coordinate (in scene space) below which an actor
                          // draws IN FRONT of this mask, above which BEHIND it
};

type SceneDefinition = {
  // ...existing fields...
  walkBehinds: WalkBehind[];
};
```

A **fixed/furniture-anchored character** (Quire, Bramble, Old Bottlecap) is not a
special case in this system — it's just an actor whose baseline never changes,
authored once as a constant matching where its feet/base would be if it could move.
This unifies "walking character" and "fixed NPC" into the same sort, instead of the
fixed NPC being hand-tuned separately.

### Mask formats

Two acceptable approaches, pick one per project and stay consistent:

1. **Alpha-mask image** — a same-canvas-size image where the walk-behind object
   (a pillar, a desk edge, a counter front) is opaque and everything else is
   transparent, painted as a separate layer split out of the background plate at
   authoring time. This is what AGS does. Simple to author, simple to render (draw
   the mask sprite at the computed depth, it visually occludes anything behind it).
2. **Polygon** — an array of `{x, y}` points defining the occluding region, rendered
   as a clip mask. More flexible for procedural/resizable UI but harder to author by
   hand for organic shapes (a desk with a curved edge). Prefer alpha-mask for scene
   furniture, reserve polygon for simple geometric cases.

Start with alpha-mask — it matches how the background art is already produced
(painted scenes, not vector shapes).

## Algorithm

1. On scene load, register every `WalkBehind` as a sprite at its `mask` image,
   positioned to align exactly with where it was cut from the background plate, with
   `setDepth(baseline)`.
2. Every actor (walking or fixed) gets `setDepth(currentY)` — recomputed whenever
   its Y changes (on movement, not every render frame — this is a cheap operation,
   no need to run it in the render loop for actors that aren't currently moving).
3. UI, dialogue, and HUD elements stay in a reserved depth band **above** all scene
   content — `department-impossible-complaints` already does this correctly (UI at
   depth 20-33, scene content below), keep that convention, don't let scene depth
   values ever grow into the UI band. Pick a numeric ceiling for scene depth (e.g.,
   scene content capped under 15) and assert it in the same QA pass that checks
   walk-behind masks.
4. No two elements should render at exactly the same computed depth in a way that
   creates ambiguous stacking (a walking character's foot Y landing exactly on a
   mask's baseline) — either accept Phaser's stable-sort tie-breaking (later-added
   wins) deliberately, or nudge baselines by a small fixed epsilon per mask so ties
   can't happen; pick one and document which.

## Authoring/QA tooling

Two additions, in the same spirit as `check_registration.py`:

1. **A visual debug overlay**, toggled by a dev flag, that draws a horizontal line
   at every walk-behind mask's baseline Y and labels it with the mask's `id`. This
   lets a scene author see exactly where the front/behind boundary sits while
   placing masks, instead of guessing and eyeballing the result after the fact.
2. **An automated completeness check**: every `WalkBehind` entry has a `baseline`
   value that falls within the scene's canvas height (not accidentally off-frame),
   and every fixed-position character's authored baseline is a real, intentional
   number (not a leftover copy-paste default). Fold this into the existing
   registration-tooling suite as a third subcommand
   (`check_registration.py scene-depth <scene-data-file>`) rather than a separate
   tool, since it's the same "declared data must actually be internally consistent"
   category of check.

## Migration path for existing fixed-depth code

For `department-impossible-complaints` specifically: Quire's `setDepth(2)` becomes
`setDepth(<his authored fixed baseline>)`, computed once at the same time his
counter-contact anchor is established (same registration pass, same source of
truth — the anchor Y and the depth baseline should be derived from the same
authored number, not two independently-guessed constants that could drift apart).
The protagonist's existing `3 + y / 100` hack gets replaced with a real
`setDepth(y)` once walk-behind masks exist to sort against — right now there's
nothing in the lobby scene for her to walk behind, so the partial hack has been
invisible, but it will start mattering the moment a walk-behind mask (a pillar, a
desk corner) is added to any scene.
