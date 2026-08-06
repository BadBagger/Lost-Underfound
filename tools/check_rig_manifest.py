#!/usr/bin/env python3
"""Validate deterministic character rig manifests before animation export."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("This tool requires Pillow: pip install Pillow")


ROOT = Path(__file__).resolve().parents[1]
EDGE_MARGIN = 2
PART_REQUIRED_STATUSES = {"parts-ready", "animation-ready"}
ANIMATION_REQUIRED_STATUSES = {"animation-ready"}
STATE_EXPORTS = {
    "idle": ("art/act01-production/characters/bramble/idle", "bramble_idle"),
    "talk": ("art/act01-production/characters/bramble/talk", "bramble_talk"),
    "greeting": ("art/act01-production/characters/bramble/greeting", "bramble_greeting"),
    "handoff": ("art/act01-production/characters/bramble/handoff", "bramble_handoff"),
    "wrongAction": ("art/act01-production/characters/bramble/wrong-action", "bramble_wrong"),
}


def fail(message: str) -> None:
    print(f"FAIL - {message}")
    raise SystemExit(1)


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def image_bbox(path: Path) -> tuple[int, int, int, int] | None:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        return rgba.getchannel("A").getbbox()


def validate_part(path: Path, expected_size: tuple[int, int]) -> list[str]:
    failures: list[str] = []
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        if rgba.size != expected_size:
            failures.append(f"{rel(path)} has size {rgba.size}, expected {expected_size}")
        bbox = rgba.getchannel("A").getbbox()
        if bbox is None:
            failures.append(f"{rel(path)} is empty")
        else:
            left, top, right, bottom = bbox
            width, height = rgba.size
            if left < EDGE_MARGIN or top < EDGE_MARGIN or right > width - EDGE_MARGIN or bottom > height - EDGE_MARGIN:
                failures.append(f"{rel(path)} touches canvas edge; re-pad source instead of crop-rescuing")
    return failures


def validate_pose_data(rig_dir: Path, manifest: dict) -> list[str]:
    failures: list[str] = []
    poses_name = manifest.get("poses", "poses.json")
    poses_path = rig_dir / poses_name
    if not poses_path.exists():
        return [f"missing pose data: {rel(poses_path)}"]
    poses = json.loads(poses_path.read_text(encoding="utf-8"))
    if not poses.get("deterministic"):
        failures.append(f"{rel(poses_path)} must declare deterministic=true")
    if "viseme_map" not in poses:
        failures.append(f"{rel(poses_path)} is missing viseme_map")
    pose_states = poses.get("states", {})
    for manifest_state, state in manifest.get("states", {}).items():
        pose_state_name = "talkBase" if manifest_state == "talk" else manifest_state
        pose_state = pose_states.get(pose_state_name)
        if not pose_state:
            failures.append(f"{rel(poses_path)} missing state {pose_state_name}")
            continue
        if int(pose_state.get("frames", 0)) != int(state.get("frames", -1)):
            failures.append(
                f"{pose_state_name}: poses frame count {pose_state.get('frames')} != manifest {state.get('frames')}"
            )
        if "curves" not in pose_state and "keyframes" not in pose_state:
            failures.append(f"{pose_state_name}: must declare curves or keyframes")
    return failures


def validate_exports(manifest: dict) -> list[str]:
    failures: list[str] = []
    recorded_hashes = manifest.get("render", {}).get("hashes", {})
    for state_name, state in manifest.get("states", {}).items():
        if state_name not in STATE_EXPORTS:
            continue
        folder_text, prefix = STATE_EXPORTS[state_name]
        folder = ROOT / folder_text
        expected = int(state.get("frames", 0))
        if not folder.exists():
            failures.append(f"{state_name}: missing export folder {folder_text}")
            continue
        frames = sorted(folder.glob(f"{prefix}_*.png"))
        if len(frames) != expected:
            failures.append(f"{state_name}: expected {expected} exported frame(s), found {len(frames)}")
        seen_hashes: set[str] = set()
        for path in frames:
            failures.extend(validate_part(path, (320, 260)))
            digest = sha256(path.read_bytes()).hexdigest()
            key = rel(path)
            if recorded_hashes.get(key) != digest:
                failures.append(f"{key}: hash does not match manifest render hash")
            if digest in seen_hashes:
                failures.append(f"{key}: duplicate rendered frame hash; fake density is not allowed")
            seen_hashes.add(digest)
        registration = folder / "registration.json"
        if not registration.exists():
            failures.append(f"{state_name}: missing registration.json")
    return failures


def validate_visemes(rig_dir: Path) -> list[str]:
    failures: list[str] = []
    dialogue_path = ROOT / "script" / "ACT_01_DIALOGUE.json"
    if not dialogue_path.exists():
        return failures
    dialogue = json.loads(dialogue_path.read_text(encoding="utf-8"))
    viseme_dir = rig_dir / "visemes"
    index_path = viseme_dir / "index.json"
    index = {}
    if not index_path.exists():
        failures.append(f"missing consolidated Bramble viseme index: {rel(index_path)}")
    else:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    bramble_lines = [line for line in dialogue.get("lines", []) if line.get("speaker") == "BRAMBLE" and line.get("audio_filename")]
    for line in bramble_lines:
        path = viseme_dir / f"{line['line_id']}.mouthcues.json"
        if not path.exists():
            failures.append(f"missing Bramble viseme cue file for voiced line: {rel(path)}")
            continue
        track = json.loads(path.read_text(encoding="utf-8"))
        cues = track.get("mouthCues", [])
        if not cues:
            failures.append(f"{rel(path)} has no mouthCues")
        if index and index.get(line["line_id"]) != track:
            failures.append(f"{rel(index_path)} does not match {rel(path)}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="rig manifest path")
    args = parser.parse_args()

    manifest_path = ROOT / args.manifest
    if not manifest_path.exists():
        fail(f"missing rig manifest: {rel(manifest_path)}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rig_dir = manifest_path.parent
    failures: list[str] = []

    for key in ("schema_version", "character", "status", "canvas", "required_parts", "pivots", "states"):
        if key not in manifest:
            failures.append(f"manifest missing {key}")

    canvas = tuple(manifest.get("canvas", []))
    if len(canvas) != 2 or not all(isinstance(value, int) and value > 0 for value in canvas):
        failures.append("canvas must be [width, height] with positive integers")
        canvas = (0, 0)

    status = manifest.get("status")
    required_parts = manifest.get("required_parts", [])
    forbidden_terms = [term.lower() for term in manifest.get("forbidden_scene_terms", [])]

    if status in PART_REQUIRED_STATUSES:
        for part_name in required_parts:
            lowered = part_name.lower()
            for term in forbidden_terms:
                if term in lowered:
                    failures.append(f"part filename contains forbidden scene term {term!r}: {part_name}")
            part_path = rig_dir / "parts" / part_name
            if not part_path.exists():
                failures.append(f"missing required rig part: {rel(part_path)}")
                continue
            failures.extend(validate_part(part_path, canvas))
            if part_name not in manifest.get("pivots", {}):
                failures.append(f"missing pivot for required part: {part_name}")

    if status in ANIMATION_REQUIRED_STATUSES:
        failures.extend(validate_pose_data(rig_dir, manifest))
        failures.extend(validate_exports(manifest))
        failures.extend(validate_visemes(rig_dir))
        for state_name, state in manifest.get("states", {}).items():
            if state.get("status") != "exported":
                failures.append(f"{state_name}: animation-ready manifest requires exported state")
            if int(state.get("frames", 0)) < 2:
                failures.append(f"{state_name}: state needs at least 2 frames")

    print(f"Rig manifest: {manifest.get('character', '<unknown>')} status={status}")
    if failures:
        print(f"\nFAIL - {len(failures)} rig issue(s):")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    if status not in PART_REQUIRED_STATUSES:
        print("PASS - rig manifest is scaffolded; part validation is blocked until status is parts-ready.")
    else:
        print("PASS - rig parts are present, padded, and pivot-declared.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
