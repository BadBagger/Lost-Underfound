from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"FAIL - {message}")
    raise SystemExit(1)


def css_z_indexes(css: str) -> dict[str, int]:
    z_indexes: dict[str, int] = {}
    for match in re.finditer(r"(?P<selectors>[^{}]+)\{(?P<body>[^{}]*)\}", css, re.MULTILINE):
        z_match = re.search(r"z-index:\s*(?P<z>-?\d+)\s*;", match.group("body"))
        if not z_match:
            continue
        z = int(z_match.group("z"))
        for selector in match.group("selectors").split(","):
            selector = selector.strip()
            if selector.startswith(".") and " " not in selector and ":" not in selector:
                z_indexes[selector[1:]] = z
    return z_indexes


def main() -> int:
    manifest_path = ROOT / "art" / "act01-production" / "scene" / "layers.json"
    if not manifest_path.exists():
        fail(f"missing scene layer manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    layers = manifest.get("layers", [])
    if not layers:
        fail("scene layer manifest has no layers")

    required_ids = {
        "background-plate",
        "ambient-motion",
        "actor-shadow",
        "dust-prop",
        "gate-animation",
        "desk-front-occluder",
        "bramble-body",
        "old-bottlecap-body",
        "pip-body",
        "cobweb-disturbance",
        "button-flight",
        "scuttle-dash",
        "post-pass",
        "hotspot-masks",
    }
    found_ids = {layer.get("id") for layer in layers}
    missing = sorted(required_ids - found_ids)
    if missing:
        fail(f"missing required layer ids: {', '.join(missing)}")

    scene_dir = manifest_path.parent
    for layer in layers:
        asset = layer.get("asset")
        if asset and not (scene_dir / asset).exists():
            fail(f"layer {layer['id']} points to missing asset {asset}")

    src = (ROOT / "src" / "main.ts").read_text(encoding="utf-8")
    for layer_id in sorted(required_ids - {"hotspot-masks"}):
        needle = f'data-layer="{layer_id}"'
        if needle not in src:
            fail(f"runtime does not render layer slot {layer_id}")

    css = (ROOT / "src" / "styles.css").read_text(encoding="utf-8")
    z_indexes = css_z_indexes(css)
    manifest_z = {layer["id"]: layer.get("z") for layer in layers}
    if manifest_z["background-plate"] >= manifest_z["ambient-motion"]:
        fail("ambient-motion must draw above background-plate")
    if manifest_z["ambient-motion"] >= manifest_z["dust-prop"]:
        fail("ambient-motion must draw below interactive props and actors")
    ambient = next(layer for layer in layers if layer.get("id") == "ambient-motion")
    if ambient.get("kind") != "ambient-motion-layer":
        fail("ambient-motion must be declared as kind ambient-motion-layer")
    if ambient.get("non_interactive") is not True:
        fail("ambient-motion must be marked non_interactive")
    if int(ambient.get("max_drift_px", 999)) > 4:
        fail("ambient-motion max_drift_px must stay at or below 4")
    if ".ambient-motion-layer" not in css or "pointer-events: none;" not in css:
        fail("ambient-motion runtime CSS must be non-interactive")
    for layer_id in ("desk-front-occluder", "button-flight", "scuttle-dash", "cobweb-disturbance"):
        layer = next(layer for layer in layers if layer.get("id") == layer_id)
        if layer.get("non_interactive") is not True:
            fail(f"{layer_id} must be marked non_interactive")
    if manifest_z["gate-animation"] >= manifest_z["cobweb-disturbance"]:
        fail("cobweb-disturbance must draw above the gate animation")
    if manifest_z["cobweb-disturbance"] >= manifest_z["old-bottlecap-body"]:
        fail("cobweb-disturbance must draw below fixed actors")
    if manifest_z["old-bottlecap-body"] >= manifest_z["button-flight"]:
        fail("button-flight must draw above Bottlecap for the toll handoff")
    if manifest_z["button-flight"] >= manifest_z["scuttle-dash"]:
        fail("scuttle-dash must draw above the button-flight layer")
    for layer_id in sorted(required_ids - {"hotspot-masks"}):
        class_match = re.search(
            rf'class="(?P<classes>[^"]+)"[^>]*data-layer="{re.escape(layer_id)}"',
            src,
        )
        if not class_match:
            class_match = re.search(
                rf'data-layer="{re.escape(layer_id)}"[^>]*class="(?P<classes>[^"]+)"',
                src,
            )
        if not class_match:
            continue
        classes = class_match.group("classes").split()
        runtime_z = [z_indexes[class_name] for class_name in classes if class_name in z_indexes]
        if not runtime_z:
            fail(f"runtime layer {layer_id} has no CSS z-index on classes: {', '.join(classes)}")
        if max(runtime_z) != manifest_z[layer_id]:
            fail(
                f"runtime layer {layer_id} z-index {max(runtime_z)} does not match manifest z {manifest_z[layer_id]}"
            )

    print(f"PASS - {len(layers)} scene layer(s) declared and runtime layer slots match manifest z-order.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
