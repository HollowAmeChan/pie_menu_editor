import addon_utils
import bpy
import traceback


baseline_draw = None
preferences_window = None


def finish(success):
    print("PME_PREFS_MAX_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def verify_restored():
    try:
        from pie_menu_editor.core import ui

        checks = {
            "draw_restored": bpy.types.USERPREF_PT_addons.draw is baseline_draw,
            "state_restored": not ui.is_userpref_maximized(),
        }
        print("PME_PREFS_MAX_RESTORED", checks, flush=True)
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def restore():
    try:
        result = bpy.ops.pme.userpref_restore()
        print("PME_PREFS_MAX_RESTORE", result, flush=True)
        bpy.app.timers.register(verify_restored, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def verify_opened():
    global preferences_window
    try:
        from pie_menu_editor.core import ui

        preferences_window = next(
            window for window in bpy.context.window_manager.windows
            if any(area.type == "PREFERENCES" for area in window.screen.areas)
        )
        checks = {
            "window_opened": preferences_window is not None,
            "draw_replaced": (
                bpy.types.USERPREF_PT_addons.draw is ui.draw_addons_maximized
            ),
            "state_maximized": ui.is_userpref_maximized(),
            "active_section": bpy.context.preferences.active_section == "ADDONS",
        }
        print("PME_PREFS_MAX_OPENED", checks, flush=True)
        if not all(checks.values()):
            return finish(False)
        bpy.app.timers.register(restore, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def open_preferences():
    try:
        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            result = bpy.ops.pme.userpref_show(addon="pie_menu_editor")
        print("PME_PREFS_MAX_OPEN", result, flush=True)
        bpy.app.timers.register(verify_opened, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    global baseline_draw
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        baseline_draw = bpy.types.USERPREF_PT_addons.draw
        print("PME_PREFS_MAX_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(open_preferences, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
