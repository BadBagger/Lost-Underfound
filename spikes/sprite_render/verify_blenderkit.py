import bpy, json
result = {'enabled_modules': [], 'blenderkit_present': False, 'addon_path': None}
for addon in bpy.context.preferences.addons:
    result['enabled_modules'].append(addon.module)
    if addon.module == 'blenderkit':
        result['blenderkit_present'] = True
        result['addon_path'] = getattr(addon, '__file__', None)
print(json.dumps(result, indent=2))
