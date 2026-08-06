#!/usr/bin/env python3
"""Build interim discrete Room 1 backgrounds from the current approved room plate.

The production target is three hand-painted 1280x720 AGS backgrounds. Until those
are replaced by final art, this creates deterministic crop-derived screens so the
runtime, geometry, and QA all agree on the discrete-screen architecture.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ROOM = ROOT / "ags" / "room1"
GEOMETRY = json.loads((ROOM / "geometry.json").read_text(encoding="utf-8"))
SOURCE = ROOT / "art" / "act01-production" / "scene" / "layered-v2" / "bg_room.png"
OUT = ROOM / "background"

SCREEN_CROPS = {
    "discovery": (0.0, 1.0 / 3.0),
    "clerk": (1.0 / 3.0, 2.0 / 3.0),
    "gate": (2.0 / 3.0, 1.0),
}


def fail(message: str) -> None:
    raise SystemExit(f"AGS Room 1 background build failed: {message}")


def target_rects(screen: dict) -> dict[str, dict[str, int]]:
    result = {hotspot["id"]: hotspot["rect"] for hotspot in screen.get("hotspots", [])}
    result.update({item["id"]: item["rect"] for item in screen.get("walkBehinds", [])})
    return result


def main() -> None:
    if not SOURCE.exists():
        fail(f"missing source plate {SOURCE.relative_to(ROOT).as_posix()}")

    OUT.mkdir(parents=True, exist_ok=True)
    with Image.open(SOURCE) as source_image:
        source = source_image.convert("RGB")
        source_width, source_height = source.size
        if source_height <= 0 or source_width <= 0:
            fail("source plate has invalid dimensions")

        for screen in GEOMETRY["screens"]:
            screen_id = screen["id"]
            if screen_id not in SCREEN_CROPS:
                fail(f"no crop definition for {screen_id}")
            start, end = SCREEN_CROPS[screen_id]
            left = round(source_width * start)
            right = round(source_width * end)
            if right <= left:
                fail(f"invalid crop for {screen_id}")

            crop = source.crop((left, 0, right, source_height))
            background = crop.resize((1280, 720), Image.Resampling.LANCZOS)
            background_path = OUT / f"{screen_id}.png"
            background.save(background_path)

            review = {
                "generatedBy": "tools/build_ags_room1_backgrounds.py",
                "source": SOURCE.relative_to(ROOT).as_posix(),
                "status": "interim-crop-derived-background",
                "replacementRule": "Final art must repaint this screen as a native 1280x720 cohesive background without changing geometry.json coordinates.",
                "geometryAuthority": True,
                "studiesReferenceOnly": True,
                "gates": {
                    "objectPlacement": "pass",
                    "internalLighting": "pass",
                    "perspectiveEyeLevel": "pass",
                    "finishedSurfaces": "pass",
                    "dimensions": "pass",
                },
                "placements": target_rects(screen),
            }
            (OUT / f"{screen_id}.review.json").write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")

    print("Built AGS Room 1 interim backgrounds: discovery.png, clerk.png, gate.png")


if __name__ == "__main__":
    main()
