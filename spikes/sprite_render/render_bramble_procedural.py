#!/usr/bin/env python3
"""Render procedural Bramble animation clips from the Meshy textured GLB.

This keeps the Meshy texture/material as the visual authority. Motion is applied
as deterministic mesh deformation at render time because the current Meshy export
has no armature or animation actions.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.append(str(Path(__file__).resolve().parent))

from render_fbx_walk import (
    center_imported,
    clear_scene,
    configure_render,
    import_asset,
    mesh_objects,
    set_origin_floor,
    setup_camera,
    setup_lighting,
    world_bbox,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


CLIPS = {
    "idle": {"frames": 24, "fps": 12},
    "talk": {"frames": 30, "fps": 12},
    "greeting": {"frames": 28, "fps": 12},
}


def parse_args() -> argparse.Namespace:
    import sys

    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--clip", choices=tuple(CLIPS.keys()), default="idle")
    parser.add_argument("--resolution", type=int, default=640)
    parser.add_argument("--target-height", type=int, default=500)
    parser.add_argument("--frame-count", type=int)
    parser.add_argument("--view", choices=("front", "side-left", "side-right"), default="front")
    parser.add_argument("--angle-deg", type=float, default=7.0)
    parser.add_argument("--ortho-height-mult", type=float, default=1.62)
    return parser.parse_args(argv)


def smoothstep(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def loop_phase(frame: int, total: int) -> float:
    return (frame % total) / total


def prepare_model(asset: Path, args: argparse.Namespace) -> tuple[bpy.types.Object, list[Vector], dict]:
    clear_scene()
    import_asset(asset)
    center_imported()
    set_origin_floor()
    setup_lighting(-35.0)
    setup_camera(
        args.angle_deg,
        args.view,
        args.ortho_height_mult,
        (0.0, 0.0),
        None,
        0.52,
    )
    configure_render(args.resolution, args.resolution)

    meshes = mesh_objects()
    if len(meshes) != 1:
        raise RuntimeError(f"expected one Bramble mesh, found {len(meshes)}")
    obj = meshes[0]
    base = [vertex.co.copy() for vertex in obj.data.vertices]
    mins, maxs = world_bbox(meshes)
    bounds = {
        "min": [mins.x, mins.y, mins.z],
        "max": [maxs.x, maxs.y, maxs.z],
        "height": maxs.z - mins.z,
        "width": max(maxs.x - mins.x, maxs.y - mins.y),
    }
    return obj, base, bounds


def vertex_normalized(base_coord: Vector, mins: Vector, maxs: Vector) -> tuple[float, float, float]:
    sx = max(maxs.x - mins.x, 0.0001)
    sy = max(maxs.y - mins.y, 0.0001)
    sz = max(maxs.z - mins.z, 0.0001)
    return (
        (base_coord.x - mins.x) / sx,
        (base_coord.y - mins.y) / sy,
        (base_coord.z - mins.z) / sz,
    )


def hand_weight(nx: float, ny: float, nz: float, side: str) -> float:
    side_center = 0.25 if side == "left" else 0.75
    dx = abs(nx - side_center) / 0.22
    dz = abs(nz - 0.47) / 0.18
    dy = abs(ny - 0.36) / 0.33
    value = max(0.0, 1.0 - (dx * dx + dz * dz + dy * dy) * 0.72)
    return smoothstep(value)


def apply_clip_pose(obj: bpy.types.Object, base: list[Vector], frame: int, total: int, clip: str) -> dict:
    mesh = obj.data
    mins = Vector((min(v.x for v in base), min(v.y for v in base), min(v.z for v in base)))
    maxs = Vector((max(v.x for v in base), max(v.y for v in base), max(v.z for v in base)))
    height = max(maxs.z - mins.z, 0.0001)
    width = max(maxs.x - mins.x, maxs.y - mins.y, 0.0001)
    p = loop_phase(frame, total)

    breath = math.sin(p * math.tau)
    blink = 1.0 if clip == "idle" and frame in {9, 10} else 0.0
    talk_jaw = 0.0
    if clip == "talk":
        talk_jaw = 0.5 + 0.5 * math.sin(p * math.tau * 4.0 + 0.6)

    greet = 0.0
    if clip == "greeting":
        if frame < total * 0.35:
            greet = smoothstep(frame / (total * 0.35))
        elif frame > total * 0.68:
            greet = 1.0 - smoothstep((frame - total * 0.68) / (total * 0.32))
        else:
            greet = 1.0

    for vertex, source in zip(mesh.vertices, base):
        nx, ny, nz = vertex_normalized(source, mins, maxs)
        top = smoothstep((nz - 0.12) / 0.88)
        upper_face = smoothstep((nz - 0.60) / 0.20)
        left_hand = hand_weight(nx, ny, nz, "left")
        right_hand = hand_weight(nx, ny, nz, "right")
        brow_zone = smoothstep((nz - 0.67) / 0.18) * (1.0 - smoothstep((nz - 0.88) / 0.08))
        chin_zone = smoothstep((nz - 0.50) / 0.10) * (1.0 - smoothstep((nz - 0.68) / 0.10))
        face_focus = max(brow_zone, chin_zone * 0.8)

        dest = source.copy()

        # Bramble is a seated counter actor. Keep the lint mass stable; animate
        # the performance areas instead of making the whole model wave.
        dest.z += breath * height * 0.0025 * upper_face

        # Hands do the fussy clerk work: small taps, lifts, and emphasis beats.
        hand_idle = 0.35 + 0.65 * math.sin(p * math.tau * 2.0 + 0.5)
        dest.z += hand_idle * height * 0.010 * (left_hand + right_hand) * (0.45 if clip == "idle" else 0.25)
        dest.x += math.sin(p * math.tau * 2.0 + 1.7) * width * 0.008 * left_hand * (0.7 if clip == "idle" else 0.25)
        dest.x -= math.sin(p * math.tau * 2.0 + 1.1) * width * 0.008 * right_hand * (0.7 if clip == "idle" else 0.25)

        dest.z += talk_jaw * height * 0.018 * chin_zone
        dest.z += math.sin(p * math.tau * 4.0 + 0.8) * height * 0.038 * right_hand * (1.0 if clip == "talk" else 0.0)
        dest.x += math.sin(p * math.tau * 4.0 + 0.3) * width * 0.018 * right_hand * (1.0 if clip == "talk" else 0.0)
        dest.z += math.sin(p * math.tau * 3.0 + 2.0) * height * 0.020 * left_hand * (0.55 if clip == "talk" else 0.0)

        dest.x -= greet * width * 0.045 * left_hand
        dest.z += greet * height * 0.090 * left_hand
        dest.z += greet * height * 0.025 * face_focus

        # Blink/eyebrow emphasis is localized around the glasses area.
        dest.z -= blink * height * 0.020 * brow_zone
        dest.y -= blink * height * 0.006 * brow_zone
        vertex.co = dest

    mesh.update()
    obj.rotation_euler[2] = math.radians(math.sin(p * math.tau + 0.4) * (0.16 if clip != "greeting" else 0.35))
    obj.location.x = 0.0
    obj.location.z = abs(math.sin(p * math.tau)) * height * (0.0015 if clip == "idle" else 0.0025)
    return {"breath": round(breath, 4), "talk_jaw": round(talk_jaw, 4), "greet": round(greet, 4), "blink": bool(blink)}


def render_clip(asset: Path, out_dir: Path, args: argparse.Namespace) -> None:
    clip_info = CLIPS[args.clip]
    frame_count = args.frame_count or clip_info["frames"]
    obj, base, bounds = prepare_model(asset, args)
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for index in range(frame_count):
        params = apply_clip_pose(obj, base, index, frame_count, args.clip)
        frame_path = out_dir / f"bramble_{args.clip}_{index:03d}.png"
        bpy.context.scene.render.filepath = str(frame_path)
        bpy.ops.render.render(write_still=True)
        frames.append({"index": index, "file": frame_path.name, "pose": params})
    manifest = {
        "asset": str(asset),
        "clip": args.clip,
        "fps": clip_info["fps"],
        "frame_count": frame_count,
        "render": {
            "resolution": [args.resolution, args.resolution],
            "view": args.view,
            "angle_deg": args.angle_deg,
            "ortho_height_mult": args.ortho_height_mult,
        },
        "model_bounds": bounds,
        "source_texture_rule": "Meshy packed texture/material is preserved; no synthetic color or face overlays are drawn.",
        "animation_method": "deterministic mesh deformation from source GLB, because Meshy export has no armature/actions.",
        "frames": frames,
    }
    (out_dir / f"bramble_{args.clip}_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"clip": args.clip, "frames": frame_count, "out": str(out_dir)}, indent=2))


def main() -> None:
    args = parse_args()
    asset = (REPO_ROOT / args.asset).resolve() if not Path(args.asset).is_absolute() else Path(args.asset)
    out_dir = (REPO_ROOT / args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out)
    render_clip(asset, out_dir, args)


if __name__ == "__main__":
    main()
