import addon_utils
import bpy
import json


module = addon_utils.enable(
    "pie_menu_editor", default_set=True, persistent=False, handle_error=None
)
from pie_menu_editor.core import keymap_helper


available = set(bpy.context.window_manager.keyconfigs.default.keymaps.keys())

routes = set()
for keymap_list in keymap_helper._km_lists.values():
    for names in keymap_list.rlists.values():
        if names:
            routes.update(names)

explicit = set(keymap_helper._keymap_names)
print(
    "PME_KEYMAP_NAME_AUDIT="
    + json.dumps(
        {
            "version": bpy.app.version_string,
            "available_count": len(available),
            "route_count": len(routes),
            "missing_routes": sorted(routes - available),
            "missing_explicit_with_fallback": sorted(explicit - available),
        },
        sort_keys=True,
    ),
    flush=True,
)
