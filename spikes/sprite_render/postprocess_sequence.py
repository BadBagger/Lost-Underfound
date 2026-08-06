#!/usr/bin/env python3
"""Post-process arbitrary transparent sprite sequences with outline and QA."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


OUTLINE = (22, 12, 13, 255)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--prefix", default="sprite")
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--target-height", type=int, default=360)
    parser.add_argument("--canvas", type=int, default=512)
    parser.add_argument("--jitter-warn-px", type=float, default=4.0)
    return parser.parse_args()


def alpha_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    bbox = img.getchannel("A").getbbox()
    return bbox if bbox else (0, 0, img.width, img.height)


def fit_to_height(img: Image.Image, height: int) -> Image.Image:
    cropped = img.crop(alpha_bbox(img))
    scale = height / max(1, cropped.height)
    width = max(1, round(cropped.width * scale))
    return cropped.resize((width, height), Image.Resampling.LANCZOS)


def outline(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    alpha = rgba.getchannel("A")
    dilated = alpha.filter(ImageFilter.MaxFilter(7))
    outline_alpha = Image.eval(dilated, lambda px: 255 if px > 8 else 0)
    layer = Image.new("RGBA", rgba.size, OUTLINE)
    layer.putalpha(outline_alpha)
    return Image.alpha_composite(layer, rgba)


def anchor_from_alpha(img: Image.Image) -> tuple[float, float]:
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return (img.width / 2, img.height)
    left, top, right, bottom = bbox
    band_top = max(top, bottom - max(2, round((bottom - top) * 0.08)))
    xs: list[int] = []
    for y in range(band_top, bottom):
        for x in range(left, right):
            if alpha.getpixel((x, y)) > 8:
                xs.append(x)
    if xs:
        return (sum(xs) / len(xs), bottom)
    return ((left + right) / 2, bottom)


def normalize(frames: list[Image.Image], target_height: int, canvas_size: int) -> tuple[list[Image.Image], list[dict]]:
    fitted = [fit_to_height(frame, target_height) for frame in frames]
    anchor_canvas = (canvas_size // 2, canvas_size - 26)
    normalized: list[Image.Image] = []
    reports: list[dict] = []
    prev_anchor: tuple[float, float] | None = None
    for index, frame in enumerate(fitted):
        anchor = anchor_from_alpha(frame)
        canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        x = round(anchor_canvas[0] - anchor[0])
        y = round(anchor_canvas[1] - anchor[1])
        canvas.alpha_composite(frame, (x, y))
        norm_anchor = anchor_from_alpha(canvas)
        delta = 0.0
        if prev_anchor is not None:
            delta = math.dist(norm_anchor, prev_anchor)
        prev_anchor = norm_anchor
        normalized.append(canvas)
        reports.append(
            {
                "index": index,
                "anchor": [round(norm_anchor[0], 3), round(norm_anchor[1], 3)],
                "anchor_delta_px": round(delta, 3),
                "source_size": [frame.width, frame.height],
                "offset": [x, y],
            }
        )
    return normalized, reports


def save_sheet(frames: list[Image.Image], path: Path) -> list[int]:
    sheet = Image.new("RGBA", (sum(frame.width for frame in frames), max(frame.height for frame in frames)), (0, 0, 0, 0))
    x = 0
    for frame in frames:
        sheet.alpha_composite(frame, (x, 0))
        x += frame.width
    sheet.save(path)
    return [sheet.width, sheet.height]


def save_contact(frames: list[Image.Image], path: Path, prefix: str, anchor: tuple[int, int]) -> None:
    cols = min(6, len(frames))
    rows = math.ceil(len(frames) / cols)
    cell_w = frames[0].width
    cell_h = frames[0].height + 24
    contact = Image.new("RGBA", (cols * cell_w, rows * cell_h), (128, 128, 128, 255))
    draw = ImageDraw.Draw(contact)
    for i, frame in enumerate(frames):
        x = (i % cols) * cell_w
        y = (i // cols) * cell_h + 22
        contact.alpha_composite(frame, (x, y))
        ax = x + anchor[0]
        ay = y + anchor[1]
        draw.line((ax - 10, ay, ax + 10, ay), fill=(255, 64, 128, 255), width=1)
        draw.line((ax, ay - 10, ax, ay + 10), fill=(255, 64, 128, 255), width=1)
        draw.text((x + 5, y - 20), f"{prefix} {i:02d}", fill=(255, 244, 215, 255))
    contact.save(path)


def save_gif(frames: list[Image.Image], path: Path, fps: int) -> None:
    duration = round(1000 / fps)
    bg = []
    for frame in frames:
        canvas = Image.new("RGBA", frame.size, (128, 128, 128, 255))
        canvas.alpha_composite(frame)
        bg.append(canvas.convert("P", palette=Image.Palette.ADAPTIVE))
    bg[0].save(path, save_all=True, append_images=bg[1:], duration=duration, loop=0, disposal=2)


def main() -> None:
    args = parse_args()
    raw_dir = Path(args.raw)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = sorted(raw_dir.glob("*.png"))
    if not paths:
        raise SystemExit(f"no PNG frames found in {raw_dir}")
    source = [Image.open(path).convert("RGBA") for path in paths]
    normalized, frame_reports = normalize(source, args.target_height, args.canvas)
    outlined = [outline(frame) for frame in normalized]

    for i, frame in enumerate(outlined):
        frame.save(out_dir / f"{args.prefix}_{i:03d}.png")
    sheet_size = save_sheet(outlined, out_dir / f"{args.prefix}_spritesheet.png")
    anchor = (args.canvas // 2, args.canvas - 26)
    save_contact(outlined, out_dir / f"{args.prefix}_contact.png", args.prefix, anchor)
    save_gif(outlined, out_dir / f"{args.prefix}_preview.gif", args.fps)
    warnings = [
        {"frame": report["index"], "type": "jitter", "delta_px": report["anchor_delta_px"]}
        for report in frame_reports
        if report["anchor_delta_px"] > args.jitter_warn_px
    ]
    manifest = {
        "prefix": args.prefix,
        "fps": args.fps,
        "canvas": [args.canvas, args.canvas],
        "target_height": args.target_height,
        "frame_count": len(outlined),
        "sheet_size": sheet_size,
        "anchor_canvas": [anchor[0], anchor[1]],
        "frames": frame_reports,
        "warnings": warnings,
        "rules": [
            "All frames normalized to fixed canvas.",
            "Anchor derived from bottom alpha band and locked to anchor_canvas.",
            "Warm 3px outline added after normalization.",
            "No costume, face, or color overlays are drawn.",
        ],
    }
    (out_dir / f"{args.prefix}_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"frames": len(outlined), "warnings": len(warnings), "max_jitter_px": max((r["anchor_delta_px"] for r in frame_reports), default=0)}, indent=2))


if __name__ == "__main__":
    main()
