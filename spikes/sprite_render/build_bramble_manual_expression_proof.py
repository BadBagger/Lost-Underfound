#!/usr/bin/env python3
"""Build a Bramble expression proof from manually aligned source plates.

The source plates are full-body Bramble images on magenta. To avoid the body
drift from generated variants, this keeps Bramble1 as the fixed body and only
copies a feathered face patch from each expression plate.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
SRC = Path(r"C:\Users\KyleB\OneDrive\Pictures\Lost Animation PNGS")
OUT_ROOT = ROOT / "spikes" / "sprite_render" / "bramble_manual_expression_intake"
RAW_DIR = OUT_ROOT / "manual_patch_raw"
OUT_DIR = OUT_ROOT / "manual_patch_out"
BEAT_ROOT = OUT_ROOT / "story_beats"

CANVAS = (512, 512)
ANCHOR_CANVAS = (256, 486)
TARGET_HEIGHT = 410
FPS = 12
MAGENTA = (255, 0, 255)
OUTLINE = (22, 12, 13, 255)

# Lasso-style face patch in source-plate coordinates. It includes brows, eyes,
# spectacles, and mouth, but avoids the bow tie and most body lint.
FACE_POLYGON = [
    (67, 98),
    (87, 80),
    (124, 69),
    (172, 70),
    (215, 83),
    (245, 111),
    (244, 148),
    (221, 178),
    (174, 190),
    (118, 189),
    (76, 172),
    (55, 140),
]


def remove_magenta(img: Image.Image, tolerance: int = 44) -> Image.Image:
    rgba = img.convert("RGBA")
    data = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = data[x, y]
            dist = math.sqrt((r - MAGENTA[0]) ** 2 + (g - MAGENTA[1]) ** 2 + (b - MAGENTA[2]) ** 2)
            pink_bg = r > 175 and b > 175 and g < 135 and r - g > 70 and b - g > 70
            purple_matte = r > 90 and b > 90 and g < 82 and abs(r - b) < 92
            if dist <= tolerance or pink_bg or purple_matte:
                data[x, y] = (0, 0, 0, 0)
    return rgba


def resize_rgba_clean(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Resize RGBA without letting hidden background colors leak into edges."""
    rgba = img.convert("RGBA")
    src = np.asarray(rgba).astype(np.float32)
    alpha = src[..., 3:4] / 255.0
    premul = src.copy()
    premul[..., :3] *= alpha

    premul_img = Image.fromarray(np.clip(premul, 0, 255).astype(np.uint8), "RGBA")
    resized = np.asarray(premul_img.resize(size, Image.Resampling.LANCZOS)).astype(np.float32)
    out_alpha = resized[..., 3:4] / 255.0
    out = resized.copy()
    nonzero = out_alpha[..., 0] > 0.001
    out[..., :3][nonzero] = out[..., :3][nonzero] / out_alpha[nonzero]
    out[..., :3][~nonzero] = 0
    out[..., 3] = np.clip(out[..., 3], 0, 255)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def alpha_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    bbox = img.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("empty alpha")
    return bbox


def align_to_master(img: Image.Image, master: Image.Image) -> tuple[Image.Image, tuple[int, int]]:
    bbox = alpha_bbox(img)
    master_bbox = alpha_bbox(master)
    src_anchor = ((bbox[0] + bbox[2]) / 2, bbox[3])
    dst_anchor = ((master_bbox[0] + master_bbox[2]) / 2, master_bbox[3])
    dx = round(dst_anchor[0] - src_anchor[0])
    dy = round(dst_anchor[1] - src_anchor[1])
    aligned = Image.new("RGBA", master.size, (0, 0, 0, 0))
    aligned.alpha_composite(img, (dx, dy))
    return aligned, (dx, dy)


def make_face_mask(size: tuple[int, int]) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(FACE_POLYGON, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(4))


def expression_plate(master: Image.Image, source: Image.Image, mask: Image.Image) -> Image.Image:
    patch = Image.new("RGBA", master.size, (0, 0, 0, 0))
    patch.alpha_composite(source)
    patch.putalpha(ImageChops.multiply(patch.getchannel("A"), mask))
    out = master.copy()
    out.alpha_composite(patch)
    return out


