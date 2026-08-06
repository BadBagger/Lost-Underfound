#!/usr/bin/env python3
"""Build open/blink texture variants from an extracted Meshy texture.

This is intentionally conservative: it does not guess a single UV coordinate.
It finds existing face-eye paint in the texture atlas, enhances those locations
for the open-eye texture, and paints closed lids over the same locations for the
blink texture.
"""

from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageDraw


LINE = (22, 12, 13, 255)
PUPIL = (12, 8, 8, 255)
EYE_WHITE = (255, 247, 214, 255)
HIGHLIGHT = (255, 255, 244, 255)
MOUTH = (46, 8, 14, 255)


@dataclass
class Blob:
    bbox: tuple[int, int, int, int]
    pixels: int
    center: tuple[int, int]

    @property
    def width(self) -> int:
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> int:
        return self.bbox[3] - self.bbox[1]


def connected_components(mask: bytearray, width: int, height: int, minimum: int) -> list[Blob]:
    seen = bytearray(width * height)
    blobs: list[Blob] = []
    for y in range(height):
        for x in range(width):
            i = y * width + x
            if not mask[i] or seen[i]:
                continue
            q: deque[tuple[int, int]] = deque([(x, y)])
            seen[i] = 1
            xs: list[int] = []
            ys: list[int] = []
            while q:
                cx, cy = q.popleft()
                xs.append(cx)
                ys.append(cy)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < width and 0 <= ny < height:
                        ni = ny * width + nx
                        if mask[ni] and not seen[ni]:
                            seen[ni] = 1
                            q.append((nx, ny))
            if len(xs) >= minimum:
                blobs.append(
                    Blob(
                        bbox=(min(xs), min(ys), max(xs) + 1, max(ys) + 1),
                        pixels=len(xs),
                        center=(round(sum(xs) / len(xs)), round(sum(ys) / len(ys))),
                    )
                )
    blobs.sort(key=lambda blob: blob.pixels, reverse=True)
    return blobs


def build_masks(image: Image.Image) -> tuple[bytearray, bytearray]:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    data = rgba.load()
    skin = bytearray(width * height)
    eye_white = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            r, g, b, a = data[x, y]
            if a < 16:
                continue
            i = y * width + x
            if r > 170 and g > 112 and b > 78 and r > g and g >= b - 30:
                skin[i] = 1
            if r > 230 and g > 225 and b > 205:
                eye_white[i] = 1
    return skin, eye_white


