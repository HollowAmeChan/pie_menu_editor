import addon_utils
import bpy
import traceback


preferences = None
names = []


def finish(success):
    try:
        if preferences:
            for name in reversed(names):
                if name in preferences.pie_menus:
                    preferences.remove_pm(preferences.pie_menus[name])
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_HOTKEY_MODES_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def run_checks():
    global preferences
    try:
        from pie_menu_editor.core.addon import get_prefs
        from pie_menu_editor.core.keymap_helper import PME_OT_mouse_btn_state

        preferences = get_prefs()
        cases = (
            ("PRESS", "F13", "PRESS", "ANY"),
            ("HOLD", "F14", "PRESS", "ANY"),
            ("DOUBLE_CLICK", "F15", "DOUBLE_CLICK", "ANY"),
            ("TWEAK", "F16", "PRESS", "ANY"),
            ("CHORDS", "F17", "PRESS", "ANY"),
            ("CLICK", "F18", "CLICK", "ANY"),
            ("CLICK_DRAG", "F19", "CLICK_DRAG", "EAST"),
        )
        checks = {}
        details = {}

        for mode, key, expected_value, direction in cases:
            pm = preferences.add_pm(mode="PMENU", name=f"PMEHotkey{mode}")
            names.append(pm.name)
            pm.open_mode = mode
            if mode == "CHORDS":
                pm.chord = "B"
            if mode == "CLICK_DRAG":
                pm.drag_dir = direction
            pm.key = key
            pm.km_name = "Window"
            pm.register_hotkey()
            mapped = pm.kmis_map.get(pm.name) or {}
            kmi = mapped.get("Window")
            actual_direction = getattr(kmi, "direction", "ANY") if kmi else None
            ok = bool(
                kmi
                and kmi.type == key
                and kmi.value == expected_value
                and actual_direction == direction
            )
            if mode == "CHORDS":
                ok = ok and pm.chord == "B"
            checks[mode] = ok
            details[mode] = (
                (kmi.type, kmi.value, actual_direction, kmi.active) if kmi else None
            )

        modifier_pm = preferences.add_pm(mode="PMENU", name="PMEHotkeyModifier")
        names.append(modifier_pm.name)
        modifier_pm.key = "F20"
        modifier_pm.key_mod = "LEFTMOUSE"
        modifier_pm.km_name = "Window"
        modifier_pm.register_hotkey()
        modifier_kmi = (modifier_pm.kmis_map.get(modifier_pm.name) or {}).get("Window")
        addon_window = bpy.context.window_manager.keyconfigs.addon.keymaps["Window"]
        state_handlers = [
            item
            for item in addon_window.keymap_items
            if item.idname == PME_OT_mouse_btn_state.bl_idname
            and item.type == "LEFTMOUSE"
        ]
        checks["MOUSE_MODIFIER"] = bool(
            modifier_kmi
            and modifier_kmi.key_modifier == "NONE"
            and state_handlers
        )
        details["MOUSE_MODIFIER"] = {
            "kmi_modifier": modifier_kmi.key_modifier if modifier_kmi else None,
            "handlers": len(state_handlers),
        }

        print("PME_HOTKEY_MODES_CHECKS", checks, flush=True)
        print("PME_HOTKEY_MODES_DETAILS", details, flush=True)
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_HOTKEY_MODES_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run_checks, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
