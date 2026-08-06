#!/usr/bin/env python3
"""Validate the Codex-editable Godot/Popochiu content scaffold.

This is a pre-Godot gate. It proves the data layer is internally connected and
references real repo assets before any project import or Popochiu wiring happens.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "content" / "manifest.json"


def fail(message: str) -> None:
    raise SystemExit(f"Godot content manifest QA failed: {message}")


def load_json(path: Path) -> Any:
    if not path.exists():
        fail(f"missing JSON file: {path.relative_to(ROOT)}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")


def require_file(path_text: str, owner: str) -> None:
    path = ROOT / path_text
    if not path.exists():
        fail(f"{owner} references missing file: {path_text}")


def validate_polygon(poly: Any, owner: str) -> None:
    if not isinstance(poly, list) or len(poly) < 3:
        fail(f"{owner} must be a polygon with at least 3 points")
    for point in poly:
        if not (
            isinstance(point, list)
            and len(point) == 2
            and all(isinstance(value, (int, float)) for value in point)
        ):
            fail(f"{owner} has invalid point: {point!r}")


def validate_point(point: Any, owner: str) -> None:
    if not (
        isinstance(point, list)
        and len(point) == 2
        and all(isinstance(value, (int, float)) for value in point)
    ):
        fail(f"{owner} must be [x, y]")


def collect_line_ids(script_path: Path) -> set[str]:
    script = load_json(script_path)
    if isinstance(script, dict) and "lines" in script:
        lines = script["lines"]
    else:
        lines = script
    if not isinstance(lines, list):
        fail("dialogue source must be a list or contain a lines list")
    ids = set()
    for entry in lines:
        if isinstance(entry, dict):
            line_id = entry.get("line_id", entry.get("id"))
            if isinstance(line_id, str):
                ids.add(line_id)
    if not ids:
        fail("dialogue source exposes no line ids")
    return ids


def validate_line_refs(value: Any, valid_ids: set[str], owner: str) -> None:
    if value is None:
        return
    if isinstance(value, str):
        refs = [value]
    elif isinstance(value, list):
        refs = value
    else:
        fail(f"{owner} line reference must be string or list")
    for line_id in refs:
        if line_id not in valid_ids:
            fail(f"{owner} references unknown script line id: {line_id}")


def main() -> int:
    manifest = load_json(MANIFEST)
    if manifest.get("schema_version") != 1:
        fail("content/manifest.json must declare schema_version=1")
    if manifest.get("act_scope") != "act-01-only":
        fail("manifest must keep production scope to act-01-only")

    dialogue_source = manifest.get("dialogue_source")
    if not isinstance(dialogue_source, str):
        fail("manifest must declare dialogue_source")
    require_file(dialogue_source, "manifest.dialogue_source")
    valid_line_ids = collect_line_ids(ROOT / dialogue_source)

    rooms: dict[str, dict[str, Any]] = {}
    room_paths = manifest.get("rooms")
    if not isinstance(room_paths, list) or not room_paths:
        fail("manifest must list at least one room")

    for room_path_text in room_paths:
        if not isinstance(room_path_text, str):
            fail("room manifest entries must be strings")
        room_path = ROOT / room_path_text
        room = load_json(room_path)
        room_id = room.get("id")
        if not isinstance(room_id, str):
            fail(f"{room_path_text} missing string id")
        if room_id in rooms:
            fail(f"duplicate room id: {room_id}")
        rooms[room_id] = room

        if room.get("native_size") != [1280, 720]:
            fail(f"{room_id} native_size must be [1280, 720]")
        background = room.get("background")
        if not isinstance(background, str):
            fail(f"{room_id} missing background path")
        require_file(background, f"{room_id}.background")
        validate_polygon(room.get("walkable_polygon"), f"{room_id}.walkable_polygon")

        entries = room.get("entry_points")
        if not isinstance(entries, dict) or not entries:
            fail(f"{room_id} must declare entry_points")
        for entry_id, point in entries.items():
            validate_point(point, f"{room_id}.entry_points.{entry_id}")

        hotspots = room.get("hotspots", [])
        if not isinstance(hotspots, list):
            fail(f"{room_id}.hotspots must be a list")
        for hotspot in hotspots:
            hot_id = hotspot.get("id", "<missing>")
            validate_polygon(hotspot.get("shape"), f"{room_id}.{hot_id}.shape")
            validate_point(hotspot.get("walk_to"), f"{room_id}.{hot_id}.walk_to")
            if "essential" not in hotspot:
                fail(f"{room_id}.{hot_id} must declare essential true/false")
            for key in ("look_lines", "use_lines", "talk_lines", "success_lines", "failure_lines", "gag_pool"):
                if key in hotspot:
                    validate_line_refs(hotspot[key], valid_line_ids, f"{room_id}.{hot_id}.{key}")

    for room_id, room in rooms.items():
        for exit_data in room.get("exits", []):
            exit_id = exit_data.get("id", "<missing>")
            validate_polygon(exit_data.get("region"), f"{room_id}.{exit_id}.region")
            validate_point(exit_data.get("walk_to"), f"{room_id}.{exit_id}.walk_to")
            destination = exit_data.get("to")
            if destination not in rooms and not exit_data.get("terminal"):
                fail(f"{room_id}.{exit_id} points to unknown room: {destination}")
            if not exit_data.get("terminal"):
                entry = exit_data.get("destination_entry")
                if entry not in rooms[destination].get("entry_points", {}):
                    fail(f"{room_id}.{exit_id} points to missing entry {destination}.{entry}")

    for item_path_text in manifest.get("items", []):
        item = load_json(ROOT / item_path_text)
        item_id = item.get("id")
        if not isinstance(item_id, str):
            fail(f"{item_path_text} missing item id")
        icon = item.get("icon")
        if not isinstance(icon, str):
            fail(f"{item_id} missing icon")
        require_file(icon, f"{item_id}.icon")
        if "look_lines" in item:
            validate_line_refs(item["look_lines"], valid_line_ids, f"{item_id}.look_lines")

    for key in ("randomization", "combine_table"):
        path_text = manifest.get(key)
        if not isinstance(path_text, str):
            fail(f"manifest missing {key}")
        load_json(ROOT / path_text)

    for cutscene_path_text in manifest.get("cutscenes", []):
        cutscene = load_json(ROOT / cutscene_path_text)
        if not isinstance(cutscene.get("steps"), list) or not cutscene["steps"]:
            fail(f"{cutscene_path_text} must declare non-empty steps")

    print(
        "Godot content manifest QA passed: "
        f"{len(rooms)} room(s), {len(manifest.get('items', []))} item(s), "
        f"{len(manifest.get('cutscenes', []))} cutscene smoke path(s), "
        "all room links and script line references valid."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
