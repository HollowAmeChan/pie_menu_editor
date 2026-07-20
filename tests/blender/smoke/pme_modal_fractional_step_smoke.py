import addon_utils
import bpy
import traceback


TAG = "PME_MODAL_FRACTIONAL_STEP_SMOKE"
MENU_NAME = "PME Modal Fractional Step Smoke"
PROP_NAME = "pme_modal_fractional_step_smoke"
success = False
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

    setattr(
        bpy.types.Scene,
        PROP_NAME,
        bpy.props.FloatProperty(default=0.0, min=-10.0, max=10.0),
    )
    prefs = package.addon.get_prefs()
    existing = prefs.pie_menus.get(MENU_NAME)
    if existing is not None:
        prefs.remove_pm(existing)
    menu = prefs.add_pm(mode="MODAL", name=MENU_NAME)
    item = menu.pmis.add()
    item.mode = "PROP"
    item.name = "Fractional Step"
    item.text = "C.scene." + PROP_NAME

    temp = package.addon.temp_prefs()
    temp.prop_data.clear()
    temp.prop_data.init(item.text, package.pme.context.gen_globals())
    temp.modal_item_hk.key = "MOUSEMOVE"
    temp.modal_item_prop_min = temp.prop_data.min
    temp.modal_item_prop_max = temp.prop_data.max
    temp.modal_item_prop_step_is_set = False
    temp.modal_item_prop_step = 0.3
    custom_step_marked = temp.modal_item_prop_step_is_set
    package.modal_utils.encode_modal_data(item)
    encoded_step = float(item.icon.split(";")[3])

    decoded = package.property_utils.PropertyData()
    decoded.init(item.text, package.pme.context.gen_globals())
    package.modal_utils.decode_modal_data(item, decoded)

    operator_type = package.operators.PME_OT_modal_base
    operator_type.prop_data.clear()
    operator = operator_type()
    operator.exec_globals = package.pme.context.gen_globals()
    operator.update_pmi = None
    operator.do_update = lambda: None
    operator.execute_prop_pmi(item, 1)
    value_after_increment = getattr(bpy.context.scene, PROP_NAME)
    operator.execute_prop_pmi(item, -1)
    value_after_decrement = getattr(bpy.context.scene, PROP_NAME)

    checks = {
        "rna_accepts_fraction": abs(temp.modal_item_prop_step - 0.3) < 1e-7,
        "custom_step_marked": custom_step_marked,
        "encoded_fraction": abs(encoded_step - 0.3) < 1e-7,
        "decoded_fraction": abs(decoded.step - 0.3) < 1e-7,
        "runtime_increment": abs(value_after_increment - 0.3) < 1e-7,
        "runtime_decrement": abs(value_after_decrement) < 1e-7,
    }
    print(
        TAG + "_DATA",
        bpy.app.version_string,
        module.bl_info.get("version"),
        item.icon,
        decoded.step,
        value_after_increment,
        value_after_decrement,
        flush=True,
    )
    print(TAG + "_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    try:
        if module is not None:
            prefs = module.core.addon.get_prefs()
            menu = prefs.pie_menus.get(MENU_NAME)
            if menu is not None:
                prefs.remove_pm(menu)
        if hasattr(bpy.types.Scene, PROP_NAME):
            delattr(bpy.types.Scene, PROP_NAME)
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
