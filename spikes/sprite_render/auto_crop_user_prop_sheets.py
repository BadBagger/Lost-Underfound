#!/usr/bin/env python3
"""Auto-crop user prop sheets into connected object candidates.

This replaces the first hand-box crop pass, which cut through too many objects.
It detects non-background connected components, pads them, and emits numbered
candidate crops for human review/renaming.
"""

from __future__ import annotations

import json
import math
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "spikes" / "sprite_render" / "user_prop_art_intake_auto"
CROP_DIR = OUT_ROOT / "candidates"

SOURCES = {
    "marbles": Path(r"C:\Users\KyleB\Downloads\Codex Image Aug 5, 2026, 07_24_26 PM.png"),
    "room_props": Path(r"C:\Users\KyleB\Downloads\Codex Image Aug 5, 2026, 07_23_22 PM.png"),
    "inventory_props": Path(r"C:\Users\KyleB\Downloads\Codex Image Aug 5, 2026, 07_22_36 PM.png"),
    "scene_objects": Path(r"C:\Users\KyleB\Downloads\Codex Image Aug 5, 2026, 07_22_33 PM.png"),
}


def ensure(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def background_color(arr: np.ndarray) -> np.ndarray:
    h, w, _ = arr.shape
    points = [
        arr[0, 0],
        arr[0, w - 1],
        arr[h - 1, 0],
        arr[h - 1, w - 1],
        arr[0, w // 2],
        arr[h - 1, w // 2],
        arr[h // 2, 0],
        arr[h // 2, w - 1],
    ]
    return np.median(np.stack(points).astype(np.float32), axis=0)


def component_boxes(mask: np.ndarray, min_area: int, max_area: int) -> list[tuple[int, int, int, int, int]]:
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    boxes: list[tuple[int, int, int, int, int]] = []
    for y0 in range(h):
        for x0 in range(w):
            if seen[y0, x0] or not mask[y0, x0]:
                continue
            queue: deque[tuple[int, int]] = deque([(x0, y0)])
            seen[y0, x0] = True
            xs: list[int] = []
            ys: list[int] = []
            while queue:
                x, y = queue.popleft()
                xs.append(x)
                ys.append(y)
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny, nx] and mask[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((nx, ny))
            area = len(xs)
            if min_area <= area <= max_area:
                boxes.append((min(xs), min(ys), max(xs) + 1, max(ys) + 1, area))
    return boxes


def merge_nearby(boxes: list[tuple[int, int, int, int, int]], gap: int = 20) -> list[tuple[int, int, int, int, int]]:
    pending = boxes[:]
    changed = True
    while changed:
        changed = False
        merged: list[tuple[int, int, int, int, int]] = []
        while pending:
            a = pending.pop(0)
            ax1, ay1, ax2, ay2, aa = a
            did_merge = False
            for i, b in enumerate(pending):
                bx1, by1, bx2, by2, ba = b
                separated = ax2 + gap < bx1 or bx2 + gap < ax1 or ay2 + gap < by1 or by2 + gap < ay1
                if not separated:
                    pending.pop(i)
                    pending.append((min(ax1, bx1), min(ay1, by1), max(ax2, bx2), max(ay2, by2), aa + ba))
                    changed = True
                    did_merge = True
                    break
            if not did_merge:
                merged.append(a)
        pending = merged
    return sorted(pending, key=lambda b: (b[1], b[0]))


def crop_with_alpha(img: Image.Image, box: tuple[int, int, int, int], bg: np.ndarray, tolerance: float = 28.0) -> Image.Image:
    crop = img.crop(box).convert("RGBA")
    arr = np.asarray(crop).copy()
    rgb = arr[..., :3].astype(np.float32)
    dist = np.linalg.norm(rgb - bg.reshape(1, 1, 3), axis=2)
    alpha = np.where(dist < tolerance, 0, np.where(dist < tolerance + 24, ((dist - tolerance) / 24) * 255, 255))
    # Feather the matte slightly for review, not final production.
    alpha_img = Image.fromarray(np.clip(alpha, 0, 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.6))
    crop.putalpha(alpha_img)
    return crop


def save_contact(items: list[dict], path: Path) -> None:
    thumb = (220, 170)
    cols = 4
    rows = math.ceil(len(items) / cols)
    contact = Image.new("RGBA", (cols * thumb[0], rows * (thumb[1] + 42)), (128, 128, 128, 255))
    draw = ImageDraw.Draw(contact)
    for i, item in enumerate(items):
        img = Image.open(item["path"]).convert("RGBA")
        cell_x = (i % cols) * thumb[0]
        cell_y = (i // cols) * (thumb[1] + 42) + 38
        scale = min((thumb[0] - 14) / img.width, (thumb[1] - 10) / img.height, 1.0)
        resized = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.Resampling.LANCZOS)
        contact.alpha_composite(resized, (cell_x + (thumb[0] - resized.width) // 2, cell_y + (thumb[1] - resized.height) // 2))
        draw.text((cell_x + 6, cell_y - 32), item["id"], fill=(255, 244, 215, 255))
        draw.text((cell_x + 6, cell_y - 17), f"{item['size'][0]}x{item['size'][1]}", fill=(230, 220, 200, 255))
    contact.save(path)


def main() -> None:
    ensure(CROP_DIR)
    all_items: list[dict] = []
    for source_id, path in SOURCES.items():
        img = Image.open(path).convert("RGB")
        arr = np.asarray(img)
        bg = background_color(arr)
        dist = np.linalg.norm(arr.astype(np.float32) - bg.reshape(1, 1, 3), axis=2)
        mask = dist > 22
        # Downsampled source sheets can leave tiny texture islands; close them a bit.
        mask_img = Image.fromarray((mask * 255).astype(np.uint8), "L")
        mask_img = mask_img.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
        mask = np.asarray(mask_img) > 0
        min_area = max(800, round(img.width * img.height * 0.0015))
        max_area = round(img.width * img.height * 0.45)
        boxes = merge_nearby(component_boxes(mask, min_area, max_area), gap=16)
        source_items: list[dict] = []
        for index, (x1, y1, x2, y2, area) in enumerate(boxes):
            pad = 24
            box = (max(0, x1 - pad), max(0, y1 - pad), min(img.width, x2 + pad), min(img.height, y2 + pad))
            crop = crop_with_alpha(img, box, bg)
            crop_id = f"{source_id}_{index:02d}"
            out = CROP_DIR / f"{crop_id}.png"
            crop.save(out)
            item = {
                "id": crop_id,
                "source": source_id,
                "box": list(box),
                "area": area,
                "size": [box[2] - box[0], box[3] - box[1]],
                "path": str(out),
            }
            source_items.append(item)
            all_items.append(item)
        save_contact(source_items, OUT_ROOT / f"{source_id}_auto_contact.png")
    save_contact(all_items, OUT_ROOT / "all_auto_contact.png")
    manifest = {
        "role": "automatic object-crop candidates from user-provided prop sheets",
        "policy": "review and rename clean crops; do not final-admit without alpha cleanup and registration",
        "items": all_items,
        "warnings": [
            "Transparent/glass/cobweb assets cannot be recovered perfectly from RGB gray-background sheets.",
            "Some large multi-object source components may intentionally remain grouped for manual recrop.",
        ],
    }
    (OUT_ROOT / "auto_crop_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"items": len(all_items), "contact": str(OUT_ROOT / "all_auto_contact.png")}, indent=2))


if __name__ == "__main__":
    main()
