import bpy
import json
import traceback


def finish():
    bpy.ops.wm.quit_blender()


def probe():
    try:
        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.object.mode_set(mode="SCULPT")
            result = bpy.ops.brush.asset_activate(
                asset_library_type="ESSENTIALS",
                relative_asset_identifier=(
                    "brushes/essentials_brushes-mesh_sculpt.blend/Brush/Draw"
                ),
            )
            settings = bpy.context.scene.tool_settings.sculpt
            ref = settings.brush_asset_reference
            brush = settings.brush
            props = {
                p.identifier: getattr(ref, p.identifier)
                for p in ref.bl_rna.properties
                if p.identifier != "rna_type"
            }
            print("PME_BRUSH_ACTIVATE", result, flush=True)
            print("PME_BRUSH_NAME", settings.brush.name if settings.brush else None, flush=True)
            print("PME_BRUSH_REF", json.dumps(props, sort_keys=True), flush=True)
            print(
                "PME_BRUSH_ID",
                {
                    "library": str(brush.library) if brush else None,
                    "library_filepath": brush.library.filepath if brush and brush.library else None,
                    "asset_data": bool(brush.asset_data) if brush else None,
                    "library_weak_reference": str(brush.library_weak_reference) if brush else None,
                    "is_editable": brush.is_editable if brush else None,
                    "is_runtime_data": brush.is_runtime_data if brush else None,
                },
                flush=True,
            )
            print(
                "PME_BRUSH_READONLY",
                settings.bl_rna.properties["brush"].is_readonly,
                settings.bl_rna.properties["brush_asset_reference"].is_readonly,
                flush=True,
            )
    except Exception:
        traceback.print_exc()
    return finish()


bpy.app.timers.register(probe, first_interval=0.5)
