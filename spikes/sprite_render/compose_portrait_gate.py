#!/usr/bin/env python3
"""Compose the Otto dialogue portrait gate still and report face measurements."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


OUTLINE = (22, 12, 13, 255)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def load_palette(path: Path) -> list[tuple[int, int, int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    colors = [hex_to_rgb(value) for value in data.get("hero", {}).values()]
    deduped: list[tuple[int, int, int]] = []
    for color in colors:
        if color not in deduped:
            deduped.append(color)
    if not deduped:
        raise ValueError(f"no hero colors found in {path}")
    return deduped


def nearest(pixel: tuple[int, int, int], palette: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    return min(palette, key=lambda c: sum((pixel[i] - c[i]) ** 2 for i in range(3)))


def posterize(img: Image.Image, palette: list[tuple[int, int, int]]) -> Image.Image:
    out = img.convert("RGBA")
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a > 0:
                nr, ng, nb = nearest((r, g, b), palette)
                px[x, y] = (nr, ng, nb, a)
    return out


def outline(img: Image.Image) -> Image.Image:
    alpha = img.getchannel("A")
    dilated = alpha.filter(ImageFilter.MaxFilter(7))
    outline_alpha = Image.eval(dilated, lambda px: 255 if px > 10 else 0)
    line = Image.new("RGBA", img.size, OUTLINE)
    line.putalpha(outline_alpha)
    return Image.alpha_composite(line, img)


def clamp_channel(value: float) -> int:
    return max(0, min(255, round(value)))


def tinted_target(pixel: tuple[int, int, int], target: tuple[int, int, int], strength: float) -> tuple[int, int, int]:
    r, g, b = pixel
    lum = max(0.72, min(1.22, (0.2126 * r + 0.7152 * g + 0.0722 * b) / 125.0))
    toned = tuple(clamp_channel(channel * lum) for channel in target)
    return tuple(clamp_channel(pixel[i] * (1.0 - strength) + toned[i] * strength) for i in range(3))


def soft_palette_snap(img: Image.Image, palette: list[tuple[int, int, int]], strength: float = 0.35) -> Image.Image:
    out = img.convert("RGBA")
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a > 0:
                nr, ng, nb = nearest((r, g, b), palette)
                px[x, y] = (
                    clamp_channel(r * (1.0 - strength) + nr * strength),
                    clamp_channel(g * (1.0 - strength) + ng * strength),
                    clamp_channel(b * (1.0 - strength) + nb * strength),
                    a,
                )
    return out


def cover_background(bg: Image.Image, size: tuple[int, int]) -> Image.Image:
    scale = max(size[0] / bg.width, size[1] / bg.height)
    resized = bg.resize((round(bg.width * scale), round(bg.height * scale)), Image.Resampling.LANCZOS)
    x = (resized.width - size[0]) // 2
    y = (resized.height - size[1]) // 2
    return resized.crop((x, y, x + size[0], y + size[1]))


def face_measurements(metadata: dict) -> dict:
    samples = metadata.get("face_anchor_samples") or []
    sample = samples[0] if samples else {}
    head_h = float(sample.get("head_pixel_height") or 0)
    head_w = float(sample.get("head_pixel_width") or head_h * 0.78)
    face_width = max(1.0, min(head_w * 0.76, head_h * 0.62))
    return {
        "face_width_px": round(face_width, 2),
        "source_head_pixel_height": round(head_h, 2),
        "source_head_pixel_width": round(head_w, 2),
        "eye_width_range_px": [round(face_width * 0.15, 2), round(face_width * 0.18, 2)],
        "eye_center_separation_px": round(face_width * 0.44, 2),
        "eye_y_from_face_top_px": round(face_width * 0.53, 2),
        "pupil_width_range_px": [round(face_width * 0.018, 2), round(face_width * 0.025, 2)],
        "pupil_to_eye_width_ratio": "about 1:7",
        "anchor": sample.get("center"),
    }


def trim_alpha(img: Image.Image) -> tuple[Image.Image, tuple[int, int, int, int]]:
    bbox = img.getchannel("A").getbbox()
    if not bbox:
        return img, (0, 0, img.width, img.height)
    return img.crop(bbox), bbox


def resize_by_height(img: Image.Image, height: int) -> tuple[Image.Image, float]:
    scale = height / img.height
    width = round(img.width * scale)
    return img.resize((width, height), Image.Resampling.LANCZOS), scale


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-frame", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--background", type=Path, default=Path("ags/room1/background/clerk.png"))
    parser.add_argument("--palette", type=Path, default=Path("spikes/sprite_render/palette.json"))
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--portrait-height", type=int, default=1180)
    parser.add_argument("--portrait-x", type=int, default=1040)
    parser.add_argument("--portrait-y", type=int, default=-130)
    parser.add_argument("--treatment", choices=("strict-poster", "painterly", "source-outline"), default="strict-poster")
    parser.add_argument("--assumption", default="Otto placed on right third to leave room on the left for a second speaker.")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    raw = Image.open(args.raw_frame).convert("RGBA")
    palette = load_palette(args.palette)
    if args.treatment == "strict-poster":
        sprite = outline(posterize(raw, palette))
    elif args.treatment == "source-outline":
        sprite = outline(raw)
    else:
        sprite = outline(soft_palette_snap(raw, palette))
    sprite, sprite_bbox = trim_alpha(sprite)
    sprite, display_scale = resize_by_height(sprite, args.portrait_height)
    bg = cover_background(Image.open(args.background).convert("RGBA"), (1920, 1080))
    bg = bg.filter(ImageFilter.GaussianBlur(0.75))
    veil = Image.new("RGBA", bg.size, (18, 12, 9, 54))
    bg.alpha_composite(veil)
    bg.alpha_composite(sprite, (args.portrait_x, args.portrait_y))

    out = args.out_dir / "otto_portrait_gate_still.png"
    bg.save(out)
    sprite.save(args.out_dir / "otto_portrait_gate_sprite_r3.png")
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    measure = face_measurements(metadata)
    display_measure = {
        "trimmed_source_bbox": list(sprite_bbox),
        "display_scale": round(display_scale, 4),
        "display_portrait_height_px": args.portrait_height,
        "display_position_px": [args.portrait_x, args.portrait_y],
        "display_face_width_px_est": round(measure["face_width_px"] * display_scale, 2),
    }
    report = {
        "status": "portrait_gate_pending_user_approval",
        "output": str(out),
        "sprite_output": str(args.out_dir / "otto_portrait_gate_sprite_r3.png"),
        "raw_frame": str(args.raw_frame),
        "background": str(args.background),
        "dimensions": [1920, 1080],
        "camera": metadata.get("camera"),
        "face_measurements": measure,
        "display_measurements": display_measure,
        "treatment": args.treatment,
        "derived_asset_targets": {
            "single_sclera_width_px": [round(value * display_scale, 2) for value in measure["eye_width_range_px"]],
            "eye_center_separation_px": round(measure["eye_center_separation_px"] * display_scale, 2),
            "pupil_width_px": [round(value * display_scale, 2) for value in measure["pupil_width_range_px"]],
            "pupil_rule": "small dot, not iris disc; roughly 1:7 against sclera width",
        },
        "assumptions": [args.assumption],
        "gate": "Do not create final dialogue face assets until this still is approved.",
    }
    (args.out_dir / "portrait_gate_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(out), "face_width_px": measure["face_width_px"]}, indent=2))


if __name__ == "__main__":
    main()
