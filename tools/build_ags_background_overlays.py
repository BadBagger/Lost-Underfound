from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
AGS_DIR = ROOT / "ags"


COLORS = {
    "walkable": (61, 111, 196, 72),
    "hotspot": (244, 199, 88, 92),
    "exit": (103, 224, 185, 100),
    "standing": (239, 98, 98, 220),
    "walkbehind": (158, 113, 219, 92),
    "baseline": (158, 113, 219, 255),
}


def load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def rect_xyxy(rect: list[int | float] | dict[str, int | float]) -> tuple[int, int, int, int]:
    if isinstance(rect, dict):
        x = rect["x"]
        y = rect["y"]
        w = rect["width"]
        h = rect["height"]
    else:
        x, y, w, h = rect
    return (round(x), round(y), round(x + w), round(y + h))


def draw_label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.ImageFont) -> None:
    x, y = xy
    bbox = draw.textbbox((x, y), text, font=font)
    pad = 3
    draw.rectangle(
        (bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad),
        fill=(18, 12, 9, 210),
    )
    draw.text((x, y), text, fill=(255, 237, 186, 255), font=font)


def draw_screen_overlay(screen: dict, background_path: Path, out_path: Path) -> None:
    with Image.open(background_path) as img:
        base = img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_font(15)

    walkable = screen.get("walkable") or screen.get("walkableArea")
    if walkable:
        pts = [tuple(point) for point in walkable]
        draw.polygon(pts, fill=COLORS["walkable"], outline=(61, 111, 196, 210))
        draw_label(draw, pts[0], "walkable", font)

    for item in screen.get("walkbehinds", []) + screen.get("walkBehinds", []):
        box = rect_xyxy(item["rect"])
        draw.rectangle(box, fill=COLORS["walkbehind"], outline=(158, 113, 219, 230), width=2)
        y = round(item.get("baseline_y", item.get("baseline")))
        draw.line((box[0], y, box[2], y), fill=COLORS["baseline"], width=3)
        draw_label(draw, (box[0] + 4, max(0, box[1] - 20)), f"{item['id']} baseline", font)

    for hotspot in screen.get("hotspots", []):
        box = rect_xyxy(hotspot["rect"])
        draw.rectangle(box, fill=COLORS["hotspot"], outline=(244, 199, 88, 230), width=2)
        draw_label(draw, (box[0] + 4, box[1] + 4), hotspot["id"], font)

    for exit_item in screen.get("exits", []):
        box = rect_xyxy(exit_item.get("rect") or exit_item.get("exitHotspot"))
        draw.rectangle(box, fill=COLORS["exit"], outline=(103, 224, 185, 230), width=2)
        destination = exit_item.get("to") or exit_item.get("destinationScreenId")
        draw_label(draw, (box[0] + 4, box[1] + 4), f"exit->{destination}", font)

    standing_positions = screen.get("standing_positions") or screen.get("standingPositions") or {}
    for name, point in standing_positions.items():
        if isinstance(point, dict):
            x, y = round(point["x"]), round(point["y"])
        else:
            x, y = round(point[0]), round(point[1])
        draw.line((x - 14, y, x + 14, y), fill=COLORS["standing"], width=3)
        draw.line((x, y - 14, x, y + 14), fill=COLORS["standing"], width=3)
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=COLORS["standing"])
        draw_label(draw, (x + 8, y - 18), name, font)

    composed = Image.alpha_composite(base, overlay).convert("RGB")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    composed.save(out_path)


def make_contact(room_dir: Path, paths: list[Path]) -> None:
    if not paths:
        return
    font = load_font(20)
    thumb_w, thumb_h = 426, 240
    pad = 18
    label_h = 34
    width = (thumb_w + pad) * 3 + pad
    rows = (len(paths) + 2) // 3
    height = rows * (thumb_h + label_h + pad) + pad
    sheet = Image.new("RGB", (width, height), "#201712")
    draw = ImageDraw.Draw(sheet)

    for index, path in enumerate(paths):
        with Image.open(path) as img:
            thumb = img.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        col = index % 3
        row = index // 3
        x = pad + col * (thumb_w + pad)
        y = pad + row * (thumb_h + label_h + pad)
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y, x + thumb_w - 1, y + thumb_h - 1), outline="#8b6b42", width=2)
        draw.text((x, y + thumb_h + 6), path.stem, fill="#f2dfba", font=font)

    out_dir = room_dir / "background_overlays"
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet.save(out_dir / "contact.png")


def main() -> None:
    all_paths: list[Path] = []
    for geometry_path in sorted(AGS_DIR.glob("room*/geometry.json")):
        room_dir = geometry_path.parent
        geometry = json.loads(geometry_path.read_text(encoding="utf-8"))
        room_paths: list[Path] = []
        for screen in geometry["screens"]:
            bg_path = room_dir / "background" / f"{screen['id']}.png"
            if not bg_path.exists():
                continue
            out_path = room_dir / "background_overlays" / f"{screen['id']}.png"
            draw_screen_overlay(screen, bg_path, out_path)
            room_paths.append(out_path)
            all_paths.append(out_path)
        make_contact(room_dir, room_paths)

    make_contact(AGS_DIR, all_paths)
    print(f"Built {len(all_paths)} background geometry overlays.")


if __name__ == "__main__":
    main()
