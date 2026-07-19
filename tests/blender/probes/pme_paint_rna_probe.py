import bpy
import json


def type_info(name):
    tp = getattr(bpy.types, name, None)
    if tp is None:
        return None
    props = tp.bl_rna.properties
    return {
        key: key in props
        for key in (
            "brush",
            "palette",
            "use_unified_color",
            "use_unified_size",
            "use_unified_strength",
        )
    }


result = {
    name: type_info(name)
    for name in (
        "Paint",
        "ImagePaint",
        "Sculpt",
        "VertexPaint",
        "WeightPaint",
        "UnifiedPaintSettings",
    )
}

tool_settings = bpy.context.scene.tool_settings
for attr in ("image_paint", "sculpt", "vertex_paint", "weight_paint"):
    value = getattr(tool_settings, attr, None)
    result[f"runtime:{attr}"] = None if value is None else {
        key: hasattr(value, key)
        for key in ("brush", "palette")
    }

print("PME_PAINT_RNA=" + json.dumps(result, sort_keys=True))
