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
    print("PME_BRUSH_SWITCH_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def run():
    global menu_name
    try:
        from pie_menu_editor.core import compatibility_fixes, pme
        from pie_menu_editor.core.addon import get_prefs
        from pie_menu_editor.core.bl_utils import activate_brush

        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.object.mode_set(mode="SCULPT")
            for name in ("Draw", "Smooth"):
                result = bpy.ops.brush.asset_activate(
                    asset_library_type="ESSENTIALS",
                    relative_asset_identifier=(
                        "brushes/essentials_brushes-mesh_sculpt.blend/Brush/" + name
                    ),
                )
                print("PME_BRUSH_PRELOAD", name, result, flush=True)

            settings = bpy.context.scene.tool_settings.sculpt
            before = settings.brush.name if settings.brush else None

            prefs = get_prefs()
            menu = prefs.add_pm(mode="DIALOG", name="PME Brush Migration Smoke")
            menu_name = menu.name
            item = menu.pmis.add()
            item.name = "Legacy Draw"
            item.mode = "COMMAND"
            item.text = 'paint_settings(C).brush = D.brushes["Draw"]'
            compatibility_fixes.fix_1_19_4(prefs, menu)
            migrated = item.text == 'activate_brush("Draw")'
            print("PME_BRUSH_COMMAND_MIGRATED", migrated, item.text, flush=True)

            exec_globals = pme.context.gen_globals()
            command_result = pme.context.exe(item.text, exec_globals, use_try=False)
            after = settings.brush.name if settings.brush else None
            reference = settings.brush_asset_reference
            checks = {
                "started_on_smooth": before == "Smooth",
                "migration": migrated,
                "command_result": bool(command_result),
                "switched_to_draw": after == "Draw",
                "reference_type": reference.asset_library_type == "ESSENTIALS",
                "reference_target": reference.relative_asset_identifier.endswith(
                    "/Brush/Draw"
                ),
            }
            print("PME_BRUSH_SWITCH_CHECKS", checks, flush=True)

            menu_result = bpy.ops.wm.call_menu(name="PME_MT_brush_set")
            print("PME_BRUSH_SET_MENU", menu_result, flush=True)

        bpy.app.timers.register(
            lambda: finish(all(checks.values()) and "INTERFACE" in menu_result),
            first_interval=1.0,
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
        print("PME_BRUSH_SWITCH_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
