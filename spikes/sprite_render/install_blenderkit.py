import bpy, sys, json
zip_path = r'C:\Users\KyleB\Downloads\blenderkit-v3.21.0.260628.zip'
result = {'zip': zip_path, 'installed': False, 'enabled': False, 'modules': [], 'errors': []}
try:
    bpy.ops.preferences.addon_install(filepath=zip_path, overwrite=True)
    result['installed'] = True
except Exception as exc:
    result['errors'].append(f'install: {exc}')
for module in ('blenderkit', 'blenderkit_client'):
    try:
        bpy.ops.preferences.addon_enable(module=module)
        result['enabled'] = True
    except Exception as exc:
        result['errors'].append(f'enable {module}: {exc}')
try:
    bpy.ops.wm.save_userpref()
except Exception as exc:
    result['errors'].append(f'save prefs: {exc}')
for addon in bpy.context.preferences.addons:
    if 'blend' in addon.module.lower() or 'kit' in addon.module.lower():
        result['modules'].append(addon.module)
print(json.dumps(result, indent=2))
