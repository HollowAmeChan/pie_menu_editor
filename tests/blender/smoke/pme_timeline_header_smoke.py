import addon_utils
import bpy
import os
import traceback


state = {}
menu_name = None
target = None
original_draw = None
original_print_exc = None


def finish(success):
    global target, original_draw, original_print_exc
    try:
        if target and original_draw:
            target.draw = original_draw
        if original_print_exc:
            from pie_menu_editor.core import ui_utils

            ui_utils.print_exc = original_print_exc
        from pie_menu_editor.core.addon import get_prefs

        preferences = get_prefs()
        if menu_name and menu_name in preferences.pie_menus:
            preferences.remove_pm(preferences.pie_menus[menu_name])
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_TIMELINE_HEADER_STATE", state, flush=True)
    print("PME_TIMELINE_HEADER_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify():
    direct_calls = state.get("after", 0) - state.get("before", 0)
    return finish(
        direct_calls > 0
        and state.get("errors", 0) == 0
        and state.get("mapping") == state.get("expected")
    )


def run():
    global menu_name, target, original_draw, original_print_exc
    try:
        from pie_menu_editor.core import pme, ui_utils
        from pie_menu_editor.core.addon import get_prefs

        preferences = get_prefs()
        pme.context.add_global("SMOKE_STATE", state)
        original_print_exc = ui_utils.print_exc

        def tracked_error(*args, **kwargs):
            state["errors"] = state.get("errors", 0) + 1
            return original_print_exc(*args, **kwargs)

        ui_utils.print_exc = tracked_error
        kind = os.environ.get("PME_HEADER_KIND", "TIMELINE")
        if kind == "TIMELINE":
            expected_name = (
                "TIME_MT_editor_menus"
                if hasattr(bpy.types, "TIME_MT_editor_menus")
                else "DOPESHEET_MT_editor_menus"
            )
        elif kind == "IMAGE":
            expected_name = "IMAGE_MT_editor_menus"
        else:
            expected_name = "CLIP_MT_tracking_editor_menus"
        target = getattr(bpy.types, expected_name)
        original_draw = target.draw

        def tracked_draw(self, context):
            state["target_draw"] = state.get("target_draw", 0) + 1
            return original_draw(self, context)

        target.draw = tracked_draw

        menu = preferences.add_pm(mode="DIALOG", name="PME Timeline Header Smoke")
        menu_name = menu.name
        item = menu.pmis.add()
        item.name = "Timeline Header"
        item.mode = "CUSTOM"
        item.text = (
            "SMOKE_STATE['before'] = SMOKE_STATE.get('target_draw', 0); "
            "header_menu(['CURRENT']); "
            "SMOKE_STATE['after'] = SMOKE_STATE.get('target_draw', 0)"
        )

        window = bpy.context.window
        area = next(
            (
                item
                for item in window.screen.areas
                if item.type == "DOPESHEET_EDITOR"
                and item.spaces.active.mode == "TIMELINE"
            ),
            None,
        )
        if kind == "IMAGE":
            area.type = "IMAGE_EDITOR"
        elif kind == "CLIP":
            area.type = "CLIP_EDITOR"
        region = next((item for item in area.regions if item.type == "WINDOW"), None)
        if not area or not region:
            return finish(False)
        with bpy.context.temp_override(
            window=window, screen=window.screen, area=area, region=region
        ):
            result = bpy.ops.wm.pme_user_pie_menu_call(
                "INVOKE_DEFAULT",
                pie_menu_name=menu.name,
                invoke_mode="SUB",
                keymap="Window",
            )
        state["mapping"] = (
            expected_name
            if kind == "CLIP"
            else ui_utils.HEADER_MENU_TYPES[kind]
        )
        state["expected"] = expected_name
        print("PME_TIMELINE_HEADER_TARGET", expected_name, flush=True)
        print("PME_TIMELINE_HEADER_RETURN", result, flush=True)
        bpy.app.timers.register(verify, first_interval=1.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_TIMELINE_HEADER_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
