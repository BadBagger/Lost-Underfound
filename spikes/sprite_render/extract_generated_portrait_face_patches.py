#!/usr/bin/env python3
"""Extract transparent Otto dialogue face patches from an image-generated sheet.

The image generator is allowed to solve the painterly face states, but the game
asset must not carry any generated room/background pixels. This script slices a
2x3 state sheet and emits transparent overlays registered to the base portrait.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter


STATES = [
    "neutral",
    "small_open",
    "wide_open",
    "teeth",
    "blink",
    "skeptical",
]


def save(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def slice_grid(sheet: Image.Image, cols: int = 2, rows: int = 3) -> list[Image.Image]:
    cell_w = sheet.width / cols
    cell_h = sheet.height / rows
    cells: list[Image.Image] = []
    for row in range(rows):
        for col in range(cols):
            left = round(col * cell_w)
            upper = round(row * cell_h)
            right = round((col + 1) * cell_w)
            lower = round((row + 1) * cell_h)
            cells.append(sheet.crop((left, upper, right, lower)))
    return cells


def chroma_alpha(img: Image.Image, key: tuple[int, int, int] = (255, 0, 255)) -> Image.Image:
    rgb = img.convert("RGB")
    arr = np.asarray(rgb).astype(np.int32)
    key_arr = np.asarray(key, dtype=np.int32)
    dist = np.sqrt(np.sum((arr - key_arr) ** 2, axis=2))
    alpha = np.clip((dist - 18) / 72 * 255, 0, 255).astype(np.uint8)
    alpha_img = Image.fromarray(alpha, "L").filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.35))
    out = img.convert("RGBA")
    out.putalpha(alpha_img)
    return out


def skin_mask(crop: Image.Image) -> Image.Image:
    """Create a soft alpha mask for Otto's visible face skin and facial marks."""

    rgb = crop.convert("RGB")
    arr = np.asarray(rgb).astype(np.int16)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]

    # Skin pixels in this portrait are warm cream/yellow. Keep the rule broad
    # enough to survive generated shading but narrow enough to reject blue hood.
    warm_skin = (r > 165) & (g > 120) & (b > 75) & (r >= g + 8) & (g >= b + 12)
    skin_l = Image.fromarray((warm_skin.astype(np.uint8) * 255), "L")

    # Pull small eyes, brows, mouth, and cheek lines into the face patch by
    # growing from the skin island rather than by accepting all dark pixels.
    grown = skin_l.filter(ImageFilter.MaxFilter(35))
    grown = grown.filter(ImageFilter.MinFilter(7))
    grown = grown.filter(ImageFilter.GaussianBlur(2.2))

    # Keep the patch face-shaped and away from the hood/hair corners.
    shape = Image.new("L", crop.size, 0)
    draw = ImageDraw.Draw(shape)
    w, h = crop.size
    draw.ellipse(
        [
            round(w * 0.06),
            round(h * 0.03),
            round(w * 0.96),
            round(h * 0.98),
        ],
        fill=255,
    )
    draw.polygon(
        [
            (round(w * 0.12), round(h * 0.08)),
            (round(w * 0.86), round(h * 0.10)),
            (round(w * 0.98), round(h * 0.58)),
            (round(w * 0.74), round(h * 0.98)),
            (round(w * 0.20), round(h * 0.85)),
            (0, round(h * 0.42)),
        ],
        fill=255,
    )
    shape = shape.filter(ImageFilter.GaussianBlur(1.5))
    return ImageChops.multiply(grown, shape)


def trim_alpha(img: Image.Image, pad: int = 8) -> tuple[Image.Image, tuple[int, int, int, int]]:
    bbox = img.getbbox()
    if bbox is None:
        return img, (0, 0, img.width, img.height)
    left = max(0, bbox[0] - pad)
    top = max(0, bbox[1] - pad)
    right = min(img.width, bbox[2] + pad)
    bottom = min(img.height, bbox[3] + pad)
    return img.crop((left, top, right, bottom)), (left, top, right, bottom)


def checkerboard(size: tuple[int, int], cell: int = 24) -> Image.Image:
    img = Image.new("RGBA", size, (230, 222, 205, 255))
    draw = ImageDraw.Draw(img)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle([x, y, x + cell - 1, y + cell - 1], fill=(92, 82, 74, 255))
    return img


