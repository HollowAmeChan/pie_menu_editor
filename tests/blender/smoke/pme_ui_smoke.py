import addon_utils
import bpy
import traceback


def finish(success):
    print("PME_UI_SMOKE_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify_registration():
    try:
        from pie_menu_editor.core.extra_operators import preferences_panel_type

        preferences = bpy.context.preferences.addons.get("pie_menu_editor")
        sections = {
            item.identifier
            for item in bpy.context.preferences.bl_rna.properties[
                "active_section"
            ].enum_items
        }
        panel_map = {
            section: preferences_panel_type(section).__name__
            if preferences_panel_type(section)
            else None
            for section in sections
        }
        checks = {
            "preferences": preferences is not None,
            "window_manager_data": hasattr(bpy.types.WindowManager, "pme"),
            "menu_operator": hasattr(bpy.types, "WM_OT_pme_user_pie_menu_call"),
            "wait_operator": hasattr(bpy.types, "PME_OT_wait_context"),
            "preferences_panels": all(panel_map.values()),
        }
        print("PME_UI_SMOKE_CHECKS", checks, flush=True)
        print("PME_UI_PANEL_MAP", panel_map, flush=True)
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def open_preferences_popup():
    try:
        result = bpy.ops.pme.popup_user_preferences("INVOKE_DEFAULT", tab="INTERFACE")
        print("PME_UI_POPUP_RETURN", result, flush=True)
        bpy.app.timers.register(verify_registration, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


try:
    module = addon_utils.enable(
        "pie_menu_editor", default_set=True, persistent=False, handle_error=None
    )
    print(
        "PME_UI_ENABLE_RETURN",
        module.__name__ if module else None,
        module.__file__ if module else None,
        flush=True,
    )
    bpy.app.timers.register(open_preferences_popup, first_interval=1.0)
except Exception:
    traceback.print_exc()
    finish(False)
