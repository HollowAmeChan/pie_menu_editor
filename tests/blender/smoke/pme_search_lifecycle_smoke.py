import addon_utils
import bpy
import traceback


results = []


def finish(success):
    print("PME_SEARCH_RESULTS", results, flush=True)
    print("PME_SEARCH_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def invoke_search(label, next_callback):
    try:
        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            result = bpy.ops.wm.search_menu("INVOKE_DEFAULT")
        results.append((label, sorted(result)))
        bpy.app.timers.register(next_callback, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def search_after_reenable():
    return invoke_search("reenabled", verify)


def verify():
    success = len(results) == 2 and all(
        "FINISHED" in result or "RUNNING_MODAL" in result or "INTERFACE" in result
        for _, result in results
    )
    return finish(success)


def reenable():
    try:
        addon_utils.disable("pie_menu_editor", default_set=True, handle_error=None)
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_SEARCH_REENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(search_after_reenable, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def search_initial():
    return invoke_search("initial", reenable)


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_SEARCH_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(search_initial, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
