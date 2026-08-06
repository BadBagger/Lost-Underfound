#!/usr/bin/env python3
"""Build simple timing proofs for environment and prop animation beats.

These are not final paintings. They are registration-locked proof sheets for
door/lighting/shake timing so the story beats can be reviewed before final art.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "spikes" / "sprite_render" / "environment_prop_proofs"
CANVAS = (512, 288)
FPS = 12


def ensure(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_contact(frames: list[Image.Image], path: Path) -> None:
    cols = 6
    rows = math.ceil(len(frames) / cols)
    contact = Image.new("RGBA", (cols * CANVAS[0], rows * (CANVAS[1] + 22)), (126, 126, 126, 255))
    draw = ImageDraw.Draw(contact)
    for index, frame in enumerate(frames):
        x = (index % cols) * CANVAS[0]
        y = (index // cols) * (CANVAS[1] + 22) + 22
        contact.alpha_composite(frame, (x, y))
        draw.text((x + 6, y - 18), f"{index:02d}", fill=(255, 244, 215, 255))
    contact.save(path)


def save_gif(frames: list[Image.Image], path: Path) -> None:
    duration = round(1000 / FPS)
    flattened: list[Image.Image] = []
    for frame in frames:
        bg = Image.new("RGBA", frame.size, (84, 76, 70, 255))
        bg.alpha_composite(frame)
        flattened.append(bg.convert("P", palette=Image.Palette.ADAPTIVE))
    flattened[0].save(path, save_all=True, append_images=flattened[1:], duration=duration, loop=0, disposal=2)


def door_frame(open_t: float, settle: float) -> Image.Image:
    img = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark Annex opening stays registered; the slab moves/rotates over it.
    opening = (165, 34, 347, 260)
    draw.rounded_rectangle(opening, radius=12, fill=(18, 15, 17, 255), outline=(52, 37, 30, 255), width=8)
    draw.rectangle((184, 48, 328, 247), fill=(10, 9, 12, 255))

    # Heavy door slab pivots left with a small overshoot, then settles.
    pivot_x, pivot_y = opening[0] + 9, opening[1] + 8
    angle = -78 * open_t + 8 * settle
    slab = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    sd = ImageDraw.Draw(slab)
    sd.rounded_rectangle((opening[0] + 8, opening[1] + 10, opening[2] - 8, opening[3] - 8), radius=10, fill=(92, 62, 44, 255), outline=(24, 16, 13, 255), width=5)
    for y in range(opening[1] + 28, opening[3] - 22, 34):
        sd.line((opening[0] + 24, y, opening[2] - 24, y + 6), fill=(52, 34, 25, 255), width=3)
    sd.ellipse((opening[2] - 44, 139, opening[2] - 26, 157), fill=(178, 136, 72, 255), outline=(32, 22, 17, 255), width=3)
    rotated = slab.rotate(angle, center=(pivot_x, pivot_y), resample=Image.Resampling.BICUBIC)
    img.alpha_composite(rotated)

    # Dust edge puffs are timing hints, not final particle art.
    puff_alpha = int(120 * max(0.0, math.sin(open_t * math.pi)))
    if puff_alpha:
        puff = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        pd = ImageDraw.Draw(puff)
        for i in range(7):
            px = 174 + i * 25
            py = 248 + math.sin(i) * 5
            pd.ellipse((px - 7, py - 4, px + 9, py + 6), fill=(186, 168, 130, puff_alpha))
        puff = puff.filter(ImageFilter.GaussianBlur(4))
        img.alpha_composite(puff)
    return img


def build_annex_open() -> dict:
    out = OUT_ROOT / "annex_door_open"
    ensure(out)
    keys = [
        (0.00, 0.00, "closed hold"),
        (0.00, 0.00, "decision hold"),
        (0.05, 0.00, "clunk anticipation"),
        (0.20, 0.00, "first heavy move"),
        (0.42, 0.00, "mid swing"),
        (0.68, 0.00, "weight carries"),
        (0.92, 0.00, "near open"),
        (1.08, 0.00, "overshoot"),
        (0.98, 0.45, "settle back"),
        (1.00, 1.00, "open hold"),
        (1.00, 1.00, "open hold"),
        (1.00, 1.00, "open hold"),
    ]
    frames = [door_frame(open_t, settle) for open_t, settle, _ in keys]
    for index, frame in enumerate(frames):
        frame.save(out / f"annex_door_open_{index:03d}.png")
    save_contact(frames, out / "annex_door_open_contact.png")
    save_gif(frames, out / "annex_door_open_preview.gif")
    manifest = {
        "name": "annex_door_open",
        "frame_count": len(frames),
        "fps": FPS,
        "canvas": list(CANVAS),
        "role": "timing proof only; final Annex door painting must replace this drawing",
        "timing_notes": [note for _, _, note in keys],
        "warnings": [],
    }
    (out / "annex_door_open_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest | {"path": str(out)}


def tremor_frame(intensity: float, fade: float, label: str) -> Image.Image:
    img = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    warm = int(80 * intensity * fade)
    cool = int(70 * (1.0 - fade) * intensity)
    if warm:
        draw.rectangle((0, 0, CANVAS[0], CANVAS[1]), fill=(255, 215, 116, warm))
    if cool:
        draw.rectangle((0, 0, CANVAS[0], CANVAS[1]), fill=(48, 72, 95, cool))
    amp = 5 + round(12 * intensity)
    for i in range(9):
        x = 54 + i * 51 + math.sin(i * 1.7) * amp
        y = 48 + math.cos(i * 0.9) * amp * 0.5
        draw.line((x - 8, y, x + 8, y + 3), fill=(245, 231, 188, int(80 * intensity)), width=2)
    draw.text((12, 12), label, fill=(255, 244, 215, 180))
    return img


def build_tremor(name: str, intensity: float) -> dict:
    out = OUT_ROOT / name
    ensure(out)
    frames: list[Image.Image] = []
    notes: list[str] = []
    total = 18
    for i in range(total):
        t = i / (total - 1)
        envelope = math.sin(t * math.pi)
        flicker = 0.55 + 0.45 * math.sin(i * 2.35)
        frame_intensity = intensity * envelope * flicker
        frames.append(tremor_frame(frame_intensity, 1.0 - t * 0.35, name.replace("_", " ")))
        notes.append(f"envelope={envelope:.2f}, flicker={flicker:.2f}")
    for index, frame in enumerate(frames):
        frame.save(out / f"{name}_{index:03d}.png")
    save_contact(frames, out / f"{name}_contact.png")
    save_gif(frames, out / f"{name}_preview.gif")
    manifest = {
        "name": name,
        "frame_count": len(frames),
        "fps": FPS,
        "canvas": list(CANVAS),
        "role": "transparent full-screen overlay timing proof; draw over the finished room, not baked into background art",
        "intensity": intensity,
        "timing_notes": notes,
        "warnings": [],
    }
    (out / f"{name}_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest | {"path": str(out)}


def main() -> None:
    ensure(OUT_ROOT)
    results = [
        build_annex_open(),
        build_tremor("first_tremor_overlay", 0.45),
        build_tremor("roar_arrives_overlay", 1.00),
        build_tremor("roar_passed_overlay", 0.35),
    ]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
