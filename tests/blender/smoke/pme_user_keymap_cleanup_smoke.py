import addon_utils
import bpy
import traceback


TAG = "PME_USER_KEYMAP_CLEANUP_SMOKE"
KEYMAP_NAME = "PME User Keymap Cleanup Smoke"
keymap = None
success = False


def property_state(kmi):
    properties = kmi.properties
    return {
        prop.identifier: {
            "set": properties.is_property_set(prop.identifier),
            "value": getattr(properties, prop.identifier),
            "default": prop.default,
        }
        for prop in properties.bl_rna.properties
        if prop.identifier != "rna_type"
    }


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

    user_keymaps = bpy.context.window_manager.keyconfigs.user.keymaps
    keymap = user_keymaps.new(name=KEYMAP_NAME, space_type="EMPTY")

    empty = keymap.keymap_items.new(
        "wm.pme_user_pie_menu_call", "F21", "PRESS"
    )
    explicit_defaults = keymap.keymap_items.new(
        "wm.pme_user_pie_menu_call", "F22", "PRESS"
    )
    explicit_defaults.properties.pie_menu_name = ""
    explicit_defaults.properties.invoke_mode = ""
    explicit_defaults.properties.keymap = ""
    explicit_defaults.properties.slot = -1
    valid = keymap.keymap_items.new(
        "wm.pme_user_pie_menu_call", "F23", "PRESS"
    )
    valid.properties.pie_menu_name = "PME Smoke Menu"
    valid.properties.invoke_mode = "HOTKEY"
    valid.properties.keymap = KEYMAP_NAME
    unrelated = keymap.keymap_items.new("wm.save_as_mainfile", "F24", "PRESS")

    empty_state = property_state(empty)
    explicit_default_state = property_state(explicit_defaults)
    valid_state = property_state(valid)
    removed = package.keymap_helper.remove_empty_pme_user_keymap_items()
    remaining = list(keymap.keymap_items)
    removed_again = package.keymap_helper.remove_empty_pme_user_keymap_items()

    checks = {
        "removed_empty_items": removed == 2,
        "cleanup_is_idempotent": removed_again == 0,
        "valid_item_preserved": valid in remaining,
        "valid_properties_preserved": (
            valid.properties.pie_menu_name == "PME Smoke Menu"
            and valid.properties.invoke_mode == "HOTKEY"
            and valid.properties.keymap == KEYMAP_NAME
        ),
        "unrelated_item_preserved": unrelated in remaining,
        "only_expected_items_remain": len(remaining) == 2,
    }
    print(
        TAG + "_DATA",
        bpy.app.version_string,
        "empty=",
        empty_state,
        "explicit_defaults=",
        explicit_default_state,
        "valid=",
        valid_state,
        "removed=",
        removed,
        flush=True,
    )
    print(TAG + "_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    try:
        if keymap is not None:
            user_keymaps = bpy.context.window_manager.keyconfigs.user.keymaps
            if KEYMAP_NAME in user_keymaps:
                user_keymaps.remove(user_keymaps[KEYMAP_NAME])
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
