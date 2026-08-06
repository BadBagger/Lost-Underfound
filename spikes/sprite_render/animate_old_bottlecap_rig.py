#!/usr/bin/env python3
"""Render a restrained Old Bottlecap rig-idle proof from a Meshy GLB.

This is an intake/proof renderer, not final animation admission. It assumes the
Meshy UniRig export uses generic Bone_### names and drives only broad controls.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Vector


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--resolution", type=int, default=768)
    parser.add_argument("--view", choices=("front", "side-left", "side-right"), default="front")
    parser.add_argument("--clip", choices=("idle", "admission_stillness_break"), default="idle")
    return parser.parse_args(argv)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_model(path: Path) -> None:
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()))


def meshes() -> list[bpy.types.Object]:
    return [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]


def armatures() -> list[bpy.types.Object]:
    return [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]


def world_bbox(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    mins = Vector((math.inf, math.inf, math.inf))
    maxs = Vector((-math.inf, -math.inf, -math.inf))
    for obj in objects:
        for corner in obj.bound_box:
            point = obj.matrix_world @ Vector(corner)
            mins.x = min(mins.x, point.x)
            mins.y = min(mins.y, point.y)
            mins.z = min(mins.z, point.z)
            maxs.x = max(maxs.x, point.x)
            maxs.y = max(maxs.y, point.y)
            maxs.z = max(maxs.z, point.z)
    return mins, maxs


def center_and_floor() -> None:
    render_meshes = [obj for obj in meshes() if obj.name != "Icosphere"]
    mins, maxs = world_bbox(render_meshes)
    center = (mins + maxs) * 0.5
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.location -= center
    mins, _ = world_bbox(render_meshes)
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.location.z -= mins.z


def hide_nonrender_helpers() -> None:
    for obj in bpy.context.scene.objects:
        if obj.name.lower().startswith("icosphere"):
            obj.hide_viewport = True
            obj.hide_render = True


def setup_render(resolution: int) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.78, 0.76, 0.70)

    bpy.ops.object.light_add(type="AREA", location=(-3.2, -4.0, 5.5))
    light = bpy.context.object
    light.name = "warm_upper_left_key"
    light.data.energy = 430
    light.data.size = 4.0

    bpy.ops.object.camera_add(location=(0, -4.2, 1.18), rotation=(math.radians(78), 0, 0))
    cam = bpy.context.object
    scene.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 2.05


def set_view(view: str) -> None:
    yaw = {"front": 0.0, "side-left": math.radians(20), "side-right": math.radians(-20)}[view]
    for obj in bpy.context.scene.objects:
        if obj.parent is None and obj.type != "CAMERA" and obj.type != "LIGHT":
            obj.rotation_euler[2] += yaw


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge0 == edge1:
        return 1.0 if x >= edge1 else 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def admission_curve(frame: int, total: int) -> dict[str, float]:
    if total <= 1:
        t = 0.0
    else:
        t = frame / (total - 1)
    # A held comedy beat: stillness first, then one tiny posture break, then back.
    enter = smoothstep(0.28, 0.48, t)
    exit_ = smoothstep(0.68, 0.92, t)
    hold = enter * (1.0 - exit_)
    blink = smoothstep(0.48, 0.54, t) * (1.0 - smoothstep(0.61, 0.67, t))
    return {
        "hold": hold,
        "down_glance": hold * 1.0,
        "blink": blink,
        "tiny_exhale": math.sin(max(0.0, min(1.0, (t - 0.52) / 0.32)) * math.pi) * hold,
    }


def reset_pose(armature: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="POSE")
    for bone in armature.pose.bones:
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = Euler((0, 0, 0), "XYZ")
        bone.location = (0, 0, 0)
        bone.scale = (1, 1, 1)


def set_pose(armature: bpy.types.Object, frame: int, total: int, clip: str) -> dict[str, float]:
    phase = (frame / total) * math.tau
    # Slow asymmetrical values: one main breath/rock cycle plus a small secondary.
    rock = math.sin(phase) * math.radians(2.4)
    settle = math.sin(phase * 2.0 + 0.7) * math.radians(0.55)
    nod = math.sin(phase - 0.9) * math.radians(0.75)
    arm_l = math.sin(phase + 0.25) * math.radians(1.8)
    arm_r = math.sin(phase + math.pi + 0.25) * math.radians(1.8)

    admit = admission_curve(frame, total) if clip == "admission_stillness_break" else None
    if admit:
        # Smaller than idle at the top of the beat. The admission should read as
        # a break in stillness, not a separate expressive rig.
        rock *= 0.22 + (0.28 * (1.0 - admit["hold"]))
        settle *= 0.20
        nod = math.radians(0.2) + math.radians(4.2) * admit["down_glance"] - math.radians(0.8) * admit["tiny_exhale"]
        arm_l *= 0.12
        arm_r *= 0.12

    reset_pose(armature)

    # Generic UniRig mapping from measured bone positions.
    def rot(name: str, xyz: tuple[float, float, float], influence: float = 1.0) -> None:
        bone = armature.pose.bones.get(name)
        if bone:
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = Euler(tuple(v * influence for v in xyz), "XYZ")

    # Lower/upper stack: tiny heavy sway, intentionally not squashy.
    rot("Bone_013", (0, rock * 0.42, 0))
    rot("Bone_012", (0, rock * 0.34, 0))
    rot("Bone_011", (nod, rock * 0.32, settle))
    rot("Bone_010", (nod * 0.7, rock * 0.25, settle * 0.5))

    # Arms settle with the body; hands remain mostly deadpan.
    rot("Bone_020", (0, 0, -arm_l * 0.45))
    rot("Bone_019", (0, arm_l * 0.25, 0))
    rot("Bone_024", (0, 0, arm_r * 0.45))
    rot("Bone_023", (0, arm_r * 0.25, 0))
    rot("Bone_017", (0, 0, math.sin(phase + 1.4) * math.radians(0.9)))
    rot("Bone_021", (0, 0, math.sin(phase + 4.2) * math.radians(0.9)))

    if admit:
        # Eye-cap bones are not explicitly identified in the Meshy rig, so this
        # stays as posture/arm acting only. No synthetic face overlay is drawn.
        rot("Bone_011", (nod + math.radians(1.8) * admit["blink"], rock * 0.2, settle * 0.35))
        rot("Bone_020", (0, 0, math.radians(-1.2) * admit["hold"]))
        rot("Bone_024", (0, 0, math.radians(1.2) * admit["hold"]))

    bpy.ops.object.mode_set(mode="OBJECT")
    values = {
        "rock_deg": round(math.degrees(rock), 3),
        "nod_deg": round(math.degrees(nod), 3),
        "settle_deg": round(math.degrees(settle), 3),
    }
    if admit:
        values.update({key: round(value, 3) for key, value in admit.items()})
    return values


def main() -> None:
    args = parse_args()
    out = Path(args.out)
    raw = out / "frames_raw"
    raw.mkdir(parents=True, exist_ok=True)

    clear_scene()
    import_model(Path(args.input))
    hide_nonrender_helpers()
    center_and_floor()
    setup_render(args.resolution)
    set_view(args.view)
    armature = armatures()[0]

    metadata = {
        "input": str(Path(args.input).resolve()),
        "clip": args.clip,
        "fps": args.fps,
        "frames": args.frames,
        "view": args.view,
        "armature": armature.name,
        "notes": [
            "Restrained Old Bottlecap rig proof only; no final animation admission.",
            "Icosphere helper hidden from render.",
            "Bone mapping is positional over generic Meshy UniRig names.",
            "No synthetic face, costume, or object overlays are drawn.",
        ],
        "frame_pose_values": [],
    }
    scene = bpy.context.scene
    for frame in range(args.frames):
        scene.frame_set(frame)
        values = set_pose(armature, frame, args.frames, args.clip)
        metadata["frame_pose_values"].append({"frame": frame, **values})
        scene.render.filepath = str(raw / f"old_bottlecap_{args.clip}_raw_{frame:03d}.png")
        bpy.ops.render.render(write_still=True)

    (out / f"old_bottlecap_{args.clip}_blender_manifest.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"clip": args.clip, "frames": args.frames, "out": str(out)}, indent=2))


if __name__ == "__main__":
    main()
