#!/usr/bin/env python3
"""Build a six-frame Scuttle dash proof with explicit smear frames.

This is a sprite-production proof from the rigged Meshy render, not final frame
admission. Frames 2 and 3 are intentionally stylized smear frames per Scuttle's
Act 1 dash contract: readable solid poses immediately before and after.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


OUTLINE = (22, 12, 13, 255)
BG = (128, 128, 128, 255)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--prefix", default="scuttle_dash")
    parser.add_argument("--canvas", type=int, default=512)
    parser.add_argument("--target-height", type=int, default=210)
    parser.add_argument("--fps", type=int, default=16)
    return parser.parse_args()


def alpha_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    bbox = img.getchannel("A").getbbox()
    return bbox if bbox else (0, 0, img.width, img.height)


def fit_height(img: Image.Image, height: int) -> Image.Image:
    crop = img.crop(alpha_bbox(img))
    scale = height / max(1, crop.height)
    return crop.resize((max(1, round(crop.width * scale)), height), Image.Resampling.LANCZOS)


def outline(img: Image.Image) -> Image.Image:
    alpha = img.getchannel("A")
    dilated = alpha.filter(ImageFilter.MaxFilter(7))
    outline_alpha = Image.eval(dilated, lambda p: 255 if p > 8 else 0)
    layer = Image.new("RGBA", img.size, OUTLINE)
    layer.putalpha(outline_alpha)
    return Image.alpha_composite(layer, img)


def anchor_from_alpha(img: Image.Image) -> tuple[float, float]:
    alpha = img.getchannel("A")
    left, top, right, bottom = alpha_bbox(img)
    band_top = max(top, bottom - max(2, round((bottom - top) * 0.08)))
    xs: list[int] = []
    for y in range(band_top, bottom):
        for x in range(left, right):
            if alpha.getpixel((x, y)) > 8:
                xs.append(x)
    return ((sum(xs) / len(xs)) if xs else (left + right) / 2, bottom)


def scale_about_anchor(img: Image.Image, sx: float, sy: float) -> Image.Image:
    bbox = alpha_bbox(img)
    crop = img.crop(bbox)
    w = max(1, round(crop.width * sx))
    h = max(1, round(crop.height * sy))
    scaled = crop.resize((w, h), Image.Resampling.BICUBIC)
    canvas = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ax, ay = anchor_from_alpha(img)
    src_ax = ax - bbox[0]
    src_ay = ay - bbox[1]
    dst_ax = src_ax * sx
    dst_ay = src_ay * sy
    canvas.alpha_composite(scaled, (round(ax - dst_ax), round(ay - dst_ay)))
    return canvas


def paste_on_canvas(sprite: Image.Image, canvas_size: int, anchor_canvas: tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    ax, ay = anchor_from_alpha(sprite)
    canvas.alpha_composite(sprite, (round(anchor_canvas[0] - ax), round(anchor_canvas[1] - ay)))
    return canvas


def smear(sprite: Image.Image, factor: float, blur: int, fade_tail: bool = True) -> Image.Image:
    stretched = scale_about_anchor(sprite, factor, 0.78)
    blurred = stretched.filter(ImageFilter.GaussianBlur(radius=blur))
    # Keep a crisp hint of the head/eyes by compositing a faint original over the blur.
    ghost = Image.blend(blurred, stretched, 0.42)
    if fade_tail:
        alpha = ghost.getchannel("A")
        mask = Image.new("L", ghost.size, 0)
        draw = ImageDraw.Draw(mask)
        bbox = alpha_bbox(ghost)
        left, top, right, bottom = bbox
        width = max(1, right - left)
        for x in range(left, right):
            t = (x - left) / width
            # Motion reads left-to-right; keep leading side stronger.
            value = round(255 * (0.42 + 0.58 * t))
            draw.line((x, top, x, bottom), fill=value)
        alpha = ImageChops.multiply(alpha, mask)
        ghost.putalpha(alpha)
    return ghost


def save_contact(frames: list[Image.Image], path: Path, prefix: str, anchor: tuple[int, int]) -> None:
    cols = len(frames)
    cell = frames[0].width
    sheet = Image.new("RGBA", (cell * cols, cell + 26), BG)
    draw = ImageDraw.Draw(sheet)
    for i, frame in enumerate(frames):
        x = i * cell
        sheet.alpha_composite(frame, (x, 24))
        ax = x + anchor[0]
        ay = 24 + anchor[1]
        draw.line((ax - 9, ay, ax + 9, ay), fill=(255, 64, 128, 255), width=1)
        draw.line((ax, ay - 9, ax, ay + 9), fill=(255, 64, 128, 255), width=1)
        label = f"{prefix}_{i:02d}"
        if i in {2, 3}:
            label += " SMEAR"
        draw.text((x + 5, 5), label, fill=(255, 244, 215, 255))
    sheet.save(path)


def save_gif(frames: list[Image.Image], path: Path, fps: int) -> None:
    duration = round(1000 / fps)
    bg_frames = []
    for frame in frames:
        bg = Image.new("RGBA", frame.size, BG)
        bg.alpha_composite(frame)
        bg_frames.append(bg.convert("P", palette=Image.Palette.ADAPTIVE))
    bg_frames[0].save(path, save_all=True, append_images=bg_frames[1:], duration=duration, loop=0, disposal=2)


def main() -> None:
    args = parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = Image.open(args.source).convert("RGBA")
    base = fit_height(base, args.target_height)
    base_canvas = paste_on_canvas(base, args.canvas, (args.canvas // 2, args.canvas - 38))

    poses = [
        scale_about_anchor(base_canvas, 1.0, 1.0),    # readable ready
        scale_about_anchor(base_canvas, 0.92, 1.04),  # launch coil
        smear(base_canvas, 1.82, 2),                  # smear travel
        smear(base_canvas, 2.18, 3),                  # stronger smear travel
        scale_about_anchor(base_canvas, 1.03, 0.98),  # readable landing
        scale_about_anchor(base_canvas, 0.96, 1.0),   # skitter off/settle
    ]
    # Lean poses slightly without breaking the anchor.
    poses[1] = poses[1].rotate(-4, resample=Image.Resampling.BICUBIC, center=(args.canvas // 2, args.canvas - 38))
    poses[4] = poses[4].rotate(3, resample=Image.Resampling.BICUBIC, center=(args.canvas // 2, args.canvas - 38))
    anchor_target = (args.canvas // 2, args.canvas - 38)
    frames = [paste_on_canvas(outline(pose), args.canvas, anchor_target) for pose in poses]

    reports = []
    prev = None
    for i, frame in enumerate(frames):
        frame_path = out / f"{args.prefix}_{i:03d}.png"
        frame.save(frame_path)
        anchor = anchor_from_alpha(frame)
        delta = 0.0 if prev is None else math.dist(anchor, prev)
        prev = anchor
        reports.append(
            {
                "index": i,
                "file": frame_path.name,
                "anchor": [round(anchor[0], 3), round(anchor[1], 3)],
                "anchor_delta_px": round(delta, 3),
                "type": "smear" if i in {2, 3} else "solid",
            }
        )

    sheet = Image.new("RGBA", (sum(f.width for f in frames), args.canvas), (0, 0, 0, 0))
    x = 0
    for frame in frames:
        sheet.alpha_composite(frame, (x, 0))
        x += frame.width
    sheet.save(out / f"{args.prefix}_spritesheet.png")
    save_contact(frames, out / f"{args.prefix}_contact.png", args.prefix, anchor_target)
    save_gif(frames, out / f"{args.prefix}_preview.gif", args.fps)
    manifest = {
        "prefix": args.prefix,
        "fps": args.fps,
        "frame_count": len(frames),
        "canvas": [args.canvas, args.canvas],
        "anchor_canvas": [anchor_target[0], anchor_target[1]],
        "source": str(Path(args.source).resolve()),
        "frames": reports,
        "warnings": [
            {"frame": r["index"], "type": "anchor_delta", "delta_px": r["anchor_delta_px"]}
            for r in reports
            if r["anchor_delta_px"] > 6 and r["type"] != "smear"
        ],
        "notes": [
            "Frames 2 and 3 are intentional smear frames.",
            "Frames 0 and 4 are crisp readable poses bracketing the smear.",
            "This proof uses 2D smear shaping from the rendered rig candidate.",
        ],
    }
    (out / f"{args.prefix}_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"frames": len(frames), "warnings": len(manifest["warnings"])}, indent=2))


if __name__ == "__main__":
    main()
