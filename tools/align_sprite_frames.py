#!/usr/bin/env python3
"""Normalize AI-generated sprite frames onto a fixed registration canvas.

The tool writes only to out/<anim>/ by default. It cuts alpha first, computes a
stable foot/contact anchor from the alpha mask, then composites each frame onto
a fixed transparent canvas so that every frame shares the same runtime anchor.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

import numpy as np

try:
    from PIL import Image, ImageDraw, ImageSequence
except ImportError:
    sys.exit("This tool requires Pillow: pip install Pillow")


IMAGE_EXTS = {".png", ".webp", ".jpg", ".jpeg"}
DEFAULT_EXCLUDED_STEMS = {
    "onion",
    "contact_sheet",
    "contact-sheet",
    "spritesheet",
    "preview",
}


def parse_pair(value: str, label: str) -> tuple[int, int]:
    match = re.fullmatch(r"\s*(\d+)\s*[x,]\s*(\d+)\s*", value)
    if not match:
        raise argparse.ArgumentTypeError(f"{label} must look like 512x512 or 256,480")
    return int(match.group(1)), int(match.group(2))


def natural_key(path: Path) -> list[object]:
    parts = re.split(r"(\d+)", path.stem.lower())
    return [int(part) if part.isdigit() else part for part in parts]


def is_review_artifact(path: Path) -> bool:
    stem = path.stem.lower()
    return stem in DEFAULT_EXCLUDED_STEMS or stem.endswith("-contact-sheet") or stem.endswith("_contact_sheet")


def list_frames(input_dir: Path, pattern: str) -> list[Path]:
    frames = sorted(
        [
            path
            for path in input_dir.glob(pattern)
            if path.is_file() and path.suffix.lower() in IMAGE_EXTS and not is_review_artifact(path)
        ],
        key=natural_key,
    )
    if not frames:
        raise SystemExit(f"{input_dir}: no image frames found")
    return frames


def dominant_corner_rgb(image: Image.Image) -> tuple[int, int, int]:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    corners = [
        pixels[0, 0],
        pixels[width - 1, 0],
        pixels[0, height - 1],
        pixels[width - 1, height - 1],
    ]
    # Quantize slightly so near-solid generated backgrounds still agree.
    quantized = [tuple((channel // 8) * 8 for channel in corner[:3]) for corner in corners]
    most_common = Counter(quantized).most_common(1)[0][0]
    return most_common


def has_useful_alpha(image: Image.Image) -> bool:
    if image.mode not in ("RGBA", "LA") and "transparency" not in image.info:
        return False
    alpha = np.asarray(image.convert("RGBA").getchannel("A"))
    return bool(np.any(alpha < 250))


def resolve_bg_mode(image: Image.Image, requested: str) -> str:
    if requested != "auto":
        return requested
    return "alpha" if has_useful_alpha(image) else "flat"


def cut_flat_alpha(image: Image.Image, tolerance: int) -> Image.Image:
    rgba = image.convert("RGBA")
    bg = np.array(dominant_corner_rgb(rgba), dtype=np.int16)
    arr = np.asarray(rgba).copy()
    rgb = arr[:, :, :3].astype(np.int16)
    dist = np.sqrt(np.sum((rgb - bg) ** 2, axis=2))
    alpha = arr[:, :, 3]
    remove = dist <= tolerance
    alpha[remove] = 0

    # Preserve partial edge alpha instead of hard chewing generated antialiasing.
    fringe = (dist > tolerance) & (dist <= tolerance * 2)
    if np.any(fringe):
        ramp = np.clip((dist - tolerance) / max(1, tolerance), 0.0, 1.0)
        alpha[fringe] = np.minimum(alpha[fringe], (ramp[fringe] * 255).astype(np.uint8))

    # Despill the closest one-pixel-ish edge by nudging RGB away from the matte.
    edge = (alpha > 0) & (dist <= tolerance * 3)
    if np.any(edge):
        strength = np.clip(1.0 - (dist / max(1, tolerance * 3)), 0.0, 1.0)[:, :, None]
        corrected = rgb + ((rgb - bg) * strength * 0.35)
        arr[:, :, :3] = np.where(edge[:, :, None], np.clip(corrected, 0, 255), arr[:, :, :3]).astype(np.uint8)

    arr[:, :, 3] = alpha
    return Image.fromarray(arr, "RGBA")


def cut_rembg_alpha(image: Image.Image) -> Image.Image:
    try:
        from rembg import remove
    except ImportError:
        raise SystemExit("BG_MODE=rembg requires optional deps: pip install rembg onnxruntime")
    return remove(image.convert("RGBA")).convert("RGBA")


def prepare_alpha(image: Image.Image, mode: str, tolerance: int) -> tuple[Image.Image, str]:
    resolved = resolve_bg_mode(image, mode)
    if resolved == "alpha":
        return image.convert("RGBA"), resolved
    if resolved == "flat":
        return cut_flat_alpha(image, tolerance), resolved
    if resolved == "rembg":
        return cut_rembg_alpha(image), resolved
    raise SystemExit(f"unsupported bg mode: {mode}")


def content_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    alpha = np.asarray(image.getchannel("A"))
    ys, xs = np.where(alpha > 0)
    if len(xs) == 0:
        return None
    left = int(xs.min())
    top = int(ys.min())
    right = int(xs.max()) + 1
    bottom = int(ys.max()) + 1
    return left, top, right - left, bottom - top


def compute_anchor(image: Image.Image, bbox: tuple[int, int, int, int], foot_band: float) -> tuple[int, int, str]:
    alpha = np.asarray(image.getchannel("A"))
    x, y, width, height = bbox
    anchor_y = y + height - 1
    band_height = max(1, int(math.ceil(height * foot_band)))
    band_top = max(y, y + height - band_height)
    band = alpha[band_top : y + height, x : x + width] > 0
    ys, xs = np.where(band)
    if len(xs) >= 2:
        anchor_x = x + int(round((int(xs.min()) + int(xs.max())) / 2))
        return anchor_x, anchor_y, "bottom-band-midpoint"
    return x + width // 2, anchor_y, "bbox-center-fallback"


def overflow_amount(offset: tuple[int, int], size: tuple[int, int], canvas: tuple[int, int]) -> int:
    ox, oy = offset
    width, height = size
    canvas_w, canvas_h = canvas
    overflow = max(0, -ox, -oy, ox + width - canvas_w, oy + height - canvas_h)
    return int(overflow)


def draw_crosshair(draw: ImageDraw.ImageDraw, point: tuple[int, int], size: int = 9) -> None:
    x, y = point
    draw.line((x - size, y, x + size, y), fill=(255, 0, 255, 255), width=1)
    draw.line((x, y - size, x, y + size), fill=(255, 0, 255, 255), width=1)
    draw.ellipse((x - 2, y - 2, x + 2, y + 2), outline=(20, 12, 18, 255), width=1)


def save_contact_sheet(output_frames: list[Path], out_path: Path, anchor: tuple[int, int]) -> None:
    with Image.open(output_frames[0]) as first:
        cell_w, cell_h = first.size
    cols = min(6, len(output_frames))
    rows = math.ceil(len(output_frames) / cols)
    sheet = Image.new("RGBA", (cols * cell_w, rows * cell_h), (128, 128, 128, 255))
    draw = ImageDraw.Draw(sheet)
    for index, frame_path in enumerate(output_frames):
        image = Image.open(frame_path).convert("RGBA")
        col = index % cols
        row = index // cols
        origin = (col * cell_w, row * cell_h)
        sheet.alpha_composite(image, origin)
        draw_crosshair(draw, (origin[0] + anchor[0], origin[1] + anchor[1]))
        draw.text((origin[0] + 8, origin[1] + 8), f"{index:03d}", fill=(255, 0, 255, 255))
    sheet.save(out_path)


def save_preview_gif(output_frames: list[Path], out_path: Path, fps: int) -> None:
    duration_ms = max(1, int(round(1000 / fps)))
    frames = [Image.open(path).convert("RGBA") for path in output_frames]
    # GIF has no real alpha; composite over neutral grey for registration review.
    gif_frames = []
    for frame in frames:
        bg = Image.new("RGBA", frame.size, (128, 128, 128, 255))
        bg.alpha_composite(frame)
        gif_frames.append(bg.convert("P", palette=Image.Palette.ADAPTIVE))
    gif_frames[0].save(
        out_path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=duration_ms,
        loop=0,
        disposal=2,
    )


def save_spritesheet(output_frames: list[Path], out_path: Path, coords_path: Path, anim: str) -> None:
    frames = [Image.open(path).convert("RGBA") for path in output_frames]
    cell_w, cell_h = frames[0].size
    sheet = Image.new("RGBA", (cell_w * len(frames), cell_h), (0, 0, 0, 0))
    coords = {"anim": anim, "cell": [cell_w, cell_h], "frames": []}
    for index, frame in enumerate(frames):
        x = index * cell_w
        sheet.alpha_composite(frame, (x, 0))
        coords["frames"].append({"file": output_frames[index].name, "x": x, "y": 0, "w": cell_w, "h": cell_h})
    sheet.save(out_path)
    coords_path.write_text(json.dumps(coords, indent=2) + "\n", encoding="utf-8")


def process(args: argparse.Namespace) -> int:
    input_dir = args.input_dir.resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"input dir not found: {input_dir}")

    anim = args.anim or input_dir.name
    out_dir = (args.out_root / anim).resolve()
    if out_dir.exists() and args.clean:
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    frame_paths = list_frames(input_dir, args.glob)
    manifest = {
        "anim": anim,
        "source_dir": str(input_dir),
        "canvas": list(args.canvas),
        "anchor_canvas": list(args.anchor_canvas),
        "fps": args.fps,
        "bg_mode": args.bg_mode,
        "flat_tolerance": args.flat_tolerance,
        "foot_band": args.foot_band,
        "jitter_warn_px": args.jitter_warn_px,
        "frames": [],
        "warnings": [],
    }

    output_frames: list[Path] = []
    previous_anchor: tuple[int, int] | None = None
    max_jitter = 0.0
    overflow_seen = False

    for index, src_path in enumerate(frame_paths):
        with Image.open(src_path) as raw:
            cut, resolved_bg_mode = prepare_alpha(raw, args.bg_mode, args.flat_tolerance)

        bbox = content_bbox(cut)
        if bbox is None:
            manifest["warnings"].append({"frame": index, "type": "empty-alpha", "src": src_path.name})
            anchor_src = (cut.width // 2, cut.height - 1)
            anchor_method = "empty-fallback"
        else:
            anchor_x, anchor_y, anchor_method = compute_anchor(cut, bbox, args.foot_band)
            anchor_src = (anchor_x, anchor_y)

        delta = 0.0
        if previous_anchor is not None:
            delta = math.dist(anchor_src, previous_anchor)
            max_jitter = max(max_jitter, delta)
            if delta > args.jitter_warn_px:
                manifest["warnings"].append({"frame": index, "type": "jitter", "delta_px": round(delta, 2)})
        previous_anchor = anchor_src

        if bbox:
            bbox_x, bbox_y, bbox_w, bbox_h = bbox
            content = cut.crop((bbox_x, bbox_y, bbox_x + bbox_w, bbox_y + bbox_h))
            anchor_content = (anchor_src[0] - bbox_x, anchor_src[1] - bbox_y)
        else:
            content = cut
            anchor_content = anchor_src

        offset = (args.anchor_canvas[0] - anchor_content[0], args.anchor_canvas[1] - anchor_content[1])
        overflow = overflow_amount(offset, content.size, args.canvas)
        if overflow:
            overflow_seen = True
            manifest["warnings"].append({"frame": index, "type": "overflow", "px": overflow})

        out_file = f"{anim}_{index:03d}.png"
        out_path = out_dir / out_file
        canvas = Image.new("RGBA", args.canvas, (0, 0, 0, 0))
        if not overflow:
            canvas.alpha_composite(content, offset)
            canvas.save(out_path)
            output_frames.append(out_path)

        manifest["frames"].append(
            {
                "file": out_file,
                "src": src_path.name,
                "bbox": list(bbox) if bbox else None,
                "anchor_src": [anchor_src[0], anchor_src[1]],
                "anchor_content": [anchor_content[0], anchor_content[1]],
                "anchor_method": anchor_method,
                "anchor_delta_px": round(delta, 2),
                "paste_offset": [offset[0], offset[1]],
                "bg_mode": resolved_bg_mode,
            }
        )

    if output_frames and not overflow_seen:
        save_preview_gif(output_frames, out_dir / "preview.gif", args.fps)
        save_contact_sheet(output_frames, out_dir / "contact_sheet.png", args.anchor_canvas)
        if args.sheet:
            save_spritesheet(output_frames, out_dir / "spritesheet.png", out_dir / "spritesheet.coords.json", anim)

    manifest["summary"] = {
        "frames_processed": len(frame_paths),
        "warnings": len(manifest["warnings"]),
        "max_jitter_px": round(max_jitter, 2),
        "overflow_failed": overflow_seen,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(
        f"{len(frame_paths)} frames processed, {len(manifest['warnings'])} warnings, "
        f"max jitter {max_jitter:.2f}px."
    )
    if overflow_seen:
        print(f"FAIL: at least one frame overflows {args.canvas}; see {out_dir / 'manifest.json'}", file=sys.stderr)
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Registration-lock sprite frames onto a fixed canvas.")
    parser.add_argument("input_dir", type=Path, help="Directory containing source frames for one animation.")
    parser.add_argument("anim", nargs="?", help="Animation name. Defaults to input directory name.")
    parser.add_argument("--out-root", type=Path, default=Path("out"), help="Output root. Writes to <out-root>/<anim>/")
    parser.add_argument("--canvas", type=lambda value: parse_pair(value, "canvas"), default=(512, 512))
    parser.add_argument("--anchor-canvas", type=lambda value: parse_pair(value, "anchor-canvas"), default=(256, 480))
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--bg-mode", choices=("auto", "flat", "rembg", "alpha"), default="auto")
    parser.add_argument("--flat-tolerance", type=int, default=24)
    parser.add_argument("--foot-band", type=float, default=0.06)
    parser.add_argument("--jitter-warn-px", type=float, default=6)
    parser.add_argument("--sheet", action="store_true", help="Also write spritesheet.png and spritesheet.coords.json.")
    parser.add_argument("--glob", default="*", help="Input frame glob relative to input_dir, e.g. 'walk_*.png'.")
    parser.add_argument("--clean", action="store_true", help="Delete the target output folder before writing.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return process(args)


if __name__ == "__main__":
    raise SystemExit(main())
