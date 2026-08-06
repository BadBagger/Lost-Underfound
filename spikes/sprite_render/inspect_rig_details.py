from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import bpy

argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument('--input', required=True)
p.add_argument('--out', required=True)
args = p.parse_args(argv)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
input_path = Path(args.input).resolve()
if input_path.suffix.lower() == ".fbx":
    bpy.ops.import_scene.fbx(filepath=str(input_path))
else:
    bpy.ops.import_scene.gltf(filepath=str(input_path))
report = {'objects': [], 'armatures': [], 'mesh_armature_modifiers': [], 'vertex_groups': []}
for obj in bpy.context.scene.objects:
    report['objects'].append({'name': obj.name, 'type': obj.type, 'parent': obj.parent.name if obj.parent else None})
    if obj.type == 'ARMATURE':
        report['armatures'].append({
            'name': obj.name,
            'bones': [{'name': b.name, 'parent': b.parent.name if b.parent else None, 'head': list(map(float,b.head_local)), 'tail': list(map(float,b.tail_local))} for b in obj.data.bones]
        })
    if obj.type == 'MESH':
        report['vertex_groups'].append({'mesh': obj.name, 'groups': [g.name for g in obj.vertex_groups]})
        for m in obj.modifiers:
            if m.type == 'ARMATURE':
                report['mesh_armature_modifiers'].append({'mesh': obj.name, 'modifier': m.name, 'object': m.object.name if m.object else None})
Path(args.out).parent.mkdir(parents=True, exist_ok=True)
Path(args.out).write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({
 'armatures': [(a['name'], len(a['bones'])) for a in report['armatures']],
 'armature_modifiers': report['mesh_armature_modifiers'],
 'vertex_group_counts': [(v['mesh'], len(v['groups'])) for v in report['vertex_groups']],
 'first_bones': report['armatures'][0]['bones'][:20] if report['armatures'] else []
}, indent=2))
