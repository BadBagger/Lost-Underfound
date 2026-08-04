"""Validate each discrete Room 1 background before AGS import."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ROOM = ROOT / "ags" / "room1"
SPEC = json.loads((ROOM / "geometry.json").read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise SystemExit(f"AGS Room 1 background QA failed: {message}")


def targets(screen: dict) -> dict[str, dict[str, int]]:
    result = {hotspot["id"]: hotspot["rect"] for hotspot in screen.get("hotspots", [])}
    result.update({item["id"]: item["rect"] for item in screen.get("walkBehinds", [])})
    return result


def main() -> None:
    for screen in SPEC["screens"]:
        screen_id = screen["id"]
        background = ROOM / screen["background"]
        review = background.with_suffix(".review.json")
        if not background.is_file():
            fail(f"missing {screen_id} background")
        if not review.is_file():
            fail(f"missing {screen_id} placement and visual-review manifest")
        with Image.open(background) as image:
            if image.size != (1280, 720) or image.mode not in {"RGB", "L"}:
                fail(f"{screen_id} must be opaque 1280x720")

        evidence = json.loads(review.read_text(encoding="utf-8"))
        if evidence.get("geometryAuthority") is not True or evidence.get("studiesReferenceOnly") is not True:
            fail(f"{screen_id} review must treat geometry as authority and studies as look references")
        expected_gates = {"objectPlacement", "internalLighting", "perspectiveEyeLevel", "finishedSurfaces", "dimensions"}
        if any(evidence.get("gates", {}).get(gate) != "pass" for gate in expected_gates):
            fail(f"{screen_id} has unapproved background acceptance gates")

        for name, target in targets(screen).items():
            measured = evidence.get("placements", {}).get(name)
            if not measured:
                fail(f"{screen_id} lacks measured {name} placement")
            tolerance = 2 if name in {"bramble-desk", "toll-gate"} else 6
            for key in ("x", "y", "width", "height"):
                if abs(measured[key] - target[key]) > tolerance:
                    fail(f"{screen_id} {name} {key} exceeds {tolerance}px tolerance")
    print("AGS Room 1 background QA passed: all three opaque screen backgrounds and placements verified.")


if __name__ == "__main__":
    main()
