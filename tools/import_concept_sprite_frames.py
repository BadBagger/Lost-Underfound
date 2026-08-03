#!/usr/bin/env python3
"""Import approved concept-grid frames into registered Act 1 sprite sheets.

This intentionally avoids re-generating character identity. It slices from the
approved pink-background concept grids, removes the pink matte, normalizes each
pose to the existing registration anchors, and writes Forge-ready PNG frames.
"""

from __future__ import annotations

import json
import colorsys
import math
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from collections import deque

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "art" / "act01-production" / "characters-sprite-v2"
SOURCE_OUT = ROOT / "art" / "act01-production" / "source" / "concept-sprite-grids"
QA_OUT = ROOT / "art" / "act01-production" / "qa" / "sprite-v2"


@dataclass(frozen=True)
class SheetSpec:
    name: str
    source: Path
    cols: int
    rows: int
    indices: list[int]
    out_dir: Path
    prefix: str
    canvas: tuple[int, int]
    anchor: tuple[int, int]
    target_height: int
    actor_type: str
    roles: list[str]
    crop_region: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)
    crop_bottom_fraction: float | None = None


def pink_key_alpha(img: Image.Image) -> Image.Image:
    """Remove the pink concept background with a soft matte."""
    rgba = img.convert("RGBA")
    pix = rgba.load()
    w, h = rgba.size

    samples = []
    for x in range(0, w, max(1, w // 24)):
        samples.append(pix[x, 0][:3])
        samples.append(pix[x, h - 1][:3])
    for y in range(0, h, max(1, h // 24)):
        samples.append(pix[0, y][:3])
        samples.append(pix[w - 1, y][:3])
    key = tuple(round(sum(s[i] for s in samples) / len(samples)) for i in range(3))

    out = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    opix = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = pix[x, y]
            d = math.sqrt((r - key[0]) ** 2 + (g - key[1]) ** 2 + (b - key[2]) ** 2)
            hue, sat, val = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            is_magenta_bg = (0.82 <= hue <= 0.96) and sat > 0.38 and val > 0.42
            if is_magenta_bg or d < 42:
                na = 0
            elif d > 105:
                na = a
            else:
                na = round(a * ((d - 38) / 67))
            # Despill the pink edge instead of leaving a halo.
            if na and r > b and r > g:
                r = min(r, round((g + b) / 2 + 45))
            opix[x, y] = (r, g, b, na)
    return out


def keep_main_components(img: Image.Image) -> Image.Image:
    """Drop grid-neighbor fragments after chroma keying.

    The concept grids have some poses close enough that an even cell can clip a
    shoe, antenna, or prop from the row above. Keeping significant components
    only avoids those orphan bits entering production frames.
    """
    alpha = img.getchannel("A")
    w, h = img.size
    seen = bytearray(w * h)
    components: list[tuple[int, tuple[int, int, int, int], list[int]]] = []

    def idx(x: int, y: int) -> int:
        return y * w + x

    for sy in range(h):
        for sx in range(w):
            start = idx(sx, sy)
            if seen[start] or alpha.getpixel((sx, sy)) <= 8:
                seen[start] = 1
                continue
            q: deque[tuple[int, int]] = deque([(sx, sy)])
            seen[start] = 1
            pixels: list[int] = []
            min_x = max_x = sx
            min_y = max_y = sy
            while q:
                x, y = q.popleft()
                p = idx(x, y)
                pixels.append(p)
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < w and 0 <= ny < h:
                        n = idx(nx, ny)
                        if not seen[n]:
                            seen[n] = 1
                            if alpha.getpixel((nx, ny)) > 8:
                                q.append((nx, ny))
            components.append((len(pixels), (min_x, min_y, max_x + 1, max_y + 1), pixels))

    if not components:
        return img
    components.sort(key=lambda item: item[0], reverse=True)
    largest = components[0][0]
    main_bounds = components[0][1]
    expanded_main = (
        max(0, main_bounds[0] - 24),
        max(0, main_bounds[1] - 24),
        min(w, main_bounds[2] + 24),
        min(h, main_bounds[3] + 24),
    )

    def overlaps(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
        return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]

    keep = bytearray(w * h)
    for area, bounds, pixels in components:
        bw = bounds[2] - bounds[0]
        bh = bounds[3] - bounds[1]
        is_main = bounds == main_bounds
        is_near_main = overlaps(bounds, expanded_main)
        if is_main or (is_near_main and (area >= largest * 0.025 and bw > 8 and bh > 8)):
            for p in pixels:
                keep[p] = 1
    out = img.copy()
    opix = out.load()
    for y in range(h):
        for x in range(w):
            if not keep[idx(x, y)]:
                opix[x, y] = (0, 0, 0, 0)
            elif opix[x, y][3] < 42:
                opix[x, y] = (0, 0, 0, 0)
    return out


def alpha_bounds(img: Image.Image) -> tuple[int, int, int, int] | None:
    return img.getchannel("A").getbbox()


def crop_cell(source: Image.Image, spec: SheetSpec, index: int) -> Image.Image:
    col = index % spec.cols
    row = index // spec.cols
    cw = source.width / spec.cols
    ch = source.height / spec.rows
    rx0, ry0, rx1, ry1 = spec.crop_region
    left = round(col * cw + rx0 * cw)
    top = round(row * ch + ry0 * ch)
    right = round(col * cw + rx1 * cw)
    bottom = round(row * ch + ry1 * ch)
    if spec.crop_bottom_fraction is not None:
        bottom = min(bottom, round(top + spec.crop_bottom_fraction * ch))
    return source.crop((left, top, right, bottom))


def normalize(cell: Image.Image, spec: SheetSpec) -> Image.Image:
    keyed = keep_main_components(pink_key_alpha(cell))
    bounds = alpha_bounds(keyed)
    if not bounds:
        raise RuntimeError(f"{spec.name}: empty frame after keying")
    subject = keyed.crop(bounds)
    scale = spec.target_height / max(1, subject.height)
    nw = max(1, round(subject.width * scale))
    nh = max(1, round(subject.height * scale))
    subject = subject.resize((nw, nh), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", spec.canvas, (0, 0, 0, 0))
    x = round(spec.anchor[0] - nw / 2)
    y = round(spec.anchor[1] - nh)
    canvas.alpha_composite(subject, (x, y))
    return canvas


def write_registration(spec: SheetSpec, files: list[str]) -> None:
    frames = []
    for i, file in enumerate(files):
        frame = {
            "file": file,
            "anchor": list(spec.anchor),
            "role": spec.roles[i] if i < len(spec.roles) else f"pose-{i + 1:02d}",
        }
        if i == 0:
            frame["canonical"] = True
            frame["scale_reference"] = [spec.anchor[0], spec.anchor[1] - spec.target_height]
        frames.append(frame)
    data = {
        "sheet": spec.name,
        "actor_type": spec.actor_type,
        "canvas": {"width": spec.canvas[0], "height": spec.canvas[1]},
        "anchor_tolerance_px": 1,
        "frames": frames,
        "approval_state": "concept-grid-import-production-pass",
        "identity_source": str(spec.source.relative_to(ROOT)).replace("\\", "/"),
    }
    (spec.out_dir / "registration.json").write_text(json.dumps(data, indent=2) + "\n")


def contact_sheet(spec: SheetSpec, frames: list[Path]) -> None:
    pad = 24
    label_h = 28
    cols = min(6, len(frames))
    rows = math.ceil(len(frames) / cols)
    w = cols * (spec.canvas[0] + pad) + pad
    h = rows * (spec.canvas[1] + label_h + pad) + pad
    sheet = Image.new("RGBA", (w, h), (255, 72, 202, 255))
    draw = ImageDraw.Draw(sheet)
    for i, frame in enumerate(frames):
        img = Image.open(frame).convert("RGBA")
        x = pad + (i % cols) * (spec.canvas[0] + pad)
        y = pad + (i // cols) * (spec.canvas[1] + label_h + pad)
        sheet.alpha_composite(img, (x, y))
        draw.text((x, y + spec.canvas[1] + 4), spec.roles[i] if i < len(spec.roles) else frame.stem, fill=(40, 18, 32, 255))
    QA_OUT.mkdir(parents=True, exist_ok=True)
    sheet.save(QA_OUT / f"{spec.name}-contact-sheet.png")


def import_sheet(spec: SheetSpec) -> None:
    spec.out_dir.mkdir(parents=True, exist_ok=True)
    for old in spec.out_dir.glob("*.png"):
        old.unlink()
    old_registration = spec.out_dir / "registration.json"
    if old_registration.exists():
        old_registration.unlink()
    source = Image.open(spec.source).convert("RGBA")
    files: list[str] = []
    frame_paths: list[Path] = []
    for out_i, index in enumerate(spec.indices, 1):
        cell = crop_cell(source, spec, index)
        frame = normalize(cell, spec)
        filename = f"{spec.prefix}_{out_i:02d}.png"
        frame.save(spec.out_dir / filename)
        files.append(filename)
        frame_paths.append(spec.out_dir / filename)
    write_registration(spec, files)
    contact_sheet(spec, frame_paths)


def specs() -> Iterable[SheetSpec]:
    concept = ROOT / "art" / "concept-sheets"
    generated = ROOT / "art" / "act01-production" / "source" / "generated-sprite-strips"
    return [
        SheetSpec(
            name="pip-idle",
            source=concept / "act01-idle-72" / "pip-idle-72-grid.png",
            cols=9,
            rows=8,
            indices=[0, 1, 2, 3, 4, 5, 6, 7],
            out_dir=OUT_ROOT / "pip" / "idle",
            prefix="pip_idle",
            canvas=(320, 360),
            anchor=(160, 300),
            target_height=220,
            actor_type="walk-plane",
            roles=["neutral", "breath-in", "breath-full", "small-hand", "blink", "settle", "alert", "thinking"],
        ),
        SheetSpec(
            name="pip-pickup",
            source=concept / "act01-interactions" / "pip-pickup-item-36-grid.png",
            cols=9,
            rows=4,
            indices=[0, 3, 5, 7, 9, 12, 15, 18],
            out_dir=OUT_ROOT / "pip" / "dust-reach",
            prefix="pip_dust",
            canvas=(320, 360),
            anchor=(160, 300),
            target_height=220,
            actor_type="walk-plane",
            roles=["notice-button", "lean-down", "crouch", "reach-contact", "hand-near-button", "grasp", "rise-with-button", "present-button"],
        ),
        SheetSpec(
            name="pip-handoff",
            source=concept / "act01-interactions" / "pip-handoff-old-bottlecap-36-grid.png",
            cols=8,
            rows=4,
            indices=[1, 2, 3, 4, 9, 10],
            out_dir=OUT_ROOT / "pip" / "toll-paid",
            prefix="pip_toll",
            canvas=(320, 360),
            anchor=(160, 300),
            target_height=220,
            actor_type="walk-plane",
            roles=["holds-button", "windup", "extend", "release", "follow-through", "hand-empty"],
            crop_region=(0.0, 0.0, 0.58, 1.0),
        ),
        SheetSpec(
            name="pip-relief",
            source=concept / "act01-interactions" / "pip-handoff-old-bottlecap-36-grid.png",
            cols=8,
            rows=4,
            indices=[25, 28, 29, 30, 31],
            out_dir=OUT_ROOT / "pip" / "relief",
            prefix="pip_relief",
            canvas=(320, 360),
            anchor=(160, 300),
            target_height=220,
            actor_type="walk-plane",
            roles=["tense", "realization", "exhale", "bounce", "grin-settle"],
            crop_region=(0.0, 0.0, 0.58, 1.0),
        ),
        SheetSpec(
            name="bramble-idle",
            source=generated / "bramble-clean-actor-strip.png",
            cols=6,
            rows=1,
            indices=[0, 1, 2, 3, 4, 5],
            out_dir=OUT_ROOT / "bramble" / "idle",
            prefix="bramble_idle",
            canvas=(320, 260),
            anchor=(160, 205),
            target_height=187,
            actor_type="furniture-anchored",
            roles=["idle-neutral", "talk-open", "talk-closed", "inspect", "handoff", "turnaround"],
            crop_region=(0.0, 0.0, 1.0, 1.0),
        ),
        SheetSpec(
            name="bramble-talk",
            source=generated / "bramble-clean-actor-strip.png",
            cols=6,
            rows=1,
            indices=[0, 1, 2, 3, 4, 5],
            out_dir=OUT_ROOT / "bramble" / "talk",
            prefix="bramble_talk",
            canvas=(320, 260),
            anchor=(160, 205),
            target_height=187,
            actor_type="furniture-anchored",
            roles=["idle-neutral", "talk-open", "talk-closed", "inspect", "handoff", "turnaround"],
            crop_region=(0.0, 0.0, 1.0, 1.0),
        ),
        SheetSpec(
            name="old-bottlecap-idle",
            source=concept / "act01-idle-72" / "old-bottlecap-idle-72-grid.png",
            cols=8,
            rows=9,
            indices=[0, 1, 3, 5, 11, 21, 27, 63],
            out_dir=OUT_ROOT / "old-bottlecap" / "idle",
            prefix="old_bottlecap_idle",
            canvas=(320, 260),
            anchor=(160, 210),
            target_height=132,
            actor_type="furniture-anchored",
            roles=["neutral-heavy", "slow-rock", "blink", "eye-shift", "judgment", "tilt", "breath-out", "return-neutral"],
        ),
        SheetSpec(
            name="old-bottlecap-toll-refused",
            source=concept / "act01-idle-72" / "old-bottlecap-idle-72-grid.png",
            cols=8,
            rows=9,
            indices=[0, 8, 13, 29, 63],
            out_dir=OUT_ROOT / "old-bottlecap" / "toll-refused",
            prefix="old_bottlecap_refuse",
            canvas=(320, 260),
            anchor=(160, 210),
            target_height=132,
            actor_type="furniture-anchored",
            roles=["idle", "unimpressed", "dismissive-look", "turn-away", "return-idle"],
        ),
        SheetSpec(
            name="old-bottlecap-toll-paid",
            source=concept / "act01-idle-72" / "old-bottlecap-idle-72-grid.png",
            cols=8,
            rows=9,
            indices=[64, 66, 67, 68, 69, 70, 71],
            out_dir=OUT_ROOT / "old-bottlecap" / "toll-paid",
            prefix="old_bottlecap_paid",
            canvas=(320, 260),
            anchor=(160, 210),
            target_height=132,
            actor_type="furniture-anchored",
            roles=["notices-button", "lean-in", "accepts-button", "inspects-held", "consideration", "approval", "settle"],
            crop_region=(0.1, 0.0, 0.9, 1.0),
        ),
        SheetSpec(
            name="old-bottlecap-talk",
            source=concept / "act01-idle-72" / "old-bottlecap-idle-72-grid.png",
            cols=8,
            rows=9,
            indices=[0, 2, 10, 14],
            out_dir=OUT_ROOT / "old-bottlecap" / "talk",
            prefix="old_bottlecap_talk",
            canvas=(320, 260),
            anchor=(160, 210),
            target_height=132,
            actor_type="furniture-anchored",
            roles=["neutral", "mouth-open", "tiny-emphasis", "close"],
        ),
        SheetSpec(
            name="scuttle-dash",
            source=concept / "act01-idle-72" / "scuttle-idle-72-grid.png",
            cols=9,
            rows=8,
            indices=[0, 5, 6, 7, 8],
            out_dir=OUT_ROOT / "scuttle" / "dash",
            prefix="scuttle_dash",
            canvas=(180, 160),
            anchor=(90, 120),
            target_height=77,
            actor_type="walk-plane",
            roles=["ready", "launch", "smear-roll", "landing", "skitter-off"],
        ),
    ]


def main() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    SOURCE_OUT.mkdir(parents=True, exist_ok=True)
    for source in {
        spec.source for spec in specs()
    }:
        shutil.copy2(source, SOURCE_OUT / source.name)
    for spec in specs():
        import_sheet(spec)
        print(f"imported {spec.name} -> {spec.out_dir.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
