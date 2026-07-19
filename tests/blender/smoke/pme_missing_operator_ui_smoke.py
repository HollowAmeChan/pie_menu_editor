import addon_utils
import bpy
import traceback


menu_name = None
errors = []


def finish():
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        if menu_name and menu_name in prefs.pie_menus:
            prefs.remove_pm(prefs.pie_menus[menu_name])
    except Exception:
        traceback.print_exc()
    expected_count = 2 if bpy.app.version >= (5, 1, 0) else 0
    success = len(errors) == expected_count
    if errors:
        success = success and all(
            error["message"] == "Operator not found: mesh.loop_multi_select"
            for error in errors
        )
    print("PME_MISSING_OPERATOR_ERRORS", errors, flush=True)
    print("PME_MISSING_OPERATOR_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def run():
    global menu_name
    try:
        from pie_menu_editor.core import layout_helper, pme
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        prefs.show_error_trace = True
        original_error = layout_helper.lh.error

        def tracked_error(text, message=None):
            errors.append(
                {
                    "item": getattr(pme.context.pmi, "name", ""),
                    "text": text,
                    "message": message,
                }
            )
            return original_error(text, message)

        layout_helper.lh.error = tracked_error
        menu = prefs.add_pm(mode="PMENU", name="PME Missing Operator Smoke")
        menu_name = menu.name
        menu.pmis[0].name = "Removed Loop Select"
        menu.pmis[0].mode = "COMMAND"
        menu.pmis[0].text = "bpy.ops.mesh.loop_multi_select(ring=False)"
        menu.pmis[1].name = "Known Select All"
        menu.pmis[1].mode = "COMMAND"
        menu.pmis[1].text = "bpy.ops.object.select_all(action='SELECT')"
        menu.pmis[2].name = "Known Positional Select All"
        menu.pmis[2].mode = "COMMAND"
        menu.pmis[2].text = (
            "bpy.ops.object.select_all('INVOKE_DEFAULT', action='SELECT')"
        )
        menu.pmis[3].name = "Removed Positional Loop Select"
        menu.pmis[3].mode = "COMMAND"
        menu.pmis[3].text = (
            "bpy.ops.mesh.loop_multi_select('INVOKE_DEFAULT', ring=False)"
        )

        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            result = bpy.ops.wm.pme_user_pie_menu_call(
                "INVOKE_DEFAULT",
                pie_menu_name=menu.name,
                invoke_mode="SUB",
                keymap="Window",
            )
            print("PME_MISSING_OPERATOR_CALL", result, flush=True)

        bpy.app.timers.register(finish, first_interval=1.5)
    except Exception:
        traceback.print_exc()
        return finish()
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_MISSING_OPERATOR_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish()
    return None


bpy.app.timers.register(enable, first_interval=0.2)
