#!/usr/bin/env python3
"""Generate Bramble LoRA proof strips through a running local ComfyUI server."""

from __future__ import annotations

import argparse
import json
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMFY_URL = "http://127.0.0.1:8188"
COMFY_OUTPUT = Path("D:/CodexDeps/ComfyUI/output")
OUT_DIR = ROOT / "art" / "lora" / "proofs" / "bramble"
CLIENT_ID = "codex-lost-underfound-bramble-proof"
LORA_NAME = "lost-underfound\\lu_bramble_clerk_proof.safetensors"
CKPT_NAME = "sd_xl_base_1.0.safetensors"


PROMPTS = {
    "idle": (
        "single horizontal animation source strip, six evenly spaced poses left to right, "
        "lu_bramble_clerk, Bramble only, rounded grey-brown lint dustball clerk creature, no animal body, no rabbit ears, "
        "shaggy dust fluff silhouette, small round spectacles, tiny mitten hands, bow tie, fussy procedure-proud personality, "
        "warm painterly storybook character art, "
        "flat solid chroma pink background, no grid, no border, same character identity, same scale, same camera distance, "
        "same eye level, generous margins, actor only, poses: neutral idle, breath in, blink, tiny weight settle, "
        "small skeptical glance, return to neutral"
    ),
    "talk": (
        "single horizontal animation source strip, six evenly spaced poses left to right, "
        "lu_bramble_clerk, Bramble only, rounded grey-brown lint dustball clerk creature, no animal body, no rabbit ears, "
        "shaggy dust fluff silhouette, small round spectacles, tiny mitten hands, bow tie, fussy procedure-proud personality, "
        "warm painterly storybook character art, "
        "flat solid chroma pink background, no grid, no border, same character identity, same scale, same camera distance, "
        "same eye level, generous margins, actor only, poses: closed mouth listening, mouth open small, mouth open wide, "
        "corrective finger gesture, worried emphasis, closed mouth settle"
    ),
}

NEGATIVE = (
    "desk, chair, counter, bell, ledger, paper stacks, cubbies, gate, room, wall, floor, UI, speech bubble, "
    "text, label, watermark, extra character, cropped body, missing hands, inconsistent scale, duplicate fused poses, "
    "cast shadow on background, rabbit, bunny rabbit, long ears, animal muzzle, paws, tail, tuxedo, suit, wine glass, cup"
)


def request_json(path: str, payload: dict | None = None, timeout: int = 10) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{COMFY_URL}{path}", data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.URLError as exc:
        raise SystemExit(f"FAIL - Comfy request failed for {path}: {exc}") from exc


def build_prompt(kind: str, seed: int) -> dict:
    positive = PROMPTS[kind]
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": CKPT_NAME},
        },
        "2": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["1", 0],
                "clip": ["1", 1],
                "lora_name": LORA_NAME,
                "strength_model": 1.25,
                "strength_clip": 1.0,
            },
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": positive, "clip": ["2", 1]},
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": NEGATIVE, "clip": ["2", 1]},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 1536, "height": 512, "batch_size": 1},
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["2", 0],
                "seed": seed,
                "steps": 28,
                "cfg": 6.5,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
                "denoise": 1.0,
            },
        },
        "7": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["6", 0], "vae": ["1", 2]},
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["7", 0],
                "filename_prefix": f"lost-underfound/bramble_lora_proof_{kind}",
            },
        },
    }


def wait_for_history(prompt_id: str, timeout_seconds: int) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        history = request_json(f"/history/{prompt_id}", timeout=10)
        if prompt_id in history:
            status = history[prompt_id].get("status", {})
            if status.get("status_str") == "error":
                raise SystemExit(f"FAIL - Comfy prompt {prompt_id} errored: {json.dumps(status, indent=2)}")
            return history[prompt_id]
        time.sleep(2)
    raise SystemExit(f"FAIL - timed out waiting for Comfy prompt {prompt_id}")


def copy_outputs(kind: str, history: dict) -> list[Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    outputs = history.get("outputs", {})
    for node_output in outputs.values():
        for image in node_output.get("images", []):
            filename = image["filename"]
            subfolder = image.get("subfolder", "")
            source = COMFY_OUTPUT / subfolder / filename
            if not source.exists():
                raise SystemExit(f"FAIL - Comfy reported missing output: {source}")
            destination = OUT_DIR / f"{kind}_{filename}"
            shutil.copy2(source, destination)
            copied.append(destination)
    if not copied:
        raise SystemExit(f"FAIL - Comfy prompt produced no copied outputs for {kind}")
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=480)
    args = parser.parse_args()

    request_json("/system_stats", timeout=5)
    for index, kind in enumerate(("idle", "talk"), start=1):
        prompt = build_prompt(kind, seed=61040 + index)
        response = request_json("/prompt", {"prompt": prompt, "client_id": CLIENT_ID}, timeout=10)
        prompt_id = response.get("prompt_id")
        if not prompt_id:
            raise SystemExit(f"FAIL - Comfy did not return prompt_id: {response}")
        print(f"Queued {kind}: {prompt_id}")
        history = wait_for_history(prompt_id, args.timeout)
        copied = copy_outputs(kind, history)
        for path in copied:
            print(f"Copied {kind}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
