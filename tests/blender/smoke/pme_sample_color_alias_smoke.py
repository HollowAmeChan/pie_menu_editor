import addon_utils
import bpy
import traceback


menu_name = None


def finish(success):
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        if menu_name and menu_name in prefs.pie_menus:
            prefs.remove_pm(prefs.pie_menus[menu_name])
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_SAMPLE_ALIAS_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def run():
    global menu_name
    try:
        from pie_menu_editor.core import compatibility_fixes, pme
        from pie_menu_editor.core.addon import get_prefs
        from pie_menu_editor.core.bl_utils import sculpt_sample_color

        prefs = get_prefs()
        menu = prefs.add_pm(mode="DIALOG", name="PME Sample Color Alias Smoke")
        menu_name = menu.name
        item = menu.pmis.add()
        item.name = "Sample Sculpt Color"
        item.mode = "COMMAND"
        item.text = "bpy.ops.sculpt.sample_color()"
        compatibility_fixes.fix_1_19_8(prefs, menu)

        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.object.mode_set(mode="SCULPT")
            bpy.ops.brush.asset_activate(
                asset_library_type="ESSENTIALS",
                relative_asset_identifier=(
                    "brushes/essentials_brushes-mesh_sculpt.blend/Brush/Paint Hard"
                ),
            )
            if bpy.app.version >= (5, 0, 0):
                helper_result = sculpt_sample_color(
                    location=(area.width // 2, area.height // 2)
                )
            else:
                helper_result = sculpt_sample_color()
            command_result = pme.context.exe(item.text, use_try=False)
            menu_result = bpy.ops.wm.pme_user_pie_menu_call(
                "INVOKE_DEFAULT",
                pie_menu_name=menu.name,
                invoke_mode="SUB",
                keymap="Window",
            )

        checks = {
            "migration": item.text == "sculpt_sample_color()",
            "helper_result": (
                "FINISHED" in helper_result
                if bpy.app.version >= (5, 1, 0)
                else "PASS_THROUGH" in helper_result
            ),
            "command_executed": bool(command_result),
            "menu_drawn": "CANCELLED" in menu_result,
        }
        print("PME_SAMPLE_ALIAS_HELPER", helper_result, flush=True)
        print("PME_SAMPLE_ALIAS_CHECKS", checks, flush=True)
        bpy.app.timers.register(
            lambda: finish(all(checks.values())), first_interval=1.0
        )
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_SAMPLE_ALIAS_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
