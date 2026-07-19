import addon_utils
import bpy
import traceback


area = None
before_width = 0


def finish(success):
    print("PME_AREA_MOVE_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify():
    try:
        after_width = area.width
        checks = {
            "area_valid": any(
                candidate == area
                for candidate in bpy.context.window_manager.windows[0].screen.areas
            ),
            "width_changed": abs(after_width - before_width) >= 10,
        }
        print(
            "PME_AREA_MOVE_CHECKS",
            checks,
            {"before": before_width, "after": after_width},
            flush=True,
        )
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def move_area():
    global area, before_width
    try:
        window = bpy.context.window_manager.windows[0]
        screen = window.screen
        area = next(a for a in screen.areas if a.ui_type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        before_width = area.width
        window.cursor_warp(area.x + area.width // 2, area.y + area.height // 2)
        with bpy.context.temp_override(
            window=window, screen=screen, area=area, region=region
        ):
            result = bpy.ops.pme.area_move(
                "INVOKE_DEFAULT",
                area="VIEW_3D",
                edge="RIGHT",
                delta=-40,
                move_cursor=False,
            )
        print("PME_AREA_MOVE_CALL_RETURN", result, flush=True)
        bpy.app.timers.register(verify, first_interval=2.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_AREA_MOVE_ENABLE_RETURN", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(move_area, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
