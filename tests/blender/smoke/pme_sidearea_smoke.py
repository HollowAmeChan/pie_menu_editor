import addon_utils
import bpy
import os
import traceback


initial_area_count = 0
screen = None
window = None
side = os.environ.get("PME_SIDE", "LEFT")


def area_size(area):
    return area.width if side in {"LEFT", "RIGHT"} else area.height


def finish(success):
    print("PME_SIDEAREA_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def find_area(ui_type):
    return next((area for area in screen.areas if area.ui_type == ui_type), None)


def call_toggle(action, context_area, width=260):
    region = next(
        (region for region in context_area.regions if region.type == "WINDOW"), None
    )
    with bpy.context.temp_override(
        window=window, screen=screen, area=context_area, region=region
    ):
        return bpy.ops.pme.sidearea_toggle(
            "EXEC_DEFAULT",
            action=action,
            main_area="VIEW_3D",
            area="IMAGE_EDITOR",
            ignore_area="NONE",
            side=side,
            width=width,
            header="DEFAULT",
        )


def verify_hidden():
    try:
        checks = {
            "area_count_restored": len(screen.areas) == initial_area_count,
            "main_area_present": find_area("VIEW_3D") is not None,
            "side_area_removed": find_area("IMAGE_EDITOR") is None,
        }
        print("PME_SIDEAREA_HIDE_CHECKS", checks, flush=True)
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def verify_reconfigured_and_hide():
    try:
        main_area = find_area("VIEW_3D")
        side_area = find_area("IMAGE_EDITOR")
        checks = {
            "area_count_stable": len(screen.areas) == initial_area_count + 1,
            "side_reconfigured": side_area is not None,
            "side_resized": side_area is not None and abs(area_size(side_area) - 320) <= 12,
        }
        print("PME_SIDEAREA_RECONFIGURE_CHECKS", checks, flush=True)
        if not all(checks.values()):
            return finish(False)
        result = call_toggle("HIDE", main_area, width=320)
        print("PME_SIDEAREA_HIDE_RETURN", result, flush=True)
        bpy.app.timers.register(verify_hidden, first_interval=2.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def verify_shown_and_reconfigure():
    try:
        main_area = find_area("VIEW_3D")
        side_area = find_area("IMAGE_EDITOR")
        checks = {
            "area_available": len(screen.areas) in {initial_area_count, initial_area_count + 1},
            "main_area_present": main_area is not None,
            "side_area_present": side_area is not None,
            "side_size": side_area is not None and abs(area_size(side_area) - 260) <= 12,
        }
        print("PME_SIDEAREA_SHOW_CHECKS", checks, flush=True)
        print(
            "PME_SIDEAREA_LAYOUT",
            [
                (area.ui_type, area.x, area.y, area.width, area.height)
                for area in screen.areas
            ],
            flush=True,
        )
        if not all(checks.values()):
            return finish(False)
        side_area.ui_type = "TEXT_EDITOR"
        result = call_toggle("SHOW", main_area, width=320)
        print("PME_SIDEAREA_RECONFIGURE_RETURN", result, flush=True)
        bpy.app.timers.register(verify_reconfigured_and_hide, first_interval=2.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def show_sidearea():
    global initial_area_count, screen, window
    try:
        window = bpy.context.window_manager.windows[-1]
        screen = window.screen
        main_area = find_area("VIEW_3D")
        if main_area is None:
            raise RuntimeError("VIEW_3D area not found")
        initial_area_count = len(screen.areas)
        if initial_area_count != 1:
            raise RuntimeError(f"Expected one popup area, got {initial_area_count}")
        result = call_toggle("SHOW", main_area)
        print("PME_SIDEAREA_SHOW_RETURN", result, flush=True)
        bpy.app.timers.register(verify_shown_and_reconfigure, first_interval=2.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def create_test_window():
    try:
        result = bpy.ops.pme.popup_area(
            "INVOKE_DEFAULT",
            area="VIEW_3D",
            width=1200,
            height=800,
            center=True,
            auto_close=False,
        )
        print("PME_SIDEAREA_WINDOW_RETURN", result, flush=True)
        bpy.app.timers.register(show_sidearea, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_SIDEAREA_ENABLE_RETURN", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(create_test_window, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
