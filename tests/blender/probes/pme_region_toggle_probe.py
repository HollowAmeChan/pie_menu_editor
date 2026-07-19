import bpy
import traceback


success = False
try:
    window = bpy.context.window_manager.windows[0]
    screen = window.screen
    area = next(
        candidate for candidate in screen.areas if candidate.type == "VIEW_3D"
    )
    header = next(
        candidate for candidate in area.regions if candidate.type == "HEADER"
    )
    initial = area.spaces.active.show_region_header
    with bpy.context.temp_override(
        window=window,
        screen=screen,
        area=area,
        region=header,
    ):
        hide_result = bpy.ops.screen.region_toggle(region_type="HEADER")
    hidden = area.spaces.active.show_region_header
    with bpy.context.temp_override(
        window=window,
        screen=screen,
        area=area,
        region=header,
    ):
        restore_result = bpy.ops.screen.region_toggle(region_type="HEADER")
    restored = area.spaces.active.show_region_header
    checks = {
        "hide_finished": hide_result == {"FINISHED"},
        "changed": hidden != initial,
        "restore_finished": restore_result == {"FINISHED"},
        "restored": restored == initial,
    }
    print(
        "PME_REGION_TOGGLE_CHECKS",
        bpy.app.version_string,
        checks,
        (initial, hidden, restored),
        flush=True,
    )
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    print("PME_REGION_TOGGLE_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
