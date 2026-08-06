#!/usr/bin/env python3
"""Build Bramble face-only expression overlays from regenerated full-body states."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "art" / "rigs" / "bramble" / "source" / "expression-regeneration" / "locked-sliced"
OUT = ROOT / "art" / "rigs" / "bramble" / "source" / "expression-regeneration" / "face-overlays"
PROOF = OUT / "proof"

NAMES = ["neutral", "blink", "small_open", "wide_open", "skeptical", "pleased"]

# Fixed crop in the 362x724 source-cell coordinate space. This is deliberately
# only the performance mask: brows, glasses, eyes, nose, mouth, and nearby face.
# Keep this to the performance area: brows, glasses, eyes, nose, and mouth.
# The final output does not paste this whole box. It derives a soft lasso mask
# from the pixels that changed versus neutral, then overlays only those pixels.
FACE_BOX = (82, 204, 284, 382)
SEARCH_BOX = (70, 190, 292, 390)
RIGID_BOX = (55, 150, 315, 385)
TARGET_ANCHOR = (181, 287)


def load_source(name: str, index: int) -> Image.Image:
    return Image.open(SRC / f"bramble_expr_{index + 1:02d}_{name}.png").convert("RGBA")


def feature_anchor(img: Image.Image) -> tuple[float, float]:
    """Find the center of high-contrast facial features within SEARCH_BOX."""
    sx0, sy0, sx1, sy1 = SEARCH_BOX
    crop = img.crop(SEARCH_BOX).convert("RGBA")
    points: list[tuple[int, int, float]] = []
    for y in range(crop.height):
        for x in range(crop.width):
            r, g, b, a = crop.getpixel((x, y))
            if a < 40:
                continue
            brightness = (r + g + b) / 3
            chroma = max(r, g, b) - min(r, g, b)
            is_glasses_or_pupil = brightness < 112
            is_gold_highlight = r > 145 and g > 95 and b < 75 and chroma > 55
            if not (is_glasses_or_pupil or is_gold_highlight):
                continue
            # Keep the bow tie out of the anchor. It is useful art, bad geometry.
            if sy0 + y > 338:
                continue
            weight = 1.8 if is_glasses_or_pupil else 1.0
            points.append((sx0 + x, sy0 + y, weight))
    if not points:
        return TARGET_ANCHOR
    total = sum(weight for _, _, weight in points)
    return (
        sum(x * weight for x, _, weight in points) / total,
        sum(y * weight for _, y, weight in points) / total,
    )


def silhouette_offset(neutral: Image.Image, img: Image.Image) -> tuple[int, int, float]:
    """Register an expression to neutral using the rigid head silhouette.

    The expression pixels themselves move by design, so using pupils/mouths as
    registration landmarks causes visible swimming. The outer head alpha is more
    stable and tells us how the generated source tile drifted.
    """
    neutral_alpha = np.array(neutral.getchannel("A").crop(RIGID_BOX), dtype=np.uint8) > 40
    best: tuple[float, int, int] | None = None
    for dx in range(-28, 29):
        for dy in range(-18, 19):
            shifted = Image.new("L", img.size, 0)
            shifted.paste(img.getchannel("A"), (dx, dy))
            current_alpha = np.array(shifted.crop(RIGID_BOX), dtype=np.uint8) > 40
            score = float(np.mean(neutral_alpha != current_alpha))
            if best is None or score < best[0]:
                best = (score, dx, dy)
    assert best is not None
    return best[1], best[2], best[0]


def aperture_mask(size: tuple[int, int]) -> Image.Image:
    w, h = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((4, 0, w - 4, h - 1), radius=34, fill=255)
    draw.ellipse((10, 1, w - 10, h + 22), fill=255)
    # Trim the bottom so the bow tie/body never enters the expression plate.
    draw.rectangle((0, h - 9, w, h), fill=0)
    return mask.filter(ImageFilter.GaussianBlur(0.8))


def edge_extend_rgb(img: Image.Image) -> Image.Image:
    """Avoid black matte under translucent pixels by blurring nearest source color."""
    rgba = img.convert("RGBA")
    alpha = rgba.getchannel("A")
    rgb = rgba.convert("RGB")
    grown_alpha = alpha.filter(ImageFilter.MaxFilter(9))
    matte = Image.new("RGB", rgba.size, (0, 0, 0))
    matte.paste(rgb, mask=alpha)
    for _ in range(5):
        blurred = matte.filter(ImageFilter.GaussianBlur(2))
        matte.paste(blurred, mask=Image.eval(grown_alpha, lambda px: 255 if px > 0 else 0))
        matte.paste(rgb, mask=alpha)
    out = matte.convert("RGBA")
    out.putalpha(alpha)
    return out


def changed_lasso_mask(neutral_face: Image.Image, expr_face: Image.Image) -> Image.Image:
    """Build a GIMP-style soft lasso around only the expression changes."""
    neutral = np.array(neutral_face.convert("RGBA"), dtype=np.int16)
    expr = np.array(expr_face.convert("RGBA"), dtype=np.int16)
    rgb_delta = np.abs(expr[:, :, :3] - neutral[:, :, :3]).sum(axis=2)
    alpha_delta = np.abs(expr[:, :, 3] - neutral[:, :, 3])
    expr_alpha = expr[:, :, 3] > 35
    changed = ((rgb_delta > 42) | (alpha_delta > 36)) & expr_alpha

    raw = Image.fromarray((changed.astype(np.uint8) * 255), "L")
    region = Image.new("L", raw.size, 0)
    draw = ImageDraw.Draw(region)
    # Manual lasso equivalents. These deliberately avoid the outer fur/head
    # silhouette, which is where generated source drift creates black bites.
    draw.rounded_rectangle((24, 30, raw.width - 24, 92), radius=24, fill=255)
    draw.rounded_rectangle((66, 82, raw.width - 66, 132), radius=16, fill=255)
    region = region.filter(ImageFilter.GaussianBlur(0.5))
    raw = Image.composite(raw, Image.new("L", raw.size, 0), region)

    # Expand slightly like a human lasso would, then feather the cut edge.
    raw = raw.filter(ImageFilter.MaxFilter(7))
    raw = raw.filter(ImageFilter.GaussianBlur(0.9))
    return raw


def make_plate(neutral_img: Image.Image, img: Image.Image, dx: int, dy: int) -> tuple[Image.Image, Image.Image, Image.Image]:
    shifted = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shifted.alpha_composite(img, (dx, dy))
    neutral_face = neutral_img.crop(FACE_BOX)
    expr_face = shifted.crop(FACE_BOX)
    mask = changed_lasso_mask(neutral_face, expr_face)
    face = expr_face.copy()
    face.putalpha(mask)
    face = edge_extend_rgb(face)
    full = Image.new("RGBA", img.size, (0, 0, 0, 0))
    full.alpha_composite(face, (FACE_BOX[0], FACE_BOX[1]))
    return face, full, mask


def composite_preview(base: Image.Image, full_plate: Image.Image) -> Image.Image:
    out = base.copy()
    out.alpha_composite(full_plate)
    return out


def lerp_rgba(a: Image.Image, b: Image.Image, t: float) -> Image.Image:
    return Image.blend(a.convert("RGBA"), b.convert("RGBA"), max(0.0, min(1.0, t)))


def save_contact(images: list[tuple[str, Image.Image]], path: Path) -> None:
    cols = 3
    cell_w = images[0][1].width
    cell_h = images[0][1].height + 26
    rows = math.ceil(len(images) / cols)
    contact = Image.new("RGBA", (cols * cell_w, rows * cell_h), (128, 128, 128, 255))
    draw = ImageDraw.Draw(contact)
    for i, (name, img) in enumerate(images):
        x = (i % cols) * cell_w
        y = (i // cols) * cell_h + 24
        contact.alpha_composite(img, (x, y))
        draw.text((x + 6, y - 20), name, fill=(255, 244, 215, 255))
    contact.save(path)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    PROOF.mkdir(parents=True, exist_ok=True)

    sources = [load_source(name, index) for index, name in enumerate(NAMES)]
    anchors = [feature_anchor(img) for img in sources]
    neutral_anchor = anchors[0]

    records = []
    face_images: list[tuple[str, Image.Image]] = []
    full_plates: list[tuple[str, Image.Image]] = []
    for name, img, anchor in zip(NAMES, sources, anchors):
        measured_dx, measured_dy, silhouette_score = silhouette_offset(sources[0], img)
        # Use the source strip's locked cell placement as the alignment truth.
        # Whole-plate offsets make the lasso drift; only the expression pixels
        # should change over the neutral master.
        dx = 0
        dy = 0
        face, full, delta_mask = make_plate(sources[0], img, dx, dy)
        face_path = OUT / f"bramble_face_{name}.png"
        full_path = OUT / f"bramble_face_{name}_full.png"
        mask_path = OUT / f"bramble_face_{name}_mask.png"
        face.save(face_path)
        full.save(full_path)
        delta_mask.save(mask_path)
        face_images.append((name, face))
        full_plates.append((name, full))
        records.append(
            {
                "name": name,
                "source_anchor": [round(anchor[0], 3), round(anchor[1], 3)],
                "neutral_anchor": [round(neutral_anchor[0], 3), round(neutral_anchor[1], 3)],
                "transform": {
                    "dx": dx,
                    "dy": dy,
                    "rotate": 0,
                    "scale": 1,
                    "silhouette_score": round(silhouette_score, 4),
                    "measured_dx_not_applied": measured_dx,
                    "measured_dy_not_applied": measured_dy,
                },
                "face_plate": str(face_path.relative_to(ROOT)).replace("\\", "/"),
                "full_plate": str(full_path.relative_to(ROOT)).replace("\\", "/"),
                "delta_mask": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
            }
        )

    save_contact(face_images, OUT / "bramble_face_overlays_contact.png")

    base = sources[0]
    proof_images: list[tuple[str, Image.Image]] = []
    for name, full in full_plates:
        preview = composite_preview(base, full)
        preview_path = PROOF / f"bramble_face_overlay_preview_{name}.png"
        preview.save(preview_path)
        proof_images.append((name, preview))
    save_contact(proof_images, PROOF / "bramble_face_overlay_locked_body_contact.png")

    # Point-to-point acting pass: slow holds, anticipation, and transitional
    # blends. These are face-only overlays on a locked Bramble body.
    plate_preview_by_name = {name: composite_preview(base, full) for name, full in full_plates}
    beats = [
        ("neutral", "neutral", 12, "settled watch"),
        ("neutral", "blink", 2, "blink close"),
        ("blink", "neutral", 3, "blink reopen"),
        ("neutral", "neutral", 6, "post-blink rest"),
        ("neutral", "skeptical", 7, "brow decision"),
        ("skeptical", "skeptical", 14, "skeptical hold"),
        ("skeptical", "small_open", 6, "small breath before speech"),
        ("small_open", "small_open", 8, "small-open hold"),
        ("small_open", "neutral", 5, "mouth close"),
        ("neutral", "neutral", 5, "listen rest"),
        ("neutral", "pleased", 8, "pleased realization"),
        ("pleased", "pleased", 14, "pleased hold"),
        ("pleased", "wide_open", 4, "little surprised aside"),
        ("wide_open", "wide_open", 6, "surprised hold"),
        ("wide_open", "neutral", 6, "settle back"),
        ("neutral", "neutral", 12, "final neutral hold"),
    ]
    frames: list[Image.Image] = []
    sequence: list[dict] = []
    frame_index = 0
    for start, end, count, note in beats:
        for i in range(count):
            t = 0.0 if count <= 1 else (i / (count - 1))
            t = t * t * (3.0 - 2.0 * t)
            frame = lerp_rgba(plate_preview_by_name[start], plate_preview_by_name[end], t)
            frames.append(frame)
            sequence.append({"index": frame_index, "from": start, "to": end, "t": round(t, 3), "note": note})
            frame_index += 1
    gif_frames = []
    for frame in frames:
        canvas = Image.new("RGBA", frame.size, (128, 128, 128, 255))
        canvas.alpha_composite(frame)
        gif_frames.append(canvas.convert("P", palette=Image.Palette.ADAPTIVE))
    gif_path = PROOF / "bramble_face_overlay_locked_body_preview.gif"
    gif_frames[0].save(gif_path, save_all=True, append_images=gif_frames[1:], duration=1000 // 8, loop=0, disposal=2)

    manifest = {
        "source_dir": str(SRC.relative_to(ROOT)).replace("\\", "/"),
        "output_dir": str(OUT.relative_to(ROOT)).replace("\\", "/"),
        "face_box": list(FACE_BOX),
        "search_box": list(SEARCH_BOX),
        "rigid_box": list(RIGID_BOX),
        "target_anchor": list(TARGET_ANCHOR),
        "frame_count": len(records),
        "frames": records,
        "proof": {
            "locked_body_contact": str((PROOF / "bramble_face_overlay_locked_body_contact.png").relative_to(ROOT)).replace("\\", "/"),
            "locked_body_preview": str(gif_path.relative_to(ROOT)).replace("\\", "/"),
        },
        "acting_sequence": sequence,
        "rules": [
            "Only the fixed face aperture is retained from each regenerated expression.",
            "Only pixels that differ from the neutral master are carried forward, like a soft lasso selection.",
            "The rest of the body and unchanged facial structure is discarded, so source body drift does not affect runtime overlay.",
            "No procedural eyes, mouth, hands, body motion, or generated replacement features are drawn by this tool.",
        ],
    }
    (OUT / "bramble_face_overlays_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"frames": len(records), "contact": manifest["proof"]["locked_body_contact"], "preview": manifest["proof"]["locked_body_preview"]}, indent=2))


if __name__ == "__main__":
    main()
