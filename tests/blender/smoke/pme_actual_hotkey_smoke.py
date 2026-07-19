from collections import Counter
import addon_utils
import bpy
import json
import os
from pathlib import Path
import traceback


TAG = "PME_ACTUAL_HOTKEY_SMOKE"
SOURCE = Path(os.environ["PME_ACTUAL_JSON"])
success = False
try:
    module = addon_utils.enable(
        "pie_menu_editor",
        default_set=True,
        persistent=False,
        handle_error=None,
    )
    package = module.core
    if not hasattr(bpy.types.WindowManager, "pme"):
        for waiter in package.PME_OT_wait_context.instances:
            waiter.cancelled = True
        package.on_context()

    result = bpy.ops.wm.pm_import(
        "EXEC_DEFAULT",
        filepath=str(SOURCE),
        mode="REPLACE",
        tags=TAG,
    )
    prefs = package.addon.get_prefs()
    imported = [pm for pm in prefs.pie_menus if pm.has_tag(TAG)]
    hotkey_menus = [
        pm
        for pm in imported
        if pm.ed.has_hotkey and pm.enabled and pm.key != "NONE"
    ]
    registered = []
    registration_errors = []
    keymap_counts = Counter()
    for pm in hotkey_menus:
        kmis = pm.kmis_map.get(pm.name)
        if not kmis:
            registration_errors.append((pm.name, "missing kmis_map"))
            continue
        registered.append(pm)
        for keymap_name, kmi in kmis.items():
            keymap_counts[keymap_name] += 1
            if kmi.idname != "wm.pme_user_pie_menu_call":
                registration_errors.append((pm.name, keymap_name, kmi.idname))
            if kmi.properties.pie_menu_name != pm.name:
                registration_errors.append(
                    (pm.name, keymap_name, kmi.properties.pie_menu_name)
                )
            if kmi.properties.keymap != keymap_name:
                registration_errors.append(
                    (pm.name, keymap_name, kmi.properties.keymap)
                )

    unresolved = {
        pm.name: pm.parse_keymap(False)
        for pm in hotkey_menus
        if pm.parse_keymap(False)
    }
    checks = {
        "import_finished": result == {"FINISHED"},
        "hotkeys_present": len(hotkey_menus) > 0,
        "all_registered": len(registered) == len(hotkey_menus),
        "no_registration_errors": not registration_errors,
        "no_unresolved_keymaps": not unresolved,
        "no_missing_keymaps": not prefs.missing_kms,
    }
    print(
        "PME_ACTUAL_HOTKEY_DATA",
        bpy.app.version_string,
        module.bl_info.get("version"),
        "imported=",
        len(imported),
        "hotkey_menus=",
        len(hotkey_menus),
        "registered=",
        len(registered),
        "keymaps=",
        dict(sorted(keymap_counts.items())),
        "names=",
        [pm.name for pm in hotkey_menus],
        flush=True,
    )
    print(
        "PME_ACTUAL_HOTKEY_ERRORS",
        registration_errors,
        "unresolved=",
        unresolved,
        "missing=",
        prefs.missing_kms,
        flush=True,
    )
    print("PME_ACTUAL_HOTKEY_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    print("PME_ACTUAL_HOTKEY_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
