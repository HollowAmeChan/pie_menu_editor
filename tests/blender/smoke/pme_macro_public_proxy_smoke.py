import addon_utils
import bpy
import traceback


TAG = "PME_MACRO_PUBLIC_PROXY_SMOKE"
MENU_NAME = "PME Macro Public Proxy Smoke"
MARKER = "pme_macro_public_proxy_smoke"
operator_registered = False
success = False


class PME_OT_macro_public_proxy_dependency(bpy.types.Operator):
    bl_idname = "pme.macro_public_proxy_dependency"
    bl_label = "PME Macro Public Proxy Dependency"

    def execute(self, context):
        return {'FINISHED'}


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
    old = prefs.pie_menus.get(MENU_NAME)
    if old is not None:
        prefs.remove_pm(old)

    bpy.utils.register_class(PME_OT_macro_public_proxy_dependency)
    operator_registered = True
    menu = prefs.add_pm("MACRO", MENU_NAME)
    dependency = menu.pmis[0]
    dependency.name = "Dependency"
    dependency.mode = "COMMAND"
    dependency.text = (
        "bpy.ops.pme.macro_public_proxy_dependency('INVOKE_DEFAULT')"
    )
    marker = menu.pmis.add()
    marker.name = "Marker"
    marker.mode = "COMMAND"
    marker.text = f'C.scene["{MARKER}"] = C.scene.get("{MARKER}", 0) + 1'
    package.macro_utils.update_macro(menu)

    proxy_type = package.macro_utils._macro_proxies[menu.name]
    native_type = package.macro_utils._macros[menu.name]
    public_operator = eval("bpy.ops." + proxy_type.bl_idname)
    bpy.context.scene[MARKER] = 0
    valid_result = public_operator("EXEC_DEFAULT")
    marker_after_valid = bpy.context.scene.get(MARKER, 0)

    bpy.utils.unregister_class(PME_OT_macro_public_proxy_dependency)
    operator_registered = False
    bpy.context.scene[MARKER] = 0
    missing_result = public_operator("EXEC_DEFAULT")
    marker_after_missing = bpy.context.scene.get(MARKER, 0)

    checks = {
        "public_id_is_operator_proxy": (
            issubclass(proxy_type, bpy.types.Operator)
            and not issubclass(proxy_type, bpy.types.Macro)
        ),
        "native_macro_is_internal": (
            issubclass(native_type, bpy.types.Macro)
            and "INTERNAL" in native_type.bl_options
        ),
        "valid_public_call_finished": valid_result == {'FINISHED'},
        "valid_public_call_executed": marker_after_valid == 1,
        "stale_public_call_cancelled": missing_result == {'CANCELLED'},
        "stale_public_call_stopped": marker_after_missing == 0,
        "unsafe_native_removed": menu.name not in package.macro_utils._macros,
        "safe_proxy_retained": menu.name in package.macro_utils._macro_proxies,
    }
    print(
        TAG + "_DATA",
        bpy.app.version_string,
        module.bl_info.get("version"),
        "proxy=",
        proxy_type.bl_idname,
        "native=",
        native_type.bl_idname,
        "results=",
        (valid_result, missing_result),
        "markers=",
        (marker_after_valid, marker_after_missing),
        flush=True,
    )
    print(TAG + "_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    try:
        if operator_registered:
            bpy.utils.unregister_class(PME_OT_macro_public_proxy_dependency)
        prefs = locals().get("prefs")
        if prefs:
            menu = prefs.pie_menus.get(MENU_NAME)
            if menu is not None:
                prefs.remove_pm(menu)
        bpy.context.scene.pop(MARKER, None)
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
