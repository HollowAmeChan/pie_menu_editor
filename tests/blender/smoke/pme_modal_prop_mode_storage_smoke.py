import addon_utils
import bpy
import traceback


MENU_NAME = "PME Modal Property Mode Storage Smoke"
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

    prefs = package.addon.get_prefs()
    old = prefs.pie_menus.get(MENU_NAME)
    if old is not None:
        prefs.remove_pm(old)
    menu = prefs.add_pm(mode="MODAL", name=MENU_NAME)
    prefs.active_pie_menu_idx = prefs.pie_menus.find(menu.name)
    package.pme.context.edit_item_idx = 0

    data = prefs.pmi_data
    data.mode = "PROP"
    tpr = package.addon.temp_prefs()
    tpr.modal_item_prop_mode = "MOVE"
    before = (tpr.modal_item_prop_mode, tpr.modal_item_hk.key)
    data.mode = "COMMAND"
    after = (tpr.modal_item_prop_mode, tpr.modal_item_hk.key)
    custom_value = tpr.get("modal_item_prop_mode", None)

    checks = {
        "before_move": before == ("MOVE", "MOUSEMOVE"),
        "after_key": after == ("KEY", "NONE"),
    }
    print(
        "PME_MODAL_PROP_MODE_DATA",
        bpy.app.version_string,
        module.bl_info.get("version"),
        "before=",
        before,
        "after=",
        after,
        "custom=",
        custom_value,
        flush=True,
    )
    print("PME_MODAL_PROP_MODE_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    try:
        package = getattr(locals().get("module"), "core", None)
        if package is not None:
            prefs = package.addon.get_prefs()
            menu = prefs.pie_menus.get(MENU_NAME)
            if menu is not None:
                prefs.remove_pm(menu)
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_MODAL_PROP_MODE_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
