"""Render the authoritative AGS Room 1 geometry review plate."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "ags" / "room1" / "geometry.json"
OUT = ROOT / "ags" / "room1" / "room1-greybox.png"
PAINT_GUIDE_OUT = ROOT / "ags" / "room1" / "room1-paint-guide.png"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    return ImageFont.truetype(path, size)


def label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, color: str = "#f5f7fa") -> None:
    draw.text((xy[0] + 1, xy[1] + 1), text, font=font(15, True), fill="#151b22")
    draw.text(xy, text, font=font(15, True), fill=color)


def main() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    width = spec["resolution"]["width"]
    height = spec["resolution"]["height"]
    image = Image.new("RGB", (width, height), "#41474f")
    draw = ImageDraw.Draw(image)

    # Room shell and horizon. Greybox contains no final scene art.
    draw.rectangle((0, 0, width, 505), fill="#60666c")
    draw.rectangle((0, 505, width, height), fill="#30363d")
    draw.line((0, 505, width, 505), fill="#9aa3ad", width=3)
    for y in range(545, height, 45):
        draw.line((0, y, width, y), fill="#434b54", width=1)

    walk = [tuple(point) for point in spec["walkableArea"]]
    draw.polygon(walk, fill="#526b70", outline="#92d6d6", width=3)
    label(draw, (80, 526), "WALKABLE FLOOR")

    # Furniture is deliberately geometric: these are the painted-background footprints.
    desk = spec["walkBehinds"][0]
    rect = desk["rect"]
    draw.rectangle((rect["x"], rect["y"], rect["x"] + rect["width"], rect["y"] + rect["height"]), fill="#7a6260", outline="#f0c674", width=3)
    draw.line((rect["x"], desk["baseline"], rect["x"] + rect["width"], desk["baseline"]), fill="#ffcc66", width=4)
    label(draw, (rect["x"] + 12, rect["y"] + 12), "DESK (painted into background)")
    label(draw, (rect["x"] + 12, desk["baseline"] + 5), "walk-behind baseline 614", "#ffdc8b")

    gate = spec["walkBehinds"][1]
    rect = gate["rect"]
    draw.rounded_rectangle((rect["x"], rect["y"], rect["x"] + rect["width"], rect["y"] + rect["height"]), radius=20, fill="#50606b", outline="#f0c674", width=3)
    draw.line((rect["x"], gate["baseline"], rect["x"] + rect["width"], gate["baseline"]), fill="#ffcc66", width=4)
    label(draw, (rect["x"] + 18, rect["y"] + 16), "TOLL GATE")
    label(draw, (rect["x"] + 18, gate["baseline"] + 5), "walk-behind baseline 568", "#ffdc8b")

    colors = {"pip": "#8ee4df", "bramble": "#d0b0e8", "bottlecap": "#f2c879"}
    poses = spec["standingPositions"]
    for key, value in poses.items():
        color = colors["pip"] if key.startswith("pip") else colors["bramble"] if key.startswith("bramble") else colors["bottlecap"]
        x, y = value["x"], value["y"]
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=color, outline="#182028", width=2)
        draw.line((x, y, x, y - 45 if key.startswith("pip") else y - 32), fill=color, width=3)
        label(draw, (x + 12, y - 26), key.replace("-", " "), color)

    for hotspot in spec["hotspots"]:
        rect = hotspot["rect"]
        xy = (rect["x"], rect["y"], rect["x"] + rect["width"], rect["y"] + rect["height"])
        draw.rectangle(xy, outline="#f07f8f", width=3)
        label(draw, (rect["x"] + 4, rect["y"] + 4), hotspot["id"], "#ff9ca8")

    draw.rectangle((16, 14, 580, 95), fill="#20262c", outline="#92d6d6", width=2)
    draw.text((30, 26), "LOST & UNDERFOUND - ROOM 1 GEOMETRY", font=font(24, True), fill="#f5f7fa")
    draw.text((30, 60), "AGS greybox: coordinates and baselines are authoritative; art follows.", font=font(15), fill="#cbd5df")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT)
    print(OUT)

    # A deliberately unlabeled placement guide for the final background paint-over.
    # It captures only fixed geometry and must never ship as room art.
    guide = Image.new("RGB", (width, height), "#34363a")
    guide_draw = ImageDraw.Draw(guide)
    guide_draw.rectangle((0, 0, width, 505), fill="#5f5b53")
    guide_draw.rectangle((0, 505, width, height), fill="#6b5842")
    guide_draw.rectangle((0, 0, width, 150), fill="#2d2928")
    for hotspot in spec["hotspots"]:
        rect = hotspot["rect"]
        colors = {
            "couch-ceiling": "#2d2928",
            "cubby-wall": "#6e4933",
            "dust-clump": "#71686a",
            "popcorn-boulder": "#d7b361",
            "wall-note": "#e7cf83",
            "sign-in-log": "#caa66d",
            "service-bell": "#d2a745",
            "toll-gate": "#48616a",
            "cobweb-curtain": "#aeb3ad",
        }
        guide_draw.rectangle(
            (rect["x"], rect["y"], rect["x"] + rect["width"], rect["y"] + rect["height"]),
            fill=colors[hotspot["id"]],
        )
    guide_draw.rectangle(
        (desk["rect"]["x"], desk["rect"]["y"], desk["rect"]["x"] + desk["rect"]["width"], desk["rect"]["y"] + desk["rect"]["height"]),
        fill="#744a35",
    )
    guide.save(PAINT_GUIDE_OUT)
    print(PAINT_GUIDE_OUT)


if __name__ == "__main__":
    main()
