import addon_utils
import bpy
import traceback


TAG = "PME_POPUP_STATE_CACHE_SMOKE"
MARKER = "PME popup state cache"
state = {"checks": {}}


def finish(success):
    print(TAG + "_CHECKS", state.get("checks", {}), flush=True)
    print(
        TAG + "_DATA",
        bpy.app.version_string,
        {
            "cached_space_property_count": state.get(
                "cached_space_property_count", 0
            ),
            "filter_cached": state.get("filter_cached"),
            "sort_cached": state.get("sort_cached"),
            "restored_filter": state.get("restored_filter"),
            "command_count": state.get("command_count"),
            "timers_before_disable": state.get("timers_before_disable"),
        },
        flush=True,
    )
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def popup_window(windows_before):
    new_windows = set(bpy.context.window_manager.windows) - windows_before
    return next(iter(new_windows)) if len(new_windows) == 1 else None


def invoke_popup():
    source_window = state["source_window"]
    source_area = state["source_area"]
    source_region = state["source_region"]
    windows_before = set(bpy.context.window_manager.windows)
    with bpy.context.temp_override(
        window=source_window,
        screen=source_window.screen,
        area=source_area,
        region=source_region,
    ):
        result = bpy.ops.pme.popup_area(
            "INVOKE_DEFAULT",
            area="OUTLINER",
            width=420,
            height=320,
            center=False,
            auto_close=False,
            cmd=(
                'C.scene["pme_popup_state_cache_cmd"] = '
                'C.scene.get("pme_popup_state_cache_cmd", 0) + 1'
            ),
        )
    return result, popup_window(windows_before)


def verify_second():
    try:
        window = state["second_window"]
        area = window.screen.areas[0]
        space = area.spaces.active
        extra_operators = state["module"].core.extra_operators
        cache = extra_operators._popup_area_states
        cache_snapshot = next(iter(cache.values()), {})
        timers = extra_operators._popup_area_state_timers
        callbacks = tuple(timers)
        command_count = bpy.context.scene.get("pme_popup_state_cache_cmd")
        restored_filter = space.filter_text
        checks = {
            "first_finished": state["first_result"] == {"FINISHED"},
            "first_created": state["first_window_created"],
            "first_closed": state["close_result"] == {"FINISHED"},
            "second_finished": state["second_result"] == {"FINISHED"},
            "second_created": window is not None,
            "outliner_restored": area.ui_type == "OUTLINER",
            "filter_restored": restored_filter == MARKER,
            "sort_restored": not space.use_sort_alpha,
            "statusbar_restored": not window.screen.show_statusbar,
            "command_ran_once": command_count == 1,
            "blender5_cache_present": (
                bool(cache) if bpy.app.version >= (5, 0, 0) else True
            ),
            "version_uses_expected_timer": (
                bool(callbacks)
                if bpy.app.version >= (5, 0, 0)
                else not callbacks
            ),
        }
        addon_utils.disable(
            "pie_menu_editor",
            default_set=True,
            handle_error=None,
        )
        checks.update(
            addon_disabled=addon_utils.check("pie_menu_editor")
            == (False, False),
            cache_cleared=not cache,
            timers_cleared=not timers,
            callbacks_unregistered=all(
                not bpy.app.timers.is_registered(callback)
                for callback in callbacks
            ),
        )
        state["checks"] = checks
        cached_space = cache_snapshot.get("space", {})
        state["cached_space_property_count"] = len(cached_space)
        state["filter_cached"] = cached_space.get("filter_text") == MARKER
        state["sort_cached"] = cached_space.get("use_sort_alpha") is False
        state["restored_filter"] = restored_filter
        state["command_count"] = command_count
        state["timers_before_disable"] = len(callbacks)
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def open_second():
    try:
        result, window = invoke_popup()
        if window is None:
            raise RuntimeError("Second Popup Area was not created")
        state["second_result"] = result
        state["second_window"] = window
        bpy.app.timers.register(verify_second, first_interval=0.3)
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


def close_first():
    try:
        window = state["first_window"]
        area = window.screen.areas[0]
        region = next(
            region for region in area.regions if region.type == "WINDOW"
        )
        with bpy.context.temp_override(
            window=window,
            screen=window.screen,
            area=area,
            region=region,
        ):
            state["close_result"] = bpy.ops.wm.window_close("EXEC_DEFAULT")
        bpy.app.timers.register(open_second, first_interval=0.3)
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

    source_window = bpy.context.window
    source_area = next(
        area for area in source_window.screen.areas if area.type == "VIEW_3D"
    )
    source_region = next(
        region for region in source_area.regions if region.type == "WINDOW"
    )
    state.update(
        module=module,
        source_window=source_window,
        source_area=source_area,
        source_region=source_region,
    )

    first_result, first_window = invoke_popup()
    if first_window is None:
        raise RuntimeError("First Popup Area was not created")
    first_area = first_window.screen.areas[0]
    first_space = first_area.spaces.active
    first_space.filter_text = MARKER
    first_space.use_sort_alpha = False
    first_window.screen.show_statusbar = False
    state.update(
        first_result=first_result,
        first_window=first_window,
        first_window_created=True,
    )
    bpy.app.timers.register(close_first, first_interval=0.6)
except Exception:
    traceback.print_exc()
    finish(False)
