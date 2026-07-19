import addon_utils
import bpy
from pathlib import Path
import traceback


TAG = "PME_COMMUNITY_51_SMOKE"
FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "pme_community_51_menus.json"
)
preferences = None
errors = []
menu_names = []


def tagged_names():
    return [pm.name for pm in preferences.pie_menus if pm.has_tag(TAG)]


def finish(success):
    try:
        for name in reversed(tagged_names()):
            if name in preferences.pie_menus:
                preferences.remove_pm(preferences.pie_menus[name])
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_COMMUNITY_ERRORS", errors, flush=True)
    print("PME_COMMUNITY_CONFIG_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def draw_object_menu():
    try:
        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            if bpy.context.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            result = bpy.ops.wm.pme_user_pie_menu_call(
                "INVOKE_DEFAULT",
                pie_menu_name="Pie: (Object Mode): Edit Mode Tools",
                invoke_mode="SUB",
                keymap="Window",
            )
        print("PME_COMMUNITY_OBJECT_CALL", result, flush=True)
        checks = {
            "menus_imported": len(menu_names) == 40,
            "edit_menu": "Pie: (Edit Mode) Selection" in preferences.pie_menus,
            "object_menu": (
                "Pie: (Object Mode): Edit Mode Tools" in preferences.pie_menus
            ),
            "old_operator_removed": not any(
                "bpy.ops.mesh.loop_multi_select" in item.text
                for name in menu_names
                for item in preferences.pie_menus[name].pmis
            ),
            "compat_command_present": any(
                "mesh_loop_multi_select" in item.text
                for name in menu_names
                for item in preferences.pie_menus[name].pmis
            ),
            "object_menu_drawn": "CANCELLED" in result,
        }
        print("PME_COMMUNITY_CHECKS", checks, flush=True)
        bpy.app.timers.register(
            lambda: finish(all(checks.values())), first_interval=1.0
        )
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def draw_edit_menu():
    try:
        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.context.scene.tool_settings.mesh_select_mode = (False, True, False)
            result = bpy.ops.wm.pme_user_pie_menu_call(
                "INVOKE_DEFAULT",
                pie_menu_name="Pie: (Edit Mode) Selection",
                invoke_mode="SUB",
                keymap="Window",
            )
        print("PME_COMMUNITY_EDIT_CALL", result, flush=True)
        if "CANCELLED" not in result:
            return finish(False)
        bpy.app.timers.register(draw_object_menu, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def import_config():
    global preferences, menu_names
    try:
        from pie_menu_editor.core import layout_helper, pme
        from pie_menu_editor.core.addon import get_prefs

        preferences = get_prefs()
        original_error = layout_helper.lh.error

        def tracked_error(text, message=None):
            errors.append(
                (
                    getattr(pme.context.pmi, "name", ""),
                    message or "draw exception",
                )
            )
            return original_error(text, message)

        layout_helper.lh.error = tracked_error
        result = bpy.ops.wm.pm_import(
            "EXEC_DEFAULT",
            filepath=str(FIXTURE),
            mode="RENAME",
            tags=TAG,
        )
        menu_names = tagged_names()
        print("PME_COMMUNITY_IMPORT", result, len(menu_names), flush=True)
        if "FINISHED" not in result:
            return finish(False)
        bpy.app.timers.register(draw_edit_menu, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_COMMUNITY_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(import_config, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