def build_contact(patches: dict[str, Image.Image], out: Path) -> None:
    cell_w, cell_h = 260, 250
    cols = 3
    rows = 2
    sheet = checkerboard((cols * cell_w, rows * cell_h), cell=18)
    draw = ImageDraw.Draw(sheet)
    for i, state in enumerate(STATES):
        patch = patches[state]
        thumb = patch.copy()
        thumb.thumbnail((cell_w - 28, cell_h - 50), Image.Resampling.LANCZOS)
        x = (i % cols) * cell_w
        y = (i // cols) * cell_h
        sheet.alpha_composite(thumb, (x + (cell_w - thumb.width) // 2, y + 34))
        draw.text((x + 10, y + 8), state, fill=(255, 244, 215, 255))
    save(sheet, out)


def extract_from_full_frame_sheet(args: argparse.Namespace, base: Image.Image, cells: list[Image.Image]) -> dict[str, Image.Image]:
    patches: dict[str, Image.Image] = {}
    for state, cell in zip(STATES, cells):
        resized = cell.resize(base.size, Image.Resampling.LANCZOS)
        crop_box = tuple(args.crop)
        face_crop = resized.crop(crop_box)
        mask = skin_mask(face_crop)
        patch = face_crop.copy()
        patch.putalpha(mask)
        trimmed, _trim_box = trim_alpha(patch)
        patches[state] = trimmed
    return patches


def extract_from_chroma_patch_sheet(cells: list[Image.Image]) -> dict[str, Image.Image]:
    keyed_cells = [chroma_alpha(cell) for cell in cells]
    union: tuple[int, int, int, int] | None = None
    for keyed in keyed_cells:
        bbox = keyed.getbbox()
        if bbox is None:
            continue
        if union is None:
            union = bbox
        else:
            union = (
                min(union[0], bbox[0]),
                min(union[1], bbox[1]),
                max(union[2], bbox[2]),
                max(union[3], bbox[3]),
            )
    if union is None:
        raise RuntimeError("No keyed subject pixels found in chroma patch sheet")
    pad = 12
    union = (
        max(0, union[0] - pad),
        max(0, union[1] - pad),
        min(keyed_cells[0].width, union[2] + pad),
        min(keyed_cells[0].height, union[3] + pad),
    )
    return {state: keyed.crop(union) for state, keyed in zip(STATES, keyed_cells)}


def fit_patch_to_box(patch: Image.Image, box: tuple[int, int, int, int], stretch: bool = False) -> Image.Image:
    target_w = box[2] - box[0]
    target_h = box[3] - box[1]
    fitted = patch.copy()
    if stretch:
        fitted = fitted.resize((target_w, target_h), Image.Resampling.LANCZOS)
    else:
        fitted.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
    return fitted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--base-still", type=Path, default=Path("spikes/sprite_render/dialogue_portrait_gate/otto_portrait_gate_still.png"))
    parser.add_argument("--out-dir", type=Path, default=Path("spikes/sprite_render/dialogue_portrait_face_system/generated_face_patches"))
    parser.add_argument("--crop", type=int, nargs=4, default=(1160, 245, 1475, 665), metavar=("L", "T", "R", "B"))
    parser.add_argument("--input-kind", choices=("full-frame-sheet", "chroma-patch-sheet"), default="full-frame-sheet")
    parser.add_argument("--target-box", type=int, nargs=4, default=(1160, 225, 1510, 675), metavar=("L", "T", "R", "B"))
    parser.add_argument("--stretch-to-target", action="store_true")
    args = parser.parse_args()

    base = Image.open(args.base_still).convert("RGBA")
    sheet = Image.open(args.sheet).convert("RGBA")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    cells = slice_grid(sheet)
    if len(cells) != len(STATES):
        raise RuntimeError(f"Expected {len(STATES)} cells, got {len(cells)}")

    manifest: dict[str, object] = {
        "source_sheet": str(args.sheet),
        "base_still": str(args.base_still),
        "input_kind": args.input_kind,
        "frame_size": list(base.size),
        "crop": list(args.crop),
        "target_box": list(args.target_box),
        "stretch_to_target": args.stretch_to_target,
        "states": {},
        "constraints": [
            "Generated room/background pixels are discarded.",
            "Output patches contain only a feathered face-region alpha.",
            "Costume, hood, horns, belly, body, and room remain model/base pixels.",
        ],
    }
    if args.input_kind == "chroma-patch-sheet":
        patches = extract_from_chroma_patch_sheet(cells)
    else:
        patches = extract_from_full_frame_sheet(args, base, cells)

    full_overlays: list[Image.Image] = []

    target_box = tuple(args.target_box)
    target_cx = (target_box[0] + target_box[2]) // 2
    target_cy = (target_box[1] + target_box[3]) // 2
    for state in STATES:
        trimmed = patches[state]
        fitted = fit_patch_to_box(trimmed, target_box, stretch=args.stretch_to_target)
        full = Image.new("RGBA", base.size, (0, 0, 0, 0))
        dest = (round(target_cx - fitted.width / 2), round(target_cy - fitted.height / 2))
        full.alpha_composite(fitted, dest)
        composite = Image.alpha_composite(base, full)

        save(trimmed, args.out_dir / f"otto_face_patch_{state}.png")
        save(fitted, args.out_dir / f"otto_face_patch_fitted_{state}.png")
        save(full, args.out_dir / f"otto_face_overlay_full_{state}.png")
        save(composite, args.out_dir / f"otto_face_composite_{state}.png")
        full_overlays.append(composite)
        manifest["states"][state] = {
            "patch": f"otto_face_patch_{state}.png",
            "fitted_patch": f"otto_face_patch_fitted_{state}.png",
            "full_overlay": f"otto_face_overlay_full_{state}.png",
            "composite_preview": f"otto_face_composite_{state}.png",
            "placement": [dest[0], dest[1]],
            "fitted_size": [fitted.width, fitted.height],
        }

    build_contact(patches, args.out_dir / "otto_generated_face_patch_contact.png")
    full_overlays[0].save(
        args.out_dir / "otto_generated_face_patch_preview.gif",
        save_all=True,
        append_images=full_overlays[1:],
        duration=120,
        loop=0,
        disposal=2,
    )
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(args.out_dir), "states": len(STATES)}, indent=2))


if __name__ == "__main__":
    main()
