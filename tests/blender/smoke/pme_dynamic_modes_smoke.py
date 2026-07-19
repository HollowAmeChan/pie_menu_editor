import addon_utils
import bpy
import traceback
from types import SimpleNamespace


preferences = None
names = []
state = {}
hidden_panel_name = None
event_xy = (100, 100)


def log(name, value):
    print(name, value, flush=True)


def cleanup():
    global hidden_panel_name
    try:
        from pie_menu_editor.core import panel_utils
        from pie_menu_editor.core.operators import (
            PME_OT_modal_base,
            PME_OT_sticky_key,
        )

        active = PME_OT_modal_base.active
        if active:
            try:
                active.do_cancel()
            except Exception:
                traceback.print_exc()
            PME_OT_modal_base.active = None

        PME_OT_sticky_key.root_instance = None
        PME_OT_sticky_key.active_instance = None
        PME_OT_sticky_key.idx = 0

        if hidden_panel_name and panel_utils.is_panel_hidden(hidden_panel_name):
            panel_utils.unhide_panel(hidden_panel_name)

        if preferences:
            for name in reversed(names):
                if name in preferences.pie_menus:
                    preferences.remove_pm(preferences.pie_menus[name])
    except Exception:
        traceback.print_exc()


def finish(success):
    cleanup()
    log("PME_DYNAMIC_MODES_STATE", state)
    log("PME_DYNAMIC_MODES_RESULT", "OK" if success else "FAILED")
    bpy.ops.wm.quit_blender()
    return None


def find_view3d_context():
    window = bpy.context.window
    if not window:
        return None
    for area in window.screen.areas:
        if area.type != "VIEW_3D":
            continue
        region = next((r for r in area.regions if r.type == "WINDOW"), None)
        if region:
            return {"window": window, "screen": window.screen, "area": area, "region": region}
    return None


def verify_sticky():
    ok = state.get("sticky_press") == 1 and state.get("sticky_release") == 1
    log("PME_STICKY_CHECK", ok)
    return finish(ok)


