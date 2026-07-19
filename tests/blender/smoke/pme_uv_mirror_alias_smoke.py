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
    print("PME_UV_MIRROR_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def run():
    global menu_name
    try:
        from pie_menu_editor.core import compatibility_fixes, pme
        from pie_menu_editor.core.addon import get_prefs
        from pie_menu_editor.core.bl_utils import mesh_faces_mirror_uv

        prefs = get_prefs()
        menu = prefs.add_pm(mode="DIALOG", name="PME UV Mirror Alias Smoke")
        menu_name = menu.name
        for name, direction in (("Positive", "POSITIVE"), ("Negative", "NEGATIVE")):
            item = menu.pmis.add()
            item.name = name
            item.mode = "COMMAND"
            item.text = (
                "bpy.ops.mesh.faces_mirror_uv("
                f"direction='{direction}', precision=3)"
            )

        compatibility_fixes.fix_1_19_7(prefs, menu)
        command_items = [
            item for item in menu.pmis if item.mode == "COMMAND" and item.text
        ]
        migrated = [item.text for item in command_items]
        expected = [
            "mesh_faces_mirror_uv(direction='POSITIVE', precision=3)",
            "mesh_faces_mirror_uv(direction='NEGATIVE', precision=3)",
        ]

        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            obj = bpy.context.active_object
            if not obj.data.uv_layers:
                obj.data.uv_layers.new(name="UVMap")
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
            bpy.ops.mesh.select_all(action="SELECT")
            positive_result = mesh_faces_mirror_uv(
                direction='POSITIVE', precision=3
            )
            negative_result = mesh_faces_mirror_uv(
                direction='NEGATIVE', precision=3
            )
            command_results = [
                pme.context.exe(item.text, use_try=False) for item in command_items
            ]
            menu_result = bpy.ops.wm.pme_user_pie_menu_call(
                "INVOKE_DEFAULT",
                pie_menu_name=menu.name,
                invoke_mode="SUB",
                keymap="Window",
            )

        checks = {
            "migration": migrated == expected,
            "positive_finished": "FINISHED" in positive_result,
            "negative_finished": "FINISHED" in negative_result,
            "commands_executed": all(command_results),
            "menu_drawn": "CANCELLED" in menu_result,
        }
        print("PME_UV_MIRROR_MIGRATED", migrated, flush=True)
        print("PME_UV_MIRROR_CHECKS", checks, flush=True)
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
        print("PME_UV_MIRROR_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
