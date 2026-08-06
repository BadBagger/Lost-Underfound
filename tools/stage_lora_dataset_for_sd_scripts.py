#!/usr/bin/env python3
"""Stage a repo LoRA dataset into the local sd-scripts/kohya folder layout."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("This tool requires Pillow: pip install Pillow")


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "art" / "lora" / "manifest.json"
DEFAULT_TRAINING_ROOT = Path("D:/CodexDeps/lora_training")
TRAINING_BACKGROUNDS = [
    ("solid warm parchment background", (205, 184, 139)),
    ("solid muted blue grey background", (91, 113, 128)),
    ("solid dark umber background", (70, 54, 43)),
    ("solid soft clay background", (151, 112, 89)),
    ("solid desaturated olive background", (108, 117, 83)),
    ("solid neutral grey background", (128, 128, 128)),
]


def fail(message: str) -> None:
    raise SystemExit(f"FAIL - {message}")


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def character_entry(manifest: dict, character_id: str) -> dict:
    for character in manifest["characters"]:
        if character["id"] == character_id:
            return character
    fail(f"unknown character id: {character_id}")


def assert_inside(child: Path, parent: Path) -> None:
    child_resolved = child.resolve()
    parent_resolved = parent.resolve()
    if parent_resolved != child_resolved and parent_resolved not in child_resolved.parents:
        fail(f"refusing path outside target root: {child_resolved}")


def flatten_for_training(source: Path, target: Path, background_rgb: tuple[int, int, int]) -> None:
    with Image.open(source) as image:
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (*background_rgb, 255))
        background.alpha_composite(rgba)
        background.convert("RGB").save(target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("character", help="character id from art/lora/manifest.json")
    parser.add_argument("--training-root", default=str(DEFAULT_TRAINING_ROOT))
    parser.add_argument("--repeats", type=int, default=2)
    args = parser.parse_args()

    if args.repeats < 1:
        fail("--repeats must be positive")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    character = character_entry(manifest, args.character)
    if character.get("status") not in {"dataset-ready", "trainable", "trained-proof", "trained-candidate", "trained"}:
        fail(f"{args.character} is not dataset-ready; current status is {character.get('status')!r}")

    source_dir = ROOT / character["dataset_dir"]
    if not source_dir.exists():
        fail(f"dataset_dir missing: {rel(source_dir)}")

    training_root = Path(args.training_root)
    if not training_root.exists():
        fail(f"training root missing: {training_root}")

    dataset_root = training_root / f"dataset_{character['id'].replace('-', '_')}"
    repeat_dir = dataset_root / f"{args.repeats}_{character['trigger']}"
    assert_inside(dataset_root, training_root)
    assert_inside(repeat_dir, dataset_root)

    if repeat_dir.exists():
        shutil.rmtree(repeat_dir)
    repeat_dir.mkdir(parents=True)

    copied_pairs = 0
    for index, image_path in enumerate(sorted(source_dir.glob(f"{character['id']}_*.png")), start=1):
        caption_path = source_dir / f"{image_path.stem}.txt"
        if not caption_path.exists():
            fail(f"missing caption for {rel(image_path)}")
        stem = f"img_{index:04d}"
        background_label, background_rgb = TRAINING_BACKGROUNDS[(index - 1) % len(TRAINING_BACKGROUNDS)]
        flatten_for_training(image_path, repeat_dir / f"{stem}.png", background_rgb)
        caption = caption_path.read_text(encoding="utf-8").strip()
        (repeat_dir / f"{stem}.txt").write_text(f"{caption}, {background_label}\n", encoding="utf-8")
        copied_pairs += 1

    if copied_pairs == 0:
        fail(f"no dataset image/caption pairs copied from {rel(source_dir)}")

    print(f"Staged {copied_pairs} image/caption pair(s)")
    print(f"Source: {rel(source_dir)}")
    print(f"sd-scripts dataset: {repeat_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
