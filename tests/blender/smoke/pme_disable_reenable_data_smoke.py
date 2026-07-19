import addon_utils
import bpy
import traceback


CASES = (
    ("PME Re-enable Data A", "DIALOG"),
    ("PME Re-enable Data B", "SCRIPT"),
    ("PME Re-enable PMENU", "PMENU"),
    ("PME Re-enable RMENU", "RMENU"),
    ("PME Re-enable MACRO", "MACRO"),
    ("PME Re-enable MODAL", "MODAL"),
    ("PME Re-enable STICKY", "STICKY"),
    ("PME Re-enable PANEL", "PANEL"),
    ("PME Re-enable HPANEL", "HPANEL"),
    ("PME Re-enable PROPERTY", "PROPERTY"),
)
NAMES = tuple(name for name, _mode in CASES)
before_signature = None
original_hold_time = None
expected_hold_time = None


def signature(prefs):
    return [
        (
            menu.name,
            menu.mode,
            [(item.name, item.mode, item.text) for item in menu.pmis],
        )
        for menu in prefs.pie_menus
        if menu.name in NAMES
    ]


def cleanup(prefs):
    for name in reversed(NAMES):
        menu = prefs.pie_menus.get(name)
        if menu is not None:
            prefs.remove_pm(menu)


def finish(success, checks=None, after_signature=None):
    try:
        if "pie_menu_editor" in bpy.context.preferences.addons:
            from pie_menu_editor.core.addon import get_prefs

            prefs = get_prefs()
            if original_hold_time is not None:
                prefs.hold_time = original_hold_time
            cleanup(prefs)
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_DISABLE_REENABLE_DATA_CHECKS", checks or {}, flush=True)
    print(
        "PME_DISABLE_REENABLE_DATA_SIGNATURES",
        {"before": before_signature, "after": after_signature},
        flush=True,
    )
    print(
        "PME_DISABLE_REENABLE_DATA_RESULT",
        "OK" if success else "FAILED",
        flush=True,
    )
    bpy.ops.wm.quit_blender()
    return None


def verify_reenabled():
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        after_signature = signature(prefs)
        checks = {
            "addon_enabled": "pie_menu_editor" in bpy.context.preferences.addons,
            "menu_count": len(after_signature) == len(NAMES),
            "exact_data_and_order": after_signature == before_signature,
            "scalar_preference_preserved": prefs.hold_time == expected_hold_time,
        }
        return finish(all(checks.values()), checks, after_signature)
    except Exception:
        traceback.print_exc()
        return finish(False)


def reenable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print(
            "PME_DISABLE_REENABLE_DATA_REENABLE",
            module.__file__ if module else None,
            flush=True,
        )
        bpy.app.timers.register(verify_reenabled, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def disable():
    try:
        addon_utils.disable("pie_menu_editor", default_set=True, handle_error=None)
        bpy.app.timers.register(reenable, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def setup():
    global before_signature, expected_hold_time, original_hold_time
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        cleanup(prefs)
        original_hold_time = prefs.hold_time
        expected_hold_time = 437
        prefs.hold_time = expected_hold_time

        first = prefs.add_pm(mode="DIALOG", name=NAMES[0])
        first.pmis[0].name = "First"
        first.pmis[0].mode = "COMMAND"
        first.pmis[0].text = "bpy.ops.wm.redraw_timer(iterations=1)"

        second = prefs.add_pm(mode="SCRIPT", name=NAMES[1])
        second.pmis[0].name = "Second"
        second.pmis[0].mode = "COMMAND"
        second.pmis[0].text = "print('PME re-enable data smoke')"

        for name, mode in CASES[2:]:
            prefs.add_pm(mode=mode, name=name)

        before_signature = signature(prefs)
        bpy.app.timers.register(disable, first_interval=0.2)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print(
            "PME_DISABLE_REENABLE_DATA_ENABLE",
            module.__file__ if module else None,
            flush=True,
        )
        bpy.app.timers.register(setup, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
