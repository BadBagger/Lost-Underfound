import bpy, json
import addon_utils
addon_utils.enable('blenderkit', default_set=True)
prefs = bpy.context.preferences.addons['blenderkit'].preferences
out = {}
for name in dir(prefs):
    if name.startswith('_'):
        continue
    if any(k in name.lower() for k in ['api', 'token', 'login', 'user', 'email', 'key', 'oauth']):
        try:
            value = getattr(prefs, name)
            if isinstance(value, str):
                out[name] = {'present': bool(value), 'length': len(value)}
            else:
                out[name] = str(value)
        except Exception as e:
            out[name] = f'ERR {e}'
print(json.dumps(out, indent=2))
