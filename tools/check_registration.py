#!/usr/bin/env python3
"""
Frame registration/normalization gate for animation cel sheets.

Two checks, run as subcommands:

  frames      Within one character's sheet: every frame must share the same
              canvas size and the same contact anchor (foot-ground for a
              walk-plane actor, counter/desk-contact line for a
              furniture-anchored actor), within tolerance.

  cast-scale  Across characters: every character's body scale, measured in a
              shared abstract "world height unit", must match its declared
              proportion relative to the rest of the cast -- so one actor
              doesn't render enormous next to another who's tiny in the same
              scene, even though each actor's own sheet is internally
              consistent.

Usage:
    python check_registration.py frames path/to/sheet/registration.json [--onion-skin out.png] [--tolerance-px 2]
    python check_registration.py cast-scale path/to/cast_scale.json [--tolerance-pct 8]

--- registration.json (one per character sheet) ---
{
  "sheet": "protagonist-walk",
  "actor_type": "walk-plane" | "furniture-anchored",
  "canvas": { "width": 384, "height": 512 },
  "anchor_tolerance_px": 2,
  "frames": [
    { "file": "walk_01.png", "anchor": [192, 480], "role": "left-contact", "canonical": true, "scale_reference": [192, 40] },
    { "file": "walk_02.png", "anchor": [192, 480], "role": "left-recoil-down" }
  ]
}

"anchor" is the contact-point pixel a human has confirmed for that frame --
foot-ground contact, or a furniture-anchored actor's counter-contact line.
It is authored data, not something inferred from pixel content: inferring
it from the visible bounding box would misfire on any frame with
legitimate secondary motion (a trailing coat tail, a raised arm), which the
Animation Bible requires, not forbids.

"scale_reference" is a SECOND authored landmark -- by convention, the
character's head-top in that pose -- required only on the frame(s) marked
"canonical": true (the character's neutral/idle pose). The vertical
distance between "anchor" and "scale_reference" on the canonical frame is
that character's measured standing height, in that sheet's own source
pixels. This is what cast-scale compares across characters -- not raw
sprite/canvas size, which is meaningless to compare directly once
furniture-anchored actors are cropped to a partial view.

--- cast_scale.json (one per project, lists the whole cast) ---
{
  "world_unit": "average adult standing height = 1.0",
  "tolerance_pct": 8,
  "actors": [
    { "name": "protagonist", "registration": "protagonist-walk/registration.json", "world_height_units": 1.0 },
    { "name": "quire", "registration": "quire-work/registration.json", "world_height_units": 0.97 },
    { "name": "kid-sidekick", "registration": "sidekick-walk/registration.json", "world_height_units": 0.65 }
  ]
}

world_height_units is director-authored ground truth for the cast's
relative proportions (an adult vs. a child, not an adult vs. another
adult who should read as the same size). The tool converts every
character's measured source-pixel height into "pixels per world unit" and
flags any actor whose value doesn't agree with the rest of the cast within
tolerance -- which is the actual bug this check exists for: source art
authored at inconsistent real-world scale, independent of anything the
engine does with setDisplaySize later.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("This tool requires Pillow: pip install Pillow")


# ---------- frames ----------

def load_registration(path: Path) -> dict:
    data = json.loads(path.read_text())
    required = {"sheet", "actor_type", "canvas", "frames"}
    missing = required - data.keys()
    if missing:
        sys.exit(f"{path}: registration.json missing required keys: {sorted(missing)}")
    if data["actor_type"] not in ("walk-plane", "furniture-anchored"):
        sys.exit(f"{path}: actor_type must be 'walk-plane' or 'furniture-anchored', got {data['actor_type']!r}")
    return data


def check_frame(sheet_dir: Path, frame: dict, expected_canvas: dict) -> list:
    frame_path = sheet_dir / frame["file"]
    if not frame_path.exists():
        return [f"{frame['file']}: file not found"]

    with Image.open(frame_path) as img:
        img = img.convert("RGBA")
        width, height = img.size
        failures = []

        if width != expected_canvas["width"] or height != expected_canvas["height"]:
            failures.append(
                f"{frame['file']}: canvas {width}x{height} != sheet canvas "
                f"{expected_canvas['width']}x{expected_canvas['height']}"
            )

        anchor_x, anchor_y = frame["anchor"]
        if not (0 <= anchor_x < width and 0 <= anchor_y < height):
            failures.append(
                f"{frame['file']}: declared anchor {frame['anchor']} falls outside "
                f"the frame's own canvas ({width}x{height})"
            )
    return failures


def check_anchor_consistency(frames: list, tolerance_px: int) -> list:
    if not frames:
        return []
    ref_x, ref_y = frames[0]["anchor"]
    failures = []
    for frame in frames[1:]:
        x, y = frame["anchor"]
        drift = max(abs(x - ref_x), abs(y - ref_y))
        if drift > tolerance_px:
            failures.append(
                f"{frame['file']}: anchor {frame['anchor']} drifts {drift}px from "
                f"sheet reference anchor {frames[0]['anchor']} ({frames[0]['file']}), "
                f"tolerance is {tolerance_px}px"
            )
    return failures


def build_onion_skin(sheet_dir: Path, frames: list, canvas: dict, out_path: Path) -> None:
    ref_x, ref_y = frames[0]["anchor"]
    composite = Image.new("RGBA", (canvas["width"], canvas["height"]), (0, 0, 0, 0))
    alpha_step = max(1, 255 // len(frames))

    for frame in frames:
        frame_path = sheet_dir / frame["file"]
        if not frame_path.exists():
            print(f"warning: {frame['file']} missing, skipped in onion-skin", file=sys.stderr)
            continue
        with Image.open(frame_path) as img:
            img = img.convert("RGBA")
            dx = ref_x - frame["anchor"][0]
            dy = ref_y - frame["anchor"][1]
            shifted = Image.new("RGBA", composite.size, (0, 0, 0, 0))
            shifted.paste(img, (dx, dy))
            r, g, b, a = shifted.split()
            a = a.point(lambda px: min(px, alpha_step))
            shifted.putalpha(a)
            composite = Image.alpha_composite(composite, shifted)

    draw = ImageDraw.Draw(composite)
    size = 10
    draw.line((ref_x - size, ref_y, ref_x + size, ref_y), fill=(255, 0, 255, 255), width=1)
    draw.line((ref_x, ref_y - size, ref_x, ref_y + size), fill=(255, 0, 255, 255), width=1)
    composite.save(out_path)
    print(f"onion-skin composite written to {out_path}")


def run_frames(args) -> int:
    if not args.registration_json.exists():
        sys.exit(f"not found: {args.registration_json}")

    data = load_registration(args.registration_json)
    sheet_dir = args.registration_json.parent
    tolerance_px = args.tolerance_px if args.tolerance_px is not None else data.get("anchor_tolerance_px", 2)
    frames = data["frames"]
    if not frames:
        sys.exit("registration.json declares zero frames")

    failures = []
    for frame in frames:
        failures.extend(check_frame(sheet_dir, frame, data["canvas"]))
    failures.extend(check_anchor_consistency(frames, tolerance_px))

    print(f"Sheet: {data['sheet']} ({data['actor_type']}), {len(frames)} frames, tolerance {tolerance_px}px")
    if failures:
        print(f"\nFAIL — {len(failures)} registration issue(s):")
        for failure in failures:
            print(f"  - {failure}")
    else:
        print("PASS — every frame matches the sheet's canvas size and anchor point.")

    if args.onion_skin:
        build_onion_skin(sheet_dir, frames, data["canvas"], args.onion_skin)
        print("Review the composite by eye even on a PASS — this checks the declared anchor")
        print("data is internally consistent, not that the anchor was placed correctly in the")
        print("first place. Confirm the crosshair sits on the real contact point.")

    return 1 if failures else 0


# ---------- cast-scale ----------

def measure_standing_height(registration_path: Path) -> tuple:
    """Returns (height_px, canonical_frame_filename)."""
    data = load_registration(registration_path)
    canonical = [f for f in data["frames"] if f.get("canonical")]
    if not canonical:
        sys.exit(f"{registration_path}: no frame marked \"canonical\": true — cast-scale needs "
                  f"one neutral/idle-pose frame per character with a \"scale_reference\" landmark")
    frame = canonical[0]
    if "scale_reference" not in frame:
        sys.exit(f"{registration_path}: canonical frame {frame['file']} has no \"scale_reference\"")
    _, anchor_y = frame["anchor"]
    _, ref_y = frame["scale_reference"]
    return abs(anchor_y - ref_y), frame["file"]


def run_cast_scale(args) -> int:
    if not args.cast_scale_json.exists():
        sys.exit(f"not found: {args.cast_scale_json}")

    data = json.loads(args.cast_scale_json.read_text())
    tolerance_pct = args.tolerance_pct if args.tolerance_pct is not None else data.get("tolerance_pct", 8)
    base_dir = args.cast_scale_json.parent

    measurements = []
    for actor in data["actors"]:
        reg_path = base_dir / actor["registration"]
        height_px, frame_file = measure_standing_height(reg_path)
        world_units = actor["world_height_units"]
        px_per_unit = height_px / world_units
        measurements.append({
            "name": actor["name"], "height_px": height_px, "frame": frame_file,
            "world_height_units": world_units, "px_per_unit": px_per_unit,
        })

    print(f"Cast scale check, {len(measurements)} actor(s), tolerance {tolerance_pct}%\n")
    for m in measurements:
        print(f"  {m['name']:<16} standing height {m['height_px']}px on {m['frame']} "
              f"({m['world_height_units']} world units -> {m['px_per_unit']:.1f} px/unit)")

    if len(measurements) < 2:
        print("\nOnly one actor — nothing to compare yet.")
        return 0

    mean_px_per_unit = sum(m["px_per_unit"] for m in measurements) / len(measurements)
    failures = []
    for m in measurements:
        deviation_pct = abs(m["px_per_unit"] - mean_px_per_unit) / mean_px_per_unit * 100
        if deviation_pct > tolerance_pct:
            failures.append(
                f"{m['name']}: {m['px_per_unit']:.1f} px/unit is {deviation_pct:.1f}% off the "
                f"cast mean ({mean_px_per_unit:.1f} px/unit) — source art was authored at the "
                f"wrong real-world scale relative to the rest of the cast, tolerance is {tolerance_pct}%"
            )

    if failures:
        print(f"\nFAIL — {len(failures)} actor(s) out of scale with the cast:")
        for failure in failures:
            print(f"  - {failure}")
    else:
        print("\nPASS — every actor's source-art scale agrees with the cast's declared proportions.")

    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    frames_parser = subparsers.add_parser("frames", help="check one character sheet's internal frame registration")
    frames_parser.add_argument("registration_json", type=Path)
    frames_parser.add_argument("--onion-skin", type=Path, default=None)
    frames_parser.add_argument("--tolerance-px", type=int, default=None)
    frames_parser.set_defaults(func=run_frames)

    cast_parser = subparsers.add_parser("cast-scale", help="check relative body scale across the whole cast")
    cast_parser.add_argument("cast_scale_json", type=Path)
    cast_parser.add_argument("--tolerance-pct", type=float, default=None)
    cast_parser.set_defaults(func=run_cast_scale)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
