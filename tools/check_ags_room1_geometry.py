"""Fail the build when the AGS Room 1 geometry contract drifts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "ags" / "room1" / "geometry.json"


def fail(message: str) -> None:
    raise SystemExit(f"AGS Room 1 geometry QA failed: {message}")


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    width = spec["resolution"]["width"]
    height = spec["resolution"]["height"]
    viewport = spec["viewport"]
    if (width, height) != (3840, 720):
        fail("Room 1 must remain a 3840x720 three-screen scrolling room")
    if viewport["width"] * viewport["screensWide"] != width:
        fail("room width must equal an integer number of viewport widths")
    if spec["camera"]["xMax"] != width - viewport["width"]:
        fail("camera xMax must match the rightmost legal viewport origin")

    desk, gate = spec["walkBehinds"]
    if desk["id"] != "desk" or desk["baseline"] != 614:
        fail("desk baseline must stay at 614")
    if gate["id"] != "toll-gate" or gate["baseline"] != 568:
        fail("gate baseline must stay at 568")

    positions = spec["standingPositions"]
    if not (positions["pip-talk-clerk"]["y"] < desk["baseline"]):
        fail("Pip's clerk spot must render behind the desk")
    if not (positions["old-bottlecap-guard"]["y"] > gate["baseline"]):
        fail("Bottlecap must render in front of gate bars")
    if positions["pip-entry"]["x"] < width - viewport["width"]:
        fail("Pip must begin in the rightmost camera beat")

    walkable = spec["walkableArea"]
    walkable_min_x = min(point[0] for point in walkable)
    walkable_max_x = max(point[0] for point in walkable)
    required_route = (
        positions["pip-entry"]["x"],
        positions["pip-exit-grate"]["x"],
        positions["pip-talk-clerk"]["x"],
        spec["hotspots"][0]["rect"]["x"],
        spec["hotspots"][1]["rect"]["x"],
    )
    if not all(walkable_min_x <= x <= walkable_max_x for x in required_route):
        fail("walkable corridor must connect entry, gate, clerk, cubbies, and dust")

    pip_height = spec["actorReference"]["pipHeight"]
    counter_delta = positions["pip-talk-clerk"]["y"] - desk["counterTopY"]
    if not (0.42 * pip_height <= counter_delta <= 0.58 * pip_height):
        fail("desk counter must meet Pip around mid-torso at clerk spot")

    print("AGS Room 1 geometry QA passed: 3-screen room, connected walk corridor, locked baselines, and calibrated actor blocking.")


if __name__ == "__main__":
    main()
