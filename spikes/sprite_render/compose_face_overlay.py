#!/usr/bin/env python3
"""Composite a deterministic face overlay onto sprite proof frames.

This is a proof compositor. It derives a face anchor from the alpha bounds so the
current Meshy render can be evaluated immediately. Production should replace the
heuristic anchor with Blender-projected head socket data.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


LINE = (22, 12, 13, 255)
SKIN_SHADOW = (158, 111, 65, 255)
EYE_WHITE = (255, 244, 215, 255)
PUPIL = (22, 12, 13, 255)
MOUTH_DARK = (82, 36, 43, 255)
TONGUE = (176, 72, 86, 255)

ASSET_NAMES = {
    "eyes_open": "eyes_open.png",
    "eyes_half": "eyes_half.png",
    "eyes_closed": "eyes_closed.png",
    "nose": "nose.png",
    "A": "mouth_A.png",
    "B": "mouth_B.png",
    "C": "mouth_C.png",
    "D": "mouth_D.png",
    "E": "mouth_E.png",
    "F": "mouth_F.png",
}


def alpha_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    bbox = img.getchannel("A").getbbox()
    if not bbox:
        raise ValueError("frame has no visible alpha")
    return bbox


def derive_face_anchor(img: Image.Image) -> dict:
    left, top, right, bottom = alpha_bbox(img)
    width = right - left
    height = bottom - top
    return {
        "center": [round(left + width * 0.51, 2), round(top + height * 0.23, 2)],
        "scale": round(max(width, height) / 206.0, 4),
        "rotation_degrees": 0.0,
        "source": "alpha_bbox_heuristic",
    }


def load_projected_anchors(path: Path | None) -> dict[int, dict]:
    if not path:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    anchors = {}
    for sample in data.get("face_anchor_samples", []):
        index = sample.get("index")
        if isinstance(index, int):
            anchors[index] = {
                "center": sample["center"],
                "scale": sample.get("scale", 1.0),
                "head_pixel_height": sample.get("head_pixel_height"),
                "head_pixel_width": sample.get("head_pixel_width"),
                "rotation_degrees": sample.get("rotation_degrees", 0.0),
                "source": sample.get("source", "blender_projected_bone"),
                "bone": sample.get("bone"),
            }
    return anchors


def load_face_assets(path: Path | None) -> dict[str, Image.Image]:
    if not path:
        return {}
    assets = {}
    for key, name in ASSET_NAMES.items():
        asset_path = path / name
        if asset_path.exists():
            assets[key] = Image.open(asset_path).convert("RGBA")
    return assets


def paste_centered(layer: Image.Image, asset: Image.Image, center: tuple[float, float], target_width: float) -> None:
    scale = target_width / asset.width
    size = (max(1, round(asset.width * scale)), max(1, round(asset.height * scale)))
    resized = asset.resize(size, Image.Resampling.LANCZOS)
    x = round(center[0] - resized.width / 2)
    y = round(center[1] - resized.height / 2)
    layer.alpha_composite(resized, (x, y))


def composite_clean_face_patch(
    layer: Image.Image,
    center: tuple[float, float],
    face_w: float,
    face_h: float,
    scale: float,
) -> None:
    """Softly cover Meshy's baked facial features without a rectangular sticker."""
    cx, cy = center
    patch = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    mask = Image.new("L", layer.size, 0)
    patch_draw = ImageDraw.Draw(patch)
    mask_draw = ImageDraw.Draw(mask)

    # Slightly asymmetrical face-feature patch: taller than the eye/mouth area,
    # tucked under the hairline, and narrower near the chin. It is not meant to
    # repaint the whole face, only to quiet the old baked eyes/mouth.
    left = cx - face_w * 0.40
    right = cx + face_w * 0.40
    top = cy - face_h * 0.13
    bottom = cy + face_h * 0.43
    skin = (238, 198, 148, 246)
    shade = (214, 150, 102, 72)
    mask_draw.ellipse((left, top, right, bottom), fill=230)
    mask_draw.polygon(
        [
            (cx - face_w * 0.20, cy + face_h * 0.30),
            (cx + face_w * 0.22, cy + face_h * 0.30),
            (cx + face_w * 0.06, cy + face_h * 0.53),
            (cx - face_w * 0.06, cy + face_h * 0.53),
        ],
        fill=190,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(max(1.0, 1.15 * scale)))
    patch_draw.rectangle((0, 0, layer.width, layer.height), fill=skin)
    # A tiny bit of cheek/nose warmth so the patch does not become a flat sticker.
    patch_draw.ellipse((left, cy + face_h * 0.05, cx - face_w * 0.06, bottom), fill=shade)
    patch.putalpha(mask)
    layer.alpha_composite(patch)


