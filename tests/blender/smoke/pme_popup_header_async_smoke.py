import addon_utils
import bpy
import os
import traceback


state = {}


def finish(success):
    source_space = state.get("source_space")
    if source_space is not None:
        source_space.show_region_header = state["source_visible"]
    print(
        "PME_POPUP_HEADER_ASYNC_RESULT",
        "OK" if success else "FAILED",
        flush=True,
    )
    bpy.ops.wm.quit_blender()


def verify():
    try:
        new_windows = (
            set(bpy.context.window_manager.windows) - state["windows_before"]
        )
        new_areas = [
            area
            for window in new_windows
            for area in window.screen.areas
        ]
        new_headers = [
            next(
                region for region in area.regions if region.type == "HEADER"
            )
            for area in new_areas
        ]
        checks = {
            "enabled": state["module"] is not None,
            "installed_path": not os.environ.get("PME_EXPECTED_ADDON_ROOT")
            or os.path.normcase(state["module"].__file__).startswith(
                os.path.normcase(os.environ["PME_EXPECTED_ADDON_ROOT"])
            ),
            "direct_hidden": state["direct_hidden"],
            "direct_shown": state["direct_shown"],
            "finished": state["result"] == {"FINISHED"},
            "new_window": len(new_windows) == 1,
            "new_header_hidden": len(new_areas) == 1
            and not new_areas[0].spaces.active.show_region_header,
            "new_header_position": len(new_headers) == 1
            and new_headers[0].alignment == state["target_position"],
            "source_visibility_unchanged": (
                state["source_space"].show_region_header
                == state["source_visible"]
            ),
            "source_position_unchanged": (
                state["source_header"].alignment
                == state["source_position"]
            ),
        }
        print(
            "PME_POPUP_HEADER_ASYNC_CHECKS",
            bpy.app.version_string,
            checks,
            "source=",
            state["source_position"],
            "target=",
            state["target_position"],
            "new=",
            [
                (area.spaces.active.show_region_header, header.alignment)
                for area, header in zip(new_areas, new_headers)
            ],
            state["module"].__file__,
            flush=True,
        )
        finish(all(checks.values()))
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
    source_header = next(
        region for region in source_area.regions if region.type == "HEADER"
    )
    source_region = next(
        region for region in source_area.regions if region.type == "WINDOW"
    )
    source_space = source_area.spaces.active
    source_visible = source_space.show_region_header
    source_position = source_header.alignment
    target_position = "BOTTOM" if source_position == "TOP" else "TOP"
    override = module.core.screen_utils.get_override_args(
        area=source_area,
        region=source_header,
    )
    operator_type = bpy.types.PME_OT_popup_area
    operator_type.update_header_state(
        bpy.context,
        source_position + "_HIDE",
        source_position == "TOP",
        True,
        override,
    )
    direct_hidden = not source_space.show_region_header
    operator_type.update_header_state(
        bpy.context,
        source_position,
        source_position == "TOP",
        False,
        override,
    )
    direct_shown = source_space.show_region_header

    with bpy.context.temp_override(
        window=source_window,
        screen=source_screen,
        area=source_area,
        region=source_region,
    ):
        result = bpy.ops.pme.popup_area(
            "INVOKE_DEFAULT",
            area="VIEW_3D",
            width=320,
            height=240,
            center=False,
            auto_close=False,
            header=target_position + "_HIDE",
        )

    state.update(
        module=module,
        windows_before=windows_before,
        source_space=source_space,
        source_header=source_header,
        source_visible=source_visible,
        source_position=source_position,
        target_position=target_position,
        direct_hidden=direct_hidden,
        direct_shown=direct_shown,
        result=result,
    )
    bpy.app.timers.register(verify, first_interval=0.15)
except Exception:
    traceback.print_exc()
    finish(False)
