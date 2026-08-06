#!/usr/bin/env python3
"""Curate usable user prop art-intake candidates after crop review."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
AUTO_ROOT = ROOT / "spikes" / "sprite_render" / "user_prop_art_intake_auto"
AUTO_CROPS = AUTO_ROOT / "candidates"
OUT_ROOT = ROOT / "spikes" / "sprite_render" / "user_prop_art_curated"
OUT_CROPS = OUT_ROOT / "accepted_review_crops"


ACCEPT = {
    "thread_spool": "inventory_props_00.png",
    "button_dark_two_hole": "inventory_props_01.png",
    "old_bottlecap_token": "inventory_props_02.png",
    "needle": "inventory_props_03.png",
    "threaded_needle": "inventory_props_04.png",
    "intake_parcel": "inventory_props_05.png",
    "founders_ledger_closed": "inventory_props_06.png",
    "annotated_evidence_candidate": "inventory_props_07.png",
    "pips_marble_broken_candidate": "inventory_props_08.png",
    "clerk_counter_station_reference": "room_props_00.png",
    "notice_board_reference": "room_props_01.png",
    "station_and_annex_door_reference": "room_props_02.png",
    "scene_object_sheet_reference": "scene_objects_00.png",
}


REJECTED = [
    "spikes/sprite_render/user_prop_art_intake/",
    "marbles_00 grouped all five marbles together; use original marble sheet and hand separate candidates.",
    "glass/cobweb/dust partial transparency cannot be recovered cleanly from RGB gray-background sheets.",
]


def ensure(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_contact(items: list[dict], path: Path) -> None:
    thumb = (220, 170)
    cols = 4
    rows = (len(items) + cols - 1) // cols
    contact = Image.new("RGBA", (cols * thumb[0], rows * (thumb[1] + 42)), (128, 128, 128, 255))
    draw = ImageDraw.Draw(contact)
    for i, item in enumerate(items):
        img = Image.open(item["path"]).convert("RGBA")
        x = (i % cols) * thumb[0]
        y = (i // cols) * (thumb[1] + 42) + 38
        scale = min((thumb[0] - 14) / img.width, (thumb[1] - 10) / img.height, 1.0)
        resized = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.Resampling.LANCZOS)
        contact.alpha_composite(resized, (x + (thumb[0] - resized.width) // 2, y + (thumb[1] - resized.height) // 2))
        draw.text((x + 6, y - 32), item["name"][:28], fill=(255, 244, 215, 255))
        draw.text((x + 6, y - 17), item["source_crop"], fill=(230, 220, 200, 255))
    contact.save(path)


def main() -> None:
    ensure(OUT_CROPS)
    items: list[dict] = []
    for name, filename in ACCEPT.items():
        src = AUTO_CROPS / filename
        if not src.exists():
            raise FileNotFoundError(src)
        dest = OUT_CROPS / f"{name}.png"
        shutil.copy2(src, dest)
        with Image.open(dest) as img:
            size = list(img.size)
        items.append(
            {
                "name": name,
                "source_crop": filename,
                "path": str(dest),
                "size": size,
                "admission_status": "review crop only; final alpha cleanup and registration still required",
            }
        )
    contact = OUT_ROOT / "curated_user_prop_intake_contact.png"
    save_contact(items, contact)
    manifest = {
        "role": "curated subset of user-provided prop art intake",
        "status": "partial_accept_for_review",
        "accepted_review_crops": items,
        "rejected_or_needs_manual": REJECTED,
        "next_step": "Use accepted review crops as visual source candidates; hand-separate marble candidates from original sheet and redo alpha cleanup for glass/cobweb/dust.",
        "contact_sheet": str(contact),
    }
    (OUT_ROOT / "curated_user_prop_intake_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"accepted": len(items), "contact": str(contact)}, indent=2))


if __name__ == "__main__":
    main()
