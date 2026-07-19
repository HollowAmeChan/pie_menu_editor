import addon_utils
import bpy
import os
import traceback
from types import SimpleNamespace


success = False
source_space = None
initial_visible = None
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
        (area for area in source_screen.areas if area.type == "VIEW_3D"),
        source_screen.areas[0],
    )
    header_region = next(
        region for region in source_area.regions if region.type == "HEADER"
    )
    window_region = next(
        region for region in source_area.regions if region.type == "WINDOW"
    )
    source_space = source_area.spaces.active
    initial_visible = source_space.show_region_header
    on_top = (
        window_region.y == source_area.y
        if header_region.height > 1
        else header_region.y > source_area.y
    )
    position = "TOP" if on_top else "BOTTOM"
    override = module.core.screen_utils.get_override_args(
        area=source_area,
        region=header_region,
    )
    operator_type = bpy.types.PME_OT_popup_area
    header_updates = []

    operator_type.update_header(
        SimpleNamespace(header=position + "_HIDE"),
        bpy.context,
        on_top,
        True,
        override,
    )
    direct_hidden = not source_space.show_region_header
    operator_type.update_header(
        SimpleNamespace(header=position),
        bpy.context,
        on_top,
        False,
        override,
    )
    direct_shown = source_space.show_region_header

    original_update_header = operator_type.update_header

    def record_update_header(self, context, on_top, visible, data):
        target_space = data["area"].spaces.active
        before = target_space.show_region_header
        result = original_update_header(self, context, on_top, visible, data)
        header_updates.append(
            (
                data["area"].as_pointer(),
                self.header,
                on_top,
                visible,
                before,
                target_space.show_region_header,
            )
        )
        return result

    operator_type.update_header = record_update_header

    with bpy.context.temp_override(
        window=source_window,
        screen=source_screen,
        area=source_area,
        region=window_region,
    ):
        result = bpy.ops.pme.popup_area(
            "INVOKE_DEFAULT",
            area="VIEW_3D",
            width=320,
            height=240,
            center=True,
            auto_close=False,
            header=position + "_HIDE",
        )

    new_windows = set(bpy.context.window_manager.windows) - windows_before
    new_header_states = [
        area.spaces.active.show_region_header
        for window in new_windows
        for area in window.screen.areas
    ]
    checks = {
        "enabled": module is not None,
        "installed_path": not os.environ.get("PME_EXPECTED_ADDON_ROOT")
        or os.path.normcase(module.__file__).startswith(
            os.path.normcase(os.environ["PME_EXPECTED_ADDON_ROOT"])
        ),
        "direct_hidden": direct_hidden,
        "direct_shown": direct_shown,
        "finished": result == {"FINISHED"},
        "new_window": len(new_windows) == 1,
        "new_header_hidden": new_header_states == [False],
        "source_unchanged": source_space.show_region_header == initial_visible,
    }
    print(
        "PME_POPUP_HEADER_CHECKS",
        bpy.app.version_string,
        checks,
        "position=",
        position,
        "new_states=",
        new_header_states,
        "updates=",
        header_updates,
        module.__file__,
        flush=True,
    )
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    if source_space is not None and initial_visible is not None:
        source_space.show_region_header = initial_visible
    print("PME_POPUP_HEADER_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