def mouth_path(draw: ImageDraw.ImageDraw, cx: float, cy: float, width: float, height: float, viseme: str) -> None:
    sx = max(1.0, width / 18.0)
    half_w = width * 0.5
    half_h = height * 0.5
    if viseme == "A":
        draw.line([(cx - half_w, cy), (cx + half_w, cy)], fill=LINE, width=max(2, round(1.5 * sx)))
    elif viseme == "B":
        draw.ellipse([cx - half_w * 0.78, cy - half_h * 0.55, cx + half_w * 0.78, cy + half_h], fill=MOUTH_DARK, outline=LINE, width=max(2, round(1.5 * sx)))
    elif viseme == "C":
        draw.ellipse([cx - half_w * 0.82, cy - half_h, cx + half_w * 0.82, cy + half_h * 1.15], fill=MOUTH_DARK, outline=LINE, width=max(2, round(1.5 * sx)))
        draw.arc([cx - half_w * 0.45, cy + half_h * 0.05, cx + half_w * 0.45, cy + half_h * 1.15], 200, 340, fill=TONGUE, width=max(1, round(1.4 * sx)))
    elif viseme == "D":
        draw.arc([cx - half_w, cy - half_h, cx + half_w, cy + half_h], 15, 165, fill=LINE, width=max(2, round(1.5 * sx)))
    elif viseme == "E":
        draw.ellipse([cx - half_w * 0.42, cy - half_h, cx + half_w * 0.42, cy + half_h], fill=MOUTH_DARK, outline=LINE, width=max(2, round(1.5 * sx)))
    else:
        draw.arc([cx - half_w, cy - half_h, cx + half_w, cy + half_h], 20, 160, fill=LINE, width=max(2, round(1.5 * sx)))


