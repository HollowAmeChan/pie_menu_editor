import addon_utils
import bpy
import traceback


MENU_NAME = "pme_property_editor_smoke"


def finish(success):
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        menu = prefs.pie_menus.get(MENU_NAME)
        if menu is not None:
            prefs.remove_pm(menu)
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_PROPERTY_EDITOR_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def run():
    try:
        from pie_menu_editor.core import pme
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        old = prefs.pie_menus.get(MENU_NAME)
        if old is not None:
            prefs.remove_pm(old)
        menu = prefs.add_pm(mode="PROPERTY", name=MENU_NAME)
        prefs.active_pie_menu_idx = prefs.pie_menus.find(menu.name)
        menu.poll_cmd = "INT"
        item = menu.pmis.add()
        item.name = "GET"
        item.mode = "COMMAND"
        item.text = "return self.get(menu, 0)"
        pme.context.edit_item_idx = len(menu.pmis) - 1
        menu.ed.register_props(menu)

        before = item.ed_text
        item.ed_text = "return 42"
        after_valid = item.ed_text
        stored_valid = item.text
        item.ed_text = "return ("
        after_invalid = item.ed_text
        stored_invalid = item.text
        set_item = menu.pmis.add()
        set_item.name = "SET"
        set_item.mode = "COMMAND"
        set_item.text = "self[menu] = value"
        item.text = "return self.get(menu, 0)"
        menu.ed.register_props(menu)
        menu.ed.on_pm_add(menu)
        setattr(prefs.props, MENU_NAME, 42)
        dynamic_value = getattr(prefs.props, MENU_NAME)

        checks = {
            "initial_read": before == "return self.get(menu, 0)",
            "valid_read": after_valid == "return 42",
            "valid_storage": stored_valid == "return 42",
            "invalid_read": after_invalid == "return (",
            "invalid_storage": stored_invalid == "return (",
            "invalid_marked": item.icon == "ERROR",
            "dynamic_value": dynamic_value == 42,
        }
        print("PME_PROPERTY_EDITOR_VALUES", {
            "before": before,
            "after_valid": after_valid,
            "stored_valid": stored_valid,
            "after_invalid": after_invalid,
            "stored_invalid": stored_invalid,
            "icon": item.icon,
            "dynamic_value": dynamic_value,
        }, flush=True)
        print("PME_PROPERTY_EDITOR_CHECKS", checks, flush=True)
        finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_PROPERTY_EDITOR_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
