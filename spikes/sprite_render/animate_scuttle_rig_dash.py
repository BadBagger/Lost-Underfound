#!/usr/bin/env python3
"""Render Scuttle's six-frame dash from the Meshy rig.

The rig uses generic Meshy UniRig bone names, so this script maps controls by
bone position from the inspected Scuttle model. Legs are animated from the
skeleton first; downstream smear treatment is allowed only on travel frames.
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
    parser.add_argument("--resolution", type=int, default=768)
    parser.add_argument("--view", choices=("side-left", "side-right", "front"), default="side-left")
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


def hide_helpers() -> None:
    for obj in bpy.context.scene.objects:
        if obj.name.lower().startswith("icosphere"):
            obj.hide_render = True
            obj.hide_viewport = True


def setup_render(resolution: int) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.78, 0.76, 0.70)

    bpy.ops.object.light_add(type="AREA", location=(-3.2, -4.0, 4.8))
    light = bpy.context.object
    light.name = "warm_upper_left_key"
    light.data.energy = 390
    light.data.size = 4.0

    bpy.ops.object.camera_add(location=(0, -4.4, 1.0), rotation=(math.radians(78), 0, 0))
    cam = bpy.context.object
    cam.name = "scuttle_dash_camera"
    scene.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 4.0


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def set_view(view: str) -> None:
    cam = bpy.context.scene.camera
    positions = {
        "front": Vector((0, -4.4, 1.0)),
        "side-left": Vector((4.4, 0, 1.0)),
        "side-right": Vector((-4.4, 0, 1.0)),
    }
    cam.location = positions[view]
    look_at(cam, Vector((0, 0, 0.72)))


LEG_CHAINS = {
    "rear_r": ["Bone_029", "Bone_028", "Bone_027"],
    "rear_l": ["Bone_034", "Bone_033", "Bone_032"],
    "mid_r": ["Bone_010", "Bone_009", "Bone_008"],
    "mid_l": ["Bone_014", "Bone_013", "Bone_012"],
    "front_r": ["Bone_018", "Bone_017", "Bone_016"],
    "front_l": ["Bone_022", "Bone_021", "Bone_020"],
    "nose_r": ["Bone_040", "Bone_039", "Bone_038"],
    "nose_l": ["Bone_044", "Bone_043", "Bone_042"],
}

ANTENNA_CHAINS = {
    "r": ["Bone_055", "Bone_054", "Bone_053", "Bone_052"],
    "l": ["Bone_061", "Bone_060", "Bone_059", "Bone_058"],
}


def reset_pose(armature: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="POSE")
    for bone in armature.pose.bones:
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = Euler((0, 0, 0), "XYZ")
    bpy.ops.object.mode_set(mode="OBJECT")


def rot(armature: bpy.types.Object, name: str, xyz: tuple[float, float, float]) -> None:
    bone = armature.pose.bones.get(name)
    if not bone:
        return
    bone.rotation_mode = "XYZ"
    bone.rotation_euler = Euler(xyz, "XYZ")


def set_chain(armature: bpy.types.Object, names: list[str], swing: float, lift: float, curl: float) -> None:
    values = [
        (math.radians(lift), math.radians(swing), math.radians(curl)),
        (math.radians(-lift * 0.35), math.radians(swing * 0.65), math.radians(-curl * 0.4)),
        (math.radians(lift * 0.25), math.radians(swing * 0.35), math.radians(curl * 0.25)),
    ]
    for name, value in zip(names, values):
        rot(armature, name, value)


def apply_dash_pose(armature: bpy.types.Object, index: int) -> dict:
    # Six authored key poses matching Act 1 dash: ready, launch, smear, smear, landing, off.
    keys = [
        {"body": -3, "pitch": 0, "legs": [12, -12, 8, -8], "antenna": 2, "note": "ready solid"},
        {"body": -12, "pitch": -8, "legs": [54, -48, 42, -38], "antenna": -12, "note": "launch solid"},
        {"body": -18, "pitch": -13, "legs": [-62, 58, -52, 48], "antenna": -20, "note": "travel smear pose"},
        {"body": -20, "pitch": -15, "legs": [66, -62, 56, -52], "antenna": -22, "note": "travel smear pose"},
        {"body": 8, "pitch": 6, "legs": [-48, 44, -36, 32], "antenna": 14, "note": "landing solid"},
        {"body": 0, "pitch": 0, "legs": [0, 0, 0, 0], "antenna": 3, "note": "settle solid"},
    ]
    k = keys[index]
    reset_pose(armature)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="POSE")

    body_y = math.radians(k["body"])
    pitch = math.radians(k["pitch"])
    rot(armature, "Bone_001", (pitch * 0.45, body_y * 0.35, 0))
    rot(armature, "Bone_003", (pitch * 0.65, body_y * 0.45, 0))
    rot(armature, "Bone_002", (pitch * 0.35, body_y * 0.28, 0))
    rot(armature, "Bone_024", (pitch * 0.25, body_y * 0.22, 0))
    rot(armature, "Bone_023", (pitch * 0.2, body_y * 0.18, 0))

    a, b, c, d = k["legs"]
    set_chain(armature, LEG_CHAINS["front_r"], a, 8, -8)
    set_chain(armature, LEG_CHAINS["mid_l"], a * 0.85, 7, -6)
    set_chain(armature, LEG_CHAINS["rear_r"], c, 7, -5)
    set_chain(armature, LEG_CHAINS["front_l"], b, -7, 7)
    set_chain(armature, LEG_CHAINS["mid_r"], b * 0.85, -6, 6)
    set_chain(armature, LEG_CHAINS["rear_l"], d, -7, 5)
    set_chain(armature, LEG_CHAINS["nose_r"], c * 0.55, 3, -4)
    set_chain(armature, LEG_CHAINS["nose_l"], d * 0.55, -3, 4)

    antenna = k["antenna"]
    for chain, side in [(ANTENNA_CHAINS["r"], 1), (ANTENNA_CHAINS["l"], -1)]:
        for part, name in enumerate(chain):
            rot(
                armature,
                name,
                (
                    math.radians(antenna * 0.35),
                    math.radians(side * (antenna + part * 2) * 0.5),
                    math.radians(side * antenna * 0.25),
                ),
            )

    bpy.ops.object.mode_set(mode="OBJECT")
    return {"frame": index, **k}


def main() -> None:
    args = parse_args()
    out = Path(args.out)
    raw = out / "frames_raw"
    raw.mkdir(parents=True, exist_ok=True)

    clear_scene()
    import_model(Path(args.input))
    hide_helpers()
    center_and_floor()
    setup_render(args.resolution)
    set_view(args.view)
    armature = armatures()[0]

    meta = {
        "input": str(Path(args.input).resolve()),
        "armature": armature.name,
        "view": args.view,
        "fps": 16,
        "frames": [],
        "notes": [
            "Rig-driven Scuttle dash. Legs and antennae are keyed before post smear.",
            "Frames 2 and 3 are intended to receive smear post-processing.",
        ],
    }
    scene = bpy.context.scene
    for i in range(6):
        scene.frame_set(i)
        meta["frames"].append(apply_dash_pose(armature, i))
        scene.render.filepath = str(raw / f"scuttle_dash_rig_raw_{i:03d}.png")
        bpy.ops.render.render(write_still=True)
    (out / "scuttle_dash_rig_blender_manifest.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps({"frames": 6, "out": str(out)}, indent=2))


if __name__ == "__main__":
    main()
