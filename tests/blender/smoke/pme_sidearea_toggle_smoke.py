import addon_utils
import bpy
import os
import traceback


TAG = "PME_SIDEAREA_TOGGLE_SMOKE"
SIDE = os.environ.get("PME_SIDE", "RIGHT").upper()
UI_SCALE = os.environ.get("PME_UI_SCALE")
UI_LINE_WIDTH = os.environ.get("PME_UI_LINE_WIDTH")
state = {
    "step": 0,
    "success": False,
    "checks": {},
    "before": None,
    "before_pointers": set(),
    "original_ui_scale": None,
    "original_ui_line_width": None,
}


def area_size(area):
    return area.width if SIDE in {"LEFT", "RIGHT"} else area.height


def find_side_area(screen, main):
    for area in screen.areas:
        if area.ui_type != "PROPERTIES" or area == main:
            continue
        if SIDE in {"LEFT", "RIGHT"}:
            if abs(area.y - main.y) > 5 or abs(area.height - main.height) > 5:
                continue
            gap = (
                main.x - (area.x + area.width)
                if SIDE == "LEFT"
                else area.x - (main.x + main.width)
            )
        else:
            if abs(area.x - main.x) > 5 or abs(area.width - main.width) > 5:
                continue
            gap = (
                area.y - (main.y + main.height)
                if SIDE == "TOP"
                else main.y - (area.y + area.height)
            )
        if 0 < gap < 12:
            return area
    return None


def area_snapshot(screen):
    return sorted(
        (
            area.ui_type,
            area.x,
            area.y,
            area.width,
            area.height,
        )
        for area in screen.areas
    )


def finish(success):
    state["success"] = success
    try:
        view = bpy.context.preferences.view
        if state["original_ui_scale"] is not None:
            view.ui_scale = state["original_ui_scale"]
        if state["original_ui_line_width"] is not None:
            view.ui_line_width = state["original_ui_line_width"]
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_CHECKS", state["checks"], flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def run_step():
    try:
        context = bpy.context
        screen = context.window.screen
        if state["step"] == 0:
            main = next(area for area in screen.areas if area.ui_type == "VIEW_3D")
            before = area_snapshot(screen)
            state["before"] = before
            state["before_pointers"] = {
                area.as_pointer() for area in screen.areas
            }
            with context.temp_override(area=main):
                result = bpy.ops.pme.sidearea_toggle(
                    "EXEC_DEFAULT",
                    action="SHOW",
                    area="PROPERTIES",
                    side=SIDE,
                    main_area="VIEW_3D",
                    width=300,
                )
            state["checks"]["show_finished"] = result == {"FINISHED"}
            state["checks"]["before_has_main_area"] = any(
                item[0] == "VIEW_3D" for item in before
            )
            print(TAG + "_SHOW_REQUEST", result, before, flush=True)
            state["step"] = 1
            return 0.35

        if state["step"] == 1:
            shown = area_snapshot(screen)
            main = next((area for area in screen.areas if area.ui_type == "VIEW_3D"), None)
            side_area = find_side_area(screen, main) if main else None
            state["show_delta"] = len(shown) - len(state["before"])
            state["checks"]["show_area_count_valid"] = state[
                "show_delta"
            ] in {0, 1}
            state["checks"]["show_types_correct"] = (
                main is not None
                and side_area is not None
                and side_area.ui_type == "PROPERTIES"
            )
            state["checks"]["show_requested_size"] = (
                side_area is not None
                and abs(area_size(side_area) - 300) <= 12
            )
            print(TAG + "_SHOWN", shown, flush=True)
            if main is None or side_area is None:
                return finish(False)

            with context.temp_override(area=main):
                result = bpy.ops.pme.sidearea_toggle(
                    "EXEC_DEFAULT",
                    action="HIDE",
                    area="PROPERTIES",
                    side=SIDE,
                    main_area="VIEW_3D",
                    width=300,
                )
            state["checks"]["hide_finished"] = result == {"FINISHED"}
            print(TAG + "_HIDE_REQUEST", result, flush=True)
            state["step"] = 2
            return 0.35

        hidden = area_snapshot(screen)
        main = next(
            (area for area in screen.areas if area.ui_type == "VIEW_3D"),
            None,
        )
        state["checks"]["hide_area_count_valid"] = (
            len(hidden)
            == len(state["before"]) + state["show_delta"] - 1
        )
        state["checks"]["hide_removed_side"] = (
            main is not None and find_side_area(screen, main) is None
        )
        if state["show_delta"] == 1:
            state["checks"]["hide_restored_layout"] = hidden == state["before"]
        print(TAG + "_HIDDEN", hidden, flush=True)
        return finish(all(state["checks"].values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


try:
    module = addon_utils.enable(
        "pie_menu_editor",
        default_set=True,
        persistent=False,
        handle_error=None,
    )
    package = module.core
    if not hasattr(bpy.types.WindowManager, "pme"):
        for waiter in package.PME_OT_wait_context.instances:
            waiter.cancelled = True
        package.on_context()

    view = bpy.context.preferences.view
    if UI_SCALE is not None:
        state["original_ui_scale"] = view.ui_scale
        view.ui_scale = float(UI_SCALE)
    if UI_LINE_WIDTH is not None:
        state["original_ui_line_width"] = view.ui_line_width
        view.ui_line_width = UI_LINE_WIDTH.upper()
    print(
        TAG + "_VERSION",
        bpy.app.version_string,
        module.bl_info.get("version"),
        SIDE,
        {"ui_scale": view.ui_scale, "ui_line_width": view.ui_line_width},
        flush=True,
    )
    bpy.app.timers.register(run_step, first_interval=0.5)
except Exception:
    traceback.print_exc()
    finish(False)
