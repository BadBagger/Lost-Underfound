"""Validate the final Room 1 background before it is imported into AGS."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ROOM = ROOT / "ags" / "room1"
GEOMETRY = ROOM / "geometry.json"
BACKGROUND = ROOM / "background" / "room1-background.png"
REVIEW = ROOM / "background" / "room1-background-review.json"
SEAM_DIR = ROOM / "background" / "qa"


def fail(message: str) -> None:
    raise SystemExit(f"AGS Room 1 background QA failed: {message}")


def target_rects(spec: dict) -> dict[str, dict[str, int]]:
    hotspots = {hotspot["id"]: hotspot["rect"] for hotspot in spec["hotspots"]}
    walk_behinds = {item["id"]: item["rect"] for item in spec["walkBehinds"]}
    return {
        "cubbies": hotspots["cubby-wall"],
        "dust-clump": hotspots["dust-clump"],
        "popcorn-boulder": hotspots["popcorn-boulder"],
        "wall-note": hotspots["wall-note"],
        "sign-in-log": hotspots["sign-in-log"],
        "desk": walk_behinds["desk"],
        "service-bell": hotspots["service-bell"],
        "toll-gate": walk_behinds["toll-gate"],
        "cobweb-tunnel": hotspots["cobweb-curtain"],
    }


def main() -> None:
    if not BACKGROUND.is_file():
        fail("missing ags/room1/background/room1-background.png")
    if not REVIEW.is_file():
        fail("missing placement and visual-review manifest")

    spec = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    with Image.open(BACKGROUND) as image:
        if image.size != (3840, 720):
            fail("background must be exactly 3840x720")
        if image.mode not in {"RGB", "L"}:
            fail("background must be fully opaque; alpha-bearing modes are not allowed")

    if review.get("geometryAuthority") is not True:
        fail("review must confirm geometry.json is the placement authority")
    if review.get("studiesReferenceOnly") is not True:
        fail("review must confirm generated studies were look references only")

    expected_gates = {
        "lockedObjectPlacement",
        "seamContinuity",
        "lightContinuity",
        "perspectiveEyeLevel",
        "finishedSurfaces",
        "dimensions",
    }
    gates = review.get("gates", {})
    failed_gates = sorted(gate for gate in expected_gates if gates.get(gate) != "pass")
    if failed_gates:
        fail("unapproved acceptance gates: " + ", ".join(failed_gates))
    if review.get("deskClerkBay") != "pass":
        fail("review must confirm the desk is a counter with an open clerk recess, not a sealed crate")

    targets = target_rects(spec)
    placements = review.get("placements", {})
    for name, target in targets.items():
        measured = placements.get(name)
        if not measured:
            fail(f"missing measured placement for {name}")
        tolerance = 2 if name in {"desk", "toll-gate"} else 6
        for key in ("x", "y", "width", "height"):
            delta = abs(measured[key] - target[key])
            if delta > tolerance:
                fail(f"{name} {key} delta {delta}px exceeds {tolerance}px")

    for seam in (1280, 2560):
        crop = SEAM_DIR / f"seam-{seam}.png"
        if not crop.is_file():
            fail(f"missing 200px seam review crop for x={seam}")
        with Image.open(crop) as image:
            if image.size != (200, 720):
                fail(f"seam-{seam}.png must be 200x720")

    print("AGS Room 1 background QA passed: dimensions, opaque surface, placement deltas, visual gates, and seam evidence verified.")


if __name__ == "__main__":
    main()
