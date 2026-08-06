#!/usr/bin/env python3
"""Compose texture-only and face-overlay sprite proofs on an AGS room plate."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw


def alpha_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    bbox = img.getchannel("A").getbbox()
    if not bbox:
        raise ValueError("frame has no visible alpha")
    return bbox


def fit_actor_height(img: Image.Image, target_height: int) -> Image.Image:
    bbox = alpha_bbox(img)
    crop = img.crop(bbox)
    scale = target_height / crop.height
    size = (max(1, round(crop.width * scale)), target_height)
    return crop.resize(size, Image.Resampling.LANCZOS)


def frame_paths(path: Path, pattern: str) -> list[Path]:
    paths = sorted(path.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"no frames in {path} matching {pattern!r}")
    return paths


def composite_frame(plate: Image.Image, sprite: Image.Image, foot: tuple[int, int]) -> Image.Image:
    canvas = plate.copy()
    x = foot[0] - sprite.width // 2
    y = foot[1] - sprite.height
    canvas.alpha_composite(sprite, (x, y))
    return canvas


def save_strip(frames: list[Image.Image], path: Path, label: str) -> None:
    cols = min(4, len(frames))
    rows = math.ceil(len(frames) / cols)
    thumb_w = 320
    thumb_h = 180
    sheet = Image.new("RGBA", (cols * thumb_w, rows * (thumb_h + 26)), (42, 29, 24, 255))
    draw = ImageDraw.Draw(sheet)
    for index, frame in enumerate(frames):
        thumb = frame.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (index % cols) * thumb_w
        y = (index // cols) * (thumb_h + 26) + 26
        sheet.alpha_composite(thumb, (x, y))
        draw.text((x + 8, y - 20), f"{label} #{index:02d}", fill=(255, 244, 215, 255))
    sheet.save(path)


def save_side_by_side(texture_frames: list[Image.Image], overlay_frames: list[Image.Image], path: Path) -> None:
    count = min(len(texture_frames), len(overlay_frames), 6)
    thumb_w = 360
    thumb_h = 203
    sheet = Image.new("RGBA", (thumb_w * 2, (thumb_h + 28) * count), (42, 29, 24, 255))
    draw = ImageDraw.Draw(sheet)
    for index in range(count):
        y = index * (thumb_h + 28) + 28
        left = texture_frames[index].resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        right = overlay_frames[index].resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.alpha_composite(left, (0, y))
        sheet.alpha_composite(right, (thumb_w, y))
        draw.text((8, y - 20), f"texture-only #{index:02d}", fill=(255, 244, 215, 255))
        draw.text((thumb_w + 8, y - 20), f"face-overlay #{index:02d}", fill=(255, 244, 215, 255))
    sheet.save(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plate", default=Path("ags/room1/background/discovery.png"), type=Path)
    parser.add_argument("--texture-frames", default=Path("spikes/sprite_render/socket_walk_render/frames_raw"), type=Path)
    parser.add_argument("--texture-glob", default="walk_raw_???.png")
    parser.add_argument("--overlay-frames", default=Path("spikes/sprite_render/socket_face_overlay_proof"), type=Path)
    parser.add_argument("--overlay-glob", default="talk_face_???.png")
    parser.add_argument("--out-dir", default=Path("spikes/sprite_render/gameplay_scale_proof"), type=Path)
    parser.add_argument("--actor-height", type=int, default=230)
    parser.add_argument("--foot-x", type=int, default=660)
    parser.add_argument("--foot-y", type=int, default=666)
    parser.add_argument("--fps", type=int, default=12)
    args = parser.parse_args()

    plate = Image.open(args.plate).convert("RGBA")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    texture_paths = frame_paths(args.texture_frames, args.texture_glob)
    overlay_paths = frame_paths(args.overlay_frames, args.overlay_glob)
    count = min(len(texture_paths), len(overlay_paths))

    texture_frames = []
    overlay_frames = []
    for index in range(count):
        texture_sprite = fit_actor_height(Image.open(texture_paths[index]).convert("RGBA"), args.actor_height)
        overlay_sprite = fit_actor_height(Image.open(overlay_paths[index]).convert("RGBA"), args.actor_height)
        texture_frames.append(composite_frame(plate, texture_sprite, (args.foot_x, args.foot_y)))
        overlay_frames.append(composite_frame(plate, overlay_sprite, (args.foot_x, args.foot_y)))

    save_strip(texture_frames, args.out_dir / "texture_only_contact.png", "texture")
    save_strip(overlay_frames, args.out_dir / "face_overlay_contact.png", "overlay")
    save_side_by_side(texture_frames, overlay_frames, args.out_dir / "texture_vs_overlay_contact.png")

    texture_frames[0].save(
        args.out_dir / "texture_only_preview.gif",
        save_all=True,
        append_images=texture_frames[1:],
        duration=round(1000 / args.fps),
        loop=0,
    )
    overlay_frames[0].save(
        args.out_dir / "face_overlay_preview.gif",
        save_all=True,
        append_images=overlay_frames[1:],
        duration=round(1000 / args.fps),
        loop=0,
    )
    (args.out_dir / "manifest.json").write_text(json.dumps({
        "plate": str(args.plate),
        "actor_height": args.actor_height,
        "foot": [args.foot_x, args.foot_y],
        "frame_count": count,
        "outputs": [
            "texture_only_contact.png",
            "face_overlay_contact.png",
            "texture_vs_overlay_contact.png",
            "texture_only_preview.gif",
            "face_overlay_preview.gif",
        ],
        "purpose": "Judge whether face overlay is worth production work at true gameplay scale on the approved AGS plate.",
    }, indent=2), encoding="utf-8")
    print(json.dumps({"frames": count, "actor_height": args.actor_height, "out": str(args.out_dir)}, indent=2))


if __name__ == "__main__":
    main()
