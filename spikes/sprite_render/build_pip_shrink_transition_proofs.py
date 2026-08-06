#!/usr/bin/env python3
"""Build Pip shrink/grow transition proof sheets from a locked sprite source.

These are blocking/intake proofs for the opening and ending size-change beats.
They deliberately transform existing Pip pixels only; no face, costume, or body
details are generated.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--mode", choices=("shrink_down", "shrink_back_up"), required=True)
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--canvas", type=int, default=640)
    parser.add_argument("--anchor-y", type=int, default=588)
    return parser.parse_args()


def alpha_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    bbox = img.getchannel("A").getbbox()
    if not bbox:
        raise ValueError("source image has no alpha content")
    return bbox


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def content_anchor(img: Image.Image) -> tuple[float, float]:
    alpha = img.getchannel("A")
    left, top, right, bottom = alpha_bbox(img)
    band_top = max(top, bottom - max(3, round((bottom - top) * 0.08)))
    xs: list[int] = []
    for y in range(band_top, bottom):
        for x in range(left, right):
            if alpha.getpixel((x, y)) > 8:
                xs.append(x)
    return ((sum(xs) / len(xs)) if xs else ((left + right) / 2), bottom)


def tint_pulse(size: tuple[int, int], amount: float) -> Image.Image:
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx = size[0] // 2
    cy = int(size[1] * 0.58)
    max_r = int(size[0] * (0.22 + 0.18 * amount))
    for i in range(4):
        r = max_r + i * 18
        alpha = int(68 * amount * (1.0 - i * 0.18))
        if alpha <= 0:
            continue
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 217, 120, alpha), width=3)
    return overlay.filter(ImageFilter.GaussianBlur(radius=1.2))


def scale_for(mode: str, t: float) -> float:
    e = ease_in_out(t)
    if mode == "shrink_down":
        return 1.55 * (1.0 - e) + 1.0 * e
    return 1.0 * (1.0 - e) + 1.55 * e


def squash_for(t: float) -> tuple[float, float]:
    # A tiny anticipation/settle compression. Kept small so it reads as a size
    # effect, not model deformation.
    pulse = math.sin(t * math.pi) ** 2
    return (1.0 + 0.035 * pulse, 1.0 - 0.025 * pulse)


def build_frames(source: Image.Image, args: argparse.Namespace) -> tuple[list[Image.Image], list[dict]]:
    cropped = source.crop(alpha_bbox(source))
    source_anchor = content_anchor(cropped)
    anchor_canvas = (args.canvas // 2, args.anchor_y)
    frames: list[Image.Image] = []
    reports: list[dict] = []
    prev_anchor: tuple[float, float] | None = None

    for index in range(args.frames):
        t = index / max(1, args.frames - 1)
        scale = scale_for(args.mode, t)
        sx, sy = squash_for(t)
        width = max(1, round(cropped.width * scale * sx))
        height = max(1, round(cropped.height * scale * sy))
        resized = cropped.resize((width, height), Image.Resampling.LANCZOS)
        resized_anchor = (source_anchor[0] * scale * sx, source_anchor[1] * scale * sy)

        sprite_canvas = Image.new("RGBA", (args.canvas, args.canvas), (0, 0, 0, 0))
        pulse = math.sin(t * math.pi)

        x = round(anchor_canvas[0] - resized_anchor[0])
        y = round(anchor_canvas[1] - resized_anchor[1])
        sprite_canvas.alpha_composite(resized, (x, y))
        norm_anchor = content_anchor(sprite_canvas)
        delta = math.dist(norm_anchor, prev_anchor) if prev_anchor else 0.0
        prev_anchor = norm_anchor
        canvas = Image.new("RGBA", (args.canvas, args.canvas), (0, 0, 0, 0))
        if pulse > 0.05:
            canvas = Image.alpha_composite(canvas, tint_pulse(canvas.size, pulse))
        canvas = Image.alpha_composite(canvas, sprite_canvas)
        frames.append(canvas)
        reports.append(
            {
                "index": index,
                "scale": round(scale, 4),
                "squash_x": round(sx, 4),
                "squash_y": round(sy, 4),
                "offset": [x, y],
                "anchor": [round(norm_anchor[0], 3), round(norm_anchor[1], 3)],
                "anchor_delta_px": round(delta, 3),
            }
        )
    return frames, reports


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
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    source = Image.open(args.source).convert("RGBA")
    frames, reports = build_frames(source, args)
    anchor = (args.canvas // 2, args.anchor_y)

    for i, frame in enumerate(frames):
        frame.save(out / f"{args.prefix}_{i:03d}.png")
    sheet = Image.new("RGBA", (args.canvas * len(frames), args.canvas), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        sheet.alpha_composite(frame, (i * args.canvas, 0))
    sheet.save(out / f"{args.prefix}_spritesheet.png")
    save_contact(frames, out / f"{args.prefix}_contact.png", args.prefix, anchor)
    save_gif(frames, out / f"{args.prefix}_preview.gif", args.fps)

    warnings = [
        {"frame": report["index"], "type": "jitter", "delta_px": report["anchor_delta_px"]}
        for report in reports
        if report["anchor_delta_px"] > 1.25
    ]
    manifest = {
        "prefix": args.prefix,
        "mode": args.mode,
        "source": str(Path(args.source).resolve()),
        "fps": args.fps,
        "frame_count": len(frames),
        "canvas": [args.canvas, args.canvas],
        "anchor_canvas": [anchor[0], anchor[1]],
        "frames": reports,
        "warnings": warnings,
        "notes": [
            "Proof/blocking transition only; final normal-size scene staging is not authored yet.",
            "Transforms existing Pip pixels only; no face, costume, or body details are generated.",
            "Foot/contact anchor remains fixed so the size change reads as happening in place.",
        ],
    }
    (out / f"{args.prefix}_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"frames": len(frames), "warnings": len(warnings), "max_jitter_px": max((r["anchor_delta_px"] for r in reports), default=0)}, indent=2))


if __name__ == "__main__":
    main()
