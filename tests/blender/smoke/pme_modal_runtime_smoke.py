import addon_utils
import bpy
import os
from pathlib import Path
import traceback


TAG = "PME_MODAL_RUNTIME_SMOKE"
FIXTURE = Path(
    os.environ.get(
        "PME_MODAL_FIXTURE",
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "pme_modal_fixture.json",
    )
)
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
        if state["step"] == 1:
            if not hasattr(bpy.types.WindowManager, "pme"):
                return 0.1
            result = bpy.ops.wm.pm_import(
                "EXEC_DEFAULT",
                filepath=str(FIXTURE),
                mode="REPLACE",
                tags=TAG,
            )
            state["checks"]["import_finished"] = result == {"FINISHED"}
            area = next(
                area for area in bpy.context.screen.areas if area.type == "VIEW_3D"
            )
            region = next(
                region for region in area.regions if region.type == "WINDOW"
            )
            with bpy.context.temp_override(area=area, region=region):
                invoke_result = bpy.ops.wm.pme_user_pie_menu_call(
                    "INVOKE_DEFAULT",
                    pie_menu_name="PME Modal Smoke",
                    invoke_mode="SUB",
                )
            state["checks"]["outer_call_started"] = invoke_result == {"CANCELLED"}
            state["checks"]["modal_became_active"] = (
                package.operators.PME_OT_modal_base.active is not None
            )
            print(TAG + "_START", invoke_result, flush=True)
            state["step"] = 2
            return 0.35

        overlay = package.overlay.Overlay("VIEW_3D")
        state["checks"]["invoke_command_ran"] = (
            bpy.context.scene.get("pme_modal_invoke") == 1
        )
        state["checks"]["finish_command_ran"] = (
            bpy.context.scene.get("pme_modal_finish") == 1
        )
        state["checks"]["cancel_not_run"] = (
            bpy.context.scene.get("pme_modal_cancel", 0) == 0
        )
        state["checks"]["modal_cleared"] = (
            package.operators.PME_OT_modal_base.active is None
        )
        state["checks"]["overlay_hidden"] = overlay.handler is None
        with bpy.context.temp_override(area=None, region=None):
            no_context_result = bpy.ops.pme.modal(
                "INVOKE_DEFAULT", pm_name="PME Modal Smoke"
            )
        state["checks"]["no_area_cancelled"] = no_context_result == {"CANCELLED"}
        state["checks"]["no_area_left_inactive"] = (
            package.operators.PME_OT_modal_base.active is None
        )
        print(
            TAG + "_END",
            bpy.app.version_string,
            module.bl_info.get("version"),
            bpy.context.scene.get("pme_modal_invoke"),
            bpy.context.scene.get("pme_modal_finish"),
            bpy.context.scene.get("pme_modal_cancel", 0),
            "active=",
            package.operators.PME_OT_modal_base.active,
            "overlay=",
            overlay.handler,
            "no_area=",
            no_context_result,
            flush=True,
        )
        return finish(all(state["checks"].values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


bpy.app.timers.register(run_step, first_interval=0.1)
