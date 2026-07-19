import addon_utils
import bpy
import traceback


initial_windows = 0


def finish(success):
    print("PME_POPUP_AREA_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify():
    try:
        windows = list(bpy.context.window_manager.windows)
        checks = {
            "new_window": len(windows) > initial_windows,
            "valid_screen": all(window.screen is not None for window in windows),
        }
        print(
            "PME_POPUP_AREA_CHECKS",
            checks,
            [(window.width, window.height, window.screen.name) for window in windows],
            flush=True,
        )
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def open_popup_area():
    global initial_windows
    try:
        initial_windows = len(bpy.context.window_manager.windows)
        result = bpy.ops.pme.popup_area(
            "INVOKE_DEFAULT",
            area="VIEW_3D",
            width=320,
            height=240,
            center=True,
            auto_close=False,
        )
        print("PME_POPUP_AREA_CALL_RETURN", result, flush=True)
        bpy.app.timers.register(verify, first_interval=2.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_POPUP_AREA_ENABLE_RETURN", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(open_popup_area, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
