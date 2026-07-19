import addon_utils
import bpy
import traceback


TAG = "PME_POPUP_DESTROY_BEFORE_HEADER"
state = {"callback_calls": 0, "callback_errors": []}


def finish(success, checks=None):
    try:
        module = state.get("module")
        original = state.get("original_callback")
        if module is not None and original is not None:
            module.core.extra_operators._apply_popup_area_header = original
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_CHECKS", checks or {}, flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify():
    try:
        window_pointers = {
            window.as_pointer() for window in bpy.context.window_manager.windows
        }
        popup_screen = bpy.data.screens.get(state["popup_screen_name"])
        legacy_screen_retained = (
            popup_screen is not None and popup_screen.users == 0
        )
        checks = {
            "popup_finished": state["popup_result"] == {"FINISHED"},
            "popup_created": state["popup_created"],
            "window_close_finished": state["close_result"] == {"FINISHED"},
            "popup_destroyed": state["popup_pointer"] not in window_pointers,
            "screen_lifecycle_safe": (
                legacy_screen_retained
                if bpy.app.version < (5, 0, 0)
                else popup_screen is None
            ),
            "header_callback_ran": state["callback_calls"] == 1,
            "header_callback_contained": not state["callback_errors"],
            "addon_still_enabled": addon_utils.check(
                "pie_menu_editor"
            ) == (True, True),
        }
        return finish(all(checks.values()), checks)
    except Exception:
        traceback.print_exc()
        return finish(False)


def close_popup():
    try:
        popup_window = next(
            (
                window
                for window in bpy.context.window_manager.windows
                if window.as_pointer() == state["popup_pointer"]
            ),
            None,
        )
        if popup_window is None:
            state["close_result"] = {"CANCELLED"}
        else:
            popup_area = popup_window.screen.areas[0]
            popup_region = next(
                (
                    region
                    for region in popup_area.regions
                    if region.type == "WINDOW"
                ),
                None,
            )
            with bpy.context.temp_override(
                window=popup_window,
                screen=popup_window.screen,
                area=popup_area,
                region=popup_region,
            ):
                state["close_result"] = bpy.ops.wm.window_close("EXEC_DEFAULT")
        bpy.app.timers.register(verify, first_interval=0.2)
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

    extra_operators = module.core.extra_operators
    original_callback = extra_operators._apply_popup_area_header

    def tracked_callback(*args, **kwargs):
        state["callback_calls"] += 1
        try:
            return original_callback(*args, **kwargs)
        except Exception:
            state["callback_errors"].append(traceback.format_exc())
            raise

    extra_operators._apply_popup_area_header = tracked_callback
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
            auto_close=False,
            header="BOTTOM_HIDE",
        )

    new_windows = set(bpy.context.window_manager.windows) - windows_before
    popup_window = next(iter(new_windows)) if len(new_windows) == 1 else None
    popup_created = popup_window is not None
    popup_pointer = popup_window.as_pointer() if popup_window else 0
    popup_screen_name = popup_window.screen.name if popup_window else ""

    state.update(
        module=module,
        original_callback=original_callback,
        popup_result=popup_result,
        popup_created=popup_created,
        popup_pointer=popup_pointer,
        popup_screen_name=popup_screen_name,
        close_result=None,
    )
    bpy.app.timers.register(close_popup, first_interval=0.001)
except Exception:
    traceback.print_exc()
    finish(False)
