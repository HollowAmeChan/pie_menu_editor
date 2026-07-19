import addon_utils
import bpy
import traceback


TAG = "PME_SIDEAREA_TOGGLE_SMOKE"
state = {"step": 0, "success": False, "checks": {}, "before": None}


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
            with context.temp_override(area=main):
                result = bpy.ops.pme.sidearea_toggle(
                    "EXEC_DEFAULT",
                    action="SHOW",
                    area="PROPERTIES",
                    side="RIGHT",
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
            side = next((area for area in screen.areas if area.ui_type == "PROPERTIES"), None)
            state["checks"]["show_added_one_area"] = (
                len(shown) == len(state["before"]) + 1
            )
            state["checks"]["show_types_correct"] = main is not None and side is not None
            state["checks"]["show_width_reasonable"] = (
                side is not None and 32 <= side.width <= context.window.width // 2 + 4
            )
            print(TAG + "_SHOWN", shown, flush=True)
            if main is None or side is None:
                return finish(False)

            with context.temp_override(area=main):
                result = bpy.ops.pme.sidearea_toggle(
                    "EXEC_DEFAULT",
                    action="HIDE",
                    area="PROPERTIES",
                    side="RIGHT",
                    main_area="VIEW_3D",
                    width=300,
                )
            state["checks"]["hide_finished"] = result == {"FINISHED"}
            print(TAG + "_HIDE_REQUEST", result, flush=True)
            state["step"] = 2
            return 0.35

        hidden = area_snapshot(screen)
        state["checks"]["hide_restored_area_count"] = (
            len(hidden) == len(state["before"])
        )
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
    print(TAG + "_VERSION", bpy.app.version_string, module.bl_info.get("version"), flush=True)
    bpy.app.timers.register(run_step, first_interval=0.1)
except Exception:
    traceback.print_exc()
    finish(False)
