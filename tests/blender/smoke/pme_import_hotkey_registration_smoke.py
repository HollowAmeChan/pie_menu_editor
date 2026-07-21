import addon_utils
import bpy
import json
import os
import tempfile
import traceback
from pathlib import Path


TAG = "PME_IMPORT_HOTKEY_REGISTRATION_SMOKE"
SOURCE_ENV = "PME_IMPORT_HOTKEY_JSON"
DEFAULT_SOURCE = Path(tempfile.gettempdir()) / "pme_import_hotkey_fixture.json"
preferences = None
original_restore_mouse_pos = None
verification = {}


def default_data():
    empty_items = [[""] for _index in range(10)]
    return {
        "version": "1.18.6",
        "menus": [
            [
                "PME Import Hotkey W",
                "Window",
                "W, NONE",
                empty_items,
                "PMENU",
                "pm?",
                "PRESS",
                "",
                "",
            ],
            [
                "PME Import Hotkey Space",
                "Window",
                "shift+SPACE, NONE",
                empty_items,
                "PMENU",
                "pm?",
                "PRESS",
                "",
                "",
            ],
        ],
    }


def source_path():
    configured = os.environ.get(SOURCE_ENV)
    if configured:
        return Path(configured)
    DEFAULT_SOURCE.write_text(json.dumps(default_data()), encoding="utf-8")
    return DEFAULT_SOURCE


def hotkey_specs(source):
    data = json.loads(source.read_text(encoding="utf-8"))
    menus = data if isinstance(data, list) else data["menus"]
    return {
        menu[0]: (menu[1], menu[2])
        for menu in menus
        if len(menu) > 4 and menu[2] and menu[4] in {"PMENU", "RMENU", "STICKY"}
    }


def cleanup():
    global original_restore_mouse_pos
    if not preferences:
        return
    if original_restore_mouse_pos is not None:
        preferences.restore_mouse_pos = original_restore_mouse_pos
        original_restore_mouse_pos = None
    for pm in list(preferences.pie_menus)[::-1]:
        if pm.has_tag(TAG):
            preferences.remove_pm(pm)


def keyconfig_items(keyconfig, menu_names):
    if keyconfig is None:
        return []
    found = []
    for keymap in keyconfig.keymaps:
        for kmi in keymap.keymap_items:
            if kmi.idname != "wm.pme_user_pie_menu_call":
                continue
            try:
                menu_name = kmi.properties.pie_menu_name
            except (AttributeError, ReferenceError, RuntimeError, TypeError):
                menu_name = None
            if menu_name not in menu_names:
                continue
            found.append(
                (
                    menu_name,
                    keymap.name,
                    kmi.type,
                    kmi.value,
                    kmi.ctrl,
                    kmi.shift,
                    kmi.alt,
                    kmi.oskey,
                    kmi.active,
                )
            )
    return found


def view3d_context():
    window = bpy.context.window
    if window is None:
        return None
    for area in window.screen.areas:
        if area.type != "VIEW_3D":
            continue
        region = next((item for item in area.regions if item.type == "WINDOW"), None)
        if region is not None:
            return {
                "window": window,
                "screen": window.screen,
                "area": area,
                "region": region,
            }
    return None


def stop_active_calls():
    from pie_menu_editor.core.operators import WM_OT_pme_user_pie_menu_call

    for active in list(WM_OT_pme_user_pie_menu_call.active_ops.values()):
        active.cancelled = True
        active.modal_stop()


def report_results():
    try:
        stop_active_calls()
        checks = verification["checks"]
        checks["all_menus_callable"] = (
            len(verification["call_results"]) == len(verification["specs"])
            and not verification["call_errors"]
        )
        print(
            "PME_IMPORT_HOTKEY_REGISTRATION_DATA",
            bpy.app.version_string,
            "source=",
            str(verification["source"]),
            "hotkeys=",
            len(verification["specs"]),
            "registered=",
            verification["registered"],
            "names=",
            sorted(verification["specs"]),
            flush=True,
        )
        print(
            "PME_IMPORT_HOTKEY_REGISTRATION_ERRORS",
            verification["registration_errors"],
            flush=True,
        )
        print(
            "PME_IMPORT_HOTKEY_REGISTRATION_KEYCONFIGS",
            verification["keyconfig_state"],
            flush=True,
        )
        print(
            "PME_IMPORT_HOTKEY_REGISTRATION_CALLS",
            {
                "results": verification["call_results"],
                "errors": verification["call_errors"],
            },
            flush=True,
        )
        print("PME_IMPORT_HOTKEY_REGISTRATION_CHECKS", checks, flush=True)
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def invoke_next_menu():
    try:
        stop_active_calls()
        pending = verification["pending_calls"]
        if not pending:
            bpy.app.timers.register(report_results, first_interval=0.5)
            return None
        name = pending.pop(0)
        pm = verification["imported"].get(name)
        override = view3d_context()
        if pm is None or override is None:
            verification["call_errors"].append((name, "missing menu or context"))
            return 0.4
        with bpy.context.temp_override(**override):
            result = bpy.ops.wm.pme_user_pie_menu_call(
                "INVOKE_DEFAULT",
                pie_menu_name=name,
                invoke_mode="HOTKEY",
                keymap=pm.km_name,
            )
        verification["call_results"][name] = result
        return 0.4
    except Exception as exc:
        verification["call_errors"].append(
            (verification["pending_calls"], type(exc).__name__, str(exc))
        )
        return 0.4


