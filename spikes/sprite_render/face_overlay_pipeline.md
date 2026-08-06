# Face Overlay Pipeline Decision

## Decision

Use Meshy's baked texture for game-scale body color and simple open/blink face
states. Use deterministic 2D face elements attached to the rendered 3D head for
talking, closeups, and any expression where eyes/irises/mouth need to act.

## Why

The textured animated GLB fixed the structural color bug: costume and skin colors
now move with the mesh instead of sliding in screen space. A normal/blink texture
swap also works for full-body walking sprites because the face is small and the
blink remains bound to the head.

Talking still needs authored 2D face elements. A texture-only face cannot drive
Rhubarb visemes, pupil direction, or expression beats cleanly, and scripted UV
mouth painting can create stray marks when the generated atlas rotates or
fragments the face islands.

## Production Goal

Each game character render has two cooperating layers:

1. `body`: Blender-rendered textured mesh, palette-quantized, registered to the
   character anchor.
2. `face`: optional 2D face cards attached to a tracked face anchor.

The face overlay is the authority for eyes open/half/closed, pupil direction,
brows, nose, mouth visemes A-F, and special expressions whenever a character is
talking or framed large enough for the face to read.

This matches the production pattern shown in the user's 2D-face-on-3D-head
reference: the model stays 3D for body motion, while the expression language is
handled by flat, authored 2D facial elements stuck to the head.

## Face Anchor Data

Every rendered frame manifest must include a face anchor:

```json
{
  "frame": "walk_000.png",
  "body_anchor": [256, 480],
  "face_anchor": {
    "center": [258, 171],
    "scale": 1.0,
    "rotation_degrees": -3.5
  }
}
```

The anchor is derived from a Blender head bone or a named empty/socket projected
into the render camera. Current Meshy biped exports include usable `Head`,
`head_end`, and `headfront` bones. A raw bone is not automatically the artistic
face center, so the renderer may apply a model/rig-space adjustment before
projection, such as lifting from `headfront` along the animated `neck` -> `Head`
vector.

Do not solve face placement with fixed 2D pixel offsets in production. Pixel
offsets are camera-angle-specific and will break across turnarounds. If a future
mesh lacks a reliable facial socket, add one in Blender once and keep it with
the source asset.

## Composition Order

1. Render body from Blender using source texture.
2. Cut to alpha and align to fixed canvas.
3. Quantize body to the legal hero palette.
4. Composite face overlays at `face_anchor`.
5. Run the final warm outline pass over body plus face together, or draw a
   dedicated face-line overlay if the global outline is too heavy.

Do not outline the body before adding the face, because the face must share the
same final line language.

## Face Proportions

Use simple portrait spacing rules as the default overlay layout:

- eyes sit near the vertical midpoint of the visible face area,
- combined eye width is materially narrower than the face opening, not the full
  face width,
- nose sits roughly halfway between eye line and chin,
- nose width tracks the inner eye spacing,
- mouth sits roughly halfway between nose and chin,
- mouth corners align near the pupils.

These rules are adapted from standard drawing-proportion guidance, including the
Sketchbook Nation face-spacing lesson used for this pass. The exact proportions
may be stylized per character, but they must remain relative to measured head
size rather than fixed pixels.

Review contact sheets must not draw anchor crosshairs over the face by default.
Anchor/debug guides belong in a separate debug sheet so they do not masquerade as
facial features.

Face parts are real assets, not procedural circles, once a character enters
production. Each character/view needs its own face asset set:

- front / near-front face assets for front-ish poses,
- 3/4 face assets for 3/4 poses,
- side-profile assets for side poses and turnarounds.

Do not reuse front-facing eye pairs on a profile turn and call it final. It is
acceptable in a spike, but production admission requires the asset set to match
the rendered view.

Important scale rule: face overlays are not mandatory for gameplay-scale walk or
idle sprites. First compare texture-only and overlay versions at the final room
scale. If the overlay is not materially more readable in-room, prefer the
texture-bound normal/blink face and spend effort on body acting, timing, and
gait. Reserve overlay systems for closeups, talking heads, or failed
texture-only expressions.

## Texture Variant Blink Path

For gameplay-scale sprites, the preferred middle path is texture variants:

- `normal` texture: open eyes, readable irises/pupils, readable mouth.
- `blink` texture: same texture with closed eyelids painted on the UV map.
- Optional `talk` or `surprise` textures only when a state truly needs them.

The renderer may swap the material image on selected frame indexes, such as
`--base-texture <png> --blink-texture <png> --blink-frames 9-10`. This keeps
face details bound to the model and camera while avoiding a full 2D per-view
overlay system for ordinary walk/idle.

Production note: use Meshy retexture or a real texture-paint pass to create
these texture variants. Scripted UV edits are acceptable only as proofs because
Meshy UV placement can change by export.

Do not use scripted UV painting for talk mouths in production. If the mouth must
animate, use the 2D face-card system below.

## Talk Animation

Talk is not a baked mouth-flap cycle. The body runs a subtle talking-base loop:
head/body breath, small brow/eye movement, and hand/shoulder gesture if the
state calls for it.

The mouth channel stays independent and is driven by Rhubarb viseme output for
voiced dialogue, or by a deterministic text-length mouth-flap fallback for
text-only lines.

Required mouth shapes:

- `mouth_A_closed`
- `mouth_B_open_small`
- `mouth_C_open_wide`
- `mouth_D_ee`
- `mouth_E_oo`
- `mouth_F_rest`

## Blink Animation

Blink is a separate timed channel, not part of the body render:

- open hold,
- half-close for 1 frame,
- closed for 1-2 frames,
- half-open for 1 frame,
- return open.

Blink timing may jitter slightly per loop, but the sprite registration cannot
move.

## Admission Gate

A production talk or closeup clip fails admission if:

- any frame lacks `face_anchor`,
- no open-eye overlay is present,
- no closed-eye overlay is present,
- no mouth/viseme overlay is present for talk-capable characters,
- the visual QA contact sheet shows missing eyes, nose, or mouth at gameplay
  size.

Gameplay-scale walk/idle clips may be admitted with texture-bound open/blink
states if the visual QA contact sheet proves eyes and blink read at final room
scale and the clip does not need lip-sync or expression acting.
