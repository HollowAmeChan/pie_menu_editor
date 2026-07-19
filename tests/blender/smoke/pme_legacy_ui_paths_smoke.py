import addon_utils
import bpy
import traceback


state = {}


def view3d_override():
    window = bpy.context.window
    if not window:
        return None
    for area in window.screen.areas:
        if area.type == "VIEW_3D":
            region = next((item for item in area.regions if item.type == "WINDOW"), None)
            if region:
                return {
                    "window": window,
                    "screen": window.screen,
                    "area": area,
                    "region": region,
                }
    return None


def finish(success):
    try:
        if "pie_menu_editor" in bpy.context.preferences.addons:
            from pie_menu_editor.core.ui import is_userpref_maximized

            if is_userpref_maximized():
                bpy.ops.pme.userpref_restore()
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_LEGACY_UI_STATE", state, flush=True)
    print("PME_LEGACY_UI_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify_panel_popup():
    return finish(bool(state.get("panel_popup")))


def open_panel_popup():
    try:
        panel = next(
            (
                name
                for name in (
                    "VIEW3D_PT_view3d_properties",
                    "VIEW3D_PT_view3d_cursor",
                )
                if hasattr(bpy.types, name)
            ),
            None,
        )
        print("PME_LEGACY_PANEL_TYPE", panel, flush=True)
        if not panel:
            return finish(False)
        override = view3d_override()
        if not override:
            return finish(False)
        with bpy.context.temp_override(**override):
            result = bpy.ops.pme.popup_panel(
                "INVOKE_DEFAULT", panel=panel, area="VIEW_3D", header=True, frame=True
            )
        state["panel_popup"] = "RUNNING_MODAL" in result
        print("PME_LEGACY_PANEL_POPUP_RETURN", result, flush=True)
        bpy.app.timers.register(verify_panel_popup, first_interval=2.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def verify_maximized():
    try:
        from pie_menu_editor.core.ui import is_userpref_maximized

        maximized = is_userpref_maximized()
        state["maximized"] = maximized
        print("PME_LEGACY_MAXIMIZED", maximized, flush=True)
        if not maximized:
            return finish(False)
        result = bpy.ops.pme.userpref_restore()
        state["restored"] = not is_userpref_maximized()
        print("PME_LEGACY_RESTORE_RETURN", result, flush=True)
        if not state["restored"]:
            return finish(False)
        bpy.app.timers.register(open_panel_popup, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def maximize_preferences():
    try:
        override = view3d_override()
        if not override:
            return finish(False)
        with bpy.context.temp_override(**override):
            result = bpy.ops.pme.userpref_show(addon="pie_menu_editor")
        state["maximize_return"] = set(result)
        print("PME_LEGACY_MAXIMIZE_RETURN", result, flush=True)
        bpy.app.timers.register(verify_maximized, first_interval=2.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_LEGACY_UI_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(maximize_preferences, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
