# Act 1 Layering And Scene Cohesion Contract

Act 1 is not a flat screenshot with sprites pasted on top, but it is also not a
pile of orphaned transparent props. The room must read as one authored world.

Revised principle: the opaque background plate owns everything an actor never
sorts behind. Only true occluders, actor slots, animated props, and foreground
partial-alpha elements stay separate.

Current generated production pack:

- `art/act01-production/scene/layered-v2/bg_room.png` - opaque furnished room
  plate.
- `art/act01-production/scene/layered-v2/occluders/desk_front.png` - transparent
  desk front/top occluder for Bramble.
- `art/act01-production/scene/layered-v2/occluders/gate_front.png` - transparent
  gate bars/latch occluder for Old Bottlecap.
- `art/act01-production/scene/layered-v2/cobweb.png` - transparent foreground
  partial-alpha web.
- `art/act01-production/scene/layered-v2/fx/soft_oval_shadow.png` - reusable
  contact-shadow sprite.
- `art/act01-production/scene/layered-v2/qa/partial-alpha-dark-check.png` -
  dark-background cobweb/dust alpha QA.
- `art/act01-production/scene/layered-v2/qa/assembled-scene.png` - current
  Forge composite screenshot for review.

Do not split background furniture just because it is furniture. The cubby shelf,
bookcase, wall dressing, floor, ceiling, far gate opening, and non-sortable junk
belong in `bg_room.png` so they share light, perspective, and value.

Keep separate only:

1. Actor occluders: desk front, gate front, and any future furniture face an
   actor can be behind.
2. Animated props: dust reveal, button states, opening grate.
3. Foreground partial-alpha elements: cobweb curtain and similar wispy overlays.
4. Runtime-only integration layers: contact shadows and global post pass.

Scene blocking guidance from the user's adventure-game references:

- Build the room around readable stage planes before generating assets.
- Each actor needs a clear standing/sitting baseline and a visible floor or
  ledge contact point.
- Large set pieces should frame actor positions, not compete with them.
- Foreground occluders should have a compositional reason: desk counter, gate
  bars, overhanging frame, curtain, or similar.
- Character scale is judged against furniture first. Pip's scene height is the
  reference; counter height should hit around torso if Pip stands behind it.
- Lighting is a scene contract. The master key for this room is warm
  upper-left, and every generated cutout must match it.

Forge integration requirements:

- Actor source-art scale stays canonical: Pip `1.0`, Bramble `0.85`, Old
  Bottlecap `0.6`, Scuttle `0.35`, Grommet `2.4` deferred.
- Scene placement calibrates those actors to the room. Do not rescale individual
  animation frames.
- Contact shadows are runtime layers drawn at actor/prop baselines. Do not bake
  shadows into actor or prop art.
- Color grade, vignette, and grain are one runtime post pass over the composed
  scene. Do not bake them into individual PNGs.
- Cobweb and dust dispersal tails preserve partial alpha. Check them over a dark
  background before committing.

`forge/lost-underfound-act1.forge.json` is the active truth for the current
playable export. The AdventureForge browser test asserts the active layer list,
scale calibration, post pass, dynamic shadow asset, depth ordering, and Act 1
playthrough.

Character model source for the current Act 1 production pass is:

- `art/act01-production/source/character-reference-sheet.png`

Generated model-sheet cutouts are normalized into registered canvases. If scene
placement is wrong, adjust the actor slot or layer plane. If the model drawing
itself is wrong, replace the model-sheet source/crop and regenerate.
