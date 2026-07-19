import addon_utils
import bpy
import traceback


MENU_NAME = "PME Property Remove Storage Smoke"
VALUE = 73


def finish(success, checks=None, details=None):
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        menu = prefs.pie_menus.get(MENU_NAME)
        if menu is not None:
            prefs.remove_pm(menu)
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_PROPERTY_REMOVE_STORAGE_CHECKS", checks or {}, flush=True)
    print("PME_PROPERTY_REMOVE_STORAGE_DETAILS", details or {}, flush=True)
    print(
        "PME_PROPERTY_REMOVE_STORAGE_RESULT",
        "OK" if success else "FAILED",
        flush=True,
    )
    bpy.ops.wm.quit_blender()
    return None


def add_int_property(prefs):
    from pie_menu_editor.core.ed_property import (
        register_user_property,
        unregister_user_property,
    )

    menu = prefs.add_pm(mode="PROPERTY", name=MENU_NAME)
    unregister_user_property(menu)
    menu.poll_cmd = "INT"
    register_user_property(menu)
    return menu


def run():
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        old = prefs.pie_menus.get(MENU_NAME)
        if old is not None:
            prefs.remove_pm(old)

        first = add_int_property(prefs)
        setattr(prefs.props, MENU_NAME, VALUE)
        assigned = getattr(prefs.props, MENU_NAME)
        prefs.remove_pm(first)

        class_property_removed = not hasattr(prefs.props.__class__, MENU_NAME)
        second = add_int_property(prefs)
        recreated = getattr(prefs.props, MENU_NAME)
        setattr(prefs.props, MENU_NAME, VALUE)
        second.set_data("save", False)
        second.ed.init_pm(second)
        reset_value = getattr(prefs.props, MENU_NAME)

        checks = {
            "assigned": assigned == VALUE,
            "class_property_removed": class_property_removed,
            "recreated_at_default": recreated == 0,
            "nonpersistent_value_reset": reset_value == 0,
        }
        details = {
            "blender": bpy.app.version_string,
            "assigned": assigned,
            "recreated": recreated,
            "reset_value": reset_value,
        }
        return finish(all(checks.values()), checks, details)
    except Exception:
        traceback.print_exc()
        return finish(False)


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print(
            "PME_PROPERTY_REMOVE_STORAGE_ENABLE",
            module.__file__ if module else None,
            flush=True,
        )
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
