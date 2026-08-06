#!/usr/bin/env python3
"""Validate the Lost & Underfound LoRA production manifest."""

import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("This tool requires Pillow: pip install Pillow")


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "art" / "lora" / "manifest.json"
MIN_TRANSPARENCY_MARGIN = 2
DATASET_REQUIRED_STATUSES = {"dataset-ready", "trainable", "trained-proof", "trained-candidate", "trained"}
MODEL_REQUIRED_STATUSES = {"trained-proof", "trained-candidate", "trained"}
FORBIDDEN_SCENE_CAPTION_TERMS = ("desk", "gate", "room", "speech bubble", "ui")
FORBIDDEN_CAPTION_TERMS_BY_CHARACTER = {
    "bramble": (
        "rabbit",
        "bunny",
        "fox",
        "animal ears",
        "dustball",
        "lint",
        "spectacles",
        "bow tie",
        "mitten hands",
    )
}


def fail(message: str) -> None:
    print(f"FAIL - {message}")
    raise SystemExit(1)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def image_has_canvas_margin(path: Path) -> bool:
    with Image.open(path) as image:
        image = image.convert("RGBA")
        alpha = image.getchannel("A")
        bbox = alpha.getbbox()
        if bbox is None:
            return False
        left, top, right, bottom = bbox
        width, height = image.size
        return (
            left >= MIN_TRANSPARENCY_MARGIN
            and top >= MIN_TRANSPARENCY_MARGIN
            and right <= width - MIN_TRANSPARENCY_MARGIN
            and bottom <= height - MIN_TRANSPARENCY_MARGIN
        )


def validate_dataset(character: dict, minimum_images: int) -> list[str]:
    failures: list[str] = []
    dataset_dir = ROOT / character["dataset_dir"]
    if not dataset_dir.exists():
        failures.append(f"{character['id']}: dataset_dir does not exist: {character['dataset_dir']}")
        return failures

    images = sorted(path for path in dataset_dir.glob("*.png") if path.name != "contact-sheet.png")
    captions = {path.stem for path in dataset_dir.glob("*.txt")}
    if len(images) < minimum_images:
        failures.append(
            f"{character['id']}: dataset-ready/trainable status requires at least {minimum_images} PNGs, found {len(images)}"
        )

    trigger = character["trigger"]
    for image in images:
        caption = dataset_dir / f"{image.stem}.txt"
        if image.stem not in captions:
            failures.append(f"{character['id']}: missing caption for {rel(image)}")
            continue
        text = caption.read_text(encoding="utf-8")
        if trigger not in text:
            failures.append(f"{character['id']}: caption {rel(caption)} is missing trigger token {trigger!r}")
        lowered = text.lower()
        if any(word in lowered for word in FORBIDDEN_SCENE_CAPTION_TERMS):
            failures.append(f"{character['id']}: caption {rel(caption)} includes scene/UI terms")
        for word in FORBIDDEN_CAPTION_TERMS_BY_CHARACTER.get(character["id"], ()):
            if word in lowered:
                failures.append(
                    f"{character['id']}: caption {rel(caption)} describes identity term {word!r}; bind identity to trigger"
                )
        if not image_has_canvas_margin(image):
            failures.append(f"{character['id']}: {rel(image)} touches the frame edge or is empty")
    return failures


