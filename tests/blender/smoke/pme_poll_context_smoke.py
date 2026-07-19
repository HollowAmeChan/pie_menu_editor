import addon_utils
import bpy
from types import SimpleNamespace
import traceback


TAG = "PME_POLL_CONTEXT_SMOKE"
MENU_NAME = "PME Poll Context Smoke"
ERROR_MENU_NAME = "PME Poll Context Error Smoke"
created = []
success = False


def add_menu(prefs, name, poll_cmd):
    menu = prefs.add_pm("SCRIPT", name)
    created.append(menu.name)
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
    menu = add_menu(
        prefs,
        MENU_NAME,
        (
            "return (C.mode == context.mode and C.area == context.area "
            "and C.region == context.region and C.space_data == context.space_data "
            "and bpy.context.mode == context.mode)"
        ),
    )
    error_menu = add_menu(
        prefs,
        ERROR_MENU_NAME,
        "_ = C.mode; raise RuntimeError('poll context smoke')",
    )

    ambient_context = package.bl_utils.bl_context.context
    area = next(item for item in bpy.context.screen.areas if item.type == "VIEW_3D")
    region = next(item for item in area.regions if item.type == "WINDOW")
    passed_context = SimpleNamespace(
        mode="PME_PASSED_CONTEXT",
        area=area,
        region=region,
        space_data=area.spaces.active,
    )

    direct_poll = menu.poll(None, passed_context)
    restored_after_success = package.bl_utils.bl_context.context is ambient_context
    error_poll = error_menu.poll(None, passed_context)
    restored_after_error = package.bl_utils.bl_context.context is ambient_context

    checks = {
        "passed_context_used_by_C": direct_poll is True,
        "context_restored_after_success": restored_after_success,
        "poll_error_is_safe_false": error_poll is False,
        "context_restored_after_error": restored_after_error,
    }
    print(
        TAG + "_DATA",
        bpy.app.version_string,
        "ambient_mode=",
        bpy.context.mode,
        "passed_mode=",
        passed_context.mode,
        "direct_poll=",
        direct_poll,
        "error_poll=",
        error_poll,
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
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
