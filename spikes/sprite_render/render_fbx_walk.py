#!/usr/bin/env python3
"""Headless Blender renderer for the sprite-render spike.

Run with Blender:
  blender --background --python spikes/sprite_render/render_fbx_walk.py -- --asset ... --out ...
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable

import bpy
import bpy_extras.object_utils
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    import sys

    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset")
    parser.add_argument("--fbx")
    parser.add_argument("--out", required=True)
    parser.add_argument("--fps", type=float, default=12.0)
    parser.add_argument("--frame-count", type=int)
    parser.add_argument("--still-frame", type=float)
    parser.add_argument("--angle-deg", type=float, default=8.0)
    parser.add_argument("--resolution", type=int, default=512)
    parser.add_argument("--resolution-x", type=int)
    parser.add_argument("--resolution-y", type=int)
    parser.add_argument("--target-height", type=int, default=430)
    parser.add_argument("--ortho-height-mult", type=float, default=2.15)
    parser.add_argument("--ortho-scale", type=float)
    parser.add_argument("--camera-target-z-frac", type=float, default=0.5)
    parser.add_argument("--camera-shift-x", type=float, default=0.0)
    parser.add_argument("--camera-shift-y", type=float, default=0.0)
    parser.add_argument("--light-yaw-deg", type=float, default=-35.0)
    parser.add_argument("--view", choices=("front", "side-left", "side-right"), default="side-left")
    parser.add_argument("--material-mode", choices=("source", "heuristic-lit", "heuristic-flat"), default="source")
    parser.add_argument("--face-anchor-bone", default="headfront")
    parser.add_argument("--face-anchor-up-units", type=float, default=0.0)
    parser.add_argument("--face-decals", action="store_true")
    parser.add_argument("--base-texture", type=Path)
    parser.add_argument("--blink-texture", type=Path)
    parser.add_argument("--blink-frames", default="")
    args = parser.parse_args(argv)
    if not args.asset and not args.fbx:
        parser.error("one of --asset or --fbx is required")
    return args


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_asset(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(path))
    elif suffix == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(path))
    else:
        raise ValueError(f"unsupported asset format: {path.suffix}")


def mesh_objects() -> list[bpy.types.Object]:
    return [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]


def armature_objects() -> list[bpy.types.Object]:
    return [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]


def world_bbox(objects: Iterable[bpy.types.Object]) -> tuple[Vector, Vector]:
    mins = Vector((math.inf, math.inf, math.inf))
    maxs = Vector((-math.inf, -math.inf, -math.inf))
    for obj in objects:
        for corner in obj.bound_box:
            p = obj.matrix_world @ Vector(corner)
            mins.x = min(mins.x, p.x)
            mins.y = min(mins.y, p.y)
            mins.z = min(mins.z, p.z)
            maxs.x = max(maxs.x, p.x)
            maxs.y = max(maxs.y, p.y)
            maxs.z = max(maxs.z, p.z)
    return mins, maxs


def center_imported() -> None:
    meshes = mesh_objects()
    if not meshes:
        return
    mins, maxs = world_bbox(meshes)
    center = (mins + maxs) * 0.5
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.location -= center


def set_origin_floor() -> None:
    meshes = mesh_objects()
    if not meshes:
        return
    mins, _ = world_bbox(meshes)
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.location.z -= mins.z


HERO_MATERIALS = {
    "suit": (0.05, 0.34, 0.78, 1.0),
    "belly": (0.23, 0.78, 0.74, 1.0),
    "face": (0.93, 0.61, 0.41, 1.0),
    "horn": (0.15, 0.58, 0.70, 1.0),
    "shoe": (0.03, 0.20, 0.50, 1.0),
}


def make_material(name: str, color: tuple[float, float, float, float], material_kind: str, material_mode: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    if material_mode == "heuristic-flat":
        nodes.clear()
        output = nodes.new(type="ShaderNodeOutputMaterial")
        emission = nodes.new(type="ShaderNodeEmission")
        emission.inputs["Color"].default_value = color
        emission.inputs["Strength"].default_value = 1.0
        links.new(emission.outputs["Emission"], output.inputs["Surface"])
        return mat

    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.9 if material_kind in {"suit", "belly"} else 0.72
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0

        if material_kind in {"suit", "belly"}:
            noise = nodes.new(type="ShaderNodeTexNoise")
            noise.name = f"{material_kind}_woven_noise"
            noise.inputs["Scale"].default_value = 58
            noise.inputs["Detail"].default_value = 13
            noise.inputs["Roughness"].default_value = 0.62
            bump = nodes.new(type="ShaderNodeBump")
            bump.name = f"{material_kind}_cloth_bump"
            bump.inputs["Strength"].default_value = 0.055
            bump.inputs["Distance"].default_value = 0.045
            links.new(noise.outputs["Fac"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        elif material_kind == "face":
            noise = nodes.new(type="ShaderNodeTexNoise")
            noise.name = "skin_soft_noise"
            noise.inputs["Scale"].default_value = 38
            noise.inputs["Detail"].default_value = 6
            bump = nodes.new(type="ShaderNodeBump")
            bump.name = "skin_soft_bump"
            bump.inputs["Strength"].default_value = 0.018
            bump.inputs["Distance"].default_value = 0.02
            links.new(noise.outputs["Fac"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def has_source_material_data() -> bool:
    for obj in mesh_objects():
        if len(obj.material_slots) > 0:
            return True
        mesh = obj.data
        if getattr(mesh, "color_attributes", None) and len(mesh.color_attributes) > 0:
            return True
        if len(mesh.uv_layers) > 0:
            return True
    return False


def enable_source_vertex_color_materials() -> list[str]:
    """Render imported vertex colors when present; leave real texture/material slots untouched."""
    applied: list[str] = []
    for obj in mesh_objects():
        mesh = obj.data
        if len(obj.material_slots) > 0:
            applied.append(f"{obj.name}: imported material slots")
            continue
        color_attrs = list(getattr(mesh, "color_attributes", []))
        if not color_attrs:
            continue
        attr = color_attrs[0]
        mesh.materials.clear()
        mat = bpy.data.materials.new(f"{obj.name}_source_vertex_color")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        output = nodes.new(type="ShaderNodeOutputMaterial")
        attribute = nodes.new(type="ShaderNodeAttribute")
        attribute.attribute_name = attr.name
        emission = nodes.new(type="ShaderNodeEmission")
        emission.inputs["Strength"].default_value = 1.0
        links.new(attribute.outputs["Color"], emission.inputs["Color"])
        links.new(emission.outputs["Emission"], output.inputs["Surface"])
        mesh.materials.append(mat)
        for poly in mesh.polygons:
            poly.material_index = 0
        applied.append(f"{obj.name}: vertex color attribute {attr.name}")
    return applied


def apply_reference_materials(material_mode: str) -> list[str]:
    """Assign colors to mesh regions so they stick to the animated body."""
    for obj in mesh_objects():
        mesh = obj.data
        mesh.materials.clear()
        material_indexes: dict[str, int] = {}
        for name, color in HERO_MATERIALS.items():
            mesh.materials.append(make_material(f"meshy_{name}", color, name, material_mode))
            material_indexes[name] = len(mesh.materials) - 1

        verts = [vertex.co for vertex in mesh.vertices]
        min_x = min(v.x for v in verts)
        max_x = max(v.x for v in verts)
        min_y = min(v.y for v in verts)
        max_y = max(v.y for v in verts)
        min_z = min(v.z for v in verts)
        max_z = max(v.z for v in verts)
        width = max(max_x - min_x, 0.0001)
        depth = max(max_y - min_y, 0.0001)
        height = max(max_z - min_z, 0.0001)
        front_y = min_y + depth * 0.53

        for poly in mesh.polygons:
            center = Vector((0, 0, 0))
            for vertex_index in poly.vertices:
                center += mesh.vertices[vertex_index].co
            center /= len(poly.vertices)
            nx = (center.x - min_x) / width
            nz = (center.z - min_z) / height
            is_front = center.y >= front_y
            face_oval = is_front and ((nx - 0.5) / 0.24) ** 2 + ((nz - 0.77) / 0.13) ** 2 < 1.0
            belly_oval = is_front and ((nx - 0.5) / 0.23) ** 2 + ((nz - 0.43) / 0.21) ** 2 < 1.0
            horn_zone = nz > 0.86 and (nx < 0.25 or nx > 0.75)
            hand_zone = 0.18 < nz < 0.52 and (nx < 0.16 or nx > 0.84)
            shoe_zone = nz < 0.11

            if horn_zone:
                poly.material_index = material_indexes["horn"]
            elif face_oval or hand_zone:
                poly.material_index = material_indexes["face"]
            elif belly_oval:
                poly.material_index = material_indexes["belly"]
            elif shoe_zone:
                poly.material_index = material_indexes["shoe"]
            else:
                poly.material_index = material_indexes["suit"]
    return ["heuristic coordinate material assignment"]


def setup_camera(
    angle_deg: float,
    view: str,
    ortho_height_mult: float,
    camera_shift: tuple[float, float],
    ortho_scale: float | None = None,
    target_z_frac: float = 0.5,
) -> None:
    meshes = mesh_objects()
    mins, maxs = world_bbox(meshes)
    height = maxs.z - mins.z
    width = max(maxs.x - mins.x, maxs.y - mins.y)
    center = (mins + maxs) * 0.5
    target_z = mins.z + height * target_z_frac

    bpy.ops.object.camera_add()
    camera = bpy.context.object
    angle = math.radians(angle_deg)
    distance = max(height * 5.0, 5.0)
    target = Vector((center.x, center.y, target_z))
    if view == "front":
        camera.location = Vector((center.x, center.y - distance * math.cos(angle), center.z + distance * math.sin(angle)))
    elif view == "side-right":
        camera.location = Vector((center.x - distance * math.cos(angle) * 0.48, center.y - distance * math.cos(angle) * 0.82, center.z + distance * math.sin(angle)))
    else:
        camera.location = Vector((center.x + distance * math.cos(angle) * 0.48, center.y - distance * math.cos(angle) * 0.82, center.z + distance * math.sin(angle)))
    direction = target - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    if ortho_scale is not None:
        camera.data.ortho_scale = ortho_scale
    else:
        camera.data.ortho_scale = max(height * ortho_height_mult, width * 1.85)
    camera.data.shift_x = camera_shift[0]
    camera.data.shift_y = camera_shift[1]
    bpy.context.scene.camera = camera


def setup_lighting(light_yaw_deg: float) -> None:
    bpy.context.scene.world = bpy.data.worlds.new("TransparentWorld")
    bpy.context.scene.world.color = (0, 0, 0)

    yaw = math.radians(light_yaw_deg)
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 4))
    key = bpy.context.object
    key.name = "WarmUpperLeftKey"
    key.data.energy = 2.4
    key.rotation_euler = (math.radians(52), 0, yaw)
    key.data.color = (1.0, 0.82, 0.47)

    bpy.ops.object.light_add(type="SUN", location=(0, 0, 4))
    fill = bpy.context.object
    fill.name = "DimFill"
    fill.data.energy = 0.82
    fill.rotation_euler = (math.radians(75), 0, math.radians(120))
    fill.data.color = (0.55, 0.62, 0.72)

    for obj in mesh_objects():
        if hasattr(obj, "visible_shadow"):
            obj.visible_shadow = False
        if hasattr(obj, "hide_shadow"):
            obj.hide_shadow = True


def make_emission_material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new(type="ShaderNodeOutputMaterial")
    emission = nodes.new(type="ShaderNodeEmission")
    emission.inputs["Color"].default_value = color
    emission.inputs["Strength"].default_value = 1.0
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return mat


def add_face_decal_plane(
    name: str,
    material: bpy.types.Material,
    size: tuple[float, float],
) -> bpy.types.Object:
    width, height = size
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    verts = [
        (-width / 2, 0, -height / 2),
        (width / 2, 0, -height / 2),
        (width / 2, 0, height / 2),
        (-width / 2, 0, height / 2),
    ]
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def add_model_face_decals() -> list[str]:
    armatures = armature_objects()
    if not armatures:
        return ["face decals skipped: no armature"]
    armature = armatures[0]
    if not armature.pose.bones.get("Head") or not armature.pose.bones.get("headfront"):
        return ["face decals skipped: no Head bone"]

    black = make_emission_material("face_decal_black", (0.05, 0.025, 0.02, 1.0))
    eye_white = make_emission_material("face_decal_eye_white", (1.0, 0.94, 0.77, 1.0))
    mouth = make_emission_material("face_decal_mouth", (0.20, 0.04, 0.05, 1.0))

    decals = [
        add_face_decal_plane("face_left_eye_white", eye_white, (0.105, 0.082)),
        add_face_decal_plane("face_right_eye_white", eye_white, (0.105, 0.082)),
        add_face_decal_plane("face_left_iris", black, (0.046, 0.052)),
        add_face_decal_plane("face_right_iris", black, (0.046, 0.052)),
        add_face_decal_plane("face_mouth", mouth, (0.105, 0.035)),
    ]
    for obj in decals:
        obj["face_decal"] = True
    return [f"model-space face decals driven by {armature.name}:Head/headfront"]


def parse_frame_set(value: str) -> set[int]:
    frames: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            frames.update(range(int(start), int(end) + 1))
        else:
            frames.add(int(part))
    return frames


def find_source_texture_node() -> bpy.types.ShaderNodeTexImage | None:
    for obj in mesh_objects():
        for slot in obj.material_slots:
            material = slot.material
            if not material or not material.use_nodes:
                continue
            for node in material.node_tree.nodes:
                if node.bl_idname == "ShaderNodeTexImage" and getattr(node, "image", None):
                    return node
    return None


def load_texture(path: Path | None, label: str) -> bpy.types.Image | None:
    if not path:
        return None
    if not path.exists():
        raise FileNotFoundError(f"{label} texture not found: {path}")
    return bpy.data.images.load(str(path))


def update_model_face_decals() -> None:
    armatures = armature_objects()
    if not armatures:
        return
    armature = armatures[0]
    head = bone_world_location(armature, "Head")
    front = bone_world_location(armature, "headfront")
    neck = bone_world_location(armature, "neck")
    if head is None or front is None:
        return
    forward = front - head
    if forward.length < 0.0001:
        return
    forward.normalize()
    up = Vector((0, 0, 1))
    if neck is not None and (head - neck).length > 0.0001:
        up = (head - neck).normalized()
    right = forward.cross(up)
    if right.length < 0.0001:
        right = Vector((1, 0, 0))
    right.normalize()
    up = right.cross(forward).normalized()

    center = front + forward * 0.035 + up * 0.115
    layout = {
        "face_left_eye_white": center - right * 0.075 + up * 0.01,
        "face_right_eye_white": center + right * 0.075 + up * 0.01,
        "face_left_iris": center - right * 0.075 + up * 0.008 + forward * 0.006,
        "face_right_iris": center + right * 0.075 + up * 0.008 + forward * 0.006,
        "face_mouth": center - up * 0.115 + forward * 0.008,
    }
    for obj in bpy.context.scene.objects:
        if not obj.get("face_decal"):
            continue
        obj.location = layout.get(obj.name, center)
        obj.rotation_euler = forward.to_track_quat("Y", "Z").to_euler()


def configure_render(resolution_x: int, resolution_y: int) -> None:
    scene = bpy.context.scene
    available_engines = {item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in available_engines else "BLENDER_EEVEE"
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 32
    scene.render.resolution_x = resolution_x
    scene.render.resolution_y = resolution_y
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"


def action_frame_range() -> tuple[float, float] | None:
    starts: list[float] = []
    ends: list[float] = []
    for obj in bpy.context.scene.objects:
        if obj.animation_data and obj.animation_data.action:
            start, end = obj.animation_data.action.frame_range
            starts.append(start)
            ends.append(end)
    if starts and ends:
        return min(starts), max(ends)
    return None


def root_sample() -> dict:
    armatures = armature_objects()
    armature = armatures[0] if armatures else None
    if not armature:
        return {"armature_location": [0, 0, 0], "root_bone_location": None}
    root_bone = armature.pose.bones[0] if armature.pose.bones else None
    root_location = None
    if root_bone:
        root_location = list((armature.matrix_world @ root_bone.head).to_tuple())
    return {
        "armature_location": list(armature.matrix_world.translation.to_tuple()),
        "root_bone_location": root_location,
    }


def bone_world_location(armature: bpy.types.Object, bone_name: str) -> Vector | None:
    bone = armature.pose.bones.get(bone_name)
    if not bone:
        return None
    return armature.matrix_world @ bone.head


def face_anchor_sample(anchor_bone_preference: str, up_units: float) -> dict | None:
    scene = bpy.context.scene
    camera = scene.camera
    armatures = armature_objects()
    if not camera or not armatures:
        return None
    armature = armatures[0]
    anchor_bone = None
    anchor_world = None
    candidate_bones = [anchor_bone_preference, "headfront", "Head", "head_end", "neck"]
    for bone_name in dict.fromkeys(candidate_bones):
        location = bone_world_location(armature, bone_name)
        if location is not None:
            anchor_bone = bone_name
            anchor_world = location
            break
    if anchor_world is None:
        return None

    if up_units:
        neck = bone_world_location(armature, "neck")
        head = bone_world_location(armature, "Head")
        if neck is not None and head is not None and (head - neck).length > 0.0001:
            anchor_world += (head - neck).normalized() * up_units
        else:
            anchor_world += Vector((0, 0, up_units))

    ndc = bpy_extras.object_utils.world_to_camera_view(scene, camera, anchor_world)
    pixel = [
        round(ndc.x * scene.render.resolution_x, 2),
        round((1.0 - ndc.y) * scene.render.resolution_y, 2),
    ]

    projected_points = {}
    for bone_name in ("neck", "Head", "head_end", "headfront"):
        location = bone_world_location(armature, bone_name)
        if location is None:
            continue
        point_ndc = bpy_extras.object_utils.world_to_camera_view(scene, camera, location)
        projected_points[bone_name] = Vector((
            point_ndc.x * scene.render.resolution_x,
            (1.0 - point_ndc.y) * scene.render.resolution_y,
            0.0,
        ))

    head_pixel_height = 42.0
    head_pixel_width = 34.0
    if "head_end" in projected_points and "neck" in projected_points:
        head_pixel_height = max(1.0, (projected_points["head_end"] - projected_points["neck"]).length)
    elif "Head" in projected_points and "neck" in projected_points:
        head_pixel_height = max(1.0, (projected_points["Head"] - projected_points["neck"]).length * 2.4)
    if "headfront" in projected_points and "Head" in projected_points:
        head_pixel_width = max(1.0, (projected_points["headfront"] - projected_points["Head"]).length * 2.2)
    scale = head_pixel_height / 64.0

    return {
        "bone": anchor_bone,
        "center": pixel,
        "scale": round(scale, 4),
        "head_pixel_height": round(head_pixel_height, 2),
        "head_pixel_width": round(head_pixel_width, 2),
        "rotation_degrees": 0.0,
        "source": "blender_projected_bone",
        "model_space_adjustment": {
            "neck_to_head_up_units": up_units,
        },
    }


def main() -> None:
    args = parse_args()
    out = Path(args.out)
    if not out.is_absolute():
        out = REPO_ROOT / out
    out = out.resolve()
    frames_out = out / "frames_raw"
    frames_out.mkdir(parents=True, exist_ok=True)

    asset = Path(args.asset or args.fbx)

    clear_scene()
    import_asset(asset)
    center_imported()
    set_origin_floor()
    if args.material_mode == "source":
        material_report = enable_source_vertex_color_materials()
    else:
        material_report = apply_reference_materials(args.material_mode)
    face_decal_report = add_model_face_decals() if args.face_decals else []
    setup_camera(
        args.angle_deg,
        args.view,
        args.ortho_height_mult,
        (args.camera_shift_x, args.camera_shift_y),
        args.ortho_scale,
        args.camera_target_z_frac,
    )
    setup_lighting(args.light_yaw_deg)
    configure_render(args.resolution_x or args.resolution, args.resolution_y or args.resolution)
    blink_frames = parse_frame_set(args.blink_frames)
    texture_node = find_source_texture_node()
    imported_texture = texture_node.image if texture_node else None
    base_texture = load_texture(args.base_texture, "base")
    normal_texture = base_texture or imported_texture
    blink_texture = load_texture(args.blink_texture, "blink")

    scene = bpy.context.scene
    source_fps = float(scene.render.fps or 30)
    action_range = action_frame_range()
    has_animation = action_range is not None
    if args.still_frame is not None:
        start = end = float(args.still_frame)
        duration_seconds = max((args.frame_count or 1) / args.fps, 1 / args.fps)
        frame_count = max(1, args.frame_count or 1)
        sample_frames = [start for _ in range(frame_count)]
        has_animation = False
    elif has_animation:
        start, end = action_range
        duration_seconds = max((end - start) / source_fps, 1 / args.fps)
        frame_count = max(2, args.frame_count or int(round(duration_seconds * args.fps)))
        sample_frames = [start + (end - start) * (i / frame_count) for i in range(frame_count)]
    else:
        start = end = float(bpy.context.scene.frame_current)
        duration_seconds = 1 / args.fps
        frame_count = 1
        sample_frames = [start]

    metadata = {
        "asset": str(asset.resolve()),
        "format": asset.suffix.lower().lstrip("."),
        "has_animation": has_animation,
        "source_frame_range": [start, end],
        "source_fps": source_fps,
        "target_fps": args.fps,
        "duration_seconds": duration_seconds,
        "frame_count": frame_count,
        "camera": {
            "type": "orthographic",
            "view": args.view,
            "angle_deg_above_horizontal": args.angle_deg,
            "ortho_scale": scene.camera.data.ortho_scale,
            "target_z_frac": args.camera_target_z_frac,
            "shift": [args.camera_shift_x, args.camera_shift_y],
        },
        "material_mode": args.material_mode,
        "source_material_data_present": has_source_material_data(),
        "material_report": material_report,
        "face_decals": {
            "enabled": args.face_decals,
            "report": face_decal_report,
        },
        "blink_texture": {
            "enabled": bool(blink_texture),
            "path": str(args.blink_texture) if args.blink_texture else None,
            "blink_frames": sorted(blink_frames),
            "texture_node_found": texture_node is not None,
        },
        "base_texture": {
            "enabled": bool(base_texture),
            "path": str(args.base_texture) if args.base_texture else None,
            "texture_node_found": texture_node is not None,
        },
        "lighting": {
            "key": "warm upper-left sun",
            "fill": "dim cool fill",
            "cast_shadows": False,
        },
        "root_motion_samples": [],
    }

    for index, source_frame in enumerate(sample_frames):
        scene.frame_set(int(round(source_frame)))
        bpy.context.view_layer.update()
        if texture_node and blink_texture and index in blink_frames:
            texture_node.image = blink_texture
        elif texture_node and normal_texture:
            texture_node.image = normal_texture
        bpy.context.view_layer.update()
        metadata["root_motion_samples"].append({"index": index, "source_frame": source_frame, **root_sample()})
        face_anchor = face_anchor_sample(args.face_anchor_bone, args.face_anchor_up_units)
        if face_anchor:
            metadata.setdefault("face_anchor_samples", []).append({"index": index, "source_frame": source_frame, **face_anchor})
        metadata.setdefault("render_frame_states", []).append({
            "index": index,
            "source_frame": source_frame,
            "texture_state": "blink" if blink_texture and index in blink_frames else "normal",
        })
        scene.render.filepath = str(frames_out / f"walk_raw_{index:03d}.png")
        bpy.ops.render.render(write_still=True)

    (out / "blender_render_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
