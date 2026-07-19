import addon_utils
import bpy
import traceback


def finish(success):
    print("PME_LIFECYCLE_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify_reenabled():
    try:
        from pie_menu_editor.core import load_post_handler, load_pre_handler

        checks = {
            "preferences": "pie_menu_editor" in bpy.context.preferences.addons,
            "window_manager_data": hasattr(bpy.types.WindowManager, "pme"),
            "menu_operator": hasattr(bpy.types, "WM_OT_pme_user_pie_menu_call"),
            "single_load_pre": bpy.app.handlers.load_pre.count(load_pre_handler) == 1,
            "single_load_post": bpy.app.handlers.load_post.count(load_post_handler) == 1,
        }
        print("PME_LIFECYCLE_REENABLE_CHECKS", checks, flush=True)
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def reenable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_LIFECYCLE_REENABLE_RETURN", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(verify_reenabled, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def disable():
    try:
        addon_utils.disable("pie_menu_editor", default_set=True, handle_error=None)
        checks = {
            "preferences_removed": "pie_menu_editor"
            not in bpy.context.preferences.addons,
            "window_manager_data_removed": not hasattr(bpy.types.WindowManager, "pme"),
            "menu_operator_removed": not hasattr(
                bpy.types, "WM_OT_pme_user_pie_menu_call"
            ),
        }
        print("PME_LIFECYCLE_DISABLE_CHECKS", checks, flush=True)
        if not all(checks.values()):
            return finish(False)
        bpy.app.timers.register(reenable, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_LIFECYCLE_ENABLE_RETURN", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(disable, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
