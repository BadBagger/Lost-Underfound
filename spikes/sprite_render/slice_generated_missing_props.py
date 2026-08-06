#!/usr/bin/env python3
"""Slice generated replacement prop sheets for missing Act 2/3 assets."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "spikes" / "sprite_render" / "generated_missing_prop_art" / "source_sheets"
OUT = ROOT / "spikes" / "sprite_render" / "generated_missing_prop_art" / "sliced"
CONTACT = ROOT / "spikes" / "sprite_render" / "generated_missing_prop_art" / "generated_missing_props_contact.png"
MAGENTA = np.array([255, 0, 255], dtype=np.float32)


def ensure(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def key_magenta(img: Image.Image, tolerance: float = 72.0) -> Image.Image:
    rgba = img.convert("RGBA")
    arr = np.asarray(rgba).copy()
    rgb = arr[..., :3].astype(np.float32)
    dist = np.linalg.norm(rgb - MAGENTA.reshape(1, 1, 3), axis=2)
    pink_bg = (rgb[..., 0] > 175) & (rgb[..., 2] > 175) & (rgb[..., 1] < 140)
    hard_key = (dist < tolerance) | pink_bg
    alpha = np.where(hard_key, 0, 255).astype(np.uint8)
    alpha = np.asarray(Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(0.45))).copy()
    alpha[hard_key] = 0
    arr[..., 3] = np.minimum(arr[..., 3], alpha)
    # Remove magenta spill from antialiased pixels that survive near fuzzy edges.
    soft_pink = (arr[..., 3] > 0) & (rgb[..., 0] > 145) & (rgb[..., 2] > 145) & (rgb[..., 1] < 150)
    neutral = np.maximum(rgb[..., 1], np.minimum(rgb[..., 0], rgb[..., 2]) * 0.35).astype(np.uint8)
    arr[..., 0][soft_pink] = neutral[soft_pink]
    arr[..., 2][soft_pink] = neutral[soft_pink]
    arr[..., :3][arr[..., 3] == 0] = 0
    return Image.fromarray(arr, "RGBA")


def key_black_to_partial_alpha(img: Image.Image) -> Image.Image:
    """Extract pale web strands from a black-source render while preserving softness."""
    rgba = img.convert("RGBA")
    arr = np.asarray(rgba).copy()
    rgb = arr[..., :3].astype(np.float32)
    max_channel = rgb.max(axis=2)
    alpha = np.clip((max_channel - 4.0) * 1.45, 0, 255).astype(np.uint8)
    visible = alpha > 0
    safe_alpha = np.maximum(alpha.astype(np.float32), 1.0)
    unpremultiplied = np.clip(rgb * (255.0 / safe_alpha[..., None]), 0, 255).astype(np.uint8)
    arr[..., :3] = np.where(visible[..., None], unpremultiplied, 0)
    arr[..., 3] = np.minimum(arr[..., 3], alpha)
    return Image.fromarray(arr, "RGBA")


def keep_main_alpha_component(img: Image.Image, min_area: int = 96) -> Image.Image:
    """Drop disconnected neighbor scraps left by wide sheet crops."""
    arr = np.asarray(img.convert("RGBA")).copy()
    mask = arr[..., 3] > 18
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    components: list[tuple[int, list[tuple[int, int]], bool]] = []

    for sy in range(h):
        for sx in range(w):
            if not mask[sy, sx] or seen[sy, sx]:
                continue
            stack = [(sx, sy)]
            seen[sy, sx] = True
            pixels: list[tuple[int, int]] = []
            touches_edge = False
            while stack:
                x, y = stack.pop()
                pixels.append((x, y))
                if x == 0 or x == w - 1 or y == 0 or y == h - 1:
                    touches_edge = True
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((nx, ny))
            components.append((len(pixels), pixels, touches_edge))

    if not components:
        return img

    largest = max(area for area, _, _ in components)
    keep = np.zeros((h, w), dtype=bool)
    for area, pixels, touches_edge in components:
        # The real prop is the dominant body. Edge-touching fragments from
        # neighboring sheet cells are kept only if they are clearly substantial.
        if area == largest or (area >= max(min_area, int(largest * 0.08)) and not touches_edge):
            for x, y in pixels:
                keep[y, x] = True

    arr[..., 3] = np.where(keep, arr[..., 3], 0).astype(np.uint8)
    arr[..., :3][arr[..., 3] == 0] = 0
    return Image.fromarray(arr, "RGBA")


def despill_magenta_edges(img: Image.Image, include_opaque: bool = False) -> Image.Image:
    """Neutralize chroma-key pink on soft edges without recoloring opaque art."""
    arr = np.asarray(img.convert("RGBA")).copy()
    rgb = arr[..., :3].astype(np.int16)
    alpha = arr[..., 3]
    r = rgb[..., 0]
    g = rgb[..., 1]
    b = rgb[..., 2]
    edge = (alpha > 0) if include_opaque else ((alpha > 0) & (alpha < 246))
    magenta_like = (r > g + 38) & (b > g + 38) & (np.abs(r - b) < 96)
    target = edge & magenta_like
    if target.any():
        neutral = np.clip((g * 1.12 + np.minimum(r, b) * 0.18), 0, 255).astype(np.uint8)
        arr[..., 0][target] = neutral[target]
        arr[..., 2][target] = neutral[target]
        arr[..., 1][target] = np.maximum(arr[..., 1][target], (neutral[target] * 0.82).astype(np.uint8))
    return Image.fromarray(arr, "RGBA")


def remove_magenta_spill_pixels(img: Image.Image) -> Image.Image:
    """For fuzzy dust only: surviving magenta pixels are source background, not art."""
    arr = np.asarray(img.convert("RGBA")).copy()
    rgb = arr[..., :3].astype(np.int16)
    alpha = arr[..., 3]
    r = rgb[..., 0]
    g = rgb[..., 1]
    b = rgb[..., 2]
    spill = (alpha > 0) & (r > g + 28) & (b > g + 28) & (np.abs(r - b) < 112)
    arr[..., 3][spill] = 0
    arr[..., :3][arr[..., 3] == 0] = 0
    return Image.fromarray(arr, "RGBA")


def content_crop(img: Image.Image, padding: int = 18) -> Image.Image:
    bbox = img.getchannel("A").getbbox()
    if not bbox:
        return img
    x1, y1, x2, y2 = bbox
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(img.width, x2 + padding)
    y2 = min(img.height, y2 + padding)
    return img.crop((x1, y1, x2, y2))


def slice_by_boxes(sheet: Image.Image, specs: list[tuple[str, tuple[int, int, int, int], str]]) -> list[dict]:
    items: list[dict] = []
    ensure(OUT)
    for name, box, note in specs:
        crop = sheet.crop(box)
        if name.startswith("dust_"):
            keyed = remove_magenta_spill_pixels(
                despill_magenta_edges(keep_main_alpha_component(key_magenta(crop, tolerance=95.0)), include_opaque=True)
            )
        else:
            keyed = keep_main_alpha_component(key_magenta(crop, tolerance=62.0))
        keyed = content_crop(keyed)
        path = OUT / f"{name}.png"
        keyed.save(path)
        items.append(
            {
                "name": name,
                "source_box": list(box),
                "note": note,
                "path": str(path),
                "size": [keyed.width, keyed.height],
                "alpha_policy": "magenta chroma-key review alpha; final admission still needs edge QA",
            }
        )
    return items


def add_black_keyed_item(path: Path, name: str, note: str) -> dict:
    keyed = content_crop(keep_main_alpha_component(key_black_to_partial_alpha(Image.open(path))))
    out_path = OUT / f"{name}.png"
    keyed.save(out_path)
    return {
        "name": name,
        "source_box": None,
        "note": note,
        "path": str(out_path),
        "size": [keyed.width, keyed.height],
        "alpha_policy": "partial alpha extracted from black-background source; review over dark and light plates",
    }


def save_contact(items: list[dict]) -> None:
    thumb = (230, 190)
    cols = 4
    rows = math.ceil(len(items) / cols)
    contact = Image.new("RGBA", (cols * thumb[0], rows * (thumb[1] + 42)), (128, 128, 128, 255))
    draw = ImageDraw.Draw(contact)
    for i, item in enumerate(items):
        img = Image.open(item["path"]).convert("RGBA")
        x = (i % cols) * thumb[0]
        y = (i // cols) * (thumb[1] + 42) + 38
        scale = min((thumb[0] - 16) / img.width, (thumb[1] - 12) / img.height, 1.0)
        resized = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.Resampling.LANCZOS)
        contact.alpha_composite(resized, (x + (thumb[0] - resized.width) // 2, y + (thumb[1] - resized.height) // 2))
        draw.text((x + 6, y - 32), item["name"][:28], fill=(255, 244, 215, 255))
        draw.text((x + 6, y - 17), f"{item['size'][0]}x{item['size'][1]}", fill=(230, 220, 200, 255))
    contact.save(CONTACT)


def main() -> None:
    ensure(OUT)
    marble_sheet = Image.open(SRC / "marble_candidates_generated.png").convert("RGB")
    dust_sheet = Image.open(SRC / "dust_cobweb_correct_marble_generated.png").convert("RGB")

    # Boxes are intentionally row-layout-based with wide cells; content_crop
    # trims each prop after the magenta background is removed.
    marble_items = slice_by_boxes(
        marble_sheet,
        [
            ("marble_galaxy_final_candidate", (0, 250, 310, 760), "wrong: galaxy swirl"),
            ("marble_radiator_tag_final_candidate", (295, 230, 625, 800), "wrong: radiator tag"),
            ("marble_scratch_decoy_final_candidate", (615, 265, 900, 765), "wrong: scratch/star-decoy mark"),
            ("marble_flawless_final_candidate", (890, 260, 1205, 760), "wrong: clear/flawless"),
            ("marble_broken_decoy_final_candidate", (1190, 285, 1536, 760), "wrong: broken shell/dust interior"),
        ],
    )
    dust_items = slice_by_boxes(
        dust_sheet,
        [
            ("dust_button_hidden_final_candidate", (0, 180, 475, 720), "dust clump with button hidden"),
            ("dust_clump_open_final_candidate", (450, 155, 900, 730), "disturbed hollow dust clump"),
            ("marble_correct_star_nick_final_candidate", (1340, 175, 1831, 735), "correct Pip marble with lopsided star nick"),
        ],
    )
    cobweb_item = add_black_keyed_item(
        SRC / "cobweb_curtain_generated_black.png",
        "cobweb_curtain_final_candidate",
        "clean regenerated cobweb curtain; extracted from black source to avoid magenta strand contamination",
    )
    items = marble_items + dust_items + [cobweb_item]
    save_contact(items)
    manifest = {
        "role": "generated replacement art for missing/bad-crop props",
        "source_sheets": {
            "marbles": str(SRC / "marble_candidates_generated.png"),
            "dust_cobweb_correct_marble": str(SRC / "dust_cobweb_correct_marble_generated.png"),
            "clean_cobweb_black_source": str(SRC / "cobweb_curtain_generated_black.png"),
        },
        "items": items,
        "contact_sheet": str(CONTACT),
        "warnings": [
            "Fifth marble from five-candidate sheet is a broken decoy, not the correct marble.",
            "Correct star-nick Pip marble is sourced from the second generated sheet.",
            "Cobweb uses partial alpha extracted from a black-background source; verify over light and dark plates before admission.",
            "Dust clump candidates use a dust-only spill deletion pass; automatic magenta-like counts are zero, but fuzzy edges still need visual edge QA.",
        ],
    }
    (OUT.parent / "generated_missing_props_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"items": len(items), "contact": str(CONTACT)}, indent=2))


if __name__ == "__main__":
    main()
