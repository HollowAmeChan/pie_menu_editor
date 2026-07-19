import ast
import addon_utils
import bpy
import os
from pathlib import Path
import traceback


def read_expected_version():
    init_file = Path(__file__).resolve().parents[3] / "__init__.py"
    module = ast.parse(init_file.read_text(encoding="utf-8"), filename=str(init_file))
    for statement in module.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "bl_info"
            for target in statement.targets
        ):
            continue
        return tuple(ast.literal_eval(statement.value)["version"])
    raise RuntimeError(f"Unable to read add-on version from {init_file}")


TAG = "PME_RELEASE_ZIP_INSTALL_SMOKE"
ARCHIVE = Path(os.environ["PME_RELEASE_ZIP"])
EXPECTED_VERSION = read_expected_version()
checks = {}
success = False


def ensure_context(module):
    package = module.core
    if not hasattr(bpy.types.WindowManager, "pme"):
        for waiter in package.PME_OT_wait_context.instances:
            waiter.cancelled = True
        package.on_context()
    return package


try:
    install_result = bpy.ops.preferences.addon_install(
        "EXEC_DEFAULT",
        filepath=str(ARCHIVE),
        overwrite=True,
        enable_on_install=True,
        target="DEFAULT",
    )
    checks["install_finished"] = install_result == {"FINISHED"}

    modules = {module.__name__: module for module in addon_utils.modules(refresh=True)}
    module = modules.get("pie_menu_editor")
    checks["module_discovered"] = module is not None
    if module is None:
        raise RuntimeError("Installed pie_menu_editor module was not discovered")

    enabled_module = addon_utils.enable(
        "pie_menu_editor",
        default_set=True,
        persistent=False,
        handle_error=None,
    )
    checks["enable_returned_module"] = enabled_module is not None
    package = ensure_context(enabled_module)
    checks["version_matches"] = enabled_module.bl_info.get("version") == EXPECTED_VERSION
    checks["installed_from_user_scripts"] = (
        "scripts" in Path(enabled_module.__file__).parts
        and Path(enabled_module.__file__).name == "__init__.py"
    )
    checks["preferences_available"] = package.addon.get_prefs() is not None
    checks["first_enable_state"] = addon_utils.check("pie_menu_editor") == (True, True)

    addon_utils.disable("pie_menu_editor", default_set=True, handle_error=None)
    checks["disabled_state"] = addon_utils.check("pie_menu_editor") == (False, False)

    enabled_module = addon_utils.enable(
        "pie_menu_editor",
        default_set=True,
        persistent=False,
        handle_error=None,
    )
    package = ensure_context(enabled_module)
    checks["reenabled_state"] = addon_utils.check("pie_menu_editor") == (True, True)
    checks["reenabled_preferences"] = package.addon.get_prefs() is not None

    print(
        TAG + "_DATA",
        bpy.app.version_string,
        enabled_module.bl_info.get("version"),
        enabled_module.__file__,
        flush=True,
    )
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    print(TAG + "_CHECKS", checks, flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
