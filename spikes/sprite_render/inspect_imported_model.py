"""Inspect imported mesh material/texture/animation data in Blender."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(argv)


def import_model(path: Path) -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    if path.suffix.lower() in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(path))
    elif path.suffix.lower() == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(path))
    else:
        raise ValueError(f"Unsupported model extension: {path.suffix}")


def main() -> None:
    args = parse_args()
    source = Path(args.input).resolve()
    out = Path(args.out).resolve()
    import_model(source)

    report = {
        "file": str(source),
        "size": source.stat().st_size,
        "objects": [],
        "materials": [],
        "images": [],
        "armatures": [],
        "actions": [action.name for action in bpy.data.actions],
    }

    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            report["objects"].append(
                {
                    "name": obj.name,
                    "type": obj.type,
                    "vertices": len(obj.data.vertices),
                    "polygons": len(obj.data.polygons),
                    "uv_layers": [uv.name for uv in obj.data.uv_layers],
                    "color_attributes": [attr.name for attr in obj.data.color_attributes],
                    "material_slots": [
                        slot.material.name if slot.material else None
                        for slot in obj.material_slots
                    ],
                }
            )
        elif obj.type == "ARMATURE":
            report["armatures"].append(
                {"name": obj.name, "bones": len(obj.data.bones)}
            )

    for mat in bpy.data.materials:
        nodes = []
        if mat.use_nodes and mat.node_tree:
            for node in mat.node_tree.nodes:
                item = {"type": node.bl_idname, "name": node.name}
                image = getattr(node, "image", None)
                if image:
                    item["image"] = image.name
                nodes.append(item)
        report["materials"].append(
            {"name": mat.name, "use_nodes": mat.use_nodes, "nodes": nodes}
        )

    for image in bpy.data.images:
        report["images"].append(
            {
                "name": image.name,
                "size": list(image.size),
                "packed": image.packed_file is not None,
                "filepath": image.filepath,
            }
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2)[:5000])


if __name__ == "__main__":
    main()
