import addon_utils
import bpy
import traceback


windows_before = set()
REQUESTED_SIZE = (320, 240)


def finish(success):
    print("PME_POPUP_AREA_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify():
    try:
        windows = list(bpy.context.window_manager.windows)
        new_windows = [window for window in windows if window not in windows_before]
        popup = new_windows[0] if len(new_windows) == 1 else None
        checks = {
            "new_window": len(new_windows) == 1,
            "valid_screen": all(window.screen is not None for window in windows),
            "requested_width": (
                popup is not None and abs(popup.width - REQUESTED_SIZE[0]) <= 2
            ),
            "requested_height": (
                popup is not None and abs(popup.height - REQUESTED_SIZE[1]) <= 2
            ),
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
    global windows_before
    try:
        windows_before = set(bpy.context.window_manager.windows)
        result = bpy.ops.pme.popup_area(
            "INVOKE_DEFAULT",
            area="VIEW_3D",
            width=REQUESTED_SIZE[0],
            height=REQUESTED_SIZE[1],
            center=False,
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