def finish(success):
    try:
        cleanup()
    except Exception:
        traceback.print_exc()
        success = False
    print(
        "PME_IMPORT_HOTKEY_REGISTRATION_RESULT",
        "OK" if success else "FAILED",
        flush=True,
    )
    bpy.ops.wm.quit_blender()
    return None


def run():
    global original_restore_mouse_pos, preferences
    try:
        from pie_menu_editor.core import keymap_helper
        from pie_menu_editor.core.addon import get_prefs

        preferences = get_prefs()
        cleanup()
        source = source_path()
        specs = hotkey_specs(source)
        result = bpy.ops.wm.pm_import(
            "EXEC_DEFAULT",
            filepath=str(source),
            mode="REPLACE",
            tags=TAG,
        )
        imported = {
            pm.name: pm for pm in preferences.pie_menus if pm.has_tag(TAG)
        }
        addon_keyconfig = bpy.context.window_manager.keyconfigs.addon
        window_keymap = addon_keyconfig.keymaps.get("Window")
        keymap_items = [] if window_keymap is None else list(window_keymap.keymap_items)

        missing_maps = []
        mismatches = []
        matching_items = []
        for name, (keymap_name, hotkey) in specs.items():
            pm = imported.get(name)
            if pm is None:
                mismatches.append((name, "menu missing"))
                continue
            mapped = pm.kmis_map.get(name) or {}
            if keymap_name not in mapped:
                missing_maps.append(name)

            parsed = keymap_helper.parse_hotkey(hotkey)
            expected_key, ctrl, shift, alt, oskey, any_mod, key_mod, _chord = parsed
            candidates = [
                kmi
                for kmi in keymap_items
                if kmi.idname == "wm.pme_user_pie_menu_call"
                and kmi.properties.pie_menu_name == name
            ]
            if len(candidates) != 1:
                mismatches.append((name, "kmi count", len(candidates)))
                continue
            kmi = candidates[0]
            matching_items.append(kmi)
            actual = (
                kmi.type,
                kmi.ctrl,
                kmi.shift,
                kmi.alt,
                kmi.oskey,
                kmi.any,
                kmi.key_modifier,
                kmi.value,
                kmi.properties.keymap,
            )
            expected = (
                expected_key,
                ctrl,
                shift,
                alt,
                oskey,
                any_mod,
                key_mod,
                "PRESS",
                keymap_name,
            )
            if actual != expected:
                mismatches.append((name, actual, expected))

        checks = {
            "operator_finished": result == {"FINISHED"},
            "hotkeys_in_source": bool(specs),
            "all_hotkey_menus_imported": all(name in imported for name in specs),
            "all_kmis_mapped": not missing_maps,
            "all_kmis_created_once": len(matching_items) == len(specs),
            "all_kmi_fields_match": not mismatches,
            "all_addon_kmis_active": all(kmi.active for kmi in matching_items),
        }
        keyconfig_state = {
            name: keyconfig_items(getattr(bpy.context.window_manager.keyconfigs, name), specs)
            for name in ("addon", "user", "active")
        }

        original_restore_mouse_pos = preferences.restore_mouse_pos
        preferences.restore_mouse_pos = False
        verification.clear()
        verification.update(
            {
                "source": source,
                "specs": specs,
                "imported": imported,
                "registered": len(matching_items),
                "checks": checks,
                "registration_errors": {
                    "missing_maps": missing_maps,
                    "mismatches": mismatches,
                },
                "keyconfig_state": keyconfig_state,
                "pending_calls": list(specs),
                "call_results": {},
                "call_errors": [],
            }
        )
        bpy.app.timers.register(invoke_next_menu, first_interval=0.1)
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
        print(
            "PME_IMPORT_HOTKEY_REGISTRATION_ENABLE",
            module.__file__ if module else None,
            flush=True,
        )
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
