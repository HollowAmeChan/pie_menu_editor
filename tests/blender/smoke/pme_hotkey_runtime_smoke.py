import addon_utils
import bpy
import traceback
from types import SimpleNamespace


TAG = "PME_HOTKEY_RUNTIME_SMOKE"
state = {"checks": {}}
preferences = None
names = []
original_hold_time = None
original_chord_time = None
event_xy = (100, 100)
view_context = None


def event(key, value):
    return SimpleNamespace(
        type=key,
        value=value,
        mouse_x=event_xy[0],
        mouse_y=event_xy[1],
    )


def finish(success):
    try:
        from pie_menu_editor.core.operators import WM_OT_pme_user_pie_menu_call

        for operator in list(WM_OT_pme_user_pie_menu_call.active_ops.values()):
            operator.cancelled = True
            operator.modal_stop()
        WM_OT_pme_user_pie_menu_call.pressed_key = None
        WM_OT_pme_user_pie_menu_call.hold_inst = None

        if preferences:
            preferences.hold_time = original_hold_time
            preferences.chord_time = original_chord_time
            for name in reversed(names):
                if name in preferences.pie_menus:
                    preferences.remove_pm(preferences.pie_menus[name])
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_STATE", state, flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def add_script_menu(name, key, open_mode, marker, chord="NONE"):
    menu = preferences.add_pm(mode="SCRIPT", name=name)
    names.append(menu.name)
    menu.pmis[0].text = (
        f"INPUT_STATE['{marker}'] = INPUT_STATE.get('{marker}', 0) + 1"
    )
    menu.key = key
    menu.km_name = "Window"
    menu.open_mode = open_mode
    if open_mode == "CHORDS":
        menu.chord = chord
    menu.register_hotkey()
    return menu


def add_pair(prefix, key, secondary_mode, secondary_marker, chord="NONE"):
    press = add_script_menu(prefix + " Press", key, "PRESS", prefix + "_press")
    secondary = add_script_menu(
        prefix + " " + secondary_mode,
        key,
        secondary_mode,
        secondary_marker,
        chord=chord,
    )
    press.unregister_hotkey()
    secondary.register_hotkey()
    mapped = secondary.kmis_map.get(secondary.name) or {}
    state["checks"][prefix + "_registered"] = bool(
        mapped
        and all(
            item.idname == "wm.pme_user_pie_menu_call"
            and item.properties.invoke_mode == "HOTKEY"
            for item in mapped.values()
        )
    )
    return secondary.name


def invoke_hotkey(menu_name, key):
    from pie_menu_editor.core.operators import WM_OT_pme_user_pie_menu_call

    menu = preferences.pie_menus[menu_name]
    with bpy.context.temp_override(**view_context):
        result = bpy.ops.wm.pme_user_pie_menu_call(
            "INVOKE_DEFAULT",
            pie_menu_name=menu.name,
            invoke_mode="HOTKEY",
            keymap="Window",
        )
    operator = WM_OT_pme_user_pie_menu_call.active_ops.get(menu.name)
    WM_OT_pme_user_pie_menu_call.pressed_key = key
    print(TAG + "_INVOKE", menu.name, result, bool(operator), flush=True)
    return result, operator