def crossfade(a: Image.Image, b: Image.Image, t: float) -> Image.Image:
    return Image.blend(a, b, t)


def normalize(img: Image.Image) -> Image.Image:
    bbox = alpha_bbox(img)
    cropped = img.crop(bbox)
    scale = TARGET_HEIGHT / cropped.height
    resized = resize_rgba_clean(cropped, (round(cropped.width * scale), TARGET_HEIGHT))
    rb = alpha_bbox(resized)
    xs: list[int] = []
    bottom = rb[3]
    band_top = max(rb[1], bottom - max(3, round((rb[3] - rb[1]) * 0.07)))
    alpha = resized.getchannel("A")
    for y in range(band_top, bottom):
        for x in range(rb[0], rb[2]):
            if alpha.getpixel((x, y)) > 8:
                xs.append(x)
    anchor_x = sum(xs) / len(xs) if xs else (rb[0] + rb[2]) / 2
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    canvas.alpha_composite(resized, (round(ANCHOR_CANVAS[0] - anchor_x), round(ANCHOR_CANVAS[1] - bottom)))
    return canvas


def outline(img: Image.Image) -> Image.Image:
    alpha = img.getchannel("A")
    dilated = alpha.filter(ImageFilter.MaxFilter(7))
    outline_alpha = Image.eval(dilated, lambda px: 255 if px > 8 else 0)
    layer = Image.new("RGBA", img.size, OUTLINE)
    layer.putalpha(outline_alpha)
    return Image.alpha_composite(layer, img)


