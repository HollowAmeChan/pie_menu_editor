import addon_utils
import bpy
import traceback


MENU_NAME = "PME Missing Property Draw Smoke"
ERROR_MENU_NAME = "PME Missing Property Custom Error Smoke"
success = False
created = []
original_print_exc = None
original_layout_error = None


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

    operators = package.operators
    layout_helper = package.layout_helper
    prefs = package.addon.get_prefs()
    missing_menu = prefs.add_pm("PMENU", MENU_NAME)
    missing_item = missing_menu.pmis[0]
    missing_item.mode = "PROP"
    missing_item.text = "C.object.location"
    missing_custom_item = missing_menu.pmis[1]
    missing_custom_item.mode = "CUSTOM"
    missing_custom_item.text = "L.prop(C.object, 'location')"
    created.append(missing_menu.name)

    error_menu = prefs.add_pm("PMENU", ERROR_MENU_NAME)
    error_item = error_menu.pmis[0]
    error_item.mode = "CUSTOM"
    error_item.text = "raise RuntimeError('custom draw smoke')"
    created.append(error_menu.name)

    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    bpy.context.view_layer.objects.active = None

    captured = []
    draw_mode = "missing"
    original_print_exc = operators.print_exc
    original_layout_error = layout_helper.LayoutHelper.error

    def capture_print_exc(*args, **kwargs):
        captured.append(("print_exc", args, kwargs))

    def capture_layout_error(self, text, message=None):
        captured.append(("layout_error", text, message))

    operators.print_exc = capture_print_exc
    layout_helper.LayoutHelper.error = capture_layout_error

    class PME_MT_missing_property_draw_smoke(bpy.types.Menu):
        bl_idname = "PME_MT_missing_property_draw_smoke"
        bl_label = "PME missing property draw smoke"

        def draw(self, context):
            from pie_menu_editor.core.layout_helper import lh

            layout = self.layout.column()
            lh.lt(layout, operator_context="INVOKE_DEFAULT")
            menu = missing_menu if draw_mode == "missing" else error_menu
            for index, item in enumerate(menu.pmis):
                if item.mode != "EMPTY":
                    operators.WM_OT_pme_user_pie_menu_call._draw_item(
                        prefs, menu, item, index
                    )

    bpy.utils.register_class(PME_MT_missing_property_draw_smoke)
    window = bpy.context.window_manager.windows[0]
    screen = window.screen
    area = next(
        (candidate for candidate in screen.areas if candidate.type == "VIEW_3D"),
        screen.areas[0],
    )
    region = next(
        (candidate for candidate in area.regions if candidate.type == "WINDOW"),
        None,
    )
    with bpy.context.temp_override(
        window=window,
        screen=screen,
        area=area,
        region=region,
    ):
        missing_draw_result = bpy.ops.wm.call_menu(
            name=PME_MT_missing_property_draw_smoke.bl_idname
        )
    missing_events = list(captured)
    draw_mode = "error"
    with bpy.context.temp_override(
        window=window,
        screen=screen,
        area=area,
        region=region,
    ):
        error_draw_result = bpy.ops.wm.call_menu(
            name=PME_MT_missing_property_draw_smoke.bl_idname
        )
    error_events = captured[len(missing_events):]

    checks = {
        "missing_menu_drawn": missing_draw_result == {"INTERFACE"},
        "missing_property_is_silent": not missing_events,
        "error_menu_drawn": error_draw_result == {"INTERFACE"},
        "custom_error_is_reported": any(
            event[0] == "layout_error" for event in error_events
        ),
    }
    print(
        "PME_MISSING_PROPERTY_DRAW_DATA",
        bpy.app.version_string,
        "draw_results=",
        (missing_draw_result, error_draw_result),
        "captured=",
        captured,
        flush=True,
    )
    print("PME_MISSING_PROPERTY_DRAW_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    try:
        if "operators" in locals() and original_print_exc is not None:
            operators.print_exc = original_print_exc
        if "layout_helper" in locals() and original_layout_error is not None:
            layout_helper.LayoutHelper.error = original_layout_error
        if "PME_MT_missing_property_draw_smoke" in locals():
            bpy.utils.unregister_class(PME_MT_missing_property_draw_smoke)
        if "prefs" in locals():
            for name in reversed(created):
                if name in prefs.pie_menus:
                    prefs.remove_pm(prefs.pie_menus[name])
    except Exception:
        traceback.print_exc()
        success = False
    print(
        "PME_MISSING_PROPERTY_DRAW_RESULT",
        "OK" if success else "FAILED",
        flush=True,
    )
    bpy.ops.wm.quit_blender()