def verify_chord_timeout():
    try:
        state["checks"]["chord_timeout_press"] = (
            state.get("chord_timeout_press") == 1
        )
        state["checks"]["chord_timeout_not_matched"] = (
            state.get("chord_timeout_match", 0) == 0
        )
        from pie_menu_editor.core.operators import WM_OT_pme_user_pie_menu_call

        state["checks"]["operators_cleared"] = (
            not WM_OT_pme_user_pie_menu_call.active_ops
            and WM_OT_pme_user_pie_menu_call.hold_inst is None
        )
        return finish(all(state["checks"].values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def start_chord_timeout():
    try:
        result, operator = invoke_hotkey(state["chord_timeout_menu"], "F16")
        state["checks"]["chord_timeout_started"] = (
            result == {"RUNNING_MODAL"} and operator is not None
        )
        bpy.app.timers.register(
            verify_chord_timeout,
            first_interval=preferences.chord_time / 1000 + 0.6,
        )
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def verify_chord_match():
    try:
        state["checks"]["chord_matched"] = state.get("chord_match") == 1
        state["checks"]["chord_press_not_run"] = state.get("chord_press", 0) == 0
        bpy.app.timers.register(start_chord_timeout, first_interval=0.3)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def match_chord():
    try:
        operator = state["chord_operator"]
        result = operator.modal(bpy.context, event("B", "PRESS"))
        state["checks"]["chord_event_cancelled"] = result == {"CANCELLED"}
        bpy.app.timers.register(verify_chord_match, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def start_chord_match():
    try:
        result, operator = invoke_hotkey(state["chord_menu"], "F15")
        state["checks"]["chord_started"] = (
            result == {"RUNNING_MODAL"} and operator is not None
        )
        state["chord_operator"] = operator
        bpy.app.timers.register(match_chord, first_interval=0.1)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def verify_long_hold():
    try:
        state["checks"]["long_hold_ran"] = state.get("long_hold") == 1
        state["checks"]["long_press_not_run"] = state.get("long_press", 0) == 0
        bpy.app.timers.register(start_chord_match, first_interval=0.3)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def start_long_hold():
    try:
        result, operator = invoke_hotkey(state["long_menu"], "F14")
        state["checks"]["long_hold_started"] = (
            result == {"RUNNING_MODAL"} and operator is not None
        )
        bpy.app.timers.register(
            verify_long_hold,
            first_interval=preferences.hold_time / 1000 + 0.6,
        )
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def verify_short_press():
    try:
        state["checks"]["short_press_ran"] = state.get("short_press") == 1
        state["checks"]["short_hold_not_run"] = state.get("short_hold", 0) == 0
        bpy.app.timers.register(start_long_hold, first_interval=0.3)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def release_short_press():
    try:
        from pie_menu_editor.core.operators import WM_OT_pme_user_pie_menu_call

        operator = state["short_operator"]
        result = operator.modal(bpy.context, event("F13", "RELEASE"))
        state["checks"]["short_release_finished"] = (
            result in ({"FINISHED"}, {"CANCELLED"})
            and state["short_menu"] not in WM_OT_pme_user_pie_menu_call.active_ops
        )
        print(TAG + "_SHORT_RELEASE", result, flush=True)
        bpy.app.timers.register(verify_short_press, first_interval=0.4)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def start_short_press():
    try:
        result, operator = invoke_hotkey(state["short_menu"], "F13")
        state["checks"]["short_hold_started"] = (
            result == {"RUNNING_MODAL"} and operator is not None
        )
        state["short_operator"] = operator
        bpy.app.timers.register(release_short_press, first_interval=0.05)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def setup():
    global event_xy
    global original_chord_time
    global original_hold_time
    global preferences
    global view_context
    try:
        from pie_menu_editor.core import pme
        from pie_menu_editor.core.addon import get_prefs

        preferences = get_prefs()
        pme.context.add_global("INPUT_STATE", state)
        original_hold_time = preferences.hold_time
        original_chord_time = preferences.chord_time
        preferences.hold_time = 150
        preferences.chord_time = 150

        area = next(
            candidate
            for candidate in bpy.context.window.screen.areas
            if candidate.type == "VIEW_3D"
        )
        region = next(
            candidate for candidate in area.regions if candidate.type == "WINDOW"
        )
        view_context = {
            "window": bpy.context.window,
            "screen": bpy.context.window.screen,
            "area": area,
            "region": region,
        }
        event_xy = (area.x + area.width // 2, area.y + area.height // 2)

        state["short_menu"] = add_pair(
            "short", "F13", "HOLD", "short_hold"
        )
        state["long_menu"] = add_pair("long", "F14", "HOLD", "long_hold")
        state["chord_menu"] = add_pair(
            "chord", "F15", "CHORDS", "chord_match", chord="B"
        )
        state["chord_timeout_menu"] = add_pair(
            "chord_timeout",
            "F16",
            "CHORDS",
            "chord_timeout_match",
            chord="C",
        )
        bpy.context.window_manager.keyconfigs.update()
        bpy.app.timers.register(start_short_press, first_interval=0.3)
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
        print(TAG + "_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(setup, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
