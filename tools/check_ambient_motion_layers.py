#!/usr/bin/env python3
"""Validate subtle ambient motion clips for the Act 1 room screens."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ags" / "ambient_motion_layers.json"
MAIN = ROOT / "src" / "main.ts"
SCENE_LAYERS = ROOT / "art" / "act01-production" / "scene" / "layers.json"


def fail(message: str) -> None:
    print(f"FAIL - {message}")
    raise SystemExit(1)


def frame_path(folder: str, prefix: str, index: int) -> Path:
    return ROOT / folder / f"{prefix}_{index:02d}.png"


def main() -> int:
    if not MANIFEST.exists():
        fail(f"missing ambient motion manifest: {MANIFEST.relative_to(ROOT).as_posix()}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    clips = manifest.get("clips", [])
    if not clips:
        fail("ambient motion manifest has no clips")

    admission = manifest.get("admission", {})
    min_loop_frames = int(admission.get("min_loop_frames", 6))
    max_fps = float(admission.get("max_fps", 5))
    max_dx = float(admission.get("max_path_dx_px", 64))
    max_dy = float(admission.get("max_path_dy_px", 16))

    scene_layers = json.loads(SCENE_LAYERS.read_text(encoding="utf-8"))
    scene_layer_ids = {layer.get("id") for layer in scene_layers.get("layers", [])}
    if "ambient-motion" not in scene_layer_ids:
        fail("scene layer manifest must declare ambient-motion")

    runtime = MAIN.read_text(encoding="utf-8")
    if 'import ambientMotion from "../ags/ambient_motion_layers.json"' not in runtime:
        fail("runtime must import the ambient motion manifest")
    if 'data-ambient-id="' not in runtime:
        fail("runtime must render identifiable ambient clips")

    ids: set[str] = set()
    for clip in clips:
        clip_id = clip.get("id", "")
        if not clip_id:
            fail("ambient clip is missing id")
        if clip_id in ids:
            fail(f"duplicate ambient clip id: {clip_id}")
        ids.add(clip_id)
        if clip.get("data_layer") != "ambient-motion":
            fail(f"{clip_id} must render inside data-layer ambient-motion")
        if clip.get("non_interactive") is not True:
            fail(f"{clip_id} must be non_interactive")
        if clip.get("loop") is not True:
            fail(f"{clip_id} must be a slow loop, not a one-shot event")
        frames = int(clip.get("frames", 0))
        if frames < min_loop_frames:
            fail(f"{clip_id} has {frames} frames; minimum is {min_loop_frames} to avoid fast-cycle jank")
        fps = float(clip.get("fps", 0))
        if fps <= 0 or fps > max_fps:
            fail(f"{clip_id} fps {fps} is outside ambient range 0 < fps <= {max_fps}")
        path = clip.get("path", {})
        if abs(float(path.get("dx", 0))) > max_dx:
            fail(f"{clip_id} moves too far horizontally for ambient motion")
        if abs(float(path.get("dy", 0))) > max_dy:
            fail(f"{clip_id} moves too far vertically for ambient motion")
        folder = str(clip.get("folder", ""))
        prefix = str(clip.get("prefix", ""))
        if not folder or not prefix:
            fail(f"{clip_id} must declare folder and prefix")
        for index in range(frames):
            frame = frame_path(folder, prefix, index)
            if not frame.exists():
                fail(f"{clip_id} missing frame {frame.relative_to(ROOT).as_posix()}")
        position = clip.get("position", {})
        for field in ("x", "y", "width", "height"):
            if float(position.get(field, 0)) <= 0:
                fail(f"{clip_id} position.{field} must be positive")
        if float(position["x"]) + float(position["width"]) > 1280:
            fail(f"{clip_id} extends past the room width")
        if float(position["y"]) + float(position["height"]) > 720:
            fail(f"{clip_id} extends past the room height")

    print(f"PASS - {len(clips)} ambient motion clip(s) are slow, non-interactive, and frame-complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
