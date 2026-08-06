# 3D-to-2D Sprite Render Spike

## Inputs

- Source zip: `C:\Users\KyleB\Downloads\Meshy_AI_Little_Monster_in_a_B_biped.zip`
- Walking FBX: `spikes/sprite_render/input/Meshy_AI_Little_Monster_in_a_B_biped/Meshy_AI_Little_Monster_in_a_B_biped_Animation_Walking_withSkin.fbx`
- Textured static GLB proof: `spikes/sprite_render/input/meshy_textured/Meshy_AI_Head_and_shoulders_po_0805160857_texture.glb`
- Textured animated walk GLB proof: `spikes/sprite_render/input/meshy_textured_animated/walking_textured.glb`
- Plate used for composite/palette reference: `ags/room1/background/discovery.png`

## Render Settings

- Blender: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`
- Headless command: `blender --background --python spikes/sprite_render/render_fbx_walk.py`
- FPS: 12
- Camera: orthographic, side-biased 3/4 profile, 8 degrees above horizontal
- Framing: full-body with explicit orthographic height padding
- Material mode: source mesh materials/vertex colors only; no coordinate-inferred materials in the normal path
- Shadows: no cast shadows
- Gait: unchanged from source FBX

## Outputs

- `spikes/sprite_render/out/walk_R1.png` - full-body source-material render
- `spikes/sprite_render/out/walk_R2.png` - R1 quantized to nearest `palette.json` hero entry per pixel
- `spikes/sprite_render/out/walk_R3.png` - R2 plus warm dark outline
- `spikes/sprite_render/out/contact_R1.png`
- `spikes/sprite_render/out/contact_R2.png`
- `spikes/sprite_render/out/contact_R3.png`
- `spikes/sprite_render/out/composite_R1.mp4`
- `spikes/sprite_render/out/composite_R2.mp4`
- `spikes/sprite_render/out/composite_R3.mp4`
- `spikes/sprite_render/out/sprite_only_R3.mp4`
- `spikes/sprite_render/out/walk_offsets.json`
- `spikes/sprite_render/blender_render_metadata.json`
- `spikes/sprite_render/input/meshy_textured/textured_glb_inspection.json`
- `spikes/sprite_render/input/meshy_textured_animated/walking_textured_glb_inspection.json`
- `spikes/sprite_render/textured_proof/texture_R3_outline.png`
- `spikes/sprite_render/textured_proof/texture_proof_manifest.json`
- `spikes/sprite_render/textured_walk_proof/textured_walk_R3_contact.png`
- `spikes/sprite_render/textured_walk_proof/textured_walk_R3_preview.gif`
- `spikes/sprite_render/textured_walk_proof/textured_walk_manifest.json`

## Measurements

- Frames rendered: 12
- Sheet size: 1332 x 179 for R1/R2/R3
- Individual normalized frame size: 111 x 179, with 143px actor content height plus padding
- Composite clips: 1280 x 720, 12 fps, 3 seconds
- Sprite-only R3 clip: 640 x 360, 12 fps, 3 seconds

## Palette Coverage

Palette comes from `spikes/sprite_render/palette.json` because no root `palette.json` exists. Postprocess quantizes each rendered pixel to the nearest `hero` palette entry.

- R1: 0.00% within RGB distance 12 - fail
- R2: 100.00% within RGB distance 12 - pass
- R3: 95.05% within RGB distance 12 - pass

## Root Motion Assessment

The imported walk clip is effectively in-place for engine purposes.

- Armature object location delta: 0.0
- Root bone span: x 0.0546, y 0.0377, z 0.0424 Blender units
- Root bone start-to-end distance: 0.0327 Blender units

Interpretation: the character does not translate through the scene at the armature/object level. The root bone has small cyclical sway, but movement in-game should be driven by AGS/Godot character position, not by extracting FBX root motion.

## Visual Verdict

R3 is the most useful treatment for this plate because the warm dark outline makes the render sit closer to the painted room style while preserving body-attached source-inspired colors. R1 is cleaner as a material/color control but reads more 3D. R2 keeps palette discipline but lacks the stronger edge language.

The full body is visible in every frame, the sprite has been scaled down to the 143px actor-height target, and the render is no longer front-on. The normal render path now uses the mesh's imported source material data only. It does not use coordinate-inferred materials.

The animated FBX has UVs, but no imported material slots, no image texture, and no vertex color attributes. Result: source mode honestly renders the brown/neutral mesh. R2/R3 then correctly quantize/outline that source render, but they cannot recover blue costume/teal belly zones that are absent from the animated FBX.

The part-segmentation FBX helps identify regions, but it is static and has one missing/fragmented hand. It should be used for diagnostics only, not as final texture authority and not as the basis for a manual per-character material-zone workflow. The next quality step is exporting the actual Meshy textured animated asset, then rendering source mode again. The gait remains adult/stock-animation-like; this spike intentionally did not correct gait.

## Meshy Texture Proof

The Meshy-native texture route now works for a static GLB. Blender imports
`spikes/sprite_render/input/meshy_textured/Meshy_AI_Head_and_shoulders_po_0805160857_texture.glb`
with:

- mesh `mesh_node`
- `UVMap`
- material slot `material`
- packed `base_color` image texture at 2048 x 2048

The proof render at `spikes/sprite_render/textured_proof/texture_R3_outline.png`
uses source mesh material data, then palette quantization and the warm outline.
This fixes the screen-space color bug: color zones are now attached to the body
texture and will move with the mesh.

The static GLB has no armature or actions, but the follow-up Meshy animation ZIP
does preserve the important data. The short-path copy
`spikes/sprite_render/input/meshy_textured_animated/walking_textured.glb`
imports in Blender with:

- mesh `char1`
- `UVMap`
- material slot `Material_1`
- packed `texture_0` image texture at 2048 x 2048
- armature `Armature` with 24 bones
- action `Armature|walking_man|baselayer`

The animated R3 proof is
`spikes/sprite_render/textured_walk_proof/textured_walk_R3_contact.png` and the
loop preview is
`spikes/sprite_render/textured_walk_proof/textured_walk_R3_preview.gif`.

The proof confirms the production path: Meshy texture -> textured animated GLB
-> Blender source-material render -> palette quantization -> warm outline. The
remaining quality issue is animation direction, not material binding. This walk
is still a Meshy stock/adult gait and should be treated as a pipeline proof, not
final Pip acting.

## Assumptions

- `[ASSUMPTION]` No root `palette.json` was present, so this spike uses `spikes/sprite_render/palette.json`.
- `[ASSUMPTION]` Palette validation uses RGB distance against an extracted palette, not CIE dE, because the referenced validation tool is absent.
- `[ASSUMPTION]` The exported offset schema in `walk_offsets.json` is a local matte-compatible report rather than an integration target, because no matte tool was available.
- `[ASSUMPTION]` The animated FBX contains UVs but no texture image, material slots, or vertex color attributes. Source mode therefore cannot show blue/teal source colors until a textured Meshy animation export is supplied.
- `[ASSUMPTION]` The Meshy walking motion remains a pipeline proof, not final acting; final Pip still needs a game-specific walk/idle performance.

## Face / Acting Gate

The textured walk proof is not admitted as a production sprite because the face
is not readable at game size: eyes, nose, and mouth detail are missing or too
weak after render, palette quantization, and outline.

Production goal: keep Meshy/Blender as the body-motion layer and add a
deterministic 2D face overlay rig attached to a per-frame `face_anchor`. The face
overlay supplies eyes open/half/closed, pupils, brows, nose, and Rhubarb-ready
mouth visemes A-F. Talk animation is a body/brow/eye loop with an independent
mouth channel, not a baked texture-only flap.

The detailed contract is in
`spikes/sprite_render/face_overlay_pipeline.md`.

Implemented proof files:

- `spikes/sprite_render/socket_walk_render/blender_render_metadata.json`
- `spikes/sprite_render/socket_face_overlay_proof/face_overlay_manifest.json`
- `spikes/sprite_render/socket_face_overlay_proof/talk_face_contact.png`
- `spikes/sprite_render/socket_face_overlay_proof/talk_face_preview.gif`

The renderer now projects the Meshy `headfront` bone into camera pixel space and
records `face_anchor_samples` per rendered frame. The compositor can consume
those anchors directly. This proves the correct technical approach: socket-bound
face overlays, not texture-only facial detail and not alpha-bbox guessing. The
current overlay art is a proof layer only; final Pip art still needs approved
face drawings for eyes, brows, nose, and mouth visemes.

Follow-up correction: the raw `headfront` point was too low for the artistic face
center, and a fixed `-18px` overlay lift was rejected because it is
camera-angle-specific. The current socket proof instead applies a model-space
lift before projection:

- `--face-anchor-bone headfront`
- `--face-anchor-up-units 0.23`
- no 2D overlay pixel offset

This keeps the correction in rig/model space, so it can survive alternate camera
views and turnarounds.

## Gameplay-Scale Face Verdict

The decisive comparison is now rendered on the approved AGS discovery plate at
the geometry reference height:

- `spikes/sprite_render/gameplay_scale_proof/texture_vs_overlay_contact.png`
- `spikes/sprite_render/gameplay_scale_proof/texture_only_preview.gif`
- `spikes/sprite_render/gameplay_scale_proof/face_overlay_preview.gif`

Settings:

- Plate: `ags/room1/background/discovery.png`
- Actor height: 230px, from `ags/room1/geometry.json`
- Foot position: `[660, 666]`

Verdict: at actual gameplay scale, the texture-only face is already carrying the
readable head/face impression. The overlay adds little visible benefit and adds
substantial production cost: per-view eye assets, blink states, mouth states, and
socket calibration for every character. Therefore face overlays should not be a
mandatory requirement for gameplay-scale walking sprites.

Recommended production split:

- Gameplay-scale walk/idle: use Meshy texture-bound face unless a specific state
  visibly fails at true scale.
- Dialogue/talking-head closeups: use deterministic 2D face overlays or a
  separate 2D rig, because the face is large enough for expression detail to
  matter.
- QA rule: judge face systems at final in-room scale before approving any added
  overlay complexity.

## Texture Variant Blink Proof

Implemented renderer support for a texture-bound blink path:

- `render_fbx_walk.py --blink-texture <png> --blink-frames 9-10`
- Extracted base packed texture:
  `spikes/sprite_render/texture_variants/otto_base_texture.png`
- Generated proof blink texture:
  `spikes/sprite_render/texture_variants/otto_blink_texture_proof.png`
- Rendered proof:
  `spikes/sprite_render/blink_texture_render/frames_raw/`
- Gameplay-scale proof:
  `spikes/sprite_render/blink_texture_gameplay_proof/texture_only_contact.png`

Result: material texture swapping works and records frame states in metadata.
The scripted UV paint proof did not visibly create a readable blink at gameplay
scale, which means the UV edit likely missed or under-hit the face island. Do
not keep guessing UV coordinates. Production should create the `normal` and
`blink` textures through Meshy retexture or a real texture-paint pass, then use
the renderer's texture-swap path.

## Color QA Revision

The prior palette pass was too permissive because dark outline/background pixels
could dominate the census and still count as legal palette coverage. The new
QA script, `spikes/sprite_render/check_sprite_visual_qa.py`, excludes outline,
room-dark, and hair-like dark pixels before checking character color shares. It
also fails production checks when a face overlay is required but missing.

Current visual QA output:

- `spikes/sprite_render/textured_walk_proof/visual_qa.json`
- Frames measured: 12
- Result: fail, as intended
- Dominant color excluding outline/background: `teal_belly`
- `blue_costume` share: 16.866%, below the 25% minimum
- `warm_highlight` share: 12.608%, above the 1% maximum
- Missing face overlay warning: present

## Dialogue / Cutscene Otto Proof

Implemented the first mid-shot dialogue proof for Otto:

- Stable body render from the textured animated GLB using `--still-frame 1`
  and `--frame-count 24`, so the dialogue proof does not accidentally inherit
  walk-cycle body motion.
- Deterministic 2D face-card overlay driven by the Blender-projected
  `headfront` anchor, with open/half/closed eyes, nose, and mouth shapes A-F.
- 1280 x 720 cutscene composite over the clerk room plate with softened
  background and a bottom dialogue bar.

Outputs:

- `spikes/sprite_render/dialogue_otto_bust_render/`
- `spikes/sprite_render/dialogue_otto_face_overlay/`
- `spikes/sprite_render/dialogue_otto_scene/dialogue_scene_preview.gif`
- `spikes/sprite_render/dialogue_otto_scene/dialogue_scene_contact.png`
- `spikes/sprite_render/dialogue_otto_scene/dialogue_scene_002.png`

Verdict: this is the correct lane for dialogue. Texture-bound face detail can
serve walking/idle at room scale, but dialogue/cutscene Otto should use 2D face
cards attached to the 3D head. The current face-card art is still proof art, but
the render/composite architecture is sound.

Known follow-up: replace the current generic face-card PNGs with Otto-specific
painted face assets and drive mouth shapes from Rhubarb or a dialogue-timing
track instead of the current deterministic A-F cycle.

## Dialogue Portrait Gate

Implemented the first 1920 x 1080 Otto portrait gate still using the cutscene
framing direction: large cropped bust on the right third, room plate softened
behind him, and enough empty stage space on the left for a second speaker.

Outputs:

- `spikes/sprite_render/dialogue_portrait_source_fullbody/frames_raw/walk_raw_000.png`
- `spikes/sprite_render/dialogue_portrait_source_fullbody/blender_render_metadata.json`
- `spikes/sprite_render/dialogue_portrait_gate/otto_portrait_gate_still.png`
- `spikes/sprite_render/dialogue_portrait_gate/otto_portrait_gate_sprite_r3.png`
- `spikes/sprite_render/dialogue_portrait_gate/portrait_gate_report.json`

The still deliberately uses the textured face only. It does not create final
2D dialogue face cards yet, because the dialogue portrait brief requires the
camera/framing/render tier to be approved before face asset production begins.

Follow-up correction: the Meshy textured GLB is now treated as the visual
authority for Otto. Synthetic costume/face repair in the portrait compositor was
removed after it proved to be reshaping an already-correct belly patch and face.
The current source-outline gate renders the textured GLB as-is and applies only
the warm outline in post. Strict palette quantization remains available as a
control, but it is not the default portrait treatment because nearest-palette
snapping can turn valid blue costume shading into cyan.

Measured display targets from the current gate:

- Display portrait height: 1220px
- Estimated display face width: 199.61px
- Single sclera target: 29.93-35.94px
- Eye-center separation target: 87.82px
- Pupil target: 3.59-5.0px, roughly 1:7 against sclera width

Current painterly sprite census:

- Costume blue share within RGB distance 32: 43.38%
- Teal belly share within RGB distance 32: 7.6%
- Dark border share: 82.57%
- Palette pass within RGB distance 32: 66.29%

The lower palette pass is expected for this treatment because the sprite is no
longer hard-quantized. Dialogue portrait QA should separately check color-role
dominance and outline coverage instead of reusing the flat-cel palette gate.

The source texture contains a stray teal shoulder/chest region. The portrait
compositor now treats that as a known Meshy texture artifact: teal is allowed
only in the horns and a lower-left belly oval fitted to the turned torso.
Non-belly teal/cyan pixels are forced back into the blue costume role before the
soft palette pass. The current teal component moved from roughly `x=121..433,
y=623..900` to `x=121..342, y=658..900`, removing the separate chest/shoulder
oval from the portrait proof.

Renderer fixes added for this gate:

- `--ortho-scale` for absolute portrait camera experiments.
- `--camera-target-z-frac` for model-space vertical camera targeting.
- Relative render output paths now resolve against the repo root so Blender
  cannot accidentally write frames to `C:\spikes`.

Verdict: the cutscene lane is now visually testable. The current still is a
framing approval candidate, not a final Otto portrait. If approved, the next
step is a locked-camera 2D face-card set for this exact portrait angle: open
eyes, blink, four brow states, and text-driven mouth shapes.

## Generated Dialogue Face Patches

The dialogue portrait face workflow now uses image generation for the face-state
art, but not for the final frame composite.

Source sheet:

- `spikes/sprite_render/dialogue_portrait_face_system/source_generation/otto_generated_face_patch_sheet.png`

Extractor:

- `spikes/sprite_render/extract_generated_portrait_face_patches.py`

Outputs:

- `spikes/sprite_render/dialogue_portrait_face_system/generated_face_patches/otto_face_patch_neutral.png`
- `spikes/sprite_render/dialogue_portrait_face_system/generated_face_patches/otto_face_patch_small_open.png`
- `spikes/sprite_render/dialogue_portrait_face_system/generated_face_patches/otto_face_patch_wide_open.png`
- `spikes/sprite_render/dialogue_portrait_face_system/generated_face_patches/otto_face_patch_teeth.png`
- `spikes/sprite_render/dialogue_portrait_face_system/generated_face_patches/otto_face_patch_blink.png`
- `spikes/sprite_render/dialogue_portrait_face_system/generated_face_patches/otto_face_patch_skeptical.png`
- `spikes/sprite_render/dialogue_portrait_face_system/generated_face_patches/otto_face_overlay_full_*.png`
- `spikes/sprite_render/dialogue_portrait_face_system/generated_face_patches/otto_face_composite_*.png`
- `spikes/sprite_render/dialogue_portrait_face_system/generated_face_patches/otto_generated_face_patch_contact.png`
- `spikes/sprite_render/dialogue_portrait_face_system/generated_face_patches/otto_generated_face_patch_preview.gif`

Method:

- Generate only a 2x3 face-patch sheet on a flat `#ff00ff` key, based on the
  locked Otto face crop.
- Chroma-key the magenta background locally.
- Keep one shared union crop for all six states so blinking and mouth changes do
  not shift the registration.
- Fit every state to the same portrait target box: `[1184, 225, 1534, 675]`.
- Emit both cropped transparent patches and full-frame transparent overlays.

This fixes the previous compositing error. The generated background is discarded,
and the final game-facing asset is a transparent face patch that lives on top of
the static model render. The costume, hood, horns, belly patch, body, desk, and
room remain the base model/background pixels.
