import json
import os
import sys

import bpy


sys.path.insert(0, os.environ["PME_ADDONS_ROOT"])
from pie_menu_editor.core.extra_operators import PREFERENCES_PANEL_CANDIDATES


result = {}
for section, candidates in PREFERENCES_PANEL_CANDIDATES.items():
    available = [name for name in candidates if hasattr(bpy.types, name)]
    result[section] = available

print(
    "PME_PREFERENCES_PANEL_MAP_AUDIT",
    json.dumps(
        {
            "blender": bpy.app.version_string,
            "sections": result,
            "missing_sections": [key for key, value in result.items() if not value],
        },
        sort_keys=True,
    ),
    flush=True,
)
