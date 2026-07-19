import bpy
from bl_ui.properties_paint_common import UnifiedPaintPanel


tool_settings = bpy.context.scene.tool_settings
print(
    "PME_UPS_GLOBAL",
    bpy.app.version_string,
    hasattr(tool_settings, "unified_paint_settings"),
    flush=True,
)
for name in (
    "sculpt",
    "image_paint",
    "vertex_paint",
    "weight_paint",
    "gpencil_paint",
    "gpencil_sculpt",
):
    settings = getattr(tool_settings, name, None)
    print(
        "PME_UPS_OWNER",
        name,
        type(settings).__name__ if settings is not None else None,
        hasattr(settings, "unified_paint_settings") if settings is not None else False,
        flush=True,
    )
current = UnifiedPaintPanel.paint_settings(bpy.context)
print(
    "PME_UPS_CURRENT",
    type(current).__name__ if current is not None else None,
    hasattr(current, "unified_paint_settings") if current is not None else False,
    flush=True,
)
