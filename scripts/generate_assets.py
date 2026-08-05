from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art"


def ensure(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def frame(path: Path, size: tuple[int, int]) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def draw_pip(draw: ImageDraw.ImageDraw, anchor: tuple[int, int], top_y: int, pose: int) -> None:
    ax, ay = anchor
    bob = [0, 6, 10, 4, 0, 6, 10, 4, 0][pose]
    lean = [-8, -5, 0, 5, 8, 5, 0, -5, -8][pose]
    head_y = top_y + bob
    body_y = head_y + 58
    coat_y = body_y + 78
    left_step = [-30, -24, -8, 12, 28, 18, 4, -14, -30][pose]
    right_step = [28, 18, 4, -14, -30, -24, -8, 12, 28][pose]
    draw.ellipse((ax - 38 + lean, head_y, ax + 38 + lean, head_y + 58), fill="#f3b489", outline="#3b2417", width=4)
    draw.ellipse((ax - 15 + lean, head_y + 19, ax - 8 + lean, head_y + 26), fill="#221510")
    draw.ellipse((ax + 14 + lean, head_y + 19, ax + 21 + lean, head_y + 26), fill="#221510")
    draw.arc((ax - 13 + lean, head_y + 30, ax + 17 + lean, head_y + 48), 10, 165, fill="#6b2c24", width=3)
    draw.polygon(
        [(ax - 42 + lean, body_y), (ax + 42 + lean, body_y), (ax + 31, coat_y), (ax - 31, coat_y)],
        fill="#d54b35",
        outline="#3b2417",
    )
    draw.line((ax - 32 + lean, body_y + 22, ax - 56, body_y + 70 - bob // 2), fill="#3b2417", width=8)
    draw.line((ax + 32 + lean, body_y + 22, ax + 56, body_y + 58 + bob // 2), fill="#3b2417", width=8)
    draw.line((ax - 16, coat_y, ax + left_step, ay), fill="#263a54", width=10)
    draw.line((ax + 16, coat_y, ax + right_step, ay), fill="#263a54", width=10)
    draw.ellipse((ax + left_step - 16, ay - 7, ax + left_step + 18, ay + 5), fill="#22252a")
    draw.ellipse((ax + right_step - 16, ay - 7, ax + right_step + 18, ay + 5), fill="#22252a")


def write_pip() -> None:
    sheet = ART / "pip-walk"
    ensure(sheet)
    roles = [
        "left-contact",
        "left-recoil-down",
        "left-passing",
        "left-high-point",
        "right-contact",
        "right-recoil-down",
        "right-passing",
        "right-high-point",
        "loop-safe-return",
    ]
    frames = []
    for i, role in enumerate(roles):
        img, draw = frame(sheet / f"pip_walk_{i+1:02}.png", (320, 360))
        draw_pip(draw, (160, 300), 80, i)
        img.save(sheet / f"pip_walk_{i+1:02}.png")
        entry = {"file": f"pip_walk_{i+1:02}.png", "anchor": [160, 300], "role": role}
        if i == 0:
            entry["canonical"] = True
            entry["scale_reference"] = [160, 80]
        frames.append(entry)
    save_json(sheet / "registration.json", {
        "sheet": "pip-walk",
        "actor_type": "walk-plane",
        "canvas": {"width": 320, "height": 360},
        "anchor_tolerance_px": 1,
        "frames": frames,
    })


def draw_bottlecap(draw: ImageDraw.ImageDraw, anchor: tuple[int, int], top_y: int, tilt: int) -> None:
    ax, ay = anchor
    x = ax + tilt
    draw.ellipse((x - 62, top_y + 38, x + 62, ay + 14), fill="#9a6333", outline="#382211", width=5)
    draw.ellipse((x - 49, top_y + 51, x + 49, ay - 3), outline="#f2c879", width=6)
    draw.rectangle((x - 22, top_y + 88, x + 22, top_y + 97), fill="#4a2a17")
    draw.line((x - 22, top_y + 83, x - 6, top_y + 78), fill="#22130a", width=5)
    draw.line((x + 22, top_y + 83, x + 6, top_y + 78), fill="#22130a", width=5)
    draw.ellipse((x - 25, top_y + 73, x - 15, top_y + 83), fill="#17100c")
    draw.ellipse((x + 15, top_y + 73, x + 25, top_y + 83), fill="#17100c")
    draw.line((30, ay, 290, ay), fill="#74451f", width=8)


def write_bottlecap() -> None:
    sheet = ART / "old-bottlecap-idle"
    ensure(sheet)
    frames = []
    for i, tilt in enumerate([0, -3, 0, 3]):
        img, draw = frame(sheet / f"old_bottlecap_idle_{i+1:02}.png", (320, 260))
        draw_bottlecap(draw, (160, 210), 78, tilt)
        img.save(sheet / f"old_bottlecap_idle_{i+1:02}.png")
        entry = {"file": f"old_bottlecap_idle_{i+1:02}.png", "anchor": [160, 210], "role": "fixed-contact-idle"}
        if i == 0:
            entry["canonical"] = True
            entry["scale_reference"] = [160, 78]
        frames.append(entry)
    save_json(sheet / "registration.json", {
        "sheet": "old-bottlecap-idle",
        "actor_type": "furniture-anchored",
        "canvas": {"width": 320, "height": 260},
        "anchor_tolerance_px": 1,
        "frames": frames,
    })


def draw_bramble(draw: ImageDraw.ImageDraw, anchor: tuple[int, int], top_y: int, stamp: int) -> None:
    ax, ay = anchor
    draw.ellipse((ax - 72, top_y + 34, ax + 72, ay + 18), fill="#b9b2a4", outline="#50483e", width=4)
    draw.ellipse((ax - 48, top_y + 8, ax + 48, top_y + 94), fill="#cec9bb", outline="#50483e", width=4)
    draw.ellipse((ax - 58, top_y, ax - 20, top_y + 38), fill="#d8d3c6")
    draw.ellipse((ax + 20, top_y, ax + 58, top_y + 38), fill="#d8d3c6")
    draw.ellipse((ax - 20, top_y + 43, ax - 10, top_y + 53), fill="#211b16")
    draw.ellipse((ax + 10, top_y + 43, ax + 20, top_y + 53), fill="#211b16")
    draw.rectangle((42, ay - 12, 278, ay + 30), fill="#8c6545", outline="#50391f", width=4)
    draw.rectangle((ax + 42, ay - 42 - stamp, ax + 64, ay - 13 - stamp), fill="#7b2e2d")
    draw.line((ax + 20, top_y + 88, ax + 54, ay - 20 - stamp), fill="#6f675d", width=8)


def write_bramble() -> None:
    sheet = ART / "bramble-idle"
    ensure(sheet)
    frames = []
    for i, stamp in enumerate([0, 5, 18, 5]):
        img, draw = frame(sheet / f"bramble_idle_{i+1:02}.png", (320, 260))
        draw_bramble(draw, (160, 205), 18, stamp)
        img.save(sheet / f"bramble_idle_{i+1:02}.png")
        entry = {"file": f"bramble_idle_{i+1:02}.png", "anchor": [160, 205], "role": "desk-work-idle"}
        if i == 0:
            entry["canonical"] = True
            entry["scale_reference"] = [160, 18]
        frames.append(entry)
    save_json(sheet / "registration.json", {
        "sheet": "bramble-idle",
        "actor_type": "furniture-anchored",
        "canvas": {"width": 320, "height": 260},
        "anchor_tolerance_px": 1,
        "frames": frames,
    })


def write_small_actor(name: str, world_units: float, height_px: int, size: tuple[int, int], anchor: tuple[int, int]) -> None:
    sheet = ART / name
    ensure(sheet)
    top_y = anchor[1] - height_px
    frames = []
    for i, dx in enumerate([0, 4, 0, -4]):
        img, draw = frame(sheet / f"{name}_{i+1:02}.png", size)
        ax, ay = anchor
        draw.ellipse((ax - height_px // 4 + dx, top_y, ax + height_px // 4 + dx, ay), fill="#5aa37a", outline="#173421", width=3)
        draw.ellipse((ax - 8 + dx, top_y + height_px // 3, ax - 2 + dx, top_y + height_px // 3 + 6), fill="#10100d")
        draw.ellipse((ax + 2 + dx, top_y + height_px // 3, ax + 8 + dx, top_y + height_px // 3 + 6), fill="#10100d")
        draw.line((ax - 26 + dx, ay, ax + 26 + dx, ay), fill="#263b2c", width=4)
        img.save(sheet / f"{name}_{i+1:02}.png")
        entry = {"file": f"{name}_{i+1:02}.png", "anchor": list(anchor), "role": "provisional-scale-idle"}
        if i == 0:
            entry["canonical"] = True
            entry["scale_reference"] = [anchor[0], top_y]
        frames.append(entry)
    actor_type = "walk-plane" if "walk" in name else "furniture-anchored"
    save_json(sheet / "registration.json", {
        "sheet": name,
        "actor_type": actor_type,
        "canvas": {"width": size[0], "height": size[1]},
        "anchor_tolerance_px": 1,
        "frames": frames,
        "provisional": True,
        "world_height_units": world_units,
    })


def write_qa_fixtures() -> None:
    ok = ART / "qa-placeholder"
    bad = ART / "qa-broken"
    ensure(ok)
    ensure(bad)
    for target, bad_second in [(ok, False), (bad, True)]:
        frames = []
        for i in range(2):
            size = (120, 120) if not (bad_second and i == 1) else (130, 120)
            img, draw = frame(target / f"fixture_{i+1:02}.png", size)
            draw.rectangle((48, 30, 72, 96), fill="#5588c8")
            img.save(target / f"fixture_{i+1:02}.png")
            anchor = [60, 96] if not (bad_second and i == 1) else [75, 96]
            entry = {"file": f"fixture_{i+1:02}.png", "anchor": anchor, "role": "fixture"}
            if i == 0:
                entry["canonical"] = True
                entry["scale_reference"] = [60, 30]
            frames.append(entry)
        save_json(target / "registration.json", {
            "sheet": target.name,
            "actor_type": "walk-plane",
            "canvas": {"width": 120, "height": 120},
            "anchor_tolerance_px": 1,
            "frames": frames,
        })


def write_cast_scale() -> None:
    save_json(ART / "cast_scale.json", {
        "world_unit": "Pip's shrunk-down standing height = 1.0",
        "tolerance_pct": 8,
        "actors": [
            {"name": "pip", "registration": "pip-walk/registration.json", "world_height_units": 1.0},
            {"name": "bramble", "registration": "bramble-idle/registration.json", "world_height_units": 0.85},
            {"name": "grommet", "registration": "grommet-idle/registration.json", "world_height_units": 2.4},
            {"name": "scuttle", "registration": "scuttle-walk/registration.json", "world_height_units": 0.35},
            {"name": "old-bottlecap", "registration": "old-bottlecap-idle/registration.json", "world_height_units": 0.6},
        ],
    })


def main() -> None:
    write_qa_fixtures()
    write_pip()
    write_bottlecap()
    write_bramble()
    write_small_actor("scuttle-walk", 0.35, 77, (180, 160), (90, 120))
    write_small_actor("grommet-idle", 2.4, 528, (460, 700), (230, 620))
    write_cast_scale()


if __name__ == "__main__":
    main()
