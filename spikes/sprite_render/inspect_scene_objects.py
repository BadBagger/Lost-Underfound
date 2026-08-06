#!/usr/bin/env python3
"""Print imported Blender object hierarchy for a model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy


argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
args = parser.parse_args(argv)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
input_path = Path(args.input).resolve()
if input_path.suffix.lower() == ".fbx":
    bpy.ops.import_scene.fbx(filepath=str(input_path))
else:
    bpy.ops.import_scene.gltf(filepath=str(input_path))

print(
    json.dumps(
        [
            {
                "name": obj.name,
                "type": obj.type,
                "parent": obj.parent.name if obj.parent else None,
                "children": [child.name for child in obj.children],
                "rotation": [round(v, 4) for v in obj.rotation_euler],
            }
            for obj in bpy.context.scene.objects
        ],
        indent=2,
    )
)
