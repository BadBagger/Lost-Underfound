#!/usr/bin/env python3
"""Build deterministic transparent face-part PNG assets for overlay proofs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


LINE = (22, 12, 13, 255)
SKIN_SHADOW = (158, 111, 65, 255)
EYE_WHITE = (255, 244, 215, 255)
PUPIL = (22, 12, 13, 255)
HIGHLIGHT = (255, 255, 235, 255)
MOUTH_DARK = (82, 36, 43, 255)
TONGUE = (176, 72, 86, 255)


def save(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def draw_eye_pair(state: str) -> Image.Image:
    img = Image.new("RGBA", (80, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    centers = [(22, 16), (58, 16)]
    for cx, cy in centers:
        if state == "closed":
            draw.line([(cx - 10, cy), (cx + 10, cy)], fill=LINE, width=3)
            continue
        if state == "half":
            draw.ellipse([cx - 10, cy - 6, cx + 10, cy + 8], fill=EYE_WHITE, outline=LINE, width=3)
            draw.rectangle([cx - 12, cy - 12, cx + 12, cy - 1], fill=(0, 0, 0, 0))
            draw.arc([cx - 10, cy - 7, cx + 10, cy + 9], 0, 180, fill=LINE, width=3)
            draw.ellipse([cx - 4, cy - 1, cx + 4, cy + 7], fill=PUPIL)
            continue
        draw.ellipse([cx - 9, cy - 11, cx + 9, cy + 11], fill=EYE_WHITE, outline=LINE, width=3)
        draw.ellipse([cx - 5, cy - 6, cx + 5, cy + 7], fill=PUPIL)
        draw.ellipse([cx - 2, cy - 5, cx + 1, cy - 2], fill=HIGHLIGHT)
    return img


def draw_nose() -> Image.Image:
    img = Image.new("RGBA", (24, 30), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.line([(12, 3), (10, 14), (14, 21)], fill=SKIN_SHADOW, width=3)
    draw.arc([8, 16, 19, 28], 195, 335, fill=LINE, width=2)
    return img.filter(ImageFilter.GaussianBlur(0.15))


def draw_mouth(shape: str) -> Image.Image:
    img = Image.new("RGBA", (52, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if shape == "A":
        draw.line([(12, 15), (40, 15)], fill=LINE, width=4)
    elif shape == "B":
        draw.ellipse([13, 10, 39, 22], fill=MOUTH_DARK, outline=LINE, width=3)
    elif shape == "C":
        draw.ellipse([14, 5, 38, 27], fill=MOUTH_DARK, outline=LINE, width=3)
        draw.arc([18, 15, 34, 30], 200, 340, fill=TONGUE, width=3)
    elif shape == "D":
        draw.arc([12, 7, 40, 24], 15, 165, fill=LINE, width=4)
    elif shape == "E":
        draw.ellipse([18, 7, 34, 25], fill=MOUTH_DARK, outline=LINE, width=3)
    else:
        draw.arc([13, 8, 39, 24], 20, 160, fill=LINE, width=4)
    return img


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=Path("spikes/sprite_render/face_assets/otto"), type=Path)
    args = parser.parse_args()

    save(draw_eye_pair("open"), args.out_dir / "eyes_open.png")
    save(draw_eye_pair("half"), args.out_dir / "eyes_half.png")
    save(draw_eye_pair("closed"), args.out_dir / "eyes_closed.png")
    save(draw_nose(), args.out_dir / "nose.png")
    for shape in ["A", "B", "C", "D", "E", "F"]:
        save(draw_mouth(shape), args.out_dir / f"mouth_{shape}.png")

    manifest = {
        "asset_set": "otto_face_parts_v1",
        "canonical_face_width": 80,
        "files": [
            "eyes_open.png",
            "eyes_half.png",
            "eyes_closed.png",
            "nose.png",
            "mouth_A.png",
            "mouth_B.png",
            "mouth_C.png",
            "mouth_D.png",
            "mouth_E.png",
            "mouth_F.png",
        ],
        "notes": [
            "Transparent face-part assets for overlay proofing.",
            "Eyes are intentionally wider-spaced than the procedural prototype.",
        ],
    }
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(args.out_dir), "files": len(manifest["files"])}, indent=2))


if __name__ == "__main__":
    main()
