#!/usr/bin/env python3
"""Visual QA for 3D-to-2D sprite proofs."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

from PIL import Image


DEFAULT_IGNORE_NAMES = {"outline", "room_dark", "hair"}


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"expected 6-digit hex color, got {value!r}")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def load_palette(path: Path) -> dict[str, tuple[int, int, int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    hero = data.get("hero")
    if not isinstance(hero, dict):
        raise ValueError(f"{path} does not contain a hero palette object")
    return {name: hex_to_rgb(value) for name, value in hero.items()}


def nearest_name(pixel: tuple[int, int, int], palette: dict[str, tuple[int, int, int]]) -> tuple[str, float]:
    name = min(palette, key=lambda key: color_distance(pixel, palette[key]))
    return name, color_distance(pixel, palette[name])


def iter_frame_paths(frames_dir: Path, frame_glob: str) -> list[Path]:
    paths = sorted(path for path in frames_dir.glob(frame_glob) if path.is_file())
    if not paths:
        raise FileNotFoundError(f"no PNG frames found in {frames_dir} matching {frame_glob!r}")
    return paths


def analyze_frame(
    path: Path,
    palette: dict[str, tuple[int, int, int]],
    ignore_names: set[str],
    distance_threshold: float,
    alpha_threshold: int,
) -> dict:
    img = Image.open(path).convert("RGBA")
    total_visible = 0
    analyzed = 0
    near_palette = 0
    ignored = Counter()
    counts = Counter()
    max_distance = 0.0

    for r, g, b, a in img.getdata():
        if a < alpha_threshold:
            continue
        total_visible += 1
        name, dist = nearest_name((r, g, b), palette)
        max_distance = max(max_distance, dist)
        if name in ignore_names:
            ignored[name] += 1
            continue
        analyzed += 1
        counts[name] += 1
        if dist <= distance_threshold:
            near_palette += 1

    shares = {name: count / analyzed for name, count in counts.items()} if analyzed else {}
    return {
        "file": path.name,
        "visible_pixels": total_visible,
        "analyzed_pixels": analyzed,
        "ignored_pixels": dict(sorted(ignored.items())),
        "palette_coverage": near_palette / analyzed if analyzed else 0.0,
        "max_distance": round(max_distance, 3),
        "counts": dict(sorted(counts.items())),
        "shares": {name: round(value, 5) for name, value in sorted(shares.items())},
        "dominant_color": counts.most_common(1)[0][0] if counts else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames-dir", required=True, type=Path)
    parser.add_argument("--frame-glob", default="*.png")
    parser.add_argument("--palette", default=Path("spikes/sprite_render/palette.json"), type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--target-color", default="blue_costume")
    parser.add_argument("--min-target-share", type=float, default=0.25)
    parser.add_argument("--forbid-color", action="append", default=["warm_highlight"])
    parser.add_argument("--max-forbid-share", type=float, default=0.01)
    parser.add_argument("--distance-threshold", type=float, default=12.0)
    parser.add_argument("--alpha-threshold", type=int, default=8)
    parser.add_argument("--face-mode", choices=["texture_only", "overlay"], default="texture_only")
    parser.add_argument("--require-face-overlay", action="store_true")
    args = parser.parse_args()

    palette = load_palette(args.palette)
    paths = iter_frame_paths(args.frames_dir, args.frame_glob)
    ignore_names = set(DEFAULT_IGNORE_NAMES)
    frames = [
        analyze_frame(path, palette, ignore_names, args.distance_threshold, args.alpha_threshold)
        for path in paths
    ]

    total_counts = Counter()
    total_analyzed = 0
    total_visible = 0
    ignored = Counter()
    coverage_sum = 0.0
    for frame in frames:
        total_counts.update(frame["counts"])
        total_analyzed += frame["analyzed_pixels"]
        total_visible += frame["visible_pixels"]
        ignored.update(frame["ignored_pixels"])
        coverage_sum += frame["palette_coverage"]

    total_shares = {name: count / total_analyzed for name, count in total_counts.items()} if total_analyzed else {}
    warnings: list[dict] = []

    target_share = total_shares.get(args.target_color, 0.0)
    if target_share < args.min_target_share:
        warnings.append({
            "type": "target_color_low",
            "color": args.target_color,
            "share": round(target_share, 5),
            "minimum": args.min_target_share,
        })

    for color in args.forbid_color:
        share = total_shares.get(color, 0.0)
        if share > args.max_forbid_share:
            warnings.append({
                "type": "forbidden_color_high",
                "color": color,
                "share": round(share, 5),
                "maximum": args.max_forbid_share,
            })

    if args.require_face_overlay and args.face_mode != "overlay":
        warnings.append({
            "type": "missing_face_overlay",
            "message": "production clips need a deterministic face overlay for eyes, blink, nose, and mouth visemes",
        })

    report = {
        "frames_dir": str(args.frames_dir),
        "palette": str(args.palette),
        "frame_count": len(frames),
        "ignored_palette_names": sorted(ignore_names),
        "visible_pixels": total_visible,
        "analyzed_pixels": total_analyzed,
        "ignored_pixels": dict(sorted(ignored.items())),
        "mean_palette_coverage": round(coverage_sum / len(frames), 5),
        "dominant_color_excluding_ignored": total_counts.most_common(1)[0][0] if total_counts else None,
        "shares_excluding_ignored": {name: round(value, 5) for name, value in sorted(total_shares.items())},
        "face_mode": args.face_mode,
        "warnings": warnings,
        "frames": frames,
        "passes": not warnings,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "frames": len(frames),
        "passes": report["passes"],
        "warnings": len(warnings),
        "dominant_color_excluding_ignored": report["dominant_color_excluding_ignored"],
        "target_share": round(target_share, 5),
    }, indent=2))
    return 0 if report["passes"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
