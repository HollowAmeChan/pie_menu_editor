import addon_utils
import bpy
from types import SimpleNamespace
import traceback


TAG = "PME_KEEP_PIE_OPEN_SAFETY_SMOKE"
success = False


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

    block = SimpleNamespace(flag=0)
    layout_pointer = SimpleNamespace(
        root=SimpleNamespace(
            contents=SimpleNamespace(
                block=SimpleNamespace(contents=block),
            )
        )
    )
    original_c_layout = package.c_utils.c_layout
    calls = []

    def tracked_c_layout(layout):
        calls.append(layout)
        return layout_pointer

    package.c_utils.c_layout = tracked_c_layout
    try:
        result = package.pme.context.keep_pie_open(object())
    finally:
        package.c_utils.c_layout = original_c_layout

    if bpy.app.version < (5, 0, 0):
        checks = {
            "legacy_layout_accessed": len(calls) == 1,
            "legacy_flag_set": bool(block.flag & package.c_utils.UI_BLOCK_KEEP_OPEN),
            "legacy_result_true": result is True,
        }
    else:
        checks = {
            "modern_layout_not_accessed": not calls,
            "modern_flag_unchanged": block.flag == 0,
            "modern_result_false": result is False,
        }

    print(
        TAG + "_DATA",
        bpy.app.version_string,
        "calls=",
        len(calls),
        "flag=",
        block.flag,
        "result=",
        result,
        flush=True,
    )
    print(TAG + "_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
