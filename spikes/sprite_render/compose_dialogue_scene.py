#!/usr/bin/env python3
"""Compose a dialogue/cutscene proof from transparent character frames."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


PANEL = (31, 20, 15, 232)
PANEL_LINE = (230, 196, 134, 255)
TEXT = (255, 241, 203, 255)
NAME = (255, 214, 126, 255)


def alpha_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    bbox = img.getchannel("A").getbbox()
    if not bbox:
        raise ValueError("transparent frame has no visible content")
    return bbox


def fit_height(img: Image.Image, height: int) -> Image.Image:
    bbox = alpha_bbox(img)
    crop = img.crop(bbox)
    scale = height / crop.height
    return crop.resize((max(1, round(crop.width * scale)), height), Image.Resampling.LANCZOS)


def letterbox_cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    scale = max(target_w / img.width, target_h / img.height)
    resized = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
    x = (resized.width - target_w) // 2
    y = (resized.height - target_h) // 2
    return resized.crop((x, y, x + target_w, y + target_h))


def draw_dialogue_panel(img: Image.Image, speaker: str, line: str) -> None:
    draw = ImageDraw.Draw(img)
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    bold_path = Path("C:/Windows/Fonts/arialbd.ttf")
    body_font = ImageFont.truetype(str(font_path), 25) if font_path.exists() else ImageFont.load_default()
    name_font = ImageFont.truetype(str(bold_path), 18) if bold_path.exists() else ImageFont.load_default()
    panel = (44, 516, img.width - 44, img.height - 34)
    draw.rounded_rectangle(panel, radius=10, fill=PANEL, outline=PANEL_LINE, width=2)
    draw.text((panel[0] + 28, panel[1] + 24), speaker.upper(), fill=NAME, font=name_font)
    # Simple manual wrap; this is proof UI, not final text layout.
    words = line.split()
    lines: list[str] = []
    current = ""
    max_chars = 58
    for word in words:
        test = f"{current} {word}".strip()
        if len(test) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    y = panel[1] + 62
    for wrapped in lines[:3]:
        draw.text((panel[0] + 28, y), wrapped, fill=TEXT, font=body_font)
        y += 34


def compose_frame(bg: Image.Image, sprite: Image.Image, frame_index: int, args: argparse.Namespace) -> Image.Image:
    frame = bg.copy()
    # Small proof-only idle: the body breathes one pixel or two while mouth moves.
    bob = round(__import__("math").sin(frame_index / 24 * __import__("math").tau) * args.idle_bob)
    x = args.actor_x - sprite.width // 2
    y = args.actor_bottom_y - sprite.height + bob
    frame.alpha_composite(sprite, (x, y))
    draw_dialogue_panel(frame, args.speaker, args.line)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--background", type=Path, default=Path("ags/room1/background/clerk.png"))
    parser.add_argument("--frames-dir", type=Path, required=True)
    parser.add_argument("--frame-glob", default="talk_face_???.png")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--actor-height", type=int, default=690)
    parser.add_argument("--actor-x", type=int, default=860)
    parser.add_argument("--actor-bottom-y", type=int, default=725)
    parser.add_argument("--idle-bob", type=int, default=3)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--speaker", default="Otto")
    parser.add_argument("--line", default="Whoa. Okay. That is a lot of down there.")
    args = parser.parse_args()

    bg = Image.open(args.background).convert("RGBA")
    bg = letterbox_cover(bg, (1280, 720))
    # Cutscene mood: soften the plate so the dialogue actor owns the frame.
    softened = bg.filter(ImageFilter.GaussianBlur(1.1))
    veil = Image.new("RGBA", softened.size, (24, 16, 12, 74))
    softened.alpha_composite(veil)

    paths = sorted(args.frames_dir.glob(args.frame_glob))
    if not paths:
        raise FileNotFoundError(f"no frames found in {args.frames_dir} matching {args.frame_glob}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    frames: list[Image.Image] = []
    for index, path in enumerate(paths):
        sprite = fit_height(Image.open(path).convert("RGBA"), args.actor_height)
        composed = compose_frame(softened, sprite, index, args)
        composed.save(args.out_dir / f"dialogue_scene_{index:03d}.png")
        frames.append(composed.convert("RGB"))

    frames[0].save(
        args.out_dir / "dialogue_scene_preview.gif",
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / args.fps),
        loop=0,
    )

    cols = 4
    thumb_w = 320
    thumb_h = 180
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + 24)), (35, 24, 20))
    draw = ImageDraw.Draw(sheet)
    for index, frame in enumerate(frames):
        x = (index % cols) * thumb_w
        y = (index // cols) * (thumb_h + 24) + 24
        sheet.paste(frame.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (x, y))
        draw.text((x + 8, y - 18), f"dialogue #{index:02d}", fill=(255, 244, 215))
    sheet.save(args.out_dir / "dialogue_scene_contact.png")

    (args.out_dir / "manifest.json").write_text(json.dumps({
        "background": str(args.background),
        "frames_dir": str(args.frames_dir),
        "frame_count": len(frames),
        "fps": args.fps,
        "actor_height": args.actor_height,
        "actor_position": {"x": args.actor_x, "bottom_y": args.actor_bottom_y},
        "speaker": args.speaker,
        "line": args.line,
        "outputs": ["dialogue_scene_preview.gif", "dialogue_scene_contact.png"],
        "purpose": "Mid-shot dialogue/cutscene proof for texture-bound 3D body plus 2D face-card acting.",
    }, indent=2), encoding="utf-8")
    print(json.dumps({"frames": len(frames), "out": str(args.out_dir)}, indent=2))


if __name__ == "__main__":
    main()
