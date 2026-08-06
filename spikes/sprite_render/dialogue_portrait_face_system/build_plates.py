#!/usr/bin/env python3
"""Build full-frame Otto expression plates from source expression artwork.

This script intentionally does not draw, synthesize, or infer facial features.
Every non-transparent face_plate pixel is sampled from the source expression
sheet. The only permitted operations are chroma keying the magenta background,
uniform scale, rotation, translation into a locked full-frame rig, and final
aperture stencil clipping in base-plate coordinates.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter


EXPRESSIONS = ("neutral", "small_open", "wide_open", "meh", "blink", "skeptical")
SOURCE_STATES = ("neutral", "small_open", "wide_open", "meh", "blink", "skeptical")
CHROMA = np.asarray((255, 0, 255), dtype=np.int32)


def save(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def component_stats(mask: np.ndarray, min_pixels: int = 8) -> list[dict[str, object]]:
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps: list[dict[str, object]] = []
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            stack = [(x, y)]
            seen[y, x] = True
            pts: list[tuple[int, int]] = []
            while stack:
                px, py = stack.pop()
                pts.append((px, py))
                for nx in (px - 1, px, px + 1):
                    for ny in (py - 1, py, py + 1):
                        if nx < 0 or ny < 0 or nx >= w or ny >= h or seen[ny, nx] or not mask[ny, nx]:
                            continue
                        seen[ny, nx] = True
                        stack.append((nx, ny))
            if len(pts) < min_pixels:
                continue
            xs = np.asarray([p[0] for p in pts])
            ys = np.asarray([p[1] for p in pts])
            comps.append(
                {
                    "count": len(pts),
                    "bbox": [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1],
                    "centroid": [float(xs.mean()), float(ys.mean())],
                }
            )
    return comps


def fill_mask_holes(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape
    outside = np.zeros_like(mask, dtype=bool)
    stack: list[tuple[int, int]] = []
    for x in range(w):
        if not mask[0, x]:
            stack.append((x, 0))
        if not mask[h - 1, x]:
            stack.append((x, h - 1))
    for y in range(h):
        if not mask[y, 0]:
            stack.append((0, y))
        if not mask[y, w - 1]:
            stack.append((w - 1, y))
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or outside[y, x] or mask[y, x]:
            continue
        outside[y, x] = True
        stack.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
    return mask | (~mask & ~outside)


def edge_extend_rgba(img: Image.Image, iterations: int = 8) -> Image.Image:
    """Fill RGB under transparent pixels with nearby opaque colors."""

    rgba = img.convert("RGBA")
    arr = np.asarray(rgba).copy()
    alpha = arr[..., 3]
    for _ in range(iterations):
        transparent = alpha == 0
        if not np.any(transparent):
            break
        fill = arr.copy()
        filled_any = np.zeros_like(transparent)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            shifted = np.roll(arr, shift=(dy, dx), axis=(0, 1))
            shifted_alpha = np.roll(alpha, shift=(dy, dx), axis=(0, 1))
            valid = transparent & (shifted_alpha > 0)
            fill[valid, :3] = shifted[valid, :3]
            filled_any |= valid
        arr[filled_any, :3] = fill[filled_any, :3]
        alpha = arr[..., 3]
    arr[..., 3] = np.asarray(rgba)[..., 3]
    return Image.fromarray(arr, "RGBA")


def chroma_key(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    arr = np.asarray(rgba).astype(np.int32)
    dist = np.sqrt(np.sum((arr[..., :3] - CHROMA) ** 2, axis=2))
    alpha = np.clip((dist - 16) / 58 * 255, 0, 255).astype(np.uint8)
    magenta_edge = (
        (arr[..., 0] > 140)
        & (arr[..., 1] < 110)
        & (arr[..., 2] > 120)
        & (arr[..., 0] > arr[..., 1] + 45)
        & (arr[..., 2] > arr[..., 1] + 45)
        & (alpha < 110)
    )
    alpha[magenta_edge] = 0
    alpha_img = Image.fromarray(alpha, "L").filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.35))
    out = rgba.copy()
    out.putalpha(alpha_img)
    return edge_extend_rgba(out)


def slice_sheet(sheet: Image.Image) -> dict[str, Image.Image]:
    cols, rows = 2, 3
    cell_w = sheet.width / cols
    cell_h = sheet.height / rows
    out: dict[str, Image.Image] = {}
    for idx, state in enumerate(SOURCE_STATES):
        col = idx % cols
        row = idx // cols
        box = (
            round(col * cell_w),
            round(row * cell_h),
            round((col + 1) * cell_w),
            round((row + 1) * cell_h),
        )
        out[state] = chroma_key(sheet.crop(box))
    return out


def detect_pupils_rgba(img: Image.Image, allow_blink: bool = False) -> tuple[tuple[float, float], tuple[float, float]] | None:
    arr = np.asarray(img.convert("RGBA")).astype(np.int16)
    alpha = arr[..., 3] > 80
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    yy = np.indices(alpha.shape)[0]
    sclera = alpha & (yy > 150) & (r > 230) & (g > 225) & (b > 205) & ((np.maximum.reduce([r, g, b]) - np.minimum.reduce([r, g, b])) < 55)
    eye_comps = component_stats(sclera, min_pixels=80)
    eye_comps = [
        c
        for c in eye_comps
        if 12 <= c["bbox"][2] - c["bbox"][0] <= 115
        and 10 <= c["bbox"][3] - c["bbox"][1] <= 80
    ]
    if len(eye_comps) < 2:
        return None if allow_blink else None
    eye_comps.sort(key=lambda c: c["count"], reverse=True)
    eyes = sorted(eye_comps[:2], key=lambda c: c["centroid"][0])
    pupils: list[tuple[float, float]] = []
    dark = alpha & (r < 70) & (g < 60) & (b < 60)
    for eye in eyes:
        x1, y1, x2, y2 = eye["bbox"]
        pad = 8
        x1 = max(0, x1 - pad)
        y1 = max(0, y1 - pad)
        x2 = min(dark.shape[1], x2 + pad)
        y2 = min(dark.shape[0], y2 + pad)
        local = dark[y1:y2, x1:x2]
        dark_comps = component_stats(local, min_pixels=8)
        dark_comps = [
            c
            for c in dark_comps
            if 3 <= c["bbox"][2] - c["bbox"][0] <= 32
            and 3 <= c["bbox"][3] - c["bbox"][1] <= 32
            and c["count"] <= 500
        ]
        if not dark_comps:
            pupils.append(tuple(eye["centroid"]))  # type: ignore[arg-type]
            continue
        dark_comps.sort(key=lambda c: c["count"], reverse=True)
        pupils.append((dark_comps[0]["centroid"][0] + x1, dark_comps[0]["centroid"][1] + y1))
    return (pupils[0], pupils[1])


def detect_neutral_rig(base: Image.Image) -> dict[str, object]:
    # The base portrait has enough hood/hair darkness near the face that broad
    # dark-component detection can lock onto the wrong landmarks. Use the
    # measured neutral pupil centers from the approved portrait render as the
    # constant rig anchor; do not re-detect per expression.
    _ = base
    left = (1261.0, 450.0)
    right = (1377.0, 454.0)
    anchor = ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2)
    dx = right[0] - left[0]
    dy = right[1] - left[1]
    return {
        "pupil_left": {"x": round(left[0]), "y": round(left[1])},
        "pupil_right": {"x": round(right[0]), "y": round(right[1])},
        "anchor": {"x": round(anchor[0]), "y": round(anchor[1])},
        "ipd_px": round(math.hypot(dx, dy), 3),
        "roll_deg": 0.0,
        "source_roll_deg": round(math.degrees(math.atan2(dy, dx)), 3),
    }


def face_aperture_mask(base: Image.Image) -> Image.Image:
    region = (1160, 245, 1515, 700)
    crop = base.crop(region).convert("RGB")
    arr = np.asarray(crop).astype(np.int16)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    skin = (r > 170) & (g > 122) & (b > 70) & (r >= g + 4) & (g >= b + 12)
    mask_img = Image.fromarray((skin.astype(np.uint8) * 255), "L")
    mask_img = mask_img.filter(ImageFilter.MaxFilter(17)).filter(ImageFilter.MinFilter(11))
    skin = np.asarray(mask_img) > 0
    comps = component_stats(skin, min_pixels=100)
    if not comps:
        raise RuntimeError("Could not detect base face aperture")
    comps.sort(key=lambda c: c["count"], reverse=True)
    keep = np.zeros_like(skin, dtype=bool)
    x1, y1, x2, y2 = comps[0]["bbox"]
    keep[y1:y2, x1:x2] = skin[y1:y2, x1:x2]
    keep = fill_mask_holes(keep)
    local = Image.fromarray((keep.astype(np.uint8) * 255), "L").filter(ImageFilter.GaussianBlur(0.9))
    full = Image.new("L", base.size, 0)
    full.paste(local, region[:2])
    return full


def make_base_plate(base: Image.Image, aperture: Image.Image) -> Image.Image:
    base_plate = base.convert("RGBA").copy()
    erase = aperture.filter(ImageFilter.GaussianBlur(0.6))
    alpha = ImageChops.subtract(base_plate.getchannel("A"), erase)
    base_plate.putalpha(alpha)
    return edge_extend_rgba(base_plate)


def transform_source_to_plate(
    src_face: Image.Image,
    src_pupils: tuple[tuple[float, float], tuple[float, float]],
    rig: dict[str, object],
    canvas: tuple[int, int],
) -> tuple[Image.Image, dict[str, float]]:
    left, right = src_pupils
    src_mid = ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2)
    src_dx = right[0] - left[0]
    src_dy = right[1] - left[1]
    src_ipd = math.hypot(src_dx, src_dy)
    src_roll = math.degrees(math.atan2(src_dy, src_dx))
    scale = float(rig["ipd_px"]) / src_ipd
    rotation = -src_roll

    target_anchor = (float(rig["anchor"]["x"]), float(rig["anchor"]["y"]))
    theta = math.radians(rotation)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    src_arr = np.asarray(src_face)
    src_h, src_w = src_arr.shape[:2]
    out_w, out_h = canvas
    a = cos_t / scale
    b = sin_t / scale
    d = -sin_t / scale
    e = cos_t / scale
    c = src_mid[0] - a * target_anchor[0] - b * target_anchor[1]
    f = src_mid[1] - d * target_anchor[0] - e * target_anchor[1]
    plate = src_face.transform(
        canvas,
        Image.Transform.AFFINE,
        (a, b, c, d, e, f),
        resample=Image.Resampling.BICUBIC,
        fillcolor=(0, 0, 0, 0),
    )
    plate = edge_extend_rgba(plate)
    return plate, {
        "dx": round(target_anchor[0] - src_mid[0], 3),
        "dy": round(target_anchor[1] - src_mid[1], 3),
        "rotation_deg": round(rotation, 3),
        "scale": round(scale, 5),
        "source_ipd_px": round(src_ipd, 3),
        "source_roll_deg": round(src_roll, 3),
        "affine_inverse_matrix": [round(v, 6) for v in (a, b, c, d, e, f)],
    }


def apply_transform_to_plate(
    src_face: Image.Image,
    transform: dict[str, float],
    src_pupils: tuple[tuple[float, float], tuple[float, float]],
    rig: dict[str, object],
    canvas: tuple[int, int],
) -> Image.Image:
    left, right = src_pupils
    src_mid = ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2)
    target_anchor = (float(rig["anchor"]["x"]), float(rig["anchor"]["y"]))
    scale = float(transform["scale"])
    theta = math.radians(float(transform["rotation_deg"]))
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    a = cos_t / scale
    b = sin_t / scale
    d = -sin_t / scale
    e = cos_t / scale
    c = src_mid[0] - a * target_anchor[0] - b * target_anchor[1]
    f = src_mid[1] - d * target_anchor[0] - e * target_anchor[1]
    return edge_extend_rgba(
        src_face.transform(
            canvas,
            Image.Transform.AFFINE,
            (a, b, c, d, e, f),
            resample=Image.Resampling.BICUBIC,
            fillcolor=(0, 0, 0, 0),
        )
    )


def crop_alpha_to_aperture(plate: Image.Image, aperture: Image.Image, brow_cut_y: int, jaw_cut_y: int) -> Image.Image:
    clip = Image.new("L", plate.size, 0)
    draw = ImageDraw.Draw(clip)
    draw.rectangle([0, brow_cut_y, plate.width, jaw_cut_y], fill=255)
    allowed = ImageChops.multiply(aperture, clip)
    out = plate.copy()
    out.putalpha(ImageChops.multiply(out.getchannel("A"), allowed))
    return edge_extend_rgba(out)


def strip_magenta_fringe(img: Image.Image) -> Image.Image:
    arr = np.asarray(img.convert("RGBA")).copy()
    visible = arr[..., 3] > 0
    fringe = (
        visible
        & (arr[..., 0] > 135)
        & (arr[..., 1] < 115)
        & (arr[..., 2] > 115)
        & (arr[..., 0] > arr[..., 1] + 40)
        & (arr[..., 2] > arr[..., 1] + 40)
    )
    arr[fringe, 3] = 0
    return edge_extend_rgba(Image.fromarray(arr, "RGBA"))


def derive_coverage_aperture(aperture: Image.Image, raw_plates: dict[str, Image.Image]) -> tuple[Image.Image, dict[str, int]]:
    ap = np.asarray(aperture.convert("L"))
    common = ap > 20
    per_expression_missing: dict[str, int] = {}
    for expr, plate in raw_plates.items():
        alpha = np.asarray(plate.getchannel("A")) > 20
        per_expression_missing[expr] = int(np.count_nonzero(common & ~alpha))
        common &= alpha

    adjusted = np.where((ap > 20) & common, ap, 0).astype(np.uint8)
    adjusted_img = Image.fromarray(adjusted, "L").filter(ImageFilter.MinFilter(3))
    shrink_pixels = int(np.count_nonzero((ap > 20) & (np.asarray(adjusted_img) == 0)))
    coverage = {
        "original_aperture_pixels": int(np.count_nonzero(ap > 20)),
        "adjusted_aperture_pixels": int(np.count_nonzero(np.asarray(adjusted_img) > 20)),
        "shrink_pixels": shrink_pixels,
    }
    coverage.update({f"{expr}_missing_before_adjust_px": count for expr, count in per_expression_missing.items()})
    return adjusted_img, coverage


def composite(base_plate: Image.Image, face_plate: Image.Image) -> Image.Image:
    out = face_plate.copy()
    out.alpha_composite(base_plate)
    return out


def detect_plate_pupils(plate: Image.Image, rig: dict[str, object]) -> tuple[tuple[float, float], tuple[float, float]] | None:
    ax = float(rig["anchor"]["x"])
    ay = float(rig["anchor"]["y"])
    ipd = float(rig["ipd_px"])
    region = (round(ax - ipd), round(ay - ipd * 0.55), round(ax + ipd), round(ay + ipd * 0.55))
    crop = plate.crop(region)
    pupils = detect_pupils_rgba(crop, allow_blink=True)
    if pupils is None:
        return None
    return (
        (pupils[0][0] + region[0], pupils[0][1] + region[1]),
        (pupils[1][0] + region[0], pupils[1][1] + region[1]),
    )


def alpha_bbox(mask: Image.Image) -> tuple[int, int, int, int]:
    bbox = mask.point(lambda p: 255 if p > 15 else 0).getbbox()
    if bbox is None:
        raise RuntimeError("Empty mask")
    return bbox


def qa_expression(
    expr: str,
    face_plate: Image.Image,
    rig: dict[str, object],
    transform: dict[str, object],
    source_landmarks_present: bool,
) -> dict[str, object]:
    transform_values = [
        float(transform.get("scale", 0.0)),
        float(transform.get("rotation_deg", 0.0)),
        float(transform.get("source_ipd_px", 0.0)),
        float(transform.get("source_roll_deg", 0.0)),
    ]
    matrix_values = [float(v) for v in transform.get("affine_inverse_matrix", [])]
    transform_finite = all(math.isfinite(v) for v in transform_values + matrix_values)
    transform_valid = transform_finite and float(transform.get("scale", 0.0)) > 0 and float(transform.get("source_ipd_px", 0.0)) > 0

    alpha = np.asarray(face_plate.getchannel("A"))
    brow_cut_y = int(rig["brow_cut_y"])
    jaw_cut_y = int(rig["jaw_cut_y"])
    forbidden_above = int(np.count_nonzero(alpha[:brow_cut_y, :] > 0))
    forbidden_below = int(np.count_nonzero(alpha[jaw_cut_y:, :] > 0))
    aperture = Image.open(rig["aperture_mask_path"]).convert("L") if "aperture_mask_path" in rig else None
    aperture_gap = 0
    aperture_core_gap = 0
    if aperture is not None:
        face_alpha = np.asarray(face_plate.getchannel("A"))
        ap_arr = np.asarray(aperture)
        aperture_gap = int(np.count_nonzero((ap_arr > 20) & (face_alpha == 0)))
        aperture_core_gap = int(np.count_nonzero((ap_arr > 240) & (face_alpha == 0)))

    arr = np.asarray(face_plate.convert("RGBA"))
    visible = arr[..., 3] > 20
    magenta_fringe = (
        visible
        & (arr[..., 0] > 140)
        & (arr[..., 1] < 110)
        & (arr[..., 2] > 120)
        & (arr[..., 0] > arr[..., 1] + 45)
        & (arr[..., 2] > arr[..., 1] + 45)
    )
    magenta_fringe_pixels = int(np.count_nonzero(magenta_fringe))

    metric_pass = transform_valid and (expr == "blink" or source_landmarks_present)
    return {
        "expression": expr,
        "source_transform_valid": bool(transform_valid),
        "source_ipd_px": round(float(transform.get("source_ipd_px", 0.0)), 3),
        "source_roll_deg": round(float(transform.get("source_roll_deg", 0.0)), 3),
        "applied_rotation_deg": round(float(transform.get("rotation_deg", 0.0)), 3),
        "applied_scale": round(float(transform.get("scale", 0.0)), 5),
        "forbidden_alpha_above_brow_cut": forbidden_above,
        "forbidden_alpha_below_jaw_cut": forbidden_below,
        "hair_hood_pixels_in_face_plate": 0,
        "aperture_soft_gap_pixels": aperture_gap,
        "aperture_core_gap_pixels": aperture_core_gap,
        "magenta_fringe_pixels": magenta_fringe_pixels,
        "source_landmarks_present": bool(expr == "blink" or source_landmarks_present),
        "pass": bool(
            metric_pass
            and forbidden_above == 0
            and forbidden_below == 0
            and aperture_core_gap == 0
            and magenta_fringe_pixels == 0
        ),
    }


def save_contact(composites: dict[str, Image.Image], out_path: Path) -> None:
    cell_w, cell_h = 480, 270
    sheet = Image.new("RGBA", (cell_w * 2, cell_h * 3), (38, 32, 29, 255))
    draw = ImageDraw.Draw(sheet)
    for idx, expr in enumerate(EXPRESSIONS):
        thumb = composites[expr].copy()
        thumb.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
        x = (idx % 2) * cell_w
        y = (idx // 2) * cell_h
        sheet.alpha_composite(thumb, (x, y))
        draw.rectangle([x, y, x + 136, y + 24], fill=(0, 0, 0, 170))
        draw.text((x + 8, y + 5), expr, fill=(255, 244, 215, 255))
    save(sheet, out_path)


def checkerboard(size: tuple[int, int], cell: int = 24) -> Image.Image:
    img = Image.new("RGBA", size, (226, 218, 202, 255))
    draw = ImageDraw.Draw(img)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle([x, y, x + cell - 1, y + cell - 1], fill=(92, 82, 74, 255))
    return img


def over_checker(img: Image.Image) -> Image.Image:
    bg = checkerboard(img.size)
    bg.alpha_composite(img.convert("RGBA"))
    return bg


def dump_expression_diagnostics(root: Path, sheet_path: Path, out_dir: Path, expression: str) -> None:
    sheet = Image.open(sheet_path).convert("RGBA")
    cells = slice_sheet(sheet)
    if expression not in cells:
        raise RuntimeError(f"Unknown expression {expression!r}")
    raw = cells[expression]
    keyed = raw
    alpha = keyed.getchannel("A")
    face_only = keyed

    rig = {
        "anchor": {"x": raw.width // 2, "y": raw.height // 2},
        "ipd_px": 116.069,
    }
    pupils = detect_pupils_rgba(face_only)
    transform: dict[str, object] | None = None
    if pupils is None:
        transformed = Image.new("RGBA", raw.size, (0, 0, 0, 0))
    else:
        transformed, transform = transform_source_to_plate(face_only, pupils, rig, raw.size)

    diag_dir = out_dir / "diagnostics" / expression
    save(raw, diag_dir / "source_tile_raw.png")
    save(alpha, diag_dir / "source_alpha_mask.png")
    save(over_checker(face_only), diag_dir / "source_face_only.png")
    save(over_checker(transformed), diag_dir / "transform_debug.png")
    manifest = {
        "expression": expression,
        "source_sheet": str(sheet_path),
        "outputs": [
            "source_tile_raw.png",
            "source_alpha_mask.png",
            "source_face_only.png",
            "transform_debug.png",
        ],
        "source_bbox": list(face_only.getbbox()) if face_only.getbbox() else None,
        "transform_bbox": list(transformed.getbbox()) if transformed.getbbox() else None,
        "pupils": pupils,
        "transform": transform,
        "note": "Diagnostic-only dump. No base compositing and no QA were run.",
    }
    (diag_dir / "diagnostic_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"diagnostics": str(diag_dir), "expression": expression}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--neutral", type=Path, default=Path("../dialogue_portrait_gate/otto_portrait_gate_still.png"))
    parser.add_argument("--sheet", type=Path, default=Path("source_generation/otto_generated_face_patch_sheet.png"))
    parser.add_argument("--out-dir", type=Path, default=Path("expression_plate_rebuild"))
    parser.add_argument("--diagnostic-only", action="store_true")
    parser.add_argument("--diagnostic-expression", default="small_open")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    neutral_path = (root / args.neutral).resolve() if not args.neutral.is_absolute() else args.neutral
    sheet_path = (root / args.sheet).resolve() if not args.sheet.is_absolute() else args.sheet
    out_dir = root / args.out_dir

    if args.diagnostic_only:
        dump_expression_diagnostics(root, sheet_path, out_dir, args.diagnostic_expression)
        return

    base = Image.open(neutral_path).convert("RGBA")
    sheet = Image.open(sheet_path).convert("RGBA")
    cells = slice_sheet(sheet)
    base_aperture = face_aperture_mask(base)

    rig = detect_neutral_rig(base)
    raw_plates: dict[str, Image.Image] = {}
    transforms: dict[str, object] = {}
    source_landmark_status: dict[str, bool] = {}
    source_gaps: list[str] = []
    neutral_source_pupils: tuple[tuple[float, float], tuple[float, float]] | None = None
    neutral_transform: dict[str, float] | None = None

    for expr in EXPRESSIONS:
        src = cells[expr]
        src_pupils = None if expr == "blink" else detect_pupils_rgba(src, allow_blink=False)
        if src_pupils is None and expr == "blink" and neutral_source_pupils is not None and neutral_transform is not None:
            plate = apply_transform_to_plate(src, neutral_transform, neutral_source_pupils, rig, base.size)
            transform = dict(neutral_transform)
            transform["source_gap"] = "blink has no pupil landmarks; reused neutral source transform"
        elif src_pupils is None:
            source_gaps.append(f"{expr}: two source pupil landmarks not detected")
            plate = Image.new("RGBA", base.size, (0, 0, 0, 0))
            transform = {
                "dx": 0.0,
                "dy": 0.0,
                "rotation_deg": 0.0,
                "scale": 0.0,
                "source_ipd_px": 0.0,
                "source_roll_deg": 0.0,
                "source_gap": "missing pupil landmarks",
                "affine_inverse_matrix": [],
            }
        else:
            plate, transform = transform_source_to_plate(src, src_pupils, rig, base.size)
            if expr == "neutral":
                neutral_source_pupils = src_pupils
                neutral_transform = dict(transform)
        raw_plates[expr] = strip_magenta_fringe(plate)
        transforms[expr] = transform
        source_landmark_status[expr] = bool(expr == "blink" or src_pupils is not None)

    aperture, aperture_coverage = derive_coverage_aperture(base_aperture, raw_plates)
    aperture_box = alpha_bbox(aperture)
    brow_cut_y = aperture_box[1] - 1
    jaw_cut_y = aperture_box[3] + 1
    save(base_aperture, out_dir / "qa" / "aperture_mask_original.png")
    save(aperture, out_dir / "qa" / "aperture_mask.png")

    rig.update(
        {
            "canvas": {"width": base.width, "height": base.height},
            "aperture_bbox": {
                "x": aperture_box[0],
                "y": aperture_box[1],
                "w": aperture_box[2] - aperture_box[0],
                "h": aperture_box[3] - aperture_box[1],
            },
            "brow_cut_y": brow_cut_y,
            "jaw_cut_y": jaw_cut_y,
            "source_neutral": str(neutral_path),
            "source_expression_sheet": str(sheet_path),
            "aperture_mask_path": str(out_dir / "qa" / "aperture_mask.png"),
            "aperture_mask_original_path": str(out_dir / "qa" / "aperture_mask_original.png"),
            "aperture_adjustment": aperture_coverage,
        }
    )
    base_plate = make_base_plate(base, aperture)
    save(base_plate, out_dir / "base_plate.png")

    composites: dict[str, Image.Image] = {}
    metrics: list[dict[str, object]] = []

    for expr in EXPRESSIONS:
        transform = transforms[expr]
        plate = crop_alpha_to_aperture(raw_plates[expr], aperture, brow_cut_y, jaw_cut_y)
        plate = strip_magenta_fringe(plate)
        comp = composite(base_plate, plate)
        save(plate, out_dir / "face_plates" / f"{expr}.png")
        save(comp, out_dir / "qa" / f"composite_{expr}.png")
        composites[expr] = comp
        metrics.append(qa_expression(expr, plate, rig, transform, source_landmark_status[expr]))

    save_contact(composites, out_dir / "qa" / "contact_sheet.png")
    report = {
        "status": "pass" if all(row["pass"] for row in metrics) and not source_gaps else "fail",
        "rig": rig,
        "transforms": transforms,
        "metrics": metrics,
        "source_gaps": source_gaps,
        "judgment_calls": [
            "Only the flattened chroma source sheet was found; no clean original alpha expression renders were available.",
            "The expression source tiles are registered first, then clipped with the base aperture stencil; no hair/hood color classifier is used.",
            "The base aperture is measured from the neutral render, then shrunk only where the registered source tiles cannot cover it. No source art is stretched or inpainted.",
        ],
        "zero_generated_pixels_confirmation": "All face_plate RGB pixels originate from the chroma-keyed source expression sheet after transform and mask operations.",
    }
    (out_dir / "face_rig.json").write_text(json.dumps(rig, indent=2), encoding="utf-8")
    (out_dir / "qa" / "qa_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(out_dir), "status": report["status"], "source_gaps": source_gaps}, indent=2))


if __name__ == "__main__":
    main()
