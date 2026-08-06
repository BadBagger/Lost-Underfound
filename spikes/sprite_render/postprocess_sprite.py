#!/usr/bin/env python3
"""Post-process Blender frames into R1/R2/R3 sprite spike deliverables."""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
SPIKE = ROOT / "spikes" / "sprite_render"
RAW = SPIKE / "frames_raw"
OUT = SPIKE / "out"
PLATE = ROOT / "ags" / "room1" / "background" / "discovery.png"
PALETTE_JSON_CANDIDATES = [ROOT / "palette.json", SPIKE / "palette.json"]
FPS = 12
TARGET_HEIGHT = 143
CANVAS_PAD = 18
OUTLINE = (22, 12, 13, 255)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"expected 6-digit hex color, got {value!r}")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def alpha_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    bbox = img.getchannel("A").getbbox()
    if not bbox:
        return (0, 0, img.width, img.height)
    return bbox


def fit_to_height(img: Image.Image, height: int) -> Image.Image:
    bbox = alpha_bbox(img)
    cropped = img.crop(bbox)
    scale = height / max(1, cropped.height)
    size = (max(1, round(cropped.width * scale)), height)
    return cropped.resize(size, Image.Resampling.LANCZOS)


def load_hero_palette() -> tuple[list[tuple[int, int, int]], Path]:
    for path in PALETTE_JSON_CANDIDATES:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        hero = data.get("hero")
        if not isinstance(hero, dict):
            continue
        colors = [hex_to_rgb(value) for value in hero.values() if isinstance(value, str)]
        if colors:
            deduped: list[tuple[int, int, int]] = []
            for color in colors:
                if color not in deduped:
                    deduped.append(color)
            return deduped, path
    raise FileNotFoundError("no palette.json with a non-empty hero object was found")


