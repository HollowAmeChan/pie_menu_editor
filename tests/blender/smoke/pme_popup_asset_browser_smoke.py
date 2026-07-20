import addon_utils
import bpy
import traceback


TAG = "PME_POPUP_ASSET_BROWSER_SMOKE"
REQUESTED_SIZE = (900, 600)
state = {"checks": {}, "windows_before": set()}
module = None


def finish(success):
    print(TAG + "_CHECKS", state["checks"], flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify_closed():
    try:
        checks = state["checks"]
        popup_pointer = state["popup_pointer"]
        checks["popup_closed"] = not any(
            window.as_pointer() == popup_pointer
            for window in bpy.context.window_manager.windows
        )
        checks["source_window_alive"] = any(
            window.as_pointer() == state["source_pointer"]
            for window in bpy.context.window_manager.windows
        )
        checks["addon_still_enabled"] = addon_utils.check(
            "pie_menu_editor"
        )[1]
        extra_operators = module.core.extra_operators
        checks["state_timer_removed"] = not (
            extra_operators._popup_area_state_timers
        )
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def verify_opened():
    try:
        windows = list(bpy.context.window_manager.windows)
        new_windows = [
            window
            for window in windows
            if window not in state["windows_before"]
        ]
        popup = new_windows[0] if len(new_windows) == 1 else None
        area = popup.screen.areas[0] if popup and popup.screen.areas else None
        space = area.spaces.active if area else None
        checks = state["checks"]
        checks.update(
            new_window=len(new_windows) == 1,
            asset_ui_type=area is not None and area.ui_type == "ASSETS",
            file_browser_area=area is not None and area.type == "FILE_BROWSER",
            asset_browse_mode=(
                space is not None and space.browse_mode == "ASSETS"
            ),
            asset_params_ready=(
                space is not None and space.params is not None
            ),
            requested_width=(
                popup is not None
                and abs(popup.width - REQUESTED_SIZE[0]) <= 2
            ),
            requested_height=(
                popup is not None
                and abs(popup.height - REQUESTED_SIZE[1]) <= 2
            ),
        )
        if popup is None or area is None or not all(checks.values()):
            return finish(False)

        state["popup_pointer"] = popup.as_pointer()
        with bpy.context.temp_override(
            window=popup,
            screen=popup.screen,
            area=area,
        ):
            close_result = bpy.ops.wm.window_close()
        checks["close_finished"] = close_result == {"FINISHED"}
        bpy.app.timers.register(verify_closed, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def open_asset_browser():
    try:
        source = bpy.context.window
        state["source_pointer"] = source.as_pointer()
        state["windows_before"] = set(bpy.context.window_manager.windows)
        result = bpy.ops.pme.popup_area(
            "INVOKE_DEFAULT",
            area="ASSETS",
            width=REQUESTED_SIZE[0],
            height=REQUESTED_SIZE[1],
            center=False,
            auto_close=False,
        )
        state["checks"]["open_finished"] = result == {"FINISHED"}
        bpy.app.timers.register(verify_opened, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    global module
    try:
        module = addon_utils.enable(
            "pie_menu_editor",
            default_set=True,
            persistent=False,
            handle_error=None,
        )
        if not hasattr(bpy.types.WindowManager, "pme"):
            for waiter in module.core.PME_OT_wait_context.instances:
                waiter.cancelled = True
            module.core.on_context()
        bpy.app.timers.register(open_asset_browser, first_interval=0.2)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.1)
