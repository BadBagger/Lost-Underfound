from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_TS = ROOT / "src" / "main.ts"
STYLES_CSS = ROOT / "src" / "styles.css"
GEOMETRY_JSON = ROOT / "ags" / "room1" / "geometry.json"
SCRIPT_JSON = ROOT / "script" / "ACT_01_SCRIPT.json"


EXPECTED_SCREENS = {"discovery", "clerk", "gate"}
EXPECTED_REQUIRED_LINES = {
    "act01-001-pip-cold-open-landing",
    "act01-002-pip-cold-open-goal",
    "act01-004-pip-dustclump-examine",
    "act01-005-pip-dustclump-search-success",
    "act01-006-pip-dustclump-search-again",
    "act01-014-pip-cobweb-examine",
    "act01-015-scuttle-cameo-bark",
    "act01-016-pip-cobweb-reaction",
    "act01-017-bramble-greeting",
    "act01-018-pip-greeting-response",
    "act01-019-bramble-marble-common",
    "act01-020-pip-popular-how",
    "act01-021-bramble-deflect",
    "act01-022-bramble-teach-verbs",
    "act01-023-pip-already-do-that",
    "act01-024-bramble-natural-claimant",
    "act01-025-bramble-quest-lead",
    "act01-026-pip-quest-lead-interrupt",
    "act01-027-bramble-quest-lead-gate",
    "act01-028-pip-what-does-he-want",
    "act01-029-bramble-toll",
    "act01-030-pip-any-tips",
    "act01-031-bramble-toll-hint",
    "act01-038-bottlecap-no-toll",
    "act01-039-bottlecap-toll-accepted",
    "act01-040-bottlecap-toll-close",
    "act01-041-pip-lost-and-underfound-joke",
    "act01-042-bottlecap-go",
    "act01-044-pip-return-to-bramble",
    "act01-045-bramble-almost-disappointed",
    "act01-048-pip-fallback-try-exit",
    "act01-049-pip-transition-out",
}


