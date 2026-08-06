# ComfyUI LoRA Pipeline - Lost & Underfound

This is the character-identity production lane for generated animation art.
ComfyUI/LoRA is allowed to help keep a character consistent across new poses, but
it does not replace the Animation Bible, registration QA, cast-scale QA, or visual
review.

## Goal

Use one small character LoRA per approved character design:

- `lu_pip_shrunk_kid`
- `lu_bramble_clerk`
- `lu_old_bottlecap_guard`
- `lu_scuttle_courier`
- `lu_grommet_guardian` is deferred until Acts 2-3 have script/design detail.

The LoRA controls identity only. Pose, framing, contact line, sprite-strip
structure, and scene placement are controlled separately.

## Production Order

1. Approve the character identity source.
   - The source must be actor-only.
   - The source must not include scene furniture, gate bars, UI, speech bubbles,
     text labels, or baked shadows.
   - The source must show complete intended construction. A crop that removes
     Old Bottlecap's lower cap stack, Pip's feet, Bramble's active hands, or any
     other designed part is rejected before training.
2. Build a curated LoRA dataset.
   - Put files under `art/lora/datasets/<character>/`.
   - Every `.png` needs a same-stem `.txt` caption.
   - Captions must include the character trigger token and must not describe a
     desk, gate, room, or UI unless the character design itself contains it.
   - For character identity LoRAs, caption variable training facts and omit
     defining identity traits that should bind to the trigger. For Bramble,
     captions must not repeat dustball/lint/spectacles/bow-tie/hand-shape terms
     in every file; those belong in the identity prompt and source art review,
     not the per-frame caption.
   - Do not train from a constant flat-color isolation background. Keep the repo
     source crops transparent for QA, then flatten the staged trainer copy onto
     varied simple mattes and caption the matte as variable data.
   - Prefer `python tools/build_lora_dataset.py <character>` so the dataset is
     derived from registered frames and quarantined sources are rejected.
3. Run `npm run qa:lora`.
   - This validates the manifest and catches rejected/quarantined sources before
     training.
   - A character marked `dataset-ready` or `trainable` must have enough captioned
     source images.
   - A character marked `trained` must also point at an existing LoRA file.
4. Train the LoRA in ComfyUI or a kohya-compatible trainer.
   - Save outputs under `art/lora/models/`.
   - Record the training run in `art/lora/manifest.json`.
5. Generate approved source material.
   - For normal actors, this may be a source strip if the LoRA passes identity
     review and the strip obeys the structure contract.
   - For Bramble, LoRA output is restricted to canonical identity sheets and rig
     part sources. Do not use independent diffusion generations as final Bramble
     animation frames.
6. Rig or slice and normalize frames.
   - Bramble animation must come from the deterministic rig lane in
     `docs/BRAMBLE_RIG_PIPELINE.md`.
   - Every runtime sheet still goes through `tools/check_registration.py`.
   - Cast scale still goes through `tools/check_registration.py cast-scale`.
   - Full-construction contact sheets and scene composites remain required.

## Non-Negotiable Rules

- Do not train on quarantined, rejected, cropped, or scene-composited actor frames.
- Do not use LoRA output directly in game before registration and cast-scale QA.
- Do not use a LoRA as a frame factory for off-manifold characters that have
  already shown identity collapse. Bramble's runtime animation must be exported
  from a deterministic rig or equivalent pinned-part source.
- Do not "fix" per-frame size drift with per-frame runtime scale, crop, or offset.
- Do not use blur to conceal idle, talk, or normal walk drift.
- Use smear frames only where the Animation Bible allows them: fast sudden motion
  with readable solid poses before and after.
- Do not bake scale differences into source images. Generate each actor to fill
  its own training/frame canvas; runtime scale comes from data.

## Training Guidance

Recommended starting target for each finalized character:

- 16-30 curated actor-only images.
- 768 or 1024 square training crops, padded rather than cropped.
- Repeat count low enough to avoid overfitting tiny artifacts.
- Trigger token unique per character, always present in the caption.
- 8-12 visual check generations after training before using the LoRA for state
  strips.

For the current repo state, this lane is scaffolded but not trained. Comfy Desktop
is detected at:

`C:/Users/KyleB/AppData/Local/Comfy-Desktop/ComfyUI-Installs/ComfyUI/ComfyUI`

The shared model folder is:

`C:/Users/KyleB/AppData/Local/Comfy-Desktop/ComfyUI-Shared/models`

Codex verified the Comfy venv sees CUDA on an NVIDIA GeForce RTX 5080. Training
still requires a curated character dataset and a kohya-compatible training node or
external trainer path before any LoRA can be marked usable.

## Current Pilot

Bramble is the first dataset pilot because the clerk/talking-head use case is
where the current production art is most sensitive to identity drift and desk
registration. The registered actor-only production frames were tested first, but
visual QA rejected that dataset because it mixed the older flat/vector Bramble
with the newer painterly dust-bunny Bramble.

That rejected dataset is quarantined at:

- `art/lora/quarantine/bramble-mixed-identity-dataset/`

The current Bramble dataset is built from clean actor-only pink-background source
sheets:

- `art/lora/source/bramble/bramble-clean-source-12.png`
- `art/lora/source/bramble/bramble-clean-source-08.png`

