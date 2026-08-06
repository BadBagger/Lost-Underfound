# LoRA Production Area

This folder holds the controlled identity-training lane for Lost & Underfound.

- `manifest.json` is the source of truth for character trigger tokens, training
  eligibility, source paths, and output model paths.
- `datasets/<character>/` is where approved actor-only training images and
  captions go.
- `prompts/` holds reusable state-strip prompt blocks for ComfyUI generation.
- `models/` is reserved for trained LoRA files and must be documented in the
  manifest before use.

Run `npm run qa:lora` before training or generating state strips from a new LoRA.
The LoRA lane is allowed to improve character identity consistency, but every
generated runtime sheet still has to pass registration, cast-scale, full
construction, and visual QA.
