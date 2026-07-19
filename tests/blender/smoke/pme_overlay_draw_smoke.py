import addon_utils
import bpy
import traceback


errors = []
state = {}


def finish(success):
    print("PME_OVERLAY_DRAW_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def verify():
    try:
        overlay_module = state["module"].core.overlay
        space = overlay_module.space_groups["VIEW_3D"]
        checks = {
            "running_result": state["result"] == {"RUNNING_MODAL"},
            "handler_created": state["handler_created"],
            "redraw_finished": state["redraw_result"] == {"FINISHED"},
            "draw_called": state["draw_calls"] > 0,
            "no_draw_errors": not errors,
            "handler_removed": space.handler is None,
            "operator_stopped": not overlay_module.PME_OT_overlay.is_running,
        }
        print(
            "PME_OVERLAY_DRAW_CHECKS",
            bpy.app.version_string,
            checks,
            "calls=",
            state["draw_calls"],
            "errors=",
            errors,
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
    if not hasattr(bpy.types, "PME_OT_overlay"):
        for waiter in module.core.PME_OT_wait_context.instances:
            waiter.cancelled = True
        module.core.on_context()

    overlay_module = module.core.overlay
    original_draw = overlay_module._draw_handler

    def checked_draw(space):
        state["draw_calls"] += 1
        try:
            original_draw(space)
        except Exception:
            errors.append(traceback.format_exc())

    overlay_module._draw_handler = checked_draw
    state.update(module=module, draw_calls=0)

    window = bpy.context.window_manager.windows[0]
    screen = window.screen
    area = next(item for item in screen.areas if item.type == "VIEW_3D")
    region = next(item for item in area.regions if item.type == "WINDOW")
    with bpy.context.temp_override(
        window=window,
        screen=screen,
        area=area,
        region=region,
    ):
        result = bpy.ops.pme.overlay(
            "EXEC_DEFAULT",
            text="PME Overlay Smoke",
            duration=1.0,
        )
        handler_created = (
            overlay_module.space_groups["VIEW_3D"].handler is not None
        )
        redraw_result = bpy.ops.wm.redraw_timer(
            type="DRAW_WIN_SWAP",
            iterations=2,
        )

    state.update(
        result=result,
        handler_created=handler_created,
        redraw_result=redraw_result,
    )
    bpy.app.timers.register(verify, first_interval=1.5)
except Exception:
    traceback.print_exc()
    finish(False)
