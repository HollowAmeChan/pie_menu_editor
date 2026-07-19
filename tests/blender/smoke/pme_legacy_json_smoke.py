import addon_utils
import bpy
import json
import tempfile
import traceback
from pathlib import Path


FILEPATH = Path(tempfile.gettempdir()) / "pme_legacy_1136.json"
NAMES = ("PME Legacy Pie", "PME Legacy Sticky")
preferences = None


def cleanup():
    if not preferences:
        return
    for name in reversed(NAMES):
        if name in preferences.pie_menus:
            preferences.remove_pm(preferences.pie_menus[name])


def finish(success):
    try:
        cleanup()
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_LEGACY_JSON_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def run():
    global preferences
    try:
        from pie_menu_editor.core.addon import get_prefs

        preferences = get_prefs()
        cleanup()
        legacy = [
            [
                NAMES[0],
                "3D View, Object Mode",
                "F13",
                [["Legacy", "COMMAND", "", "print('legacy pie')", 0]],
                "PMENU",
                "pm?",
                "PRESS",
                "",
                "",
            ],
            [
                NAMES[1],
                "Window",
                "F14",
                [
                    ["On Press", "COMMAND", "", "print('press')", 0],
                    ["On Release", "COMMAND", "", "print('release')", 0],
                ],
                "STICKY",
                "sk?block_ui=True",
                "PRESS",
                "",
                "",
            ],
        ]
        FILEPATH.write_text(json.dumps(legacy), encoding="utf-8")
        result = bpy.ops.wm.pm_import(
            "EXEC_DEFAULT", filepath=str(FILEPATH), mode="REPLACE"
        )
        pie = preferences.pie_menus.get(NAMES[0])
        sticky = preferences.pie_menus.get(NAMES[1])
        checks = {
            "operator_finished": "FINISHED" in result,
            "pie_imported": pie is not None,
            "pie_slots_migrated": pie is not None and len(pie.pmis) == 10,
            "keymap_separator_migrated": pie is not None
            and "3D View; Object Mode" == pie.km_name,
            "sticky_imported": sticky is not None,
            "sticky_field_migrated": sticky is not None
            and "sk_block_ui=True" in sticky.data
            and "?block_ui" not in sticky.data,
            "sticky_items": sticky is not None and len(sticky.pmis) == 2,
        }
        print("PME_LEGACY_JSON_CHECKS", checks, flush=True)
        print(
            "PME_LEGACY_JSON_DATA",
            {
                "pie_slots": len(pie.pmis) if pie else None,
                "pie_keymap": pie.km_name if pie else None,
                "sticky_data": sticky.data if sticky else None,
            },
            flush=True,
        )
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_LEGACY_JSON_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
