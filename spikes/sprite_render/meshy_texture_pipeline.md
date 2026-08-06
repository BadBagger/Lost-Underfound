# Meshy Texture Pipeline Decision

## Decision

Use Meshy's own texturing/export pipeline for character color. Do not use
BlenderKit/PBR materials as the production color path for this 3D-to-2D sprite
spike.

## Why

The target render is flat two-tone cel/posterized art with hard boundaries and a
warm outline. BlenderKit materials are realistic PBR assets: weave normals,
roughness maps, subsurface/reflectance behavior, and high-frequency detail. The
post pass quantizes the render to `palette.json` and outlines it, so most PBR
material detail is discarded.

The correct color authority is the generated character texture, because Meshy
has the strongest understanding of its own mesh regions: face, suit, belly,
hands, horns, and shoes. Manual region rebuilding from the static segmentation
FBX is a detour and does not scale to the full cast.

## Required Meshy Export

Export a textured version of the animated character where the animation file
keeps the mesh texture/material assignment.

Preferred:

- Textured `.fbx` or `.glb`
- Animated, equivalent to `*_Animation_*_withSkin`
- Includes or embeds:
  - image texture files, or
  - material slots with texture nodes, or
  - vertex colors

Current local export status:

- `spikes/sprite_render/input/Meshy_AI_Little_Monster_in_a_B_biped/` contains
  only `.fbx` files.
- No local `.png`, `.jpg`, `.jpeg`, `.webp`, `.tga`, `.bmp`, `.tif`, `.tiff`, or
  `.exr` texture files were present.
- The animated walking FBX imports as a brown/neutral mesh in source mode because
  it has no usable material slots, texture image, or vertex color colorway.
- A Meshy-native textured static GLB has now been exported to
  `spikes/sprite_render/input/meshy_textured/Meshy_AI_Head_and_shoulders_po_0805160857_texture.glb`.
  Blender imports it with `UVMap`, material slot `material`, and a packed
  2048 x 2048 image texture named `base_color`. This confirms the correct color
  authority path.
- A textured animated Meshy ZIP has now been exported to
  `spikes/sprite_render/input/meshy_textured_animated/Meshy_AI_Head_and_shoulders_po_biped.zip`.
  Its extracted `walking_textured.glb` short-path copy imports in Blender with
  `UVMap`, material slot `Material_1`, a packed 2048 x 2048 image texture named
  `texture_0`, a 24-bone armature, and action
  `Armature|walking_man|baselayer`.

## Blender Render Path

Keep:

- Corrected 3/4 camera.
- Full-body framing.
- Flat lighting.
- No cast shadows.
- Source material mode.
- Palette quantization after render.
- Warm outline after quantization.

Do not:

- Apply screen-space color overlays.
- Infer body colors from mesh coordinates as the normal production path.
- Rebuild part zones manually from the static segmentation mesh unless it is a
  one-off diagnostic.
- Use BlenderKit/PBR materials for character identity color.

## Acceptance

A Meshy export is usable when `render_fbx_walk.py --material-mode source`
produces a source render with body-attached regions:

- blue suit/costume,
- teal belly/accent,
- warm face/hands,
- darker shoes,
- no color sliding during animation.

Then `postprocess_sprite.py` may quantize and outline the render into the game
palette.

This is body-color acceptance only. Production facial acting is owned by the
separate face overlay pipeline in `face_overlay_pipeline.md`. A Meshy texture
that lacks readable eyes, nose, or mouth is not a final sprite failure by itself,
but it means the clip cannot be admitted until deterministic face overlays and
face anchors are present.

Palette QA must exclude transparent pixels, outline pixels, and background-like
dark pixels before computing character color coverage. The outline cannot be
allowed to make a wrong-color body pass.

Current proof files:

- `spikes/sprite_render/textured_proof/frames_raw/walk_raw_000.png`
- `spikes/sprite_render/textured_proof/texture_source_crop.png`
- `spikes/sprite_render/textured_proof/texture_R2_palette.png`
- `spikes/sprite_render/textured_proof/texture_R3_outline.png`
- `spikes/sprite_render/textured_proof/texture_proof_manifest.json`
- `spikes/sprite_render/textured_walk_proof/textured_walk_R3_contact.png`
- `spikes/sprite_render/textured_walk_proof/textured_walk_R3_preview.gif`
- `spikes/sprite_render/textured_walk_proof/textured_walk_manifest.json`
