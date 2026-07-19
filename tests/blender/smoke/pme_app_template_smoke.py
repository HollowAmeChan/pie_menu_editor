import addon_utils
import bpy
from bpy.app.handlers import persistent
import traceback


MENU_NAME = "PME App Template Smoke"
TARGET_TEMPLATE = "Sculpting"


def finish(success):
    print("PME_APP_TEMPLATE_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def verify():
    try:
        from pie_menu_editor.core.addon import get_prefs
        from pie_menu_editor.core import previews_helper

        prefs = get_prefs()
        menu = prefs.pie_menus.get(MENU_NAME)
        checks = {
            "addon_enabled": "pie_menu_editor" in bpy.context.preferences.addons,
            "preferences": prefs is not None,
            "menu_preserved": menu is not None,
            "menu_item_preserved": menu is not None
            and menu.pmis[0].text == "bpy.ops.wm.redraw_timer(iterations=1)",
            "preview_alive": previews_helper.ph.preview is not None,
            "load_pre_once": sum(
                handler.__name__ == "load_pre_handler"
                for handler in bpy.app.handlers.load_pre
            )
            == 1,
            "load_post_once": sum(
                handler.__name__ == "load_post_handler"
                for handler in bpy.app.handlers.load_post
            )
            == 1,
        }
        print("PME_APP_TEMPLATE_CHECKS", checks, flush=True)
        if menu is not None:
            prefs.remove_pm(menu)
        finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


@persistent
def after_load(_):
    try:
        bpy.app.handlers.load_post.remove(after_load)
    except ValueError:
        pass
    bpy.app.timers.register(verify, first_interval=1.0)


def switch_template():
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        old = prefs.pie_menus.get(MENU_NAME)
        if old is not None:
            prefs.remove_pm(old)
        menu = prefs.add_pm(mode="DIALOG", name=MENU_NAME)
        menu.pmis[0].name = "Template Marker"
        menu.pmis[0].mode = "COMMAND"
        menu.pmis[0].text = "bpy.ops.wm.redraw_timer(iterations=1)"
        bpy.app.handlers.load_post.append(after_load)
        result = bpy.ops.wm.read_homefile(app_template=TARGET_TEMPLATE)
        print("PME_APP_TEMPLATE_SWITCH", result, flush=True)
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_APP_TEMPLATE_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(switch_template, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
