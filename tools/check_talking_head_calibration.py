"""Check anchor, canvas, and construction margins for talking-head sprite clips."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise SystemExit(f"Talking-head calibration QA failed: {message}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: check_talking_head_calibration.py <registration.json>")
    registration_path = ROOT / sys.argv[1]
    spec = json.loads(registration_path.read_text(encoding="utf-8"))
    canvas = (spec["canvas"]["width"], spec["canvas"]["height"])
    expected_anchor_y = spec["frames"][0]["anchor"][1]
    visible_heights: list[int] = []

    for frame in spec["frames"]:
        path = registration_path.parent / frame["file"]
        with Image.open(path).convert("RGBA") as image:
            if image.size != canvas:
                fail(f"{path.name} canvas is {image.size}, expected {canvas}")
            alpha = image.getchannel("A")
            bbox = alpha.getbbox()
            if not bbox:
                fail(f"{path.name} has no opaque actor pixels")
            left, top, right, bottom = bbox
            if abs(bottom - expected_anchor_y) > 1:
                fail(f"{path.name} lower contact {bottom}px drifts from anchor {expected_anchor_y}px")
            if left <= 0 or right >= canvas[0] or top <= 0:
                fail(f"{path.name} is cropped against its frame edge")
            visible_heights.append(bottom - top)

    minimum, maximum = min(visible_heights), max(visible_heights)
    if maximum - minimum > round(maximum * 0.08):
        fail(f"visible actor height drifts from {minimum}px to {maximum}px; regenerate or re-pad, never blur")
    print(
        f"Talking-head calibration QA passed: {len(visible_heights)} frames, "
        f"shared lower anchor {expected_anchor_y}px, visible-height range {minimum}-{maximum}px."
    )


if __name__ == "__main__":
    main()
