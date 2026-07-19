import bpy
import json


items = bpy.types.Event.bl_rna.properties["type"].enum_items
print(
    "PME_EVENT_CATALOG=" + json.dumps(sorted(item.identifier for item in items)),
    flush=True,
)
