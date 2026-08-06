#!/usr/bin/env python3
"""Build Scuttle's dash sheet from six Blender rig-rendered frames."""

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
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--prefix", default="scuttle_dash_rig")
    parser.add_argument("--canvas", type=int, default=512)
    parser.add_argument("--target-height", type=int, default=176)
    parser.add_argument("--fps", type=int, default=16)
    return parser.parse_args()


def alpha_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    bbox = img.getchannel("A").getbbox()
    return bbox if bbox else (0, 0, img.width, img.height)


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


def paste_on_canvas(sprite: Image.Image, canvas_size: int, anchor_canvas: tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    ax, ay = anchor_from_alpha(sprite)
    canvas.alpha_composite(sprite, (round(anchor_canvas[0] - ax), round(anchor_canvas[1] - ay)))
    return canvas


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
    canvas.alpha_composite(scaled, (round(ax - src_ax * sx), round(ay - src_ay * sy)))
    return canvas


def smear(sprite: Image.Image, factor: float, blur: int) -> Image.Image:
    stretched = scale_about_anchor(sprite, factor, 0.76)
    blurred = stretched.filter(ImageFilter.GaussianBlur(radius=blur))
    ghost = Image.blend(blurred, stretched, 0.34)
    alpha = ghost.getchannel("A")
    mask = Image.new("L", ghost.size, 0)
    draw = ImageDraw.Draw(mask)
    left, top, right, bottom = alpha_bbox(ghost)
    width = max(1, right - left)
    for x in range(left, right):
        t = (x - left) / width
        draw.line((x, top, x, bottom), fill=round(255 * (0.38 + 0.62 * t)))
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
        draw.text((x + 5, 5), f"{prefix}_{i:02d}{' SMEAR' if i in {2, 3} else ''}", fill=(255, 244, 215, 255))
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
    source_dir = Path(args.source_dir)
    sources = sorted(source_dir.glob("*.png"))
    if len(sources) != 6:
        raise SystemExit(f"Expected 6 rig frames in {source_dir}, found {len(sources)}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    anchor_target = (args.canvas // 2, args.canvas - 38)
    frames: list[Image.Image] = []
    reports = []
    for i, source in enumerate(sources):
        sprite = fit_height(Image.open(source).convert("RGBA"), args.target_height)
        frame = paste_on_canvas(sprite, args.canvas, anchor_target)
        if i == 2:
            frame = smear(frame, 1.8, 2)
        elif i == 3:
            frame = smear(frame, 2.12, 3)
        frame = paste_on_canvas(outline(frame), args.canvas, anchor_target)
        frame_path = out / f"{args.prefix}_{i:03d}.png"
        frame.save(frame_path)
        anchor = anchor_from_alpha(frame)
        reports.append(
            {
                "index": i,
                "file": frame_path.name,
                "source": source.name,
                "type": "smear" if i in {2, 3} else "solid",
                "anchor": [round(anchor[0], 3), round(anchor[1], 3)],
                "anchor_error_px": round(math.dist(anchor, anchor_target), 3),
            }
        )
        frames.append(frame)

    sheet = Image.new("RGBA", (args.canvas * len(frames), args.canvas), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        sheet.alpha_composite(frame, (i * args.canvas, 0))
    sheet.save(out / f"{args.prefix}_spritesheet.png")
    save_contact(frames, out / f"{args.prefix}_contact.png", args.prefix, anchor_target)
    save_gif(frames, out / f"{args.prefix}_preview.gif", args.fps)

    warnings = [
        {"frame": r["index"], "type": "anchor_error", "px": r["anchor_error_px"]}
        for r in reports
        if r["anchor_error_px"] > 1.5
    ]
    manifest = {
        "prefix": args.prefix,
        "fps": args.fps,
        "frame_count": len(frames),
        "canvas": [args.canvas, args.canvas],
        "anchor_canvas": [anchor_target[0], anchor_target[1]],
        "source_dir": str(source_dir.resolve()),
        "frames": reports,
        "warnings": warnings,
        "notes": [
            "Built from six Blender rig-rendered Scuttle frames, not one static source.",
            "Frames 2 and 3 are intentional smear frames.",
            "Every frame is re-anchored after outline/smear so the game receives stable sprite cells.",
        ],
    }
    (out / f"{args.prefix}_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"frames": len(frames), "warnings": len(warnings), "max_anchor_error": max(r["anchor_error_px"] for r in reports)}, indent=2))


if __name__ == "__main__":
    main()
