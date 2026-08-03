from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art"
OUT = ART / "act01-production"
REFERENCE_SHEET = OUT / "source" / "character-reference-sheet.png"

PX_PER_UNIT = 220
REFERENCE_CROPS = {
    "pip-front": (118, 41, 246, 321),
    "pip-walk": (1123, 61, 1283, 315),
    "pip-run": (1305, 117, 1493, 322),
    "bramble-idle": (1043, 390, 1219, 545),
    "bramble-talk": (1258, 377, 1460, 544),
    "old-bottlecap": (71, 604, 295, 777),
    "old-bottlecap-open": (997, 571, 1216, 782),
    "scuttle": (101, 805, 232, 967),
}


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


def reference_cutout(name: str) -> Image.Image | None:
    if not REFERENCE_SHEET.exists():
        return None
    with Image.open(REFERENCE_SHEET) as source:
        crop = source.convert("RGBA").crop(REFERENCE_CROPS[name])
    alpha = crop.getchannel("A")
    pixels = crop.load()
    width, height = crop.size
    background: set[tuple[int, int]] = set()
    stack: list[tuple[int, int]] = []

    def is_paper(x: int, y: int) -> bool:
        r, g, b, a = pixels[x, y]
        return a > 0 and r > 224 and g > 214 and b > 196

    for x in range(width):
        if is_paper(x, 0):
            stack.append((x, 0))
        if is_paper(x, height - 1):
            stack.append((x, height - 1))
    for y in range(height):
        if is_paper(0, y):
            stack.append((0, y))
        if is_paper(width - 1, y):
            stack.append((width - 1, y))

    while stack:
        x, y = stack.pop()
        if (x, y) in background or not is_paper(x, y):
            continue
        background.add((x, y))
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in background:
                stack.append((nx, ny))

    matte = Image.new("L", crop.size, 255)
    matte_pixels = matte.load()
    for x, y in background:
        matte_pixels[x, y] = 0
    crop.putalpha(Image.composite(alpha, matte, matte))
    bbox = crop.getbbox()
    if not bbox:
        return None
    return crop.crop(bbox)


def paste_registered_cutout(
    canvas_img: Image.Image,
    cutout: Image.Image,
    anchor: tuple[int, int],
    target_height: int,
    x_offset: int = 0,
    y_offset: int = 0,
    mirror: bool = False,
    tilt_degrees: float = 0,
    render_scale: int = 3,
) -> None:
    sprite = cutout.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if mirror else cutout.copy()
    scaled_height = target_height * render_scale
    scale = scaled_height / sprite.height
    sprite = sprite.resize((max(1, round(sprite.width * scale)), scaled_height), Image.Resampling.LANCZOS)
    if tilt_degrees:
        sprite = sprite.rotate(tilt_degrees, expand=True, resample=Image.Resampling.BICUBIC)
    x = anchor[0] * render_scale - sprite.width // 2 + x_offset * render_scale
    y = anchor[1] * render_scale - sprite.height + y_offset * render_scale
    canvas_img.alpha_composite(sprite, (x, y))


def draw_motion_streak(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], color: str = "#f3d07d99", scale: int = 3) -> None:
    for idx in range(len(points) - 1):
        width = max(2, 10 - idx * 2)
        line(draw, (*points[idx], *points[idx + 1]), color, width, scale)


def draw_button_token(draw: ImageDraw.ImageDraw, x: int, y: int, scale: int = 3) -> None:
    ellipse(draw, (x - 13, y - 13, x + 13, y + 13), "#69a19b", "#2f2117", 3, scale)
    ellipse(draw, (x - 4, y - 5, x + 4, y + 3), "#2b2118", scale=scale)
    line(draw, (x - 8, y + 7, x + 8, y + 7), "#2b2118", 2, scale)


