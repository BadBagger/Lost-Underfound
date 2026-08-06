#!/usr/bin/env python3
"""Extract the first packed image texture from a GLB/FBX via Blender."""

from __future__ import annotations

import argparse
from pathlib import Path

import bpy


def parse_args() -> argparse.Namespace:
    import sys

    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    suffix = args.asset.suffix.lower()
    if suffix in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(args.asset))
    elif suffix == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(args.asset))
    else:
        raise ValueError(f"unsupported asset format: {args.asset.suffix}")

    candidates = [image for image in bpy.data.images if image.size[0] and image.size[1]]
    candidates = [image for image in candidates if image.name not in {"Render Result", "Viewer Node"}]
    if not candidates:
        raise RuntimeError("no texture images found")

    image = candidates[0]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    image.filepath_raw = str(args.out)
    image.file_format = "PNG"
    image.save()
    print(f"saved {image.name} {tuple(image.size)} to {args.out}")


if __name__ == "__main__":
    main()
