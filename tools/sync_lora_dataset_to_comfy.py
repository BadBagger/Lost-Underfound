#!/usr/bin/env python3
"""Mirror a QA-approved LoRA dataset into the local ComfyUI input folder."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "art" / "lora" / "manifest.json"
COMFY_DATASET_ROOT = "lost-underfound-lora"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL - {message}")


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_manifest() -> dict:
    if not MANIFEST.exists():
        fail(f"missing manifest: {rel(MANIFEST)}")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def character_entry(manifest: dict, character_id: str) -> dict:
    for character in manifest["characters"]:
        if character["id"] == character_id:
            return character
    fail(f"unknown character id: {character_id}")


def assert_inside(child: Path, parent: Path) -> None:
    child_resolved = child.resolve()
    parent_resolved = parent.resolve()
    if parent_resolved != child_resolved and parent_resolved not in child_resolved.parents:
        fail(f"refusing to touch path outside target root: {child_resolved}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("character", help="character id from art/lora/manifest.json")
    parser.add_argument(
        "--folder",
        default=None,
        help="Override Comfy input subfolder. Use for an already-indexed Comfy dataset slot such as 3d.",
    )
    parser.add_argument(
        "--comfy-root",
        default=None,
        help="Override the ComfyUI root from the manifest, useful when a different server is already running.",
    )
    parser.add_argument(
        "--flat",
        action="store_true",
        help="Copy character PNG/TXT pairs directly into --folder instead of replacing the folder.",
    )
    args = parser.parse_args()

    manifest = load_manifest()
    character = character_entry(manifest, args.character)
    if character.get("status") not in {"dataset-ready", "trainable", "trained"}:
        fail(f"{args.character} is not dataset-ready; current status is {character.get('status')!r}")

    source_dir = ROOT / character["dataset_dir"]
    if not source_dir.exists():
        fail(f"dataset_dir missing: {rel(source_dir)}")

    comfy_root = Path(args.comfy_root or manifest["backend"].get("local_comfyui_path", ""))
    if not comfy_root.exists():
        fail(f"ComfyUI root missing: {comfy_root}")
    input_root = comfy_root / "input"
    if not input_root.exists():
        fail(f"ComfyUI input folder missing: {input_root}")

    if args.folder:
        mirror_root = input_root
        target_dir = input_root / args.folder
    else:
        mirror_root = input_root / COMFY_DATASET_ROOT
        target_dir = mirror_root / character["id"]
        mirror_root.mkdir(parents=True, exist_ok=True)
    assert_inside(target_dir, mirror_root)

    if target_dir.exists() and not args.flat:
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=args.flat)

    copied = 0
    for source in sorted(source_dir.iterdir()):
        if args.flat:
            if not source.name.startswith(f"{character['id']}_") or source.suffix.lower() not in {".png", ".txt"}:
                continue
        elif source.suffix.lower() not in {".png", ".txt", ".json"}:
            continue
        if args.flat:
            destination = target_dir / source.name
            assert_inside(destination, target_dir)
            if destination.exists():
                destination.unlink()
        shutil.copy2(source, target_dir / source.name)
        copied += 1

    print(f"Synced {copied} file(s)")
    print(f"Source: {rel(source_dir)}")
    print(f"Comfy dataset: {target_dir}")
    print(f"Comfy loader folder name should appear as: {args.folder or COMFY_DATASET_ROOT + '/' + character['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
