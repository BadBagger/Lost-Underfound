#!/usr/bin/env python3
"""Slice clean pink-background LoRA source sheets into captioned dataset images."""

from __future__ import annotations

import argparse
import json
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
PINK = (255, 0, 255)
KEY_TOLERANCE = 44
FORBIDDEN_CAPTION_TERMS = (
    "desk",
    "gate",
    "room",
    "speech bubble",
    "ui",
    "rabbit",
    "bunny",
    "fox",
    "animal ears",
)


def fail(message: str) -> None:
    raise SystemExit(f"FAIL - {message}")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_manifest() -> dict:
    if not MANIFEST.exists():
        fail(f"missing manifest: {rel(MANIFEST)}")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def character_entry(manifest: dict, character_id: str) -> dict:
    for character in manifest["characters"]:
        if character["id"] == character_id:
            return character
    fail(f"unknown character id: {character_id}")


def pink_key_image(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            distance = abs(r - PINK[0]) + abs(g - PINK[1]) + abs(b - PINK[2])
            generated_pink = r >= 185 and b >= 145 and g <= 95 and (r + b - g) >= 330
            if distance <= KEY_TOLERANCE or generated_pink:
                pixels[x, y] = (PINK[0], PINK[1], PINK[2], 0)
    return rgba


def crop_actor_from_keyed(cell: Image.Image) -> Image.Image:
    bbox = cell.getchannel("A").getbbox()
    if bbox is None:
        fail("sheet cell is empty after pink key")
    return cell.crop(bbox)


def detected_pose_boxes(keyed: Image.Image, expected_count: int) -> list[tuple[int, int, int, int]]:
    alpha = keyed.getchannel("A")
    pixels = alpha.load()
    width, height = keyed.size
    visited = bytearray(width * height)
    components: list[tuple[int, int, int, int, int]] = []

    def index(x: int, y: int) -> int:
        return y * width + x

    for y in range(height):
        for x in range(width):
            start_index = index(x, y)
            if visited[start_index] or pixels[x, y] == 0:
                continue

            stack = [(x, y)]
            visited[start_index] = 1
            left = right = x
            top = bottom = y
            area = 0
            while stack:
                px, py = stack.pop()
                area += 1
                left = min(left, px)
                right = max(right, px)
                top = min(top, py)
                bottom = max(bottom, py)
                for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    ni = index(nx, ny)
                    if visited[ni] or pixels[nx, ny] == 0:
                        continue
                    visited[ni] = 1
                    stack.append((nx, ny))

            comp_width = right - left + 1
            comp_height = bottom - top + 1
            if area >= 400 and comp_width >= 28 and comp_height >= 28:
                components.append((area, left, right + 1, top, bottom + 1))

    if len(components) < expected_count:
        details = ", ".join(f"{left}-{right}/area{area}" for area, left, right, _top, _bottom in components)
        fail(f"detected {len(components)} usable component(s), expected {expected_count}: {details}")

    selected = sorted(components, reverse=True)[:expected_count]
    boxes = [
        (max(0, left - 20), max(0, top - 20), min(width, right + 20), min(height, bottom + 20))
        for _area, left, right, _top, _bottom in sorted(selected, key=lambda component: component[1])
        for top, bottom in [(_top, _bottom)]
    ]
    return boxes


def normalize_actor(actor: Image.Image, output: Path) -> tuple[int, int, int, int]:
    pixels = actor.load()
    for y in range(actor.height):
        for x in range(actor.width):
            r, g, b, a = pixels[x, y]
            if a > 0 and r >= 150 and b >= 120 and g <= 105 and (r + b - g) >= 230:
                pixels[x, y] = (PINK[0], PINK[1], PINK[2], 0)

    keep_largest_alpha_component(actor)
    bbox = actor.getchannel("A").getbbox()
    if bbox is None:
        fail("actor became empty after despill")
    actor = actor.crop(bbox)

    scale = min(MAX_ACTOR_SIZE / actor.width, MAX_ACTOR_SIZE / actor.height)
    resized = actor.resize(
        (max(1, round(actor.width * scale)), max(1, round(actor.height * scale))),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (PINK[0], PINK[1], PINK[2], 0))
    x = (CANVAS_SIZE - resized.width) // 2
    y = (CANVAS_SIZE - resized.height) // 2
    canvas.alpha_composite(resized, (x, y))
    canvas.save(output)
    return (x, y, x + resized.width, y + resized.height)


def keep_largest_alpha_component(image: Image.Image) -> None:
    alpha = image.getchannel("A")
    alpha_pixels = alpha.load()
    pixels = image.load()
    width, height = image.size
    visited = bytearray(width * height)
    components: list[tuple[int, list[tuple[int, int]]]] = []

    def index(x: int, y: int) -> int:
        return y * width + x

    for y in range(height):
        for x in range(width):
            start_index = index(x, y)
            if visited[start_index] or alpha_pixels[x, y] == 0:
                continue
            stack = [(x, y)]
            visited[start_index] = 1
            points: list[tuple[int, int]] = []
            while stack:
                px, py = stack.pop()
                points.append((px, py))
                for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    ni = index(nx, ny)
                    if visited[ni] or alpha_pixels[nx, ny] == 0:
                        continue
                    visited[ni] = 1
                    stack.append((nx, ny))
            components.append((len(points), points))

    if not components:
        return
    keep = set(max(components, key=lambda item: item[0])[1])
    for _size, points in components:
        for x, y in points:
            if (x, y) not in keep:
                pixels[x, y] = (PINK[0], PINK[1], PINK[2], 0)


def clean_dataset(dataset_dir: Path, character_id: str) -> None:
    dataset_dir.mkdir(parents=True, exist_ok=True)
    for path in dataset_dir.iterdir():
        if path.name == ".gitkeep":
            continue
        if path.name.startswith(f"{character_id}_") or path.name in {"contact-sheet.png", "dataset.json"}:
            path.unlink()


def caption_for(character: dict, pose_label: str) -> str:
    caption = f"{character['trigger']}, actor-only source, isolated transparent crop, {pose_label}"
    lowered = caption.lower()
    for term in FORBIDDEN_CAPTION_TERMS:
        if term in lowered:
            fail(f"generated caption contains forbidden term {term!r}: {caption}")
    return caption


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


def update_manifest(manifest: dict, character: dict) -> None:
    character["status"] = "dataset-ready"
    character["dataset_contact_sheet"] = f"{character['dataset_dir']}/contact-sheet.png"
    character["dataset_manifest"] = f"{character['dataset_dir']}/dataset.json"
    character["blocked_until"] = [
        "LoRA training run",
        "post-training identity review",
        "state-strip registration QA",
    ]
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def parse_sheet_arg(value: str) -> tuple[Path, int]:
    try:
        path_text, count_text = value.rsplit(":", 1)
        count = int(count_text)
    except ValueError:
        fail(f"sheet must be formatted as path:pose_count, got {value!r}")
    path = ROOT / path_text
    if not path.exists():
        fail(f"missing source sheet: {rel(path)}")
    if count < 1:
        fail("pose_count must be positive")
    return path, count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("character", help="character id from art/lora/manifest.json")
    parser.add_argument("--sheet", action="append", required=True, help="source sheet as path:pose_count")
    args = parser.parse_args()

    manifest = load_manifest()
    character = character_entry(manifest, args.character)
    dataset_dir = ROOT / character["dataset_dir"]
    clean_dataset(dataset_dir, character["id"])

    output_images: list[Path] = []
    records = []
    output_index = 1
    for sheet_path, pose_count in [parse_sheet_arg(sheet) for sheet in args.sheet]:
        with Image.open(sheet_path) as sheet:
            sheet = sheet.convert("RGBA")
            keyed = pink_key_image(sheet)
            for pose_index, box in enumerate(detected_pose_boxes(keyed, pose_count), start=1):
                cell = keyed.crop(box)
                actor = crop_actor_from_keyed(cell)
                stem = f"{character['id']}_{output_index:03d}_source_{pose_index:02d}"
                image_path = dataset_dir / f"{stem}.png"
                caption_path = dataset_dir / f"{stem}.txt"
                bbox = normalize_actor(actor, image_path)
                caption_path.write_text(caption_for(character, f"clean source pose {pose_index}") + "\n", encoding="utf-8")
                output_images.append(image_path)
                records.append(
                    {
                        "file": rel(image_path),
                        "caption": rel(caption_path),
                        "source_sheet": rel(sheet_path),
                        "source_pose": pose_index,
                        "normalized_alpha_bbox": bbox,
                    }
                )
                output_index += 1

    minimum = int(manifest["rules"].get("minimum_trainable_images", 16))
    if len(output_images) < minimum:
        fail(f"{character['id']} needs at least {minimum} images; generated {len(output_images)}")

    write_contact_sheet(dataset_dir, output_images)
    (dataset_dir / "dataset.json").write_text(
        json.dumps(
            {
                "character": character["id"],
                "trigger": character["trigger"],
                "canvas": [CANVAS_SIZE, CANVAS_SIZE],
                "source_policy": "clean generated actor-only pink-background source sheets",
                "frames": records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    update_manifest(manifest, character)

    print(f"Sliced {len(output_images)} LoRA dataset image(s) for {character['id']}")
    print(f"Dataset: {rel(dataset_dir)}")
    print(f"Contact sheet: {rel(dataset_dir / 'contact-sheet.png')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