def save_contact(frames: list[Image.Image], path: Path) -> None:
    cols = 6
    rows = math.ceil(len(frames) / cols)
    cell_h = CANVAS[1] + 24
    contact = Image.new("RGBA", (cols * CANVAS[0], rows * cell_h), (128, 128, 128, 255))
    draw = ImageDraw.Draw(contact)
    for index, frame in enumerate(frames):
        x = (index % cols) * CANVAS[0]
        y = (index // cols) * cell_h + 22
        contact.alpha_composite(frame, (x, y))
        ax = x + ANCHOR_CANVAS[0]
        ay = y + ANCHOR_CANVAS[1]
        draw.line((ax - 10, ay, ax + 10, ay), fill=(255, 64, 128, 255))
        draw.line((ax, ay - 10, ax, ay + 10), fill=(255, 64, 128, 255))
        draw.text((x + 5, y - 20), f"{index:02d}", fill=(255, 244, 215, 255))
    contact.save(path)


def save_gif(frames: list[Image.Image], path: Path) -> None:
    duration = round(1000 / FPS)
    bg: list[Image.Image] = []
    for frame in frames:
        canvas = Image.new("RGBA", frame.size, (128, 128, 128, 255))
        canvas.alpha_composite(frame)
        bg.append(canvas.convert("P", palette=Image.Palette.ADAPTIVE))
    bg[0].save(path, save_all=True, append_images=bg[1:], duration=duration, loop=0, disposal=2)


def headroom_report(frames: list[Image.Image]) -> tuple[int, list[dict]]:
    min_top = CANVAS[1]
    warnings: list[dict] = []
    for index, frame in enumerate(frames):
        left, top, right, bottom = alpha_bbox(frame)
        min_top = min(min_top, top)
        if top < 18:
            warnings.append({"frame": index, "type": "headroom", "top_margin_px": top})
        if left <= 0 or right >= CANVAS[0] or bottom >= CANVAS[1]:
            warnings.append({"frame": index, "type": "edge_contact", "bbox": [left, top, right, bottom]})
    return min_top, warnings


def build_frames(expressions: list[Image.Image], timeline: list[int], inbetween: float = 0.7) -> tuple[list[Image.Image], list[Image.Image]]:
    raw_frames: list[Image.Image] = []
    for index, expr_index in enumerate(timeline):
        frame = expressions[expr_index]
        if index > 0 and timeline[index - 1] != expr_index:
            prev = expressions[timeline[index - 1]]
            raw_frames.append(crossfade(prev, frame, inbetween))
        raw_frames.append(frame)
    final_frames = [outline(normalize(frame)) for frame in raw_frames]
    return raw_frames, final_frames


def write_sequence(
    name: str,
    raw_frames: list[Image.Image],
    final_frames: list[Image.Image],
    paths: list[Path],
    transforms: list[dict],
    timeline: list[int],
    mask: Image.Image,
) -> dict:
    out_dir = OUT_DIR if name == "manual_patch" else BEAT_ROOT / name
    raw_dir = RAW_DIR if name == "manual_patch" else out_dir / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    for index, frame in enumerate(raw_frames):
        frame.save(raw_dir / f"bramble_{name}_raw_{index:03d}.png")
    for index, frame in enumerate(final_frames):
        frame.save(out_dir / f"bramble_{name}_{index:03d}.png")

    contact = out_dir / f"bramble_{name}_contact.png"
    preview = out_dir / f"bramble_{name}_preview.gif"
    manifest_path = out_dir / f"bramble_{name}_manifest.json"
    save_contact(final_frames, contact)
    save_gif(final_frames, preview)
    min_top, warnings = headroom_report(final_frames)

    manifest = {
        "name": name,
        "source": [str(path) for path in paths],
        "frame_count": len(final_frames),
        "fps": FPS,
        "canvas": list(CANVAS),
        "anchor_canvas": list(ANCHOR_CANVAS),
        "target_height": TARGET_HEIGHT,
        "body_policy": "Bramble1 is the fixed master body; other plates contribute only a feathered face patch.",
        "generated_features": 0,
        "timing_policy": "Held expression beats with a single quick 70% in-between on expression changes.",
        "edge_policy": "RGBA resized through premultiplied alpha to prevent magenta source-background fringe.",
        "timeline_expression_indices": timeline,
        "face_mask_polygon": FACE_POLYGON,
        "source_alignment": transforms,
        "min_top_margin_px": min_top,
        "warnings": warnings,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "name": name,
        "frames": len(final_frames),
        "warnings": len(warnings),
        "min_top_margin_px": min_top,
        "preview": str(preview),
        "contact": str(contact),
        "manifest": str(manifest_path),
    }


def main() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    BEAT_ROOT.mkdir(parents=True, exist_ok=True)

    paths = [SRC / f"Bramble{i}.png" for i in range(1, 7)]
    sources = [remove_magenta(Image.open(path)) for path in paths]
    master = sources[0]
    mask = make_face_mask(master.size)

    aligned: list[Image.Image] = []
    transforms: list[dict] = []
    for path, source in zip(paths, sources):
        placed, offset = align_to_master(source, master)
        aligned.append(placed)
        transforms.append({"source": str(path), "dx": offset[0], "dy": offset[1]})

    expressions = [expression_plate(master, source, mask) for source in aligned]

    # Held, readable expression beats with quick point-to-point changes.
    # Bramble is a blob; the face does the acting while the body stays locked.
    timeline: list[int] = [
        0, 0, 0, 0,
        1, 1, 1,
        0, 0,
        2, 2, 2, 2,
        3, 3, 3,
        2, 2,
        4, 4, 4,
        5, 5, 5, 5,
        0, 0, 0, 0,
    ]
    summaries = []
    raw_frames, final_frames = build_frames(expressions, timeline)
    summaries.append(write_sequence("manual_patch", raw_frames, final_frames, paths, transforms, timeline, mask))

    story_timelines = {
        "thread_handoff": [0, 0, 2, 2, 3, 3, 3, 2, 0, 0],
        "parcel_defensive": [0, 0, 5, 5, 4, 4, 4, 5, 0, 0],
        "ledger_recognition": [0, 0, 2, 2, 4, 4, 3, 3, 2, 0, 0],
        "toggle_pushback": [0, 5, 5, 4, 4, 3, 3, 4, 5, 0],
        "thinking_nudge": [0, 0, 2, 2, 2, 5, 5, 4, 4, 0, 0],
    }
    for name, beat_timeline in story_timelines.items():
        beat_raw, beat_final = build_frames(expressions, beat_timeline)
        summaries.append(write_sequence(name, beat_raw, beat_final, paths, transforms, beat_timeline, mask))

    print(json.dumps({"sequences": summaries}, indent=2))


if __name__ == "__main__":
    main()
