import addon_utils
import bpy
import traceback


TAG = "PME_OVERLAY_DISABLE_SMOKE"
state = {"step": 0, "checks": {}}


def finish(success):
    print(TAG + "_CHECKS", state["checks"], flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def run_step():
    try:
        if state["step"] == 0:
            module = addon_utils.enable(
                "pie_menu_editor",
                default_set=True,
                persistent=False,
                handle_error=None,
            )
            state["module"] = module
            state["step"] = 1
            return 0.25

        module = state["module"]
        package = module.core
        overlay = package.overlay
        if state["step"] == 1:
            if not hasattr(bpy.types.WindowManager, "pme"):
                return 0.1
            area = next(
                area for area in bpy.context.screen.areas if area.type == "VIEW_3D"
            )
            region = next(
                region for region in area.regions if region.type == "WINDOW"
            )
            with bpy.context.temp_override(area=area, region=region):
                result = bpy.ops.pme.overlay(
                    "INVOKE_DEFAULT",
                    text="PME Overlay Disable Smoke",
                    duration=10.0,
                )
            space = overlay.space_groups["VIEW_3D"]
            state["space"] = space
            state["checks"]["overlay_started"] = (
                result == {"RUNNING_MODAL"} and space.handler is not None
            )
            addon_utils.disable(
                "pie_menu_editor", default_set=True, handle_error=None
            )
            state["step"] = 2
            return 0.35

        space = state["space"]
        leaked_classes = sorted(
            cls.__name__
            for cls in list(package.get_classes())
            + [package.PME_OT_wait_context, package.PME_OT_wait_keymaps]
            if getattr(bpy.types, cls.__name__, None) is cls
        )
        state["checks"]["addon_disabled"] = addon_utils.check(
            "pie_menu_editor"
        ) == (False, False)
        state["checks"]["handler_removed"] = space.handler is None
        state["checks"]["running_flag_cleared"] = not overlay.PME_OT_overlay.is_running
        state["checks"]["active_instance_cleared"] = (
            overlay.PME_OT_overlay.active_instance is None
        )
        state["checks"]["no_registered_classes"] = not leaked_classes
        print(
            TAG + "_DATA",
            bpy.app.version_string,
            module.bl_info.get("version"),
            "handler=",
            space.handler,
            "running=",
            overlay.PME_OT_overlay.is_running,
            "instance=",
            overlay.PME_OT_overlay.active_instance,
            "classes=",
            leaked_classes,
            flush=True,
        )
        return finish(all(state["checks"].values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


bpy.app.timers.register(run_step, first_interval=0.1)