def nearest_color(pixel: tuple[int, int, int], palette: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    return min(palette, key=lambda c: (pixel[0] - c[0]) ** 2 + (pixel[1] - c[1]) ** 2 + (pixel[2] - c[2]) ** 2)


def posterize(img: Image.Image, palette: list[tuple[int, int, int]]) -> Image.Image:
    rgba = img.convert("RGBA")
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pixels[x, y]
            if a:
                nr, ng, nb = nearest_color((r, g, b), palette)
                pixels[x, y] = (nr, ng, nb, a)
    return rgba


def outlined(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    alpha = rgba.getchannel("A")
    dilated = alpha.filter(ImageFilter.MaxFilter(7))
    outline_alpha = Image.eval(dilated, lambda px: 255 if px > 10 else 0)
    outline = Image.new("RGBA", rgba.size, OUTLINE)
    outline.putalpha(outline_alpha)
    outline = Image.alpha_composite(outline, rgba)
    return outline


def color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def palette_coverage(frames: Iterable[Image.Image], palette: list[tuple[int, int, int]], threshold: float = 12.0) -> dict:
    total = 0
    close = 0
    max_distance = 0.0
    for img in frames:
        rgba = img.convert("RGBA")
        for r, g, b, a in rgba.getdata():
            if a < 8:
                continue
            total += 1
            dist = min(color_distance((r, g, b), color) for color in palette)
            max_distance = max(max_distance, dist)
            if dist <= threshold:
                close += 1
    coverage = close / total if total else 1
    return {"threshold_rgb_distance": threshold, "coverage": coverage, "coverage_pct": round(coverage * 100, 2), "max_distance": round(max_distance, 2), "passes_90pct": coverage >= 0.9}


def normalize_frames(frames: list[Image.Image]) -> tuple[list[Image.Image], list[dict], tuple[int, int]]:
    fitted = [fit_to_height(frame, TARGET_HEIGHT) for frame in frames]
    max_w = max(frame.width for frame in fitted) + CANVAS_PAD * 2
    max_h = TARGET_HEIGHT + CANVAS_PAD * 2
    anchor_x = max_w // 2
    anchor_y = CANVAS_PAD + TARGET_HEIGHT
    output = []
    offsets = []
    for index, frame in enumerate(fitted):
        canvas = Image.new("RGBA", (max_w, max_h), (0, 0, 0, 0))
        x = anchor_x - frame.width // 2
        y = anchor_y - frame.height
        canvas.alpha_composite(frame, (x, y))
        output.append(canvas)
        offsets.append({"index": index, "file": f"walk_{index:03d}.png", "x": x, "y": y, "w": frame.width, "h": frame.height, "anchor": [anchor_x, anchor_y]})
    return output, offsets, (max_w, max_h)


def save_sheet(frames: list[Image.Image], path: Path) -> tuple[int, int]:
    width = sum(frame.width for frame in frames)
    height = max(frame.height for frame in frames)
    sheet = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    x = 0
    for frame in frames:
        sheet.alpha_composite(frame, (x, 0))
        x += frame.width
    sheet.save(path)
    return sheet.size


def save_contact(frames: list[Image.Image], path: Path, label: str) -> None:
    cols = min(8, len(frames))
    rows = math.ceil(len(frames) / cols)
    cell_w = frames[0].width
    cell_h = frames[0].height + 24
    contact = Image.new("RGBA", (cols * cell_w, rows * cell_h), (128, 128, 128, 255))
    draw = ImageDraw.Draw(contact)
    for i, frame in enumerate(frames):
        x = (i % cols) * cell_w
        y = (i // cols) * cell_h + 22
        contact.alpha_composite(frame, (x, y))
        draw.text((x + 4, y - 20), f"{label} #{i:02d}", fill=(255, 244, 215, 255))
    contact.save(path)


def save_composite_video(frames: list[Image.Image], path: Path, sprite_only: bool = False) -> None:
    tmp = OUT / f"tmp_{path.stem}"
    tmp.mkdir(parents=True, exist_ok=True)
    plate = Image.open(PLATE).convert("RGBA")
    if sprite_only:
        plate = Image.new("RGBA", (640, 360), (128, 128, 128, 255))
    for i, frame in enumerate(frames):
        canvas = plate.copy()
        x = 520 if not sprite_only else 320
        y = 620 if not sprite_only else 300
        px = x - frame.width // 2
        py = y - frame.height
        canvas.alpha_composite(frame, (px, py))
        canvas.convert("RGB").save(tmp / f"frame_{i:03d}.png")
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-stream_loop",
        "2",
        "-i",
        str(tmp / "frame_%03d.png"),
        "-t",
        str(round(len(frames) / FPS * 3, 3)),
        "-vf",
        "format=yuv420p",
        str(path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw_paths = sorted(RAW.glob("walk_raw_*.png"))
    if not raw_paths:
        raise SystemExit(f"no raw frames found in {RAW}")
    raw_source = [Image.open(path).convert("RGBA") for path in raw_paths]
    palette, palette_source = load_hero_palette()

    normalized_raw, offsets, frame_size = normalize_frames(raw_source)
    r2 = [posterize(frame, palette) for frame in normalized_raw]
    r3 = [outlined(frame) for frame in r2]
    variants = {
        "R1": normalized_raw,
        "R2": r2,
        "R3": r3,
    }
    sheet_sizes = {}
    coverage = {}
    for name, frames in variants.items():
        sheet_sizes[name] = save_sheet(frames, OUT / f"walk_{name}.png")
        save_contact(frames, OUT / f"contact_{name}.png", name)
        save_composite_video(frames, OUT / f"composite_{name}.mp4")
        coverage[name] = palette_coverage(frames, palette)
    save_composite_video(r3, OUT / "sprite_only_R3.mp4", sprite_only=True)

    manifest = {
        "format": "matte-offsets-compatible",
        "fps": FPS,
        "frame_count": len(normalized_raw),
        "frame_size": list(frame_size),
        "sheet_sizes": {key: list(value) for key, value in sheet_sizes.items()},
        "anchor": offsets[0]["anchor"],
        "frames": offsets,
        "palette_source": str(palette_source.relative_to(ROOT)),
        "palette_colors": palette,
        "palette_coverage": coverage,
        "assumptions": [
            "No root palette.json was present, so postprocess used spikes/sprite_render/palette.json hero colors.",
            "Composite position uses the discovery room walkable band at approximately x=520, y=620.",
            "Postprocess quantizes each rendered source pixel to the nearest hero palette entry, then outlines.",
        ],
    }
    (OUT / "walk_offsets.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"frames": len(normalized_raw), "frame_size": frame_size, "sheet_sizes": sheet_sizes, "palette_coverage": coverage}, indent=2))


if __name__ == "__main__":
    main()
