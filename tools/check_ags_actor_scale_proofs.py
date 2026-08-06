"""Ensure AGS actor-scale proof sheets exist for every discrete screen."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
AGS_DIR = ROOT / "ags"
PROOF_DIR = AGS_DIR / "actor_scale_proofs"
EXPECTED_SIZE = (1280, 720)


def fail(message: str) -> None:
    raise SystemExit(f"AGS actor-scale proof QA failed: {message}")


def main() -> None:
    checked = 0
    for geometry_path in sorted(AGS_DIR.glob("room*/geometry.json")):
        room = geometry_path.parent.name
        spec = json.loads(geometry_path.read_text(encoding="utf-8"))
        for screen in spec.get("screens", []):
            proof = PROOF_DIR / room / f"{screen['id']}.png"
            if not proof.is_file():
                fail(f"missing proof for {room}/{screen['id']}; run npm.cmd run ags:actor-scale-proofs")
            with Image.open(proof) as image:
                if image.size != EXPECTED_SIZE:
                    fail(f"{proof} must be {EXPECTED_SIZE[0]}x{EXPECTED_SIZE[1]}")
            checked += 1
    contact = PROOF_DIR / "contact.png"
    if not contact.is_file():
        fail("missing actor-scale contact sheet; run npm.cmd run ags:actor-scale-proofs")
    print(f"AGS actor-scale proof QA passed: {checked} screen proof(s) and contact sheet are present.")


if __name__ == "__main__":
    main()
