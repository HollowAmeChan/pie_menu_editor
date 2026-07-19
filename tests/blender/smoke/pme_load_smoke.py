import addon_utils
import bpy
from bpy.app.handlers import persistent
from pathlib import Path
import tempfile
import traceback


target = Path(tempfile.gettempdir()) / (
    "pme-load-smoke-%d.%d.blend" % bpy.app.version[:2]
)
menu_name = None


def finish(success):
    print("PME_LOAD_RESULT", "OK" if success else "FAILED", flush=True)
    try:
        target.unlink(missing_ok=True)
    except Exception:
        traceback.print_exc()
    bpy.ops.wm.quit_blender()
    return None


def verify_loaded():
    try:
        from pie_menu_editor.core.addon import get_prefs

        preferences = get_prefs()
        menu = preferences.pie_menus.get(menu_name)
        checks = {
            "preferences": "pie_menu_editor" in bpy.context.preferences.addons,
            "menu_preserved": menu is not None,
            "pmi_count": menu is not None and len(menu.pmis) == 10,
            "pmi_name": menu is not None and menu.pmis[0].name == "Load Marker",
            "pmi_text": menu is not None
            and menu.pmis[0].text == "bpy.ops.wm.redraw_timer(iterations=1)",
        }
        print("PME_LOAD_CHECKS", checks, flush=True)
        if menu is not None:
            preferences.remove_pm(menu)
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


@persistent
def after_load(_):
    if Path(bpy.data.filepath) == target:
        bpy.app.timers.register(verify_loaded, first_interval=0.5)


def save_and_load():
    global menu_name
    try:
        from pie_menu_editor.core.addon import get_prefs

        preferences = get_prefs()
        menu = preferences.add_pm(mode="PMENU", name="Load Smoke")
        menu_name = menu.name
        menu.pmis[0].name = "Load Marker"
        menu.pmis[0].mode = "COMMAND"
        menu.pmis[0].text = "bpy.ops.wm.redraw_timer(iterations=1)"
        bpy.app.handlers.load_post.append(after_load)
        bpy.ops.wm.save_as_mainfile(filepath=str(target), check_existing=False)
        bpy.ops.wm.open_mainfile(filepath=str(target))
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_LOAD_ENABLE_RETURN", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(save_and_load, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
