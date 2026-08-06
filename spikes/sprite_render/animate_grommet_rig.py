#!/usr/bin/env python3
"""Render Grommet-specific proof clips from the Meshy biped FBX.

These are intake/proof renders, not final animation admission. The source export
only includes a generic walk, so this script clears that action and authors
small furniture-anchored poses directly on the skeleton.
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
            "pre_idle",
            "post_shiver",
            "mended_reaction",
            "guardian_brace",
            "strain_hold",
            "post_danger_relief",
            "annex_decision",
            "first_walk",
        ),
        required=True,
    )
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--frames", type=int, default=36)
    parser.add_argument("--resolution", type=int, default=768)
    parser.add_argument("--view", choices=("front", "side-left", "side-right"), default="front")
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

    bpy.ops.object.light_add(type="AREA", location=(-3.2, -4.0, 5.6))
    light = bpy.context.object
    light.name = "warm_upper_left_key"
    light.data.energy = 430
    light.data.size = 4.5

    bpy.ops.object.camera_add(location=(0, -5.0, 1.22), rotation=(math.radians(78), 0, 0))
    cam = bpy.context.object
    scene.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 2.35


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def set_view(view: str) -> None:
    cam = bpy.context.scene.camera
    positions = {
        "front": Vector((0, -5.0, 1.22)),
        "side-left": Vector((4.8, -0.9, 1.22)),
        "side-right": Vector((-4.8, -0.9, 1.22)),
    }
    cam.location = positions[view]
    look_at(cam, Vector((0, 0, 0.82)))


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


def reset_pose(
    armature: bpy.types.Object,
    base_pose: dict[str, tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]],
) -> None:
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="POSE")
    for bone in armature.pose.bones:
        bone.rotation_mode = "XYZ"
        rotation, location, scale = base_pose.get(
            bone.name,
            ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)),
        )
        bone.rotation_euler = Euler(rotation, "XYZ")
        bone.location = Vector(location)
        bone.scale = Vector(scale)
    bpy.ops.object.mode_set(mode="OBJECT")


def rot(armature: bpy.types.Object, name: str, xyz: tuple[float, float, float]) -> None:
    bone = armature.pose.bones.get(name)
    if not bone:
        return
    bone.rotation_mode = "XYZ"
    bone.rotation_euler = Euler(xyz, "XYZ")


def clear_animation() -> None:
    for obj in bpy.context.scene.objects:
        obj.animation_data_clear()
    for action in list(bpy.data.actions):
        bpy.data.actions.remove(action)


def add_rot(armature: bpy.types.Object, name: str, xyz: tuple[float, float, float]) -> None:
    bone = armature.pose.bones.get(name)
    if not bone:
        return
    bone.rotation_mode = "XYZ"
    bone.rotation_euler.rotate(Euler(xyz, "XYZ"))


def apply_pre_idle(
    armature: bpy.types.Object,
    base_pose: dict[str, tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]],
    frame: int,
    total: int,
) -> dict[str, float]:
    # Shy/still idle: held posture, eye-level life from head and hands only.
    phase = (frame / total) * math.tau
    breath = math.sin(phase) * math.radians(0.85)
    tiny_look = math.sin(phase * 0.5 - 0.6) * math.radians(1.6)
    hand_l = math.sin(phase + 0.25) * math.radians(1.4)
    hand_r = math.sin(phase + math.pi + 0.25) * math.radians(1.2)

    reset_pose(armature, base_pose)
    add_rot(armature, "Spine02", (breath * 0.25, 0, 0))
    add_rot(armature, "Spine01", (breath * 0.18, 0, 0))
    add_rot(armature, "Spine", (breath * 0.12, 0, 0))
    add_rot(armature, "neck", (math.radians(-1.2), 0, tiny_look * 0.25))
    add_rot(armature, "Head", (math.radians(-1.7), 0, tiny_look))
    add_rot(armature, "LeftArm", (math.radians(1.0), 0, hand_l * 0.4))
    add_rot(armature, "LeftForeArm", (0, 0, hand_l * 0.55))
    add_rot(armature, "LeftHand", (0, 0, hand_l * 0.75))
    add_rot(armature, "RightArm", (math.radians(0.8), 0, -hand_r * 0.4))
    add_rot(armature, "RightForeArm", (0, 0, -hand_r * 0.55))
    add_rot(armature, "RightHand", (0, 0, -hand_r * 0.75))
    return {
        "breath_deg": round(math.degrees(breath), 3),
        "head_look_deg": round(math.degrees(tiny_look), 3),
    }


def apply_post_shiver(
    armature: bpy.types.Object,
    base_pose: dict[str, tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]],
    frame: int,
    total: int,
) -> dict[str, float]:
    # Starts from shy idle, adds two brief shoulder tells across a long held loop.
    values = apply_pre_idle(armature, base_pose, frame, total)
    phase = frame / total
    pulse_a = math.exp(-((phase - 0.32) / 0.055) ** 2)
    pulse_b = math.exp(-((phase - 0.72) / 0.05) ** 2)
    shiver = (pulse_a - pulse_b * 0.65) * math.radians(4.2)
    counter = (pulse_a + pulse_b) * math.radians(1.2)

    add_rot(armature, "Spine", (counter * 0.15, shiver * 0.08, -shiver * 0.08))
    add_rot(armature, "LeftShoulder", (0, shiver * 0.35, shiver * 0.8))
    add_rot(armature, "LeftArm", (0, shiver * 0.22, shiver * 0.7))
    add_rot(armature, "LeftForeArm", (0, shiver * 0.12, shiver * 0.55))
    add_rot(armature, "Head", (counter * 0.22, 0, -shiver * 0.18))
    values["shoulder_shiver_deg"] = round(math.degrees(shiver), 3)
    return values


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def hold_peak(center: float, half_width: float, value: float) -> float:
    distance = abs(value - center)
    if distance >= half_width:
        return 0.0
    t = distance / half_width
    return 1.0 - (t * t * (3.0 - 2.0 * t))


def apply_mended_reaction(
    armature: bpy.types.Object,
    base_pose: dict[str, tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]],
    frame: int,
    total: int,
) -> dict[str, float]:
    # Act 2 climax: stillness first, then a small vulnerable realization.
    # Timeline: neutral hold -> notice -> held silence -> soft relief -> settle.
    t = frame / max(1, total - 1)
    reset_pose(armature, base_pose)

    notice = smoothstep(0.12, 0.32, t)
    silent_hold = hold_peak(0.48, 0.18, t)
    relief = smoothstep(0.58, 0.82, t)
    settle = smoothstep(0.84, 1.0, t)

    head_down = math.radians(-2.0 - 4.0 * notice + 1.7 * relief)
    head_tilt = math.radians(-1.4 * notice + 2.2 * relief - 1.0 * settle)
    chest_soften = math.radians(-1.2 * notice - 1.8 * relief + 1.1 * settle)
    shoulder_release = math.radians(4.4 * relief - 2.0 * settle)
    tiny_breath = math.sin(t * math.pi * 5.0) * math.radians(0.25) * (0.3 + relief)

    # Freeze the held-silence span a little by subtracting secondary motion at peak.
    hold_dampen = 1.0 - silent_hold * 0.72

    add_rot(armature, "Spine02", ((chest_soften + tiny_breath) * 0.25 * hold_dampen, 0, 0))
    add_rot(armature, "Spine01", ((chest_soften + tiny_breath) * 0.36 * hold_dampen, 0, 0))
    add_rot(armature, "Spine", ((chest_soften + tiny_breath) * 0.44 * hold_dampen, 0, 0))
    add_rot(armature, "neck", (head_down * 0.35, 0, head_tilt * 0.28))
    add_rot(armature, "Head", (head_down, 0, head_tilt))

    # Hands come in slightly toward the repaired seam, then soften outward.
    left_hand_in = math.radians(-8.5 * notice + 4.0 * relief)
    right_hand_in = math.radians(6.5 * notice - 2.5 * relief)
    add_rot(armature, "LeftShoulder", (0, 0, left_hand_in * 0.25))
    add_rot(armature, "LeftArm", (math.radians(-3.0 * notice), 0, left_hand_in * 0.55))
    add_rot(armature, "LeftForeArm", (0, math.radians(1.8 * notice), left_hand_in * 0.75))
    add_rot(armature, "LeftHand", (0, 0, left_hand_in * 0.85))
    add_rot(armature, "RightShoulder", (0, 0, right_hand_in * 0.22))
    add_rot(armature, "RightArm", (math.radians(-2.0 * notice), 0, right_hand_in * 0.45))
    add_rot(armature, "RightForeArm", (0, math.radians(-1.4 * notice), right_hand_in * 0.68))
    add_rot(armature, "RightHand", (0, 0, right_hand_in * 0.82))

    # Shoulder release is the emotional payoff: tiny but visible.
    add_rot(armature, "LeftShoulder", (0, shoulder_release * 0.25, shoulder_release * 0.65))
    add_rot(armature, "RightShoulder", (0, -shoulder_release * 0.18, -shoulder_release * 0.45))

    return {
        "notice": round(notice, 3),
        "silent_hold": round(silent_hold, 3),
        "relief": round(relief, 3),
        "settle": round(settle, 3),
        "head_down_deg": round(math.degrees(head_down), 3),
        "shoulder_release_deg": round(math.degrees(shoulder_release), 3),
    }


def apply_guardian_brace(
    armature: bpy.types.Object,
    base_pose: dict[str, tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]],
    frame: int,
    total: int,
) -> dict[str, float]:
    # Act 3: Grommet chooses to block the danger. This is a held, weighty
    # anticipation-to-brace beat, not a bouncy mascot move.
    t = frame / max(1, total - 1)
    reset_pose(armature, base_pose)

    notice = smoothstep(0.04, 0.20, t)
    gather = hold_peak(0.28, 0.16, t)
    plant = smoothstep(0.26, 0.54, t)
    impact = hold_peak(0.62, 0.07, t)
    settle = smoothstep(0.66, 0.92, t)

    brace = min(1.0, plant + settle * 0.25)
    head_down = math.radians(-2.2 - 4.8 * notice - 2.8 * brace + 1.0 * settle)
    chest_forward = math.radians(-1.0 * notice - 6.2 * plant - 1.6 * impact + 1.4 * settle)
    shoulder_wide = math.radians(22.0 * plant + 5.5 * impact - 3.0 * settle)
    hand_press = math.radians(23.0 * plant + 5.5 * impact - 4.0 * settle)
    elbow_lock = math.radians(-7.0 * gather + 12.0 * plant + 4.0 * impact)
    foot_plant = math.radians(3.0 * plant + 1.0 * impact)

    add_rot(armature, "Spine", (chest_forward * 0.52, 0, 0))
    add_rot(armature, "Spine01", (chest_forward * 0.36, 0, 0))
    add_rot(armature, "Spine02", (chest_forward * 0.24, 0, 0))
    add_rot(armature, "neck", (head_down * 0.3, 0, 0))
    add_rot(armature, "Head", (head_down, 0, math.radians(-0.6 * notice)))

    add_rot(armature, "LeftShoulder", (0, shoulder_wide * 0.35, -shoulder_wide * 0.68))
    add_rot(armature, "LeftArm", (math.radians(-4.0 * plant), shoulder_wide * 0.15, -shoulder_wide * 0.92))
    add_rot(armature, "LeftForeArm", (0, elbow_lock * 0.18, -hand_press * 0.36))
    add_rot(armature, "LeftHand", (0, math.radians(-2.0 * plant), -hand_press * 0.34))

    add_rot(armature, "RightShoulder", (0, -shoulder_wide * 0.32, shoulder_wide * 0.62))
    add_rot(armature, "RightArm", (math.radians(-3.0 * plant), -shoulder_wide * 0.13, shoulder_wide * 0.82))
    add_rot(armature, "RightForeArm", (0, -elbow_lock * 0.14, hand_press * 0.32))
    add_rot(armature, "RightHand", (0, math.radians(1.6 * plant), hand_press * 0.3))

    add_rot(armature, "LeftUpLeg", (foot_plant * 0.25, 0, foot_plant * 0.12))
    add_rot(armature, "RightUpLeg", (foot_plant * 0.18, 0, -foot_plant * 0.1))

    return {
        "notice": round(notice, 3),
        "gather": round(gather, 3),
        "plant": round(plant, 3),
        "impact": round(impact, 3),
        "settle": round(settle, 3),
        "brace_deg": round(math.degrees(chest_forward), 3),
        "hand_press_deg": round(math.degrees(hand_press), 3),
    }


def apply_strain_hold(
    armature: bpy.types.Object,
    base_pose: dict[str, tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]],
    frame: int,
    total: int,
) -> dict[str, float]:
    # Loopable held strain. The body stays planted; motion is pressure, breath,
    # and tiny tremor through shoulders/hands.
    t = frame / max(1, total)
    phase = t * math.tau
    reset_pose(armature, base_pose)

    pressure = 0.74 + 0.16 * math.sin(phase - 0.6)
    tremor = math.sin(phase * 5.0) * math.radians(0.7) + math.sin(phase * 8.0 + 0.4) * math.radians(0.35)
    breath = math.sin(phase) * math.radians(0.9)
    fatigue = math.sin(phase * 0.5 - 0.2) * math.radians(0.8)

    chest_forward = math.radians(-6.0) - breath * 0.4
    head_down = math.radians(-8.0) + fatigue * 0.45
    shoulder_wide = math.radians(21.5 + pressure * 4.0)
    hand_press = math.radians(23.0 + pressure * 3.5) + tremor

    add_rot(armature, "Spine", (chest_forward * 0.55, tremor * 0.05, tremor * 0.12))
    add_rot(armature, "Spine01", ((chest_forward + breath) * 0.35, tremor * 0.04, tremor * 0.08))
    add_rot(armature, "Spine02", ((chest_forward + breath) * 0.22, 0, tremor * 0.05))
    add_rot(armature, "neck", (head_down * 0.3, 0, fatigue * 0.2))
    add_rot(armature, "Head", (head_down, 0, fatigue))

    add_rot(armature, "LeftShoulder", (0, shoulder_wide * 0.36, -shoulder_wide * 0.7 + tremor))
    add_rot(armature, "LeftArm", (math.radians(-4.0), shoulder_wide * 0.16, -shoulder_wide * 0.92 + tremor * 0.8))
    add_rot(armature, "LeftForeArm", (0, math.radians(2.6), -hand_press * 0.36))
    add_rot(armature, "LeftHand", (0, math.radians(-2.2), -hand_press * 0.34))

    add_rot(armature, "RightShoulder", (0, -shoulder_wide * 0.32, shoulder_wide * 0.62 - tremor))
    add_rot(armature, "RightArm", (math.radians(-3.2), -shoulder_wide * 0.13, shoulder_wide * 0.82 - tremor * 0.7))
    add_rot(armature, "RightForeArm", (0, math.radians(-2.0), hand_press * 0.32))
    add_rot(armature, "RightHand", (0, math.radians(1.7), hand_press * 0.3))

    add_rot(armature, "LeftUpLeg", (math.radians(0.8), 0, math.radians(0.4)))
    add_rot(armature, "RightUpLeg", (math.radians(0.6), 0, math.radians(-0.35)))

    return {
        "pressure": round(pressure, 3),
        "tremor_deg": round(math.degrees(tremor), 3),
        "breath_deg": round(math.degrees(breath), 3),
        "head_down_deg": round(math.degrees(head_down), 3),
        "hand_press_deg": round(math.degrees(hand_press), 3),
    }


def apply_post_danger_relief(
    armature: bpy.types.Object,
    base_pose: dict[str, tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]],
    frame: int,
    total: int,
) -> dict[str, float]:
    # Act 3 aftermath: he is a little windswept, then realizes he held.
    # The performance moves from strain residue to a quiet proud softening.
    t = frame / max(1, total - 1)
    reset_pose(armature, base_pose)

    exhausted_hold = 1.0 - smoothstep(0.12, 0.34, t)
    breath_back = smoothstep(0.20, 0.54, t)
    proud_notice = smoothstep(0.46, 0.72, t)
    settle = smoothstep(0.78, 1.0, t)
    tiny_laugh = hold_peak(0.70, 0.12, t)

    after_tremor = math.sin(t * math.pi * 13.0) * math.radians(0.45) * exhausted_hold
    exhale = math.sin(t * math.pi) * math.radians(1.2) * breath_back

    head_down = math.radians(-7.0 * exhausted_hold - 1.5 * breath_back + 3.0 * proud_notice - 1.0 * settle)
    head_tilt = math.radians(-1.0 * exhausted_hold + 2.8 * proud_notice - 1.0 * settle)
    chest = math.radians(-5.2 * exhausted_hold - 1.5 * exhale + 2.6 * proud_notice - 1.4 * settle)
    shoulder_drop = math.radians(-7.0 * breath_back - 2.5 * exhale + 3.2 * proud_notice)
    arm_return = math.radians(16.0 * exhausted_hold - 6.0 * breath_back - 3.0 * settle)

    add_rot(armature, "Spine", (chest * 0.55, after_tremor * 0.05, after_tremor * 0.1))
    add_rot(armature, "Spine01", (chest * 0.35, 0, after_tremor * 0.08))
    add_rot(armature, "Spine02", (chest * 0.22, 0, after_tremor * 0.05))
    add_rot(armature, "neck", (head_down * 0.28, 0, head_tilt * 0.25))
    add_rot(armature, "Head", (head_down, 0, head_tilt + after_tremor))

    # Start with a little residual brace, then let arms soften down and inward.
    add_rot(armature, "LeftShoulder", (0, arm_return * 0.18, -arm_return * 0.42 + shoulder_drop * 0.22))
    add_rot(armature, "LeftArm", (math.radians(-2.0 * exhausted_hold), arm_return * 0.08, -arm_return * 0.58 + shoulder_drop * 0.18))
    add_rot(armature, "LeftForeArm", (0, math.radians(1.4 * exhausted_hold), -arm_return * 0.22 + shoulder_drop * 0.18))
    add_rot(armature, "LeftHand", (0, math.radians(-1.2 * exhausted_hold), -arm_return * 0.18 + shoulder_drop * 0.12))

    add_rot(armature, "RightShoulder", (0, -arm_return * 0.16, arm_return * 0.38 - shoulder_drop * 0.2))
    add_rot(armature, "RightArm", (math.radians(-1.8 * exhausted_hold), -arm_return * 0.07, arm_return * 0.5 - shoulder_drop * 0.16))
    add_rot(armature, "RightForeArm", (0, math.radians(-1.2 * exhausted_hold), arm_return * 0.2 - shoulder_drop * 0.16))
    add_rot(armature, "RightHand", (0, math.radians(1.0 * exhausted_hold), arm_return * 0.16 - shoulder_drop * 0.1))

    # Tiny bounce of pride without moving the whole body.
    add_rot(armature, "Head", (math.radians(-0.8 * tiny_laugh), 0, math.radians(0.6 * tiny_laugh)))
    add_rot(armature, "Spine02", (math.radians(0.5 * tiny_laugh), 0, 0))

    return {
        "exhausted_hold": round(exhausted_hold, 3),
        "breath_back": round(breath_back, 3),
        "proud_notice": round(proud_notice, 3),
        "tiny_laugh": round(tiny_laugh, 3),
        "head_down_deg": round(math.degrees(head_down), 3),
        "shoulder_drop_deg": round(math.degrees(shoulder_drop), 3),
    }


def apply_annex_decision(
    armature: bpy.types.Object,
    base_pose: dict[str, tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]],
    frame: int,
    total: int,
) -> dict[str, float]:
    # Act 3 Annex: the important beat is the decision before the door moves.
    # He stays sweet and shy; the visible action is a tiny courage-gather,
    # hand preparation, and resolved stillness.
    t = frame / max(1, total - 1)
    reset_pose(armature, base_pose)

    notice = smoothstep(0.08, 0.26, t)
    doubt_hold = hold_peak(0.34, 0.16, t)
    gather = smoothstep(0.34, 0.58, t)
    reach = smoothstep(0.54, 0.78, t)
    resolve = smoothstep(0.74, 1.0, t)

    breath = math.sin(t * math.pi * 2.0) * math.radians(0.65)
    tiny_tremor = math.sin(t * math.pi * 11.0) * math.radians(0.22) * (1.0 - resolve) * gather

    head_down = math.radians(-2.4 - 2.5 * notice - 1.4 * doubt_hold + 2.8 * resolve)
    head_turn = math.radians(-1.0 * notice + 4.2 * reach - 1.0 * resolve)
    chest = math.radians(-1.3 * notice - 2.0 * gather + 1.2 * resolve) + breath * 0.45
    shoulder_tuck = math.radians(4.5 * notice + 2.0 * doubt_hold - 2.5 * resolve)
    hand_prepare = math.radians(7.5 * gather + 7.0 * reach - 3.0 * resolve)

    add_rot(armature, "Spine", (chest * 0.48, 0, head_turn * 0.08))
    add_rot(armature, "Spine01", (chest * 0.34, 0, head_turn * 0.06))
    add_rot(armature, "Spine02", (chest * 0.22, 0, head_turn * 0.04))
    add_rot(armature, "neck", (head_down * 0.3, 0, head_turn * 0.28))
    add_rot(armature, "Head", (head_down + tiny_tremor, 0, head_turn))

    # One hand moves toward the unseen Annex mechanism; the other stays close
    # to the body so the beat reads careful, not heroic.
    add_rot(armature, "LeftShoulder", (0, shoulder_tuck * 0.2, shoulder_tuck * 0.48))
    add_rot(armature, "LeftArm", (math.radians(-1.5 * notice), 0, shoulder_tuck * 0.72))
    add_rot(armature, "LeftForeArm", (0, 0, hand_prepare * 0.55))
    add_rot(armature, "LeftHand", (0, math.radians(1.2 * reach), hand_prepare * 0.75))

    add_rot(armature, "RightShoulder", (0, -hand_prepare * 0.18, hand_prepare * 0.48))
    add_rot(armature, "RightArm", (math.radians(-2.0 * reach), -hand_prepare * 0.08, hand_prepare * 0.72))
    add_rot(armature, "RightForeArm", (0, math.radians(-1.6 * reach), hand_prepare * 0.55))
    add_rot(armature, "RightHand", (0, math.radians(1.4 * reach), hand_prepare * 0.72))

    return {
        "notice": round(notice, 3),
        "doubt_hold": round(doubt_hold, 3),
        "gather": round(gather, 3),
        "reach": round(reach, 3),
        "resolve": round(resolve, 3),
        "head_turn_deg": round(math.degrees(head_turn), 3),
        "hand_prepare_deg": round(math.degrees(hand_prepare), 3),
    }


FIRST_WALK_KEYS = [
    {
        "role": "left contact",
        "left_leg": -12.0,
        "left_knee": 5.0,
        "left_foot": 6.0,
        "right_leg": 14.0,
        "right_knee": -3.0,
        "right_foot": -5.0,
        "hip_y": -1.0,
        "hip_z": -1.5,
        "torso": -1.0,
        "head": -1.0,
        "left_arm": 7.0,
        "right_arm": -7.0,
    },
    {
        "role": "left recoil/down",
        "left_leg": -8.0,
        "left_knee": 13.0,
        "left_foot": 2.0,
        "right_leg": 10.0,
        "right_knee": 8.0,
        "right_foot": -6.0,
        "hip_y": -2.4,
        "hip_z": -3.5,
        "torso": -3.0,
        "head": -2.2,
        "left_arm": 4.5,
        "right_arm": -4.5,
    },
    {
        "role": "left passing",
        "left_leg": -2.0,
        "left_knee": 8.0,
        "left_foot": 0.0,
        "right_leg": 1.0,
        "right_knee": 18.0,
        "right_foot": 4.0,
        "hip_y": 0.0,
        "hip_z": -0.8,
        "torso": -1.5,
        "head": -0.8,
        "left_arm": 1.5,
        "right_arm": -1.5,
    },
    {
        "role": "left high point",
        "left_leg": 7.0,
        "left_knee": 3.0,
        "left_foot": -3.0,
        "right_leg": -8.0,
        "right_knee": 21.0,
        "right_foot": 8.0,
        "hip_y": 1.8,
        "hip_z": 1.0,
        "torso": 0.2,
        "head": 1.0,
        "left_arm": -3.0,
        "right_arm": 3.0,
    },
    {
        "role": "right contact",
        "left_leg": 14.0,
        "left_knee": -3.0,
        "left_foot": -5.0,
        "right_leg": -12.0,
        "right_knee": 5.0,
        "right_foot": 6.0,
        "hip_y": 1.0,
        "hip_z": -1.5,
        "torso": -1.0,
        "head": -1.0,
        "left_arm": -7.0,
        "right_arm": 7.0,
    },
    {
        "role": "right recoil/down",
        "left_leg": 10.0,
        "left_knee": 8.0,
        "left_foot": -6.0,
        "right_leg": -8.0,
        "right_knee": 13.0,
        "right_foot": 2.0,
        "hip_y": 2.4,
        "hip_z": -3.5,
        "torso": -3.0,
        "head": -2.2,
        "left_arm": -4.5,
        "right_arm": 4.5,
    },
    {
        "role": "right passing",
        "left_leg": 1.0,
        "left_knee": 18.0,
        "left_foot": 4.0,
        "right_leg": -2.0,
        "right_knee": 8.0,
        "right_foot": 0.0,
        "hip_y": 0.0,
        "hip_z": -0.8,
        "torso": -1.5,
        "head": -0.8,
        "left_arm": -1.5,
        "right_arm": 1.5,
    },
    {
        "role": "right high point",
        "left_leg": -8.0,
        "left_knee": 21.0,
        "left_foot": 8.0,
        "right_leg": 7.0,
        "right_knee": 3.0,
        "right_foot": -3.0,
        "hip_y": -1.8,
        "hip_z": 1.0,
        "torso": 0.2,
        "head": 1.0,
        "left_arm": 3.0,
        "right_arm": -3.0,
    },
    {
        "role": "loop-safe return",
        "left_leg": -12.0,
        "left_knee": 5.0,
        "left_foot": 6.0,
        "right_leg": 14.0,
        "right_knee": -3.0,
        "right_foot": -5.0,
        "hip_y": -1.0,
        "hip_z": -1.5,
        "torso": -1.0,
        "head": -1.0,
        "left_arm": 7.0,
        "right_arm": -7.0,
    },
]


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def interpolate_key_pose(frame: int, total: int) -> tuple[dict[str, float | str], float]:
    if total <= 1:
        return FIRST_WALK_KEYS[0], 0.0
    position = (frame / (total - 1)) * (len(FIRST_WALK_KEYS) - 1)
    left_index = min(len(FIRST_WALK_KEYS) - 2, int(math.floor(position)))
    right_index = left_index + 1
    local = position - left_index
    eased = smoothstep(0.0, 1.0, local)
    left = FIRST_WALK_KEYS[left_index]
    right = FIRST_WALK_KEYS[right_index]
    pose: dict[str, float | str] = {"role": left["role"] if local < 0.5 else right["role"]}
    for key, value in left.items():
        if key == "role":
            continue
        pose[key] = lerp(float(value), float(right[key]), eased)
    return pose, position


def apply_first_walk(
    armature: bpy.types.Object,
    base_pose: dict[str, tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]],
    frame: int,
    total: int,
) -> dict[str, float | str]:
    # Grommet's first-ever walk: slow, deliberate, slightly unsure. The cycle
    # follows the 9-role walk contract but keeps the motion soft and heavy.
    pose, position = interpolate_key_pose(frame, total)
    reset_pose(armature, base_pose)

    hip_y = math.radians(float(pose["hip_y"]))
    hip_z = math.radians(float(pose["hip_z"]))
    torso = math.radians(float(pose["torso"]))
    head = math.radians(float(pose["head"]))
    left_leg = math.radians(float(pose["left_leg"]))
    right_leg = math.radians(float(pose["right_leg"]))
    left_knee = math.radians(float(pose["left_knee"]))
    right_knee = math.radians(float(pose["right_knee"]))
    left_foot = math.radians(float(pose["left_foot"]))
    right_foot = math.radians(float(pose["right_foot"]))
    left_arm = math.radians(float(pose["left_arm"]))
    right_arm = math.radians(float(pose["right_arm"]))

    cautious = math.sin((frame / max(1, total - 1)) * math.pi)
    cloth_lag = math.sin((frame / max(1, total - 1)) * math.tau * 2.0 + 0.6) * math.radians(0.8)

    add_rot(armature, "Hips", (0, hip_y * 0.14, hip_z * 0.18))
    add_rot(armature, "Spine", (torso * 0.42, hip_y * 0.08, hip_z * 0.12 + cloth_lag * 0.2))
    add_rot(armature, "Spine01", (torso * 0.28, hip_y * 0.05, hip_z * 0.08 + cloth_lag * 0.15))
    add_rot(armature, "Spine02", (torso * 0.18, 0, cloth_lag * 0.1))
    add_rot(armature, "neck", (head * 0.35, 0, -hip_z * 0.08))
    add_rot(armature, "Head", (head, 0, -hip_z * 0.12))

    # For this Meshy rig, X rotation gives the readable side-view leg swing.
    add_rot(armature, "LeftUpLeg", (left_leg * 0.72, 0, hip_z * 0.05))
    add_rot(armature, "LeftLeg", (left_knee * 0.72, 0, 0))
    add_rot(armature, "LeftFoot", (left_foot * 0.75, 0, 0))
    add_rot(armature, "RightUpLeg", (right_leg * 0.72, 0, -hip_z * 0.05))
    add_rot(armature, "RightLeg", (right_knee * 0.72, 0, 0))
    add_rot(armature, "RightFoot", (right_foot * 0.75, 0, 0))

    # Counter-swing stays small: he is moving for the first time, not striding.
    add_rot(armature, "LeftShoulder", (0, 0, -left_arm * 0.2))
    add_rot(armature, "LeftArm", (left_arm * 0.2, 0, -left_arm * 0.55))
    add_rot(armature, "LeftForeArm", (0, 0, -left_arm * 0.2))
    add_rot(armature, "RightShoulder", (0, 0, right_arm * 0.18))
    add_rot(armature, "RightArm", (right_arm * 0.18, 0, right_arm * 0.5))
    add_rot(armature, "RightForeArm", (0, 0, right_arm * 0.18))

    add_rot(armature, "Head", (math.radians(-0.9 * cautious), 0, 0))

    nearest_key = min(range(len(FIRST_WALK_KEYS)), key=lambda index: abs(position - index))
    return {
        "role": str(pose["role"]),
        "nearest_key_role": FIRST_WALK_KEYS[nearest_key]["role"],
        "key_position": round(position, 3),
        "left_leg_deg": round(math.degrees(left_leg), 3),
        "right_leg_deg": round(math.degrees(right_leg), 3),
        "hip_z_deg": round(math.degrees(hip_z), 3),
        "cautious": round(cautious, 3),
    }


CLIPS = {
    "pre_idle": apply_pre_idle,
    "post_shiver": apply_post_shiver,
    "mended_reaction": apply_mended_reaction,
    "guardian_brace": apply_guardian_brace,
    "strain_hold": apply_strain_hold,
    "post_danger_relief": apply_post_danger_relief,
    "annex_decision": apply_annex_decision,
    "first_walk": apply_first_walk,
}


def main() -> None:
    args = parse_args()
    out = Path(args.out)
    raw = out / "frames_raw"
    raw.mkdir(parents=True, exist_ok=True)

    clear_scene()
    import_model(Path(args.input))
    center_and_floor()
    setup_render(args.resolution)
    set_view(args.view)

    armature_list = armatures()
    if not armature_list:
        raise SystemExit("no armature found")
    armature = armature_list[0]
    scene = bpy.context.scene
    scene.frame_set(0)
    bpy.context.view_layer.update()
    base_pose = capture_pose(armature)
    clear_animation()

    metadata = {
        "input": str(Path(args.input).resolve()),
        "clip": args.clip,
        "fps": args.fps,
        "frames": args.frames,
        "view": args.view,
        "armature": armature.name,
        "notes": [
            "Grommet-specific proof only; no final animation admission.",
            "Source FBX walk action cleared before authored poses are applied.",
            "Motion is limited to head, hands, shoulders, and tiny cloth-breath.",
            "No costume, face, or color overlays are drawn.",
        ],
        "frame_pose_values": [],
    }

    pose_fn = CLIPS[args.clip]
    for frame in range(args.frames):
        scene.frame_set(frame)
        values = pose_fn(armature, base_pose, frame, args.frames)
        metadata["frame_pose_values"].append({"frame": frame, **values})
        scene.render.filepath = str(raw / f"grommet_{args.clip}_raw_{frame:03d}.png")
        bpy.ops.render.render(write_still=True)

    (out / f"grommet_{args.clip}_blender_manifest.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"clip": args.clip, "frames": args.frames, "out": str(out)}, indent=2))


if __name__ == "__main__":
    main()
