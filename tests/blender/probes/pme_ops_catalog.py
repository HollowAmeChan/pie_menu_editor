import bpy
import json


modules = (
    "mesh",
    "object",
    "view3d",
    "screen",
    "wm",
    "transform",
    "anim",
    "action",
    "graph",
    "paint",
    "sculpt",
    "brush",
)
catalog = {name: sorted(dir(getattr(bpy.ops, name))) for name in modules}
print("PME_OPS_CATALOG=" + json.dumps(catalog, sort_keys=True), flush=True)
