#!/usr/bin/env python3
"""Build and render Bramble's deterministic part rig."""

from __future__ import annotations

import json
import math
import shutil
from hashlib import sha256
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:
    raise SystemExit("This tool requires Pillow: pip install Pillow")


ROOT = Path(__file__).resolve().parents[1]
RIG = ROOT / "art" / "rigs" / "bramble"
PARTS = RIG / "parts"
POSES = RIG / "poses.json"
MANIFEST = RIG / "manifest.json"
OUT = ROOT / "art" / "act01-production" / "characters" / "bramble"
QA = ROOT / "art" / "act01-production" / "qa"
CANONICAL_SOURCE = RIG / "source" / "bramble_canonical_alpha.png"
BODY_ONLY_SOURCE = RIG / "source" / "bramble_body_only_alpha.png"
PART_SHEET_SOURCE = RIG / "source" / "bramble_parts_sheet_alpha.png"
SOURCE_CANVAS = (1024, 1024)
RUNTIME_CANVAS = (320, 260)
RUNTIME_ANCHOR = [160, 205]
FINAL_SOURCE_Y_OFFSET = 40
PINK = (255, 0, 255, 255)


def ease_in_out(t: float) -> float:
    return 0.5 - math.cos(max(0.0, min(1.0, t)) * math.pi) * 0.5


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def transparent() -> Image.Image:
    return Image.new("RGBA", SOURCE_CANVAS, (0, 0, 0, 0))


def canonical_body_canvas(squash: float = 1.0, lift: int = 0) -> Image.Image | None:
    source_path = BODY_ONLY_SOURCE if BODY_ONLY_SOURCE.exists() else CANONICAL_SOURCE
    if not source_path.exists():
        return None
    source = Image.open(source_path).convert("RGBA")
    bbox = source.getchannel("A").getbbox()
    if bbox is None:
        return None
    source = source.crop(bbox)
    target_height = int(720 * squash)
    target_width = int(source.width * (target_height / source.height) / math.sqrt(squash))
    source = source.resize((target_width, target_height), Image.Resampling.LANCZOS)
    canvas = transparent()
    x = (SOURCE_CANVAS[0] - target_width) // 2
    bottom = 800 + lift
    y = bottom - target_height
    canvas.alpha_composite(source, (x, y))
    return canvas


def draw_soft_ellipse(layer: Image.Image, box: tuple[int, int, int, int], fill: tuple[int, int, int, int], blur: int = 0) -> None:
    shape = Image.new("RGBA", SOURCE_CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shape)
    draw.ellipse(box, fill=fill)
    if blur:
        shape = shape.filter(ImageFilter.GaussianBlur(blur))
    layer.alpha_composite(shape)


