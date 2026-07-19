import addon_utils
import bpy
import os
from pathlib import Path
import traceback


TAG = "PME_EDITOR_KEYMAP_SMOKE"
FIXTURE = Path(os.environ["PME_KEYMAP_FIXTURE"])
EXPECTED = {
    "PME KM 3D View": ["3D View"],
    "PME KM 3D View Generic": ["3D View Generic"],
    "PME KM Object": ["Object Non-modal"],
    "PME KM Mesh": ["Mesh"],
    "PME KM Sculpt": ["Sculpt"],
    "PME KM Node": ["Node Editor"],
    "PME KM Image": ["Image"],
    "PME KM Image Generic": ["Image Generic"],
    "PME KM Multi": ["3D View", "Node Editor"],
}
checks = {}
errors = []
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
        filepath=str(FIXTURE),
        mode="REPLACE",
        tags=TAG,
    )
    prefs = package.addon.get_prefs()
    imported = [pm for pm in prefs.pie_menus if pm.has_tag(TAG)]
    actual = {}
    for pm in imported:
        parsed = pm.parse_keymap()
        missing = pm.parse_keymap(False)
        kmis = pm.kmis_map.get(pm.name) or {}
        actual[pm.name] = {
            "stored": pm.km_name,
            "parsed": parsed,
            "missing": missing,
            "registered": sorted(kmis),
        }
        expected = EXPECTED[pm.name]
        if parsed != expected:
            errors.append((pm.name, "parsed", parsed, expected))
        if missing:
            errors.append((pm.name, "missing", missing))
        if sorted(kmis) != sorted(expected):
            errors.append((pm.name, "registered", sorted(kmis), expected))
        for keymap_name, kmi in kmis.items():
            if kmi.idname != "wm.pme_user_pie_menu_call":
                errors.append((pm.name, keymap_name, "idname", kmi.idname))
            if kmi.properties.pie_menu_name != pm.name:
                errors.append(
                    (pm.name, keymap_name, "menu", kmi.properties.pie_menu_name)
                )
            if kmi.properties.keymap != keymap_name:
                errors.append(
                    (pm.name, keymap_name, "keymap", kmi.properties.keymap)
                )

    checks["import_finished"] = result == {"FINISHED"}
    checks["all_imported"] = len(imported) == len(EXPECTED)
    checks["no_registration_errors"] = not errors
    checks["no_missing_keymaps"] = not prefs.missing_kms
    print(
        TAG + "_DATA",
        bpy.app.version_string,
        module.bl_info.get("version"),
        actual,
        flush=True,
    )
    print(TAG + "_ERRORS", errors, "prefs_missing=", prefs.missing_kms, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    print(TAG + "_CHECKS", checks, flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
