import addon_utils
import bpy
import traceback


TAG = "PME_MACRO_MISSING_OPERATOR_SMOKE"
MENU_NAME = "PME Macro Missing Operator Smoke"
CHILD_MENU_NAME = "PME Nested Missing Operator Smoke"
PARENT_MENU_NAME = "PME Parent Missing Operator Smoke"
MARKER = "pme_macro_missing_operator_smoke"
created = []
test_operator_registered = False
success = False


class PME_OT_macro_missing_operator_smoke(bpy.types.Operator):
    bl_idname = "pme.macro_missing_operator_smoke"
    bl_label = "PME Macro Missing Operator Smoke"

    def execute(self, context):
        return {"FINISHED"}


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
    menu = prefs.add_pm("MACRO", MENU_NAME)
    created.append(menu.name)
    missing_item = menu.pmis[0]
    missing_item.name = "Missing Operator"
    missing_item.mode = "COMMAND"
    missing_item.text = (
        "bpy.ops.pme.macro_missing_operator_smoke('INVOKE_DEFAULT')"
    )
    marker_item = menu.pmis.add()
    marker_item.name = "Marker"
    marker_item.mode = "COMMAND"
    marker_item.text = f'C.scene["{MARKER}"] = C.scene.get("{MARKER}", 0) + 1'
    package.macro_utils.update_macro(menu)
    bpy.context.scene[MARKER] = 0

    raised = False
    try:
        missing_result = package.macro_utils.execute_macro(menu)
    except Exception:
        raised = True
        missing_result = None

    marker_after_missing = bpy.context.scene.get(MARKER, 0)
    menu_call_result = bpy.ops.wm.pme_user_pie_menu_call(
        "INVOKE_DEFAULT",
        pie_menu_name=menu.name,
        invoke_mode="SUB",
        keymap="Window",
    )
    marker_after_menu_call = bpy.context.scene.get(MARKER, 0)
    missing_item.enabled = False
    package.macro_utils.update_macro(menu)
    valid_result = package.macro_utils.execute_macro(menu)
    marker_after_valid = bpy.context.scene.get(MARKER, 0)

    bpy.utils.register_class(PME_OT_macro_missing_operator_smoke)
    test_operator_registered = True
    missing_item.enabled = True
    package.macro_utils.update_macro(menu)
    bpy.utils.unregister_class(PME_OT_macro_missing_operator_smoke)
    test_operator_registered = False
    bpy.context.scene[MARKER] = 0
    removed_after_build_result = package.macro_utils.execute_macro(menu)
    marker_after_removed_after_build = bpy.context.scene.get(MARKER, 0)

    child = prefs.add_pm("MACRO", CHILD_MENU_NAME)
    created.append(child.name)
    child.pmis[0].name = "Nested Missing Operator"
    child.pmis[0].mode = "COMMAND"
    child.pmis[0].text = "bpy.ops.pme.nested_missing_macro_smoke()"
    package.macro_utils.update_macro(child)

    parent = prefs.add_pm("MACRO", PARENT_MENU_NAME)
    created.append(parent.name)
    parent.pmis[0].name = "Nested Macro"
    parent.pmis[0].mode = "MENU"
    parent.pmis[0].text = child.name
    parent_marker = parent.pmis.add()
    parent_marker.name = "Parent Marker"
    parent_marker.mode = "COMMAND"
    parent_marker.text = marker_item.text
    package.macro_utils.update_macro(parent)
    bpy.context.scene[MARKER] = 0
    nested_result = package.macro_utils.execute_macro(parent)
    marker_after_nested = bpy.context.scene.get(MARKER, 0)

    checks = {
        "missing_operator_does_not_raise": not raised,
        "missing_operator_rejected": missing_result is False,
        "whole_macro_stopped": marker_after_missing == 0,
        "menu_call_cancelled_safely": menu_call_result == {"CANCELLED"},
        "menu_call_stops_whole_macro": marker_after_menu_call == 0,
        "macro_recovers_after_disable": marker_after_valid == 1,
        "valid_macro_invoked": valid_result is not False,
        "removed_after_build_rejected": removed_after_build_result is False,
        "removed_after_build_stops_macro": marker_after_removed_after_build == 0,
        "nested_missing_operator_rejected": nested_result is False,
        "parent_macro_stopped": marker_after_nested == 0,
    }
    print(
        TAG + "_DATA",
        bpy.app.version_string,
        "raised=",
        raised,
        "missing_result=",
        missing_result,
        "menu_call_result=",
        menu_call_result,
        "valid_result=",
        valid_result,
        "removed_after_build_result=",
        removed_after_build_result,
        "nested_result=",
        nested_result,
        "markers=",
        (
            marker_after_missing,
            marker_after_menu_call,
            marker_after_valid,
            marker_after_removed_after_build,
            marker_after_nested,
        ),
        flush=True,
    )
    print(TAG + "_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    try:
        if test_operator_registered:
            bpy.utils.unregister_class(PME_OT_macro_missing_operator_smoke)
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
