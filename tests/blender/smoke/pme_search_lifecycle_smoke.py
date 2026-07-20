import addon_utils
import bpy
import traceback


results = []
macro_name = "PME Developer Search Macro"
hidden_group_name = "PME Developer Search Hidden Panels"
hidden_panel_name = "VIEW3D_PT_view3d_properties"


def prepare_search_state(module):
    package = module.core
    if not hasattr(bpy.types.WindowManager, "pme"):
        for waiter in package.PME_OT_wait_context.instances:
            waiter.cancelled = True
        package.on_context()
    bpy.context.preferences.view.show_developer_ui = True
    prefs = package.addon.get_prefs()
    if macro_name not in prefs.pie_menus:
        macro = prefs.add_pm("MACRO", macro_name)
        macro.pmis[0].text = "bpy.ops.wm.redraw_timer(iterations=1)"
    if hidden_group_name not in prefs.pie_menus:
        hidden_group = prefs.add_pm("HPANEL", hidden_group_name)
        item = hidden_group.pmis.add()
        item.name = "View"
        item.mode = "EMPTY"
        item.text = hidden_panel_name
        hidden_group.ed.init_pm(hidden_group)
    return (
        macro_name in package.macro_utils._macros
        and package.panel_utils.is_panel_hidden(hidden_panel_name)
    )


def finish(success):
    print("PME_SEARCH_RESULTS", results, flush=True)
    print("PME_SEARCH_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def invoke_search(label, next_callback):
    try:
        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            result = bpy.ops.wm.search_menu("INVOKE_DEFAULT")
        results.append((label, sorted(result)))
        bpy.app.timers.register(next_callback, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def search_after_reenable():
    return invoke_search("reenabled", verify)


def verify():
    search_results = [
        item for item in results if item[0] in {"initial", "reenabled"}
    ]
    macro_results = [item for item in results if item[0].endswith("_macro")]
    success = (
        len(search_results) == 2
        and all(
            "FINISHED" in result
            or "RUNNING_MODAL" in result
            or "INTERFACE" in result
            for _, result in search_results
        )
        and len(macro_results) == 2
        and all(value for _, value in macro_results)
    )
    return finish(success)


def reenable():
    try:
        addon_utils.disable("pie_menu_editor", default_set=True, handle_error=None)
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_SEARCH_REENABLE", module.__file__ if module else None, flush=True)
        results.append(("reenabled_macro", prepare_search_state(module)))
        bpy.app.timers.register(search_after_reenable, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def search_initial():
    return invoke_search("initial", reenable)


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_SEARCH_ENABLE", module.__file__ if module else None, flush=True)
        results.append(("initial_macro", prepare_search_state(module)))
        bpy.app.timers.register(search_initial, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
