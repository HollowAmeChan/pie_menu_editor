import addon_utils
import bpy
import traceback


TAG = "PME_SIDEAREA_DISABLE_SMOKE"
state = {"checks": {}}
module = None
extra_operators = None


def finish(success):
    print(TAG + "_CHECKS", state["checks"], flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify_reenabled():
    try:
        checks = state["checks"]
        checks["reenabled"] = addon_utils.check("pie_menu_editor")[1]
        checks["operator_restored"] = hasattr(
            bpy.types, "PME_OT_sidearea_toggle"
        )
        checks["timer_set_still_empty"] = not extra_operators._side_area_rebuild_timers
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def reenable():
    try:
        enabled = addon_utils.enable(
            "pie_menu_editor",
            default_set=True,
            persistent=False,
            handle_error=None,
        )
        if not hasattr(bpy.types.WindowManager, "pme"):
            for waiter in enabled.core.PME_OT_wait_context.instances:
                waiter.cancelled = True
            enabled.core.on_context()
        bpy.app.timers.register(verify_reenabled, first_interval=0.1)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def trigger_and_disable():
    global extra_operators
    try:
        context = bpy.context
        screen = context.window.screen
        area_count = len(screen.areas)
        main = next(area for area in screen.areas if area.ui_type == "VIEW_3D")
        bottom = next(area for area in screen.areas if area.ui_type == "TIMELINE")
        region = next(
            item for item in main.regions if item.type == "WINDOW"
        )
        with context.temp_override(area=main, region=region):
            result = bpy.ops.pme.sidearea_toggle(
                "EXEC_DEFAULT",
                action="SHOW",
                area="PROPERTIES",
                side="BOTTOM",
                main_area="VIEW_3D",
                width=300,
            )
        extra_operators = module.core.extra_operators
        callbacks = tuple(extra_operators._side_area_rebuild_timers)
        state["checks"].update(
            show_finished=result == {"FINISHED"},
            adjacent_area_was_joined=(
                len(screen.areas) == area_count - 1
                and not any(
                    area.ui_type == "TIMELINE" for area in screen.areas
                )
            ),
            rebuild_timer_pending=len(callbacks) == 1,
            rebuild_timer_registered=(
                len(callbacks) == 1
                and bpy.app.timers.is_registered(callbacks[0])
            ),
        )
        addon_utils.disable(
            "pie_menu_editor",
            default_set=False,
            handle_error=None,
        )
        state["checks"].update(
            disabled=not addon_utils.check("pie_menu_editor")[1],
            timer_set_cleared=not extra_operators._side_area_rebuild_timers,
            callbacks_unregistered=all(
                not bpy.app.timers.is_registered(callback)
                for callback in callbacks
            ),
        )
        bpy.app.timers.register(reenable, first_interval=0.1)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    global module
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
        bpy.app.timers.register(trigger_and_disable, first_interval=0.1)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.1)
