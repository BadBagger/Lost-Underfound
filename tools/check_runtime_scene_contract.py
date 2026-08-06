#!/usr/bin/env python3
"""Runtime scene contract checks for the Act 1 browser/Forge reference build."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "src" / "main.ts"
GEOMETRY = ROOT / "ags" / "room1" / "geometry.json"
ADMISSION = ROOT / "art" / "animation_admission.json"
CHARACTER_MODELS = ROOT / "content" / "act1_character_models.json"
ENGINE_EXPORTS = {
    "pip": ROOT / "art" / "engine-export" / "pip" / "pip.engine.json",
    "old-bottlecap": ROOT / "art" / "engine-export" / "old-bottlecap" / "old-bottlecap.engine.json",
    "scuttle": ROOT / "art" / "engine-export" / "scuttle" / "scuttle.engine.json",
    "bramble": ROOT / "art" / "engine-export" / "bramble" / "bramble.engine.json",
}
FINALIZED_CHARACTERS = {"bramble"}
PROVISIONAL_RUNTIME_CHARACTERS = {"pip", "old-bottlecap", "scuttle"}


def fail(message: str) -> None:
    raise SystemExit(f"Runtime scene QA failed: {message}")


def read(path: Path) -> str:
    if not path.exists():
        fail(f"missing required file: {path.relative_to(ROOT).as_posix()}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    source = read(MAIN)
    geometry = json.loads(read(GEOMETRY))
    admission = json.loads(read(ADMISSION))
    character_models = json.loads(read(CHARACTER_MODELS))
    exports = {character: json.loads(read(path)) for character, path in ENGINE_EXPORTS.items()}

    if 'import roomGeometry from "../ags/room1/geometry.json"' not in source:
        fail("runtime must import AGS room geometry instead of duplicating hotspot coordinates")
    if 'import characterModels from "../content/act1_character_models.json"' not in source:
        fail("runtime must import the Act 1 character model registry")
    if "const hotspots:" in source or "Object.entries(hotspots)" in source:
        fail("runtime still appears to use a single-screen hotspot table")
    if "screen.hotspots" not in source or "screen.exits" not in source:
        fail("runtime must render screen-local hotspots and exits")
    if "dialogue-panel" not in source or "dialogue-card" not in source:
        fail("dialogue must render in the dedicated bottom panel")
    if 'class="dialogue ' in source or "position: fixed" in read(ROOT / "src" / "styles.css"):
        fail("dialogue must not be a fixed/over-stage bubble")
    for field in ("pipHeight", "brambleTalkingHeadHeight", "oldBottlecapHeight", "scuttleHeight"):
        if f"geometry.actorReference.{field}" not in source:
            fail(f"runtime must derive actor scale from geometry.actorReference.{field}")
    if 'standingPoint("bramble-talking-head"' not in source:
        fail("Bramble must be anchored from the clerk talking-head geometry point")
    if 'standingPoint("old-bottlecap-guard"' not in source:
        fail("Bottlecap must be anchored from the gate guard geometry point")
    if "interaction-blocked" not in source:
        fail("runtime must block hotspots/exits while dialogue or topic UI is open")
    if "walkPipTo(target" not in source or "runHotspotInteraction(id)" not in source:
        fail("runtime must walk Pip to the hotspot interaction point before firing the interaction")
    if "state.current?.speaker === \"PIP\"" not in source or "pipTalk" not in source:
        fail("runtime must use Pip talk frames while Pip dialogue is active")
    if '"pip-inspect"' not in source:
        fail("runtime must include a Pip inspect beat before inspect dialogue")
    if "backgrounds:" not in source or "assets.scene.backgrounds[state.screenId]" not in source:
        fail("runtime must select the screen-local AGS background for the active screen")
    if 'data-layer="ambient-motion"' not in source or "ambient-motion-layer" not in source:
        fail("runtime must expose a non-interactive ambient motion layer between background and actors")
    for data_layer in ("desk-front-occluder", "gate-animation", "dust-prop", "button-flight", "cobweb-disturbance", "scuttle-dash"):
        if f'data-layer="{data_layer}"' not in source:
            fail(f"runtime must expose interactable/change layer {data_layer}")
    if "layered-v2/bg_room.png" in source:
        fail("runtime must not use the old shared room plate as the active screen background")

    screens = {screen["id"]: screen for screen in geometry.get("screens", [])}
    if set(screens) != {"discovery", "clerk", "gate"}:
        fail("geometry must define exactly discovery, clerk, and gate screens")
    for screen_id, screen in screens.items():
        if not screen.get("hotspots"):
            fail(f"{screen_id} has no hotspots")
        if not screen.get("exits"):
            fail(f"{screen_id} has no exits")
    if "cobweb-curtain" not in {hotspot["id"] for hotspot in screens["gate"]["hotspots"]}:
        fail("gate screen must retain cobweb-curtain as a live hotspot")
    bottlecap_y = screens["gate"]["standingPositions"]["old-bottlecap-guard"]["y"]
    gate_baseline = screens["gate"]["walkBehinds"][0]["baseline"]
    if bottlecap_y <= gate_baseline:
        fail("Bottlecap must be staged in front of the gate baseline, not behind the bars")

    sheets = {sheet["id"]: sheet for sheet in admission.get("sheets", [])}
    required_loop_frames = {
        "pip-idle": 12,
        "pip-walk": 12,
        "bramble-idle": 24,
        "bramble-talk": 48,
        "old-bottlecap-idle": 24,
    }
    for sheet_id, min_frames in required_loop_frames.items():
        sheet = sheets.get(sheet_id)
        if not sheet:
            fail(f"animation admission is missing {sheet_id}")
        if sheet.get("loop") is not True:
            fail(f"{sheet_id} must be declared as a loop")
        if int(sheet.get("min_loop_frames", 0)) < min_frames:
            fail(f"{sheet_id} min_loop_frames is too low; short cycles caused visible jank")

    for asset_key in ("brambleGreeting", "brambleHandoff", "brambleWrong"):
        if asset_key not in source:
            fail(f"runtime must load the finished Bramble state asset set: {asset_key}")
    for action_name in ("bramble-greeting", "bramble-handoff", "bramble-wrong"):
        if action_name not in source:
            fail(f"runtime must be able to play Bramble action state {action_name}")

    active_characters = character_models.get("characters", {})
    if set(active_characters) != set(ENGINE_EXPORTS):
        fail(
            "active runtime character registry must exactly match loadable Act 1 engine exports: "
            f"{sorted(ENGINE_EXPORTS)}"
        )
    for character in FINALIZED_CHARACTERS:
        if active_characters.get(character, {}).get("admission") != "finalized":
            fail(f"{character} must be marked finalized in the runtime character registry")
    for character in PROVISIONAL_RUNTIME_CHARACTERS:
        if active_characters.get(character, {}).get("admission") != "provisional-runtime":
            fail(f"{character} must be marked provisional-runtime until the updated accurate model is admitted")
    if set(character_models.get("not_finalized", {})) & FINALIZED_CHARACTERS:
        fail("finalized characters must not also appear in not_finalized")
    for character in PROVISIONAL_RUNTIME_CHARACTERS:
        if character not in character_models.get("not_finalized", {}):
            fail(f"{character} must be documented in not_finalized while it remains provisional")
    for character, export_path in ENGINE_EXPORTS.items():
        model = active_characters.get(character)
        if not model:
            fail(f"missing runtime character model: {character}")
        expected_manifest = export_path.relative_to(ROOT).as_posix()
        if model.get("engine_manifest") != expected_manifest:
            fail(f"{character} runtime registry points at the wrong engine manifest")
        if exports[character].get("status") != "engine-export-ready":
            fail(f"{character} engine export is not marked engine-export-ready")
        for state_name, state in model.get("states", {}).items():
            folder = ROOT / state.get("folder", "")
            if not folder.exists():
                fail(f"{character}:{state_name} runtime frame folder is missing")
            if int(state.get("frames", 0)) <= 0:
                fail(f"{character}:{state_name} must declare a positive frame count")

    runtime_assets = {
        "pip": {
            "pipIdle": "idle",
            "pipWalk": "walk",
            "pipTalk": "talk",
            "pipDust": "dustReach",
            "pipToll": "tollPaid",
        },
        "old-bottlecap": {
            "bottlecapIdle": "idle",
            "bottlecapRefused": "tollRefused",
            "bottlecapPaid": "tollPaid",
        },
        "scuttle": {
            "scuttleDash": "dash",
        },
        "bramble": {
            "brambleIdle": "idle",
            "brambleTalk": "talk",
            "brambleGreeting": "greeting",
            "brambleHandoff": "handoff",
            "brambleWrong": "wrongAction",
        },
    }
    for character, assets in runtime_assets.items():
        for runtime_key, export_state in assets.items():
            expected_frames = exports[character]["states"][export_state]["frames"]
            registered_frames = active_characters[character]["states"][export_state]["frames"]
            if registered_frames != expected_frames:
                fail(
                    f"runtime registry {character}:{export_state} has {registered_frames} frames, "
                    f"but engine export declares {expected_frames}"
                )
            expected_pattern = f'{runtime_key}: characterFrames("{character}", "{export_state}")'
            if expected_pattern not in source:
                fail(
                    f"runtime {runtime_key} must resolve {character}:{export_state} through the character model registry"
                )
    if "brambleMouths: brambleMouthFrames()" not in source:
        fail("runtime must load Bramble's separate mouth overlay frames")
    for cue in exports["bramble"]["mouth_visemes"]["cues"]:
        if cue not in active_characters["bramble"].get("mouths", {}).get("cues", []):
            fail(f"runtime registry must include Bramble mouth viseme cue {cue}")

    print(
        "Runtime scene QA passed: geometry-driven screens, bottom dialogue UI, actor scale anchors, "
        "Bottlecap gate staging, cobweb hotspot, character export parity, finalized/provisional cast status, "
        "state playback, and loop-frame floors are enforced."
    )


if __name__ == "__main__":
    main()
