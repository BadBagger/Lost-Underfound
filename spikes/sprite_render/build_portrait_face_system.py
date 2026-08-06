#!/usr/bin/env python3
"""Build Otto dialogue portrait face assets and a text-driven talk preview."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


LINE = (22, 12, 13, 255)
SKIN = (239, 202, 150, 238)
SKIN_SHADE = (177, 111, 80, 90)
SCLERA = (255, 249, 221, 255)
PUPIL = (22, 12, 13, 255)
BLUSH = (231, 127, 105, 150)
MOUTH_DARK = (58, 27, 31, 255)
TONGUE = (179, 78, 91, 255)
TEETH = (255, 248, 221, 255)


def load_report(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def display_face_geometry(report: dict) -> dict[str, float]:
    display = report["display_measurements"]
    face = report["face_measurements"]
    x0, y0, _x1, _y1 = display["trimmed_source_bbox"]
    scale = display["display_scale"]
    px, py = display["display_position_px"]
    anchor_x, anchor_y = face["anchor"]
    cx = px + (anchor_x - x0) * scale
    cy = py + (anchor_y - y0) * scale
    face_w = display["display_face_width_px_est"]
    face_h = face_w * 1.32
    # The Meshy `headfront` socket projects near the hood/forehead on this
    # model. Dialogue face cards need the artistic face center instead.
    cy += face_h * 0.39
    cx -= face_w * 0.12
    face_top = cy - face_h * 0.50
    eye_y = face_top + face_h * 0.53
    nose_y = face_top + face_h * 0.68
    mouth_y = face_top + face_h * 0.81
    return {
        "face_center_x": cx,
        "face_center_y": cy,
        "face_width": face_w,
        "face_height": face_h,
        "eye_y": eye_y,
        "nose_y": nose_y,
        "mouth_y": mouth_y,
        "eye_gap": face_w * 0.44,
        "eye_width": face_w * 0.17,
        "pupil_width": face_w * 0.023,
    }


def save(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def asset_canvas(w: int, h: int) -> Image.Image:
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def draw_sclera_pair(face_w: float, closed: bool = False) -> Image.Image:
    width = round(face_w * 0.76)
    height = round(face_w * 0.23)
    img = asset_canvas(width, height)
    draw = ImageDraw.Draw(img)
    eye_w = face_w * 0.17
    eye_h = eye_w * 0.68
    gap = face_w * 0.44
    cy = height * 0.52
    for cx in (width / 2 - gap / 2, width / 2 + gap / 2):
        if closed:
            draw.arc([cx - eye_w * 0.58, cy - eye_h * 0.38, cx + eye_w * 0.58, cy + eye_h * 0.50], 8, 172, fill=LINE, width=3)
        else:
            draw.ellipse([cx - eye_w / 2, cy - eye_h / 2, cx + eye_w / 2, cy + eye_h / 2], fill=SCLERA, outline=LINE, width=3)
    return img


def draw_pupil(face_w: float) -> Image.Image:
    size = max(4, round(face_w * 0.035))
    img = asset_canvas(size, size)
    draw = ImageDraw.Draw(img)
    r = size * 0.34
    cx = cy = size / 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PUPIL)
    return img


def draw_brows(face_w: float, state: str) -> Image.Image:
    width = round(face_w * 0.82)
    height = round(face_w * 0.25)
    img = asset_canvas(width, height)
    draw = ImageDraw.Draw(img)
    gap = face_w * 0.44
    brow_w = face_w * 0.19
    cy = height * 0.58
    centers = (width / 2 - gap / 2, width / 2 + gap / 2)
    if state == "raised":
        offsets = [(-brow_w / 2, -6, brow_w / 2, -10), (-brow_w / 2, -10, brow_w / 2, -6)]
    elif state == "furrowed":
        offsets = [(-brow_w / 2, -8, brow_w / 2, 2), (-brow_w / 2, 2, brow_w / 2, -8)]
    elif state == "skeptical":
        offsets = [(-brow_w / 2, -11, brow_w / 2, -5), (-brow_w / 2, 2, brow_w / 2, -5)]
    else:
        offsets = [(-brow_w / 2, -4, brow_w / 2, -6), (-brow_w / 2, -6, brow_w / 2, -4)]
    for cx, (x1, y1, x2, y2) in zip(centers, offsets):
        draw.line([(cx + x1, cy + y1), (cx + x2, cy + y2)], fill=LINE, width=4)
    return img


def draw_mouth(face_w: float, state: str) -> Image.Image:
    width = round(face_w * 0.34)
    height = round(face_w * 0.19)
    img = asset_canvas(width, height)
    draw = ImageDraw.Draw(img)
    cx, cy = width / 2, height / 2
    if state == "closed":
        draw.arc([cx - width * 0.28, cy - height * 0.08, cx + width * 0.28, cy + height * 0.34], 15, 165, fill=LINE, width=3)
    elif state == "small_open":
        draw.ellipse([cx - width * 0.18, cy - height * 0.20, cx + width * 0.18, cy + height * 0.25], fill=MOUTH_DARK, outline=LINE, width=3)
    elif state == "wide_open":
        draw.ellipse([cx - width * 0.30, cy - height * 0.34, cx + width * 0.30, cy + height * 0.40], fill=MOUTH_DARK, outline=LINE, width=3)
        draw.arc([cx - width * 0.16, cy + height * 0.08, cx + width * 0.16, cy + height * 0.44], 200, 340, fill=TONGUE, width=2)
    else:
        draw.rounded_rectangle([cx - width * 0.32, cy - height * 0.32, cx + width * 0.32, cy + height * 0.35], radius=4, fill=MOUTH_DARK, outline=LINE, width=3)
        draw.rectangle([cx - width * 0.23, cy - height * 0.22, cx + width * 0.23, cy - height * 0.02], fill=TEETH)
        draw.line([(cx - width * 0.23, cy - height * 0.02), (cx + width * 0.23, cy - height * 0.02)], fill=LINE, width=2)
    return img


def paste_center(layer: Image.Image, asset: Image.Image, center: tuple[float, float]) -> None:
    layer.alpha_composite(asset, (round(center[0] - asset.width / 2), round(center[1] - asset.height / 2)))


def soft_clear_face(layer: Image.Image, geo: dict[str, float]) -> None:
    mask = Image.new("L", layer.size, 0)
    patch = Image.new("RGBA", layer.size, SKIN)
    shade = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    md = ImageDraw.Draw(mask)
    sd = ImageDraw.Draw(shade)
    cx, cy = geo["face_center_x"], geo["face_center_y"]
    fw, fh = geo["face_width"], geo["face_height"]
    # Broad enough to erase Meshy's baked eyes/mouth before new acting parts
    # are drawn, but starts below the hairline so it does not repaint the hood.
    md.rounded_rectangle(
        [cx - fw * 0.62, cy - fh * 0.15, cx + fw * 0.55, cy + fh * 0.43],
        radius=round(fw * 0.18),
        fill=236,
    )
    md.ellipse([cx - fw * 0.53, cy - fh * 0.22, cx + fw * 0.46, cy + fh * 0.36], fill=228)
    md.polygon([(cx - fw * 0.20, cy + fh * 0.23), (cx + fw * 0.16, cy + fh * 0.23), (cx + fw * 0.05, cy + fh * 0.55), (cx - fw * 0.08, cy + fh * 0.55)], fill=205)
    mask = mask.filter(ImageFilter.GaussianBlur(1.4))
    patch.putalpha(mask)
    shade_mask = Image.new("L", layer.size, 0)
    shade_draw = ImageDraw.Draw(shade_mask)
    shade_draw.ellipse([cx + fw * 0.15, cy - fh * 0.05, cx + fw * 0.48, cy + fh * 0.34], fill=85)
    shade_mask = shade_mask.filter(ImageFilter.GaussianBlur(5))
    sd.rectangle((0, 0, layer.width, layer.height), fill=SKIN_SHADE)
    shade.putalpha(shade_mask)
    layer.alpha_composite(patch)
    layer.alpha_composite(shade)


def compose_face(base: Image.Image, assets: dict[str, Image.Image], geo: dict[str, float], brow: str, mouth: str, blink: bool, pupil_offset: tuple[float, float]) -> Image.Image:
    out = base.convert("RGBA").copy()
    layer = Image.new("RGBA", out.size, (0, 0, 0, 0))
    soft_clear_face(layer, geo)
    cx = geo["face_center_x"]
    eye_y = geo["eye_y"]
    gap = geo["eye_gap"]
    paste_center(layer, assets["sclera_closed" if blink else "sclera_open"], (cx, eye_y))
    if not blink:
        for ex in (cx - gap / 2, cx + gap / 2):
            paste_center(layer, assets["pupil"], (ex + pupil_offset[0], eye_y + pupil_offset[1]))
    paste_center(layer, assets[f"brow_{brow}"], (cx, eye_y - geo["face_width"] * 0.17))
    paste_center(layer, assets[f"mouth_{mouth}"], (cx, geo["mouth_y"]))
    # Static cheek warmth, intentionally small.
    draw = ImageDraw.Draw(layer)
    fw = geo["face_width"]
    draw.ellipse([cx - fw * 0.35, eye_y + fw * 0.12, cx - fw * 0.23, eye_y + fw * 0.22], fill=BLUSH)
    draw.ellipse([cx + fw * 0.26, eye_y + fw * 0.11, cx + fw * 0.39, eye_y + fw * 0.22], fill=BLUSH)
    return Image.alpha_composite(out, layer)


def build_assets(out_dir: Path, face_w: float) -> dict[str, Image.Image]:
    assets = {
        "sclera_open": draw_sclera_pair(face_w, closed=False),
        "sclera_closed": draw_sclera_pair(face_w, closed=True),
        "pupil": draw_pupil(face_w),
    }
    for brow in ("neutral", "raised", "furrowed", "skeptical"):
        assets[f"brow_{brow}"] = draw_brows(face_w, brow)
    for mouth in ("closed", "small_open", "wide_open", "teeth"):
        assets[f"mouth_{mouth}"] = draw_mouth(face_w, mouth)
    for name, img in assets.items():
        save(img, out_dir / f"{name}.png")
    return assets


def save_contact_sheet(assets: dict[str, Image.Image], out: Path) -> None:
    names = list(assets)
    cell_w, cell_h = 220, 110
    cols = 2
    rows = math.ceil(len(names) / cols)
    sheet = Image.new("RGBA", (cols * cell_w, rows * cell_h), (42, 36, 33, 255))
    draw = ImageDraw.Draw(sheet)
    for i, name in enumerate(names):
        x = (i % cols) * cell_w
        y = (i // cols) * cell_h
        draw.text((x + 8, y + 6), name, fill=(255, 244, 215, 255))
        asset = assets[name]
        sheet.alpha_composite(asset, (x + (cell_w - asset.width) // 2, y + 42))
    save(sheet, out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-still", type=Path, default=Path("spikes/sprite_render/dialogue_portrait_gate/otto_portrait_gate_still.png"))
    parser.add_argument("--report", type=Path, default=Path("spikes/sprite_render/dialogue_portrait_gate/portrait_gate_report.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("spikes/sprite_render/dialogue_portrait_face_system"))
    parser.add_argument("--fps", type=int, default=12)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = args.out_dir / "assets"
    base = Image.open(args.base_still).convert("RGBA")
    report = load_report(args.report)
    geo = display_face_geometry(report)
    assets = build_assets(assets_dir, geo["face_width"])
    save_contact_sheet(assets, args.out_dir / "otto_portrait_face_assets_contact.png")

    brow_states = {
        "neutral": ("closed", (0.0, 0.0)),
        "raised": ("small_open", (geo["pupil_width"] * 0.6, -geo["pupil_width"] * 0.2)),
        "furrowed": ("teeth", (-geo["pupil_width"] * 0.5, 0.0)),
        "skeptical": ("closed", (geo["pupil_width"] * 0.9, -geo["pupil_width"] * 0.1)),
    }
    for brow, (mouth, pupil) in brow_states.items():
        frame = compose_face(base, assets, geo, brow=brow, mouth=mouth, blink=False, pupil_offset=pupil)
        save(frame, args.out_dir / f"otto_portrait_brow_{brow}.png")

    mouth_cycle = ["closed", "small_open", "wide_open", "small_open", "teeth", "small_open", "closed", "small_open"]
    frames: list[Image.Image] = []
    for i in range(36):
        blink = i in {22, 23}
        mouth = mouth_cycle[i % len(mouth_cycle)] if i < 30 else "closed"
        brow = "raised" if i < 10 else "neutral" if i < 22 else "skeptical"
        pupil_x = math.sin(i / 18 * math.tau) * geo["pupil_width"] * 0.45
        frame = compose_face(base, assets, geo, brow=brow, mouth=mouth, blink=blink, pupil_offset=(pupil_x, 0.0))
        save(frame, args.out_dir / "frames" / f"otto_talk_{i:03d}.png")
        frames.append(frame)
    frames[0].save(
        args.out_dir / "otto_portrait_talk_preview.gif",
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / args.fps),
        loop=0,
        disposal=2,
    )
    manifest = {
        "status": "portrait_face_system_proof",
        "base_still": str(args.base_still),
        "face_geometry": {k: round(v, 2) for k, v in geo.items()},
        "assets_dir": str(assets_dir),
        "asset_count": len(assets),
        "brow_composites": [f"otto_portrait_brow_{name}.png" for name in brow_states],
        "talk_preview": "otto_portrait_talk_preview.gif",
        "frame_count": len(frames),
        "fps": args.fps,
        "constraints": [
            "No costume repainting.",
            "No belly or horn overlays.",
            "Face acting layer only.",
            "Text-driven mouth flap; no phoneme sync.",
        ],
    }
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(args.out_dir), "frames": len(frames), "assets": len(assets)}, indent=2))


if __name__ == "__main__":
    main()
