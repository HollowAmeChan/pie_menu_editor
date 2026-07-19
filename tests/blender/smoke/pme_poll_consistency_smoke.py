import addon_utils
import bpy
import traceback


TAG = "PME_POLL_CONSISTENCY_SMOKE"
FALSE_MENU = "PME Poll False Smoke"
ERROR_MENU = "PME Poll Error Smoke"
TRUE_MENU = "PME Poll True Smoke"
MARKER = "pme_poll_consistency_smoke"
TRUE_MARKER = "pme_poll_true_smoke"
created = []
success = False


def add_script_menu(prefs, name, poll_cmd, marker=MARKER):
    menu = prefs.add_pm("SCRIPT", name)
    created.append(menu.name)
    menu.poll_cmd = poll_cmd
    if not menu.pmis:
        menu.pmis.add()
    item = menu.pmis[0]
    item.name = "Marker"
    item.mode = "COMMAND"
    item.text = (
        f'C.scene["{marker}"] = C.scene.get("{marker}", 0) + 1'
    )
    return menu


try:
    module = addon_utils.enable(
        "pie_menu_editor",
        default_set=True,
        persistent=False,
        handle_error=None,
    )
    package = module.core
    if not hasattr(bpy.types.WindowManager, "pme"):
        for waiter in package.PME_OT_wait_context.instances:
            waiter.cancelled = True
        package.on_context()

    prefs = package.addon.get_prefs()
    false_menu = add_script_menu(prefs, FALSE_MENU, "return False")
    error_menu = add_script_menu(prefs, ERROR_MENU, "return 1 / 0")
    true_menu = add_script_menu(
        prefs,
        TRUE_MENU,
        'return C.area.type == "VIEW_3D" and context.area.type == "VIEW_3D"',
        TRUE_MARKER,
    )
    bpy.context.scene[MARKER] = 0
    bpy.context.scene[TRUE_MARKER] = 0

    area = next(item for item in bpy.context.screen.areas if item.type == "VIEW_3D")
    region = next(item for item in area.regions if item.type == "WINDOW")
    operator_class = package.operators.WM_OT_pme_user_pie_menu_call
    runtime_menu_class = getattr(
        bpy.types, package.ui_utils.get_pme_menu_class(false_menu.name)
    )

    error_poll_raised = False
    try:
        error_poll = error_menu.poll(operator_class, bpy.context)
    except Exception:
        error_poll_raised = True
        error_poll = None

    with bpy.context.temp_override(area=area, region=region):
        direct_poll = false_menu.poll(operator_class, bpy.context)
        true_poll = true_menu.poll(operator_class, bpy.context)
        runtime_poll = getattr(runtime_menu_class, "poll", None)
        runtime_menu_poll = runtime_poll(bpy.context) if runtime_poll else True
        sub_result = bpy.ops.wm.pme_user_pie_menu_call(
            "INVOKE_DEFAULT",
            pie_menu_name=false_menu.name,
            invoke_mode="SUB",
            keymap="Window",
        )
        preview_result = bpy.ops.pme.preview(
            "EXEC_DEFAULT", pie_menu_name=false_menu.name
        )
        open_result = package.ui_utils.open_menu(false_menu.name)
        hotkey_result = bpy.ops.wm.pme_user_pie_menu_call(
            "INVOKE_DEFAULT",
            pie_menu_name=false_menu.name,
            invoke_mode="HOTKEY",
            keymap="Window",
        )
        error_result = bpy.ops.wm.pme_user_pie_menu_call(
            "INVOKE_DEFAULT",
            pie_menu_name=error_menu.name,
            invoke_mode="SUB",
            keymap="Window",
        )
        true_result = bpy.ops.wm.pme_user_pie_menu_call(
            "INVOKE_DEFAULT",
            pie_menu_name=true_menu.name,
            invoke_mode="SUB",
            keymap="Window",
        )

    marker = bpy.context.scene.get(MARKER, 0)
    true_marker = bpy.context.scene.get(TRUE_MARKER, 0)
    checks = {
        "direct_false_poll": direct_poll is False,
        "direct_true_poll": true_poll is True,
        "runtime_menu_false_poll": runtime_menu_poll is False,
        "poll_error_is_safe_false": not error_poll_raised and error_poll is False,
        "sub_cancelled": sub_result == {"CANCELLED"},
        "preview_completed": preview_result == {"FINISHED"},
        "script_open_recognized": open_result is True,
        "hotkey_passed_through": hotkey_result == {"PASS_THROUGH"},
        "error_entry_cancelled": error_result == {"CANCELLED"},
        "no_script_side_effects": marker == 0,
        "valid_script_executed": true_result == {"CANCELLED"} and true_marker == 1,
    }
    print(
        TAG + "_DATA",
        bpy.app.version_string,
        "marker=",
        marker,
        "true_marker=",
        true_marker,
        "results=",
        {
            "sub": sub_result,
            "preview": preview_result,
            "open": open_result,
            "hotkey": hotkey_result,
            "error": error_result,
            "true": true_result,
        },
        "error_poll_raised=",
        error_poll_raised,
        flush=True,
    )
    print(TAG + "_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    try:
        prefs = locals().get("prefs")
        if prefs:
            for name in reversed(created):
                if name in prefs.pie_menus:
                    prefs.remove_pm(prefs.pie_menus[name])
        bpy.context.scene.pop(MARKER, None)
        bpy.context.scene.pop(TRUE_MARKER, None)
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
