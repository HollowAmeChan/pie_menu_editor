import addon_utils
import bpy
import os
import traceback
from types import SimpleNamespace


success = False

try:
    module = addon_utils.enable(
        "pie_menu_editor",
        default_set=True,
        persistent=False,
        handle_error=None,
    )
    if not hasattr(bpy.types, "PME_OT_restore_pie_prefs"):
        for waiter in module.core.PME_OT_wait_context.instances:
            waiter.cancelled = True
        module.core.on_context()

    restore_type = bpy.types.PME_OT_restore_pie_prefs
    mouse_type = bpy.types.PME_OT_mouse_btn_state
    restore_result = bpy.ops.pme.restore_pie_prefs("INVOKE_DEFAULT", key="A")
    mouse_result = bpy.ops.pme.mouse_btn_state(
        "INVOKE_DEFAULT", key="LEFTMOUSE"
    )

    class DummyWindowManager:
        def __init__(self):
            self.removed = []

        def event_timer_remove(self, timer):
            self.removed.append(timer)

    class DummyHandler(module.core.c_utils.HeadModalHandler):
        def finish(self):
            self.did_finish = True

    dummy = DummyHandler()
    dummy.key = "A"
    dummy.timer = object()
    dummy.finished = False
    dummy.did_finish = False
    window_manager = DummyWindowManager()
    context = SimpleNamespace(window_manager=window_manager)
    release_result = dummy.modal(
        context, SimpleNamespace(type="A", value="RELEASE")
    )
    timer_result = dummy.modal(
        context, SimpleNamespace(type="TIMER", value="NOTHING")
    )

    checks = {
        "enabled": module is not None,
        "installed_path": not os.environ.get("PME_EXPECTED_ADDON_ROOT")
        or os.path.normcase(module.__file__).startswith(
            os.path.normcase(os.environ["PME_EXPECTED_ADDON_ROOT"])
        ),
        "restore_priority": "MODAL_PRIORITY" in restore_type.bl_options,
        "mouse_priority": "MODAL_PRIORITY" in mouse_type.bl_options,
        "restore_running": restore_result == {"RUNNING_MODAL"},
        "mouse_running": mouse_result == {"RUNNING_MODAL"},
        "release_passthrough": release_result == {"PASS_THROUGH"},
        "timer_finished": timer_result == {"FINISHED"},
        "timer_removed": len(window_manager.removed) == 1,
        "finish_called": dummy.did_finish,
    }
    print(
        "PME_MODAL_PRIORITY_CHECKS",
        bpy.app.version_string,
        checks,
        module.__file__,
        flush=True,
    )
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    print("PME_MODAL_PRIORITY_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
