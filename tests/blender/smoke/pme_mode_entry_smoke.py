import addon_utils
import bpy
import os
from pathlib import Path
import traceback


TAG = "PME_MODE_ENTRY_SMOKE"
FIXTURE = Path(os.environ["PME_MODE_FIXTURE"])
state = {"step": 0, "checks": {}, "success": False}


def close_popups():
    bpy.context.window.screen = bpy.context.window.screen


def finish(success):
    state["success"] = success
    print(TAG + "_CHECKS", state["checks"], flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def invoke_menu(name):
    return bpy.ops.wm.pme_user_pie_menu_call(
        "INVOKE_DEFAULT",
        pie_menu_name=name,
        invoke_mode="SUB",
    )


def run_step():
    try:
        if state["step"] == 0:
            script_result = invoke_menu("PME Smoke Script")
            macro_result = invoke_menu("PME Smoke Macro")
            state["checks"]["script_invoked"] = script_result == {"CANCELLED"}
            state["checks"]["script_executed"] = (
                bpy.context.scene.get("pme_script_smoke") == 1
            )
            state["checks"]["macro_invoked"] = macro_result == {"CANCELLED"}
            state["step"] = 1
            return 0.2

        if state["step"] == 1:
            state["checks"]["macro_executed"] = (
                bpy.context.scene.get("pme_macro_smoke") == 1
            )
            pie_result = invoke_menu("PME Smoke Pie")
            state["checks"]["pie_invoked"] = pie_result == {"CANCELLED"}
            print(TAG + "_PIE_RESULT", pie_result, flush=True)
            state["step"] = 2
            return 0.2

        if state["step"] == 2:
            close_popups()
            dialog_result = invoke_menu("PME Smoke Dialog")
            state["checks"]["dialog_invoked"] = dialog_result in (
                {"CANCELLED"},
                {"RUNNING_MODAL"},
            )
            print(TAG + "_DIALOG_RESULT", dialog_result, flush=True)
            state["step"] = 3
            return 0.2

        close_popups()
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

    result = bpy.ops.wm.pm_import(
        "EXEC_DEFAULT",
        filepath=str(FIXTURE),
        mode="REPLACE",
        tags=TAG,
    )
    prefs = package.addon.get_prefs()
    imported = [pm for pm in prefs.pie_menus if pm.has_tag(TAG)]
    modes = {pm.name: pm.mode for pm in imported}
    expected_modes = {"PMENU", "DIALOG", "SCRIPT", "MACRO", "PROPERTY", "HPANEL"}
    state["checks"]["import_finished"] = result == {"FINISHED"}
    state["checks"]["all_modes_imported"] = (
        len(imported) == 6 and set(modes.values()) == expected_modes
    )
    prop_name = "PME Smoke Property"
    initial = getattr(prefs.props, prop_name)
    setattr(prefs.props, prop_name, True)
    state["checks"]["property_initial"] = initial is False
    state["checks"]["property_set"] = (
        getattr(prefs.props, prop_name) is True
        and bpy.context.scene.get("pme_property_smoke") is True
    )
    state["checks"]["hpanel_registered"] = modes.get(
        "PME Smoke Hidden Panels"
    ) == "HPANEL"
    print(
        TAG + "_VERSION",
        bpy.app.version_string,
        module.bl_info.get("version"),
        modes,
        flush=True,
    )
    bpy.app.timers.register(run_step, first_interval=0.1)
except Exception:
    traceback.print_exc()
    finish(False)
