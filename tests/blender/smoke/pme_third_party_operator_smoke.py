import addon_utils
import bpy
import traceback


TAG = "PME_THIRD_PARTY_OPERATOR_SMOKE"
MENU_NAME = "PME MACHIN3 Operator Smoke"
state = {}
preferences = None


def finish(success):
    try:
        if bpy.context.mode == "EDIT_MESH":
            bpy.ops.object.mode_set(mode="OBJECT")
        if preferences and MENU_NAME in preferences.pie_menus:
            preferences.remove_pm(preferences.pie_menus[MENU_NAME])
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_STATE", state, flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify():
    try:
        checks = {
            "dependency_enabled": state.get("dependency_enabled") is True,
            "menu_invoked": state.get("menu_result") == {"CANCELLED"},
            "command_ran": state.get("command_ran") == 1,
            "operator_finished": "FINISHED" in state.get("operator_result", ()),
            "mode_changed": bpy.context.mode == "EDIT_MESH",
        }
        state["checks"] = checks
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def run():
    global preferences
    try:
        from pie_menu_editor.core import pme
        from pie_menu_editor.core.addon import get_prefs

        preferences = get_prefs()
        pme.context.add_global("THIRD_PARTY_STATE", state)
        menu = preferences.add_pm(mode="SCRIPT", name=MENU_NAME)
        menu.pmis[0].text = (
            "THIRD_PARTY_STATE['operator_result'] = "
            "tuple(bpy.ops.machin3.edit_mode()); "
            "THIRD_PARTY_STATE['command_ran'] = "
            "THIRD_PARTY_STATE.get('command_ran', 0) + 1"
        )

        area = next(
            candidate
            for candidate in bpy.context.window.screen.areas
            if candidate.type == "VIEW_3D"
        )
        region = next(
            candidate for candidate in area.regions if candidate.type == "WINDOW"
        )
        with bpy.context.temp_override(area=area, region=region):
            state["menu_result"] = bpy.ops.wm.pme_user_pie_menu_call(
                "INVOKE_DEFAULT",
                pie_menu_name=menu.name,
                invoke_mode="SUB",
                keymap="Window",
            )
        bpy.app.timers.register(verify, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        dependency = addon_utils.enable(
            "MACHIN3tools",
            default_set=True,
            persistent=False,
            handle_error=None,
        )
        state["dependency_enabled"] = dependency is not None
        module = addon_utils.enable(
            "pie_menu_editor",
            default_set=True,
            persistent=False,
            handle_error=None,
        )
        print(
            TAG + "_ENABLE",
            getattr(dependency, "__file__", None),
            module.__file__ if module else None,
            flush=True,
        )
        bpy.app.timers.register(run, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
