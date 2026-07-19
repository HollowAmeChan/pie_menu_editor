import addon_utils
import bpy
import json
import tempfile
import traceback
from pathlib import Path


TAG = "PME_RT_SMOKE"
EXAMPLE_TAG = "PME_EXAMPLE_SMOKE"
OUTPUT = Path(tempfile.gettempdir()) / "pme_roundtrip.json"
preferences = None
expected = None


def tagged_names(tag):
    if not preferences:
        return []
    return [pm.name for pm in preferences.pie_menus if pm.has_tag(tag)]


def cleanup_tag(tag):
    for name in reversed(tagged_names(tag)):
        if name in preferences.pie_menus:
            preferences.remove_pm(preferences.pie_menus[name])


def finish(success):
    try:
        cleanup_tag(TAG)
        cleanup_tag(EXAMPLE_TAG)
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_IMPORT_EXPORT_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify_examples():
    try:
        imported = tagged_names(EXAMPLE_TAG)
        modes = sorted({preferences.pie_menus[name].mode for name in imported})
        checks = {
            "files_imported": len(imported) >= 11,
            "has_pmenu": "PMENU" in modes,
            "has_macro": "MACRO" in modes,
            "has_modal": "MODAL" in modes,
            "all_enabled": all(preferences.pie_menus[name].enabled for name in imported),
        }
        print("PME_EXAMPLE_IMPORT_CHECKS", checks, flush=True)
        print(
            "PME_EXAMPLE_IMPORT_DATA",
            {"count": len(imported), "modes": modes},
            flush=True,
        )
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def import_examples():
    try:
        import pie_menu_editor

        addon_root = Path(pie_menu_editor.__file__).parent
        files = sorted((addon_root / "examples").glob("*.json"))
        print("PME_EXAMPLE_IMPORT_FILES", len(files), flush=True)
        for filepath in files:
            result = bpy.ops.wm.pm_import(
                "EXEC_DEFAULT",
                filepath=str(filepath),
                mode="RENAME",
                tags=EXAMPLE_TAG,
            )
            if "FINISHED" not in result:
                return finish(False)
        bpy.app.timers.register(verify_examples, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def verify_roundtrip():
    try:
        actual = json.loads(
            json.dumps(preferences.get_export_data(mode="TAG", tag=TAG))
        )
        exact = actual == expected
        imported = tagged_names(TAG)
        modes = sorted(preferences.pie_menus[name].mode for name in imported)
        panel_registered = False
        prop_registered = False
        from pie_menu_editor.core import panel_utils

        for name in imported:
            pm = preferences.pie_menus[name]
            if pm.mode == "PANEL":
                panel_registered = bool(panel_utils._panels.get(name))
            elif pm.mode == "PROPERTY":
                prop_registered = hasattr(preferences.props.__class__, name)

        checks = {
            "exact_json_roundtrip": exact,
            "all_modes": len(imported) == 10 and len(set(modes)) == 10,
            "panel_registered": panel_registered,
            "property_registered": prop_registered,
            "disabled_preserved": any(
                not preferences.pie_menus[name].enabled for name in imported
            ),
        }
        print("PME_ROUNDTRIP_CHECKS", checks, flush=True)
        if not exact:
            print("PME_ROUNDTRIP_EXPECTED", json.dumps(expected, sort_keys=True), flush=True)
            print("PME_ROUNDTRIP_ACTUAL", json.dumps(actual, sort_keys=True), flush=True)
        if not all(checks.values()):
            return finish(False)
        cleanup_tag(TAG)
        bpy.app.timers.register(import_examples, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def import_roundtrip():
    try:
        result = bpy.ops.wm.pm_import(
            "EXEC_DEFAULT", filepath=str(OUTPUT), mode="REPLACE"
        )
        print("PME_IMPORT_RETURN", result, flush=True)
        if "FINISHED" not in result:
            return finish(False)
        bpy.app.timers.register(verify_roundtrip, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def export_roundtrip():
    global expected
    try:
        expected = json.loads(
            json.dumps(preferences.get_export_data(mode="TAG", tag=TAG))
        )
        result = bpy.ops.wm.pm_export(
            "EXEC_DEFAULT",
            filepath=str(OUTPUT),
            mode="TAG",
            tag=TAG,
            export_tags=True,
        )
        print("PME_EXPORT_RETURN", result, flush=True)
        if "FINISHED" not in result or not OUTPUT.is_file():
            return finish(False)
        written = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if written != expected:
            return finish(False)
        cleanup_tag(TAG)
        if tagged_names(TAG):
            return finish(False)
        bpy.app.timers.register(import_roundtrip, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def add_item(pm, name, mode, text, icon=""):
    pmi = pm.pmis.add()
    pmi.name = name
    pmi.mode = mode
    pmi.text = text
    pmi.icon = icon
    return pmi


def create_menus():
    global preferences
    try:
        from pie_menu_editor.core.addon import get_prefs

        preferences = get_prefs()
        modes = (
            "PMENU",
            "RMENU",
            "DIALOG",
            "SCRIPT",
            "MACRO",
            "MODAL",
            "STICKY",
            "PANEL",
            "HPANEL",
            "PROPERTY",
        )
        created_names = {}
        for index, mode in enumerate(modes):
            pm = preferences.add_pm(mode=mode, name=f"PMERT{mode}")
            pm.add_tag(TAG)
            created_names[mode] = pm.name
            if pm.ed.has_hotkey:
                pm.key = f"F{13 + index}"

        created = {
            mode: preferences.pie_menus[name]
            for mode, name in created_names.items()
        }

        pmenu = created["PMENU"]
        pmenu.open_mode = "CLICK_DRAG"
        pmenu.drag_dir = "SOUTH_EAST"
        pmenu.pmis[0].name = "Unicode \u83dc\u5355"
        pmenu.pmis[0].mode = "COMMAND"
        pmenu.pmis[0].text = "print('roundtrip')"

        created["RMENU"].pmis[0].text = "print('rmenu')"
        add_item(created["DIALOG"], "Dialog", "CUSTOM", "L.label(text='Round Trip')")
        created["SCRIPT"].pmis[0].text = "print('script')"
        created["MACRO"].pmis[0].text = "print('macro')"
        created["MODAL"].pmis[0].text = "print('modal invoke')"
        created["STICKY"].pmis[0].text = "print('sticky press')"
        created["STICKY"].pmis[1].text = "print('sticky release')"

        panel = created["PANEL"]
        panel.panel_space = "VIEW_3D"
        panel.panel_region = "UI"
        panel.panel_category = "PME RT"
        add_item(panel, "View", "MENU", "VIEW3D_MT_view")
        panel.update_panel_group()

        created["PROPERTY"].poll_cmd = "INT"
        created["PROPERTY"].ed.register_dynamic_props(created["PROPERTY"])
        created["HPANEL"].enabled = False

        print("PME_ROUNDTRIP_CREATED", sorted(created), flush=True)
        bpy.app.timers.register(export_roundtrip, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_IMPORT_EXPORT_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(create_menus, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