def draw_body_variant(path: Path, squash: float = 1.0, lift: int = 0) -> None:
    canonical = canonical_body_canvas(squash, lift)
    if canonical is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        canonical.save(path)
        return
    img = transparent()
    draw = ImageDraw.Draw(img)
    cx, bottom = 512, 805 + lift
    body_w = int(500 / math.sqrt(squash))
    body_h = int(680 * squash)
    top = bottom - body_h

    draw_soft_ellipse(img, (cx - body_w // 2, top, cx + body_w // 2, bottom), (165, 157, 142, 255), 2)
    draw.ellipse((cx - body_w // 2, top, cx + body_w // 2, bottom), outline=(69, 62, 54, 255), width=9)
    draw_soft_ellipse(img, (cx - 175, top + 90, cx + 165, bottom - 65), (206, 199, 184, 210), 10)
    draw_soft_ellipse(img, (cx - 90, top + 120, cx + 210, bottom - 110), (118, 105, 92, 52), 22)

    for i in range(150):
        angle = (i * 137.5) % 360
        radius = 205 + (i % 7) * 7
        y_bias = math.sin(i * 1.77) * 165
        x = cx + math.cos(math.radians(angle)) * radius * (0.62 + (i % 5) * 0.035)
        y = (top + body_h * 0.49) + y_bias
        if not (top + 10 < y < bottom - 8):
            continue
        length = 18 + (i % 5) * 7
        color = [(103, 96, 88, 185), (217, 205, 181, 145), (132, 123, 108, 170)][i % 3]
        draw.line((x, y, x + math.cos(math.radians(angle + 18)) * length, y - length * 0.25), fill=color, width=3)

    # Small top wisps; deliberately not ears.
    for dx, dy, bend in [(-84, 8, -18), (-39, -18, -6), (9, -24, 7), (55, -9, 18), (92, 22, 28)]:
        x = cx + dx
        y = top + 35 + dy
        draw.arc((x - 18, y - 58, x + 34, y + 18), 205 + bend, 310 + bend, fill=(86, 77, 69, 230), width=5)

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def draw_eyes(path: Path, mode: str) -> None:
    img = transparent()
    draw = ImageDraw.Draw(img)
    for cx in (450, 575):
        if mode == "closed":
            draw.arc((cx - 45, 445, cx + 45, 505), 15, 165, fill=(24, 20, 17, 255), width=11)
            draw.arc((cx - 42, 449, cx + 42, 501), 18, 162, fill=(196, 171, 129, 150), width=4)
        elif mode == "half":
            draw_soft_ellipse(img, (cx - 48, 434, cx + 48, 522), (30, 25, 20, 110), 4)
            draw.ellipse((cx - 46, 435, cx + 46, 519), fill=(230, 216, 190, 255), outline=(37, 31, 26, 255), width=8)
            draw.rectangle((cx - 46, 435, cx + 46, 482), fill=(108, 99, 85, 212))
            draw.arc((cx - 44, 430, cx + 44, 493), 190, 350, fill=(37, 31, 26, 255), width=9)
            draw.ellipse((cx - 15, 475, cx + 15, 505), fill=(23, 19, 17, 255))
            draw.ellipse((cx - 6, 478, cx + 2, 486), fill=(255, 245, 217, 170))
        else:
            draw_soft_ellipse(img, (cx - 50, 428, cx + 50, 522), (30, 25, 20, 120), 5)
            draw.ellipse((cx - 47, 430, cx + 47, 519), fill=(239, 227, 200, 255), outline=(37, 31, 26, 255), width=8)
            draw.ellipse((cx - 16, 467, cx + 16, 499), fill=(23, 19, 17, 255))
            draw.ellipse((cx - 7, 469, cx + 2, 478), fill=(255, 248, 220, 190))
            draw.arc((cx - 40, 434, cx + 40, 515), 205, 330, fill=(255, 246, 215, 70), width=5)
    img.save(path)


def draw_brows(path: Path, mode: str) -> None:
    img = transparent()
    draw = ImageDraw.Draw(img)
    if mode == "worried":
        pairs = [((405, 419), (490, 402)), ((535, 402), (620, 419))]
    elif mode == "proud":
        pairs = [((407, 400), (489, 417)), ((536, 417), (618, 400))]
    else:
        pairs = [((407, 412), (490, 407)), ((535, 407), (618, 412))]
    for a, b in pairs:
        draw.line((a[0] + 3, a[1] + 4, b[0] + 3, b[1] + 4), fill=(30, 23, 18, 110), width=13)
        draw.line((*a, *b), fill=(48, 38, 30, 255), width=10)
        draw.line((a[0], a[1] - 3, b[0], b[1] - 3), fill=(207, 180, 132, 105), width=3)
    img.save(path)


def draw_mouth(path: Path, mode: str) -> None:
    img = transparent()
    draw = ImageDraw.Draw(img)
    if CANONICAL_SOURCE.exists():
        # Painterly replacement visemes aligned to the canonical Bramble source.
        # The original source has a closed mouth baked in; open visemes cover
        # that mark with a dark inner shape and soft lip edge.
        cx, cy = 512, 548
        if mode == "closed":
            draw.arc((cx - 36, cy - 14, cx + 36, cy + 20), 8, 172, fill=(42, 29, 26, 220), width=5)
            draw.arc((cx - 32, cy - 11, cx + 32, cy + 16), 12, 168, fill=(142, 106, 90, 96), width=3)
        elif mode == "small_open":
            draw.ellipse((cx - 24, cy - 19, cx + 24, cy + 23), fill=(42, 20, 25, 240), outline=(126, 87, 75, 180), width=4)
            draw.ellipse((cx - 13, cy - 10, cx + 13, cy + 2), fill=(230, 205, 180, 170))
            draw.arc((cx - 19, cy + 3, cx + 19, cy + 24), 188, 352, fill=(167, 73, 82, 135), width=4)
        elif mode == "wide_open":
            draw.ellipse((cx - 33, cy - 29, cx + 33, cy + 35), fill=(36, 16, 23, 250), outline=(129, 84, 75, 190), width=5)
            draw.rectangle((cx - 19, cy - 23, cx + 19, cy - 10), fill=(234, 219, 190, 220))
            draw.ellipse((cx - 17, cy + 8, cx + 17, cy + 29), fill=(158, 62, 76, 170))
        elif mode == "oo":
            draw.ellipse((cx - 21, cy - 24, cx + 21, cy + 28), fill=(34, 14, 21, 248), outline=(132, 86, 76, 190), width=5)
            draw.ellipse((cx - 10, cy - 10, cx + 10, cy + 12), fill=(64, 28, 35, 220))
        else:
            draw.arc((cx - 38, cy - 3, cx + 38, cy + 33), 190, 350, fill=(51, 28, 29, 235), width=6)
            draw.arc((cx - 33, cy - 1, cx + 33, cy + 29), 194, 346, fill=(142, 106, 90, 105), width=3)
        img = img.filter(ImageFilter.GaussianBlur(0.35))
        img.save(path)
        return
    if mode == "closed":
        draw.arc((474, 548, 550, 594), 10, 170, fill=(86, 36, 48, 255), width=8)
    elif mode == "small_open":
        draw.ellipse((488, 548, 536, 604), fill=(84, 35, 47, 255), outline=(55, 25, 31, 255), width=5)
        draw.ellipse((500, 558, 524, 575), fill=(236, 198, 192, 180))
    elif mode == "wide_open":
        draw.ellipse((474, 534, 552, 625), fill=(75, 30, 41, 255), outline=(55, 25, 31, 255), width=6)
        draw.rectangle((489, 540, 537, 554), fill=(238, 226, 200, 230))
    elif mode == "oo":
        draw.ellipse((490, 542, 535, 607), fill=(66, 26, 37, 255), outline=(55, 25, 31, 255), width=7)
    else:
        draw.arc((474, 560, 550, 606), 190, 350, fill=(86, 36, 48, 255), width=8)
    img.save(path)


def draw_hand(path: Path, side: str, pose: str) -> None:
    img = transparent()
    draw = ImageDraw.Draw(img)
    left = side == "left"
    base_x = 352 if left else 672
    base_y = 630
    limb = (96, 83, 67, 255)
    limb_hi = (177, 158, 125, 140)
    hand_fill = (214, 200, 166, 255)
    outline = (47, 38, 30, 255)

    def mitten(cx: int, cy: int, angle_hint: int = 0) -> None:
        draw_soft_ellipse(img, (cx - 34, cy - 28, cx + 34, cy + 29), (28, 22, 17, 100), 3)
        draw.ellipse((cx - 32, cy - 27, cx + 32, cy + 28), fill=hand_fill, outline=outline, width=5)
        thumb_dx = -22 if left else 22
        draw.ellipse((cx + thumb_dx - 14, cy - 5, cx + thumb_dx + 13, cy + 22), fill=(198, 181, 145, 255), outline=outline, width=4)
        draw.arc((cx - 21, cy - 19, cx + 23, cy + 14), 205, 315, fill=(250, 231, 187, 150), width=4)
        draw.line((cx - 12, cy + 18, cx + 14, cy + 17), fill=(121, 101, 76, 135), width=3)

    if pose == "point":
        pts = [(base_x, base_y), (base_x - 88 if left else base_x + 88, base_y - 64)]
        draw.line((*pts[0], *pts[1]), fill=limb, width=28)
        draw.line((pts[0][0], pts[0][1] - 6, pts[1][0], pts[1][1] - 6), fill=limb_hi, width=8)
        x, y = pts[1]
        mitten(x, y)
        draw.line((x, y - 7, x - 60 if left else x + 60, y - 34), fill=hand_fill, width=14)
        draw.line((x, y - 7, x - 60 if left else x + 60, y - 34), fill=outline, width=4)
    elif pose == "handoff":
        end_x = base_x + (116 if not left else -108)
        end_y = base_y - 46
        draw.line((base_x, base_y, end_x, end_y), fill=limb, width=29)
        draw.line((base_x, base_y - 7, end_x, end_y - 7), fill=limb_hi, width=8)
        mitten(end_x, end_y)
    else:
        draw.line((base_x, base_y, base_x + (-42 if left else 42), base_y + 72), fill=limb, width=28)
        draw.line((base_x, base_y - 5, base_x + (-42 if left else 42), base_y + 67), fill=limb_hi, width=8)
        x = base_x + (-45 if left else 45)
        y = base_y + 76
        mitten(x, y)
    img.save(path)


def draw_simple_part(path: Path, name: str) -> None:
    img = transparent()
    draw = ImageDraw.Draw(img)
    if name == "spectacles":
        for cx in (450, 575):
            draw_soft_ellipse(img, (cx - 61, 421, cx + 61, 533), (25, 18, 12, 80), 2)
            draw.ellipse((cx - 58, 418, cx + 58, 530), outline=(70, 52, 30, 255), width=10)
            draw.arc((cx - 54, 421, cx + 54, 526), 205, 302, fill=(214, 174, 92, 200), width=4)
            draw.arc((cx - 55, 421, cx + 55, 527), 28, 116, fill=(255, 231, 166, 135), width=3)
        draw.line((508, 476, 517, 476), fill=(70, 52, 30, 255), width=9)
        draw.line((410, 470, 370, 458), fill=(70, 52, 30, 220), width=6)
        draw.line((615, 470, 655, 458), fill=(70, 52, 30, 220), width=6)
    elif name == "bow_tie":
        draw_soft_ellipse(img, (438, 617, 588, 704), (24, 15, 17, 95), 5)
        draw.polygon([(430, 632), (512, 684), (512, 604)], fill=(132, 45, 68, 255))
        draw.polygon([(594, 632), (512, 684), (512, 604)], fill=(132, 45, 68, 255))
        draw.polygon([(444, 637), (501, 667), (503, 621)], fill=(175, 68, 91, 155))
        draw.polygon([(580, 637), (523, 667), (521, 621)], fill=(102, 32, 52, 170))
        draw.rectangle((495, 629, 529, 680), fill=(83, 27, 44, 255))
        draw.rectangle((501, 631, 516, 676), fill=(166, 61, 82, 140))
        draw.line((430, 632, 512, 684, 594, 632), fill=(50, 20, 30, 255), width=7)
    elif name == "lint_overlay_front":
        for i in range(90):
            x = 295 + (i * 71) % 435
            y = 240 + (i * 109) % 510
            alpha = 70 + (i % 4) * 28
            draw.line((x, y, x + 15 - (i % 7) * 4, y - 7 + (i % 5) * 3), fill=(234, 221, 195, alpha), width=2)
    elif name == "shadow_reference":
        draw.ellipse((330, 772, 694, 852), fill=(0, 0, 0, 70))
    img.save(path)


def paste_part_from_sheet(sheet: Image.Image, source_box: tuple[int, int, int, int], target_size: tuple[int, int], center: tuple[int, int], out_path: Path) -> None:
    part = sheet.crop(source_box).resize(target_size, Image.Resampling.LANCZOS)
    canvas = transparent()
    canvas.alpha_composite(part, (round(center[0] - target_size[0] / 2), round(center[1] - target_size[1] / 2)))
    canvas.save(out_path)


def install_generated_part_sheet() -> bool:
    if not PART_SHEET_SOURCE.exists():
        return False
    sheet = Image.open(PART_SHEET_SOURCE).convert("RGBA")
    generated_parts = {
        "eyes_open.png": ((112, 120, 394, 266), (238, 124), (512, 468)),
        "eyes_half.png": ((488, 120, 774, 266), (238, 124), (512, 468)),
        "eyes_closed.png": ((852, 122, 1136, 270), (238, 124), (512, 468)),
        "spectacles.png": ((28, 354, 456, 514), (292, 110), (512, 472)),
        "brows_neutral.png": ((474, 408, 716, 472), (218, 58), (512, 398)),
        "brows_worried.png": ((758, 394, 980, 478), (220, 72), (512, 398)),
        "brows_proud.png": ((1020, 378, 1230, 482), (220, 78), (512, 398)),
        "mouth_closed.png": ((78, 638, 216, 688), (102, 38), (512, 562)),
        "mouth_small_open.png": ((322, 628, 454, 710), (98, 60), (512, 568)),
        "mouth_wide_open.png": ((560, 590, 710, 730), (112, 104), (512, 571)),
        "mouth_oo.png": ((820, 620, 904, 704), (66, 66), (512, 570)),
        "mouth_frown.png": ((1024, 628, 1158, 700), (112, 60), (512, 570)),
        "hand_left_rest.png": ((76, 800, 296, 978), (152, 124), (300, 715)),
        "hand_left_point.png": ((360, 758, 560, 970), (162, 172), (245, 582)),
        "hand_right_rest.png": ((670, 800, 892, 976), (152, 122), (724, 715)),
        "hand_right_handoff.png": ((944, 802, 1192, 984), (182, 134), (806, 590)),
        "bow_tie.png": ((460, 1018, 794, 1204), (190, 104), (512, 656)),
    }
    for filename, (source_box, target_size, center) in generated_parts.items():
        paste_part_from_sheet(sheet, source_box, target_size, center, PARTS / filename)
    return True


def create_parts() -> dict[str, list[int]]:
    if PARTS.exists():
        shutil.rmtree(PARTS)
    PARTS.mkdir(parents=True, exist_ok=True)
    draw_body_variant(PARTS / "body_base.png")
    draw_body_variant(PARTS / "body_squash.png", squash=0.94, lift=10)
    draw_body_variant(PARTS / "body_stretch.png", squash=1.05, lift=-7)
    for name in ("open", "half", "closed"):
        draw_eyes(PARTS / f"eyes_{name}.png", name)
    for name in ("neutral", "worried", "proud"):
        draw_brows(PARTS / f"brows_{name}.png", name)
    for name in ("closed", "small_open", "wide_open", "oo", "frown"):
        draw_mouth(PARTS / f"mouth_{name}.png", name)
    draw_hand(PARTS / "hand_left_rest.png", "left", "rest")
    draw_hand(PARTS / "hand_left_point.png", "left", "point")
    draw_hand(PARTS / "hand_right_rest.png", "right", "rest")
    draw_hand(PARTS / "hand_right_handoff.png", "right", "handoff")
    for name in ("lint_overlay_front", "spectacles", "bow_tie", "shadow_reference"):
        draw_simple_part(PARTS / f"{name}.png", name)
    install_generated_part_sheet()
    return {
        "body_base.png": [512, 805],
        "body_squash.png": [512, 805],
        "body_stretch.png": [512, 805],
        "eyes_open.png": [512, 472],
        "eyes_half.png": [512, 472],
        "eyes_closed.png": [512, 472],
        "brows_neutral.png": [512, 414],
        "brows_worried.png": [512, 414],
        "brows_proud.png": [512, 414],
        "mouth_closed.png": [512, 580],
        "mouth_small_open.png": [512, 580],
        "mouth_wide_open.png": [512, 580],
        "mouth_oo.png": [512, 580],
        "mouth_frown.png": [512, 580],
        "hand_left_rest.png": [365, 656],
        "hand_left_point.png": [365, 656],
        "hand_right_rest.png": [650, 656],
        "hand_right_handoff.png": [650, 656],
        "lint_overlay_front.png": [512, 512],
        "spectacles.png": [512, 472],
        "bow_tie.png": [512, 660],
        "shadow_reference.png": [512, 805],
    }


def write_poses() -> None:
    data = {
        "schema_version": 1,
        "deterministic": True,
        "viseme_map": {
            "X": "mouth_closed.png",
            "A": "mouth_wide_open.png",
            "B": "mouth_closed.png",
            "C": "mouth_small_open.png",
            "D": "mouth_wide_open.png",
            "E": "mouth_oo.png",
            "F": "mouth_frown.png",
        },
        "states": {
            "idle": {
                "frames": 24,
                "fps": 12,
                "loop": True,
                "curves": {
                    "breath": {"amp_px": 14, "scale_amp": 0.035, "period_frames": 48},
                    "blink_frames": [7, 8],
                    "eye_shift": {"amp_px": 4, "period_frames": 72},
                    "lint_drift": {"amp_px": 5, "alpha_amp": 0.12, "period_frames": 37},
                    "hand_micro": {"amp_px": 9, "period_frames": 31},
                },
            },
            "talkBase": {
                "frames": 48,
                "fps": 12,
                "loop": True,
                "curves": {
                    "breath": {"amp_px": 16, "scale_amp": 0.04, "period_frames": 36},
                    "blink_frames": [18, 19, 43],
                    "eye_shift": {"amp_px": 5, "period_frames": 54},
                    "brow_pulses": [6, 14, 28, 38],
                    "hand_micro": {"amp_px": 16, "period_frames": 24},
                    "lint_drift": {"amp_px": 7, "alpha_amp": 0.16, "period_frames": 41},
                },
            },
            "greeting": {
                "frames": 36,
                "fps": 12,
                "loop": False,
                "keyframes": [
                    {"frame": 0, "body_y": 8, "body_scale": 0.98, "eyes": "half", "brows": "neutral", "left_hand": "rest", "right_hand": "rest", "mouth": "closed"},
                    {"frame": 8, "body_y": 0, "body_scale": 1.02, "eyes": "open", "brows": "worried", "left_hand": "rest", "right_hand": "rest", "mouth": "small_open"},
                    {"frame": 18, "body_y": -12, "body_scale": 1.04, "eyes": "open", "brows": "proud", "left_hand": "point", "right_hand": "rest", "mouth": "wide_open"},
                    {"frame": 35, "body_y": 0, "body_scale": 1.0, "eyes": "open", "brows": "neutral", "left_hand": "rest", "right_hand": "rest", "mouth": "closed"}
                ]
            },
            "handoff": {
                "frames": 36,
                "fps": 12,
                "loop": False,
                "keyframes": [
                    {"frame": 0, "body_y": 0, "body_scale": 1.0, "eyes": "open", "brows": "neutral", "left_hand": "rest", "right_hand": "rest", "mouth": "closed"},
                    {"frame": 10, "body_y": -6, "body_scale": 1.02, "eyes": "open", "brows": "proud", "left_hand": "rest", "right_hand": "handoff", "mouth": "small_open"},
                    {"frame": 22, "body_y": -2, "body_scale": 1.01, "eyes": "half", "brows": "proud", "left_hand": "rest", "right_hand": "handoff", "mouth": "closed"},
                    {"frame": 35, "body_y": 0, "body_scale": 1.0, "eyes": "open", "brows": "neutral", "left_hand": "rest", "right_hand": "rest", "mouth": "closed"}
                ]
            },
            "wrongAction": {
                "frames": 30,
                "fps": 12,
                "loop": False,
                "keyframes": [
                    {"frame": 0, "body_y": 0, "body_scale": 1.0, "eyes": "open", "brows": "neutral", "left_hand": "rest", "right_hand": "rest", "mouth": "closed"},
                    {"frame": 7, "body_y": -4, "body_scale": 1.01, "eyes": "half", "brows": "worried", "left_hand": "point", "right_hand": "rest", "mouth": "frown"},
                    {"frame": 16, "body_y": -8, "body_scale": 1.02, "eyes": "open", "brows": "worried", "left_hand": "point", "right_hand": "rest", "mouth": "wide_open"},
                    {"frame": 29, "body_y": 0, "body_scale": 1.0, "eyes": "open", "brows": "neutral", "left_hand": "rest", "right_hand": "rest", "mouth": "closed"}
                ]
            }
        }
    }
    POSES.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_part(name: str) -> Image.Image:
    return Image.open(PARTS / name).convert("RGBA")


def transform_layer(layer: Image.Image, y: float = 0, x: float = 0, scale_x: float = 1.0, scale_y: float = 1.0, alpha: float = 1.0) -> Image.Image:
    if scale_x != 1.0 or scale_y != 1.0:
        nw = max(1, round(layer.width * scale_x))
        nh = max(1, round(layer.height * scale_y))
        resized = layer.resize((nw, nh), Image.Resampling.BICUBIC)
        canvas = transparent()
        canvas.alpha_composite(resized, ((SOURCE_CANVAS[0] - nw) // 2, (SOURCE_CANVAS[1] - nh) // 2))
        layer = canvas
    if alpha < 0.999:
        r, g, b, a = layer.split()
        a = a.point(lambda value: round(value * alpha))
        layer = Image.merge("RGBA", (r, g, b, a))
    if x or y:
        shifted = transparent()
        shifted.alpha_composite(layer, (round(x), round(y)))
        return shifted
    return layer


def state_for_keyframes(state: dict, frame: int) -> dict:
    keys = state["keyframes"]
    prev = keys[0]
    nxt = keys[-1]
    for index, key in enumerate(keys):
        if key["frame"] <= frame:
            prev = key
        if key["frame"] >= frame:
            nxt = key
            break
    if prev is nxt:
        return dict(prev)
    t = ease_in_out((frame - prev["frame"]) / max(1, nxt["frame"] - prev["frame"]))
    result = dict(prev if t < 0.5 else nxt)
    for numeric in ("body_y", "body_scale"):
        result[numeric] = lerp(float(prev[numeric]), float(nxt[numeric]), t)
    return result


def procedural_state(name: str, state: dict, frame: int) -> dict:
    curves = state["curves"]
    breath = curves["breath"]
    phase = math.sin((frame / breath["period_frames"]) * math.tau)
    blink_frames = curves.get("blink_frames", [])
    eyes = "closed" if frame in blink_frames else "half" if frame - 1 in blink_frames or frame + 1 in blink_frames else "open"
    brow = "proud" if any(abs(frame - pulse) <= 2 for pulse in curves.get("brow_pulses", [])) else "neutral"
    mouth_cycle = ["closed", "small_open", "wide_open", "small_open", "oo", "closed", "frown", "closed"]
    return {
        "body_y": -phase * breath["amp_px"],
        "body_scale": 1 + phase * breath["scale_amp"],
        "eyes": eyes,
        "brows": brow,
        "left_hand": "rest",
        "right_hand": "handoff" if name == "talkBase" and frame % 16 in (5, 6, 7, 8) else "rest",
        "mouth": "closed" if name == "idle" else mouth_cycle[(frame // 3) % len(mouth_cycle)],
        "eye_shift": math.sin(frame / curves["eye_shift"]["period_frames"] * math.tau) * curves["eye_shift"]["amp_px"],
        "hand_y": math.sin(frame / curves["hand_micro"]["period_frames"] * math.tau) * curves["hand_micro"]["amp_px"],
        "lint_x": math.sin(frame / curves["lint_drift"]["period_frames"] * math.tau) * curves["lint_drift"]["amp_px"],
        "lint_y": math.cos(frame / (curves["lint_drift"]["period_frames"] + 9) * math.tau) * curves["lint_drift"]["amp_px"] * 0.55,
        "lint_alpha": 0.84 + math.sin(frame / curves["lint_drift"]["period_frames"] * math.tau) * curves["lint_drift"]["alpha_amp"],
    }


def render_frame(state_name: str, state: dict, frame: int, include_mouth: bool = True) -> Image.Image:
    pose = state_for_keyframes(state, frame) if "keyframes" in state else procedural_state(state_name, state, frame)
    if "keyframes" in state:
        # Keyframed gestures still need secondary life so long holds are not
        # duplicated static cels. Keep this subtle: lint and hands lag the main
        # pose without changing the actor's registration.
        pose.setdefault("eye_shift", math.sin((frame + len(state_name)) / 46 * math.tau) * 2.5)
        pose.setdefault("hand_y", math.sin((frame + len(state_name) * 3) / 29 * math.tau) * 3.5)
        pose.setdefault("lint_x", math.sin((frame + 5) / 31 * math.tau) * 4.0)
        pose.setdefault("lint_y", math.cos((frame + 9) / 37 * math.tau) * 2.5)
        pose.setdefault("lint_alpha", 0.88 + math.sin((frame + 11) / 23 * math.tau) * 0.08)
    img = transparent()
    body_part = "body_base.png"
    if pose["body_scale"] < 0.99:
        body_part = "body_squash.png"
    elif pose["body_scale"] > 1.012:
        body_part = "body_stretch.png"
    using_generated_body = CANONICAL_SOURCE.exists() or BODY_ONLY_SOURCE.exists()
    using_body_only = BODY_ONLY_SOURCE.exists()
    img.alpha_composite(transform_layer(load_part(body_part), y=pose.get("body_y", 0), scale_y=pose.get("body_scale", 1.0)))
    if using_generated_body:
        shimmer = transparent()
        shimmer_draw = ImageDraw.Draw(shimmer)
        seed = sum(ord(char) for char in state_name) + frame * 17
        for i in range(6):
            x = 345 + ((seed + i * 61) % 330)
            y = 290 + ((seed * 3 + i * 47) % 385)
            alpha = 32 + ((seed + i * 13) % 28)
            shimmer_draw.line((x, y, x + 7 - (i % 3) * 4, y - 3 + (i % 2) * 4), fill=(230, 211, 175, alpha), width=2)
        img.alpha_composite(transform_layer(shimmer, x=pose.get("lint_x", 0) * 0.22, y=pose.get("lint_y", 0) * 0.22))
    if not using_generated_body or using_body_only:
        img.alpha_composite(transform_layer(load_part("lint_overlay_front.png"), x=pose.get("lint_x", 0), y=pose.get("lint_y", 0), alpha=clamp(pose.get("lint_alpha", 0.9), 0.65, 1.0)))
        img.alpha_composite(transform_layer(load_part(f"eyes_{pose['eyes']}.png"), x=pose.get("eye_shift", 0), y=pose.get("body_y", 0) * 0.35))
        img.alpha_composite(transform_layer(load_part(f"brows_{pose['brows']}.png"), x=pose.get("eye_shift", 0) * 0.55, y=pose.get("body_y", 0) * 0.35))
        img.alpha_composite(transform_layer(load_part("spectacles.png"), y=pose.get("body_y", 0) * 0.35))
    elif pose["eyes"] != "open":
        img.alpha_composite(transform_layer(load_part(f"eyes_{pose['eyes']}.png"), x=pose.get("eye_shift", 0), y=pose.get("body_y", 0) * 0.35, alpha=0.82))
    if include_mouth and (not using_generated_body or using_body_only or pose["mouth"] != "closed"):
        img.alpha_composite(transform_layer(load_part(f"mouth_{pose['mouth']}.png"), y=pose.get("body_y", 0) * 0.45))
    if not using_generated_body or using_body_only:
        img.alpha_composite(transform_layer(load_part("bow_tie.png"), y=pose.get("body_y", 0) * 0.55))
        img.alpha_composite(transform_layer(load_part(f"hand_left_{pose['left_hand']}.png"), y=pose.get("hand_y", 0)))
        img.alpha_composite(transform_layer(load_part(f"hand_right_{pose['right_hand']}.png"), y=-abs(pose.get("hand_y", 0)) if pose["right_hand"] == "handoff" else pose.get("hand_y", 0)))
    else:
        if pose["left_hand"] != "rest":
            img.alpha_composite(transform_layer(load_part(f"hand_left_{pose['left_hand']}.png"), y=pose.get("hand_y", 0), alpha=0.86))
        if pose["right_hand"] != "rest":
            img.alpha_composite(transform_layer(load_part(f"hand_right_{pose['right_hand']}.png"), y=-abs(pose.get("hand_y", 0)) if pose["right_hand"] == "handoff" else pose.get("hand_y", 0), alpha=0.86))
    if FINAL_SOURCE_Y_OFFSET:
        padded = transparent()
        padded.alpha_composite(img, (0, FINAL_SOURCE_Y_OFFSET))
        img = padded
    return img.resize(RUNTIME_CANVAS, Image.Resampling.LANCZOS)


def write_registration(folder: Path, sheet_name: str, frame_count: int, prefix: str, state_name: str) -> None:
    frames = []
    for index in range(1, frame_count + 1):
        role = f"{state_name}-{index:02d}"
        entry = {"file": f"{prefix}_{index:02d}.png", "anchor": RUNTIME_ANCHOR, "role": role}
        if index == 1:
            entry["canonical"] = True
            entry["scale_reference"] = [160, 18]
        frames.append(entry)
    data = {
        "sheet": f"bramble-{state_name}",
        "actor_type": "furniture-anchored",
        "canvas": {"width": RUNTIME_CANVAS[0], "height": RUNTIME_CANVAS[1]},
        "anchor_tolerance_px": 1,
        "frames": frames,
        "approval_state": "rig-exported-pending-visual-review",
        "source": "art/rigs/bramble/manifest.json + art/rigs/bramble/poses.json",
    }
    folder.joinpath("registration.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_contact_sheet(folder: Path, frames: list[Path], label: str) -> None:
    thumb_w, thumb_h = 160, 130
    cols = 6
    rows = math.ceil(len(frames) / cols)
    sheet = Image.new("RGBA", (cols * thumb_w, rows * (thumb_h + 24)), PINK)
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except OSError:
        font = ImageFont.load_default()
    draw.text((10, 8), label, fill=(20, 12, 18), font=font)
    for i, path in enumerate(frames):
        with Image.open(path) as frame:
            thumb = frame.convert("RGBA")
            thumb.thumbnail((thumb_w - 18, thumb_h - 28), Image.Resampling.LANCZOS)
            x = (i % cols) * thumb_w + (thumb_w - thumb.width) // 2
            y = (i // cols) * (thumb_h + 24) + 18
            sheet.alpha_composite(thumb, (x, y))
            draw.text(((i % cols) * thumb_w + 8, y + thumb.height + 1), path.stem, fill=(20, 12, 18), font=font)
    QA.mkdir(parents=True, exist_ok=True)
    sheet.save(QA / f"bramble-{label}-contact-sheet.png")


def write_mouth_contact_sheet(frames: list[Path]) -> None:
    thumb_w, thumb_h = 160, 130
    sheet = Image.new("RGBA", (len(frames) * thumb_w, thumb_h + 34), PINK)
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except OSError:
        font = ImageFont.load_default()
    draw.text((10, 8), "mouths", fill=(20, 12, 18), font=font)
    for i, path in enumerate(frames):
        with Image.open(path) as frame:
            thumb = frame.convert("RGBA")
            thumb.thumbnail((thumb_w - 18, thumb_h - 34), Image.Resampling.LANCZOS)
            x = i * thumb_w + (thumb_w - thumb.width) // 2
            y = 20 + (thumb_h - 34 - thumb.height) // 2
            sheet.alpha_composite(thumb, (x, y))
            draw.text((i * thumb_w + 8, thumb_h + 16), path.stem, fill=(20, 12, 18), font=font)
    QA.mkdir(parents=True, exist_ok=True)
    sheet.save(QA / "bramble-mouths-contact-sheet.png")


def write_mouth_overlay_contact_sheet(base_frame: Path, frames: list[Path]) -> None:
    thumb_w, thumb_h = 180, 146
    sheet = Image.new("RGBA", (len(frames) * thumb_w, thumb_h + 34), PINK)
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except OSError:
        font = ImageFont.load_default()
    draw.text((10, 8), "mouth-overlay-runtime-alignment", fill=(20, 12, 18), font=font)
    with Image.open(base_frame) as base_source:
        base = base_source.convert("RGBA")
    for i, path in enumerate(frames):
        composite = base.copy()
        with Image.open(path) as mouth_source:
            composite.alpha_composite(mouth_source.convert("RGBA"))
        thumb = composite
        thumb.thumbnail((thumb_w - 18, thumb_h - 34), Image.Resampling.LANCZOS)
        x = i * thumb_w + (thumb_w - thumb.width) // 2
        y = 20 + (thumb_h - 34 - thumb.height) // 2
        sheet.alpha_composite(thumb, (x, y))
        draw.text((i * thumb_w + 8, thumb_h + 16), path.stem, fill=(20, 12, 18), font=font)
    QA.mkdir(parents=True, exist_ok=True)
    sheet.save(QA / "bramble-mouth-overlays-contact-sheet.png")


def write_gif(frames: list[Path], output: Path, duration_ms: int) -> None:
    images = [Image.open(path).convert("RGBA") for path in frames]
    output.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(output, save_all=True, append_images=images[1:], duration=duration_ms, loop=0, disposal=2)


def render_exports() -> dict[str, str]:
    poses = json.loads(POSES.read_text(encoding="utf-8"))
    rendered_hashes: dict[str, str] = {}
    mapping = {
        "idle": ("idle", "bramble_idle"),
        "talkBase": ("talk", "bramble_talk"),
        "greeting": ("greeting", "bramble_greeting"),
        "handoff": ("handoff", "bramble_handoff"),
        "wrongAction": ("wrong-action", "bramble_wrong"),
    }
    for state_name, (folder_name, prefix) in mapping.items():
        state = poses["states"][state_name]
        folder = OUT / folder_name
        if folder.exists():
            for png in folder.glob("*.png"):
                png.unlink()
        folder.mkdir(parents=True, exist_ok=True)
        paths = []
        for index in range(int(state["frames"])):
            frame = render_frame(state_name, state, index, include_mouth=state_name != "talkBase")
            path = folder / f"{prefix}_{index + 1:02d}.png"
            frame.save(path)
            paths.append(path)
            rendered_hashes[path.relative_to(ROOT).as_posix()] = sha256(path.read_bytes()).hexdigest()
        write_registration(folder, f"bramble-{folder_name}", int(state["frames"]), prefix, folder_name)
        write_contact_sheet(folder, paths, folder_name)
        write_gif(paths, QA / f"bramble-{folder_name}-normal.gif", round(1000 / int(state["fps"])))
        write_gif(paths, QA / f"bramble-{folder_name}-half-speed.gif", round(2000 / int(state["fps"])))
    mouth_dir = OUT / "mouths"
    if mouth_dir.exists():
        for png in mouth_dir.glob("*.png"):
            png.unlink()
    mouth_dir.mkdir(parents=True, exist_ok=True)
    poses = json.loads(POSES.read_text(encoding="utf-8"))
    mouth_paths: list[Path] = []
    for cue, part_name in poses["viseme_map"].items():
        mouth = load_part(part_name).resize(RUNTIME_CANVAS, Image.Resampling.LANCZOS)
        path = mouth_dir / f"bramble_mouth_{cue}.png"
        mouth.save(path)
        mouth_paths.append(path)
        rendered_hashes[path.relative_to(ROOT).as_posix()] = sha256(path.read_bytes()).hexdigest()
    write_mouth_contact_sheet(mouth_paths)
    write_mouth_overlay_contact_sheet(OUT / "talk" / "bramble_talk_01.png", mouth_paths)
    return rendered_hashes


def write_viseme_placeholders() -> None:
    viseme_dir = RIG / "visemes"
    viseme_dir.mkdir(parents=True, exist_ok=True)
    dialogue = json.loads((ROOT / "script" / "ACT_01_DIALOGUE.json").read_text(encoding="utf-8"))
    index: dict[str, dict] = {}
    for line in dialogue["lines"]:
        if line.get("speaker") != "BRAMBLE":
            continue
        duration = float(line.get("duration_s") or max(1.5, len(line.get("text", "")) * 0.055))
        cues = []
        cursor = 0.0
        pattern = ["X", "C", "D", "B", "E", "C", "A", "B"]
        step = 0.12
        i = 0
        while cursor < duration:
            end = min(duration, cursor + step)
            cues.append({"start": round(cursor, 3), "end": round(end, 3), "value": pattern[i % len(pattern)]})
            cursor = end
            i += 1
        out = {"line_id": line["line_id"], "source": "deterministic-text-fallback", "duration_s": duration, "mouthCues": cues}
        (viseme_dir / f"{line['line_id']}.mouthcues.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        index[line["line_id"]] = out
    (viseme_dir / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def update_manifest(pivots: dict[str, list[int]], hashes: dict[str, str]) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["status"] = "animation-ready"
    manifest["pivots"] = pivots
    manifest["poses"] = "poses.json"
    manifest["render"] = {
        "tool": "tools/render_bramble_rig.py",
        "source_canvas": list(SOURCE_CANVAS),
        "runtime_canvas": list(RUNTIME_CANVAS),
        "runtime_anchor": RUNTIME_ANCHOR,
        "deterministic": True,
        "hashes": hashes,
    }
    body_only = BODY_ONLY_SOURCE.exists()
    part_sheet = PART_SHEET_SOURCE.exists()
    manifest["source_art"] = {
        "mode": "separated-body-and-part-sheet-source" if body_only and part_sheet else "separated-body-source" if body_only else "hybrid-canonical-source",
        "body_only_alpha": BODY_ONLY_SOURCE.relative_to(ROOT).as_posix() if body_only else None,
        "canonical_alpha": CANONICAL_SOURCE.relative_to(ROOT).as_posix() if CANONICAL_SOURCE.exists() else None,
        "part_sheet_alpha": PART_SHEET_SOURCE.relative_to(ROOT).as_posix() if part_sheet else None,
        "notes": [
            "Bramble body identity comes from one high-quality keyed body-only image." if body_only else "Bramble body identity comes from one high-quality keyed canonical image.",
            "Breathing, blink, shimmer, gestures, and mouth visemes are deterministic rig controls.",
            "Generated part-sheet overlays replace procedural facial features, hands, bow tie, and visemes." if part_sheet else "Facial features, hands, bow tie, and visemes use deterministic procedural fallback art.",
            "The body has no baked face or hands; facial features, hands, bow tie, and visemes are separate rig parts." if body_only else "This is animation-ready but not a fully separated final rig because the canonical body still has baked facial details."
        ],
        "qa_contact_sheets": [
            "art/act01-production/qa/bramble-idle-contact-sheet.png",
            "art/act01-production/qa/bramble-talk-contact-sheet.png",
            "art/act01-production/qa/bramble-mouth-overlays-contact-sheet.png"
        ]
    }
    state_status = {
        "idle": ("exported", 24),
        "talk": ("exported", 48),
        "greeting": ("exported", 36),
        "handoff": ("exported", 36),
        "wrongAction": ("exported", 30),
    }
    for state, (status, frames) in state_status.items():
        manifest["states"][state]["status"] = status
        manifest["states"][state]["frames"] = frames
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    pivots = create_parts()
    write_poses()
    hashes = render_exports()
    write_viseme_placeholders()
    update_manifest(pivots, hashes)
    print("Rendered deterministic Bramble rig")
    print(f"Parts: {PARTS.relative_to(ROOT)}")
    print(f"Pose data: {POSES.relative_to(ROOT)}")
    print(f"Frames: {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
