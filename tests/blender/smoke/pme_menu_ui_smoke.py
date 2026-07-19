import addon_utils
import bpy
import traceback


menu_name = None
original_restore_mouse_pos = None


def finish(success):
    global menu_name
    try:
        from pie_menu_editor.core.addon import get_prefs
        from pie_menu_editor.core.ui_utils import pme_menu_classes

        preferences = get_prefs()
        if menu_name and menu_name in preferences.pie_menus:
            preferences.remove_pm(preferences.pie_menus[menu_name])
        if original_restore_mouse_pos is not None:
            preferences.restore_mouse_pos = original_restore_mouse_pos
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_MENU_UI_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify():
    try:
        from pie_menu_editor.core.addon import get_prefs

        preferences = get_prefs()
        checks = {
            "menu_exists": menu_name in preferences.pie_menus,
            "draw_callback": bool(bpy.context.scene.get("pme_smoke_drawn")),
            "call_operator": hasattr(bpy.types, "WM_OT_pme_user_pie_menu_call"),
        }
        print("PME_MENU_UI_CHECKS", checks, flush=True)
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def open_menu():
    global menu_name, original_restore_mouse_pos
    try:
        from pie_menu_editor.core.addon import get_prefs

        preferences = get_prefs()
        original_restore_mouse_pos = preferences.restore_mouse_pos
        preferences.restore_mouse_pos = False
        pie_menu = preferences.add_pm(mode="PMENU", name="UI Smoke Pie")
        menu_name = pie_menu.name
        item = pie_menu.pmis[0]
        item.name = "Redraw"
        item.mode = "COMMAND"
        item.text = "bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)"
        marker = pie_menu.pmis[1]
        marker.name = "Marker"
        marker.mode = "CUSTOM"
        marker.text = "D.scenes[0]['pme_smoke_drawn'] = True"
        result = bpy.ops.wm.pme_user_pie_menu_call(
            "INVOKE_DEFAULT",
            pie_menu_name=pie_menu.name,
            invoke_mode="SUB",
            keymap="Window",
        )
        print("PME_MENU_UI_CALL_RETURN", result, flush=True)
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
        print("PME_MENU_UI_ENABLE_RETURN", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(open_menu, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