def draw_dust_puffs(draw: ImageDraw.ImageDraw, anchor: tuple[int, int], pose: str, scale: int = 3) -> None:
    ax, ay = anchor
    spreads = {
        "crouch-squash": [(-70, -12, 11), (-48, -28, 7), (-25, -42, 5)],
        "crouch-smear": [(-86, -8, 15), (-58, -38, 9), (-28, -54, 6)],
        "crouch-rummage": [(-74, -16, 10), (-50, -44, 8), (-16, -58, 5)],
        "button-pop": [(-72, -50, 9), (-42, -70, 7), (-12, -84, 5)],
        "recoil-found": [(-52, -44, 7), (-22, -62, 5)],
    }.get(pose, [])
    for dx, dy, radius in spreads:
        ellipse(draw, (ax + dx - radius, ay + dy - radius, ax + dx + radius, ay + dy + radius), "#d8c5a177", scale=scale)


def draw_pip_inventory_effect(draw: ImageDraw.ImageDraw, pose: str, scale: int = 3) -> None:
    button_positions = {
        "inspect-button": (196, 205),
        "toss-windup": (190, 190),
        "button-release-smear": (224, 175),
        "toss-follow-through": (238, 165),
        "relief": (208, 205),
        "cheer": (196, 182),
        "button-pop": (93, 218),
        "recoil-found": (118, 206),
    }
    if pose == "button-release-smear":
        draw_motion_streak(draw, [(180, 205), (208, 190), (236, 174), (264, 158)], "#f0c36aaa", scale)
    if pose in button_positions:
        draw_button_token(draw, *button_positions[pose], scale=scale)


def draw_pip_idle_effect(draw: ImageDraw.ImageDraw, pose: str, scale: int = 3) -> None:
    if pose == "idle-02":
        # Local blink/settle only. Do not move the whole cutout for idle.
        line(draw, (141, 116, 154, 118), "#2b1b10", 3, scale)
        line(draw, (172, 116, 185, 118), "#2b1b10", 3, scale)
        line(draw, (128, 58, 120, 50), "#6b3a1c", 3, scale)
        line(draw, (194, 58, 203, 51), "#6b3a1c", 3, scale)


def draw_bramble_desk_effect(draw: ImageDraw.ImageDraw, pose: str, scale: int = 3) -> None:
    if pose in ("shuffle-left", "shuffle-right", "talk-wide", "talk-settle"):
        y = {"shuffle-left": 206, "shuffle-right": 202, "talk-wide": 198, "talk-settle": 204}[pose]
        polygon(draw, [(68, y), (138, y - 8), (152, y + 22), (82, y + 30)], "#efe0b9", "#5f4931", scale)
        line(draw, (82, y + 7, 136, y), "#a28058", 2, scale)
    if pose == "stamp-smear":
        draw_motion_streak(draw, [(224, 120), (225, 150), (224, 178)], "#7b2e2daa", scale)


