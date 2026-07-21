import addon_utils
import bpy
import os
import traceback


TAG = "PME_STARTUP_HOTKEY_REFRESH_SMOKE"
NAME = "PME Startup Hotkey Refresh"
CORRUPT_NAME = "PME Active Hotkey Repair"
PHASE = os.environ.get("PME_STARTUP_HOTKEY_PHASE", "WRITE").upper()
preferences = None


def matching_items(keyconfig, expected_name=NAME):
    found = []
    if keyconfig is None:
        return found
    for keymap in keyconfig.keymaps:
        for item in keymap.keymap_items:
            if item.idname != "wm.pme_user_pie_menu_call":
                continue
            try:
                menu_name = item.properties.pie_menu_name
            except (AttributeError, ReferenceError, RuntimeError, TypeError):
                continue
            if menu_name == expected_name:
                found.append(item)
    return found


def remove_menu(name=NAME):
    if preferences and name in preferences.pie_menus:
        preferences.remove_pm(preferences.pie_menus[name])


def finish(success, phase):
    print(
        TAG + "_RESULT",
        "OK" if success else "FAILED",
        "phase=",
        phase,
        flush=True,
    )
    bpy.ops.wm.quit_blender()
    return None


def write_phase():
    try:
        remove_menu()
        menu = preferences.add_pm(mode="PMENU", name=NAME)
        menu.add_tag(TAG)
        menu.km_name = "Window"
        menu.key = "F19"
        menu.open_mode = "PRESS"
        bpy.context.window_manager.keyconfigs.update()
        bpy.ops.wm.save_userpref()
        addon_items = matching_items(bpy.context.window_manager.keyconfigs.addon)
        user_items = matching_items(bpy.context.window_manager.keyconfigs.user)
        checks = {
            "menu_created": NAME in preferences.pie_menus,
            "addon_kmi_created": len(addon_items) == 1,
            "user_kmi_materialized": len(user_items) == 1,
        }
        print(TAG + "_WRITE_CHECKS", checks, flush=True)
        return finish(all(checks.values()), "WRITE")
    except Exception:
        traceback.print_exc()
        return finish(False, "WRITE")


def read_phase():
    try:
        from pie_menu_editor.core import keymap_helper

        menu = preferences.pie_menus.get(NAME)
        addon_items = matching_items(bpy.context.window_manager.keyconfigs.addon)
        user_items = matching_items(bpy.context.window_manager.keyconfigs.user)
        checks = {
            "menu_restored": menu is not None,
            "addon_kmi_restored": len(addon_items) == 1,
            "user_kmi_refreshed": len(user_items) == 1,
            "event_restored": bool(
                user_items
                and user_items[0].type == "F19"
                and user_items[0].value == "PRESS"
                and user_items[0].active
            ),
        }

        remove_menu(CORRUPT_NAME)
        corrupt = preferences.add_pm(mode="PMENU", name=CORRUPT_NAME)
        corrupt.km_name = "Window"
        corrupt.key = "F20"
        active_keymap = bpy.context.window_manager.keyconfigs.active.keymaps.get(
            "Window"
        )
        active_keymap.keymap_items.new(
            "wm.pme_user_pie_menu_call", "F20", "PRESS"
        )
        removed = keymap_helper.remove_empty_pme_user_keymap_items()
        rebuilt = keymap_helper.rebuild_pme_user_keymap_items()
        repaired_items = matching_items(
            bpy.context.window_manager.keyconfigs.user, CORRUPT_NAME
        )
        checks.update(
            {
                "stale_active_kmi_removed": removed >= 1,
                "user_kmi_repaired": len(repaired_items) == 1,
                "rebuilt_event_matches": bool(
                    repaired_items
                    and repaired_items[0].type == "F20"
                    and repaired_items[0].value == "PRESS"
                    and repaired_items[0].active
                ),
            }
        )
        print(
            TAG + "_READ_DATA",
            bpy.app.version_string,
            "addon=",
            len(addon_items),
            "user=",
            len(user_items),
            "removed=",
            removed,
            "rebuilt=",
            rebuilt,
            flush=True,
        )
        print(TAG + "_READ_CHECKS", checks, flush=True)
        success = all(checks.values())
        remove_menu(CORRUPT_NAME)
        user_keymaps = bpy.context.window_manager.keyconfigs.user.keymaps
        for keymap in user_keymaps:
            for item in list(keymap.keymap_items):
                if item.idname != "wm.pme_user_pie_menu_call":
                    continue
                try:
                    if item.properties.pie_menu_name == CORRUPT_NAME:
                        keymap.keymap_items.remove(item)
                except (AttributeError, ReferenceError, RuntimeError, TypeError):
                    continue
        remove_menu()
        bpy.context.window_manager.keyconfigs.update()
        bpy.ops.wm.save_userpref()
        return finish(success, "READ")
    except Exception:
        traceback.print_exc()
        return finish(False, "READ")


def run():
    global preferences
    try:
        from pie_menu_editor.core.addon import get_prefs

        preferences = get_prefs()
        if PHASE == "WRITE":
            return write_phase()
        if PHASE == "READ":
            return read_phase()
        print(TAG + "_ERROR", "Unknown phase", PHASE, flush=True)
        return finish(False, PHASE)
    except Exception:
        traceback.print_exc()
        return finish(False, PHASE)


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor",
            default_set=True,
            persistent=False,
            handle_error=None,
        )
        print(
            TAG + "_ENABLE",
            module.__file__ if module else None,
            module.bl_info.get("version") if module else None,
            flush=True,
        )
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False, PHASE)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
