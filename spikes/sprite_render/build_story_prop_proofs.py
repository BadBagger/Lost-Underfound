#!/usr/bin/env python3
"""Build story prop proof sheets for Act 2/3 inventory and puzzle items.

These are clean, isolated timing/readability proofs. They are intentionally not
final painterly art; final art should replace them after the puzzle language is
approved.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "spikes" / "sprite_render" / "story_prop_proofs"
CANVAS = (256, 256)
FPS = 12
OUTLINE = (22, 12, 13, 255)
INK = (42, 31, 25, 255)
PAPER = (220, 190, 132, 255)
PAPER_DARK = (166, 124, 70, 255)
THREAD = (164, 36, 52, 255)
STEEL = (177, 186, 179, 255)


def ensure(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def transparent() -> Image.Image:
    return Image.new("RGBA", CANVAS, (0, 0, 0, 0))


def shadow(draw: ImageDraw.ImageDraw, cx: int, cy: int, rx: int, ry: int, alpha: int = 70) -> None:
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(0, 0, 0, alpha))


def outline_shape(img: Image.Image, width: int = 5) -> Image.Image:
    alpha = img.getchannel("A")
    dilated = alpha
    for _ in range(width):
        dilated = dilated.filter(ImageFilter.MaxFilter(3))
    layer = Image.new("RGBA", img.size, OUTLINE)
    layer.putalpha(Image.eval(dilated, lambda px: 255 if px > 8 else 0))
    return Image.alpha_composite(layer, img)


def draw_needle(angle: float = -34, threaded: bool = False) -> Image.Image:
    img = transparent()
    layer = transparent()
    d = ImageDraw.Draw(layer)
    d.line((72, 146, 188, 105), fill=STEEL, width=9)
    d.line((72, 146, 188, 105), fill=(242, 247, 235, 255), width=3)
    d.ellipse((176, 99, 198, 119), fill=(0, 0, 0, 0), outline=STEEL, width=7)
    d.polygon([(64, 149), (77, 136), (69, 157)], fill=(220, 225, 214, 255))
    if threaded:
        d.arc((128, 70, 230, 154), start=160, end=350, fill=THREAD, width=5)
        d.arc((116, 88, 218, 172), start=170, end=350, fill=(218, 95, 98, 255), width=3)
        d.ellipse((216, 136, 226, 146), fill=THREAD)
    layer = layer.rotate(angle, center=(128, 128), resample=Image.Resampling.BICUBIC)
    img.alpha_composite(layer)
    return outline_shape(img)


def draw_thread_spool() -> Image.Image:
    img = transparent()
    d = ImageDraw.Draw(img)
    shadow(d, 128, 192, 68, 12)
    d.rounded_rectangle((71, 72, 185, 92), radius=9, fill=(176, 132, 74, 255), outline=INK, width=4)
    d.rounded_rectangle((80, 92, 176, 170), radius=11, fill=(118, 64, 68, 255), outline=INK, width=4)
    for y in range(102, 164, 9):
        d.arc((77, y - 10, 179, y + 14), start=4, end=176, fill=(211, 74, 84, 255), width=3)
    d.rounded_rectangle((68, 168, 188, 190), radius=10, fill=(176, 132, 74, 255), outline=INK, width=4)
    d.line((176, 104, 216, 78), fill=THREAD, width=4)
    d.ellipse((211, 72, 222, 83), fill=THREAD)
    return outline_shape(img)


def draw_parcel(state: str = "inventory") -> Image.Image:
    img = transparent()
    d = ImageDraw.Draw(img)
    shadow(d, 128, 190, 78, 14)
    box = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    bd = ImageDraw.Draw(box)
    bd.rounded_rectangle((62, 80, 194, 174), radius=8, fill=PAPER, outline=INK, width=5)
    bd.line((62, 112, 194, 112), fill=PAPER_DARK, width=4)
    bd.line((106, 80, 106, 174), fill=PAPER_DARK, width=4)
    bd.rectangle((118, 122, 184, 154), fill=(238, 219, 164, 255), outline=INK, width=3)
    bd.text((124, 127), "ROUND", fill=INK)
    bd.text((124, 139), "ASSET", fill=INK)
    bd.line((70, 87, 94, 106), fill=(111, 68, 42, 255), width=3)
    bd.line((87, 88, 67, 107), fill=(111, 68, 42, 255), width=3)
    if state == "dropped":
        box = box.rotate(-18, center=(128, 128), resample=Image.Resampling.BICUBIC)
    elif state == "presented":
        glow = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.rounded_rectangle((54, 72, 202, 182), radius=14, outline=(255, 236, 160, 100), width=7)
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(3)))
    img.alpha_composite(box)
    return outline_shape(img)


def draw_ledger(opened: bool = False) -> Image.Image:
    img = transparent()
    d = ImageDraw.Draw(img)
    shadow(d, 128, 195, 76, 12)
    if not opened:
        d.rounded_rectangle((63, 64, 193, 180), radius=12, fill=(92, 56, 38, 255), outline=INK, width=5)
        d.rectangle((78, 78, 178, 101), fill=(152, 105, 65, 255))
        d.text((82, 82), "FOUNDER", fill=(45, 31, 24, 255))
        d.line((82, 128, 174, 128), fill=(218, 172, 102, 255), width=3)
        d.text((102, 140), "O.B.", fill=(218, 172, 102, 255))
    else:
        d.polygon([(40, 79), (126, 60), (126, 181), (45, 197)], fill=(222, 204, 158, 255), outline=INK)
        d.polygon([(126, 60), (216, 79), (211, 197), (126, 181)], fill=(232, 214, 166, 255), outline=INK)
        d.line((126, 62, 126, 181), fill=(95, 65, 45, 255), width=4)
        for y in (92, 114, 136, 158):
            d.line((58, y, 112, y - 8), fill=(103, 73, 50, 255), width=2)
            d.line((142, y - 8, 198, y), fill=(103, 73, 50, 255), width=2)
        d.text((78, 151), "O.B.", fill=INK)
    return outline_shape(img)


def draw_annotated_evidence() -> Image.Image:
    img = transparent()
    img.alpha_composite(draw_ledger(opened=True).resize((190, 190), Image.Resampling.LANCZOS), (30, 30))
    parcel = draw_parcel("presented").resize((120, 120), Image.Resampling.LANCZOS).rotate(-9, center=(60, 60), resample=Image.Resampling.BICUBIC)
    img.alpha_composite(parcel, (92, 98))
    d = ImageDraw.Draw(img)
    d.line((88, 90, 162, 160), fill=(190, 30, 44, 255), width=5)
    d.ellipse((154, 153, 171, 170), fill=(190, 30, 44, 255), outline=INK, width=2)
    d.text((104, 64), "MATCH", fill=(190, 30, 44, 255))
    return outline_shape(img)


def draw_marble(kind: str) -> Image.Image:
    img = transparent()
    d = ImageDraw.Draw(img)
    shadow(d, 128, 181, 50, 11)
    base = (88, 88, 168, 168)
    if kind == "galaxy":
        fill = (39, 36, 78, 255)
    elif kind == "radiator":
        fill = (138, 64, 48, 255)
    elif kind == "scratch":
        fill = (70, 96, 104, 255)
    elif kind == "flawless":
        fill = (72, 120, 180, 255)
    else:
        fill = (70, 116, 168, 255)
    d.ellipse(base, fill=fill, outline=INK, width=5)
    if kind == "galaxy":
        d.arc((93, 105, 165, 155), start=210, end=40, fill=(230, 210, 128, 255), width=4)
        for x, y in [(111, 111), (135, 121), (148, 143), (119, 151)]:
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(255, 242, 190, 255))
    elif kind == "radiator":
        d.rectangle((98, 74, 158, 90), fill=(180, 180, 170, 255), outline=INK, width=3)
        d.text((105, 76), "RAD", fill=INK)
        d.line((112, 102, 147, 153), fill=(210, 128, 76, 255), width=5)
    elif kind == "scratch":
        d.line((101, 124, 151, 113), fill=(238, 230, 202, 255), width=5)
        d.line((108, 135, 158, 123), fill=(238, 230, 202, 255), width=3)
    elif kind == "flawless":
        d.ellipse((103, 98, 127, 122), fill=(180, 220, 255, 180))
        d.arc((94, 91, 164, 165), start=15, end=300, fill=(112, 174, 220, 255), width=3)
    elif kind == "correct":
        d.polygon([(110, 116), (119, 120), (124, 112), (126, 123), (137, 123), (128, 130), (132, 141), (122, 135), (113, 142), (116, 131), (106, 126)], fill=(238, 225, 182, 255), outline=INK)
        d.arc((96, 96, 162, 160), start=250, end=55, fill=(122, 178, 226, 255), width=4)
    d.ellipse((102, 96, 126, 119), fill=(255, 255, 240, 90))
    return outline_shape(img)


def save_frames(name: str, frames: list[Image.Image], notes: list[str]) -> dict:
    out = OUT_ROOT / name
    ensure(out)
    for index, frame in enumerate(frames):
        frame.save(out / f"{name}_{index:03d}.png")
    save_contact(frames, out / f"{name}_contact.png")
    save_gif(frames, out / f"{name}_preview.gif")
    manifest = {
        "name": name,
        "frame_count": len(frames),
        "fps": FPS,
        "canvas": list(CANVAS),
        "role": "isolated prop readability/timing proof; final painterly art must replace or paint over this source",
        "notes": notes,
        "warnings": [],
    }
    (out / f"{name}_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest | {"path": str(out)}


def save_contact(frames: list[Image.Image], path: Path) -> None:
    cols = 5
    rows = math.ceil(len(frames) / cols)
    contact = Image.new("RGBA", (cols * CANVAS[0], rows * (CANVAS[1] + 24)), (128, 128, 128, 255))
    draw = ImageDraw.Draw(contact)
    for index, frame in enumerate(frames):
        x = (index % cols) * CANVAS[0]
        y = (index // cols) * (CANVAS[1] + 24) + 24
        contact.alpha_composite(frame, (x, y))
        draw.text((x + 8, y - 19), f"{index:02d}", fill=(255, 244, 215, 255))
    contact.save(path)


def save_gif(frames: list[Image.Image], path: Path) -> None:
    duration = round(1000 / FPS)
    flattened: list[Image.Image] = []
    for frame in frames:
        bg = Image.new("RGBA", frame.size, (128, 128, 128, 255))
        bg.alpha_composite(frame)
        flattened.append(bg.convert("P", palette=Image.Palette.ADAPTIVE))
    flattened[0].save(path, save_all=True, append_images=flattened[1:], duration=duration, loop=0, disposal=2)


def make_item_states() -> dict:
    frames = [
        draw_needle(),
        draw_thread_spool(),
        draw_needle(threaded=True),
        draw_parcel("inventory"),
        draw_parcel("dropped"),
        draw_parcel("presented"),
        draw_ledger(False),
        draw_ledger(True),
        draw_annotated_evidence(),
    ]
    notes = [
        "needle inventory/held",
        "thread inventory",
        "threaded-needle combine result",
        "intake parcel inventory",
        "intake parcel dropped floor state",
        "intake parcel presented to Toggle/Bramble",
        "founder's ledger closed inventory",
        "founder's ledger readable/open",
        "annotated evidence combined item",
    ]
    return save_frames("item_state_sheet", frames, notes)


def make_parcel_bounce() -> dict:
    frames: list[Image.Image] = []
    notes: list[str] = []
    keys = [
        (-36, 0, 32, "falling"),
        (-24, 0, 18, "falling"),
        (-10, 0, 5, "pre-impact"),
        (0, 1, 0, "squash impact"),
        (12, 0, -7, "bounce up"),
        (22, 0, 2, "settle rotate"),
        (18, 0, 0, "settled"),
        (18, 0, 0, "hold"),
    ]
    for angle, squash, yoff, note in keys:
        frame = transparent()
        parcel = draw_parcel("dropped")
        if squash:
            parcel = parcel.resize((256, 228), Image.Resampling.BICUBIC)
            temp = transparent()
            temp.alpha_composite(parcel, (0, 20))
            parcel = temp
        parcel = parcel.rotate(angle, center=(128, 128), resample=Image.Resampling.BICUBIC)
        frame.alpha_composite(parcel, (0, yoff))
        frames.append(frame)
        notes.append(note)
    return save_frames("parcel_drop_bounce", frames, notes)


def make_marble_candidates() -> dict:
    kinds = ["galaxy", "radiator", "scratch", "flawless", "correct"]
    frames = [draw_marble(kind) for kind in kinds]
    notes = [
        "wrong: galaxy marble",
        "wrong: radiator-tagged marble",
        "wrong: scratch decoy, not star nick",
        "wrong: flawless marble",
        "correct: lopsided star nick",
    ]
    return save_frames("marble_candidates", frames, notes)


def main() -> None:
    ensure(OUT_ROOT)
    results = [make_item_states(), make_parcel_bounce(), make_marble_candidates()]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