def draw_bottlecap_effect(draw: ImageDraw.ImageDraw, pose: str, scale: int = 3) -> None:
    if pose in ("idle-02", "idle-03", "idle-04"):
        brow = {"idle-02": -2, "idle-03": 0, "idle-04": 2}[pose]
        line(draw, (125 + brow, 116, 145 + brow, 112), "#25190f", 3, scale)
        line(draw, (175 + brow, 112, 195 + brow, 116), "#25190f", 3, scale)
        if pose == "idle-03":
            line(draw, (133, 128, 143, 129), "#25190f", 3, scale)
            line(draw, (177, 129, 187, 128), "#25190f", 3, scale)
    if pose == "arm-smear":
        draw_motion_streak(draw, [(214, 184), (236, 156), (265, 128)], "#5b351eaa", scale)
    button_positions = {
        "reach-anticipation": (244, 154),
        "catch": (235, 126),
        "inspect": (184, 112),
        "approve": (206, 128),
    }
    if pose in button_positions:
        draw_button_token(draw, *button_positions[pose], scale=scale)


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
        "crouch-squash": (-12, 42, -18, 14, 0),
        "crouch-reach": (-24, 46, -18, 20, 0),
        "crouch-smear": (-34, 48, -20, 22, 0),
        "crouch-contact": (-30, 50, -18, 20, 0),
        "crouch-rummage": (-28, 52, -18, 20, 0),
        "button-pop": (8, 10, -14, 26, 0),
        "recoil-found": (14, -6, -12, 26, 0),
        "inspect-button": (3, 0, -10, 20, 0),
        "toss-windup": (-14, 8, -12, 20, 0),
        "button-release-smear": (18, -2, -12, 22, 0),
        "toss-follow-through": (22, 0, -12, 22, 0),
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
    reach = pose in ("crouch-reach", "crouch-smear", "crouch-contact", "crouch-rummage")
    toss = pose in ("inspect-button", "toss-windup", "button-release-smear", "toss-follow-through")
    if reach:
        line(draw, (ax + 28 + lean, body_y + 28, ax - 68, body_y + 95), "#e8aa80", 8, scale)
    elif toss:
        end = {
            "inspect-button": (ax + 48, body_y + 58),
            "toss-windup": (ax + 40, body_y + 22),
            "button-release-smear": (ax + 84, body_y + 10),
            "toss-follow-through": (ax + 72, body_y + 2),
        }[pose]
        line(draw, (ax + 31 + lean, body_y + 22, end[0], end[1]), "#e8aa80", 8, scale)
        line(draw, (ax - 31 + lean, body_y + 22, ax - 53, body_y + 56), "#e8aa80", 8, scale)
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
    draw_dust_puffs(draw, anchor, pose, scale)
    draw_pip_inventory_effect(draw, pose, scale)


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
            ("pip_dust_02.png", "squash-weight-drop", "crouch-squash"),
            ("pip_dust_03.png", "reach-arc", "crouch-reach"),
            ("pip_dust_04.png", "single-goofy-reach-smear", "crouch-smear"),
            ("pip_dust_05.png", "contact-hold", "crouch-contact"),
            ("pip_dust_06.png", "rummage-overlap", "crouch-rummage"),
            ("pip_dust_07.png", "button-pop-reveal", "button-pop"),
            ("pip_dust_08.png", "recoil-found-settle", "recoil-found"),
        ],
        "toll-paid": [
            ("pip_toll_01.png", "button-read-before-handoff", "inspect-button"),
            ("pip_toll_02.png", "handoff-anticipation", "toss-windup"),
            ("pip_toll_03.png", "button-release-smear", "button-release-smear"),
            ("pip_toll_04.png", "follow-through", "toss-follow-through"),
            ("pip_toll_05.png", "relief-read", "relief"),
            ("pip_toll_06.png", "small-excitement", "cheer"),
        ],
    }.items():
        sheet = base / action
        frames = []
        for idx, (file, role, pose) in enumerate(roles):
            img, d = canvas(size)
            if REFERENCE_SHEET.exists():
                cutout_name = "pip-front" if action in ("idle", "dust-reach", "toll-paid") else "pip-walk"
                if action == "toll-paid" and idx == 1:
                    cutout_name = "pip-run"
                cutout = reference_cutout(cutout_name)
                if cutout:
                    bob = {
                        "walk-left-recoil-down": 4,
                        "walk-left-passing": 2,
                        "walk-left-high": -4,
                        "walk-right-recoil-down": 4,
                        "walk-right-passing": 2,
                        "walk-right-high": -4,
                        "crouch-squash": 12,
                        "crouch-reach": 16,
                        "crouch-smear": 18,
                        "crouch-contact": 18,
                        "crouch-rummage": 18,
                        "button-pop": -3,
                        "recoil-found": -8,
                        "toss-windup": 6,
                        "button-release-smear": -3,
                        "toss-follow-through": -2,
                        "found-pop": -8,
                        "cheer": -10,
                    }.get(pose, 0)
                    mirror = pose in ("walk-right-contact", "walk-right-recoil-down", "walk-right-passing", "walk-right-high")
                    tilt = {
                        "crouch-anticipate": -4,
                        "crouch-squash": -7,
                        "crouch-reach": -10,
                        "crouch-smear": -14,
                        "crouch-contact": -10,
                        "crouch-rummage": -12,
                        "button-pop": 4,
                        "recoil-found": 8,
                        "toss-windup": -10,
                        "button-release-smear": 8,
                        "toss-follow-through": 12,
                        "found-pop": 4,
                        "cheer": -3,
                    }.get(pose, 0)
                    paste_registered_cutout(img, cutout, (160, 300), 220, y_offset=bob, mirror=mirror, tilt_degrees=tilt)
                    if action == "idle":
                        draw_pip_idle_effect(d, pose)
                    draw_dust_puffs(d, (160, 300), pose)
                    draw_pip_inventory_effect(d, pose)
                else:
                    draw_pip(d, (160, 300), 80, pose)
            else:
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
    stamp = {
        "idle-01": 0,
        "shuffle-left": 5,
        "idle-02": 8,
        "stamp-up": 28,
        "stamp-smear": 10,
        "stamp-down": -4,
        "stamp-recoil": 6,
        "talk-01": 0,
        "talk-open": 3,
        "talk-wide": 5,
        "talk-settle": 1,
    }[pose]
    mouth_open = pose in ("talk-open", "talk-wide")
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
    draw_bramble_desk_effect(draw, pose, scale)


