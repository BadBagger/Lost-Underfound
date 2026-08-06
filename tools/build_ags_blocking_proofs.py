"""Build AGS room blocking proof images from geometry and background plates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
AGS_DIR = ROOT / "ags"
OUT_DIR = AGS_DIR / "blocking_proofs"
SCREEN_SIZE = (1280, 720)

COLORS = {
    "walkable": (72, 132, 210, 68),
    "hotspot": (250, 206, 76, 92),
    "walkbehind": (62, 212, 166, 110),
    "exit": (64, 220, 160, 150),
    "entry": (110, 190, 255, 210),
    "standing": (255, 92, 92, 230),
    "line": (255, 244, 190, 235),
    "text_bg": (22, 14, 10, 210),
    "text": (255, 238, 205, 255),
}

ACTOR_HEIGHTS = {
    "pip": 194,
    "bramble": 160,
    "bottlecap": 116,
    "old-bottlecap": 116,
    "scuttle": 68,
    "grommet": 330,
    "chairman": 150,
    "toggle": 150,
}


def font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


SMALL = font(15)
LABEL = font(18)
TITLE = font(30)


def rect_tuple(rect: dict[str, Any]) -> tuple[int, int, int, int]:
    x = round(float(rect["x"]))
    y = round(float(rect["y"]))
    return x, y, x + round(float(rect["width"])), y + round(float(rect["height"]))


def point_tuple(point: dict[str, Any]) -> tuple[int, int]:
    return round(float(point["x"])), round(float(point["y"]))


def draw_label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fill: tuple[int, int, int, int] | None = None) -> None:
    x, y = xy
    bbox = draw.textbbox((x, y), text, font=SMALL)
    pad = 3
    draw.rectangle((bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad), fill=COLORS["text_bg"])
    draw.text((x, y), text, font=SMALL, fill=fill or COLORS["text"])


def actor_from_standing_id(name: str) -> str:
    lower = name.lower()
    for actor in ACTOR_HEIGHTS:
        if actor in lower:
            return "old-bottlecap" if actor == "bottlecap" else actor
    return "pip"


def draw_actor_ghost(draw: ImageDraw.ImageDraw, name: str, point: dict[str, Any]) -> None:
    x, y = point_tuple(point)
    actor = actor_from_standing_id(name)
    height = ACTOR_HEIGHTS[actor]
    width = max(34, round(height * (0.38 if actor == "pip" else 0.58)))
    if actor == "grommet":
        width = round(height * 0.52)
    if actor == "scuttle":
        width = round(height * 0.9)
    left, right = x - width // 2, x + width // 2
    top = y - height
    draw.ellipse((left, top, right, y), outline=(255, 92, 92, 255), width=3, fill=(255, 92, 92, 56))
    draw.line((x - 9, y, x + 9, y), fill=COLORS["standing"], width=3)
    draw.line((x, y - 9, x, y + 9), fill=COLORS["standing"], width=3)
    draw_label(draw, (left, max(4, top - 23)), name)


def render_screen(room_dir: Path, screen: dict[str, Any], out_path: Path) -> Path:
    background = room_dir / screen["background"]
    base = Image.open(background).convert("RGBA")
    overlay = Image.new("RGBA", SCREEN_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for poly in screen.get("walkablePolygons", []):
        points = [(round(float(p["x"])), round(float(p["y"]))) for p in poly["points"]]
        draw.polygon(points, fill=COLORS["walkable"], outline=(105, 178, 255, 210))
        draw_label(draw, points[0], "walkable")

    for item in screen.get("hotspots", []):
        box = rect_tuple(item["rect"])
        draw.rectangle(box, fill=COLORS["hotspot"], outline=(255, 219, 88, 245), width=3)
        draw_label(draw, (box[0] + 3, box[1] + 3), item["id"])

    for item in screen.get("walkBehinds", screen.get("walkbehinds", [])):
        box = rect_tuple(item["rect"])
        draw.rectangle(box, fill=COLORS["walkbehind"], outline=(95, 245, 200, 255), width=3)
        baseline = round(float(item.get("baselineY", box[3])))
        draw.line((box[0], baseline, box[2], baseline), fill=(95, 255, 210, 255), width=4)
        draw_label(draw, (box[0] + 3, box[1] + 3), f"{item['id']} baseline")

    for item in screen.get("exits", []):
        box = rect_tuple(item["exitHotspot"])
        draw.rectangle(box, fill=COLORS["exit"], outline=(80, 255, 190, 255), width=3)
        draw_label(draw, (max(4, box[0] - 130), box[1] + 3), item["id"])

    for name, point in screen.get("entryPoints", {}).items():
        x, y = point_tuple(point)
        draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=COLORS["entry"])
        draw_label(draw, (x + 12, y - 22), f"entry:{name}")

    for name, point in screen.get("standingPositions", {}).items():
        draw_actor_ghost(draw, name, point)

    composite = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(composite)
    draw.rectangle((0, 0, 520, 42), fill=(24, 15, 9, 210))
    draw.text((14, 7), f"{room_dir.name}/{screen['id']} blocking proof", font=TITLE, fill=COLORS["text"])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    composite.convert("RGB").save(out_path)
    return out_path


def build_contact(paths: list[Path]) -> Path:
    cols = 3
    thumb_w, thumb_h = 426, 240
    label_h = 42
    rows = (len(paths) + cols - 1) // cols
    contact = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (36, 22, 14))
    draw = ImageDraw.Draw(contact)
    for index, path in enumerate(paths):
        img = Image.open(path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (index % cols) * thumb_w
        y = (index // cols) * (thumb_h + label_h)
        contact.paste(img, (x, y))
        draw.text((x + 12, y + thumb_h + 8), path.stem, font=LABEL, fill=(255, 235, 200))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "contact.png"
    contact.save(out)
    return out


def main() -> None:
    paths: list[Path] = []
    for geometry_path in sorted(AGS_DIR.glob("room*/geometry.json")):
        room_dir = geometry_path.parent
        spec = json.loads(geometry_path.read_text(encoding="utf-8"))
        for screen in spec.get("screens", []):
            out = OUT_DIR / room_dir.name / f"{screen['id']}.png"
            paths.append(render_screen(room_dir, screen, out))
    contact = build_contact(paths)
    print(f"Built {len(paths)} AGS blocking proof(s). Contact sheet: {contact}")


if __name__ == "__main__":
    main()
