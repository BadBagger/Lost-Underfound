#!/usr/bin/env python3
"""Build Bramble mobile idle/follow and walk-plane proof clips.

This is a source-derived proof from the user-corrected Bramble plate, not final
admission art. Bramble's body is kept recognizable and foot-anchored; the walk
cycle is a cautious shuffle with the required nine role labels.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
SRC = Path(r"C:\Users\KyleB\OneDrive\Pictures\Lost Animation PNGS\Bramble1.png")
OUT_ROOT = ROOT / "spikes" / "sprite_render" / "bramble_mobile_proof"
RAW_ROOT = OUT_ROOT / "raw"
OUT = OUT_ROOT / "out"

CANVAS = (512, 512)
ANCHOR = (256, 486)
TARGET_HEIGHT = 392
FPS = 12
MAGENTA = (255, 0, 255)
OUTLINE = (22, 12, 13, 255)


WALK_KEYS = [
    ("contact-left-foot-forward", -5, 0, -1.8, 0.985, 1.006),
    ("recoil-down-left", -3, 5, -1.0, 1.012, 0.992),
    ("low-passing-left", -1, 2, -0.4, 1.006, 0.998),
    ("high-passing-left", 2, -4, 0.8, 0.988, 1.006),
    ("contact-right-foot-forward", 5, 0, 1.8, 0.985, 1.006),
    ("recoil-down-right", 3, 5, 1.0, 1.012, 0.992),
    ("low-passing-right", 1, 2, 0.4, 1.006, 0.998),
    ("high-passing-right", -2, -4, -0.8, 0.988, 1.006),
    ("return-to-contact-left", -5, 0, -1.8, 0.985, 1.006),
]


def remove_magenta(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    data = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = data[x, y]
            pink_bg = r > 175 and b > 175 and g < 135 and r - g > 70 and b - g > 70
            if pink_bg:
                data[x, y] = (r, g, b, 0)
    return rgba


def alpha_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    bbox = img.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("empty alpha")
    return bbox


def base_sprite() -> Image.Image:
    img = remove_magenta(Image.open(SRC))
    bbox = alpha_bbox(img)
    cropped = img.crop(bbox)
    scale = TARGET_HEIGHT / cropped.height
    return cropped.resize((round(cropped.width * scale), TARGET_HEIGHT), Image.Resampling.LANCZOS)


def outline(img: Image.Image) -> Image.Image:
    alpha = img.getchannel("A")
    dilated = alpha.filter(ImageFilter.MaxFilter(7))
    outline_alpha = Image.eval(dilated, lambda px: 255 if px > 8 else 0)
    layer = Image.new("RGBA", img.size, OUTLINE)
    layer.putalpha(outline_alpha)
    return Image.alpha_composite(layer, img)


def place(sprite: Image.Image, x_shift: int = 0, y_shift: int = 0, angle: float = 0.0, sx: float = 1.0, sy: float = 1.0) -> Image.Image:
    work = sprite.resize((round(sprite.width * sx), round(sprite.height * sy)), Image.Resampling.LANCZOS)
    work = work.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    bbox = alpha_bbox(work)
    bottom = bbox[3]
    foot_center = (bbox[0] + bbox[2]) / 2
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    x = round(ANCHOR[0] - foot_center + x_shift)
    y = round(ANCHOR[1] - bottom + y_shift)
    canvas.alpha_composite(work, (x, y))
    return outline(canvas)


def draw_contact_shadow(frame: Image.Image, width: int = 86) -> Image.Image:
    shadow = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    draw.ellipse((ANCHOR[0] - width, ANCHOR[1] - 12, ANCHOR[0] + width, ANCHOR[1] + 8), fill=(28, 20, 16, 66))
    shadow = shadow.filter(ImageFilter.GaussianBlur(7))
    shadow.alpha_composite(frame)
    return shadow


def save_contact(frames: list[Image.Image], roles: list[str], path: Path, prefix: str) -> None:
    cols = min(9, len(frames))
    rows = math.ceil(len(frames) / cols)
    cell_h = CANVAS[1] + 34
    sheet = Image.new("RGBA", (cols * CANVAS[0], rows * cell_h), (128, 128, 128, 255))
    draw = ImageDraw.Draw(sheet)
    for i, frame in enumerate(frames):
        x = (i % cols) * CANVAS[0]
        y = (i // cols) * cell_h + 30
        sheet.alpha_composite(frame, (x, y))
        ax = x + ANCHOR[0]
        ay = y + ANCHOR[1]
        draw.line((ax - 10, ay, ax + 10, ay), fill=(255, 64, 128, 255))
        draw.line((ax, ay - 10, ax, ay + 10), fill=(255, 64, 128, 255))
        label = roles[i] if i < len(roles) else f"{prefix}-{i:02d}"
        draw.text((x + 5, y - 26), f"{i:02d} {label[:36]}", fill=(255, 244, 215, 255))
    sheet.save(path)


def save_gif(frames: list[Image.Image], path: Path) -> None:
    duration = round(1000 / FPS)
    gif_frames: list[Image.Image] = []
    for frame in frames:
        bg = Image.new("RGBA", frame.size, (128, 128, 128, 255))
        bg.alpha_composite(frame)
        gif_frames.append(bg.convert("P", palette=Image.Palette.ADAPTIVE))
    gif_frames[0].save(path, save_all=True, append_images=gif_frames[1:], duration=duration, loop=0, disposal=2)


def frame_report(frames: list[Image.Image], roles: list[str]) -> tuple[list[dict], list[dict]]:
    reports: list[dict] = []
    warnings: list[dict] = []
    prev_anchor: tuple[int, int] | None = None
    for index, frame in enumerate(frames):
        bbox = alpha_bbox(frame)
        anchor = ANCHOR
        delta = 0.0 if prev_anchor is None else math.dist(anchor, prev_anchor)
        prev_anchor = anchor
        if bbox[1] < 18:
            warnings.append({"frame": index, "type": "headroom", "top_margin_px": bbox[1]})
        if bbox[0] <= 0 or bbox[2] >= CANVAS[0] or bbox[3] >= CANVAS[1]:
            warnings.append({"frame": index, "type": "edge_contact", "bbox": list(bbox)})
        reports.append({"frame": index, "role": roles[index] if index < len(roles) else "", "bbox": list(bbox), "anchor": list(anchor), "anchor_delta_px": delta})
    return reports, warnings


def write_clip(name: str, frames: list[Image.Image], roles: list[str], loop: bool, role_contract: str | None = None) -> None:
    out_dir = OUT / name
    raw_dir = RAW_ROOT / name
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    for index, frame in enumerate(frames):
        frame.save(out_dir / f"bramble_{name}_{index:03d}.png")
    save_contact(frames, roles, out_dir / f"bramble_{name}_contact.png", name)
    save_gif(frames, out_dir / f"bramble_{name}_preview.gif")
    reports, warnings = frame_report(frames, roles)
    manifest = {
        "character": "bramble",
        "clip": name,
        "source": str(SRC),
        "frame_count": len(frames),
        "fps": FPS,
        "loop": loop,
        "canvas": list(CANVAS),
        "anchor_canvas": list(ANCHOR),
        "target_height": TARGET_HEIGHT,
        "actor_type": "walk-plane",
        "role_contract": role_contract,
        "source_policy": "single approved Bramble cutout transformed only; no generated facial or costume features",
        "frames": reports,
        "warnings": warnings,
    }
    (out_dir / f"bramble_{name}_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sprite = base_sprite()

    idle_specs = [
        ("neutral-hold", 0, 0, 0.0, 1.0, 1.0),
        ("eyes-rest-hold", 0, 0, 0.0, 1.0, 1.0),
        ("small-anticipation", 0, -1, -0.25, 0.998, 1.002),
        ("settle", 0, 0, 0.0, 1.0, 1.0),
        ("tiny-glance-left", -1, 0, -0.4, 1.0, 1.0),
        ("return-hold", 0, 0, 0.0, 1.0, 1.0),
    ]
    idle_frames = [draw_contact_shadow(place(sprite, xs, ys, angle, sx, sy), 82) for _, xs, ys, angle, sx, sy in idle_specs]
    write_clip("mobile_idle", idle_frames, [spec[0] for spec in idle_specs], True)

    walk_frames = [draw_contact_shadow(place(sprite, xs, ys, angle, sx, sy), 88) for _, xs, ys, angle, sx, sy in WALK_KEYS]
    write_clip("walk_9key_shuffle", walk_frames, [spec[0] for spec in WALK_KEYS], True, "9-key walk-plane proof roles")

    summary = {
        "mobile_idle_frames": len(idle_frames),
        "walk_frames": len(walk_frames),
        "out": str(OUT),
    }
    (OUT_ROOT / "bramble_mobile_proof_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
