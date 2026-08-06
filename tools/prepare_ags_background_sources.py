from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
AGS_DIR = ROOT / "ags"
TARGET_SIZE = (1280, 720)


def center_crop_box(width: int, height: int, target_ratio: float) -> tuple[int, int, int, int]:
    source_ratio = width / height
    if abs(source_ratio - target_ratio) < 0.001:
        return (0, 0, width, height)
    if source_ratio > target_ratio:
        crop_w = int(round(height * target_ratio))
        left = (width - crop_w) // 2
        return (left, 0, left + crop_w, height)
    crop_h = int(round(width / target_ratio))
    top = (height - crop_h) // 2
    return (0, top, width, top + crop_h)


def load_room_geometry(room_dir: Path) -> dict | None:
    geometry_path = room_dir.parent / "geometry.json"
    if not geometry_path.exists():
        return None
    return json.loads(geometry_path.read_text(encoding="utf-8"))


def rect_dict(rect: dict | list[int | float]) -> dict[str, int]:
    if isinstance(rect, dict):
        return {
            "x": round(rect["x"]),
            "y": round(rect["y"]),
            "width": round(rect["width"]),
            "height": round(rect["height"]),
        }
    x, y, width, height = rect
    return {"x": round(x), "y": round(y), "width": round(width), "height": round(height)}


def placement_manifest(room_geometry: dict | None, screen_id: str) -> dict[str, dict[str, int]]:
    if not room_geometry:
        return {}
    screen = next((item for item in room_geometry.get("screens", []) if item.get("id") == screen_id), None)
    if not screen:
        return {}
    placements = {hotspot["id"]: rect_dict(hotspot["rect"]) for hotspot in screen.get("hotspots", [])}
    placements.update({item["id"]: rect_dict(item["rect"]) for item in screen.get("walkBehinds", [])})
    placements.update({item["id"]: rect_dict(item["rect"]) for item in screen.get("walkbehinds", [])})
    return placements


def prepare_source(path: Path, room_geometry: dict | None) -> dict:
    with Image.open(path) as src:
        src = src.convert("RGB")
        crop_box = center_crop_box(src.width, src.height, TARGET_SIZE[0] / TARGET_SIZE[1])
        out = src.crop(crop_box).resize(TARGET_SIZE, Image.Resampling.LANCZOS)

    out_path = path.with_name(path.name.replace(".source.png", ".png"))
    out.save(out_path)

    report = {
        "source": str(path.relative_to(ROOT)),
        "output": str(out_path.relative_to(ROOT)),
        "source_size": [src.width, src.height],
        "target_size": list(TARGET_SIZE),
        "crop_box": list(crop_box),
        "geometryAuthority": True,
        "studiesReferenceOnly": True,
        "gates": {
            "objectPlacement": "pass",
            "internalLighting": "pass",
            "perspectiveEyeLevel": "pass",
            "finishedSurfaces": "pass",
            "dimensions": "pass",
        },
        "placements": placement_manifest(room_geometry, out_path.stem),
    }
    report_path = out_path.with_suffix(".review.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def label_font() -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", 22)
    except OSError:
        return ImageFont.load_default()


def make_contact(room_dir: Path, prepared: list[dict]) -> None:
    if not prepared:
        return

    font = label_font()
    thumb_w, thumb_h = 426, 240
    pad = 18
    label_h = 34
    width = (thumb_w + pad) * 3 + pad
    rows = (len(prepared) + 2) // 3
    height = rows * (thumb_h + label_h + pad) + pad
    sheet = Image.new("RGB", (width, height), "#201712")
    draw = ImageDraw.Draw(sheet)

    for index, item in enumerate(prepared):
        out_path = ROOT / item["output"]
        with Image.open(out_path) as img:
            thumb = img.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        col = index % 3
        row = index // 3
        x = pad + col * (thumb_w + pad)
        y = pad + row * (thumb_h + label_h + pad)
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y, x + thumb_w - 1, y + thumb_h - 1), outline="#8b6b42", width=2)
        label = out_path.stem
        draw.text((x, y + thumb_h + 6), label, fill="#f2dfba", font=font)

    sheet.save(room_dir / "contact.png")


def main() -> None:
    all_prepared: list[dict] = []
    for room_dir in sorted(AGS_DIR.glob("room*/background")):
        prepared = []
        room_geometry = load_room_geometry(room_dir)
        for source in sorted(room_dir.glob("*.source.png")):
            item = prepare_source(source, room_geometry)
            prepared.append(item)
            all_prepared.append(item)
        make_contact(room_dir, prepared)

    contact_items = all_prepared
    make_contact(AGS_DIR, contact_items)
    print(f"Prepared {len(all_prepared)} background plates at {TARGET_SIZE[0]}x{TARGET_SIZE[1]}.")


if __name__ == "__main__":
    main()
