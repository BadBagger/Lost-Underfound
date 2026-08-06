#!/usr/bin/env python3
"""Build curated LoRA training datasets from registered actor frames."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("This tool requires Pillow: pip install Pillow")


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "art" / "lora" / "manifest.json"
CANVAS_SIZE = 1024
MAX_ACTOR_SIZE = 820
CONTACT_THUMB = 180
CONTACT_COLUMNS = 4
FORBIDDEN_CAPTION_TERMS = ("desk", "gate", "room", "speech bubble", "ui")


@dataclass(frozen=True)
class DatasetFrame:
    source: Path
    source_role: str
    clip: str
    index: int


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def fail(message: str) -> None:
    raise SystemExit(f"FAIL - {message}")


def load_manifest() -> dict:
    if not MANIFEST.exists():
        fail(f"missing manifest: {rel(MANIFEST)}")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def character_entry(manifest: dict, character_id: str) -> dict:
    for character in manifest["characters"]:
        if character["id"] == character_id:
            return character
    fail(f"unknown character id: {character_id}")


def collect_registered_frames(character: dict) -> list[DatasetFrame]:
    training_sources = character.get("training_sources", [])
    if not training_sources:
        fail(f"{character['id']} has no training_sources in {rel(MANIFEST)}")

    frames: list[DatasetFrame] = []
    for source in training_sources:
        registration_path = ROOT / source["registration"]
        if "quarantine" in registration_path.parts:
            fail(f"refusing quarantined source: {rel(registration_path)}")
        if not registration_path.exists():
            fail(f"missing registration source: {rel(registration_path)}")

        registration = json.loads(registration_path.read_text(encoding="utf-8"))
        if registration.get("approval_state") not in source.get("allowed_approval_states", []):
            fail(
                f"{rel(registration_path)} approval_state={registration.get('approval_state')!r} "
                f"is not allowed for LoRA dataset"
            )

        clip = source.get("clip", registration.get("sheet", registration_path.parent.name))
        for index, frame in enumerate(registration.get("frames", []), start=1):
            frame_path = registration_path.parent / frame["file"]
            if not frame_path.exists():
                fail(f"registered frame missing: {rel(frame_path)}")
            frames.append(
                DatasetFrame(
                    source=frame_path,
                    source_role=frame.get("role", f"{clip}-{index:02d}"),
                    clip=clip,
                    index=index,
                )
            )
    return frames


def normalize_frame(source: Path, output: Path) -> tuple[int, int, int, int]:
    with Image.open(source) as image:
        image = image.convert("RGBA")
        bbox = image.getchannel("A").getbbox()
        if bbox is None:
            fail(f"{rel(source)} is empty")

        actor = image.crop(bbox)
        scale = min(MAX_ACTOR_SIZE / actor.width, MAX_ACTOR_SIZE / actor.height)
        resized = actor.resize(
            (max(1, round(actor.width * scale)), max(1, round(actor.height * scale))),
            Image.Resampling.LANCZOS,
        )

        canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
        x = (CANVAS_SIZE - resized.width) // 2
        y = (CANVAS_SIZE - resized.height) // 2
        canvas.alpha_composite(resized, (x, y))
        canvas.save(output)
        return (x, y, x + resized.width, y + resized.height)


def caption_for(character: dict, frame: DatasetFrame) -> str:
    role = frame.source_role.replace("-", " ")
    for term in FORBIDDEN_CAPTION_TERMS:
        role = role.replace(term, "counterline")
    caption = (
        f"{character['trigger']}, {character['id']} actor only, warm painterly storybook character, "
        f"consistent identity, full construction visible, transparent background, {frame.clip} pose, {role}"
    )
    lowered = caption.lower()
    for term in FORBIDDEN_CAPTION_TERMS:
        if term in lowered:
            fail(f"generated caption contains forbidden term {term!r}: {caption}")
    return caption


def clean_previous_outputs(dataset_dir: Path, character_id: str) -> None:
    dataset_dir.mkdir(parents=True, exist_ok=True)
    for path in dataset_dir.iterdir():
        if path.name == ".gitkeep":
            continue
        if path.name.startswith(f"{character_id}_") or path.name in {"contact-sheet.png", "dataset.json"}:
            path.unlink()


def write_contact_sheet(dataset_dir: Path, images: list[Path]) -> None:
    rows = (len(images) + CONTACT_COLUMNS - 1) // CONTACT_COLUMNS
    sheet = Image.new("RGBA", (CONTACT_COLUMNS * CONTACT_THUMB, rows * (CONTACT_THUMB + 26)), (38, 34, 31, 255))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()

    for i, image_path in enumerate(images):
        with Image.open(image_path) as image:
            image = image.convert("RGBA")
            bbox = image.getchannel("A").getbbox()
            thumb = image.crop(bbox) if bbox else image
            thumb.thumbnail((CONTACT_THUMB - 24, CONTACT_THUMB - 42), Image.Resampling.LANCZOS)
            cell_x = (i % CONTACT_COLUMNS) * CONTACT_THUMB
            cell_y = (i // CONTACT_COLUMNS) * (CONTACT_THUMB + 26)
            sheet.alpha_composite(thumb, (cell_x + (CONTACT_THUMB - thumb.width) // 2, cell_y + 12))
            draw.text((cell_x + 10, cell_y + CONTACT_THUMB - 22), image_path.stem, fill=(245, 234, 211), font=font)

    sheet.save(dataset_dir / "contact-sheet.png")


def update_manifest(manifest: dict, character_id: str, status: str) -> None:
    for character in manifest["characters"]:
        if character["id"] == character_id:
            character["status"] = status
            character["dataset_contact_sheet"] = f"{character['dataset_dir']}/contact-sheet.png"
            character["dataset_manifest"] = f"{character['dataset_dir']}/dataset.json"
            character["blocked_until"] = [
                "LoRA training run",
                "post-training identity review",
                "state-strip registration QA",
            ]
            MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            return
    fail(f"unknown character id: {character_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("character", help="character id from art/lora/manifest.json")
    parser.add_argument("--status", default="dataset-ready", help="manifest status to write after building")
    args = parser.parse_args()

    manifest = load_manifest()
    character = character_entry(manifest, args.character)
    frames = collect_registered_frames(character)

    minimum = int(manifest["rules"].get("minimum_trainable_images", 16))
    if len(frames) < minimum:
        fail(f"{args.character} needs at least {minimum} frames; found {len(frames)}")

    dataset_dir = ROOT / character["dataset_dir"]
    clean_previous_outputs(dataset_dir, character["id"])

    output_images: list[Path] = []
    dataset_records = []
    for output_index, frame in enumerate(frames, start=1):
        stem = f"{character['id']}_{output_index:03d}_{frame.clip}_{frame.index:02d}"
        image_path = dataset_dir / f"{stem}.png"
        caption_path = dataset_dir / f"{stem}.txt"
        bbox = normalize_frame(frame.source, image_path)
        caption = caption_for(character, frame)
        caption_path.write_text(caption + "\n", encoding="utf-8")
        output_images.append(image_path)
        dataset_records.append(
            {
                "file": rel(image_path),
                "caption": rel(caption_path),
                "source": rel(frame.source),
                "source_role": frame.source_role,
                "clip": frame.clip,
                "normalized_alpha_bbox": bbox,
            }
        )

    write_contact_sheet(dataset_dir, output_images)
    (dataset_dir / "dataset.json").write_text(
        json.dumps(
            {
                "character": character["id"],
                "trigger": character["trigger"],
                "canvas": [CANVAS_SIZE, CANVAS_SIZE],
                "source_policy": "registered actor frames only; quarantined sources rejected",
                "frames": dataset_records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    update_manifest(manifest, character["id"], args.status)

    print(f"Built {len(output_images)} LoRA dataset image(s) for {character['id']}")
    print(f"Dataset: {rel(dataset_dir)}")
    print(f"Contact sheet: {rel(dataset_dir / 'contact-sheet.png')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
