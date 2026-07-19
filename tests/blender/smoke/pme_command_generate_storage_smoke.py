import addon_utils
import bpy
import traceback


MENU_NAME = "PME Command Generate Storage Smoke"
INITIAL_CMD = "bpy.ops.object.select_all(action='SELECT')"
EXPECTED_CMD = "bpy.ops.object.select_all(action='DESELECT')"


class ConfirmState:
    hotkey = False
    idx = 0
    ok = True


success = False
entered_mode = False
module = None
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

    menu = prefs.add_pm(mode="DIALOG", name=MENU_NAME)
    prefs.active_pie_menu_idx = prefs.pie_menus.find(menu.name)
    item = menu.pmis[0]
    item.mode = "COMMAND"
    item.text = INITIAL_CMD
    package.pme.context.edit_item_idx = 0

    prefs.enter_mode("PMI")
    entered_mode = True
    data = prefs.pmi_data
    menu.ed.on_pmi_pre_edit(menu, item, data)
    data.kmi.properties.action = "DESELECT"

    generate_result = bpy.ops.pme.pmi_cmd_generate(clear=False)
    generated_cmd = data.cmd
    custom_cmd = data.get("cmd", None)
    confirm_result = package.ed_base.WM_OT_pmi_data_edit.execute(
        ConfirmState(), bpy.context
    )
    entered_mode = False

    checks = {
        "operator_loaded": data.kmi.idname == "object.select_all",
        "generate_result": "PASS_THROUGH" in generate_result,
        "rna_command_updated": generated_cmd == EXPECTED_CMD,
        "confirm_result": "FINISHED" in confirm_result,
        "menu_item_updated": item.text == EXPECTED_CMD,
    }
    print(
        "PME_COMMAND_GENERATE_DATA",
        bpy.app.version_string,
        module.bl_info.get("version"),
        "generated=",
        generated_cmd,
        "custom=",
        custom_cmd,
        "saved=",
        item.text,
        flush=True,
    )
    print("PME_COMMAND_GENERATE_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    try:
        package = getattr(module, "core", None)
        if package is not None:
            prefs = package.addon.get_prefs()
            if entered_mode:
                prefs.leave_mode()
            menu = prefs.pie_menus.get(MENU_NAME)
            if menu is not None:
                prefs.remove_pm(menu)
    except Exception:
        traceback.print_exc()
        success = False
    print(
        "PME_COMMAND_GENERATE_RESULT",
        "OK" if success else "FAILED",
        flush=True,
    )
    bpy.ops.wm.quit_blender()
