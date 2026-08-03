from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art"
OUT = ART / "act01-production"

PX_PER_UNIT = 220


def ensure(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def canvas(size: tuple[int, int], scale: int = 3) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (size[0] * scale, size[1] * scale), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def down(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    return img.resize(size, Image.Resampling.LANCZOS)


def line(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], fill: str, width: int, scale: int = 3) -> None:
    draw.line(tuple(v * scale for v in xy), fill=fill, width=width * scale)


def ellipse(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str | None = None, width: int = 1, scale: int = 3) -> None:
    draw.ellipse(tuple(v * scale for v in box), fill=fill, outline=outline, width=width * scale)


def rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str | None = None, width: int = 1, scale: int = 3) -> None:
    draw.rectangle(tuple(v * scale for v in box), fill=fill, outline=outline, width=width * scale)


def polygon(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], fill: str, outline: str | None = None, scale: int = 3) -> None:
    pts = [(x * scale, y * scale) for x, y in points]
    draw.polygon(pts, fill=fill)
    if outline:
        draw.line(pts + [pts[0]], fill=outline, width=3 * scale, joint="curve")


def save_sheet_frame(sheet: Path, name: str, img: Image.Image, size: tuple[int, int]) -> None:
    ensure(sheet)
    down(img, size).save(sheet / name)


def write_registration(sheet: Path, sheet_name: str, actor_type: str, size: tuple[int, int], frames: list[dict]) -> None:
    save_json(
        sheet / "registration.json",
        {
            "sheet": sheet_name,
            "actor_type": actor_type,
            "canvas": {"width": size[0], "height": size[1]},
            "anchor_tolerance_px": 1,
            "frames": frames,
            "approval_state": "provisional-production-pass",
        },
    )


