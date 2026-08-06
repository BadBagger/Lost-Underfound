#!/usr/bin/env python3
"""Build Bramble's desk-clerk loops from manually aligned expression plates.

The source plates are full Bramble renders on magenta. The body is locked to
the first plate; only the face patch changes so Bramble can emote without the
whole dust blob drifting around.
"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path("C:/Users/KyleB/OneDrive/Pictures/Lost Animation PNGS")
OUT_ROOT = ROOT / "art" / "act01-production" / "characters" / "bramble"
QA = ROOT / "art" / "act01-production" / "qa"
MANIFEST = ROOT / "art" / "rigs" / "bramble" / "manifest.json"

CANVAS = (320, 260)
ANCHOR = (160, 252)
TOP_MARGIN = 8
BOTTOM_MARGIN = 8
FRAME_HEIGHT = CANVAS[1] - TOP_MARGIN - BOTTOM_MARGIN
FACE_RECT = (58, 84, 264, 205)
MAGENTA = (255, 0, 255)


def key_magenta(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    pixels = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            distance = ((r - MAGENTA[0]) ** 2 + (g - MAGENTA[1]) ** 2 + (b - MAGENTA[2]) ** 2) ** 0.5
            if distance < 130:
                pixels[x, y] = (0, 0, 0, 0)
            elif a:
                # Remove pink edge spill from semi-opaque lint strands.
                if r > 125 and b > 115 and g < 115 and r - g > 45 and b - g > 35:
                    warm = max(70, min(150, int((r + b) * 0.28 + g * 0.44)))
                    pixels[x, y] = (warm, max(58, min(122, g + 18)), max(48, warm - 24), a)
    return image


def crop_to_content(image: Image.Image) -> Image.Image:
    bbox = image.getchannel("A").getbbox()
    if not bbox:
        raise RuntimeError("empty Bramble source after magenta key")
    return image.crop(bbox)


def fit_to_canvas(image: Image.Image) -> Image.Image:
    image = crop_to_content(image)
    scale = FRAME_HEIGHT / image.height
    width = round(image.width * scale)
    resized = image.resize((width, FRAME_HEIGHT), Image.Resampling.LANCZOS)
    frame = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    x = ANCHOR[0] - width // 2
    y = ANCHOR[1] - FRAME_HEIGHT
    frame.alpha_composite(resized, (x, y))
    return frame


def soft_rect_mask(size: tuple[int, int]) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    pad_x = 8
    pad_y = 6
    draw.rounded_rectangle((pad_x, pad_y, size[0] - pad_x, size[1] - pad_y), radius=22, fill=255)
    # Feather by scaling through a small blur-free cascade: keeps edges soft
    # without introducing another dependency.
    for inset, alpha in ((3, 180), (6, 90)):
        draw.rounded_rectangle(
            (pad_x - inset, pad_y - inset, size[0] - pad_x + inset, size[1] - pad_y + inset),
            radius=24,
            outline=alpha,
            width=2,
        )
    return mask


def make_expression_frames() -> list[Image.Image]:
    sources = [key_magenta(SOURCE_DIR / f"Bramble{index}.png") for index in range(1, 7)]
    master = sources[0]
    mask = soft_rect_mask((FACE_RECT[2] - FACE_RECT[0], FACE_RECT[3] - FACE_RECT[1]))
    frames: list[Image.Image] = []
    for source in sources:
        frame = master.copy()
        patch = source.crop(FACE_RECT)
        frame.alpha_composite(patch, FACE_RECT[:2])
        clipped = Image.new("RGBA", master.size, (0, 0, 0, 0))
        clipped.alpha_composite(patch, FACE_RECT[:2])
        face_alpha = Image.new("L", master.size, 0)
        face_alpha.paste(mask, FACE_RECT[:2])
        base = master.copy()
        base.alpha_composite(clipped)
        # Re-apply the face patch through the mask so hair/edge drift outside
        # the facial action area never replaces the locked body.
        frame = Image.composite(base, master, face_alpha)
        frames.append(frame)
    return frames


def blend_expression(a: Image.Image, b: Image.Image, amount: float, variant: int) -> Image.Image:
    frame = Image.blend(a, b, amount)
    # Add tiny, localized breathing/lint variation so held frames are real
    # animation frames without moving the actor registration.
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    x = 110 + (variant * 17) % 92
    y = 190 + (variant * 11) % 90
    color = (235, 202, 147, 10 + (variant % 3) * 4)
    draw.line((x, y, x + 3, y - 2), fill=color, width=1)
    return Image.alpha_composite(frame, overlay)


def expand_sequence(expressions: list[Image.Image], key_ids: list[int], frame_count: int) -> list[Image.Image]:
    result: list[Image.Image] = []
    if len(key_ids) < 2:
        raise ValueError("need at least two keys")
    per_segment = frame_count / (len(key_ids) - 1)
    for frame_index in range(frame_count):
        segment = min(len(key_ids) - 2, int(frame_index / per_segment))
        local = (frame_index - segment * per_segment) / per_segment
        # Ease in/out, then hold close to keys to avoid twitchy constant motion.
        if local < 0.28:
            eased = 0.0
        elif local > 0.82:
            eased = 1.0
        else:
            t = (local - 0.28) / 0.54
            eased = t * t * (3 - 2 * t)
        result.append(blend_expression(expressions[key_ids[segment]], expressions[key_ids[segment + 1]], eased, frame_index))
    return result


def write_registration(folder: Path, sheet: str, prefix: str, frame_count: int, roles: list[str]) -> None:
    frames = []
    for index in range(frame_count):
        entry = {
            "file": f"{prefix}_{index + 1:02d}.png",
            "anchor": list(ANCHOR),
            "role": roles[index] if index < len(roles) else f"{sheet}-{index + 1:02d}",
        }
        if index == 0:
            entry["canonical"] = True
            entry["scale_reference"] = [ANCHOR[0], TOP_MARGIN]
        frames.append(entry)
    data = {
        "sheet": sheet,
        "actor_type": "furniture-anchored",
        "canvas": {"width": CANVAS[0], "height": CANVAS[1]},
        "anchor_tolerance_px": 1,
        "frames": frames,
        "approval_state": "manual-plate-desk-clerk-built",
        "source": "tools/build_bramble_desk_clerk_frames.py + C:/Users/KyleB/OneDrive/Pictures/Lost Animation PNGS/Bramble1-6.png",
    }
    (folder / "registration.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def save_contact(paths: list[Path], output: Path, columns: int = 8) -> None:
    images = [Image.open(path).convert("RGBA") for path in paths]
    rows = (len(images) + columns - 1) // columns
    sheet = Image.new("RGBA", (columns * CANVAS[0], rows * CANVAS[1]), (46, 39, 33, 255))
    for index, image in enumerate(images):
        sheet.alpha_composite(image, ((index % columns) * CANVAS[0], (index // columns) * CANVAS[1]))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def save_gif(paths: list[Path], output: Path, duration_ms: int) -> None:
    images = [Image.open(path).convert("RGBA") for path in paths]
    output.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(output, save_all=True, append_images=images[1:], duration=duration_ms, loop=0, disposal=2)


def write_frames(folder_name: str, prefix: str, frames: list[Image.Image], roles: list[str], fps: int) -> list[Path]:
    folder = OUT_ROOT / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    for png in folder.glob(f"{prefix}_*.png"):
        png.unlink()
    paths: list[Path] = []
    for index, frame in enumerate(frames):
        out = fit_to_canvas(frame)
        path = folder / f"{prefix}_{index + 1:02d}.png"
        out.save(path)
        paths.append(path)
    write_registration(folder, f"bramble-{folder_name}", prefix, len(frames), roles)
    save_contact(paths, QA / f"bramble-{folder_name}-contact-sheet.png")
    save_gif(paths, QA / f"bramble-{folder_name}-normal.gif", round(1000 / fps))
    save_gif(paths, QA / f"bramble-{folder_name}-half-speed.gif", round(2000 / fps))
    return paths


def update_hashes(changed_paths: list[Path]) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    hashes = manifest.setdefault("render", {}).setdefault("hashes", {})
    for state_name, folder_name, prefix in (
        ("idle", "idle", "bramble_idle"),
        ("talk", "talk", "bramble_talk"),
        ("greeting", "greeting", "bramble_greeting"),
        ("handoff", "handoff", "bramble_handoff"),
        ("wrongAction", "wrong-action", "bramble_wrong"),
    ):
        folder = OUT_ROOT / folder_name
        for path in sorted(folder.glob(f"{prefix}_*.png")):
            hashes[path.relative_to(ROOT).as_posix()] = sha256(path.read_bytes()).hexdigest()
    manifest["render"]["tool"] = "tools/build_bramble_desk_clerk_frames.py for desk idle/talk; tools/render_bramble_rig.py for remaining states"
    manifest["render"]["desk_clerk_source"] = "C:/Users/KyleB/OneDrive/Pictures/Lost Animation PNGS/Bramble1-6.png"
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    expressions = make_expression_frames()
    idle_keys = [0, 0, 1, 2, 0, 4, 0, 5, 0]
    talk_keys = [0, 2, 3, 2, 0, 4, 3, 2, 5, 0, 3, 0, 4]
    idle_frames = expand_sequence(expressions, idle_keys, 24)
    talk_frames = expand_sequence(expressions, talk_keys, 48)
    idle_paths = write_frames("idle", "bramble_idle", idle_frames, [f"desk-idle-{i + 1:02d}" for i in range(24)], 12)
    talk_paths = write_frames("talk", "bramble_talk", talk_frames, [f"desk-talk-{i + 1:02d}" for i in range(48)], 12)
    update_hashes(idle_paths + talk_paths)
    print(f"Wrote {len(idle_paths)} Bramble idle frame(s) and {len(talk_paths)} talk frame(s).")


if __name__ == "__main__":
    main()
