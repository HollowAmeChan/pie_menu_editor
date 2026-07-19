import bpy
import os
import tempfile


directory = os.environ.get(
    "PME_BRUSH_ASSET_LIBRARY",
    os.path.join(tempfile.gettempdir(), "pme_brush_asset_library"),
)
os.makedirs(directory, exist_ok=True)
brush = bpy.data.brushes.new("PME Custom Brush")
brush.use_paint_sculpt = True
brush.asset_mark()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(directory, "custom_brushes.blend"))
print("PME_CUSTOM_ASSET_CREATED", bpy.data.filepath, flush=True)
