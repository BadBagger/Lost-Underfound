"""Render the three authoritative discrete-screen Room 1 greyboxes."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "ags" / "room1" / "geometry.json"
OUT_DIR = ROOT / "ags" / "room1" / "greybox"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    return ImageFont.truetype(path, size)


def label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, color: str = "#f5f7fa") -> None:
    draw.text((xy[0] + 1, xy[1] + 1), text, font=font(14, True), fill="#151b22")
    draw.text(xy, text, font=font(14, True), fill=color)


def main() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    size = tuple(spec["nativeSize"].values())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for screen in spec["screens"]:
        image = Image.new("RGB", size, "#41474f")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, size[0], 505), fill="#60666c")
        draw.rectangle((0, 505, size[0], size[1]), fill="#30363d")
        draw.polygon([tuple(point) for point in screen["walkableArea"]], fill="#526b70", outline="#92d6d6", width=3)
        label(draw, (52, 530), "WALKABLE FLOOR")

        for item in screen.get("walkBehinds", []):
            rect = item["rect"]
            draw.rectangle((rect["x"], rect["y"], rect["x"] + rect["width"], rect["y"] + rect["height"]), fill="#7a6260", outline="#f0c674", width=3)
            draw.line((rect["x"], item["baseline"], rect["x"] + rect["width"], item["baseline"]), fill="#ffcc66", width=4)
            label(draw, (rect["x"] + 8, rect["y"] + 8), item["id"].upper())

        for key, point in screen.get("standingPositions", {}).items():
            draw.ellipse((point["x"] - 7, point["y"] - 7, point["x"] + 7, point["y"] + 7), fill="#8ee4df", outline="#182028", width=2)
            label(draw, (point["x"] + 10, point["y"] - 24), key, "#8ee4df")

        for hotspot in screen.get("hotspots", []):
            rect = hotspot["rect"]
            draw.rectangle((rect["x"], rect["y"], rect["x"] + rect["width"], rect["y"] + rect["height"]), outline="#f07f8f", width=3)
            label(draw, (rect["x"] + 4, rect["y"] + 4), hotspot["id"], "#ff9ca8")

        for exit_data in screen.get("exits", []):
            rect = exit_data["exitHotspot"]
            draw.rectangle((rect["x"], rect["y"], rect["x"] + rect["width"], rect["y"] + rect["height"]), outline="#b7e17e", width=3)
            label(draw, (rect["x"] + 3, rect["y"] + 3), exit_data["id"], "#b7e17e")

        draw.rectangle((16, 14, 580, 76), fill="#20262c", outline="#92d6d6", width=2)
        draw.text((30, 25), f"ROOM 1 - {screen['title'].upper()}", font=font(22, True), fill="#f5f7fa")
        draw.text((30, 52), "AGS discrete-screen geometry: local coordinates are authoritative.", font=font(13), fill="#cbd5df")
        target = OUT_DIR / f"{screen['id']}.png"
        image.save(target)
        print(target)


if __name__ == "__main__":
    main()
