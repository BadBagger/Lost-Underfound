"""Composite admitted character exports onto AGS background plates for scale review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
AGS_DIR = ROOT / "ags"
ENGINE_DIR = ROOT / "art" / "engine-export"
OUT_DIR = AGS_DIR / "actor_scale_proofs"
SCREEN_SIZE = (1280, 720)

ACTOR_ENGINE = {
    "pip": ("pip", "idle"),
    "bramble": ("bramble", "idle"),
    "old-bottlecap": ("old-bottlecap", "idle"),
    "bottlecap": ("old-bottlecap", "idle"),
    "scuttle": ("scuttle", "dash"),
}

ACTOR_PROOF_SOURCE = {
    "bramble-talking-head": ROOT / "art" / "act01-production" / "characters" / "bramble" / "desk-clerk" / "bramble_desk_source_cut.png",
}

PLACEHOLDER_HEIGHTS = {
    "grommet": 330,
    "chairman": 150,
    "toggle": 150,
}

COLORS = {
    "text": (255, 238, 205, 255),
    "text_bg": (24, 15, 9, 220),
    "missing": (255, 72, 72, 230),
    "anchor": (110, 220, 255, 230),
}


def font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


SMALL = font(15)
LABEL = font(18)
TITLE = font(30)


def label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str) -> None:
    x, y = xy
    bbox = draw.textbbox((x, y), text, font=SMALL)
    pad = 3
    draw.rectangle((bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad), fill=COLORS["text_bg"])
    draw.text((x, y), text, font=SMALL, fill=COLORS["text"])


def actor_from_name(name: str) -> str | None:
    lower = name.lower()
    if lower.startswith("pip-") or lower == "pip":
        return "pip"
    if lower.startswith("bramble-") or lower == "bramble":
        return "bramble"
    if lower.startswith("old-bottlecap-") or lower.startswith("bottlecap-") or lower in {"old-bottlecap", "bottlecap"}:
        return "old-bottlecap"
    if lower.startswith("scuttle-") or lower == "scuttle":
        return "scuttle"
    if lower.startswith("grommet-") or lower == "grommet":
        return "grommet"
    if lower.startswith("chairman-") or lower.startswith("toggle-") or lower in {"chairman", "toggle"}:
        return "chairman"
    if "old-bottlecap" in lower or "bottlecap" in lower:
        return "old-bottlecap"
    for key in ("bramble", "scuttle", "grommet", "chairman", "toggle", "pip"):
        if key in lower:
            return key
    return "pip"


def load_actor_frame(actor: str, state: str) -> tuple[Image.Image, tuple[int, int]] | None:
    meta_path = ENGINE_DIR / actor / f"{actor}.engine.json"
    if not meta_path.is_file():
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    state_meta = meta["states"][state]
    strip_path = ROOT / state_meta["file"]
    cell_w, cell_h = state_meta["cell"]
    anchor_x, anchor_y = state_meta["runtime_anchor"]
    strip = Image.open(strip_path).convert("RGBA")
    frame = strip.crop((0, 0, cell_w, cell_h))
    return frame, (anchor_x, anchor_y)


def load_named_actor_source(name: str) -> tuple[Image.Image, tuple[int, int]] | None:
    path = ACTOR_PROOF_SOURCE.get(name)
    if path is None or not path.is_file():
        return None
    frame = Image.open(path).convert("RGBA")
    bbox = frame.getchannel("A").getbbox()
    if bbox is None:
        return None
    anchor = ((bbox[0] + bbox[2]) // 2, bbox[3])
    return frame, anchor


def alpha_bbox_height(frame: Image.Image) -> int:
    bbox = frame.getchannel("A").getbbox()
    if bbox is None:
        return frame.height
    return bbox[3] - bbox[1]


def scale_for_scene(frame: Image.Image, anchor: tuple[int, int], actor: str, name: str, spec: dict[str, Any]) -> tuple[Image.Image, tuple[int, int]]:
    reference = spec.get("actorReference", {})
    target_height = None
    if name == "bramble-talking-head":
        target_height = reference.get("brambleTalkingHeadHeight")
    elif actor == "pip":
        target_height = reference.get("pipHeight")
    elif actor == "old-bottlecap":
        target_height = reference.get("oldBottlecapHeight")
    elif actor == "scuttle":
        target_height = reference.get("scuttleHeight")

    if not target_height:
        return frame, anchor

    source_height = alpha_bbox_height(frame)
    if source_height <= 0:
        return frame, anchor
    scale = float(target_height) / float(source_height)
    if abs(scale - 1.0) < 0.01:
        return frame, anchor

    size = (max(1, round(frame.width * scale)), max(1, round(frame.height * scale)))
    scaled = frame.resize(size, Image.Resampling.LANCZOS)
    scaled_anchor = (round(anchor[0] * scale), round(anchor[1] * scale))
    return scaled, scaled_anchor


def draw_missing_actor(draw: ImageDraw.ImageDraw, name: str, point: dict[str, Any]) -> None:
    actor = actor_from_name(name) or "pip"
    x = round(float(point["x"]))
    y = round(float(point["y"]))
    height = PLACEHOLDER_HEIGHTS.get(actor, 194)
    width = max(42, round(height * 0.48))
    box = (x - width // 2, y - height, x + width // 2, y)
    draw.ellipse(box, outline=COLORS["missing"], width=4, fill=(255, 72, 72, 42))
    draw.line((x - 10, y, x + 10, y), fill=COLORS["anchor"], width=3)
    draw.line((x, y - 10, x, y + 10), fill=COLORS["anchor"], width=3)
    label(draw, (box[0], max(4, box[1] - 24)), f"{name}: no admitted export")


def bramble_desk_rect(screen: dict[str, Any], name: str) -> tuple[int, int, int, int] | None:
    if name != "bramble-talking-head":
        return None
    for item in screen.get("walkBehinds", screen.get("walkbehinds", [])):
        if item["id"] == "bramble-desk":
            rect = item["rect"]
            x = round(float(rect["x"]))
            y = round(float(rect["y"]))
            return (x, y, x + round(float(rect["width"])), y + round(float(rect["height"])))
    return None


def bramble_desk_occluder(screen: dict[str, Any], name: str, background: Image.Image) -> Image.Image | None:
    if name != "bramble-talking-head":
        return None
    for item in screen.get("walkBehinds", screen.get("walkbehinds", [])):
        if item["id"] != "bramble-desk":
            continue
        polygon = item.get("frontOccluderPolygon")
        if not polygon:
            rect = bramble_desk_rect(screen, name)
            if rect is None:
                return None
            mask = Image.new("L", background.size, 0)
            ImageDraw.Draw(mask).rectangle(rect, fill=255)
        else:
            points = [(round(float(x)), round(float(y))) for x, y in polygon]
            mask = Image.new("L", background.size, 0)
            ImageDraw.Draw(mask).polygon(points, fill=255)
        return Image.composite(background, Image.new("RGBA", background.size, (0, 0, 0, 0)), mask)
    return None


def paste_actor(
    canvas: Image.Image,
    background: Image.Image,
    draw: ImageDraw.ImageDraw,
    spec: dict[str, Any],
    screen: dict[str, Any],
    name: str,
    point: dict[str, Any],
) -> None:
    actor = actor_from_name(name)
    if actor is None or actor not in ACTOR_ENGINE:
        draw_missing_actor(draw, name, point)
        return

    engine_actor, state = ACTOR_ENGINE[actor]
    loaded = load_named_actor_source(name) or load_actor_frame(engine_actor, state)
    if loaded is None:
        draw_missing_actor(draw, name, point)
        return

    frame, anchor = loaded
    frame, anchor = scale_for_scene(frame, anchor, engine_actor, name, spec)
    x = round(float(point["x"]))
    y = round(float(point["y"]))
    paste_at = (x - anchor[0], y - anchor[1])
    canvas.alpha_composite(frame, paste_at)
    occluder_layer = bramble_desk_occluder(screen, name, background)
    if occluder_layer is not None:
        canvas.alpha_composite(occluder_layer)
    draw.line((x - 10, y, x + 10, y), fill=COLORS["anchor"], width=3)
    draw.line((x, y - 10, x, y + 10), fill=COLORS["anchor"], width=3)
    label(draw, (max(4, paste_at[0]), max(4, paste_at[1] - 23)), f"{name}: {engine_actor}/{state}")


def render_screen(room_dir: Path, spec: dict[str, Any], screen: dict[str, Any], out_path: Path) -> Path:
    background = Image.open(room_dir / screen["background"]).convert("RGBA")
    base = background.copy()
    draw = ImageDraw.Draw(base)

    for name, point in screen.get("standingPositions", {}).items():
        paste_actor(base, background, draw, spec, screen, name, point)

    draw.rectangle((0, 0, 640, 42), fill=COLORS["text_bg"])
    draw.text((14, 7), f"{room_dir.name}/{screen['id']} actor-scale proof", font=TITLE, fill=COLORS["text"])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(out_path)
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
    outputs: list[Path] = []
    for geometry_path in sorted(AGS_DIR.glob("room*/geometry.json")):
        room_dir = geometry_path.parent
        spec = json.loads(geometry_path.read_text(encoding="utf-8"))
        for screen in spec.get("screens", []):
            outputs.append(render_screen(room_dir, spec, screen, OUT_DIR / room_dir.name / f"{screen['id']}.png"))
    contact = build_contact(outputs)
    print(f"Built {len(outputs)} AGS actor-scale proof(s). Contact sheet: {contact}")


if __name__ == "__main__":
    main()
