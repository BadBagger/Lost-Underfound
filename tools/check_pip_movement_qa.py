#!/usr/bin/env python3
"""Reject runtime movement settings that make Pip zip across point-and-click rooms."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "src" / "main.ts"

MIN_WALK_PX_PER_SECOND = 70
MAX_WALK_PX_PER_SECOND = 120
MIN_DURATION_MS = 900


def fail(message: str) -> None:
    raise SystemExit(f"Pip movement QA failed: {message}")


def const_number(source: str, name: str) -> float:
    match = re.search(rf"const\s+{re.escape(name)}\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*;", source)
    if not match:
        fail(f"missing named runtime constant {name}")
    return float(match.group(1))


def main() -> None:
    source = MAIN.read_text(encoding="utf-8")
    walk_match = re.search(r"const walkPipTo = .*?^};", source, re.DOTALL | re.MULTILINE)
    if not walk_match:
        fail("could not find walkPipTo timing function")
    walk_source = walk_match.group(0)
    speed = const_number(source, "PIP_WALK_PX_PER_SECOND")
    min_duration = const_number(source, "PIP_MIN_WALK_DURATION_MS")

    if not (MIN_WALK_PX_PER_SECOND <= speed <= MAX_WALK_PX_PER_SECOND):
        fail(
            f"PIP_WALK_PX_PER_SECOND={speed:g} is outside the allowed "
            f"{MIN_WALK_PX_PER_SECOND}-{MAX_WALK_PX_PER_SECOND} px/s range"
        )
    if min_duration < MIN_DURATION_MS:
        fail(f"PIP_MIN_WALK_DURATION_MS={min_duration:g} is too short for readable click-to-walk beats")

    if "distance / PIP_WALK_PX_PER_SECOND" not in walk_source:
        fail("walk duration must be derived from distance / PIP_WALK_PX_PER_SECOND")
    if re.search(r"Math\.min\(\s*[0-9]+", walk_source):
        fail("runtime still contains a numeric Math.min cap; long walks must not be capped into a zip")
    if "distance * 1.25" in walk_source or "Math.max(360" in walk_source or "1050" in walk_source:
        fail("old fast-walk timing is still present")

    far_walk_duration = (900 / speed) * 1000
    if far_walk_duration < 7000:
        fail("a 900px cross-room walk would still complete too quickly")

    print(
        "Pip movement QA passed: click-to-walk speed is distance-based, uncapped, "
        f"and tuned to {speed:g}px/s with a {min_duration:g}ms minimum beat."
    )


if __name__ == "__main__":
    main()
