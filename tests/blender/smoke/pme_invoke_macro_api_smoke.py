import addon_utils
import bpy
import traceback


TAG = "PME_INVOKE_MACRO_API_SMOKE"
MARKER = "pme_invoke_macro_api_smoke"
created = []
success = False


def add_macro(prefs, name, command, poll_cmd=None):
    menu = prefs.add_pm("MACRO", name)
    created.append(menu.name)
    menu.pmis[0].name = "Command"
    menu.pmis[0].mode = "COMMAND"
    menu.pmis[0].text = command
    if poll_cmd is not None:
        menu.poll_cmd = poll_cmd
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
    prefs.show_error_trace = True
    valid = add_macro(
        prefs,
        "PME Invoke Macro API Valid",
        f'C.scene["{MARKER}"] = C.scene.get("{MARKER}", 0) + 1',
    )
    valid_name = valid.name
    blocked = add_macro(
        prefs,
        "PME Invoke Macro API Poll Blocked",
        f'C.scene["{MARKER}"] = 100',
        "return False",
    )
    blocked_name = blocked.name
    disabled = add_macro(
        prefs,
        "PME Invoke Macro API Disabled",
        f'C.scene["{MARKER}"] = 200',
    )
    disabled_name = disabled.name
    disabled.enabled = False
    stopped = add_macro(
        prefs,
        "PME Invoke Macro API Stopped",
        "stop = True",
    )
    stopped_name = stopped.name
    stopped_marker = stopped.pmis.add()
    stopped_marker.name = "Must Not Run"
    stopped_marker.mode = "COMMAND"
    stopped_marker.text = f'C.scene["{MARKER}"] = 400'
    package.macro_utils.update_macro(stopped)
    missing_dependency = add_macro(
        prefs,
        "PME Invoke Macro API Missing Dependency",
        "bpy.ops.pme.invoke_macro_api_missing_dependency('INVOKE_DEFAULT')",
    )
    missing_dependency_name = missing_dependency.name
    script_menu = prefs.add_pm("SCRIPT", "PME Invoke Macro API Wrong Mode")
    created.append(script_menu.name)
    script_menu_name = script_menu.name
    script_menu.pmis[0].name = "Wrong Mode"
    script_menu.pmis[0].mode = "COMMAND"
    script_menu.pmis[0].text = f'C.scene["{MARKER}"] = 300'
    bpy.context.scene[MARKER] = 0

    operator_exists = hasattr(bpy.types, "PME_OT_invoke_macro")
    valid = prefs.pie_menus[valid_name]
    valid_availability = {
        "enabled": valid.enabled,
        "mode": valid.mode,
        "poll_cmd": valid.poll_cmd,
        "poll": valid.poll(
            getattr(bpy.types, "PME_OT_invoke_macro", None), bpy.context
        ),
    }
    results = {}
    if operator_exists:
        area = next(item for item in bpy.context.screen.areas if item.type == "VIEW_3D")
        region = next(item for item in area.regions if item.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            results["valid"] = bpy.ops.pme.invoke_macro(
                "EXEC_DEFAULT", menu_name=valid_name
            )
            results["missing"] = bpy.ops.pme.invoke_macro(
                "EXEC_DEFAULT", menu_name="PME Missing Macro"
            )
            results["wrong_mode"] = bpy.ops.pme.invoke_macro(
                "EXEC_DEFAULT", menu_name=script_menu_name
            )
            results["disabled"] = bpy.ops.pme.invoke_macro(
                "EXEC_DEFAULT", menu_name=disabled_name
            )
            results["blocked"] = bpy.ops.pme.invoke_macro(
                "EXEC_DEFAULT", menu_name=blocked_name
            )
            results["stopped"] = bpy.ops.pme.invoke_macro(
                "EXEC_DEFAULT", menu_name=stopped_name
            )
            results["missing_dependency"] = bpy.ops.pme.invoke_macro(
                "EXEC_DEFAULT", menu_name=missing_dependency_name
            )

    marker = bpy.context.scene.get(MARKER, 0)
    checks = {
        "operator_registered": operator_exists,
        "valid_macro_finished": results.get("valid") == {"FINISHED"},
        "valid_macro_executed_once": marker == 1,
        "missing_menu_cancelled": results.get("missing") == {"CANCELLED"},
        "wrong_mode_cancelled": results.get("wrong_mode") == {"CANCELLED"},
        "disabled_macro_cancelled": results.get("disabled") == {"CANCELLED"},
        "poll_blocked_macro_cancelled": results.get("blocked") == {"CANCELLED"},
        "stopped_macro_cancelled": results.get("stopped") == {"CANCELLED"},
        "stopped_macro_did_not_continue": marker == 1,
        "missing_dependency_cancelled": (
            results.get("missing_dependency") == {"CANCELLED"}
        ),
    }
    print(
        TAG + "_DATA",
        bpy.app.version_string,
        "operator_exists=",
        operator_exists,
        "valid_availability=",
        valid_availability,
        "results=",
        results,
        "marker=",
        marker,
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
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
