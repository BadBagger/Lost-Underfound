#!/usr/bin/env python3
"""Production animation admission gate.

This is the layer above registration. Registration proves a sheet has a stable
canvas and anchor; admission proves it has enough frames, enough padding, stable
visible construction, and an explicit full-construction review artifact.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("This tool requires Pillow: pip install Pillow")


ROOT = Path(__file__).resolve().parents[1]


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def alpha_bounds(path: Path) -> tuple[int, int, int, int] | None:
    with Image.open(path) as img:
        return img.convert("RGBA").getchannel("A").getbbox()


def count_chroma_spill(path: Path, threshold: int = 48) -> int:
    with Image.open(path) as img:
        pixels = img.convert("RGBA").load()
        width, height = img.size
        spill_pixels = 0
        for y in range(height):
            for x in range(width):
                red, green, blue, alpha = pixels[x, y]
                if alpha and min(red, blue) - green > threshold:
                    spill_pixels += 1
        return spill_pixels


def check_sheet(entry: dict) -> list[str]:
    failures: list[str] = []
    reg_path = ROOT / entry["registration"]
    data = load_json(reg_path)
    frames = data.get("frames", [])
    sheet_dir = reg_path.parent
    sheet_id = entry.get("id", data.get("sheet", entry["registration"]))

    if "quarantine" in reg_path.parts:
        failures.append(f"{sheet_id}: quarantined registrations cannot be admitted: {rel(reg_path)}")

    min_frames = int(entry.get("min_frames", 1))
    if len(frames) < min_frames:
        failures.append(f"{sheet_id}: declares {len(frames)} frame(s), minimum is {min_frames}")

    if entry.get("loop") and len(frames) < int(entry.get("min_loop_frames", min_frames)):
        failures.append(
            f"{sheet_id}: looping clip has {len(frames)} frame(s); this risks a fast/janky cycle"
        )

    review = entry.get("full_construction_review")
    if entry.get("require_full_construction_review", True):
        if not review:
            failures.append(f"{sheet_id}: missing full_construction_review metadata")
        else:
            artifact = ROOT / review.get("artifact", "")
            if review.get("status") != "pass":
                failures.append(f"{sheet_id}: full_construction_review status must be pass")
            if not review.get("reviewer"):
                failures.append(f"{sheet_id}: full_construction_review reviewer is required")
            if not artifact.exists():
                failures.append(f"{sheet_id}: review artifact not found: {review.get('artifact')}")

    min_margin = int(entry.get("min_subject_margin_px", 0))
    max_bbox_delta_pct = float(entry.get("max_bbox_delta_pct", 0))
    max_chroma_spill_px = entry.get("max_chroma_spill_px")
    canonical_frame = next((frame for frame in frames if frame.get("canonical")), frames[0] if frames else None)
    canonical_box = None
    canonical_file = None
    if canonical_frame:
        canonical_path = sheet_dir / canonical_frame["file"]
        if canonical_path.exists():
            canonical_box = alpha_bounds(canonical_path)
            canonical_file = canonical_frame["file"]
        else:
            failures.append(f"{sheet_id}: canonical frame file not found: {canonical_frame['file']}")
    for frame in frames:
        frame_path = sheet_dir / frame["file"]
        if not frame_path.exists():
            failures.append(f"{sheet_id}: missing frame file {frame['file']}")
            continue
        bounds = alpha_bounds(frame_path)
        if bounds is None:
            failures.append(f"{sheet_id}: empty alpha in {frame['file']}")
            continue
        with Image.open(frame_path) as img:
            width, height = img.size
        left, top, right, bottom = bounds
        margins = (left, top, width - right, height - bottom)
        if min_margin and min(margins) < min_margin:
            failures.append(
                f"{sheet_id}: {frame['file']} subject margin {margins} below {min_margin}px; likely cropped or under-padded"
            )
        if max_chroma_spill_px is not None:
            spill_px = count_chroma_spill(frame_path)
            if spill_px > int(max_chroma_spill_px):
                failures.append(
                    f"{sheet_id}: {frame['file']} has {spill_px} magenta-spill pixel(s); "
                    f"maximum is {max_chroma_spill_px}. Run tools/despill_chroma.py before admission."
                )
        if canonical_box and max_bbox_delta_pct:
            cw = canonical_box[2] - canonical_box[0]
            ch = canonical_box[3] - canonical_box[1]
            bw = right - left
            bh = bottom - top
            width_delta = abs(bw - cw) / max(1, cw) * 100
            height_delta = abs(bh - ch) / max(1, ch) * 100
            if width_delta > max_bbox_delta_pct or height_delta > max_bbox_delta_pct:
                failures.append(
                    f"{sheet_id}: {frame['file']} visible bbox {bw}x{bh} drifts "
                    f"{width_delta:.1f}%/{height_delta:.1f}% from canonical "
                    f"{canonical_file} {cw}x{ch}; check scale/crop drift"
                )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    failures: list[str] = []
    for entry in manifest.get("sheets", []):
        failures.extend(check_sheet(entry))

    print(f"Animation admission: {len(manifest.get('sheets', []))} sheet(s)")
    if failures:
        print(f"\nFAIL - {len(failures)} admission issue(s):")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS - production animation sheets have review artifacts, padding, frame counts, and stable construction.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
