import bpy
import traceback


def probe():
    try:
        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.object.mode_set(mode="SCULPT")
            brush = bpy.data.brushes.new("PME Local Brush")
            brush.use_paint_sculpt = True
            brush.asset_mark()
            result = bpy.ops.brush.asset_activate(
                asset_library_type="LOCAL",
                relative_asset_identifier="Brush/PME Local Brush",
            )
            settings = bpy.context.scene.tool_settings.sculpt
            ref = settings.brush_asset_reference
            print("PME_LOCAL_RESULT", result, flush=True)
            print("PME_LOCAL_ACTIVE", settings.brush.name if settings.brush else None, flush=True)
            print(
                "PME_LOCAL_REF",
                ref.asset_library_type,
                ref.asset_library_identifier,
                ref.relative_asset_identifier,
                flush=True,
            )
    except Exception:
        traceback.print_exc()
    bpy.ops.wm.quit_blender()


bpy.app.timers.register(probe, first_interval=0.5)
