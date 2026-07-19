import addon_utils
import bpy
import traceback


TAG = "PME_OVERLAY_RUNTIME_SMOKE"
state = {"step": 0, "checks": {}}


def finish(success):
    print(TAG + "_CHECKS", state["checks"], flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def run_step():
    try:
        module = state["module"]
        overlay = module.core.overlay
        space = overlay.space_groups["VIEW_3D"]
        if state["step"] == 0:
            area = next(area for area in bpy.context.screen.areas if area.type == "VIEW_3D")
            region = next(region for region in area.regions if region.type == "WINDOW")
            with bpy.context.temp_override(area=area, region=region):
                result = bpy.ops.pme.overlay(
                    "INVOKE_DEFAULT",
                    text="PME Overlay Smoke",
                    duration=1.0,
                )
            state["checks"]["invoke_running"] = result == {"RUNNING_MODAL"}
            state["checks"]["handler_installed"] = space.handler is not None
            state["checks"]["running_flag_set"] = overlay.PME_OT_overlay.is_running
            print(TAG + "_START", result, space.handler is not None, flush=True)
            state["step"] = 1
            return 1.4

        state["checks"]["handler_removed"] = space.handler is None
        state["checks"]["running_flag_cleared"] = not overlay.PME_OT_overlay.is_running
        print(
            TAG + "_END",
            bpy.app.version_string,
            module.bl_info.get("version"),
            space.handler,
            overlay.PME_OT_overlay.is_running,
            flush=True,
        )
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
    state["module"] = module
    bpy.app.timers.register(run_step, first_interval=0.1)
except Exception:
    traceback.print_exc()
    finish(False)
