#!/usr/bin/env python3
"""Render a labeled atlas for a Meshy part-segmentation FBX."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


PART_COLORS = [
    (0.10, 0.45, 0.95, 1.0),
    (0.95, 0.25, 0.18, 1.0),
    (0.10, 0.75, 0.35, 1.0),
    (0.90, 0.72, 0.15, 1.0),
    (0.60, 0.25, 0.95, 1.0),
    (0.05, 0.75, 0.78, 1.0),
    (0.95, 0.45, 0.10, 1.0),
    (0.90, 0.25, 0.60, 1.0),
    (0.35, 0.72, 0.95, 1.0),
    (0.58, 0.42, 0.25, 1.0),
    (0.78, 0.88, 0.22, 1.0),
    (0.95, 0.72, 0.58, 1.0),
    (0.18, 0.18, 0.22, 1.0),
]


def parse_args() -> argparse.Namespace:
    import sys

    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--fbx", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--resolution", type=int, default=512)
    parser.add_argument("--angle-deg", type=float, default=8.0)
    parser.add_argument("--views", default="front,side_left,side_right")
    parser.add_argument("--solo-parts", action="store_true")
    return parser.parse_args(argv)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def mesh_objects() -> list[bpy.types.Object]:
    return [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]


def world_bbox(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
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


def center_and_floor() -> None:
    meshes = mesh_objects()
    mins, maxs = world_bbox(meshes)
    center = (mins + maxs) * 0.5
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.location -= center
    mins, _ = world_bbox(meshes)
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.location.z -= mins.z


def material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
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


def assign_part_materials() -> None:
    for index, obj in enumerate(sorted(mesh_objects(), key=lambda item: item.name)):
        obj.data.materials.clear()
        obj.data.materials.append(material(f"seg_{obj.name}", PART_COLORS[index % len(PART_COLORS)]))
        for polygon in obj.data.polygons:
            polygon.material_index = 0


def setup_render(resolution: int) -> None:
    scene = bpy.context.scene
    available = {item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in available else "BLENDER_EEVEE"
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new("SegmentationWorld")
    scene.world.color = (0.5, 0.5, 0.5)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"


def setup_camera(view: str, angle_deg: float) -> None:
    meshes = mesh_objects()
    mins, maxs = world_bbox(meshes)
    height = maxs.z - mins.z
    width = max(maxs.x - mins.x, maxs.y - mins.y)
    center = (mins + maxs) * 0.5
    distance = max(height * 5.0, 5.0)
    angle = math.radians(angle_deg)

    if bpy.context.scene.camera is None:
        bpy.ops.object.camera_add()
        camera = bpy.context.object
        bpy.context.scene.camera = camera
    else:
        camera = bpy.context.scene.camera

    if view == "front":
        camera.location = Vector((center.x, center.y - distance * math.cos(angle), center.z + distance * math.sin(angle)))
    elif view == "side_right":
        camera.location = Vector((center.x - distance * math.cos(angle) * 0.48, center.y - distance * math.cos(angle) * 0.82, center.z + distance * math.sin(angle)))
    else:
        camera.location = Vector((center.x + distance * math.cos(angle) * 0.48, center.y - distance * math.cos(angle) * 0.82, center.z + distance * math.sin(angle)))

    target = Vector((center.x, center.y, center.z))
    direction = target - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = max(height * 1.38, width * 1.65)


def part_metadata() -> list[dict]:
    rows = []
    for index, obj in enumerate(sorted(mesh_objects(), key=lambda item: item.name)):
        mins, maxs = world_bbox([obj])
        rows.append(
            {
                "name": obj.name,
                "color_rgb": [round(channel * 255) for channel in PART_COLORS[index % len(PART_COLORS)][:3]],
                "vertices": len(obj.data.vertices),
                "polygons": len(obj.data.polygons),
                "bbox": {
                    "min": [round(mins.x, 4), round(mins.y, 4), round(mins.z, 4)],
                    "max": [round(maxs.x, 4), round(maxs.y, 4), round(maxs.z, 4)],
                },
                "color_attributes": [attr.name for attr in getattr(obj.data, "color_attributes", [])],
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    clear_scene()
    bpy.ops.import_scene.fbx(filepath=args.fbx)
    center_and_floor()
    assign_part_materials()
    setup_render(args.resolution)

    rendered = []
    for view in [part.strip() for part in args.views.split(",") if part.strip()]:
        setup_camera(view, args.angle_deg)
        bpy.context.scene.render.filepath = str(out / f"part_segmentation_{view}.png")
        bpy.ops.render.render(write_still=True)
        rendered.append(f"part_segmentation_{view}.png")

    solo_rendered = []
    if args.solo_parts:
        all_meshes = sorted(mesh_objects(), key=lambda item: item.name)
        for obj in all_meshes:
            for other in all_meshes:
                other.hide_render = other != obj
            setup_camera("front", args.angle_deg)
            bpy.context.scene.render.filepath = str(out / f"solo_{obj.name}_front.png")
            bpy.ops.render.render(write_still=True)
            solo_rendered.append(f"solo_{obj.name}_front.png")
        for other in all_meshes:
            other.hide_render = False

    metadata = {
        "fbx": str(Path(args.fbx).resolve()),
        "renders": rendered,
        "solo_renders": solo_rendered,
        "parts": part_metadata(),
    }
    (out / "part_segmentation_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