def draw_contact_sheet(sheet: Path, title: str, frames: list[dict], cols: int = 4) -> None:
    thumbs = []
    for frame in frames:
        with Image.open(sheet / frame["file"]) as img:
            thumbs.append((frame, img.convert("RGBA").resize((160, 180), Image.Resampling.LANCZOS)))
    rows = math.ceil(len(thumbs) / cols)
    out = Image.new("RGB", (cols * 210, rows * 230 + 48), "#f3e7cf")
    d = ImageDraw.Draw(out)
    d.text((16, 14), title, fill="#2b1b10")
    for idx, (frame, img) in enumerate(thumbs):
        x = (idx % cols) * 210 + 24
        y = (idx // cols) * 230 + 56
        out.paste(img, (x, y), img)
        d.text((x, y + 184), frame["role"], fill="#2b1b10")
    ensure(OUT / "qa")
    out.save(OUT / "qa" / f"{title.lower().replace(' ', '-')}-contact-sheet.png")


def draw_loop_capture(sheet: Path, title: str, frames: list[dict], duration_ms: int) -> None:
    imgs = []
    for frame in frames:
        with Image.open(sheet / frame["file"]) as img:
            plate = Image.new("RGBA", (360, 360), "#f3e7cf")
            sprite = img.convert("RGBA")
            plate.alpha_composite(sprite, ((360 - sprite.width) // 2, (330 - sprite.height) // 2))
            imgs.append(plate.convert("P", palette=Image.Palette.ADAPTIVE))
    ensure(OUT / "qa")
    imgs[0].save(
        OUT / "qa" / f"{title.lower().replace(' ', '-')}-normal.gif",
        save_all=True,
        append_images=imgs[1:],
        duration=duration_ms,
        loop=0,
    )
    imgs[0].save(
        OUT / "qa" / f"{title.lower().replace(' ', '-')}-half-speed.gif",
        save_all=True,
        append_images=imgs[1:],
        duration=duration_ms * 2,
        loop=0,
    )


def draw_pip(draw: ImageDraw.ImageDraw, anchor: tuple[int, int], top_y: int, pose: str, scale: int = 3) -> None:
    ax, ay = anchor
    pose_data = {
        "idle-01": (0, 0, -8, 24, 0),
        "idle-02": (0, -2, -8, 24, 1),
        "walk-left-contact": (-8, 0, -30, 28, 0),
        "walk-left-recoil-down": (-5, 7, -24, 18, 1),
        "walk-left-passing": (0, 10, -8, 4, 2),
        "walk-left-high": (5, 4, 12, -14, 3),
        "walk-right-contact": (8, 0, 28, -30, 4),
        "walk-right-recoil-down": (5, 7, 18, -24, 5),
        "walk-right-passing": (0, 10, 4, -8, 6),
        "walk-right-high": (-5, 4, -14, 12, 7),
        "walk-return": (-8, 0, -30, 28, 8),
        "crouch-anticipate": (-10, 34, -16, 16, 0),
        "crouch-reach": (-24, 46, -18, 20, 0),
        "crouch-contact": (-30, 50, -18, 20, 0),
        "found-pop": (12, -8, -12, 28, 0),
        "relief": (6, -5, -10, 20, 0),
        "cheer": (0, -12, -12, 20, 0),
    }[pose]
    lean, bob, left_step, right_step, phase = pose_data
    head_y = top_y + bob
    body_y = head_y + 58
    coat_y = body_y + 78
    shadow_w = 76 - min(20, abs(bob))
    ellipse(draw, (ax - shadow_w // 2, ay - 2, ax + shadow_w // 2, ay + 9), "#00000044", scale=scale)
    line(draw, (ax - 16, coat_y - 2, ax + left_step, ay), "#263247", 10, scale)
    line(draw, (ax + 16, coat_y - 2, ax + right_step, ay), "#263247", 10, scale)
    ellipse(draw, (ax + left_step - 17, ay - 8, ax + left_step + 18, ay + 5), "#2a2724", scale=scale)
    ellipse(draw, (ax + right_step - 17, ay - 8, ax + right_step + 18, ay + 5), "#2a2724", scale=scale)
    polygon(draw, [(ax - 43 + lean, body_y), (ax + 43 + lean, body_y), (ax + 30, coat_y), (ax - 30, coat_y)], "#315462", "#2a2019", scale)
    polygon(draw, [(ax - 26 + lean, body_y + 10), (ax + 20 + lean, body_y + 10), (ax + 15, coat_y - 8), (ax - 14, coat_y - 6)], "#d7a14e", None, scale)
    arm_raise = pose in ("found-pop", "cheer", "relief")
    reach = pose in ("crouch-reach", "crouch-contact")
    if reach:
        line(draw, (ax + 28 + lean, body_y + 28, ax - 68, body_y + 95), "#e8aa80", 8, scale)
    elif arm_raise:
        line(draw, (ax + 31 + lean, body_y + 20, ax + 56, body_y - 28), "#e8aa80", 8, scale)
        line(draw, (ax - 31 + lean, body_y + 22, ax - 55, body_y - 10), "#e8aa80", 8, scale)
    else:
        line(draw, (ax - 32 + lean, body_y + 22, ax - 55, body_y + 66 - phase % 3), "#e8aa80", 8, scale)
        line(draw, (ax + 32 + lean, body_y + 22, ax + 55, body_y + 62 + phase % 3), "#e8aa80", 8, scale)
    ellipse(draw, (ax - 39 + lean, head_y, ax + 39 + lean, head_y + 58), "#efb488", "#2a2019", 4, scale)
    polygon(draw, [(ax - 42 + lean, head_y + 8), (ax - 10 + lean, head_y - 15), (ax + 34 + lean, head_y + 7), (ax + 5 + lean, head_y + 18)], "#6b3a1c", "#2a2019", scale)
    ellipse(draw, (ax - 17 + lean, head_y + 22, ax - 9 + lean, head_y + 30), "#17120f", scale=scale)
    ellipse(draw, (ax + 13 + lean, head_y + 22, ax + 21 + lean, head_y + 30), "#17120f", scale=scale)
    if pose in ("crouch-contact", "found-pop", "cheer"):
        draw.arc(tuple(v * scale for v in (ax - 12 + lean, head_y + 31, ax + 18 + lean, head_y + 50)), 10, 165, fill="#713127", width=3 * scale)
    else:
        line(draw, (ax - 10 + lean, head_y + 43, ax + 14 + lean, head_y + 43), "#713127", 3, scale)


def make_pip_sheets() -> None:
    size = (320, 360)
    base = OUT / "characters" / "pip"
    walk_roles = [
        ("pip_walk_01.png", "left-contact", "walk-left-contact"),
        ("pip_walk_02.png", "left-recoil-down", "walk-left-recoil-down"),
        ("pip_walk_03.png", "left-passing", "walk-left-passing"),
        ("pip_walk_04.png", "left-high-point", "walk-left-high"),
        ("pip_walk_05.png", "right-contact", "walk-right-contact"),
        ("pip_walk_06.png", "right-recoil-down", "walk-right-recoil-down"),
        ("pip_walk_07.png", "right-passing", "walk-right-passing"),
        ("pip_walk_08.png", "right-high-point", "walk-right-high"),
        ("pip_walk_09.png", "loop-safe-return", "walk-return"),
    ]
    for action, roles in {
        "walk": walk_roles,
        "idle": [("pip_idle_01.png", "alive-held-idle", "idle-01"), ("pip_idle_02.png", "breath-secondary-motion", "idle-02")],
        "dust-reach": [
            ("pip_dust_01.png", "anticipation-crouch", "crouch-anticipate"),
            ("pip_dust_02.png", "reach-arc", "crouch-reach"),
            ("pip_dust_03.png", "contact-hold", "crouch-contact"),
            ("pip_dust_04.png", "found-reaction", "found-pop"),
        ],
        "toll-paid": [("pip_toll_01.png", "relief-read", "relief"), ("pip_toll_02.png", "small-excitement", "cheer")],
    }.items():
        sheet = base / action
        frames = []
        for idx, (file, role, pose) in enumerate(roles):
            img, d = canvas(size)
            draw_pip(d, (160, 300), 80, pose)
            save_sheet_frame(sheet, file, img, size)
            entry = {"file": file, "anchor": [160, 300], "role": role}
            if idx == 0:
                entry["canonical"] = True
                entry["scale_reference"] = [160, 80]
            frames.append(entry)
        write_registration(sheet, f"pip-{action}", "walk-plane", size, frames)
        draw_contact_sheet(sheet, f"pip {action}", frames)
        if action in ("walk", "idle"):
            draw_loop_capture(sheet, f"pip {action}", frames, 120 if action == "walk" else 420)


def draw_bramble(draw: ImageDraw.ImageDraw, anchor: tuple[int, int], top_y: int, pose: str, scale: int = 3) -> None:
    ax, ay = anchor
    stamp = {"idle-01": 0, "idle-02": 8, "stamp-up": 26, "stamp-down": -2, "talk-01": 0, "talk-02": 4}[pose]
    mouth_open = pose == "talk-02"
    ellipse(draw, (ax - 78, top_y + 50, ax + 78, ay + 16), "#b9b0a5", "#4d453d", 4, scale)
    ellipse(draw, (ax - 56, top_y + 12, ax + 56, top_y + 112), "#d1cbc0", "#4d453d", 4, scale)
    ellipse(draw, (ax - 68, top_y, ax - 24, top_y + 44), "#d8d2c8", "#6f675e", 2, scale)
    ellipse(draw, (ax + 24, top_y, ax + 68, top_y + 44), "#d8d2c8", "#6f675e", 2, scale)
    ellipse(draw, (ax - 31, top_y + 50, ax - 3, top_y + 78), "#eee7d7", "#473e37", 3, scale)
    ellipse(draw, (ax + 3, top_y + 50, ax + 31, top_y + 78), "#eee7d7", "#473e37", 3, scale)
    ellipse(draw, (ax - 17, top_y + 60, ax - 9, top_y + 68), "#17120f", scale=scale)
    ellipse(draw, (ax + 9, top_y + 60, ax + 17, top_y + 68), "#17120f", scale=scale)
    if mouth_open:
        ellipse(draw, (ax - 9, top_y + 83, ax + 9, top_y + 96), "#5b2a2a", scale=scale)
    else:
        line(draw, (ax - 13, top_y + 88, ax + 13, top_y + 88), "#5b2a2a", 3, scale)
    polygon(draw, [(ax - 24, top_y + 99), (ax, top_y + 118), (ax + 24, top_y + 99), (ax + 16, top_y + 130), (ax - 16, top_y + 130)], "#8b3549", "#4d1d2a", scale)
    line(draw, (ax + 32, top_y + 105, ax + 62, ay - 20 - stamp), "#7a7067", 9, scale)
    rect(draw, (ax + 50, ay - 45 - stamp, ax + 75, ay - 14 - stamp), "#7b2e2d", "#3d1716", 2, scale)


def make_bramble_sheets() -> None:
    size = (320, 260)
    base = OUT / "characters" / "bramble"
    specs = {
        "idle": [("bramble_idle_01.png", "folder-shuffle-start", "idle-01"), ("bramble_idle_02.png", "stamp-preparation", "idle-02"), ("bramble_idle_03.png", "stamp-up-anticipation", "stamp-up"), ("bramble_idle_04.png", "stamp-impact-settle", "stamp-down")],
        "talk": [("bramble_talk_01.png", "talk-closed-mouth", "talk-01"), ("bramble_talk_02.png", "talk-open-mouth", "talk-02"), ("bramble_talk_03.png", "talk-settle", "talk-01")],
    }
    for action, roles in specs.items():
        sheet = base / action
        frames = []
        for idx, (file, role, pose) in enumerate(roles):
            img, d = canvas(size)
            draw_bramble(d, (160, 205), 18, pose)
            save_sheet_frame(sheet, file, img, size)
            entry = {"file": file, "anchor": [160, 205], "role": role}
            if idx == 0:
                entry["canonical"] = True
                entry["scale_reference"] = [160, 18]
            frames.append(entry)
        write_registration(sheet, f"bramble-{action}", "furniture-anchored", size, frames)
        draw_contact_sheet(sheet, f"bramble {action}", frames)
        draw_loop_capture(sheet, f"bramble {action}", frames, 260)


def draw_bottlecap(draw: ImageDraw.ImageDraw, anchor: tuple[int, int], top_y: int, pose: str, scale: int = 3) -> None:
    ax, ay = anchor
    tilt = {"idle-01": 0, "idle-02": -4, "idle-03": 0, "idle-04": 4, "refuse-left": -8, "refuse-right": 8, "take": 0, "inspect": 0, "approve": 2}[pose]
    yoff = -5 if pose == "approve" else 0
    for level, color in enumerate(["#7e4a28", "#4d4b45", "#8b5b2e", "#b08b45"]):
        y = top_y + 92 - level * 24 + yoff
        ellipse(draw, (ax - 66 + tilt, y, ax + 66 + tilt, y + 34), color, "#2f2117", 4, scale)
        rect(draw, (ax - 58 + tilt, y + 13, ax + 58 + tilt, y + 27), color, "#2f2117", 2, scale)
    line(draw, (ax - 36 + tilt, top_y + 83 + yoff, ax - 9 + tilt, top_y + 77 + yoff), "#25190f", 5, scale)
    line(draw, (ax + 36 + tilt, top_y + 83 + yoff, ax + 9 + tilt, top_y + 77 + yoff), "#25190f", 5, scale)
    ellipse(draw, (ax - 28 + tilt, top_y + 72 + yoff, ax - 16 + tilt, top_y + 84 + yoff), "#17120f", scale=scale)
    ellipse(draw, (ax + 16 + tilt, top_y + 72 + yoff, ax + 28 + tilt, top_y + 84 + yoff), "#17120f", scale=scale)
    line(draw, (ax - 20 + tilt, top_y + 103 + yoff, ax + 20 + tilt, top_y + 103 + yoff), "#25190f", 4, scale)
    if pose in ("take", "inspect", "approve"):
        bx = ax + (66 if pose == "take" else 20)
        by = top_y + (100 if pose == "take" else 58)
        line(draw, (ax + 52, top_y + 112, bx, by), "#5b351e", 5, scale)
        ellipse(draw, (bx - 13, by - 13, bx + 13, by + 13), "#69a19b", "#2f2117", 3, scale)


def make_bottlecap_sheets() -> None:
    size = (320, 260)
    base = OUT / "characters" / "old-bottlecap"
    specs = {
        "idle": [("old_bottlecap_idle_01.png", "heavy-rock-center", "idle-01"), ("old_bottlecap_idle_02.png", "heavy-rock-left", "idle-02"), ("old_bottlecap_idle_03.png", "weighted-return", "idle-03"), ("old_bottlecap_idle_04.png", "heavy-rock-right", "idle-04")],
        "toll-refused": [("old_bottlecap_refuse_01.png", "dismissive-left", "refuse-left"), ("old_bottlecap_refuse_02.png", "dismissive-right", "refuse-right"), ("old_bottlecap_refuse_03.png", "deadpan-settle", "idle-01")],
        "toll-paid": [("old_bottlecap_paid_01.png", "button-take-arc", "take"), ("old_bottlecap_paid_02.png", "inspect-held-beat", "inspect"), ("old_bottlecap_paid_03.png", "grudging-approval", "approve")],
    }
    for action, roles in specs.items():
        sheet = base / action
        frames = []
        for idx, (file, role, pose) in enumerate(roles):
            img, d = canvas(size)
            draw_bottlecap(d, (160, 210), 78, pose)
            save_sheet_frame(sheet, file, img, size)
            entry = {"file": file, "anchor": [160, 210], "role": role}
            if idx == 0:
                entry["canonical"] = True
                entry["scale_reference"] = [160, 78]
            frames.append(entry)
        write_registration(sheet, f"old-bottlecap-{action}", "furniture-anchored", size, frames)
        draw_contact_sheet(sheet, f"old bottlecap {action}", frames)
        if action == "idle":
            draw_loop_capture(sheet, f"old bottlecap {action}", frames, 360)


def draw_scuttle(draw: ImageDraw.ImageDraw, anchor: tuple[int, int], top_y: int, pose: str, scale: int = 3) -> None:
    ax, ay = anchor
    if pose == "smear":
        ellipse(draw, (ax - 92, top_y + 15, ax + 72, ay), "#2d3036aa", scale=scale)
        line(draw, (ax - 110, top_y + 43, ax + 92, top_y + 42), "#22252a", 8, scale)
        return
    squash = 8 if pose == "land" else 0
    ellipse(draw, (ax - 40, top_y + squash, ax + 40, ay), "#30343b", "#17191d", 4, scale)
    for off in [-22, 0, 22]:
        line(draw, (ax + off, ay - 24, ax + off - 18, ay - 3), "#17191d", 4, scale)
        line(draw, (ax + off, ay - 24, ax + off + 18, ay - 3), "#17191d", 4, scale)
    line(draw, (ax - 16, top_y + 4, ax - 27, top_y - 20), "#17191d", 3, scale)
    line(draw, (ax + 16, top_y + 4, ax + 27, top_y - 20), "#17191d", 3, scale)
    ellipse(draw, (ax - 23, top_y + 18, ax - 4, top_y + 39), "#eee7d7", "#17191d", 2, scale)
    ellipse(draw, (ax + 4, top_y + 18, ax + 23, top_y + 39), "#eee7d7", "#17191d", 2, scale)
    ellipse(draw, (ax - 13, top_y + 26, ax - 7, top_y + 33), "#17191d", scale=scale)
    ellipse(draw, (ax + 8, top_y + 26, ax + 14, top_y + 33), "#17191d", scale=scale)
    rect(draw, (ax - 38, top_y + 50, ax - 18, top_y + 74), "#8e653e", "#3c2717", 2, scale)


def make_scuttle_sheets() -> None:
    size = (180, 160)
    sheet = OUT / "characters" / "scuttle" / "dash"
    roles = [("scuttle_dash_01.png", "solid-pre-dash", "ready"), ("scuttle_dash_02.png", "single-smear-cel", "smear"), ("scuttle_dash_03.png", "solid-exit-pose", "land")]
    frames = []
    for idx, (file, role, pose) in enumerate(roles):
        img, d = canvas(size)
        draw_scuttle(d, (90, 120), 43, pose)
        save_sheet_frame(sheet, file, img, size)
        entry = {"file": file, "anchor": [90, 120], "role": role}
        if idx == 0:
            entry["canonical"] = True
            entry["scale_reference"] = [90, 43]
        frames.append(entry)
    write_registration(sheet, "scuttle-dash", "walk-plane", size, frames)
    draw_contact_sheet(sheet, "scuttle dash", frames)


def make_props() -> None:
    size = (220, 180)
    dust = OUT / "props" / "dust-clump-reveal"
    frames = []
    for idx, (role, spread) in enumerate([("compact-hiding-button", 20), ("anticipation-puff-squash", 35), ("stretch-disperse", 52), ("button-revealed-settle", 70)]):
        img, d = canvas(size)
        ax, ay = 110, 125
        ellipse(d, (ax - spread, ay - 30, ax + spread, ay + 20), "#8d877e99", "#534c44", 2)
        if idx == 3:
            ellipse(d, (ax - 16, ay - 44, ax + 16, ay - 12), "#67a69f", "#2b2118", 3)
            ellipse(d, (ax - 5, ay - 33, ax + 5, ay - 23), "#2b2118")
        file = f"dust_reveal_{idx+1:02}.png"
        save_sheet_frame(dust, file, img, size)
        entry = {"file": file, "anchor": [110, 125], "role": role}
        if idx == 0:
            entry["canonical"] = True
            entry["scale_reference"] = [110, 70]
        frames.append(entry)
    write_registration(dust, "dust-clump-reveal", "furniture-anchored", size, frames)
    draw_contact_sheet(dust, "dust clump reveal", frames)

    grate = OUT / "props" / "grate-open"
    frames = []
    for idx, lift in enumerate([0, -18, -46, -74]):
        img, d = canvas(size)
        rect(d, (58, 32 + lift, 162, 142 + lift), "#6d766f99", "#2e332f", 5)
        for x in range(72, 155, 18):
            line(d, (x, 38 + lift, x, 136 + lift), "#b4beb5", 4)
        for y in range(50, 134, 18):
            line(d, (64, y + lift, 156, y + lift), "#b4beb5", 4)
        file = f"grate_open_{idx+1:02}.png"
        save_sheet_frame(grate, file, img, size)
        entry = {"file": file, "anchor": [110, 142], "role": ["closed", "mechanical-lift-start", "stretch-lift", "open-settle"][idx]}
        if idx == 0:
            entry["canonical"] = True
            entry["scale_reference"] = [110, 32]
        frames.append(entry)
    write_registration(grate, "grate-open", "furniture-anchored", size, frames)
    draw_contact_sheet(grate, "grate open", frames)


def make_scene_assets() -> None:
    scene = OUT / "scene"
    ensure(scene)
    source = OUT / "source" / "ai-room-source.png"
    if source.exists():
        with Image.open(source) as img:
            img.convert("RGB").resize((1600, 900), Image.Resampling.LANCZOS).save(scene / "entry-chamber-bg.png")
    else:
        Image.new("RGB", (1600, 900), "#3d2c22").save(scene / "entry-chamber-bg.png")
    mask = Image.new("RGBA", (1600, 900), (0, 0, 0, 0))
    d = ImageDraw.Draw(mask)
    d.rectangle((570, 500, 910, 574), fill=(145, 99, 58, 230))
    d.rectangle((1210, 455, 1460, 710), fill=(83, 68, 54, 180))
    d.rectangle((0, 770, 1600, 900), fill=(50, 35, 25, 180))
    mask.save(scene / "entry-chamber-foreground-mask.png")


def make_visual_credits() -> None:
    (ROOT / "VISUAL_ASSET_CREDITS.md").write_text(
        """# Visual Asset Credits - Lost & Underfound

Act 1 production visual source art was created with the built-in Codex image
generation tool, then converted into registered project-local raster assets under
`art/act01-production/`.

Generated source files:

- `art/act01-production/source/ai-room-source.png` - Act 1 room/background source.
- `art/act01-production/source/ai-cast-source.png` - Act 1 cast/source style board.

The shipped in-game sprite frames are normalized derivatives with fixed canvases,
explicit anchors, onion-skin QA output, and contact sheets. They are not accepted as
final solely because they were AI-generated or visually polished; each sheet must pass
the registration and cast-scale gates documented in `docs/ANIMATION_BIBLE.md`.

No third-party copyrighted characters, trademarks, or licensed source images were used
as prompts or references in this pass.
""",
        encoding="utf-8",
    )


def make_manifest() -> None:
    save_json(
        OUT / "manifest.json",
        {
            "scene": {
                "background": "scene/entry-chamber-bg.png",
                "foregroundMask": "scene/entry-chamber-foreground-mask.png",
            },
            "characters": {
                "pip": ["walk", "idle", "dust-reach", "toll-paid"],
                "bramble": ["idle", "talk"],
                "old-bottlecap": ["idle", "toll-refused", "toll-paid"],
                "scuttle": ["dash"],
            },
            "props": ["dust-clump-reveal", "grate-open"],
            "source": ["source/ai-room-source.png", "source/ai-cast-source.png"],
            "state": "provisional-production-pass",
        },
    )


def write_production_cast_scale() -> None:
    save_json(
        ART / "cast_scale.json",
        {
            "world_unit": "Pip's shrunk-down standing height = 1.0",
            "tolerance_pct": 8,
            "actors": [
                {
                    "name": "pip",
                    "registration": "act01-production/characters/pip/walk/registration.json",
                    "world_height_units": 1.0,
                },
                {
                    "name": "bramble",
                    "registration": "act01-production/characters/bramble/idle/registration.json",
                    "world_height_units": 0.85,
                },
                {
                    "name": "grommet",
                    "registration": "grommet-idle/registration.json",
                    "world_height_units": 2.4,
                },
                {
                    "name": "scuttle",
                    "registration": "act01-production/characters/scuttle/dash/registration.json",
                    "world_height_units": 0.35,
                },
                {
                    "name": "old-bottlecap",
                    "registration": "act01-production/characters/old-bottlecap/idle/registration.json",
                    "world_height_units": 0.6,
                },
            ],
        },
    )


def main() -> None:
    make_scene_assets()
    make_pip_sheets()
    make_bramble_sheets()
    make_bottlecap_sheets()
    make_scuttle_sheets()
    make_props()
    make_manifest()
    write_production_cast_scale()
    make_visual_credits()


if __name__ == "__main__":
    main()
