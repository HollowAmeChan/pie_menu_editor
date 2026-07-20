import addon_utils
import bpy
import traceback


TAG = "PME_CONTEXT_OVERRIDE_WINDOW_SMOKE"
MARKER = "pme_context_override_window"
state = {"source_window": None, "checks": {}}


def finish(success):
    try:
        if MARKER in bpy.context.scene:
            del bpy.context.scene[MARKER]
        source_pointer = state["source_window"]
        for window in tuple(bpy.context.window_manager.windows):
            if window.as_pointer() == source_pointer:
                continue
            with bpy.context.temp_override(window=window):
                bpy.ops.wm.window_close()
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_CHECKS", state["checks"], flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify():
    try:
        from pie_menu_editor.core import screen_utils

        source_pointer = state["source_window"]
        target = next(
            window
            for window in bpy.context.window_manager.windows
            if window.as_pointer() != source_pointer
        )
        initial_context_window = bpy.context.window.as_pointer()
        override_args = screen_utils.get_override_args(
            window=target,
            area="VIEW_3D",
            region="WINDOW",
        )
        area = override_args.get("area")
        region = override_args.get("region")
        checks = state["checks"]
        checks["window_resolved"] = override_args.get("window") == target
        checks["screen_from_window"] = override_args.get("screen") == target.screen
        checks["area_from_screen"] = area in target.screen.areas[:]
        checks["region_from_area"] = region in area.regions[:]

        with bpy.context.temp_override(**override_args):
            checks["direct_override_target"] = (
                bpy.context.window == target
                and bpy.context.screen == target.screen
                and bpy.context.area == area
                and bpy.context.region == region
            )
        checks["direct_override_restored"] = (
            bpy.context.window.as_pointer() == initial_context_window
        )

        override = screen_utils.override_context(
            "VIEW_3D",
            window=target,
            enter=False,
        )
        with override:
            checks["public_override_target"] = (
                bpy.context.window == target
                and bpy.context.screen == target.screen
                and bpy.context.area in target.screen.areas[:]
            )
        checks["public_override_restored"] = (
            bpy.context.window.as_pointer() == initial_context_window
        )

        result = screen_utils.exec_with_override(
            f'C.scene["{MARKER}"] = str(C.window.as_pointer())',
            window=target,
            area="VIEW_3D",
            region="WINDOW",
        )
        checks["exec_target"] = (
            result
            and bpy.context.scene.get(MARKER) == str(target.as_pointer())
        )
        checks["exec_restored"] = (
            bpy.context.window.as_pointer() == initial_context_window
        )
        print(
            TAG + "_DATA",
            bpy.app.version_string,
            {
                "source": source_pointer,
                "target": target.as_pointer(),
                "screen": target.screen.as_pointer(),
                "area": area.as_pointer(),
                "region": region.as_pointer(),
            },
            flush=True,
        )
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def open_window():
    try:
        state["source_window"] = bpy.context.window.as_pointer()
        result = bpy.ops.wm.window_new()
        state["checks"]["window_opened"] = result == {"FINISHED"}
        bpy.app.timers.register(verify, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
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
        bpy.app.timers.register(open_window, first_interval=0.2)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
