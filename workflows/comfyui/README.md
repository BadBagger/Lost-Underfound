# ComfyUI Workflow Notes

The current repo does not include a machine-specific ComfyUI graph because graph
exports are brittle across node versions, but this workstation's Comfy Desktop
install is detected at:

`C:/Users/KyleB/AppData/Local/Comfy-Desktop/ComfyUI-Installs/ComfyUI/ComfyUI`

Shared models are under:

`C:/Users/KyleB/AppData/Local/Comfy-Desktop/ComfyUI-Shared/models`

The binding production contract is in `docs/COMFYUI_LORA_PIPELINE.md` and
`art/lora/manifest.json`.

Recommended graph shape:

1. Load base checkpoint.
2. Load one character LoRA.
3. Load character reference image or IP-Adapter reference.
4. Load ControlNet/OpenPose/depth guide for the requested pose strip.
5. Generate a single horizontal state strip on flat pink or grey background.
6. Export source strip into `art/act01-production/source/`.
7. Slice, normalize, and run repo QA before AGS import.

The workflow must not output per-frame runtime sprites directly. The repo's slicer,
registration files, cast-scale manifest, onion-skin output, and visual QA remain
the acceptance gates.
