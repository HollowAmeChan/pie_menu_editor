import addon_utils
import bpy
import traceback


def finish(success):
    print("PME_FEATURE_SMOKE_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def run_feature_checks():
    try:
        from pie_menu_editor.core import property_utils
        from pie_menu_editor.core.addon import get_prefs

        preferences = get_prefs()
        before = len(preferences.pie_menus)
        pie_menu = preferences.add_pm(mode="PMENU", name="API Smoke")
        pmi_count = len(pie_menu.pmis)
        pie_menu.key = "A"
        pie_menu.km_name = "Window"
        pie_menu.register_hotkey()
        keymap_registered = bool(pie_menu.kmis_map.get(pie_menu.name))
        snapshot = property_utils.to_dict(pie_menu)
        property_utils.from_dict(pie_menu, snapshot)
        after_roundtrip = property_utils.to_dict(pie_menu)
        created_count = len(preferences.pie_menus)
        pie_menu.unregister_hotkey()
        preferences.remove_pm(pie_menu)
        checks = {
            "created": created_count == before + 1,
            "default_pmi": pmi_count > 0,
            "keymap_registered": keymap_registered,
            "serialized": isinstance(snapshot, dict),
            "roundtrip": isinstance(after_roundtrip, dict),
            "removed": len(preferences.pie_menus) == before,
        }
        print("PME_FEATURE_SMOKE_CHECKS", checks, flush=True)
        print(
            "PME_FEATURE_SMOKE_DATA",
            {
                "pmi_count": pmi_count,
                "keymap_registered": keymap_registered,
                "snapshot_keys": sorted(snapshot),
            },
            flush=True,
        )
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def enable_and_wait():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_FEATURE_ENABLE_RETURN", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run_feature_checks, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable_and_wait, first_interval=0.2)