def sticky_release():
    try:
        bpy.context.window.event_simulate(
            type="F13", value="RELEASE", x=event_xy[0], y=event_xy[1]
        )
        bpy.app.timers.register(verify_sticky, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def sticky_press():
    try:
        bpy.context.window.cursor_warp(event_xy[0], event_xy[1])
        bpy.context.window.event_simulate(
            type="F13", value="PRESS", x=event_xy[0], y=event_xy[1]
        )
        bpy.app.timers.register(sticky_release, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def run_sticky():
    global event_xy
    try:
        from pie_menu_editor.core.operators import (
            PME_OT_sticky_key,
            PME_OT_sticky_key_base,
        )

        sticky = preferences.add_pm(mode="STICKY", name="PMEStickySmoke")
        names.append(sticky.name)
        sticky.pmis[0].text = "SMOKE_STATE['sticky_press'] = SMOKE_STATE.get('sticky_press', 0) + 1"
        sticky.pmis[1].text = "SMOKE_STATE['sticky_release'] = SMOKE_STATE.get('sticky_release', 0) + 1"
        sticky.key = "F13"
        sticky.km_name = "Window"
        sticky.register_hotkey()
        registered = bool(sticky.kmis_map.get(sticky.name))
        registered_items = sticky.kmis_map.get(sticky.name) or {}
        log(
            "PME_STICKY_REGISTERED",
            {
                "ok": registered,
                "items": {
                    keymap: (item.idname, item.type, item.value, item.active)
                    for keymap, item in registered_items.items()
                },
            },
        )
        if not registered or not hasattr(bpy.context.window, "event_simulate"):
            return finish(False)
        override = find_view3d_context()
        if not override:
            return finish(False)
        area = override["area"]
        event_xy = (area.x + area.width // 2, area.y + area.height // 2)
        log("PME_STICKY_EVENT_XY", event_xy)
        bpy.context.window_manager.keyconfigs.update()

        class WindowManagerHarness:
            @staticmethod
            def modal_handler_add(operator):
                state["sticky_handler_added"] = True

        class ContextHarness:
            window_manager = WindowManagerHarness()

        class StickyHarness:
            is_root_instance = PME_OT_sticky_key_base.is_root_instance
            add_timer = PME_OT_sticky_key_base.add_timer
            remove_timer = PME_OT_sticky_key_base.remove_timer
            stop = PME_OT_sticky_key_base.stop
            restart = PME_OT_sticky_key_base.restart
            execute_pmi = PME_OT_sticky_key_base.execute_pmi
            invoke = PME_OT_sticky_key_base.invoke
            modal = PME_OT_sticky_key_base.modal

        operator = StickyHarness()
        operator.pm_name = sticky.name
        press_result = operator.invoke(
            ContextHarness(), SimpleNamespace(type="F13", value="PRESS")
        )
        release_result = operator.modal(
            bpy.context, SimpleNamespace(type="F13", value="RELEASE")
        )
        timer_result = operator.modal(
            bpy.context, SimpleNamespace(type="TIMER", value="NOTHING")
        )
        log(
            "PME_STICKY_DIRECT_EVENTS",
            {
                "press": press_result,
                "release": release_result,
                "timer": timer_result,
            },
        )
        bpy.app.timers.register(verify_sticky, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def verify_modal_cancelled():
    try:
        from pie_menu_editor.core.operators import PME_OT_modal_base

        active_cleared = PME_OT_modal_base.active is None
        ok = (
            state.get("modal_invoke") == 1
            and state.get("modal_cancel") == 1
            and active_cleared
        )
        log("PME_MODAL_CHECK", {"ok": ok, "active_cleared": active_cleared})
        if not ok:
            return finish(False)
        bpy.app.timers.register(run_modal_confirm, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def verify_modal_confirmed():
    try:
        from pie_menu_editor.core.operators import PME_OT_modal_base

        active_cleared = PME_OT_modal_base.active is None
        ok = (
            state.get("modal_confirm_invoke") == 1
            and state.get("modal_finish") == 1
            and active_cleared
        )
        log("PME_MODAL_CONFIRM_CHECK", {"ok": ok, "active_cleared": active_cleared})
        if not ok:
            return finish(False)
        bpy.app.timers.register(run_sticky, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def confirm_modal():
    try:
        from pie_menu_editor.core.operators import PME_OT_modal_base

        active = PME_OT_modal_base.active
        log("PME_MODAL_CONFIRM_ACTIVE", bool(active))
        if not active or state.get("modal_confirm_invoke") != 1:
            return finish(False)
        active.do_confirm(delay=True)
        bpy.app.timers.register(verify_modal_confirmed, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def run_modal_confirm():
    try:
        modal = preferences.add_pm(mode="MODAL", name="PMEModalConfirmSmoke")
        names.append(modal.name)
        modal.pmis[0].text = (
            "SMOKE_STATE['modal_confirm_invoke'] = "
            "SMOKE_STATE.get('modal_confirm_invoke', 0) + 1"
        )
        finish_item = modal.pmis.add()
        finish_item.name = "Finish"
        finish_item.mode = "FINISH"
        finish_item.text = (
            "SMOKE_STATE['modal_finish'] = SMOKE_STATE.get('modal_finish', 0) + 1"
        )

        override = find_view3d_context()
        if not override:
            return finish(False)
        with bpy.context.temp_override(**override):
            result = bpy.ops.pme.modal("INVOKE_DEFAULT", pm_name=modal.name)
        log("PME_MODAL_CONFIRM_RETURN", result)
        if "RUNNING_MODAL" not in result:
            return finish(False)
        bpy.app.timers.register(confirm_modal, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def cancel_modal():
    try:
        from pie_menu_editor.core.operators import PME_OT_modal_base

        active = PME_OT_modal_base.active
        log("PME_MODAL_ACTIVE", bool(active))
        if not active or state.get("modal_invoke") != 1:
            return finish(False)
        active.do_cancel(delay=True)
        bpy.app.timers.register(verify_modal_cancelled, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def run_modal():
    try:
        modal = preferences.add_pm(mode="MODAL", name="PMEModalSmoke")
        names.append(modal.name)
        modal.pmis[0].text = "SMOKE_STATE['modal_invoke'] = SMOKE_STATE.get('modal_invoke', 0) + 1"
        cancel = modal.pmis.add()
        cancel.name = "Cancel"
        cancel.mode = "CANCEL"
        cancel.text = "SMOKE_STATE['modal_cancel'] = SMOKE_STATE.get('modal_cancel', 0) + 1"

        override = find_view3d_context()
        if not override:
            log("PME_MODAL_CONTEXT", None)
            return finish(False)
        with bpy.context.temp_override(**override):
            result = bpy.ops.pme.modal("INVOKE_DEFAULT", pm_name=modal.name)
        log("PME_MODAL_RETURN", result)
        if "RUNNING_MODAL" not in result:
            return finish(False)
        bpy.app.timers.register(cancel_modal, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def run_dynamic_registration():
    global hidden_panel_name
    try:
        from pie_menu_editor.core import panel_utils, pme
        from pie_menu_editor.core.addon import get_prefs

        global preferences
        preferences = get_prefs()
        pme.context.add_global("SMOKE_STATE", state)

        panel = preferences.add_pm(mode="PANEL", name="PMEPanelSmoke")
        names.append(panel.name)
        panel.panel_space = "VIEW_3D"
        panel.panel_region = "UI"
        panel.panel_category = "PME Smoke"
        item = panel.pmis.add()
        item.name = "View Menu"
        item.mode = "MENU"
        item.text = "VIEW3D_MT_view"
        panel.update_panel_group()
        generated = panel_utils._panels.get(panel.name, [])
        panel_ok = len(generated) == 1 and hasattr(bpy.types, generated[0].__name__)
        log("PME_PANEL_CHECK", {"ok": panel_ok, "types": [p.__name__ for p in generated]})
        if not panel_ok:
            return finish(False)

        prop = preferences.add_pm(mode="PROPERTY", name="PMEPropertySmoke")
        names.append(prop.name)
        prop_ok = hasattr(preferences.props.__class__, prop.name)
        setattr(preferences.props, prop.name, True)
        prop_ok = prop_ok and getattr(preferences.props, prop.name) is True
        log("PME_PROPERTY_CHECK", prop_ok)
        if not prop_ok:
            return finish(False)

        candidates = (
            "VIEW3D_PT_view3d_properties",
            "VIEW3D_PT_view3d_cursor",
            "VIEW3D_PT_transform_orientations",
        )
        hidden_panel_name = next((name for name in candidates if hasattr(bpy.types, name)), None)
        if not hidden_panel_name:
            log("PME_HIDDEN_PANEL_CANDIDATE", None)
            return finish(False)
        panel_utils.hide_panel(hidden_panel_name)
        hide_ok = panel_utils.is_panel_hidden(hidden_panel_name) and not hasattr(
            bpy.types, hidden_panel_name
        )
        panel_utils.unhide_panel(hidden_panel_name)
        restore_ok = not panel_utils.is_panel_hidden(hidden_panel_name) and hasattr(
            bpy.types, hidden_panel_name
        )
        log("PME_HIDDEN_PANEL_CHECK", {"hide": hide_ok, "restore": restore_ok})
        if not (hide_ok and restore_ok):
            return finish(False)

        bpy.app.timers.register(run_modal, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        log("PME_DYNAMIC_MODES_ENABLE", module.__file__ if module else None)
        bpy.app.timers.register(run_dynamic_registration, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
