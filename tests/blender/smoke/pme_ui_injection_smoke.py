import addon_utils
import bpy
import traceback


baseline_legacy_menu = None


def count_callback(tp, callback):
    funcs = getattr(tp.draw, "_draw_funcs", ())
    return sum(func is callback for func in funcs)


def finish(success):
    print("PME_UI_INJECTION_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify_disabled():
    try:
        checks = {
            "addon_disabled": "pie_menu_editor" not in bpy.context.preferences.addons,
            "legacy_menu_restored": (
                hasattr(bpy.types, "WM_MT_button_context") == baseline_legacy_menu
            ),
            "wm_data_removed": not hasattr(bpy.types.WindowManager, "pme"),
        }
        print("PME_UI_INJECTION_DISABLED", checks, flush=True)
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def run_checks():
    try:
        from pie_menu_editor.core.addon import get_prefs
        from pie_menu_editor.core.ed_panel_group import PME_OT_interactive_panels_toggle
        from pie_menu_editor.core import preferences as preferences_module
        from pie_menu_editor.core.preferences import button_context_menu

        preferences = get_prefs()
        panel_tp = bpy.types.VIEW3D_PT_view3d_properties
        menu_tp = bpy.types.VIEW3D_MT_view
        header_tp = bpy.types.VIEW3D_HT_header
        targets = (
            (panel_tp, PME_OT_interactive_panels_toggle._draw),
            (menu_tp, PME_OT_interactive_panels_toggle._draw_menu),
            (header_tp, PME_OT_interactive_panels_toggle._draw_header),
        )

        cycles = []
        for _ in range(2):
            preferences.interactive_panels = True
            enabled_counts = [count_callback(tp, callback) for tp, callback in targets]
            preferences.interactive_panels = False
            disabled_counts = [count_callback(tp, callback) for tp, callback in targets]
            cycles.append((enabled_counts, disabled_counts))

        hook_tp = preferences_module._button_context_menu_type
        rmb_count = count_callback(hook_tp, button_context_menu) if hook_tp else 0

        window = bpy.context.window
        area = next((item for item in window.screen.areas if item.type == "VIEW_3D"), None)
        region = next((item for item in area.regions if item.type == "WINDOW"), None)
        with bpy.context.temp_override(
            window=window, screen=window.screen, area=area, region=region
        ):
            menu_result = bpy.ops.wm.call_menu(name="UI_MT_button_context_menu")

        checks = {
            "modern_button_menu_hook": (
                hook_tp is bpy.types.UI_MT_button_context_menu
            ),
            "rmb_callback_once": rmb_count == 1,
            "interactive_cycles": all(
                enabled == [1, 1, 1] and disabled == [0, 0, 0]
                for enabled, disabled in cycles
            ),
            "button_menu_called": "INTERFACE" in menu_result,
        }
        print("PME_UI_INJECTION_CHECKS", checks, flush=True)
        print("PME_UI_INJECTION_CYCLES", cycles, flush=True)
        print("PME_UI_INJECTION_MENU_RETURN", menu_result, flush=True)
        if not all(checks.values()):
            return finish(False)

        addon_utils.disable("pie_menu_editor", default_set=True, handle_error=None)
        bpy.app.timers.register(verify_disabled, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    global baseline_legacy_menu
    try:
        baseline_legacy_menu = hasattr(bpy.types, "WM_MT_button_context")
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_UI_INJECTION_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run_checks, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
