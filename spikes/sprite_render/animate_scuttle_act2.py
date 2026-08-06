#!/usr/bin/env python3
"""Render Scuttle Act 2 proof clips from the rigged Meshy GLB.

These are intake proofs for the Act 2 reconnect/fumble sequence. Scuttle's body,
legs, and antennae are posed through the supplied skeleton. The fumble clip adds
a simple temporary parcel prop so timing can be judged; final prop art still
needs its own admission pass.
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
    parser.add_argument("--clip", choices=("brake_stop", "fidget_idle", "parcel_fumble_drop"), required=True)
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

    bpy.ops.object.camera_add(location=(4.4, 0, 1.0))
    cam = bpy.context.object
    cam.name = "scuttle_act2_camera"
    bpy.context.scene.camera = cam
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


def set_body(armature: bpy.types.Object, yaw: float, pitch: float, roll: float = 0.0) -> None:
    rot(armature, "Bone_001", (math.radians(pitch * 0.45), math.radians(yaw * 0.35), math.radians(roll * 0.35)))
    rot(armature, "Bone_003", (math.radians(pitch * 0.65), math.radians(yaw * 0.45), math.radians(roll * 0.45)))
    rot(armature, "Bone_002", (math.radians(pitch * 0.35), math.radians(yaw * 0.28), math.radians(roll * 0.30)))
    rot(armature, "Bone_024", (math.radians(pitch * 0.25), math.radians(yaw * 0.22), math.radians(roll * 0.20)))
    rot(armature, "Bone_023", (math.radians(pitch * 0.2), math.radians(yaw * 0.18), math.radians(roll * 0.16)))


def set_tripod_legs(armature: bpy.types.Object, a: float, b: float, c: float, d: float, lift: float = 7) -> None:
    set_chain(armature, LEG_CHAINS["front_r"], a, lift, -8)
    set_chain(armature, LEG_CHAINS["mid_l"], a * 0.85, lift, -6)
    set_chain(armature, LEG_CHAINS["rear_r"], c, lift, -5)
    set_chain(armature, LEG_CHAINS["front_l"], b, -lift, 7)
    set_chain(armature, LEG_CHAINS["mid_r"], b * 0.85, -lift, 6)
    set_chain(armature, LEG_CHAINS["rear_l"], d, -lift, 5)
    set_chain(armature, LEG_CHAINS["nose_r"], c * 0.55, 3, -4)
    set_chain(armature, LEG_CHAINS["nose_l"], d * 0.55, -3, 4)


def set_antennae(armature: bpy.types.Object, antenna: float) -> None:
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


def pose_scuttle(armature: bpy.types.Object, yaw: float, pitch: float, legs: tuple[float, float, float, float], antenna: float, roll: float = 0.0) -> None:
    reset_pose(armature)
    set_body(armature, yaw, pitch, roll)
    set_tripod_legs(armature, *legs)
    set_antennae(armature, antenna)


def brake_stop_pose(armature: bpy.types.Object, index: int) -> dict:
    keys = [
        (-18, -13, (-62, 58, -52, 48), -20, 0, "incoming smear pose"),
        (-22, -16, (70, -64, 56, -54), -24, 0, "incoming smear pose"),
        (14, 11, (-56, 52, -44, 38), 22, -3, "brake plant solid"),
        (20, 15, (-28, 24, -18, 16), 28, -7, "overbrake squash"),
        (-7, -5, (22, -18, 16, -14), -8, 5, "recoil"),
        (0, 0, (6, -6, 4, -4), 8, 0, "settle"),
        (0, 0, (0, 0, 0, 0), 3, 0, "stopped hold"),
        (0, 0, (0, 0, 0, 0), 3, 0, "stopped hold"),
    ]
    yaw, pitch, legs, antenna, roll, note = keys[index]
    pose_scuttle(armature, yaw, pitch, legs, antenna, roll)
    return {"frame": index, "type": "smear" if index in {0, 1} else "solid", "note": note}


def fidget_idle_pose(armature: bpy.types.Object, index: int) -> dict:
    phase = index / 12 * math.tau
    twitch = math.sin(phase * 2.0)
    leg_tick = math.sin(phase * 3.0 + 0.8)
    yaw = 4.0 * twitch
    pitch = 2.0 * math.sin(phase + 1.2)
    legs = (12 * leg_tick, -10 * leg_tick, -8 * leg_tick, 7 * leg_tick)
    antenna = 12 * math.sin(phase * 2.0 + 0.4)
    pose_scuttle(armature, yaw, pitch, legs, antenna, roll=2.0 * twitch)
    return {"frame": index, "type": "solid", "note": "fidget/talk idle", "twitch": round(twitch, 3)}


def make_parcel() -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=0.22, location=(0, 0, 0))
    parcel = bpy.context.object
    parcel.name = "temp_intake_parcel"
    parcel.scale = (1.15, 0.52, 0.72)
    mat = bpy.data.materials.new("parcel_cardboard")
    mat.diffuse_color = (0.66, 0.45, 0.25, 1)
    parcel.data.materials.append(mat)
    return parcel


def parcel_fumble_pose(armature: bpy.types.Object, parcel: bpy.types.Object, index: int) -> dict:
    keys = [
        (0, 0, (6, -6, 4, -4), 4, 0, (-0.36, -0.18, 0.72), 0, "holding parcel"),
        (-5, -3, (18, -16, 12, -10), -5, -2, (-0.30, -0.18, 0.78), 8, "notices wobble"),
        (12, 10, (-30, 28, -22, 18), 18, 7, (-0.16, -0.18, 0.72), 28, "fumble up"),
        (-14, -9, (34, -30, 24, -22), -18, -8, (0.03, -0.18, 0.58), 70, "losing grip"),
        (18, 12, (-42, 38, -28, 24), 24, 9, (0.19, -0.18, 0.42), 118, "parcel drops"),
        (10, 6, (-28, 24, -20, 16), 18, 5, (0.32, -0.18, 0.24), 160, "bounce one"),
        (-4, -2, (16, -14, 12, -10), -6, -2, (0.40, -0.18, 0.14), 193, "bounce settle"),
        (0, 0, (0, 0, 0, 0), 5, 0, (0.44, -0.18, 0.10), 205, "parcel on floor"),
        (0, 0, (0, 0, 0, 0), 5, 0, (0.44, -0.18, 0.10), 205, "parcel hold"),
    ]
    yaw, pitch, legs, antenna, roll, parcel_loc, parcel_rot, note = keys[index]
    pose_scuttle(armature, yaw, pitch, legs, antenna, roll)
    parcel.location = parcel_loc
    parcel.rotation_euler = Euler((math.radians(parcel_rot), math.radians(parcel_rot * 0.35), math.radians(parcel_rot * 0.2)), "XYZ")
    return {"frame": index, "type": "solid", "note": note, "parcel": list(parcel_loc)}


CLIPS = {
    "brake_stop": (8, brake_stop_pose),
    "fidget_idle": (12, fidget_idle_pose),
    "parcel_fumble_drop": (9, parcel_fumble_pose),
}


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
    parcel = make_parcel()
    parcel.hide_render = args.clip != "parcel_fumble_drop"
    parcel.hide_viewport = args.clip != "parcel_fumble_drop"

    count, pose_fn = CLIPS[args.clip]
    metadata = {
        "character": "scuttle",
        "clip": args.clip,
        "input": str(Path(args.input).resolve()),
        "view": args.view,
        "fps": 12 if args.clip != "brake_stop" else 16,
        "source_policy": "Rig-driven Meshy GLB; no static body transform standing in for leg motion.",
        "prop_policy": "parcel_fumble_drop uses a temporary rig-space parcel prop for timing proof only.",
        "frames": [],
    }
    scene = bpy.context.scene
    for i in range(count):
        scene.frame_set(i)
        if args.clip == "parcel_fumble_drop":
            meta = pose_fn(armature, parcel, i)
        else:
            meta = pose_fn(armature, i)
        scene.render.filepath = str(raw / f"scuttle_{args.clip}_raw_{i:03d}.png")
        bpy.ops.render.render(write_still=True)
        metadata["frames"].append(meta)
    (out / f"scuttle_{args.clip}_blender_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps({"clip": args.clip, "frames": count, "out": str(out)}, indent=2))


if __name__ == "__main__":
    main()
