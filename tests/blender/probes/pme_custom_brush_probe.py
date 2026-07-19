import bpy
import os
import tempfile
import traceback


ASSET_LIBRARY = os.environ.get(
    "PME_BRUSH_ASSET_LIBRARY",
    os.path.join(tempfile.gettempdir(), "pme_brush_asset_library"),
)


def activate():
    try:
        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            library = bpy.context.preferences.filepaths.asset_libraries[-1]
            result = bpy.ops.brush.asset_activate(
                asset_library_type="CUSTOM",
                asset_library_identifier=library.name,
                relative_asset_identifier=(
                    "custom_brushes.blend/Brush/PME Custom Brush"
                ),
            )
            settings = bpy.context.scene.tool_settings.sculpt
            ref = settings.brush_asset_reference
            print("PME_CUSTOM_RESULT", result, flush=True)
            print("PME_CUSTOM_ACTIVE", settings.brush.name if settings.brush else None, flush=True)
            print(
                "PME_CUSTOM_REF",
                ref.asset_library_type,
                ref.asset_library_identifier,
                ref.relative_asset_identifier,
                flush=True,
            )
    except Exception:
        traceback.print_exc()
    bpy.ops.wm.quit_blender()


def setup():
    bpy.ops.preferences.asset_library_add(directory=ASSET_LIBRARY)
    library = bpy.context.preferences.filepaths.asset_libraries[-1]
    library.name = "PME Test Assets"
    area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
    region = next(r for r in area.regions if r.type == "WINDOW")
    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.object.mode_set(mode="SCULPT")
    bpy.app.timers.register(activate, first_interval=3.0)


bpy.app.timers.register(setup, first_interval=0.5)
