"""Fail the build when the discrete AGS Room 1 geometry contract drifts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "ags" / "room1" / "geometry.json"


def fail(message: str) -> None:
    raise SystemExit(f"AGS Room 1 geometry QA failed: {message}")


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("architecture") != "discrete-screens":
        fail("Room 1 must use discrete screens, never a scrolling panorama")
    if spec.get("nativeSize") != {"width": 1280, "height": 720}:
        fail("every Room 1 screen must be native 1280x720")

    screens = {screen["id"]: screen for screen in spec.get("screens", [])}
    if set(screens) != {"discovery", "clerk", "gate"}:
        fail("Room 1 must contain discovery, clerk, and gate screens")
    if spec.get("start") != {"screenId": "discovery", "entryPoint": "cold-open"}:
        fail("Pip must begin the cold open in the discovery screen")
    pip_height = spec.get("actorReference", {}).get("pipHeight")
    if not (315 <= pip_height <= 345):
        fail("Pip registered body height must stay calibrated to the painted rooms, target range 315-345px")

    for screen_id, screen in screens.items():
        if screen["background"] != f"background/{screen_id}.png":
            fail(f"{screen_id} background path must be screen-local")
        if len(screen["walkableArea"]) < 3:
            fail(f"{screen_id} needs a walkable floor polygon")
        if not screen.get("entryPoints"):
            fail(f"{screen_id} needs at least one entry point")

    discovery_ids = {hotspot["id"] for hotspot in screens["discovery"]["hotspots"]}
    if not {"cubby-wall", "dust-clump", "popcorn-boulder", "couch-ceiling"} <= discovery_ids:
        fail("discovery screen must contain the Act 1 discovery hotspots")

    clerk = screens["clerk"]
    desk = clerk["walkBehinds"][0]
    if desk["id"] != "bramble-desk" or desk["baseline"] != 642:
        fail("clerk screen desk baseline must remain 642")
    if desk["rect"] != {"x": 70, "y": 360, "width": 720, "height": 285}:
        fail("clerk desk footprint must remain 70,360,720x285")
    pip_talk = clerk["standingPositions"]["pip-talk-bramble"]
    bramble = clerk["standingPositions"]["bramble-talking-head"]
    desk_rect = desk["rect"]
    bramble_window_left = desk_rect["x"] + 0.36 * desk_rect["width"]
    bramble_window_right = desk_rect["x"] + 0.70 * desk_rect["width"]
    if not (bramble_window_left <= bramble["x"] <= bramble_window_right):
        fail("Bramble must be registered inside the desk talking-head window")
    if not (desk["counterTopY"] <= bramble["y"] <= desk["baseline"]):
        fail("Bramble must be registered as a counter-height talking head")
    if "frontOccluderPolygon" not in desk or len(desk["frontOccluderPolygon"]) < 4:
        fail("clerk desk must declare a desk-front occluder polygon for actor proofing")
    if not (pip_talk["x"] > desk_rect["x"] + desk_rect["width"] + 20):
        fail("Pip must stand beside the desk face, not on the desk")
    if not (desk["baseline"] <= pip_talk["y"] <= 690):
        fail("Pip talk position must stay on the walkable floor in front of the desk")

    gate = screens["gate"]
    gate_object = gate["walkBehinds"][0]
    if gate_object["id"] != "toll-gate" or gate_object["baseline"] != 568:
        fail("gate screen baseline must remain 568")
    if not (gate["standingPositions"]["old-bottlecap-guard"]["y"] > gate_object["baseline"]):
        fail("Bottlecap must render in front of gate bars")
    gate_ids = {hotspot["id"] for hotspot in gate["hotspots"]}
    if not {"toll-gate", "cobweb-curtain"} <= gate_ids:
        fail("gate screen must contain both gate and cobweb-tunnel hotspots")

    link_map = {(link["from"], link["to"]) for link in spec.get("linkMap", [])}
    required_links = {
        ("discovery:to-clerk", "clerk:from-discovery"),
        ("clerk:to-discovery", "discovery:from-clerk"),
        ("clerk:to-gate", "gate:from-clerk"),
        ("gate:to-clerk", "clerk:from-gate"),
    }
    if link_map != required_links:
        fail("link map must define both directions for discovery-clerk and clerk-gate")

    for screen in screens.values():
        for exit_data in screen.get("exits", []):
            destination = exit_data["destinationScreenId"]
            if destination == "act-02":
                if exit_data.get("transitionLineId") != "act01-049-pip-transition-out":
                    fail("gate transition must use exact script line act01-049-pip-transition-out")
                continue
            if destination not in screens:
                fail(f"{screen['id']} exit {exit_data['id']} has no valid destination")
            if exit_data["entryPoint"] not in screens[destination]["entryPoints"]:
                fail(f"{screen['id']} exit {exit_data['id']} targets a missing entry point")

    print("AGS Room 1 geometry QA passed: three linked 1280x720 screens, locked actor staging, and valid exits.")


if __name__ == "__main__":
    main()