def draw_face(
    img: Image.Image,
    anchor: dict,
    frame_index: int,
    mode: str,
    offset: tuple[float, float],
    assets: dict[str, Image.Image],
    clean_face_base: bool,
) -> Image.Image:
    out = img.convert("RGBA").copy()
    layer = Image.new("RGBA", out.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    cx = anchor["center"][0] + offset[0]
    cy = anchor["center"][1] + offset[1]
    head_h = float(anchor.get("head_pixel_height") or 42.0)
    head_w = float(anchor.get("head_pixel_width") or head_h * 0.78)
    face_w = max(18.0, min(head_w * 0.76, head_h * 0.62))
    face_h = max(24.0, head_h * 0.72)
    scale = face_w / 54.0

    # Simplified portrait proportions:
    # eyes near the face midpoint, nose halfway between eyes and chin, mouth
    # halfway between nose and chin; mouth corners align near the pupils.
    face_top = cy - face_h * 0.5
    eye_y = face_top + face_h * 0.50
    nose_y = face_top + face_h * 0.68
    mouth_y = face_top + face_h * 0.80

    if clean_face_base:
        # Dialogue busts use the 2D face cards as the acting authority.
        # Feather the old baked facial features away instead of drawing a box.
        composite_clean_face_patch(layer, (cx, eye_y), face_w, face_h, scale)

    blink_phase = frame_index % 48
    blink_closed = blink_phase in {10, 11}
    blink_half = blink_phase in {9, 12}
    pupil_offset = math.sin(frame_index / 12 * math.tau) * 1.4 * scale

    eye_center_gap = face_w * 0.23
    left_eye = (cx - eye_center_gap, eye_y)
    right_eye = (cx + eye_center_gap, eye_y)
    eye_w = face_w * 0.105
    eye_h = face_w * 0.135
    eye_key = "eyes_closed" if blink_closed else "eyes_half" if blink_half else "eyes_open"
    if assets and eye_key in assets:
        paste_centered(layer, assets[eye_key], (cx, eye_y), target_width=face_w * 0.72)
    else:
        for ex, ey in [left_eye, right_eye]:
            if blink_closed:
                draw.line([(ex - eye_w, ey), (ex + eye_w, ey)], fill=LINE, width=max(2, round(2 * scale)))
            elif blink_half:
                draw.arc([ex - eye_w, ey - eye_h * 0.4, ex + eye_w, ey + eye_h * 0.8], 0, 180, fill=LINE, width=max(2, round(2 * scale)))
            else:
                draw.ellipse([ex - eye_w, ey - eye_h, ex + eye_w, ey + eye_h], fill=EYE_WHITE, outline=LINE, width=max(2, round(2 * scale)))
                pr = max(2, round(2.4 * scale))
                draw.ellipse([ex + pupil_offset - pr, ey - pr, ex + pupil_offset + pr, ey + pr], fill=PUPIL)

    nose_w = max(2.0, eye_center_gap * 0.32)
    if assets and "nose" in assets:
        paste_centered(layer, assets["nose"], (cx, nose_y), target_width=max(3.0, face_w * 0.16))
    else:
        draw.arc([cx - nose_w * 0.55, nose_y - nose_w, cx + nose_w * 0.75, nose_y + nose_w * 1.2], 95, 245, fill=SKIN_SHADOW, width=max(1, round(1.4 * scale)))

    visemes = ["A", "B", "C", "D", "E", "F"] if mode == "talk" else ["A", "A", "F", "A", "A", "F"]
    viseme = visemes[frame_index % len(visemes)]
    mouth_w = max(5.0, eye_center_gap * 1.05)
    mouth_h = max(4.0, face_h * 0.10)
    if assets and viseme in assets:
        paste_centered(layer, assets[viseme], (cx, mouth_y), target_width=max(5.0, face_w * 0.46))
    else:
        mouth_path(draw, cx, mouth_y, mouth_w, mouth_h, viseme)

    return Image.alpha_composite(out, layer)


def save_contact(frames: list[Image.Image], anchors: list[dict], path: Path, draw_guides: bool) -> None:
    cols = min(6, len(frames))
    rows = math.ceil(len(frames) / cols)
    cell_w = frames[0].width
    cell_h = frames[0].height + 22
    sheet = Image.new("RGBA", (cols * cell_w, rows * cell_h), (128, 128, 128, 255))
    draw = ImageDraw.Draw(sheet)
    for index, frame in enumerate(frames):
        x = (index % cols) * cell_w
        y = (index // cols) * cell_h + 22
        sheet.alpha_composite(frame, (x, y))
        if draw_guides:
            ax, ay = anchors[index]["center"]
            draw.line([(x + ax - 7, y + ay), (x + ax + 7, y + ay)], fill=(255, 0, 255, 255), width=1)
            draw.line([(x + ax, y + ay - 7), (x + ax, y + ay + 7)], fill=(255, 0, 255, 255), width=1)
        draw.text((x + 4, y - 18), f"face #{index:02d}", fill=(255, 244, 215, 255))
    sheet.save(path)


def save_face_zoom(frames: list[Image.Image], anchors: list[dict], path: Path, zoom: int = 5) -> None:
    crops = []
    crop_w = 70
    crop_h = 96
    for index, frame in enumerate(frames):
        ax, ay = anchors[index]["center"]
        left = round(ax - crop_w / 2)
        top = round(ay - crop_h / 2)
        crop = Image.new("RGBA", (crop_w, crop_h), (128, 128, 128, 255))
        crop.alpha_composite(frame, (-left, -top))
        crop = crop.resize((crop_w * zoom, crop_h * zoom), Image.Resampling.NEAREST)
        crops.append((index, crop))

    cols = min(6, len(crops))
    rows = math.ceil(len(crops) / cols)
    cell_w = crop_w * zoom
    cell_h = crop_h * zoom + 22
    sheet = Image.new("RGBA", (cols * cell_w, rows * cell_h), (128, 128, 128, 255))
    draw = ImageDraw.Draw(sheet)
    for index, crop in crops:
        x = (index % cols) * cell_w
        y = (index // cols) * cell_h + 22
        sheet.alpha_composite(crop, (x, y))
        draw.text((x + 4, y - 18), f"zoom #{index:02d}", fill=(255, 244, 215, 255))
    sheet.save(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames-dir", required=True, type=Path)
    parser.add_argument("--frame-glob", default="*.png")
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--mode", choices=["idle", "talk"], default="talk")
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--anchor-metadata", type=Path)
    parser.add_argument("--anchor-offset-x", type=float, default=0.0)
    parser.add_argument("--anchor-offset-y", type=float, default=0.0)
    parser.add_argument("--draw-guides", action="store_true")
    parser.add_argument("--face-assets-dir", type=Path)
    parser.add_argument("--clean-face-base", action="store_true")
    args = parser.parse_args()

    paths = sorted(path for path in args.frames_dir.glob(args.frame_glob) if path.is_file())
    if not paths:
        raise FileNotFoundError(f"no frames found in {args.frames_dir} matching {args.frame_glob!r}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    frames: list[Image.Image] = []
    manifest_frames: list[dict] = []
    anchors: list[dict] = []
    projected_anchors = load_projected_anchors(args.anchor_metadata)
    face_assets = load_face_assets(args.face_assets_dir)
    for index, path in enumerate(paths):
        source = Image.open(path).convert("RGBA")
        anchor = projected_anchors.get(index) or derive_face_anchor(source)
        offset = (args.anchor_offset_x, args.anchor_offset_y)
        composed = draw_face(source, anchor, index, args.mode, offset, face_assets, args.clean_face_base)
        name = f"{args.mode}_face_{index:03d}.png"
        composed.save(args.out_dir / name)
        frames.append(composed)
        anchors.append(anchor)
        manifest_frames.append({
            "file": name,
            "source": str(path),
            "face_anchor": anchor,
            "face_overlay_offset": [args.anchor_offset_x, args.anchor_offset_y],
            "mouth_channel": "A-F" if args.mode == "talk" else "idle/rest",
            "eye_channel": "open/half/closed",
            "face_asset_mode": "png_assets" if face_assets else "procedural",
            "clean_face_base": args.clean_face_base,
        })

    save_contact(frames, anchors, args.out_dir / f"{args.mode}_face_contact.png", draw_guides=False)
    save_contact(frames, anchors, args.out_dir / f"{args.mode}_face_anchor_debug.png", draw_guides=True)
    save_face_zoom(frames, anchors, args.out_dir / f"{args.mode}_face_zoom.png")
    frames[0].save(
        args.out_dir / f"{args.mode}_face_preview.gif",
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / args.fps),
        loop=0,
        disposal=2,
    )
    warnings = []
    if not projected_anchors:
        warnings.append(
            "Proof overlay only: replace heuristic face anchors with Blender socket projection before production admission."
        )
    if args.anchor_offset_x or args.anchor_offset_y:
        warnings.append(
            "Debug-only 2D face offset used. Production should move the Blender face socket or renderer model-space socket adjustment instead."
        )
    (args.out_dir / "face_overlay_manifest.json").write_text(json.dumps({
        "face_mode": "overlay",
        "anchor_method": "blender_projected_bone" if projected_anchors else "alpha_bbox_heuristic_for_proof",
        "production_anchor_method": "Blender head bone or named face socket projected into render camera",
        "fps": args.fps,
        "frame_count": len(frames),
        "face_overlay_offset": [args.anchor_offset_x, args.anchor_offset_y],
        "face_asset_mode": "png_assets" if face_assets else "procedural",
        "face_assets_dir": str(args.face_assets_dir) if args.face_assets_dir else None,
        "clean_face_base": args.clean_face_base,
        "frames": manifest_frames,
        "warnings": warnings,
    }, indent=2), encoding="utf-8")
    print(json.dumps({"frames": len(frames), "out": str(args.out_dir), "face_mode": "overlay"}, indent=2))


if __name__ == "__main__":
    main()
