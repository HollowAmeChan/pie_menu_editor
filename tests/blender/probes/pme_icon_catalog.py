import bpy
import json


items = bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items
print(
    "PME_ICON_CATALOG=" + json.dumps(sorted(item.identifier for item in items)),
    flush=True,
)
