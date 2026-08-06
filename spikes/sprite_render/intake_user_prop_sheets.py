#!/usr/bin/env python3
"""Slice user-provided prop/source sheets into named art-intake candidates.

The input sheets are RGB images on gray backgrounds, not authored alpha plates.
This script preserves the original sheets, creates cropped candidate PNGs, and
uses a conservative gray-background key only for intake review.
"""

from __future__ import annotations

import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "spikes" / "sprite_render" / "user_prop_art_intake"
SOURCE_DIR = OUT_ROOT / "source_sheets"
CROP_DIR = OUT_ROOT / "crops"

SOURCES = {
    "marble_candidates_sheet": Path(r"C:\Users\KyleB\Downloads\Codex Image Aug 5, 2026, 07_24_26 PM.png"),
    "room_prop_sheet": Path(r"C:\Users\KyleB\Downloads\Codex Image Aug 5, 2026, 07_23_22 PM.png"),
    "inventory_prop_sheet": Path(r"C:\Users\KyleB\Downloads\Codex Image Aug 5, 2026, 07_22_36 PM.png"),
    "scene_object_sheet": Path(r"C:\Users\KyleB\Downloads\Codex Image Aug 5, 2026, 07_22_33 PM.png"),
}


@dataclass(frozen=True)
class Crop:
    source: str
    name: str
    box: tuple[int, int, int, int]
    note: str
    alpha_tolerance: int = 34


CROPS = [
    # Marble candidates: five visually distinct candidates for Act 3.
    Crop("marble_candidates_sheet", "marble_galaxy_candidate", (20, 405, 320, 795), "wrong candidate: galaxy swirl"),
    Crop("marble_candidates_sheet", "marble_radiator_tag_candidate", (335, 250, 635, 675), "wrong candidate: radiator tag"),
    Crop("marble_candidates_sheet", "marble_lopsided_star_candidate", (635, 440, 890, 725), "correct/near-correct star-mark candidate; review whether this is nick or scratch"),
    Crop("marble_candidates_sheet", "marble_flawless_candidate", (900, 315, 1195, 645), "wrong candidate: clear/flawless", alpha_tolerance=0),
    Crop("marble_candidates_sheet", "marble_broken_decoy_candidate", (1205, 450, 1495, 760), "wrong candidate: broken shell/dust interior"),
    # Inventory and puzzle items.
    Crop("inventory_prop_sheet", "button_dark_two_hole", (45, 155, 340, 360), "Act 1/prop button candidate"),
    Crop("inventory_prop_sheet", "old_bottlecap_token", (410, 135, 710, 355), "bottlecap/button standard token candidate"),
    Crop("inventory_prop_sheet", "thread_spool", (785, 105, 1135, 420), "thread item candidate"),
    Crop("inventory_prop_sheet", "needle", (40, 455, 365, 790), "needle item candidate"),
    Crop("inventory_prop_sheet", "threaded_needle", (420, 455, 720, 785), "threaded needle combine-result candidate"),
    Crop("inventory_prop_sheet", "intake_parcel", (800, 445, 1210, 805), "intake parcel item candidate"),
    Crop("inventory_prop_sheet", "founders_ledger_closed", (15, 850, 390, 1235), "founder's ledger closed candidate"),
    Crop("inventory_prop_sheet", "pips_marble_broken_candidate", (545, 845, 810, 1215), "marble candidate from inventory sheet"),
    Crop("inventory_prop_sheet", "annotated_evidence_candidate", (855, 865, 1235, 1235), "combined parcel/ledger/evidence candidate"),
    # Room props / set pieces.
    Crop("room_prop_sheet", "clerk_counter_station_candidate", (20, 95, 650, 430), "desk/counter station candidate; includes dressing"),
    Crop("room_prop_sheet", "notice_board_candidate", (760, 95, 1485, 430), "notice board candidate"),
    Crop("room_prop_sheet", "bottlecap_bramble_booths_candidate", (20, 500, 610, 960), "NPC booths/stations candidate"),
    Crop("room_prop_sheet", "annex_door_closed_candidate", (665, 505, 1070, 980), "Annex door closed candidate"),
    Crop("room_prop_sheet", "annex_door_open_candidate", (1100, 505, 1515, 980), "Annex door open candidate"),
    Crop("scene_object_sheet", "dust_button_hidden", (40, 70, 390, 300), "dust clump with hidden button"),
    Crop("scene_object_sheet", "dust_clump_open", (420, 55, 750, 315), "disturbed dust clump"),
    Crop("scene_object_sheet", "cubby_wall_candidate", (800, 20, 1515, 410), "cubby wall candidate"),
    Crop("scene_object_sheet", "gate_closed_candidate", (20, 365, 390, 635), "gate/grate closed candidate"),
    Crop("scene_object_sheet", "gate_open_candidate", (420, 355, 760, 635), "gate/grate open candidate"),
    Crop("scene_object_sheet", "founders_ledger_open_scene", (790, 360, 1510, 640), "open ledger scene prop candidate"),
    Crop("scene_object_sheet", "popcorn_boulder_candidate", (40, 690, 375, 1000), "popcorn boulder prop candidate"),
    Crop("scene_object_sheet", "cobweb_curtain_candidate", (445, 690, 760, 1010), "cobweb curtain candidate; partial alpha will need hand cleanup", alpha_tolerance=0),
    Crop("scene_object_sheet", "couch_underdesk_candidate", (800, 690, 1510, 1015), "couch underside/large furniture candidate"),
]


