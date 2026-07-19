import addon_utils
import bpy
import traceback
from types import SimpleNamespace


success = False
try:
    module = addon_utils.enable(
        "pie_menu_editor",
        default_set=True,
        persistent=False,
        handle_error=None,
    )
    if not hasattr(bpy.types.WindowManager, "pme"):
        for waiter in module.core.PME_OT_wait_context.instances:
            waiter.cancelled = True
        module.core.on_context()

    preferences = module.core.preferences
    temp_data = bpy.context.window_manager.pme
    temp_data.modal_item_prop_mode = "WHEEL"

    original_get_prefs = preferences.get_prefs
    original_temp_prefs = preferences.temp_prefs
    preferences.get_prefs = lambda: SimpleNamespace(
        selected_pm=SimpleNamespace(mode="MODAL")
    )
    preferences.temp_prefs = lambda: temp_data
    try:
        item = SimpleNamespace(
            mode="COMMAND",
            check_pmi_errors=lambda context: None,
        )
        preferences.PMIData.mode_update(item, bpy.context)
    finally:
        preferences.get_prefs = original_get_prefs
        preferences.temp_prefs = original_temp_prefs

    print(
        "PME_MODAL_PROP_MODE_VALUES",
        bpy.app.version_string,
        "rna=",
        temp_data.modal_item_prop_mode,
        "keys=",
        list(temp_data.keys()),
        "custom=",
        temp_data.get("modal_item_prop_mode", None),
        flush=True,
    )
    success = temp_data.modal_item_prop_mode == "KEY"
except Exception:
    traceback.print_exc()
finally:
    print(
        "PME_MODAL_PROP_MODE_RESULT",
        "OK" if success else "FAILED",
        flush=True,
    )
    bpy.ops.wm.quit_blender()
