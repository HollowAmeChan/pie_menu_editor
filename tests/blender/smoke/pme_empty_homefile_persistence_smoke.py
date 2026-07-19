import addon_utils
import bpy
from bpy.app.handlers import persistent
import traceback


TAG = "PME_EMPTY_HOMEFILE_PERSISTENCE"
CASES = (
    ("PME Empty Homefile PMENU", "PMENU"),
    ("PME Empty Homefile RMENU", "RMENU"),
    ("PME Empty Homefile DIALOG", "DIALOG"),
    ("PME Empty Homefile SCRIPT", "SCRIPT"),
    ("PME Empty Homefile PANEL", "PANEL"),
    ("PME Empty Homefile HPANEL", "HPANEL"),
    ("PME Empty Homefile STICKY", "STICKY"),
    ("PME Empty Homefile MACRO", "MACRO"),
    ("PME Empty Homefile MODAL", "MODAL"),
    ("PME Empty Homefile PROPERTY", "PROPERTY"),
)
NAMES = tuple(name for name, _mode in CASES)
state = {
    "before": None,
    "original_hold_time": None,
    "expected_hold_time": 463,
    "load_seen": False,
}


def signature(prefs):
    return [
        (
            menu.name,
            menu.mode,
            menu.data,
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


def finish(success, checks=None, after=None):
    try:
        if after_load in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(after_load)
        if "pie_menu_editor" in bpy.context.preferences.addons:
            from pie_menu_editor.core.addon import get_prefs

            prefs = get_prefs()
            if state["original_hold_time"] is not None:
                prefs.hold_time = state["original_hold_time"]
            cleanup(prefs)
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_CHECKS", checks or {}, flush=True)
    print(
        TAG + "_SIGNATURES",
        {"before": state["before"], "after": after},
        flush=True,
    )
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify():
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        after = signature(prefs)
        checks = {
            "load_post_seen": state["load_seen"],
            "empty_filepath": bpy.data.filepath == "",
            "addon_enabled": addon_utils.check("pie_menu_editor") == (True, True),
            "all_modes_preserved": len(after) == len(CASES),
            "exact_data_and_order": after == state["before"],
            "scalar_preference_preserved": (
                prefs.hold_time == state["expected_hold_time"]
            ),
        }
        return finish(all(checks.values()), checks, after)
    except Exception:
        traceback.print_exc()
        return finish(False)


@persistent
def after_load(_):
    state["load_seen"] = True
    bpy.app.timers.register(verify, first_interval=0.8)


def switch_to_empty_homefile():
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        cleanup(prefs)
        state["original_hold_time"] = prefs.hold_time
        prefs.hold_time = state["expected_hold_time"]

        for index, (name, mode) in enumerate(CASES):
            menu = prefs.add_pm(mode=mode, name=name)
            if not menu.pmis:
                menu.pmis.add()
            item = menu.pmis[0]
            item.name = "Marker %d" % index
            item.mode = "COMMAND"
            item.text = 'C.scene["pme_empty_homefile"] = %d' % index

        state["before"] = signature(prefs)
        bpy.app.handlers.load_post.append(after_load)
        result = bpy.ops.wm.read_homefile("EXEC_DEFAULT", use_empty=True)
        print(TAG + "_READ_HOMEFILE", result, flush=True)
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
        bpy.app.timers.register(switch_to_empty_homefile, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
