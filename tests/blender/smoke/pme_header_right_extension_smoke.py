import addon_utils
import bpy
import traceback
from types import SimpleNamespace


MENU_NAME = "TOPBAR_HT_upper_bar_right"


def count_callback(tp, callback):
    funcs = getattr(tp.draw, "_draw_funcs", ())
    return sum(func is callback for func in funcs)


def finish(success, checks=None):
    print("PME_HEADER_RIGHT_EXTENSION_CHECKS", checks or {}, flush=True)
    print(
        "PME_HEADER_RIGHT_EXTENSION_RESULT",
        "OK" if success else "FAILED",
        flush=True,
    )
    bpy.ops.wm.quit_blender()
    return None


def run():
    area = None
    menu = None
    original_area_type = None
    original_draw_layout = None
    try:
        from pie_menu_editor.core import ed_base
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        if MENU_NAME in prefs.pie_menus:
            prefs.remove_pm(prefs.pie_menus[MENU_NAME])

        menu = prefs.add_pm(mode="DIALOG", name=MENU_NAME)
        item = menu.pmis.add()
        item.name = "PME"
        item.mode = "COMMAND"
        item.text = "bpy.ops.wm.pme_user_pie_menu_call()"

        target = bpy.types.TOPBAR_HT_upper_bar
        callback = ed_base.EXTENDED_PANELS.get(MENU_NAME)
        registered = bool(callback) and count_callback(target, callback) == 1

        draw_calls = []
        original_draw_layout = ed_base.draw_pme_layout

        def tracked_draw(*args, **kwargs):
            draw_calls.append(args[0].name)

        ed_base.draw_pme_layout = tracked_draw
        owner = SimpleNamespace(layout=SimpleNamespace(column=lambda **kwargs: None))
        window = bpy.context.window
        area = next(item for item in window.screen.areas if item.type == "VIEW_3D")
        original_area_type = area.type
        area.type = "TOPBAR"
        left_region = next(
            item for item in area.regions if item.alignment == "LEFT"
        )
        right_region = next(
            item for item in area.regions if item.alignment == "RIGHT"
        )

        def draw_in_region(region):
            with bpy.context.temp_override(
                window=window, screen=window.screen, area=area, region=region
            ):
                callback(owner, bpy.context)

        if callback:
            menu.poll_cmd = "return False"
            draw_in_region(right_region)
            false_poll_calls = len(draw_calls)

            menu.poll_cmd = "return 1 / 0"
            error_poll_raised = False
            try:
                draw_in_region(right_region)
            except Exception:
                error_poll_raised = True
            error_poll_calls = len(draw_calls) - false_poll_calls

            menu.poll_cmd = "return True"
            draw_in_region(left_region)
            left_calls = len(draw_calls)
            draw_in_region(right_region)
            right_calls = len(draw_calls) - left_calls
        else:
            false_poll_calls = 0
            error_poll_calls = 0
            error_poll_raised = False
            left_calls = 0
            right_calls = 0

        ed_base.draw_pme_layout = original_draw_layout
        original_draw_layout = None
        area.type = original_area_type
        original_area_type = None
        prefs.remove_pm(menu)
        menu = None

        checks = {
            "registered_on_real_header": registered,
            "false_poll_hidden": false_poll_calls == 0,
            "error_poll_hidden": error_poll_calls == 0,
            "poll_error_contained": not error_poll_raised,
            "hidden_in_left_region": left_calls == 0,
            "drawn_in_right_region": right_calls == 1,
            "registry_cleaned": MENU_NAME not in ed_base.EXTENDED_PANELS,
            "callback_removed": not callback or count_callback(target, callback) == 0,
        }
        return finish(all(checks.values()), checks)
    except Exception:
        traceback.print_exc()
        return finish(False)
    finally:
        if original_draw_layout is not None:
            ed_base.draw_pme_layout = original_draw_layout
        if area is not None and original_area_type is not None:
            area.type = original_area_type
        if menu is not None:
            try:
                get_prefs().remove_pm(menu)
            except Exception:
                traceback.print_exc()


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print(
            "PME_HEADER_RIGHT_EXTENSION_ENABLE",
            module.__file__ if module else None,
            flush=True,
        )
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
