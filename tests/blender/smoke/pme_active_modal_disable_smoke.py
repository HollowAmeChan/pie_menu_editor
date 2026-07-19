import addon_utils
import bpy
import os
from pathlib import Path
import traceback


TAG = "PME_ACTIVE_MODAL_DISABLE_SMOKE"
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
            prefs = package.addon.get_prefs()
            pm = next(pm for pm in prefs.pie_menus if pm.has_tag(TAG))
            pm.pmis[0].text = (
                "C.scene['pme_modal_invoke'] = "
                "C.scene.get('pme_modal_invoke', 0) + 1"
            )
            area = next(
                area for area in bpy.context.screen.areas if area.type == "VIEW_3D"
            )
            region = next(
                region for region in area.regions if region.type == "WINDOW"
            )
            with bpy.context.temp_override(area=area, region=region):
                invoke_result = bpy.ops.wm.pme_user_pie_menu_call(
                    "INVOKE_DEFAULT",
                    pie_menu_name=pm.name,
                    invoke_mode="SUB",
                )
            state["checks"]["import_finished"] = result == {"FINISHED"}
            state["checks"]["outer_call_started"] = invoke_result == {"CANCELLED"}
            state["step"] = 2
            return 0.25

        if state["step"] == 2:
            active = package.operators.PME_OT_modal_base.active
            state["active"] = active
            state["modal_overlay"] = active.overlay if active is not None else None
            state["checks"]["modal_active_before_disable"] = active is not None
            state["checks"]["overlay_visible_before_disable"] = (
                active is not None and active.overlay.handler is not None
            )
            addon_utils.disable(
                "pie_menu_editor", default_set=True, handle_error=None
            )
            state["step"] = 3
            return 0.35

        modal_overlay = state["modal_overlay"]
        leaked_classes = sorted(
            cls.__name__
            for cls in list(package.get_classes())
            + [package.PME_OT_wait_context, package.PME_OT_wait_keymaps]
            if getattr(bpy.types, cls.__name__, None) is cls
        )
        state["checks"]["addon_disabled"] = addon_utils.check(
            "pie_menu_editor"
        ) == (False, False)
        state["checks"]["modal_cleared"] = (
            package.operators.PME_OT_modal_base.active is None
        )
        state["checks"]["overlay_hidden"] = modal_overlay.handler is None
        state["checks"]["no_registered_classes"] = not leaked_classes
        print(
            TAG + "_DATA",
            bpy.app.version_string,
            module.bl_info.get("version"),
            "active=",
            package.operators.PME_OT_modal_base.active is None,
            "handler=",
            modal_overlay.handler,
            "classes=",
            leaked_classes,
            flush=True,
        )
        return finish(all(state["checks"].values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


bpy.app.timers.register(run_step, first_interval=0.1)
