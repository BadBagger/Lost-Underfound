#!/usr/bin/env python3
"""Render AGS discrete-room geometry files into quick visual greyboxes."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]


COLORS = {
    "walkable": (68, 130, 98, 120),
    "hotspot": (245, 196, 83, 125),
    "walkBehind": (97, 145, 235, 145),
    "standing": (236, 102, 87, 230),
    "exit": (188, 105, 235, 155),
    "prop": (95, 213, 216, 185),
}


def poly(draw: ImageDraw.ImageDraw, points: list[list[int]], fill: tuple[int, int, int, int], outline: tuple[int, int, int, int]) -> None:
    draw.polygon([tuple(p) for p in points], fill=fill, outline=outline)


def rect_from_obj(obj: dict) -> tuple[int, int, int, int]:
    r = obj["rect"] if "rect" in obj else obj["exitHotspot"]
    return (r["x"], r["y"], r["x"] + r["width"], r["y"] + r["height"])


def render_geometry(path: Path) -> list[Path]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out_dir = path.parent / "greybox"
    out_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    width = data["nativeSize"]["width"]
    height = data["nativeSize"]["height"]
    for screen in data["screens"]:
        img = Image.new("RGBA", (width, height), (45, 42, 38, 255))
        draw = ImageDraw.Draw(img, "RGBA")
        # Rough room guide.
        draw.rectangle((0, 0, width - 1, height - 1), outline=(220, 210, 190, 255), width=3)
        draw.line((0, 512, width, 512), fill=(110, 100, 90, 255), width=2)
        if "walkableArea" in screen:
            poly(draw, screen["walkableArea"], COLORS["walkable"], (118, 230, 164, 255))
        for wb in screen.get("walkBehinds", []):
            box = rect_from_obj(wb)
            draw.rectangle(box, fill=COLORS["walkBehind"], outline=(150, 190, 255, 255), width=3)
            baseline = wb.get("baseline")
            if baseline is not None:
                draw.line((box[0], baseline, box[2], baseline), fill=(90, 170, 255, 255), width=4)
            draw.text((box[0] + 6, box[1] + 6), f"WB {wb['id']}", fill=(255, 255, 255, 255))
        for hs in screen.get("hotspots", []):
            box = rect_from_obj(hs)
            draw.rectangle(box, fill=COLORS["hotspot"], outline=(255, 230, 130, 255), width=2)
            draw.text((box[0] + 4, box[1] + 4), hs["id"], fill=(35, 30, 25, 255))
        for ex in screen.get("exits", []):
            box = rect_from_obj(ex)
            draw.rectangle(box, fill=COLORS["exit"], outline=(220, 170, 255, 255), width=3)
            draw.text((box[0] + 4, box[1] + 4), ex["id"], fill=(255, 255, 255, 255))
        for prop in screen.get("separateProps", []):
            x = prop["x"]
            y = prop["y"]
            draw.ellipse((x - 12, y - 12, x + 12, y + 12), fill=COLORS["prop"], outline=(180, 255, 255, 255), width=2)
            draw.text((x + 14, y - 8), prop["id"], fill=(210, 255, 255, 255))
        for name, pos in screen.get("standingPositions", {}).items():
            x = pos["x"]
            y = pos["y"]
            draw.line((x - 14, y, x + 14, y), fill=COLORS["standing"], width=3)
            draw.line((x, y - 14, x, y + 14), fill=COLORS["standing"], width=3)
            draw.text((x + 16, y - 18), name, fill=(255, 210, 205, 255))
        draw.text((18, 18), f"Act {data['act']} - {screen['id']}", fill=(255, 244, 220, 255))
        out = out_dir / f"{screen['id']}.png"
        img.convert("RGB").save(out)
        generated.append(out)
    return generated


def main() -> None:
    targets = [ROOT / "ags" / "room1" / "geometry.json", ROOT / "ags" / "room2" / "geometry.json", ROOT / "ags" / "room3" / "geometry.json"]
    all_generated: list[str] = []
    for target in targets:
        if target.exists():
            all_generated.extend(str(p) for p in render_geometry(target))
    print(json.dumps({"greyboxes": all_generated}, indent=2))


if __name__ == "__main__":
    main()
