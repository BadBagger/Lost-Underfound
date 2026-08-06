#!/usr/bin/env python3
"""Export Act 1 character production frames into engine-ready sprite strips."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
CHAR_ROOT = ROOT / "art" / "act01-production" / "characters"
RIG_ROOT = ROOT / "art" / "rigs"
OUT_ROOT = ROOT / "art" / "engine-export"
QA_ROOT = ROOT / "art" / "act01-production" / "qa"
PINK = (255, 0, 255, 255)


CHARACTERS: dict[str, dict] = {
    "pip": {
        "source": CHAR_ROOT / "pip",
        "role": "walk-plane player character",
        "states": {
            "idle": {
                "folder": "meshy-current/idle",
                "prefix": "pip_meshy_idle",
                "frames": 12,
                "fps": 5,
                "loop": True,
                "ags_view": "PIP_IDLE",
            },
            "walk": {
                "folder": "meshy-current/walk",
                "prefix": "pip_meshy_walk",
                "frames": 12,
                "fps": 12,
                "loop": True,
                "ags_view": "PIP_WALK_RIGHT",
            },
            "talk": {
                "folder": "meshy-current/talk",
                "prefix": "pip_meshy_talk",
                "frames": 12,
                "fps": 12,
                "loop": True,
                "ags_view": "PIP_TALK",
            },
            "inspect": {
                "folder": "meshy-current/inspect",
                "prefix": "pip_meshy_inspect",
                "frames": 14,
                "fps": 12,
                "loop": False,
                "ags_view": "PIP_INSPECT",
            },
            "dustReach": {
                "folder": "meshy-current/dust-reach",
                "prefix": "pip_meshy_dust",
                "frames": 14,
                "fps": 12,
                "loop": False,
                "ags_view": "PIP_PICKUP_DUST",
            },
            "tollPaid": {
                "folder": "meshy-current/toll-paid",
                "prefix": "pip_meshy_toll",
                "frames": 10,
                "fps": 12,
                "loop": False,
                "ags_view": "PIP_HANDOFF_TOLL",
            },
        },
        "import_note": "Import each strip as evenly divided RGBA frames. Use the walk strip as Pip's right-facing walk; mirror in-engine for left-facing movement.",
    },
    "old-bottlecap": {
        "source": CHAR_ROOT / "old-bottlecap",
        "role": "gate-anchored toll guard",
        "states": {
            "idle": {
                "folder": "meshy-current/idle",
                "prefix": "old_bottlecap_meshy_idle",
                "frames": 24,
                "fps": 12,
                "loop": True,
                "ags_view": "BOTTLECAP_IDLE",
            },
            "tollRefused": {
                "folder": "meshy-current/toll-refused",
                "prefix": "old_bottlecap_meshy_refuse",
                "frames": 5,
                "fps": 8,
                "loop": False,
                "ags_view": "BOTTLECAP_TOLL_REFUSED",
            },
            "tollPaid": {
                "folder": "meshy-current/toll-paid",
                "prefix": "old_bottlecap_meshy_paid",
                "frames": 7,
                "fps": 8,
                "loop": False,
                "ags_view": "BOTTLECAP_TOLL_PAID",
            },
        },
        "import_note": "Import as a gate-anchored guard. Bottlecap is staged in front of the gate baseline; gate bars are not allowed to crop or hide the actor.",
    },
    "scuttle": {
        "source": CHAR_ROOT / "scuttle",
        "role": "walk-plane courier cameo",
        "states": {
            "dash": {
                "folder": "meshy-current/dash",
                "prefix": "scuttle_meshy_dash",
                "frames": 6,
                "fps": 16,
                "loop": False,
                "ags_view": "SCUTTLE_DASH",
            },
        },
        "import_note": "Import as a one-shot dash. Frames 1 and 5 must stay readable solid poses; frames 3 and 4 are smear frames.",
    },
    "bramble": {
        "source": CHAR_ROOT / "bramble",
        "role": "counter-height talking-head NPC",
        "states": {
            "idle": {"folder": "idle", "prefix": "bramble_idle", "frames": 24, "fps": 12, "loop": True, "ags_view": "BRAMBLE_IDLE"},
            "talk": {"folder": "talk", "prefix": "bramble_talk", "frames": 48, "fps": 12, "loop": True, "ags_view": "BRAMBLE_TALK_BASE"},
            "greeting": {
                "folder": "greeting",
                "prefix": "bramble_greeting",
                "frames": 36,
                "fps": 12,
                "loop": False,
                "ags_view": "BRAMBLE_GREETING",
            },
            "handoff": {
                "folder": "handoff",
                "prefix": "bramble_handoff",
                "frames": 36,
                "fps": 12,
                "loop": False,
                "ags_view": "BRAMBLE_HANDOFF",
            },
            "wrongAction": {
                "folder": "wrong-action",
                "prefix": "bramble_wrong",
                "frames": 30,
                "fps": 12,
                "loop": False,
                "ags_view": "BRAMBLE_WRONG_ACTION",
            },
        },
        "mouths": ["X", "A", "B", "C", "D", "E", "F"],
        "import_note": "Import each strip as evenly divided 320x260 RGBA frames. Use the talk strip as body/brow base and mouth_visemes as overlay or AGS talk-mouth frames.",
    },
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def frame_paths(character: dict, state: dict) -> list[Path]:
    folder = character["source"] / state["folder"]
    return [folder / f"{state['prefix']}_{index:02d}.png" for index in range(1, state["frames"] + 1)]


def read_registration(character: dict, state: dict) -> dict:
    return load_json(character["source"] / state["folder"] / "registration.json")


def save_strip(paths: list[Path], output: Path) -> dict:
    first = Image.open(paths[0]).convert("RGBA")
    cell_w, cell_h = first.size
    strip = Image.new("RGBA", (cell_w * len(paths), cell_h), (0, 0, 0, 0))
    source_hashes = {}
    for index, path in enumerate(paths):
        image = Image.open(path).convert("RGBA")
        if image.size != (cell_w, cell_h):
            raise SystemExit(f"{rel(path)} is {image.size}; expected {(cell_w, cell_h)}")
        strip.alpha_composite(image, (index * cell_w, 0))
        source_hashes[rel(path)] = sha256(path.read_bytes()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    strip.save(output)
    return {
        "file": rel(output),
        "cell": [cell_w, cell_h],
        "frames": len(paths),
        "sha256": sha256(output.read_bytes()).hexdigest(),
        "source_hashes": source_hashes,
    }


def save_review_sheet(character_id: str, exports: list[dict]) -> str:
    thumb_w, thumb_h = 220, 160
    sheet = Image.new("RGBA", (thumb_w * 2, thumb_h * len(exports)), PINK)
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        font = ImageFont.load_default()
    for row, export in enumerate(exports):
        strip = Image.open(ROOT / export["file"]).convert("RGBA")
        cell_w, cell_h = export["cell"]
        first = strip.crop((0, 0, cell_w, cell_h))
        last = strip.crop((cell_w * (export["frames"] - 1), 0, cell_w * export["frames"], cell_h))
        for col, image in enumerate((first, last)):
            image.thumbnail((thumb_w - 24, thumb_h - 42), Image.Resampling.LANCZOS)
            x = col * thumb_w + (thumb_w - image.width) // 2
            y = row * thumb_h + 26
            sheet.alpha_composite(image, (x, y))
        draw.text((10, row * thumb_h + 8), f"{Path(export['file']).stem}: first / last", fill=(20, 12, 18), font=font)
        draw.text((10, row * thumb_h + thumb_h - 18), f"{export['frames']} frames @ {export['fps']} fps", fill=(20, 12, 18), font=font)
    output = QA_ROOT / f"{character_id}-engine-export-review.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return rel(output)


def export_character(character_id: str) -> None:
    character = CHARACTERS[character_id]
    out_dir = OUT_ROOT / character_id
    out_dir.mkdir(parents=True, exist_ok=True)

    exports = []
    states = {}
    runtime_canvas = None
    runtime_anchor = None
    actor_type = None

    for state_name, state in character["states"].items():
        paths = frame_paths(character, state)
        for path in paths:
            if not path.exists():
                raise SystemExit(f"missing frame: {rel(path)}")
        registration = read_registration(character, state)
        canvas = [registration["canvas"]["width"], registration["canvas"]["height"]]
        anchor = registration["frames"][0]["anchor"]
        runtime_canvas = runtime_canvas or canvas
        runtime_anchor = runtime_anchor or anchor
        actor_type = actor_type or registration["actor_type"]

        strip = save_strip(paths, out_dir / f"{character_id}_{state_name}.png")
        strip.update(
            {
                "state": state_name,
                "fps": state["fps"],
                "loop": state["loop"],
                "ags_view": state["ags_view"],
                "registration": rel(character["source"] / state["folder"] / "registration.json"),
                "runtime_canvas": canvas,
                "runtime_anchor": anchor,
            }
        )
        exports.append(strip)
        states[state_name] = strip

    manifest = {
        "schema_version": 1,
        "character": character_id,
        "status": "engine-export-ready",
        "character_role": character["role"],
        "actor_type": actor_type,
        "runtime_canvas": runtime_canvas,
        "runtime_anchor": runtime_anchor,
        "ags": {"import_note": character["import_note"]},
        "states": states,
        "qa": {
            "review_sheet": save_review_sheet(character_id, exports),
            "export_gate": f"npm.cmd run qa:engine:{'bottlecap' if character_id == 'old-bottlecap' else character_id}",
        },
    }

    if character_id == "bramble":
        rig_manifest = load_json(RIG_ROOT / "bramble" / "manifest.json")
        manifest.update(
            {
                "source_rig": "art/rigs/bramble/manifest.json",
                "source_render_hashes": rig_manifest["render"]["hashes"],
                "runtime_canvas": rig_manifest["render"]["runtime_canvas"],
                "runtime_anchor": rig_manifest["render"]["runtime_anchor"],
                "desk_contact_line_y": rig_manifest["desk_contact_line_y"],
                "ags": {
                    "character_role": "counter-height talking-head NPC",
                    "baseline_policy": "Bramble is placed behind the solid desk; only head and hands clear the counter line.",
                    "import_note": character["import_note"],
                },
            }
        )
        mouth_paths = [character["source"] / "mouths" / f"bramble_mouth_{cue}.png" for cue in character["mouths"]]
        mouth_strip = save_strip(mouth_paths, out_dir / "bramble_mouth_visemes.png")
        mouth_strip.update({"state": "mouthVisemes", "fps": 0, "loop": False, "cues": character["mouths"], "ags_view": "BRAMBLE_MOUTH_VISEMES"})
        manifest["mouth_visemes"] = mouth_strip
        manifest["qa"]["rig_gate"] = "npm.cmd run qa:rig:bramble"

    (out_dir / f"{character_id}.engine.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {character_id} engine package to {rel(out_dir)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("characters", nargs="*", choices=[*CHARACTERS.keys(), "all"], default=["all"])
    args = parser.parse_args()

    requested = list(CHARACTERS) if "all" in args.characters else args.characters
    for character_id in requested:
        export_character(character_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
