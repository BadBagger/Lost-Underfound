#!/usr/bin/env python3
"""Validate engine-ready character sprite-strip packages."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXPORT_ROOT = ROOT / "art" / "engine-export"

REQUIRED: dict[str, dict] = {
    "pip": {
        "states": {"idle": 12, "walk": 12, "talk": 12, "inspect": 14, "dustReach": 14, "tollPaid": 10},
        "alpha_margin_px": 1,
    },
    "old-bottlecap": {
        "states": {"idle": 24, "tollRefused": 5, "tollPaid": 7},
        "alpha_margin_px": 4,
    },
    "scuttle": {
        "states": {"dash": 6},
        "alpha_margin_px": 0,
        "smear_states": {"dash"},
    },
    "bramble": {
        "states": {"idle": 24, "talk": 48, "greeting": 36, "handoff": 36, "wrongAction": 30},
        "alpha_margin_px": 1,
        "mouths": ["X", "A", "B", "C", "D", "E", "F"],
    },
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def fail(character: str, message: str) -> None:
    raise SystemExit(f"{character} engine export QA failed: {message}")


def alpha_bounds(image: Image.Image) -> tuple[int, int, int, int] | None:
    return image.convert("RGBA").getchannel("A").getbbox()


def check_strip(character: str, state_name: str, state: dict, expected_frames: int, min_margin: int, allow_edge_contact: bool) -> None:
    path = ROOT / state["file"]
    if not path.exists():
        fail(character, f"{state_name}: missing strip {state['file']}")
    if sha256(path.read_bytes()).hexdigest() != state.get("sha256"):
        fail(character, f"{state_name}: strip sha256 does not match manifest")
    cell_w, cell_h = state["cell"]
    with Image.open(path) as image:
        if image.mode not in {"RGBA", "P"}:
            fail(character, f"{state_name}: strip must preserve alpha-capable mode, got {image.mode}")
        if image.size != (cell_w * expected_frames, cell_h):
            fail(character, f"{state_name}: strip size {image.size} does not match {expected_frames} cells of {cell_w}x{cell_h}")
        for index in range(expected_frames):
            frame = image.crop((index * cell_w, 0, (index + 1) * cell_w, cell_h)).convert("RGBA")
            bounds = alpha_bounds(frame)
            if bounds is None:
                fail(character, f"{state_name}: frame {index + 1} has empty alpha")
            left, top, right, bottom = bounds
            margins = (left, top, cell_w - right, cell_h - bottom)
            if not allow_edge_contact and min(margins) < min_margin:
                fail(character, f"{state_name}: frame {index + 1} margin {margins} below {min_margin}px; likely cropped")
    if state.get("frames") != expected_frames:
        fail(character, f"{state_name}: manifest frame count is wrong")
    if not state.get("ags_view"):
        fail(character, f"{state_name}: missing AGS view name")
    if not state.get("source_hashes"):
        fail(character, f"{state_name}: missing source frame hashes")
    for source, digest in state["source_hashes"].items():
        source_path = ROOT / source
        if not source_path.exists():
            fail(character, f"{state_name}: missing hashed source frame {source}")
        if sha256(source_path.read_bytes()).hexdigest() != digest:
            fail(character, f"{state_name}: source hash drifted for {source}")


def check_character(character: str) -> None:
    spec = REQUIRED[character]
    manifest_path = EXPORT_ROOT / character / f"{character}.engine.json"
    if not manifest_path.exists():
        fail(character, f"missing export manifest: {rel(manifest_path)}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "engine-export-ready":
        fail(character, "export manifest must declare status=engine-export-ready")
    if manifest.get("character") != character:
        fail(character, "export manifest character id does not match path")
    if set(manifest.get("states", {})) != set(spec["states"]):
        fail(character, "export must include exactly the required animation states")
    review = ROOT / manifest.get("qa", {}).get("review_sheet", "")
    if not review.exists():
        fail(character, "missing engine export review sheet")

    for state_name, frame_count in spec["states"].items():
        allow_edge_contact = state_name in spec.get("smear_states", set())
        check_strip(character, state_name, manifest["states"][state_name], frame_count, spec["alpha_margin_px"], allow_edge_contact)

    if "mouths" in spec:
        mouths = manifest.get("mouth_visemes", {})
        if mouths.get("cues") != spec["mouths"]:
            fail(character, "mouth viseme cue order must be X,A,B,C,D,E,F")
        mouth_path = ROOT / mouths.get("file", "")
        if not mouth_path.exists():
            fail(character, "missing mouth viseme strip")
        if sha256(mouth_path.read_bytes()).hexdigest() != mouths.get("sha256"):
            fail(character, "mouth viseme strip sha256 does not match manifest")
        cell_w, cell_h = mouths["cell"]
        with Image.open(mouth_path) as image:
            if image.size != (cell_w * len(spec["mouths"]), cell_h):
                fail(character, f"mouth viseme strip size {image.size} does not match {len(spec['mouths'])} cells of {cell_w}x{cell_h}")

    print(f"PASS - {character} engine export has complete strips, metadata, alpha-safe canvases, and matching hashes.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("characters", nargs="*", choices=[*REQUIRED.keys(), "all"], default=["all"])
    args = parser.parse_args()
    requested = list(REQUIRED) if "all" in args.characters else args.characters
    for character in requested:
        check_character(character)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
