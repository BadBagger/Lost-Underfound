from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"FAIL - {message}")
    raise SystemExit(1)


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
        "dust-prop",
        "bramble-body",
        "desk-foreground",
        "old-bottlecap-body",
        "gate-foreground",
        "pip-body",
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

    print(f"PASS - {len(layers)} scene layer(s) declared and runtime layer slots are present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
