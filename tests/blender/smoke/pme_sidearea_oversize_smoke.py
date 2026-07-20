import addon_utils
import bpy
import os
import traceback


TAG = "PME_SIDEAREA_OVERSIZE_SMOKE"
SIDE = os.environ.get("PME_SIDE", "LEFT").upper()
REQUESTED_SIZE = 2000
state = {"step": 0, "checks": {}, "before": None}


def snapshot(screen):
    return sorted(
        (area.ui_type, area.x, area.y, area.width, area.height)
        for area in screen.areas
    )


def find_main_and_side(screen):
    main = next(
        (area for area in screen.areas if area.ui_type == "VIEW_3D"),
        None,
    )
    if main is None:
        return None, None
    side = None
    for area in screen.areas:
        if area.ui_type != "ASSETS":
            continue
        if SIDE == "LEFT":
            matches = (
                abs(area.y - main.y) <= 5
                and abs(area.height - main.height) <= 5
                and 0 < main.x - (area.x + area.width) < 12
            )
        else:
            matches = (
                abs(area.x - main.x) <= 5
                and abs(area.width - main.width) <= 5
                and 0 < area.y - (main.y + main.height) < 12
            )
        if matches:
            side = area
            break
    return main, side


def area_size(area):
    return area.width if SIDE == "LEFT" else area.height


def call_show(context, main):
    region = next(
        item for item in main.regions if item.type == "WINDOW"
    )
    with context.temp_override(area=main, region=region):
        return bpy.ops.pme.sidearea_toggle(
            "EXEC_DEFAULT",
            action="SHOW",
            area="ASSETS",
            side=SIDE,
            main_area="VIEW_3D",
            width=REQUESTED_SIZE,
        )


def finish(success):
    print(TAG + "_CHECKS", state["checks"], flush=True)
    print(TAG + "_SIZES", state.get("sizes"), flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def run_step():
    try:
        context = bpy.context
        screen = context.window.screen
        if state["step"] == 0:
            state["before"] = snapshot(screen)
            main = next(
                area for area in screen.areas if area.ui_type == "VIEW_3D"
            )
            result = call_show(context, main)
            state["checks"]["first_show_finished"] = result == {"FINISHED"}
            state["step"] = 1
            return 0.35

        if state["step"] == 1:
            main, side = find_main_and_side(screen)
            if main is None or side is None:
                return finish(False)
            first_size = area_size(side)
            total_size = (
                main.width + side.width
                if SIDE == "LEFT"
                else main.height + side.height
            )
            state["first_size"] = first_size
            state["sizes"] = {"total": total_size, "first": first_size}
            state["checks"].update(
                first_added_one_area=(
                    len(screen.areas) == len(state["before"]) + 1
                ),
                first_clamped_near_half=(
                    first_size >= total_size * 0.45
                    and first_size <= total_size * 0.5 + 12
                ),
            )
            side.ui_type = "GeometryNodeTree"
            result = call_show(context, main)
            state["checks"]["second_show_finished"] = result == {"FINISHED"}
            state["step"] = 2
            return 0.35

        if state["step"] == 2:
            main, side = find_main_and_side(screen)
            if main is None or side is None:
                return finish(False)
            second_size = area_size(side)
            state["sizes"]["second"] = second_size
            state["checks"].update(
                second_area_count_stable=(
                    len(screen.areas) == len(state["before"]) + 1
                ),
                second_editor_restored=side.ui_type == "ASSETS",
                replacement_size_stable=(
                    abs(second_size - state["first_size"]) <= 12
                ),
            )
            region = next(
                item for item in main.regions if item.type == "WINDOW"
            )
            with context.temp_override(area=main, region=region):
                result = bpy.ops.pme.sidearea_toggle(
                    "EXEC_DEFAULT",
                    action="HIDE",
                    area="ASSETS",
                    side=SIDE,
                    main_area="VIEW_3D",
                    width=REQUESTED_SIZE,
                )
            state["checks"]["hide_finished"] = result == {"FINISHED"}
            state["step"] = 3
            return 0.35

        hidden = snapshot(screen)
        state["checks"]["layout_restored"] = hidden == state["before"]
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
    if not hasattr(bpy.types.WindowManager, "pme"):
        for waiter in module.core.PME_OT_wait_context.instances:
            waiter.cancelled = True
        module.core.on_context()
    bpy.app.timers.register(run_step, first_interval=0.1)
except Exception:
    traceback.print_exc()
    finish(False)
