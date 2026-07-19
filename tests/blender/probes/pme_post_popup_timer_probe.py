import addon_utils
import bpy
import traceback


def finish(success):
    print("PME_POST_POPUP_TIMER_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


try:
    module = addon_utils.enable(
        "pie_menu_editor",
        default_set=True,
        persistent=False,
        handle_error=None,
    )
    if not hasattr(bpy.types, "PME_OT_popup_area"):
        for waiter in module.core.PME_OT_wait_context.instances:
            waiter.cancelled = True
        module.core.on_context()

    windows = set(bpy.context.window_manager.windows)
    window = next(iter(windows))
    screen = window.screen
    area = next(candidate for candidate in screen.areas if candidate.type == "VIEW_3D")
    region = next(candidate for candidate in area.regions if candidate.type == "WINDOW")
    with bpy.context.temp_override(
        window=window,
        screen=screen,
        area=area,
        region=region,
    ):
        result = bpy.ops.pme.popup_area(
            "INVOKE_DEFAULT",
            area="VIEW_3D",
            width=320,
            height=240,
            auto_close=False,
        )
    created = len(set(bpy.context.window_manager.windows) - windows) == 1
    print("PME_POST_POPUP_TIMER_SETUP", result, created, flush=True)
    bpy.app.timers.register(
        lambda: finish(result == {"FINISHED"} and created),
        first_interval=0.1,
    )
except Exception:
    traceback.print_exc()
    finish(False)
