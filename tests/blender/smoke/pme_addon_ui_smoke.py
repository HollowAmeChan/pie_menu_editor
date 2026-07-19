import addon_utils
import bpy
import traceback


def finish(success):
    print("PME_ADDON_UI_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify():
    try:
        checks = {
            "preferences": "pie_menu_editor" in bpy.context.preferences.addons,
            "pme_operator": hasattr(bpy.types, "PME_OT_popup_addon_preferences"),
            "window_manager_data": hasattr(bpy.types.WindowManager, "pme"),
        }
        print("PME_ADDON_UI_CHECKS", checks, flush=True)
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def open_preferences():
    try:
        result = bpy.ops.pme.popup_addon_preferences(
            "INVOKE_DEFAULT", addon="pie_menu_editor"
        )
        print("PME_ADDON_UI_POPUP_RETURN", result, flush=True)
        bpy.app.timers.register(verify, first_interval=2.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_ADDON_UI_ENABLE_RETURN", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(open_preferences, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