def make_bramble_sheets() -> None:
    size = (320, 260)
    base = OUT / "characters" / "bramble"
    specs = {
        "idle": [
            ("bramble_idle_01.png", "folder-shuffle-start", "idle-01"),
            ("bramble_idle_02.png", "paper-slide-overlap", "shuffle-left"),
            ("bramble_idle_03.png", "stamp-preparation", "idle-02"),
            ("bramble_idle_04.png", "stamp-up-anticipation", "stamp-up"),
            ("bramble_idle_05.png", "single-stamp-smear", "stamp-smear"),
            ("bramble_idle_06.png", "stamp-impact-contact", "stamp-down"),
            ("bramble_idle_07.png", "stamp-recoil-settle", "stamp-recoil"),
        ],
        "talk": [
            ("bramble_talk_01.png", "talk-closed-mouth", "talk-01"),
            ("bramble_talk_02.png", "talk-open-mouth", "talk-open"),
            ("bramble_talk_03.png", "talk-wide-emphasis", "talk-wide"),
            ("bramble_talk_04.png", "talk-return-passing", "talk-open"),
            ("bramble_talk_05.png", "talk-settle-paper", "talk-settle"),
            ("bramble_talk_06.png", "talk-neutral-hold", "talk-01"),
        ],
    }
    for action, roles in specs.items():
        sheet = base / action
        frames = []
        for idx, (file, role, pose) in enumerate(roles):
            img, d = canvas(size)
            if REFERENCE_SHEET.exists():
                cutout = reference_cutout("bramble-talk" if action == "talk" else "bramble-idle")
                if cutout:
                    paste_registered_cutout(
                        img,
                        cutout,
                        (160, 205),
                        187,
                    )
                    draw_bramble_desk_effect(d, pose)
                else:
                    draw_bramble(d, (160, 205), 18, pose)
            else:
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
    tilt = {
        "idle-01": 0,
        "idle-02": -4,
        "idle-03": 0,
        "idle-04": 4,
        "refuse-left": -8,
        "refuse-right": 8,
        "refuse-squash": 0,
        "notice": -2,
        "reach-anticipation": -4,
        "arm-smear": 2,
        "catch": 4,
        "inspect": 0,
        "approve": 2,
        "settle": 0,
    }[pose]
    yoff = -5 if pose in ("approve", "settle") else (4 if pose == "refuse-squash" else 0)
    for level, color in enumerate(["#7e4a28", "#4d4b45", "#8b5b2e", "#b08b45"]):
        y = top_y + 92 - level * 24 + yoff
        ellipse(draw, (ax - 66 + tilt, y, ax + 66 + tilt, y + 34), color, "#2f2117", 4, scale)
        rect(draw, (ax - 58 + tilt, y + 13, ax + 58 + tilt, y + 27), color, "#2f2117", 2, scale)
    line(draw, (ax - 36 + tilt, top_y + 83 + yoff, ax - 9 + tilt, top_y + 77 + yoff), "#25190f", 5, scale)
    line(draw, (ax + 36 + tilt, top_y + 83 + yoff, ax + 9 + tilt, top_y + 77 + yoff), "#25190f", 5, scale)
    ellipse(draw, (ax - 28 + tilt, top_y + 72 + yoff, ax - 16 + tilt, top_y + 84 + yoff), "#17120f", scale=scale)
    ellipse(draw, (ax + 16 + tilt, top_y + 72 + yoff, ax + 28 + tilt, top_y + 84 + yoff), "#17120f", scale=scale)
    line(draw, (ax - 20 + tilt, top_y + 103 + yoff, ax + 20 + tilt, top_y + 103 + yoff), "#25190f", 4, scale)
    if pose in ("notice", "reach-anticipation", "arm-smear", "catch", "inspect", "approve", "settle"):
        bx = {
            "notice": ax + 52,
            "reach-anticipation": ax + 72,
            "arm-smear": ax + 96,
            "catch": ax + 78,
            "inspect": ax + 22,
            "approve": ax + 46,
            "settle": ax + 35,
        }[pose]
        by = top_y + {
            "notice": 105,
            "reach-anticipation": 78,
            "arm-smear": 62,
            "catch": 54,
            "inspect": 58,
            "approve": 54,
            "settle": 78,
        }[pose]
        line(draw, (ax + 52, top_y + 112, bx, by), "#5b351e", 5, scale)
    draw_bottlecap_effect(draw, pose, scale)


