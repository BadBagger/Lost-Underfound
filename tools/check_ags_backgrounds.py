"""Validate all discrete AGS room background plates before import."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
AGS_DIR = ROOT / "ags"
EXPECTED_SIZE = (1280, 720)


def fail(message: str) -> None:
    raise SystemExit(f"AGS background QA failed: {message}")


def rect_dict(rect: dict[str, Any]) -> dict[str, int]:
    return {
        "x": round(float(rect["x"])),
        "y": round(float(rect["y"])),
        "width": round(float(rect["width"])),
        "height": round(float(rect["height"])),
    }


def targets(screen: dict[str, Any]) -> dict[str, dict[str, int]]:
    result = {hotspot["id"]: rect_dict(hotspot["rect"]) for hotspot in screen.get("hotspots", [])}
    result.update({item["id"]: rect_dict(item["rect"]) for item in screen.get("walkBehinds", [])})
    result.update({item["id"]: rect_dict(item["rect"]) for item in screen.get("walkbehinds", [])})
    return result


def validate_room(path: Path) -> int:
    room_name = path.parent.name
    spec = json.loads(path.read_text(encoding="utf-8"))
    checked = 0
    for screen in spec.get("screens", []):
        screen_id = screen["id"]
        background = path.parent / screen["background"]
        review = background.with_suffix(".review.json")
        source = background.with_name(f"{background.stem}.source.png")
        if not background.is_file():
            fail(f"{room_name}/{screen_id} missing normalized background")
        if not source.is_file():
            fail(f"{room_name}/{screen_id} missing retained source background")
        if not review.is_file():
            fail(f"{room_name}/{screen_id} missing placement and visual-review manifest")

        with Image.open(background) as image:
            if image.size != EXPECTED_SIZE:
                fail(f"{room_name}/{screen_id} must be {EXPECTED_SIZE[0]}x{EXPECTED_SIZE[1]}")
            if image.mode not in {"RGB", "L"}:
                fail(f"{room_name}/{screen_id} must be opaque RGB/L, not {image.mode}")

        evidence = json.loads(review.read_text(encoding="utf-8"))
        if evidence.get("geometryAuthority") is not True or evidence.get("studiesReferenceOnly") is not True:
            fail(f"{room_name}/{screen_id} review must treat geometry as authority and studies as look references")
        expected_gates = {"objectPlacement", "internalLighting", "perspectiveEyeLevel", "finishedSurfaces", "dimensions"}
        for gate in expected_gates:
            if evidence.get("gates", {}).get(gate) != "pass":
                fail(f"{room_name}/{screen_id} has unapproved {gate} gate")
        visual_review = evidence.get("visualReview")
        if not isinstance(visual_review, dict):
            fail(f"{room_name}/{screen_id} missing visualReview admission notes")
        if visual_review.get("status") not in {"intake", "approved"}:
            fail(f"{room_name}/{screen_id} visualReview status must be intake or approved")
        if not visual_review.get("actorProofRequired"):
            fail(f"{room_name}/{screen_id} must require an actor-scale proof before final import")
        if not visual_review.get("blockingNotes"):
            fail(f"{room_name}/{screen_id} visualReview must include blocking notes")

        placements = evidence.get("placements", {})
        for name, target in targets(screen).items():
            measured = placements.get(name)
            if not measured:
                fail(f"{room_name}/{screen_id} lacks measured {name} placement")
            tolerance = 2 if name in {"bramble-desk", "toll-gate", "annex-door", "toggle-desk", "open-grate"} else 6
            for key in ("x", "y", "width", "height"):
                if abs(round(float(measured[key])) - target[key]) > tolerance:
                    fail(f"{room_name}/{screen_id} {name} {key} exceeds {tolerance}px tolerance")
        checked += 1
    return checked


def main() -> None:
    paths = sorted(AGS_DIR.glob("room*/geometry.json"))
    if not paths:
        fail("no AGS room geometry files found")
    count = sum(validate_room(path) for path in paths)
    print(f"AGS background QA passed: {count} opaque screen background(s) are sized, manifested, and geometry-locked.")


if __name__ == "__main__":
    main()
