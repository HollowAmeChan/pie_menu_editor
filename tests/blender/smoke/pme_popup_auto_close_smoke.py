import addon_utils
import bpy
import traceback


state = {}


def finish(success):
    print("PME_POPUP_AUTO_CLOSE_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def verify_closed():
    try:
        windows = set(bpy.context.window_manager.windows)
        checks = {
            "popup_finished": state["popup_result"] == {"FINISHED"},
            "temp_created": state["temp_created"],
            "close_passthrough": state["close_result"] == {"PASS_THROUGH"},
            "temp_closed": state["temp_window"] not in windows,
            "window_count_restored": len(windows) == len(state["windows_before"]),
        }
        print(
            "PME_POPUP_AUTO_CLOSE_CHECKS",
            bpy.app.version_string,
            checks,
            "screens=",
            [window.screen.name for window in windows],
            flush=True,
        )
        finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


def trigger_close():
    try:
        source_window = state["source_window"]
        source_area = state["source_area"]
        source_region = state["source_region"]
        with bpy.context.temp_override(
            window=source_window,
            screen=source_window.screen,
            area=source_area,
            region=source_region,
        ):
            close_result = bpy.ops.pme.window_auto_close("EXEC_DEFAULT")
        state["close_result"] = close_result
        bpy.app.timers.register(verify_closed, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


try:
    module = addon_utils.enable(
        "pie_menu_editor",
        default_set=True,
        persistent=False,
        handle_error=None,
    )
    if not hasattr(bpy.types, "PME_OT_popup_area"):
        for waiter in module.core.PME_OT_wait_context.instances:
            waiter.cancelled = True
        module.core.on_context()

    windows_before = set(bpy.context.window_manager.windows)
    source_window = next(iter(windows_before))
    source_screen = source_window.screen
    source_area = next(
        area for area in source_screen.areas if area.type == "VIEW_3D"
    )
    source_region = next(
        region for region in source_area.regions if region.type == "WINDOW"
    )
    with bpy.context.temp_override(
        window=source_window,
        screen=source_screen,
        area=source_area,
        region=source_region,
    ):
        popup_result = bpy.ops.pme.popup_area(
            "INVOKE_DEFAULT",
            area="VIEW_3D",
            width=320,
            height=240,
            center=False,
            auto_close=True,
        )
    new_windows = set(bpy.context.window_manager.windows) - windows_before
    temp_window = next(iter(new_windows)) if len(new_windows) == 1 else None
    temp_created = temp_window is not None and temp_window.screen.name.startswith(
        "PME Temp "
    )
    state.update(
        popup_result=popup_result,
        windows_before=windows_before,
        source_window=source_window,
        source_area=source_area,
        source_region=source_region,
        temp_window=temp_window,
        temp_created=temp_created,
    )
    bpy.app.timers.register(trigger_close, first_interval=0.1)
except Exception:
    traceback.print_exc()
    finish(False)
