"""Validate every discrete AGS room geometry file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AGS_DIR = ROOT / "ags"
EXTERNAL_DESTINATIONS = {"act-02", "ending"}


def fail(message: str) -> None:
    raise SystemExit(f"AGS geometry QA failed: {message}")


def rect_xywh(rect: dict[str, Any]) -> tuple[float, float, float, float]:
    return (float(rect["x"]), float(rect["y"]), float(rect["width"]), float(rect["height"]))


def assert_point(room_name: str, screen_id: str, label: str, point: dict[str, Any], width: int, height: int) -> None:
    x = float(point["x"])
    y = float(point["y"])
    if not (0 <= x <= width and 0 <= y <= height):
        fail(f"{room_name}/{screen_id} {label} point is outside native bounds")


def assert_rect(room_name: str, screen_id: str, label: str, rect: dict[str, Any], width: int, height: int) -> None:
    x, y, w, h = rect_xywh(rect)
    if w <= 0 or h <= 0:
        fail(f"{room_name}/{screen_id} {label} rect must have positive size")
    if x < 0 or y < 0 or x + w > width or y + h > height:
        fail(f"{room_name}/{screen_id} {label} rect is outside native bounds")


def validate_room(path: Path) -> None:
    room_name = path.parent.name
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("architecture") != "discrete-screens":
        fail(f"{room_name} must use discrete-screens architecture")

    native = spec.get("nativeSize")
    if native != {"width": 1280, "height": 720}:
        fail(f"{room_name} screens must be native 1280x720")
    width, height = native["width"], native["height"]

    screens = {screen["id"]: screen for screen in spec.get("screens", [])}
    if not screens:
        fail(f"{room_name} must contain at least one screen")

    start = spec.get("start", {})
    if start.get("screenId") not in screens:
        fail(f"{room_name} start screen must exist")
    if start.get("entryPoint") not in screens[start["screenId"]].get("entryPoints", {}):
        fail(f"{room_name} start entry point must exist")

    link_map = {(link["from"], link["to"]) for link in spec.get("linkMap", [])}
    seen_internal_exits: set[tuple[str, str]] = set()

    for screen_id, screen in screens.items():
        if screen.get("background") != f"background/{screen_id}.png":
            fail(f"{room_name}/{screen_id} background path must be background/{screen_id}.png")

        walkable = screen.get("walkableArea") or screen.get("walkable")
        if not walkable or len(walkable) < 3:
            fail(f"{room_name}/{screen_id} needs a walkable polygon")
        for index, point in enumerate(walkable):
            x, y = float(point[0]), float(point[1])
            if not (0 <= x <= width and 0 <= y <= height):
                fail(f"{room_name}/{screen_id} walkable point {index} is outside native bounds")

        entry_points = screen.get("entryPoints", {})
        if not entry_points:
            fail(f"{room_name}/{screen_id} needs at least one entry point")
        for name, point in entry_points.items():
            assert_point(room_name, screen_id, f"entry {name}", point, width, height)

        standing = screen.get("standingPositions") or screen.get("standing_positions") or {}
        for name, point in standing.items():
            assert_point(room_name, screen_id, f"standing {name}", point, width, height)

        for item in screen.get("hotspots", []):
            assert_rect(room_name, screen_id, f"hotspot {item['id']}", item["rect"], width, height)

        walkbehinds = screen.get("walkBehinds", []) + screen.get("walkbehinds", [])
        for item in walkbehinds:
            assert_rect(room_name, screen_id, f"walkbehind {item['id']}", item["rect"], width, height)
            baseline = float(item.get("baseline", item.get("baseline_y")))
            if not (0 <= baseline <= height):
                fail(f"{room_name}/{screen_id} walkbehind {item['id']} baseline is outside native bounds")

        for item in screen.get("exits", []):
            assert_rect(room_name, screen_id, f"exit {item['id']}", item["exitHotspot"], width, height)
            destination = item["destinationScreenId"]
            if destination in EXTERNAL_DESTINATIONS:
                continue
            if destination not in screens:
                fail(f"{room_name}/{screen_id} exit {item['id']} has no valid destination screen")
            if item["entryPoint"] not in screens[destination].get("entryPoints", {}):
                fail(f"{room_name}/{screen_id} exit {item['id']} targets a missing entry point")
            seen_internal_exits.add((screen_id, item["id"]))

    for from_ref, to_ref in link_map:
        from_screen, from_exit = from_ref.split(":", 1)
        to_screen, to_entry = to_ref.split(":", 1)
        if from_screen not in screens:
            fail(f"{room_name} link {from_ref} starts from a missing screen")
        if not any(item["id"] == from_exit for item in screens[from_screen].get("exits", [])):
            fail(f"{room_name} link {from_ref} starts from a missing exit")
        if to_screen not in screens:
            fail(f"{room_name} link {to_ref} targets a missing screen")
        if to_entry not in screens[to_screen].get("entryPoints", {}):
            fail(f"{room_name} link {to_ref} targets a missing entry point")

    link_exits = {(item.split(":", 1)[0], item.split(":", 1)[1]) for item, _ in link_map}
    missing_links = seen_internal_exits - link_exits
    if missing_links:
        readable = ", ".join(f"{screen}:{exit_id}" for screen, exit_id in sorted(missing_links))
        fail(f"{room_name} internal exits missing linkMap entries: {readable}")


def main() -> None:
    paths = sorted(AGS_DIR.glob("room*/geometry.json"))
    if not paths:
        fail("no AGS room geometry files found")
    for path in paths:
        validate_room(path)
    print(f"AGS geometry QA passed: {len(paths)} room geometry file(s) are discrete, linked, bounded, and screen-local.")


if __name__ == "__main__":
    main()