Do not train from `art/act01-production/quarantine/bramble-talking-head-talk-missing-hand/`.

Build and mirror the pilot dataset with:

```powershell
npm.cmd run lora:dataset:bramble
npm.cmd run qa:lora
npm.cmd run lora:sync:bramble
```

The sync step copies the repo-approved dataset into ComfyUI's input tree at:

`C:/Users/KyleB/AppData/Local/Comfy-Desktop/ComfyUI-Installs/ComfyUI/ComfyUI/input/lost-underfound-lora/bramble`

Treat the repo copy under `art/lora/datasets/bramble/` as the source of truth;
the Comfy input folder is only a mirror.

The repo dataset captions are intentionally minimal, for example:

```text
lu_bramble_clerk, actor-only source, isolated transparent crop, clean source pose 1
```

`npm.cmd run lora:stage:bramble:sd` creates the sd-scripts training copy as RGB
images on rotating neutral mattes and appends captions such as
`solid warm parchment background`. That variation is required; if pink or any
single isolation color appears in generated LoRA proofs, the model is rejected.

The currently running Comfy server on this machine is not the Desktop install; it
is `D:/CodexDeps/ComfyUI`. For that live server, mirror Bramble to the already
indexed `3d` dataset slot with:

```powershell
npm.cmd run lora:sync:bramble:live
```

### Proof Training Attempt

Codex queued a tiny 8-step Comfy-native proof run through:

`LoadImageTextDataSetFromFolder(3d) -> MakeTrainingDataset -> TrainLoraNode -> SaveLoRA`

Prompt id: `f4a14a30-1645-4513-bdef-727d01a9b680`.

The dataset loader worked after syncing to `D:/CodexDeps/ComfyUI/input/3d`.
Comfy logs reported the prompt executed in 127.17 seconds, but the HTTP endpoint
went down during/after the run and no `bramble_proof*.safetensors` file was found
under `D:/CodexDeps/ComfyUI/output` or `D:/CodexDeps/ComfyUI/models/loras`.

That Comfy-native path is not the approved training route right now. Do not use
Comfy's `TrainLoraNode` for final training until it reliably saves a model and
the server stays reachable after execution.

### Successful External Proof Training

Codex then used the existing `D:/CodexDeps/lora_training` + `D:/CodexDeps/sd-scripts`
training path, matching the repo's already-proven local LoRA workflow.

Commands:

```powershell
npm.cmd run lora:stage:bramble:sd
npm.cmd run lora:train:bramble:proof
```

Result:

- Staged dataset: `D:/CodexDeps/lora_training/dataset_bramble/2_lu_bramble_clerk`
- Trainer: `D:/CodexDeps/sd-scripts/sdxl_train_network.py`
- Output source: `D:/CodexDeps/lora_training/output_lu_bramble_clerk/lu_bramble_clerk_proof.safetensors`
- Repo model: `art/lora/models/lu_bramble_clerk_proof.safetensors`
- Live Comfy copy: `D:/CodexDeps/ComfyUI/models/loras/lost-underfound/lu_bramble_clerk_proof.safetensors`
- SHA256: `B6E51E85CB3764AD6DAA7F65A2378853183225235EA865FA8D1E3DDB7914FA22`
- Proof settings: 24 steps, rank 32, alpha 16, SDXL base, bf16, AdamW8bit.

This is only a proof LoRA. It proves the training lane works, but it is not
approved for runtime animation until it produces controlled Bramble test strips
that pass identity review, registration QA, and desk-scene composite QA.

Visual proof generation rejected this proof LoRA: low-weight outputs snapped
toward rabbit/fox-like animals and higher-weight outputs deformed instead of
sharpening into Bramble. Treat that as an under-bound concept, not as usable
runtime art. The corrective path is the minimal-caption + varied-matte dataset
above before any longer candidate training run.

### Bramble Rig Pivot

Because Bramble is an off-manifold creature and the proof LoRA collapsed toward
neighboring animal priors, the production path for Bramble animation is now:

1. Use ComfyUI/LoRA/reference editing only to make a canonical actor sheet and
   separated Bramble rig parts.
2. Validate the part manifest with:

   ```powershell
   npm.cmd run qa:rig:bramble
   ```

3. Animate idle, talk, gesture, and handoff from the same parts and pivots.
4. Export AGS frame sequences from the rig, then run the normal registration,
   cast-scale, full-construction, and scene-composite QA.

Do not generate Bramble idle/talk as independent per-frame diffusion images. If
a generated sheet changes silhouette, species, crop, scale, hands, spectacles, or
fur mass from cel to cel, reject it before animation.

## ComfyUI Generation Contract

Use LoRA output only to produce source strips like this:

```text
Single horizontal strip, [N] poses left to right, evenly spaced. Flat solid pink
or mid-grey background. No grid lines, no borders, no text, no cast shadows on
the background. Same character, same design, same scale, same camera distance
and eye level in every pose. Generous margins. Consistent warm upper-left light.
[character-specific anchor line]
```

Then hand the strip to the repo slicer/normalizer. If the output needs a different
crop or scale per frame, reject or regenerate the source. That is not a runtime
problem.