def ensure(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def dominant_corner_color(img: Image.Image) -> tuple[int, int, int]:
    samples: list[tuple[int, int, int]] = []
    w, h = img.size
    for x, y in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1)]:
        samples.append(img.getpixel((x, y))[:3])
    return tuple(round(sum(pixel[i] for pixel in samples) / len(samples)) for i in range(3))


def keyed_alpha(crop: Image.Image, tolerance: int) -> Image.Image:
    if tolerance <= 0:
        return crop.convert("RGBA")
    bg = dominant_corner_color(crop)
    rgba = crop.convert("RGBA")
    pix = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pix[x, y]
            dist = math.sqrt((r - bg[0]) ** 2 + (g - bg[1]) ** 2 + (b - bg[2]) ** 2)
            if dist < tolerance:
                pix[x, y] = (0, 0, 0, 0)
            elif dist < tolerance + 22:
                alpha = int(255 * ((dist - tolerance) / 22))
                pix[x, y] = (r, g, b, min(a, alpha))
    alpha = rgba.getchannel("A").filter(ImageFilter.GaussianBlur(0.7))
    rgba.putalpha(alpha)
    return rgba


def save_contact(crops: list[tuple[Crop, Image.Image]], path: Path) -> None:
    thumb = (220, 180)
    cols = 4
    rows = math.ceil(len(crops) / cols)
    contact = Image.new("RGBA", (cols * thumb[0], rows * (thumb[1] + 38)), (128, 128, 128, 255))
    draw = ImageDraw.Draw(contact)
    for index, (spec, img) in enumerate(crops):
        cell_x = (index % cols) * thumb[0]
        cell_y = (index // cols) * (thumb[1] + 38) + 34
        scale = min((thumb[0] - 16) / img.width, (thumb[1] - 12) / img.height)
        resized = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.Resampling.LANCZOS)
        pos = (cell_x + (thumb[0] - resized.width) // 2, cell_y + (thumb[1] - resized.height) // 2)
        contact.alpha_composite(resized, pos)
        draw.text((cell_x + 6, cell_y - 28), spec.name[:31], fill=(255, 244, 215, 255))
    contact.save(path)


def main() -> None:
    ensure(SOURCE_DIR)
    ensure(CROP_DIR)
    source_manifest: dict[str, dict] = {}
    for key, path in SOURCES.items():
        if not path.exists():
            raise FileNotFoundError(path)
        dest = SOURCE_DIR / f"{key}.png"
        shutil.copy2(path, dest)
        img = Image.open(path)
        source_manifest[key] = {"original": str(path), "stored": str(dest), "size": list(img.size)}

    crop_results: list[dict] = []
    contact_inputs: list[tuple[Crop, Image.Image]] = []
    opened = {key: Image.open(path).convert("RGB") for key, path in SOURCES.items()}
    for spec in CROPS:
        sheet = opened[spec.source]
        crop = sheet.crop(spec.box)
        keyed = keyed_alpha(crop, spec.alpha_tolerance)
        out = CROP_DIR / f"{spec.name}.png"
        keyed.save(out)
        contact_inputs.append((spec, keyed))
        crop_results.append(
            {
                "name": spec.name,
                "source": spec.source,
                "box": list(spec.box),
                "note": spec.note,
                "alpha_policy": "conservative gray-background key for review only; manual alpha cleanup still required before final admission",
                "path": str(out),
            }
        )

    contact_path = OUT_ROOT / "user_prop_art_intake_contact.png"
    save_contact(contact_inputs, contact_path)
    manifest = {
        "role": "REJECTED first-pass user-provided art candidate intake",
        "status": "rejected",
        "rejection_reason": "Manual crop boxes cut through neighboring objects or clipped important transparent/glass/cobweb details. Keep source sheets, but do not production-admit these crops.",
        "source_sheets": source_manifest,
        "crops": crop_results,
        "contact_sheet": str(contact_path),
        "warnings": [
            "Input sheets are RGB on gray, not true alpha; crop alpha is intake quality only.",
            "Cobweb and dust details need hand alpha cleanup because partial transparency cannot be recovered perfectly from flattened gray sheets.",
        ],
    }
    (OUT_ROOT / "user_prop_art_intake_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"crops": len(crop_results), "contact": str(contact_path)}, indent=2))


if __name__ == "__main__":
    main()
