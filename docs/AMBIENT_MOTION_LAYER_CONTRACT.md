# Ambient Motion-Layer Contract

Ambient motion is allowed only as a separate non-interactive layer. It is for low-intensity room life: dust drift, tiny light tremor, and subtle air movement. It is not a character, hotspot, occluder, cutscene effect, or puzzle state.

## Layer Position

- Draw above `background-plate`.
- Draw below `dust-prop`, `gate-animation`, all actor bodies, and all actor shadows.
- Draw below `post-pass`.
- Never draw above `hotspot-masks`.

## Interaction

- Ambient layers must use `pointer-events: none`.
- Ambient layers must not contain buttons, exits, labels, or dialogue.
- Ambient layers must not change hotspot geometry or screen blocking.

## Motion Limits

- Motion must be subtle enough that it does not read as actor movement.
- Default maximum visible drift: 4px at 1280x720 room scale.
- Default opacity range: 0.04 to 0.16.
- Looping motion must be slow and phase-offset, not a fast repeated cycle.

## Runtime Contract

The runtime must expose a `data-layer="ambient-motion"` slot. The scene layer manifest must declare that slot as `kind: "ambient-motion-layer"`.

Dedicated future ambient sprite loops still need animation-admission review before they become production art. CSS-only drift is allowed as a temporary runtime treatment because it has no character registration footprint.

## World-Building Clips

Small world-building loops are allowed in the ambient layer: tiny spiders, tag sway, lamp glow, dust motes, loose-string movement, and far-background tremor hints. They must be declared in `ags/ambient_motion_layers.json` with screen, position, frame count, FPS, opacity, and movement limits.

- Minimum loop length: 6 frames.
- Default maximum FPS: 5.
- Ambient creatures must stay out of the walk plane and must not read as interactable NPCs.
- Hanging props must keep their top anchor visually stable.
- Light/glow clips must remain subtle and must not look like an explosion, puzzle solve, or cutscene flash.
- All ambient clips must be non-interactive and draw below actors, props, dialogue, exits, and hotspot masks.
