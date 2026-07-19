import addon_utils
import bpy
from pathlib import Path
import traceback


TAG = "PME_AUTOMASKING_SMOKE"
MENU_NAME = "Popup: (Sculpt) Control Alt"
FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "pme_community_51_menus.json"
)
errors = []


def finish(success):
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        for menu in list(prefs.pie_menus):
            if menu.has_tag(TAG):
                prefs.remove_pm(menu)
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_AUTOMASKING_ERRORS", errors, flush=True)
    print("PME_AUTOMASKING_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def draw_menu():
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        menu = prefs.pie_menus[MENU_NAME]
        paths = [
            item.text
            for item in menu.pmis
            if "automasking" in item.text
        ]
        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.object.mode_set(mode="SCULPT")
            settings = bpy.context.scene.tool_settings.sculpt
            if settings.brush is None:
                bpy.ops.brush.asset_activate(
                    asset_library_type="ESSENTIALS",
                    relative_asset_identifier=(
                        "brushes/essentials_brushes-mesh_sculpt.blend/Brush/Draw"
                    ),
                )
            result = bpy.ops.wm.pme_user_pie_menu_call(
                "INVOKE_DEFAULT",
                pie_menu_name=MENU_NAME,
                invoke_mode="SUB",
                keymap="Window",
            )
        expected_fragment = "mesh_automasking_settings(paint_settings().brush)."
        checks = {
            "menu_called": "CANCELLED" in result,
            "four_paths": len(paths) == 4,
            "paths_compatible": all(expected_fragment in path for path in paths),
            "no_draw_errors": not errors,
        }
        print("PME_AUTOMASKING_PATHS", paths, flush=True)
        print("PME_AUTOMASKING_CHECKS", checks, flush=True)
        bpy.app.timers.register(
            lambda: finish(all(checks.values())), first_interval=1.0
        )
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


def import_config():
    try:
        from pie_menu_editor.core import layout_helper, pme

        original_error = layout_helper.lh.error

        def tracked_error(text, message=None):
            errors.append((getattr(pme.context.pmi, "name", ""), message))
            return original_error(text, message)

        layout_helper.lh.error = tracked_error
        result = bpy.ops.wm.pm_import(
            "EXEC_DEFAULT",
            filepath=str(FIXTURE),
            mode="RENAME",
            tags=TAG,
        )
        print("PME_AUTOMASKING_IMPORT", result, flush=True)
        if "FINISHED" not in result:
            return finish(False)
        bpy.app.timers.register(draw_menu, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_AUTOMASKING_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(import_config, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
