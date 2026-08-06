#!/usr/bin/env python3
"""Validate declared interactable/changeable scene layers."""

from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ags" / "interactive_change_layers.json"
SCENE_LAYERS = ROOT / "art" / "act01-production" / "scene" / "layers.json"
MAIN = ROOT / "src" / "main.ts"


def fail(message: str) -> None:
    print(f"FAIL - {message}")
    raise SystemExit(1)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing required file: {path.relative_to(ROOT).as_posix()}")
    return json.loads(path.read_text(encoding="utf-8"))


def geometry_bindings(room_id: str) -> dict[str, set[str]]:
    path = ROOT / "ags" / room_id / "geometry.json"
    geometry = read_json(path)
    bindings: dict[str, set[str]] = {}
    for screen in geometry.get("screens", []):
        ids: set[str] = set()
        for key in ("hotspots", "walkBehinds", "separateProps"):
            ids.update(item.get("id", "") for item in screen.get(key, []))
        bindings[screen["id"]] = {value for value in ids if value}
    return bindings


def layer_ids_from_scene_manifest() -> set[str]:
    manifest = read_json(SCENE_LAYERS)
    return {layer.get("id", "") for layer in manifest.get("layers", [])}


def assert_asset(layer: dict[str, Any]) -> None:
    asset = layer.get("asset")
    pattern = layer.get("asset_pattern")
    source = layer.get("source")
    if asset and not (ROOT / asset).exists():
        fail(f"{layer['id']} points to missing asset {asset}")
    if pattern and not glob.glob(str(ROOT / pattern)):
        fail(f"{layer['id']} asset_pattern matched no files: {pattern}")
    if source == "src/styles.css" and not (ROOT / "src" / "styles.css").exists():
        fail(f"{layer['id']} uses missing CSS source")
    if source == "background-polygon":
        return
    if not any((asset, pattern, source)):
        fail(f"{layer['id']} is production-ready but has no asset, asset_pattern, or source")


def main() -> int:
    manifest = read_json(MANIFEST)
    layers = manifest.get("layers", [])
    if not layers:
        fail("interactive change layer manifest has no layers")

    rooms = {layer.get("room") for layer in layers}
    bindings = {room: geometry_bindings(room) for room in rooms if room}
    scene_layer_ids = layer_ids_from_scene_manifest()
    source = MAIN.read_text(encoding="utf-8")

    seen: set[str] = set()
    production_ready: list[dict[str, Any]] = []
    for layer in layers:
        for key in ("room", "screen", "id", "kind", "binds_to", "z", "status"):
            if key not in layer:
                fail(f"layer is missing required field {key}: {layer}")
        layer_id = layer["id"]
        if layer_id in seen:
            fail(f"duplicate interactable change layer id: {layer_id}")
        seen.add(layer_id)
        room = layer["room"]
        screen = layer["screen"]
        if room not in bindings:
            fail(f"{layer_id} references missing room geometry: {room}")
        if screen not in bindings[room]:
            fail(f"{layer_id} references missing screen {room}:{screen}")
        if layer["binds_to"] not in bindings[room][screen]:
            fail(f"{layer_id} binds to unknown {room}:{screen} id {layer['binds_to']}")
        if layer.get("non_interactive") is not True:
            fail(f"{layer_id} must be non_interactive; hotspot masks own clicks")
        if not isinstance(layer.get("stateful"), bool):
            fail(f"{layer_id} must declare stateful true/false")
        if not isinstance(layer.get("z"), int):
            fail(f"{layer_id} z must be an integer")
        if layer["status"] not in {"planned", "production-ready"}:
            fail(f"{layer_id} has invalid status {layer['status']}")
        if layer["status"] == "production-ready":
            production_ready.append(layer)

    required_production = set(manifest.get("required_production_ids", []))
    missing_required = sorted(required_production - {layer["id"] for layer in production_ready})
    if missing_required:
        fail(f"required production change layers are not production-ready: {', '.join(missing_required)}")

    for layer in production_ready:
        assert_asset(layer)
        data_layer = layer.get("data_layer")
        if not data_layer:
            fail(f"{layer['id']} is production-ready but has no runtime data_layer")
        if f'data-layer="{data_layer}"' not in source:
            fail(f"{layer['id']} data-layer is not rendered by the runtime: {data_layer}")
        if layer["room"] == "room1" and data_layer not in scene_layer_ids:
            fail(f"{layer['id']} data-layer is not declared in Act 1 scene layers: {data_layer}")

    css = (ROOT / "src" / "styles.css").read_text(encoding="utf-8")
    for layer in production_ready:
        data_layer = layer["data_layer"]
        class_match = re.search(rf'class="(?P<classes>[^"]+)"[^>]*data-layer="{re.escape(data_layer)}"', source)
        if not class_match:
            class_match = re.search(rf'data-layer="{re.escape(data_layer)}"[^>]*class="(?P<classes>[^"]+)"', source)
        if class_match:
            classes = class_match.group("classes").split()
            class_css = "\n".join(
                block.group(0)
                for block in re.finditer(r"(?P<selectors>[^{}]+)\{(?P<body>[^{}]*)\}", css, re.MULTILINE)
                if any(f".{class_name}" in block.group("selectors") for class_name in classes)
            )
            if "pointer-events: none;" not in class_css and layer["kind"] != "foreground-occluder":
                fail(f"{layer['id']} runtime CSS must be pointer-events none")

    print(
        "PASS - "
        f"{len(layers)} interactable/change layer(s) declared; "
        f"{len(production_ready)} production-ready layer(s) bound to geometry and runtime slots."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
