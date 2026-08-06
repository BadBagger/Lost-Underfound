#!/usr/bin/env python3
"""Promote selected Meshy proof frames into Act 1 runtime production folders."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
QA_ROOT = ROOT / "art" / "act01-production" / "qa"


@dataclass(frozen=True)
class Promotion:
    character: str
    state: str
    source_dir: Path
    source_prefix: str
    dest_dir: Path
    dest_prefix: str
    frame_indices: tuple[int, ...]
    actor_type: str
    fps: int
    loop: bool
    contact_sheet: Path | None = None


PROMOTIONS = [
    Promotion(
        character="pip",
        state="idle",
        source_dir=ROOT / "spikes/sprite_render/input/meshy_cast/pip/head_shoulders_biped_export_4_walk_proof/out",
        source_prefix="pip_walk_export4",
        dest_dir=ROOT / "art/act01-production/characters/pip/meshy-current/idle",
        dest_prefix="pip_meshy_idle",
        frame_indices=(0, 1) * 6,
        actor_type="walk-plane",
        fps=8,
        loop=True,
        contact_sheet=ROOT / "spikes/sprite_render/input/meshy_cast/pip/head_shoulders_biped_export_4_walk_proof/out/pip_walk_export4_contact.png",
    ),
    Promotion(
        character="pip",
        state="walk",
        source_dir=ROOT / "spikes/sprite_render/input/meshy_cast/pip/head_shoulders_biped_export_4_walk_proof/out",
        source_prefix="pip_walk_export4",
        dest_dir=ROOT / "art/act01-production/characters/pip/meshy-current/walk",
        dest_prefix="pip_meshy_walk",
        frame_indices=tuple(range(12)),
        actor_type="walk-plane",
        fps=12,
        loop=True,
        contact_sheet=ROOT / "spikes/sprite_render/input/meshy_cast/pip/head_shoulders_biped_export_4_walk_proof/out/pip_walk_export4_contact.png",
    ),
    Promotion(
        character="pip",
        state="talk",
        source_dir=ROOT / "spikes/sprite_render/input/meshy_cast/pip/head_shoulders_biped_export_4_walk_proof/out",
        source_prefix="pip_walk_export4",
        dest_dir=ROOT / "art/act01-production/characters/pip/meshy-current/talk",
        dest_prefix="pip_meshy_talk",
        frame_indices=(0, 1) * 6,
        actor_type="walk-plane",
        fps=12,
        loop=True,
        contact_sheet=ROOT / "spikes/sprite_render/input/meshy_cast/pip/head_shoulders_biped_export_4_walk_proof/out/pip_walk_export4_contact.png",
    ),
    Promotion(
        character="pip",
        state="dust-reach",
        source_dir=ROOT / "spikes/sprite_render/input/meshy_cast/pip/story_action_proofs_act23_export4/marble_search/out",
        source_prefix="pip_marble_search",
        dest_dir=ROOT / "art/act01-production/characters/pip/meshy-current/dust-reach",
        dest_prefix="pip_meshy_dust",
        frame_indices=tuple(range(14)),
        actor_type="walk-plane",
        fps=12,
        loop=False,
        contact_sheet=ROOT / "spikes/sprite_render/input/meshy_cast/pip/story_action_proofs_act23_export4/marble_search/out/pip_marble_search_contact.png",
    ),
    Promotion(
        character="pip",
        state="toll-paid",
        source_dir=ROOT / "spikes/sprite_render/input/meshy_cast/pip/story_action_proofs_act23_export4/mend_reach/out",
        source_prefix="pip_mend_reach",
        dest_dir=ROOT / "art/act01-production/characters/pip/meshy-current/toll-paid",
        dest_prefix="pip_meshy_toll",
        frame_indices=tuple(range(10)),
        actor_type="walk-plane",
        fps=12,
        loop=False,
        contact_sheet=ROOT / "spikes/sprite_render/input/meshy_cast/pip/story_action_proofs_act23_export4/mend_reach/out/pip_mend_reach_contact.png",
    ),
    Promotion(
        character="old-bottlecap",
        state="idle",
        source_dir=ROOT / "spikes/sprite_render/input/meshy_cast/old_bottlecap/rig_idle_proof/out",
        source_prefix="old_bottlecap_idle_rig",
        dest_dir=ROOT / "art/act01-production/characters/old-bottlecap/meshy-current/idle",
        dest_prefix="old_bottlecap_meshy_idle",
        frame_indices=tuple(range(24)),
        actor_type="furniture-anchored",
        fps=12,
        loop=True,
        contact_sheet=ROOT / "spikes/sprite_render/input/meshy_cast/old_bottlecap/rig_idle_proof/out/old_bottlecap_idle_rig_contact.png",
    ),
    Promotion(
        character="old-bottlecap",
        state="toll-refused",
        source_dir=ROOT / "spikes/sprite_render/input/meshy_cast/old_bottlecap/admission_stillness_break_proof/out",
        source_prefix="old_bottlecap_admission_stillness_break",
        dest_dir=ROOT / "art/act01-production/characters/old-bottlecap/meshy-current/toll-refused",
        dest_prefix="old_bottlecap_meshy_refuse",
        frame_indices=(0, 3, 6, 9, 12),
        actor_type="furniture-anchored",
        fps=8,
        loop=False,
        contact_sheet=ROOT / "spikes/sprite_render/input/meshy_cast/old_bottlecap/admission_stillness_break_proof/out/old_bottlecap_admission_stillness_break_contact.png",
    ),
    Promotion(
        character="old-bottlecap",
        state="toll-paid",
        source_dir=ROOT / "spikes/sprite_render/input/meshy_cast/old_bottlecap/admission_stillness_break_proof/out",
        source_prefix="old_bottlecap_admission_stillness_break",
        dest_dir=ROOT / "art/act01-production/characters/old-bottlecap/meshy-current/toll-paid",
        dest_prefix="old_bottlecap_meshy_paid",
        frame_indices=(0, 3, 6, 9, 12, 15, 17),
        actor_type="furniture-anchored",
        fps=8,
        loop=False,
        contact_sheet=ROOT / "spikes/sprite_render/input/meshy_cast/old_bottlecap/admission_stillness_break_proof/out/old_bottlecap_admission_stillness_break_contact.png",
    ),
    Promotion(
        character="scuttle",
        state="dash",
        source_dir=ROOT / "spikes/sprite_render/input/meshy_cast/scuttle/dash_rig_proof/out",
        source_prefix="scuttle_dash_rig",
        dest_dir=ROOT / "art/act01-production/characters/scuttle/meshy-current/dash",
        dest_prefix="scuttle_meshy_dash",
        frame_indices=tuple(range(6)),
        actor_type="walk-plane",
        fps=16,
        loop=False,
        contact_sheet=ROOT / "spikes/sprite_render/input/meshy_cast/scuttle/dash_rig_proof/out/scuttle_dash_rig_contact.png",
    ),
]

PIP_STYLE_STATES = {"idle", "walk", "talk", "dust-reach", "toll-paid"}


def style_pip_frame(path: Path) -> None:
    """Seat Pip's clean 3D render into the warmer painted room style."""
    image = Image.open(path).convert("RGBA")
    rgba = np.asarray(image).copy()
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0
    mask = alpha > 0.02
    if not np.any(mask):
        image.save(path)
        return

    rgb = rgba[:, :, :3].astype(np.float32)
    luminance = (
        rgb[:, :, 0] * 0.2126
        + rgb[:, :, 1] * 0.7152
        + rgb[:, :, 2] * 0.0722
    )[:, :, None]

    # The rooms are warm, painterly, and lower contrast than the raw Meshy pass.
    # Pull saturation and brightness down, then bias the character into the room light.
    rgb = luminance + (rgb - luminance) * 0.78
    warm_bias = np.array([40.0, 25.0, 15.0], dtype=np.float32)
    rgb = rgb * 0.82 + warm_bias

    # Keep the costume blue but stop the cyan belly and lit hoodie from glowing.
    blueish = mask & (rgb[:, :, 2] > rgb[:, :, 0] * 1.18) & (rgb[:, :, 2] > rgb[:, :, 1] * 1.02)
    rgb[blueish] = rgb[blueish] * np.array([0.88, 0.86, 0.76], dtype=np.float32)
    cyan = mask & (rgb[:, :, 1] > 120) & (rgb[:, :, 2] > 120) & (rgb[:, :, 0] < 120)
    rgb[cyan] = rgb[cyan] * np.array([0.86, 0.82, 0.74], dtype=np.float32)

    # Add a subtle shared-paper texture so Pip is not a perfectly smooth cutout.
    yy, xx = np.indices(alpha.shape)
    grain = (
        ((xx * 17 + yy * 31) % 11).astype(np.float32)
        + ((xx * 7 + yy * 13) % 5).astype(np.float32)
    )
    grain = (grain - grain.mean()) * 0.75
    rgb[mask] = rgb[mask] + grain[mask, None]

    rgba[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    base = Image.fromarray(rgba, "RGBA")

    alpha_image = base.getchannel("A")
    outer = alpha_image.filter(ImageFilter.MaxFilter(7))
    inner = alpha_image.filter(ImageFilter.MinFilter(5))
    outer_ring = ImageChops.subtract(outer, alpha_image)
    inner_ring = ImageChops.subtract(alpha_image, inner)

    outline = Image.new("RGBA", base.size, (22, 12, 13, 0))
    outline.putalpha(outer_ring.point(lambda value: min(230, int(value * 1.15))))
    seated = Image.alpha_composite(outline, base)

    inner_line = Image.new("RGBA", base.size, (28, 16, 13, 0))
    inner_line.putalpha(inner_ring.point(lambda value: min(70, int(value * 0.55))))
    seated = Image.alpha_composite(seated, inner_line)

    seated.save(path)


def write_contact_sheet(frame_paths: list[Path], out_path: Path, anchor: tuple[int, int] = (256, 486)) -> None:
    if not frame_paths:
        return
    first = Image.open(frame_paths[0]).convert("RGBA")
    cell_w, cell_h = first.size
    cols = min(6, len(frame_paths))
    rows = (len(frame_paths) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell_w, rows * cell_h), (128, 128, 128, 255))
    draw = ImageDraw.Draw(sheet)
    for index, frame_path in enumerate(frame_paths):
        frame = Image.open(frame_path).convert("RGBA")
        x = (index % cols) * cell_w
        y = (index // cols) * cell_h
        sheet.alpha_composite(frame, (x, y))
        ax, ay = x + anchor[0], y + anchor[1]
        draw.line((ax - 9, ay, ax + 9, ay), fill=(255, 0, 255, 255), width=1)
        draw.line((ax, ay - 9, ax, ay + 9), fill=(255, 0, 255, 255), width=1)
        draw.text((x + 8, y + 8), f"{index + 1:02d}", fill=(255, 0, 255, 255))
    sheet.save(out_path)


def source_frame(promotion: Promotion, frame_index: int) -> Path:
    return promotion.source_dir / f"{promotion.source_prefix}_{frame_index:03d}.png"


def dest_frame(promotion: Promotion, output_index: int) -> Path:
    return promotion.dest_dir / f"{promotion.dest_prefix}_{output_index:02d}.png"


def registration_for(promotion: Promotion) -> dict:
    frames = []
    anchor = [256, 486]
    scale_top_y = 126
    for output_index, _source_index in enumerate(promotion.frame_indices, start=1):
        frames.append(
            {
                "file": dest_frame(promotion, output_index).name,
                "anchor": anchor,
                "role": promotion.state,
                "canonical": output_index == 1,
                **({"scale_reference": [anchor[0], scale_top_y]} if output_index == 1 else {}),
            }
        )
    return {
        "sheet": f"{promotion.character}-{promotion.state}-meshy-current",
        "actor_type": promotion.actor_type,
        "approval_state": "provisional-meshy-runtime-proof",
        "canvas": {"width": 512, "height": 512},
        "anchor_contract": "All promoted Meshy runtime frames share the fixed 512 canvas and bottom-center anchor from the sprite alignment pass.",
        "frames": frames,
    }


def main() -> int:
    QA_ROOT.mkdir(parents=True, exist_ok=True)
    promoted = 0
    for promotion in PROMOTIONS:
        promotion.dest_dir.mkdir(parents=True, exist_ok=True)
        written_frames = []
        for output_index, source_index in enumerate(promotion.frame_indices, start=1):
            source = source_frame(promotion, source_index)
            if not source.exists():
                raise SystemExit(f"missing source frame: {source}")
            target = dest_frame(promotion, output_index)
            shutil.copyfile(source, target)
            if promotion.character == "pip" and promotion.state in PIP_STYLE_STATES:
                style_pip_frame(target)
            written_frames.append(target)
            promoted += 1
        (promotion.dest_dir / "registration.json").write_text(
            json.dumps(registration_for(promotion), indent=2) + "\n",
            encoding="utf-8",
        )
        if promotion.character == "pip" and promotion.state in PIP_STYLE_STATES:
            write_contact_sheet(
                written_frames,
                QA_ROOT / f"{promotion.character}-{promotion.state}-meshy-current-contact-sheet.png",
            )
        elif promotion.contact_sheet and promotion.contact_sheet.exists():
            shutil.copyfile(
                promotion.contact_sheet,
                QA_ROOT / f"{promotion.character}-{promotion.state}-meshy-current-contact-sheet.png",
            )
        print(f"promoted {promotion.character}/{promotion.state}: {len(promotion.frame_indices)} frame(s)")
    print(f"promoted {promoted} total frame(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