def fail(message: str) -> None:
    print(f"Act 1 playthrough contract QA failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required file {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def require_text(source: str, needle: str, description: str) -> None:
    if needle not in source:
        fail(f"missing {description}: {needle}")


def require_regex(source: str, pattern: str, description: str) -> None:
    if not re.search(pattern, source, re.MULTILINE | re.DOTALL):
        fail(f"missing {description}: /{pattern}/")


def validate_script() -> None:
    script = load_json(SCRIPT_JSON)
    line_ids = {line["line_id"] for line in script.get("lines", [])}
    missing = sorted(EXPECTED_REQUIRED_LINES - line_ids)
    if missing:
        fail(f"script is missing required Act 1 route lines: {', '.join(missing)}")


def validate_geometry() -> None:
    geometry = load_json(GEOMETRY_JSON)
    if geometry.get("act") != 1:
        fail("geometry act must be 1")
    if geometry.get("architecture") != "discrete-screens":
        fail("geometry architecture must be discrete-screens")

    native_size = geometry.get("nativeSize", {})
    if native_size.get("width") != 1280 or native_size.get("height") != 720:
        fail("each AGS screen must be 1280x720")

    screens = {screen.get("id"): screen for screen in geometry.get("screens", [])}
    if set(screens) != EXPECTED_SCREENS:
        fail(f"expected screens {sorted(EXPECTED_SCREENS)}, found {sorted(screens)}")

    start = geometry.get("start", {})
    start_screen = screens.get(start.get("screenId"))
    if not start_screen:
        fail("start screen is invalid")
    if start.get("entryPoint") not in start_screen.get("entryPoints", {}):
        fail("start entry point is invalid")

    required_hotspots = {
        "discovery": {"couch-ceiling", "cubby-wall", "dust-clump", "popcorn-boulder"},
        "clerk": {"wall-note", "sign-in-log", "service-bell", "bramble-desk"},
        "gate": {"cobweb-curtain", "toll-gate"},
    }
    for screen_id, hotspot_ids in required_hotspots.items():
        found = {hotspot.get("id") for hotspot in screens[screen_id].get("hotspots", [])}
        missing = sorted(hotspot_ids - found)
        if missing:
            fail(f"{screen_id} is missing hotspots: {', '.join(missing)}")

    required_standing = {
        "clerk": {"pip-talk-bramble", "bramble-talking-head"},
        "gate": {"pip-gate", "old-bottlecap-guard"},
    }
    for screen_id, point_ids in required_standing.items():
        found = set(screens[screen_id].get("standingPositions", {}))
        missing = sorted(point_ids - found)
        if missing:
            fail(f"{screen_id} is missing standing positions: {', '.join(missing)}")

    gate_exits = {exit_def.get("id"): exit_def for exit_def in screens["gate"].get("exits", [])}
    through_grate = gate_exits.get("through-grate")
    if not through_grate:
        fail("gate screen is missing through-grate exit")
    if through_grate.get("destinationScreenId") != "act-02":
        fail("through-grate must lead to act-02")
    if through_grate.get("requiresFlag") != "gateOpen":
        fail("through-grate must require gateOpen")
    if through_grate.get("transitionLineId") != "act01-049-pip-transition-out":
        fail("through-grate must use act01-049-pip-transition-out")

    for link in geometry.get("linkMap", []):
        from_screen_id, from_exit_id = link.get("from", ":").split(":", 1)
        to_screen_id, to_entry_id = link.get("to", ":").split(":", 1)
        from_screen = screens.get(from_screen_id)
        to_screen = screens.get(to_screen_id)
        if not from_screen or not to_screen:
            fail(f"invalid link screen in {link}")
        if from_exit_id not in {exit_def.get("id") for exit_def in from_screen.get("exits", [])}:
            fail(f"invalid link exit in {link}")
        if to_entry_id not in to_screen.get("entryPoints", {}):
            fail(f"invalid link entry point in {link}")


def validate_runtime_source() -> None:
    main_ts = MAIN_TS.read_text(encoding="utf-8")

    for marker in [
        'if (id === "dust-clump")',
        "state.flags.dustSearched = true",
        'addItem("button")',
        'playAction("found-button"',
        '"act01-005-pip-dustclump-search-success"',
        'if (id === "toll-gate")',
        'state.selectedItem === "button" && hasItem("button")',
        "state.flags.gateOpen = true",
        'removeItem("button")',
        'playAction("toll-paid"',
        'playAction("toll-refused"',
        '"act01-038-bottlecap-no-toll"',
        '"act01-039-bottlecap-toll-accepted"',
        '"act01-042-bottlecap-go"',
        'exit.destinationScreenId === "act-02"',
        "state.flags.actComplete = true",
        "exit.requiresFlag && !state.flags[exit.requiresFlag]",
        "exit.transitionLineId",
        'speak("act01-048-pip-fallback-try-exit")',
        'speak("act01-001-pip-cold-open-landing", "act01-002-pip-cold-open-goal")',
        "state.current || state.topicPanelOpen || state.action",
        'data-hotspot="${hotspot.id}"',
        'data-exit="${exit.id}"',
        'data-item="${item}"',
        'state.mode = "use"',
        "brambleMouthFrame",
        "brambleVisemeTracks",
    ]:
        require_text(main_ts, marker, "runtime playthrough marker")

    require_regex(
        main_ts,
        r"talkToBramble\(\).*?act01-017-bramble-greeting.*?act01-031-bramble-toll-hint",
        "first Bramble conversation route",
    )
    require_regex(
        main_ts,
        r"state\.scuttleDash\s*=\s*\{.*?act01-014-pip-cobweb-examine.*?act01-015-scuttle-cameo-bark.*?act01-016-pip-cobweb-reaction",
        "Scuttle cameo route",
    )

    blocked_handlers = [
        r"const onHotspot = .*?if \(state\.current \|\| state\.topicPanelOpen \|\| state\.action\) return;",
        r"const onExit = .*?if \(state\.current \|\| state\.topicPanelOpen \|\| state\.action\) return;",
    ]
    for pattern in blocked_handlers:
        require_regex(main_ts, pattern, "interaction lockout")


def validate_release_hitboxes() -> None:
    styles = STYLES_CSS.read_text(encoding="utf-8")

    require_regex(styles, r"\.hotspot,\s*\.exit\s*\{.*?border:\s*1px solid transparent", "transparent release hitbox border")
    require_regex(styles, r"\.hotspot,\s*\.exit\s*\{.*?background:\s*transparent", "transparent release hitbox background")
    require_regex(styles, r"\.hotspot,\s*\.exit\s*\{.*?color:\s*transparent", "transparent release hitbox label color")
    require_regex(styles, r"\.stage\.interaction-blocked \.hotspot,\s*\.stage\.interaction-blocked \.exit\s*\{.*?pointer-events:\s*none", "blocked interaction CSS")
    require_regex(styles, r"\.dialogue-panel\s*\{.*?border-top:", "bottom dialogue panel block")

    forbidden_patterns = [
        "debug-hitbox",
        "debug-hotspot",
        "outline: 1px solid red",
        "rgba(255, 0, 0",
        "rgba(255,0,0",
    ]
    for forbidden in forbidden_patterns:
        if forbidden in styles:
            fail(f"release CSS contains debug hitbox styling: {forbidden}")


def main() -> None:
    validate_script()
    validate_geometry()
    validate_runtime_source()
    validate_release_hitboxes()
    print(
        "Act 1 playthrough contract QA passed: dust->button, Bramble intro, "
        "Bottlecap toll, gate exit, screen links, dialogue lockout, and hidden "
        "release hitboxes are enforced."
    )


if __name__ == "__main__":
    main()
