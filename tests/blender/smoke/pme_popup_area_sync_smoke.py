import addon_utils
import bpy
import os
import traceback


success = False

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
    source_region = next(
        (region for region in source_area.regions if region.type == "WINDOW"),
        None,
    )

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
            center=True,
            auto_close=False,
        )

    new_windows = set(bpy.context.window_manager.windows) - windows_before
    target_types = [
        area.ui_type
        for window in new_windows
        for area in window.screen.areas
    ]
    checks = {
        "enabled": module is not None,
        "installed_path": not os.environ.get("PME_EXPECTED_ADDON_ROOT")
        or os.path.normcase(module.__file__).startswith(
            os.path.normcase(os.environ["PME_EXPECTED_ADDON_ROOT"])
        ),
        "finished": result == {"FINISHED"},
        "new_window": len(new_windows) == 1,
        "view_3d": "VIEW_3D" in target_types,
    }
    print(
        "PME_POPUP_AREA_SYNC_CHECKS",
        bpy.app.version_string,
        checks,
        module.__file__,
        [(window.width, window.height) for window in new_windows],
        flush=True,
    )
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    print("PME_POPUP_AREA_SYNC_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
