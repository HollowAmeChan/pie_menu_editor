import addon_utils
import bpy
import os
import traceback


zip_path = os.environ["PME_RELEASE_ZIP"]
try:
    install_result = bpy.ops.preferences.addon_install(
        filepath=zip_path,
        overwrite=True,
    )
    addon_utils.modules(refresh=True)
    module = addon_utils.enable(
        "pie_menu_editor", default_set=True, persistent=False, handle_error=None
    )
    checks = {
        "install_finished": "FINISHED" in install_result,
        "module_enabled": module is not None,
        "module_name": module is not None and module.__name__ == "pie_menu_editor",
        "root_name": module is not None
        and os.path.basename(os.path.dirname(module.__file__)) == "pie_menu_editor",
        "preferences": "pie_menu_editor" in bpy.context.preferences.addons,
    }
    print("PME_ZIP_INSTALL_RETURN", install_result, flush=True)
    print("PME_ZIP_INSTALL_MODULE", module.__file__ if module else None, flush=True)
    print("PME_ZIP_INSTALL_CHECKS", checks, flush=True)
    print(
        "PME_ZIP_INSTALL_RESULT",
        "OK" if all(checks.values()) else "FAILED",
        flush=True,
    )
except Exception:
    traceback.print_exc()
    print("PME_ZIP_INSTALL_RESULT FAILED", flush=True)
