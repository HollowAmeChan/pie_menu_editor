import addon_utils
import bpy
import traceback


preferences = None
menus = {}
state = {}


def finish(success):
    try:
        for name in reversed(list(menus.values())):
            if name in preferences.pie_menus:
                preferences.remove_pm(preferences.pie_menus[name])
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_MODES_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def call_menu(menu):
    return bpy.ops.wm.pme_user_pie_menu_call(
        "INVOKE_DEFAULT",
        pie_menu_name=menu.name,
        invoke_mode="SUB",
        keymap="Window",
    )


def verify_macro():
    marker = bool(state.get("macro"))
    print("PME_MODE_MACRO_CHECK", marker, flush=True)
    return finish(marker)


def run_macro():
    try:
        menu = preferences.pie_menus[menus["MACRO"]]
        result = call_menu(menu)
        print("PME_MODE_MACRO_RETURN", result, flush=True)
        bpy.app.timers.register(verify_macro, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def verify_script():
    marker = bool(state.get("script"))
    print("PME_MODE_SCRIPT_CHECK", marker, flush=True)
    if not marker:
        return finish(False)
    bpy.app.timers.register(run_macro, first_interval=0.5)
    return None


def run_script():
    try:
        menu = preferences.pie_menus[menus["SCRIPT"]]
        result = call_menu(menu)
        print("PME_MODE_SCRIPT_RETURN", result, flush=True)
        bpy.app.timers.register(verify_script, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def verify_dialog():
    marker = bool(state.get("dialog"))
    print("PME_MODE_DIALOG_CHECK", marker, flush=True)
    if not marker:
        return finish(False)
    bpy.app.timers.register(run_script, first_interval=0.5)
    return None


def open_dialog():
    try:
        menu = preferences.pie_menus[menus["DIALOG"]]
        result = call_menu(menu)
        print("PME_MODE_DIALOG_RETURN", result, flush=True)
        bpy.app.timers.register(verify_dialog, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def verify_rmenu():
    marker = bool(state.get("rmenu"))
    print("PME_MODE_RMENU_CHECK", marker, state, id(state), flush=True)
    if not marker:
        return finish(False)
    bpy.app.timers.register(open_dialog, first_interval=0.5)
    return None


def create_and_open_modes():
    global preferences
    try:
        from pie_menu_editor.core import macro_utils, pme
        from pie_menu_editor.core.addon import get_prefs

        preferences = get_prefs()
        pme.context.add_global("SMOKE_STATE", state)
        print(
            "PME_MODE_STATE_IDS",
            id(state),
            id(pme.context.SMOKE_STATE),
            flush=True,
        )

        rmenu = preferences.add_pm(mode="RMENU", name="RMENU Smoke")
        rmenu.pmis[0].name = "Marker"
        rmenu.pmis[0].mode = "CUSTOM"
        rmenu.pmis[0].text = (
            "SMOKE_STATE['rmenu'] = True; "
            "print('PME_RMENU_CUSTOM_EXEC', id(SMOKE_STATE), flush=True)"
        )
        menus["RMENU"] = rmenu.name

        dialog = preferences.add_pm(mode="DIALOG", name="DIALOG Smoke")
        marker = dialog.pmis.add()
        marker.name = "Marker"
        marker.mode = "CUSTOM"
        marker.text = "SMOKE_STATE['dialog'] = True"
        menus["DIALOG"] = dialog.name

        script = preferences.add_pm(mode="SCRIPT", name="SCRIPT Smoke")
        script.pmis[0].text = "SMOKE_STATE['script'] = True"
        menus["SCRIPT"] = script.name

        macro = preferences.add_pm(mode="MACRO", name="MACRO Smoke")
        macro.pmis[0].text = "SMOKE_STATE['macro'] = True"
        macro_utils.update_macro(macro)
        menus["MACRO"] = macro.name

        result = call_menu(preferences.pie_menus[menus["RMENU"]])
        print("PME_MODE_RMENU_RETURN", result, flush=True)
        bpy.app.timers.register(verify_rmenu, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_MODES_ENABLE_RETURN", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(create_and_open_modes, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
