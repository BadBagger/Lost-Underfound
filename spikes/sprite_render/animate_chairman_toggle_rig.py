#!/usr/bin/env python3
"""Render Chairman Toggle proof clips from the Meshy biped FBX.

These are animation-intake proofs for Act 2/3. They use the supplied skeleton
and texture-bound model. No scene desk, UI, or drawn replacement features.
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
    parser.add_argument(
        "--clip",
        choices=(
            "idle",
            "stamp_down",
            "confrontation_entrance",
            "deflect_parcel",
            "deflect_ledger",
            "deflect_concede",
            "panic_exit",
        ),
        required=True,
    )
    parser.add_argument("--frames", type=int, default=36)
    parser.add_argument("--resolution", type=int, default=768)
    return parser.parse_args(argv)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_model(path: Path) -> None:
    bpy.ops.import_scene.fbx(filepath=str(path.resolve()))


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
    render_meshes = meshes()
    mins, maxs = world_bbox(render_meshes)
    center = (mins + maxs) * 0.5
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.location -= center
    mins, _ = world_bbox(render_meshes)
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.location.z -= mins.z


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

    bpy.ops.object.light_add(type="AREA", location=(-3.3, -4.0, 5.6))
    light = bpy.context.object
    light.name = "warm_upper_left_key"
    light.data.energy = 410
    light.data.size = 4.4

    bpy.ops.object.camera_add(location=(0, -4.8, 1.18), rotation=(math.radians(78), 0, 0))
    cam = bpy.context.object
    scene.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 2.28


def capture_pose(armature: bpy.types.Object) -> dict[str, tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="POSE")
    data = {}
    for bone in armature.pose.bones:
        bone.rotation_mode = "XYZ"
        data[bone.name] = (
            tuple(float(v) for v in bone.rotation_euler),
            tuple(float(v) for v in bone.location),
            tuple(float(v) for v in bone.scale),
        )
    bpy.ops.object.mode_set(mode="OBJECT")
    return data


def reset_pose(armature: bpy.types.Object, base_pose: dict) -> None:
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="POSE")
    for bone in armature.pose.bones:
        bone.rotation_mode = "XYZ"
        rotation, location, scale = base_pose.get(bone.name, ((0, 0, 0), (0, 0, 0), (1, 1, 1)))
        bone.rotation_euler = Euler(rotation, "XYZ")
        bone.location = Vector(location)
        bone.scale = Vector(scale)
    bpy.ops.object.mode_set(mode="OBJECT")


def add_rot(armature: bpy.types.Object, name: str, xyz: tuple[float, float, float]) -> None:
    bone = armature.pose.bones.get(name)
    if not bone:
        return
    bone.rotation_mode = "XYZ"
    bone.rotation_euler.rotate(Euler(xyz, "XYZ"))


def clear_animation() -> None:
    for obj in bpy.context.scene.objects:
        obj.animation_data_clear()
    for action in list(bpy.data.actions):
        bpy.data.actions.remove(action)


def smoothstep(a: float, b: float, x: float) -> float:
    if a == b:
        return 1.0 if x >= b else 0.0
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def pulse(center: float, width: float, x: float) -> float:
    d = abs(x - center)
    if d >= width:
        return 0.0
    t = d / width
    return 1.0 - (t * t * (3 - 2 * t))


def apply_idle(arm: bpy.types.Object, base: dict, frame: int, total: int) -> dict[str, float]:
    t = frame / total
    phase = t * math.tau
    reset_pose(arm, base)
    brisk = math.sin(phase * 3.0)
    nod = math.sin(phase * 1.0 + 0.3)
    add_rot(arm, "Spine", (math.radians(0.4) * brisk, 0, math.radians(0.35) * brisk))
    add_rot(arm, "Head", (math.radians(1.6) * nod, 0, math.radians(0.8) * brisk))
    add_rot(arm, "LeftArm", (math.radians(-7), math.radians(5), math.radians(6 + brisk * 2.0)))
    add_rot(arm, "LeftForeArm", (math.radians(5), 0, math.radians(8 + brisk * 3.0)))
    add_rot(arm, "RightArm", (math.radians(-9), math.radians(-5), math.radians(-6 - brisk * 2.0)))
    add_rot(arm, "RightForeArm", (math.radians(4), 0, math.radians(-8 - brisk * 3.0)))
    return {"brisk_hand_tick": round(brisk, 3)}


def apply_stamp_down(arm: bpy.types.Object, base: dict, frame: int, total: int) -> dict[str, float]:
    t = frame / max(1, total - 1)
    reset_pose(arm, base)
    prep = smoothstep(0.06, 0.28, t) * (1 - smoothstep(0.30, 0.42, t))
    slam = smoothstep(0.32, 0.46, t) * (1 - smoothstep(0.58, 0.78, t))
    recoil = pulse(0.52, 0.20, t)
    settle = smoothstep(0.72, 0.98, t)
    force = max(prep * 0.7, slam)
    add_rot(arm, "Hips", (0, 0, math.radians(-1.8 * force + 1.2 * recoil)))
    add_rot(arm, "Spine", (math.radians(-8.0 * force + 3.5 * recoil) * (1 - settle * 0.7), 0, math.radians(-2.5 * force)))
    add_rot(arm, "Head", (math.radians(-9.0 * force + 5.0 * recoil), 0, math.radians(2.0 * prep)))
    add_rot(arm, "RightArm", (math.radians(-62 * prep + 54 * slam - 18 * recoil), math.radians(-16), math.radians(-26)))
    add_rot(arm, "RightForeArm", (math.radians(-36 * prep + 76 * slam - 28 * recoil), 0, math.radians(-18)))
    add_rot(arm, "RightHand", (math.radians(22 * prep - 34 * slam + 10 * recoil), 0, math.radians(-8 * slam)))
    add_rot(arm, "LeftArm", (math.radians(-18 + 8 * recoil), math.radians(10), math.radians(18)))
    add_rot(arm, "LeftForeArm", (math.radians(14 - 4 * settle), 0, math.radians(18)))
    return {"stamp_force": round(force, 3), "recoil": round(recoil, 3)}


def apply_confrontation_entrance(arm: bpy.types.Object, base: dict, frame: int, total: int) -> dict[str, float]:
    t = frame / max(1, total - 1)
    reset_pose(arm, base)

    interruption = smoothstep(0.04, 0.20, t)
    startle = pulse(0.22, 0.12, t)
    compose = smoothstep(0.26, 0.54, t)
    defensive_show = smoothstep(0.48, 0.78, t)
    hold = smoothstep(0.76, 1.0, t)

    brisk_tick = math.sin(t * math.tau * 3.0) * (1.0 - interruption)
    alarm_tremor = math.sin(t * math.tau * 9.0) * startle

    spine_snap = -6.5 * startle + 3.2 * compose - 1.2 * hold
    head_snap = -10.0 * startle + 4.0 * compose
    head_turn = 12.0 * interruption - 5.0 * hold
    shoulder_lift = 10.0 * startle + 4.0 * defensive_show - 2.0 * hold

    add_rot(arm, "Hips", (0, 0, math.radians(-1.5 * interruption + 2.0 * hold)))
    add_rot(arm, "Spine", (math.radians(spine_snap + 0.45 * brisk_tick), 0, math.radians(3.0 * interruption - 2.0 * hold)))
    add_rot(arm, "Head", (math.radians(head_snap), 0, math.radians(head_turn + 1.6 * alarm_tremor)))

    # Hands stop being busy clerk hands and become "wait, explain yourself" hands.
    add_rot(arm, "LeftShoulder", (math.radians(shoulder_lift * 0.35), 0, math.radians(6.0 * defensive_show)))
    add_rot(arm, "LeftArm", (math.radians(-7 - 18 * defensive_show + 5 * hold), math.radians(8), math.radians(12 + 28 * defensive_show)))
    add_rot(arm, "LeftForeArm", (math.radians(5 + 18 * defensive_show), 0, math.radians(8 + 16 * defensive_show)))
    add_rot(arm, "LeftHand", (math.radians(-8 * defensive_show), 0, math.radians(5 * defensive_show)))

    add_rot(arm, "RightShoulder", (math.radians(shoulder_lift * 0.35), 0, math.radians(-6.0 * defensive_show)))
    add_rot(arm, "RightArm", (math.radians(-9 - 20 * defensive_show + 6 * hold), math.radians(-8), math.radians(-12 - 30 * defensive_show)))
    add_rot(arm, "RightForeArm", (math.radians(4 + 18 * defensive_show), 0, math.radians(-8 - 16 * defensive_show)))
    add_rot(arm, "RightHand", (math.radians(-8 * defensive_show), 0, math.radians(-5 * defensive_show)))

    return {
        "interruption": round(interruption, 3),
        "startle": round(startle, 3),
        "compose": round(compose, 3),
        "defensive_show": round(defensive_show, 3),
        "hold": round(hold, 3),
    }


def apply_deflect_parcel(arm: bpy.types.Object, base: dict, frame: int, total: int) -> dict[str, float]:
    t = frame / max(1, total - 1)
    reset_pose(arm, base)

    see_it = smoothstep(0.06, 0.22, t)
    dismiss = pulse(0.38, 0.20, t)
    recoil = pulse(0.58, 0.16, t)
    settle = smoothstep(0.70, 1.0, t)

    add_rot(arm, "Hips", (0, 0, math.radians(-2.0 * dismiss + 1.0 * settle)))
    add_rot(arm, "Spine", (math.radians(2.5 * see_it - 3.0 * recoil), 0, math.radians(-6.0 * dismiss + 2.0 * settle)))
    add_rot(arm, "Head", (math.radians(-2.5 * see_it + 2.0 * recoil), 0, math.radians(-10.0 * dismiss + 3.0 * settle)))

    # Parcel denial: a flat palm sweep away from himself.
    add_rot(arm, "LeftArm", (math.radians(-10 + 6 * settle), math.radians(16), math.radians(44 * dismiss - 12 * settle)))
    add_rot(arm, "LeftForeArm", (math.radians(18 * dismiss), 0, math.radians(34 * dismiss)))
    add_rot(arm, "LeftHand", (math.radians(-12 * dismiss), 0, math.radians(18 * dismiss)))
    add_rot(arm, "RightArm", (math.radians(-8), math.radians(-5), math.radians(-8 - 4 * dismiss)))
    add_rot(arm, "RightForeArm", (math.radians(4), 0, math.radians(-6)))

    return {
        "see_it": round(see_it, 3),
        "dismiss": round(dismiss, 3),
        "recoil": round(recoil, 3),
        "settle": round(settle, 3),
    }


def apply_deflect_ledger(arm: bpy.types.Object, base: dict, frame: int, total: int) -> dict[str, float]:
    t = frame / max(1, total - 1)
    reset_pose(arm, base)

    recognize = smoothstep(0.06, 0.24, t)
    block_read = pulse(0.34, 0.18, t)
    fluster = pulse(0.56, 0.22, t)
    settle = smoothstep(0.72, 1.0, t)

    add_rot(arm, "Hips", (0, 0, math.radians(2.5 * recognize - 1.2 * settle)))
    add_rot(arm, "Spine", (math.radians(-2.0 * recognize + 2.2 * settle), 0, math.radians(7.0 * block_read - 3.0 * fluster)))
    add_rot(arm, "Head", (math.radians(-4.0 * recognize + 3.0 * settle), 0, math.radians(8.0 * block_read - 12.0 * fluster + 3.0 * settle)))

    # Ledger denial: both hands come inward like he is shielding a bad record.
    add_rot(arm, "LeftShoulder", (math.radians(4 * block_read), 0, math.radians(5 * block_read)))
    add_rot(arm, "LeftArm", (math.radians(-18 * block_read + 8 * settle), math.radians(10), math.radians(30 * block_read - 8 * settle)))
    add_rot(arm, "LeftForeArm", (math.radians(28 * block_read - 10 * settle), 0, math.radians(22 * block_read)))
    add_rot(arm, "LeftHand", (math.radians(-10 * block_read), 0, math.radians(10 * block_read)))

    add_rot(arm, "RightShoulder", (math.radians(4 * fluster), 0, math.radians(-5 * fluster)))
    add_rot(arm, "RightArm", (math.radians(-20 * fluster + 8 * settle), math.radians(-10), math.radians(-32 * fluster + 8 * settle)))
    add_rot(arm, "RightForeArm", (math.radians(30 * fluster - 10 * settle), 0, math.radians(-24 * fluster)))
    add_rot(arm, "RightHand", (math.radians(-12 * fluster), 0, math.radians(-10 * fluster)))

    return {
        "recognize": round(recognize, 3),
        "block_read": round(block_read, 3),
        "fluster": round(fluster, 3),
        "settle": round(settle, 3),
    }


def apply_deflect_concede(arm: bpy.types.Object, base: dict, frame: int, total: int) -> dict[str, float]:
    t = frame / max(1, total - 1)
    reset_pose(arm, base)
    deflect_a = pulse(0.18, 0.16, t)
    deflect_b = pulse(0.38, 0.16, t)
    deflect_c = pulse(0.56, 0.14, t)
    deflate = smoothstep(0.62, 0.90, t)
    denial = max(deflect_a, deflect_b, deflect_c)
    add_rot(arm, "Hips", (0, 0, math.radians(-2.5 * denial + 4.0 * deflate)))
    add_rot(arm, "Spine", (math.radians(4.5 * denial - 8.0 * deflate), 0, math.radians(-8.0 * deflect_b + 5.0 * deflate)))
    add_rot(arm, "Head", (math.radians(-4.0 * denial + 10.0 * deflate), 0, math.radians(-9.0 * deflect_a + 8.0 * deflect_b - 8.0 * deflate)))
    add_rot(arm, "LeftArm", (math.radians(-42 * deflect_a + 18 * deflate), math.radians(18), math.radians(58 * deflect_a - 18 * deflate)))
    add_rot(arm, "LeftForeArm", (math.radians(32 * deflect_a - 16 * deflate), 0, math.radians(42 * deflect_a)))
    add_rot(arm, "LeftHand", (math.radians(-16 * deflect_a), 0, math.radians(12 * deflect_a)))
    add_rot(arm, "RightArm", (math.radians(-38 * deflect_b + 22 * deflate), math.radians(-18), math.radians(-56 * deflect_b + 14 * deflate)))
    add_rot(arm, "RightForeArm", (math.radians(30 * deflect_b - 14 * deflate), 0, math.radians(-42 * deflect_b)))
    add_rot(arm, "RightHand", (math.radians(-14 * deflect_b), 0, math.radians(-12 * deflect_b)))
    add_rot(arm, "LeftShoulder", (math.radians(5 * deflect_c), 0, math.radians(8 * deflect_c)))
    add_rot(arm, "RightShoulder", (math.radians(5 * deflect_c), 0, math.radians(-8 * deflect_c)))
    return {"deflect_a": round(deflect_a, 3), "deflect_b": round(deflect_b, 3), "deflect_c": round(deflect_c, 3), "deflate": round(deflate, 3)}


def apply_panic_exit(arm: bpy.types.Object, base: dict, frame: int, total: int) -> dict[str, float]:
    t = frame / max(1, total - 1)
    reset_pose(arm, base)
    alarm = smoothstep(0.05, 0.22, t)
    scramble = math.sin(t * math.tau * 4.0) * alarm
    lean = smoothstep(0.30, 0.82, t)
    add_rot(arm, "Hips", (0, 0, math.radians(-6 * lean)))
    add_rot(arm, "Spine", (math.radians(-4 * alarm), 0, math.radians(-10 * lean + 2 * scramble)))
    add_rot(arm, "Head", (math.radians(-7 * alarm), 0, math.radians(9 * scramble)))
    add_rot(arm, "LeftArm", (math.radians(-36 * alarm), math.radians(5), math.radians(40 * alarm + 10 * scramble)))
    add_rot(arm, "LeftForeArm", (math.radians(22 * alarm), 0, math.radians(16 * scramble)))
    add_rot(arm, "RightArm", (math.radians(-36 * alarm), math.radians(-5), math.radians(-40 * alarm - 10 * scramble)))
    add_rot(arm, "RightForeArm", (math.radians(22 * alarm), 0, math.radians(-16 * scramble)))
    add_rot(arm, "LeftUpLeg", (math.radians(18 * lean), 0, math.radians(4 * scramble)))
    add_rot(arm, "RightUpLeg", (math.radians(-16 * lean), 0, math.radians(-4 * scramble)))
    return {"alarm": round(alarm, 3), "lean": round(lean, 3), "scramble": round(scramble, 3)}


CLIPS = {
    "idle": apply_idle,
    "stamp_down": apply_stamp_down,
    "confrontation_entrance": apply_confrontation_entrance,
    "deflect_parcel": apply_deflect_parcel,
    "deflect_ledger": apply_deflect_ledger,
    "deflect_concede": apply_deflect_concede,
    "panic_exit": apply_panic_exit,
}


def main() -> None:
    args = parse_args()
    clear_scene()
    import_model(Path(args.input))
    if not meshes() or not armatures():
        raise SystemExit("model must include mesh and armature")
    center_and_floor()
    clear_animation()
    setup_render(args.resolution)
    arm = armatures()[0]
    base = capture_pose(arm)

    out = Path(args.out)
    raw = out / "frames_raw"
    raw.mkdir(parents=True, exist_ok=True)
    metadata = []
    pose_fn = CLIPS[args.clip]
    for frame in range(args.frames):
        meta = pose_fn(arm, base, frame, args.frames)
        bpy.context.scene.frame_set(frame)
        bpy.context.scene.render.filepath = str(raw / f"chairman_{args.clip}_raw_{frame:03d}.png")
        bpy.ops.render.render(write_still=True)
        metadata.append({"frame": frame, **meta})
    manifest = {
        "character": "chairman_toggle",
        "clip": args.clip,
        "input": str(Path(args.input).resolve()),
        "frames": args.frames,
        "fps": 12,
        "source_policy": "Meshy texture-bound FBX rendered with authored skeleton poses; no drawn feature overlays.",
        "metadata": metadata,
    }
    (out / f"chairman_{args.clip}_blender_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"clip": args.clip, "frames": args.frames, "out": str(out)}, indent=2))


if __name__ == "__main__":
    main()
