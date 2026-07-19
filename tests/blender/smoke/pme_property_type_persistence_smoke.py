import addon_utils
import bpy
from bpy.app.handlers import persistent
import traceback


TAG = "PME_PROPERTY_TYPE_PERSISTENCE"
CASES = (
    ("PME Property Persist Bool", "BOOL", 1, True),
    ("PME Property Persist Int Vector", "INT", 3, (7, -3, 19)),
    (
        "PME Property Persist Float Vector",
        "FLOAT",
        4,
        (0.25, -1.5, 3.75, 8.5),
    ),
    ("PME Property Persist String", "STRING", 1, "Blender 5 storage"),
    ("PME Property Persist Enum", "ENUM", 1, "BETA"),
    (
        "PME Property Persist Enum Flag",
        "ENUM_FLAG",
        1,
        {"ALPHA", "GAMMA"},
    ),
)
NAMES = tuple(item[0] for item in CASES)
state = {"load_seen": False, "checks": {}}


def cleanup(prefs):
    for name in reversed(NAMES):
        menu = prefs.pie_menus.get(name)
        if menu is not None:
            prefs.remove_pm(menu)


def normalize(value):
    if isinstance(value, set):
        return tuple(sorted(value))
    if isinstance(value, bpy.types.bpy_prop_array):
        return tuple(value)
    if hasattr(value, "to_list"):
        return tuple(value.to_list())
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return value


def values(prefs):
    return {
        name: normalize(getattr(prefs.props, name))
        for name in NAMES
    }


def expected_values():
    return {name: normalize(value) for name, _type, _size, value in CASES}


def finish(success):
    try:
        if after_load in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(after_load)
        if "pie_menu_editor" in bpy.context.preferences.addons:
            from pie_menu_editor.core.addon import get_prefs

            cleanup(get_prefs())
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_CHECKS", state["checks"], flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify_reenabled():
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        actual = values(prefs)
        state["checks"]["reenabled"] = addon_utils.check(
            "pie_menu_editor"
        ) == (True, True)
        state["checks"]["dynamic_properties_registered"] = all(
            hasattr(prefs.props.__class__, name) for name in NAMES
        )
        state["checks"]["reenable_values"] = actual == expected_values()
        print(TAG + "_REENABLE_VALUES", actual, flush=True)
        return finish(all(state["checks"].values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def reenable():
    try:
        addon_utils.enable(
            "pie_menu_editor",
            default_set=True,
            persistent=False,
            handle_error=None,
        )
        bpy.app.timers.register(verify_reenabled, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def verify_homefile():
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        actual = values(prefs)
        state["checks"]["load_post_seen"] = state["load_seen"]
        state["checks"]["empty_filepath"] = bpy.data.filepath == ""
        state["checks"]["homefile_values"] = actual == expected_values()
        print(TAG + "_HOMEFILE_VALUES", actual, flush=True)
        if not all(state["checks"].values()):
            return finish(False)

        addon_utils.disable(
            "pie_menu_editor",
            default_set=True,
            handle_error=None,
        )
        state["checks"]["disabled"] = (
            "pie_menu_editor" not in bpy.context.preferences.addons
        )
        bpy.app.timers.register(reenable, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


@persistent
def after_load(_):
    state["load_seen"] = True
    try:
        bpy.app.handlers.load_post.remove(after_load)
    except ValueError:
        pass
    bpy.app.timers.register(verify_homefile, first_interval=0.8)


def configure_property(prefs, name, prop_type, size, value):
    from pie_menu_editor.core.ed_property import (
        register_user_property,
        unregister_user_property,
    )

    menu = prefs.add_pm(mode="PROPERTY", name=name)
    unregister_user_property(menu)
    menu.poll_cmd = "ENUM" if prop_type == "ENUM_FLAG" else prop_type
    menu.set_data("vector", size)
    if prop_type in {"ENUM", "ENUM_FLAG"}:
        menu.set_data("mulsel", prop_type == "ENUM_FLAG")
        for identifier in ("ALPHA", "BETA", "GAMMA"):
            item = menu.pmis.add()
            item.name = identifier + "|" + identifier.title()
            item.mode = "PROP"
    register_user_property(menu)
    setattr(prefs.props, name, value)


def setup():
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        cleanup(prefs)
        for case in CASES:
            configure_property(prefs, *case)

        before = values(prefs)
        state["checks"]["assigned_values"] = before == expected_values()
        print(TAG + "_ASSIGNED_VALUES", before, flush=True)
        if not state["checks"]["assigned_values"]:
            return finish(False)

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
        bpy.app.timers.register(setup, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