def make_bottlecap_sheets() -> None:
    size = (320, 260)
    base = OUT / "characters" / "old-bottlecap"
    specs = {
        "idle": [("old_bottlecap_idle_01.png", "heavy-rock-center", "idle-01"), ("old_bottlecap_idle_02.png", "heavy-rock-left", "idle-02"), ("old_bottlecap_idle_03.png", "weighted-return", "idle-03"), ("old_bottlecap_idle_04.png", "heavy-rock-right", "idle-04")],
        "toll-refused": [
            ("old_bottlecap_refuse_01.png", "anticipation-glare", "idle-01"),
            ("old_bottlecap_refuse_02.png", "dismissive-left", "refuse-left"),
            ("old_bottlecap_refuse_03.png", "dismissive-right", "refuse-right"),
            ("old_bottlecap_refuse_04.png", "heavy-squash-no", "refuse-squash"),
            ("old_bottlecap_refuse_05.png", "deadpan-settle", "idle-01"),
        ],
        "toll-paid": [
            ("old_bottlecap_paid_01.png", "button-noticed", "notice"),
            ("old_bottlecap_paid_02.png", "reach-anticipation", "reach-anticipation"),
            ("old_bottlecap_paid_03.png", "single-arm-smear", "arm-smear"),
            ("old_bottlecap_paid_04.png", "button-catch-contact", "catch"),
            ("old_bottlecap_paid_05.png", "inspect-held-beat", "inspect"),
            ("old_bottlecap_paid_06.png", "grudging-approval", "approve"),
            ("old_bottlecap_paid_07.png", "weighted-settle-open", "settle"),
        ],
    }
    for action, roles in specs.items():
        sheet = base / action
        frames = []
        for idx, (file, role, pose) in enumerate(roles):
            img, d = canvas(size)
            if REFERENCE_SHEET.exists():
                cutout = reference_cutout("old-bottlecap-open" if action == "toll-paid" and idx >= 4 else "old-bottlecap")
                if cutout:
                    tilt = {
                        "refuse-left": -5,
                        "refuse-right": 5,
                        "refuse-squash": 0,
                        "reach-anticipation": -4,
                        "arm-smear": 4,
                        "catch": 5,
                        "approve": 2,
                        "settle": 1,
                    }.get(pose, 0)
                    if action == "idle":
                        tilt = 0
                    yoff = 0 if action == "idle" else (-4 if pose in ("approve", "settle") else (4 if pose == "refuse-squash" else 0))
                    paste_registered_cutout(img, cutout, (160, 210), 132, y_offset=yoff, tilt_degrees=tilt)
                    draw_bottlecap_effect(d, pose)
                else:
                    draw_bottlecap(d, (160, 210), 78, pose)
            else:
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
    if pose in ("smear-long", "smear-ball"):
        if pose == "smear-long":
            ellipse(draw, (ax - 92, top_y + 15, ax + 72, ay), "#2d3036aa", scale=scale)
            line(draw, (ax - 110, top_y + 43, ax + 92, top_y + 42), "#22252a", 8, scale)
        else:
            ellipse(draw, (ax - 46, top_y + 14, ax + 52, ay - 2), "#25282fcc", scale=scale)
            line(draw, (ax - 88, top_y + 44, ax + 34, top_y + 42), "#202329aa", 7, scale)
        return
    squash = 10 if pose == "land-squash" else (8 if pose == "land" else 0)
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
    roles = [
        ("scuttle_dash_01.png", "solid-pre-dash", "ready"),
        ("scuttle_dash_02.png", "anticipation-squash", "land-squash"),
        ("scuttle_dash_03.png", "single-long-smear-cel", "smear-long"),
        ("scuttle_dash_04.png", "rolling-smear-cel", "smear-ball"),
        ("scuttle_dash_05.png", "solid-exit-pose", "land"),
    ]
    frames = []
    for idx, (file, role, pose) in enumerate(roles):
        img, d = canvas(size)
        if REFERENCE_SHEET.exists() and pose not in ("smear-long", "smear-ball"):
            cutout = reference_cutout("scuttle")
            if cutout:
                paste_registered_cutout(img, cutout, (90, 120), 77, mirror=pose == "land", tilt_degrees=4 if pose == "land" else 0)
            else:
                draw_scuttle(d, (90, 120), 43, pose)
        else:
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
    bg = Image.new("RGB", (1600, 900), "#2f2219")
    d = ImageDraw.Draw(bg)
    for y in range(0, 900):
        shade = int(22 + 48 * (y / 900))
        d.line((0, y, 1600, y), fill=(shade + 24, shade + 12, shade + 4))
    d.rectangle((0, 0, 1600, 190), fill="#2a1c15")
    for y in range(0, 190, 16):
        d.line((0, y, 1600, y + 22), fill="#3c2a24", width=3)
    for x in range(120, 1600, 260):
        d.arc((x, 25, x + 130, 105), 20, 160, fill="#8b6a58", width=5)
    d.rectangle((0, 150, 1600, 218), fill="#5b321d")
    d.line((0, 214, 1600, 214), fill="#170d08", width=8)
    d.polygon([(320, 92), (470, 70), (488, 180), (338, 190)], fill="#cab88e", outline="#5b4630")
    d.text((350, 116), "DO NOT", fill="#3d2a1c")
    d.text((350, 146), "REMOVE", fill="#3d2a1c")
    d.rectangle((0, 650, 1600, 900), fill="#6d4528")
    d.polygon([(0, 650), (1600, 650), (1600, 900), (0, 900)], fill="#7b4b29")
    for x in range(-80, 1680, 160):
        d.line((x, 655, x + 250, 900), fill="#513119", width=4)
    for y in [695, 735, 780, 830, 875]:
        d.line((0, y, 1600, y + 12), fill="#8d5c35", width=3)
    for row, y in enumerate(range(245, 610, 70)):
        for x in range(-40 + (row % 2) * 70, 1600, 140):
            d.rounded_rectangle((x, y, x + 132, y + 68), radius=10, fill="#6b5039", outline="#3d2a1f", width=2)
    d.rectangle((0, 180, 1600, 245), fill="#3a2418")
    d.line((0, 245, 1600, 245), fill="#130d09", width=10)
    overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.polygon([(720, 245), (775, 245), (610, 650), (565, 650)], fill=(255, 222, 140, 62))
    od.polygon([(1060, 245), (1120, 245), (1000, 650), (930, 650)], fill=(255, 222, 140, 48))
    for x, y, r in [(80, 805, 48), (120, 790, 36), (95, 755, 24)]:
        od.ellipse((x - r, y - r, x + r, y + r), fill=(110, 105, 98, 92))
    for x, y in [(210, 785), (280, 820), (1110, 735), (1195, 760), (1320, 790)]:
        od.ellipse((x - 9, y - 5, x + 9, y + 5), fill=(214, 172, 80, 130))
    bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    bg.save(scene / "entry-chamber-bg.png")

    def transparent_layer() -> tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new("RGBA", (1600, 900), (0, 0, 0, 0))
        return img, ImageDraw.Draw(img)

    cubby, cd = transparent_layer()
    cd.rounded_rectangle((36, 260, 390, 690), radius=16, fill="#6b4325", outline="#2b1a10", width=8)
    colors = ["#8b2b22", "#2f6746", "#5b3d86", "#c59432", "#9d3121", "#a5a09a", "#325f86", "#af5628", "#7d8b34", "#8f323e", "#b1955d", "#754a66"]
    for idx, color in enumerate(colors):
        col = idx % 3
        row = idx // 3
        x = 68 + col * 102
        y = 290 + row * 88
        cd.rounded_rectangle((x - 38, y - 38, x + 38, y + 38), radius=12, fill="#2d2018", outline="#8f653b", width=5)
        cd.ellipse((x - 31, y - 31, x + 31, y + 31), fill=color, outline="#25170f", width=5)
        cd.ellipse((x - 19, y - 19, x + 19, y + 19), outline="#00000055", width=3)
    cubby.save(scene / "entry-chamber-cubby-wall.png")

    desk_back, dd = transparent_layer()
    dd.rounded_rectangle((500, 430, 880, 535), radius=8, fill="#a3472d", outline="#371c12", width=6)
    dd.rectangle((540, 525, 830, 585), fill="#8a3f25")
    dd.rectangle((610, 535, 650, 705), fill="#452819")
    dd.rectangle((720, 535, 760, 705), fill="#4e351b")
    for x, color in [(575, "#3b2853"), (748, "#477331")]:
        dd.rounded_rectangle((x, 560, x + 74, 745), radius=16, fill=color, outline="#2c2016", width=4)
        for yy in range(574, 735, 18):
            dd.line((x + 5, yy, x + 69, yy), fill="#00000022", width=2)
    dd.rectangle((590, 420, 875, 455), fill="#bd8d54", outline="#5c341b", width=4)
    dd.rectangle((640, 390, 805, 428), fill="#d8c57e", outline="#6b4b24", width=3)
    dd.rectangle((735, 366, 875, 430), fill="#a55228", outline="#522714", width=4)
    for x, y, color in [(770, 380, "#9d4c24"), (810, 370, "#d1a848"), (845, 350, "#c94233")]:
        dd.line((x, y + 56, x + 35, y), fill="#4d2a18", width=8)
        dd.line((x + 4, y + 52, x + 39, y - 4), fill=color, width=10)
    desk_back.save(scene / "entry-chamber-desk-back.png")

    desk_front, dfd = transparent_layer()
    dfd.rounded_rectangle((500, 472, 890, 620), radius=8, fill="#8f3f27", outline="#3b1d11", width=6)
    dfd.rectangle((640, 470, 770, 515), fill="#d7c9a6", outline="#755334", width=3)
    dfd.line((500, 472, 890, 472), fill="#d69656", width=6)
    desk_front.save(scene / "entry-chamber-desk-foreground.png")

    gate_back, gd = transparent_layer()
    gd.rounded_rectangle((1050, 285, 1360, 650), radius=44, fill="#6a5138", outline="#241912", width=10)
    gd.rounded_rectangle((1090, 320, 1320, 610), radius=18, fill="#2e2b23", outline="#20140e", width=4)
    gd.rectangle((1110, 340, 1300, 590), fill="#2a3831")
    for x in range(1120, 1305, 20):
        gd.line((x, 333, x, 598), fill="#c5cdbf", width=5)
    for y in range(350, 595, 20):
        gd.line((1104, y, 1306, y), fill="#c5cdbf", width=5)
    gd.rectangle((1320, 420, 1400, 470), fill="#9d7036", outline="#2c1c10", width=5)
    gd.ellipse((1340, 432, 1360, 452), fill="#27190e")
    gate_back.save(scene / "entry-chamber-gate-back.png")

    gate_front, gfd = transparent_layer()
    for x in [1052, 1358]:
        gfd.line((x, 320, x, 625), fill="#1e1813", width=12)
    for y in [285, 650]:
        gfd.line((1080, y, 1330, y), fill="#1e1813", width=12)
    gate_front.save(scene / "entry-chamber-gate-foreground.png")

    popcorn, pd = transparent_layer()
    for i, (x, y, r) in enumerate([(1365, 590, 62), (1420, 610, 78), (1480, 585, 55), (1410, 535, 58), (1325, 635, 42), (1500, 650, 38)]):
        pd.ellipse((x - r, y - r, x + r, y + r), fill="#d8aa58", outline="#875a26", width=5)
        pd.ellipse((x - r // 3, y - r // 4, x + r // 4, y + r // 5), fill="#f0d486")
    popcorn.save(scene / "entry-chamber-popcorn-boulder.png")

    cobweb, cwd = transparent_layer()
    for center in [(1450, 320), (1515, 420), (1420, 515)]:
        cx, cy = center
        for radius in [40, 75, 115, 155]:
            cwd.arc((cx - radius, cy - radius, cx + radius, cy + radius), 210, 355, fill="#d8d4c688", width=3)
        for angle in [-65, -35, 0, 35, 65]:
            ex = cx + int(170 * math.cos(math.radians(angle)))
            ey = cy + int(170 * math.sin(math.radians(angle)))
            cwd.line((cx, cy, ex, ey), fill="#d8d4c688", width=3)
    cobweb.save(scene / "entry-chamber-cobweb-curtain.png")

    save_json(
        scene / "layers.json",
        {
            "scene": "act01-entry-chamber",
            "coordinate_space": {"width": 1600, "height": 900},
            "layers": [
                {"id": "background-plate", "kind": "background", "asset": "entry-chamber-bg.png", "z": 1},
                {"id": "cubby-wall", "kind": "midground-prop", "asset": "entry-chamber-cubby-wall.png", "z": 4},
                {"id": "cobweb-curtain", "kind": "midground-prop", "asset": "entry-chamber-cobweb-curtain.png", "z": 4},
                {"id": "popcorn-boulder", "kind": "midground-prop", "asset": "entry-chamber-popcorn-boulder.png", "z": 5},
                {"id": "dust-prop", "kind": "midground-prop", "slot": "floor-left", "z": 6},
                {"id": "desk-back", "kind": "furniture-back", "asset": "entry-chamber-desk-back.png", "z": 7},
                {"id": "gate-back", "kind": "furniture-back", "asset": "entry-chamber-gate-back.png", "z": 7},
                {"id": "bramble-body", "kind": "furniture-anchored-actor", "slot": "behind-desk", "z": 8},
                {"id": "desk-foreground", "kind": "foreground-occluder", "asset": "entry-chamber-desk-foreground.png", "z": 10},
                {"id": "gate-foreground", "kind": "foreground-occluder", "asset": "entry-chamber-gate-foreground.png", "z": 11},
                {"id": "old-bottlecap-body", "kind": "furniture-anchored-actor", "slot": "at-gate-front", "z": 12},
                {"id": "pip-body", "kind": "walk-plane-actor", "slot": "floor", "z": 12},
                {"id": "hotspot-masks", "kind": "interaction-mask", "source": "src/main.ts", "z": 20}
            ],
        },
    )


def make_visual_credits() -> None:
    (ROOT / "VISUAL_ASSET_CREDITS.md").write_text(
        """# Visual Asset Credits - Lost & Underfound

Act 1 production visual source art was created with the built-in Codex image
generation tool, then converted into registered project-local raster assets under
`art/act01-production/`.

Generated source files:

- `art/act01-production/source/ai-room-source.png` - Act 1 room/background source.
- `art/act01-production/source/ai-cast-source.png` - Act 1 cast/source style board.
- `art/act01-production/source/character-reference-sheet.png` - Act 1 character
  model/reference sheet used for the current normalized sprite pass.

The current Act 1 room is rebuilt as project-local separated raster layers from
the deterministic asset generator so actors can render behind or in front of
furniture instead of depending on one baked background plate.

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
                "cubbyWall": "scene/entry-chamber-cubby-wall.png",
                "cobwebCurtain": "scene/entry-chamber-cobweb-curtain.png",
                "popcornBoulder": "scene/entry-chamber-popcorn-boulder.png",
                "deskBack": "scene/entry-chamber-desk-back.png",
                "deskForeground": "scene/entry-chamber-desk-foreground.png",
                "gateBack": "scene/entry-chamber-gate-back.png",
                "gateForeground": "scene/entry-chamber-gate-foreground.png",
                "layers": "scene/layers.json",
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