def main() -> int:
    if not MANIFEST.exists():
        fail(f"missing manifest: {rel(MANIFEST)}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    required = {"schema_version", "backend", "rules", "characters"}
    missing = required - manifest.keys()
    if missing:
        fail(f"manifest missing required keys: {sorted(missing)}")

    rules = manifest["rules"]
    backend = manifest["backend"]
    minimum_images = int(rules.get("minimum_trainable_images", 16))
    failures: list[str] = []
    triggers: set[str] = set()

    comfy_path = backend.get("local_comfyui_path")
    if comfy_path:
        comfy_root = Path(comfy_path)
        if not comfy_root.exists():
            failures.append(f"backend: local_comfyui_path does not exist: {comfy_path}")
        elif not (comfy_root / "main.py").exists():
            failures.append(f"backend: local_comfyui_path is missing main.py: {comfy_path}")

    running_comfy_path = backend.get("running_comfyui_path")
    if running_comfy_path:
        running_comfy_root = Path(running_comfy_path)
        if not running_comfy_root.exists():
            failures.append(f"backend: running_comfyui_path does not exist: {running_comfy_path}")
        elif not (running_comfy_root / "main.py").exists():
            failures.append(f"backend: running_comfyui_path is missing main.py: {running_comfy_path}")

    local_python = backend.get("local_python")
    if local_python and not Path(local_python).exists():
        failures.append(f"backend: local_python does not exist: {local_python}")

    shared_models_path = backend.get("shared_models_path")
    if shared_models_path:
        shared_models = Path(shared_models_path)
        if not shared_models.exists():
            failures.append(f"backend: shared_models_path does not exist: {shared_models_path}")
        elif not (shared_models / "checkpoints").exists():
            failures.append(f"backend: shared_models_path is missing checkpoints folder: {shared_models_path}")

    for character in manifest["characters"]:
        for field in ("id", "trigger", "scale", "status", "dataset_dir", "identity_prompt", "candidate_sources"):
            if field not in character:
                failures.append(f"character entry missing {field}: {character}")
                continue

        character_id = character.get("id", "<unknown>")
        trigger = character.get("trigger")
        if trigger in triggers:
            failures.append(f"{character_id}: duplicate trigger token {trigger!r}")
        triggers.add(trigger)

        prompt_path = ROOT / character.get("identity_prompt", "")
        if not prompt_path.exists():
            failures.append(f"{character_id}: identity prompt missing: {character.get('identity_prompt')}")
        elif trigger not in prompt_path.read_text(encoding="utf-8"):
            failures.append(f"{character_id}: identity prompt is missing trigger token {trigger!r}")

        dataset_dir = ROOT / character["dataset_dir"]
        if not dataset_dir.exists():
            failures.append(f"{character_id}: dataset_dir does not exist: {character['dataset_dir']}")

        for source in character.get("candidate_sources", []):
            path = ROOT / source
            if not path.exists():
                failures.append(f"{character_id}: candidate source missing: {source}")
            if "quarantine" in path.parts:
                failures.append(f"{character_id}: quarantined source cannot be a candidate: {source}")

        for source in character.get("training_sources", []):
            path = ROOT / source.get("registration", "")
            if not path.exists():
                failures.append(f"{character_id}: training source missing: {source.get('registration')}")
            if "quarantine" in path.parts:
                failures.append(f"{character_id}: quarantined source cannot be a training source: {source.get('registration')}")

        for source in character.get("rejected_sources", []):
            path = ROOT / source
            if path.exists() and "quarantine" not in path.parts:
                failures.append(f"{character_id}: rejected source is not under quarantine: {source}")

        status = character.get("status")
        if status in DATASET_REQUIRED_STATUSES:
            failures.extend(validate_dataset(character, minimum_images))
        if status in MODEL_REQUIRED_STATUSES:
            model_path = character.get("model_path")
            if not model_path:
                failures.append(f"{character_id}: trained/proof character must declare model_path")
            elif not (ROOT / model_path).exists() and not Path(model_path).exists():
                failures.append(f"{character_id}: trained/proof model_path does not exist: {model_path}")
        elif status == "deferred" and character.get("model_path"):
            failures.append(f"{character_id}: deferred character must not declare model_path")

    print(f"LoRA manifest: {len(manifest['characters'])} character(s), minimum trainable images {minimum_images}")
    if failures:
        print(f"\nFAIL - {len(failures)} LoRA manifest issue(s):")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS - LoRA manifest is structurally valid and no quarantined source is eligible for training.")
    print("Characters marked needs-curated-dataset or needs-clean-source are intentionally blocked from training.")
    print("Characters marked dataset-ready have captioned source images but still require a trained LoRA.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
