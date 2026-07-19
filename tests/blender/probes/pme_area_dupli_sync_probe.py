import bpy
import traceback


try:
    initial_windows = set(bpy.context.window_manager.windows)
    window = next(iter(initial_windows))
    screen = window.screen
    area = screen.areas[0]
    region = next((region for region in area.regions if region.type == "WINDOW"), None)
    print(
        "PME_AREA_DUPLI_SOURCE",
        area.type if area else None,
        (area.width, area.height) if area else None,
        flush=True,
    )
    with bpy.context.temp_override(
        window=window,
        screen=screen,
        area=area,
        region=region,
    ):
        result = bpy.ops.screen.area_dupli("INVOKE_DEFAULT")
    new_windows = set(bpy.context.window_manager.windows) - initial_windows
    print("PME_AREA_DUPLI_CALL", result, flush=True)
    print(
        "PME_AREA_DUPLI_WINDOWS",
        [(window.width, window.height, window.screen.name) for window in new_windows],
        flush=True,
    )
except Exception:
    traceback.print_exc()
finally:
    bpy.ops.wm.quit_blender()
