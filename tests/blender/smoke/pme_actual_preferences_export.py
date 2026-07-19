import addon_utils
import bpy
from collections import Counter
import json
import os
from pathlib import Path
import traceback


success = False
try:
    module = addon_utils.enable(
        "pie_menu_editor",
        default_set=True,
        persistent=False,
        handle_error=None,
    )
    package = getattr(module, "core", module)
    if not hasattr(bpy.types.WindowManager, "pme"):
        waiter_type = package.PME_OT_wait_context
        for waiter in waiter_type.instances:
            waiter.cancelled = True
        package.on_context()

    if hasattr(package.addon, "get_prefs"):
        preferences = package.addon.get_prefs()
    else:
        preferences = bpy.context.preferences.addons["pie_menu_editor"].preferences
    payload = preferences.get_export_data(export_tags=True, mode="ALL")
    output = Path(os.environ["PME_ACTUAL_EXPORT"])
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    modes = Counter(menu.mode for menu in preferences.pie_menus)
    names = [menu.name for menu in preferences.pie_menus]
    item_count = sum(len(menu.pmis) for menu in preferences.pie_menus)
    enabled_count = sum(menu.enabled for menu in preferences.pie_menus)
    checks = {
        "module": module is not None,
        "expected_path": os.path.normcase(module.__file__).startswith(
            os.path.normcase(os.environ["PME_EXPECTED_ADDON_ROOT"])
        ),
        "menus_present": len(names) > 0,
        "items_present": item_count > 0,
        "output_written": output.is_file() and output.stat().st_size > 0,
    }
    print(
        "PME_ACTUAL_EXPORT_DATA",
        bpy.app.version_string,
        module.bl_info.get("version"),
        "prefs_version=",
        tuple(preferences.version),
        "menus=",
        len(names),
        "items=",
        item_count,
        "enabled=",
        enabled_count,
        "modes=",
        dict(sorted(modes.items())),
        "first_names=",
        names[:10],
        "output=",
        str(output),
        flush=True,
    )
    print("PME_ACTUAL_EXPORT_CHECKS", checks, module.__file__, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    print("PME_ACTUAL_EXPORT_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