def median_skin_color(image: Image.Image, bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = bbox
    samples: list[tuple[int, int, int]] = []
    px = image.load()
    for y in range(max(0, y1), min(image.height, y2)):
        for x in range(max(0, x1), min(image.width, x2)):
            r, g, b, a = px[x, y]
            if a > 16 and r > 170 and g > 112 and b > 78 and r > g and g >= b - 30:
                samples.append((r, g, b))
    if not samples:
        return (229, 166, 124, 255)
    samples.sort()
    r = sorted(v[0] for v in samples)[len(samples) // 2]
    g = sorted(v[1] for v in samples)[len(samples) // 2]
    b = sorted(v[2] for v in samples)[len(samples) // 2]
    return (r, g, b, 255)


def expand_bbox(bbox: tuple[int, int, int, int], pad_x: int, pad_y: int, width: int, height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = bbox
    return (max(0, x1 - pad_x), max(0, y1 - pad_y), min(width, x2 + pad_x), min(height, y2 + pad_y))


def draw_open_eye(draw: ImageDraw.ImageDraw, blob: Blob) -> dict[str, object]:
    cx, cy = blob.center
    rx = max(10, round(blob.width * 0.68))
    ry = max(8, round(blob.height * 0.66))
    outline_w = max(3, round(min(rx, ry) * 0.16))
    eye_box = (cx - rx, cy - ry, cx + rx, cy + ry)
    draw.ellipse(eye_box, fill=EYE_WHITE, outline=LINE, width=outline_w)
    pupil_r = max(5, round(min(rx, ry) * 0.48))
    draw.ellipse((cx - pupil_r, cy - pupil_r, cx + pupil_r, cy + pupil_r), fill=PUPIL)
    hi = max(2, round(pupil_r * 0.34))
    draw.ellipse((cx + hi, cy - pupil_r + hi, cx + hi * 2, cy - pupil_r + hi * 2), fill=HIGHLIGHT)
    return {"center": [cx, cy], "radius": [rx, ry]}


def draw_blink_eye(draw: ImageDraw.ImageDraw, image: Image.Image, blob: Blob) -> dict[str, object]:
    cx, cy = blob.center
    rx = max(12, round(blob.width * 1.08))
    ry = max(10, round(blob.height * 0.96))
    cover = expand_bbox((cx - rx, cy - ry, cx + rx, cy + ry), rx // 2, ry // 2, image.width, image.height)
    skin = median_skin_color(image, cover)

    # Generated UV islands are often filtered and rotated. A soft ellipse alone
    # leaves white eye corners, so first wipe the whole local eye cell to skin.
    draw.rounded_rectangle(cover, radius=max(4, min(rx, ry) // 2), fill=skin)
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=skin)

    line_w = max(6, round(min(rx, ry) * 0.28))
    lid_box = (cx - rx, cy - round(ry * 0.58), cx + rx, cy + round(ry * 0.85))
    # Thick upper lid plus a tiny lower crease; this must read at sprite scale.
    draw.arc(lid_box, 12, 168, fill=LINE, width=line_w)
    crease_w = max(2, line_w // 3)
    crease_y = cy + round(ry * 0.38)
    draw.arc((cx - round(rx * 0.72), crease_y - ry // 3, cx + round(rx * 0.72), crease_y + ry // 3), 22, 158, fill=(124, 76, 55, 255), width=crease_w)
    return {"center": [cx, cy], "radius": [rx, ry], "cover": list(cover), "line_width": line_w}


def draw_mouths(open_img: Image.Image, blink_img: Image.Image, eye_blobs: list[Blob]) -> list[dict[str, object]]:
    reports: list[dict[str, object]] = []
    for blob in eye_blobs:
        cx, cy = blob.center
        # The Meshy atlas contains rotated/mirrored face islands. Mouth placement
        # is therefore authored as small marks in the plausible lower/front zones
        # around each visible eye island. At game scale this reads as one clear
        # mouth on the rendered side instead of a floating overlay.
        candidates = [
            (cx, cy + max(18, round(blob.height * 1.55))),
            (cx - max(16, round(blob.width * 0.72)), cy + max(10, round(blob.height * 0.72))),
            (cx + max(16, round(blob.width * 0.72)), cy + max(10, round(blob.height * 0.72))),
        ]
        mw = max(10, round(blob.width * 0.34))
        mh = max(5, round(blob.height * 0.20))
        for mx, my in candidates:
            if not (0 <= mx < open_img.width and 0 <= my < open_img.height):
                continue
            local = (mx - mw * 2, my - mh * 3, mx + mw * 2, my + mh * 3)
            skin = median_skin_color(open_img, local)
            # Skip marks that would land on costume/hood instead of skin.
            if skin[0] < 170:
                continue
            for img in (open_img, blink_img):
                d = ImageDraw.Draw(img)
                d.rounded_rectangle((mx - mw, my - mh, mx + mw, my + mh), radius=max(2, mh // 2), fill=MOUTH)
            reports.append({"center": [mx, my], "size": [mw * 2, mh * 2], "source_eye_center": list(blob.center)})
    return reports


def make_debug(base: Image.Image, eye_blobs: list[Blob], out: Path) -> None:
    debug = base.convert("RGBA")
    draw = ImageDraw.Draw(debug)
    for index, blob in enumerate(eye_blobs):
        x1, y1, x2, y2 = blob.bbox
        pad = max(8, blob.width // 2)
        draw.rectangle(expand_bbox(blob.bbox, pad, pad, base.width, base.height), outline=(255, 0, 255, 255), width=5)
        draw.text((x1, y1), f"eye {index}", fill=(255, 0, 255, 255))
    debug.save(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--open-out", type=Path)
    parser.add_argument("--out", type=Path, help="Backward-compatible alias for --blink-out.")
    parser.add_argument("--blink-out", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--debug", type=Path)
    parser.add_argument("--paint-mouths", action="store_true", help="Experimental: paint mouth marks into likely face UV islands.")
    args = parser.parse_args()

    base = Image.open(args.base).convert("RGBA")
    _, eye_mask = build_masks(base)
    eye_blobs = [
        blob
        for blob in connected_components(eye_mask, base.width, base.height, minimum=90)
        if 8 <= blob.width <= 180 and 8 <= blob.height <= 130
    ][:8]

    if not eye_blobs:
        raise SystemExit("No likely eye-white UV islands found; use Meshy retexture or a hand texture paint pass.")

    open_img = base.copy()
    blink_img = base.copy()
    open_draw = ImageDraw.Draw(open_img)
    blink_draw = ImageDraw.Draw(blink_img)
    open_reports = [draw_open_eye(open_draw, blob) for blob in eye_blobs]
    blink_reports = [draw_blink_eye(blink_draw, blink_img, blob) for blob in eye_blobs]
    mouth_reports = draw_mouths(open_img, blink_img, eye_blobs) if args.paint_mouths else []

    open_out = args.open_out or args.base.with_name(f"{args.base.stem}_face_open.png")
    blink_out = args.blink_out or args.out or args.base.with_name(f"{args.base.stem}_face_blink.png")
    open_out.parent.mkdir(parents=True, exist_ok=True)
    blink_out.parent.mkdir(parents=True, exist_ok=True)
    open_img.save(open_out)
    blink_img.save(blink_out)

    if args.debug:
        args.debug.parent.mkdir(parents=True, exist_ok=True)
        make_debug(base, eye_blobs, args.debug)

    report = {
        "base": str(args.base),
        "open_out": str(open_out),
        "blink_out": str(blink_out),
        "type": "eye-island-derived texture variants",
        "eye_blob_count": len(eye_blobs),
        "eye_blobs": [asdict(blob) for blob in eye_blobs],
        "open_eye_paint": open_reports,
        "blink_eye_paint": blink_reports,
        "mouth_paint": mouth_reports,
        "notes": [
            "Uses existing eye-white UV islands from the Meshy texture; no single atlas coordinate is guessed.",
            "Mouth UV painting is disabled by default because generated atlases can rotate and fragment face islands.",
            "This is still a repo-side texture paint pass. Meshy retexture or manual UV paint remains preferred for final art quality.",
        ],
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"open_out": str(open_out), "blink_out": str(blink_out), "eye_blob_count": len(eye_blobs)}, indent=2))


if __name__ == "__main__":
    main()
