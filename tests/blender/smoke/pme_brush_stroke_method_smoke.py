import addon_utils
import bpy
import traceback


MENU_NAME = "PME Brush Stroke Method Smoke"
test_brush = None
registered = False


class PME_MT_brush_stroke_method_smoke(bpy.types.Menu):
    bl_idname = "PME_MT_brush_stroke_method_smoke"
    bl_label = "PME brush stroke method smoke"

    def draw(self, context):
        from pie_menu_editor.core.bl_utils import brush_stroke_method

        brush_stroke_method(self.layout, test_brush, "SPACE", text="Spacing")


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
    menu = prefs.add_pm(mode="DIALOG", name=MENU_NAME)
    menu.pmis.clear()
    source = [
        ("PROP", "paint_settings().brush.use_space"),
        (
            "CUSTOM",
            "L.prop(paint_settings().brush, 'use_anchor', text='Anchor')",
        ),
        ("COMMAND", "paint_settings().brush.use_airbrush = True"),
        (
            "COMMAND",
            "paint_settings().brush.use_line = not paint_settings().brush.use_line",
        ),
        ("COMMAND", "return paint_settings().brush.use_curve"),
        ("COMMAND", 'D.brushes["Test"].use_restore_mesh = False'),
    ]
    for mode, text in source:
        item = menu.pmis.add()
        item.mode = mode
        item.text = text

    package.compatibility_fixes.fix_1_19_20(prefs, menu)
    migrated = [(item.mode, item.text) for item in menu.pmis]
    expected = [
        (
            "CUSTOM",
            "brush_stroke_method(L, paint_settings().brush, 'SPACE')",
        ),
        (
            "CUSTOM",
            "brush_stroke_method(L, paint_settings().brush, 'ANCHORED', text='Anchor')",
        ),
        (
            "COMMAND",
            "set_brush_stroke_method(paint_settings().brush, 'AIRBRUSH', True)",
        ),
        (
            "COMMAND",
            "set_brush_stroke_method(paint_settings().brush, 'LINE', not "
            "brush_stroke_method_enabled(paint_settings().brush, 'LINE'))",
        ),
        (
            "COMMAND",
            "return brush_stroke_method_enabled(paint_settings().brush, 'CURVE')",
        ),
        (
            "COMMAND",
            'set_brush_stroke_method(D.brushes["Test"], \'DRAG_DOT\', False)',
        ),
    ]

    try:
        test_brush = bpy.data.brushes.new(MENU_NAME, mode="SCULPT")
    except TypeError:
        test_brush = bpy.data.brushes.new(MENU_NAME)

    helpers = package.bl_utils
    set_result = helpers.set_brush_stroke_method(test_brush, "SPACE", True)
    enabled_after_set = helpers.brush_stroke_method_enabled(test_brush, "SPACE")
    clear_result = helpers.set_brush_stroke_method(test_brush, "SPACE", False)
    cleared_to_dots = test_brush.stroke_method == "DOTS"

    bpy.utils.register_class(PME_MT_brush_stroke_method_smoke)
    registered = True
    window = bpy.context.window_manager.windows[0]
    screen = window.screen
    area = next(item for item in screen.areas if item.type == "VIEW_3D")
    region = next(item for item in area.regions if item.type == "WINDOW")
    with bpy.context.temp_override(
        window=window,
        screen=screen,
        area=area,
        region=region,
    ):
        menu_result = bpy.ops.wm.call_menu(
            name=PME_MT_brush_stroke_method_smoke.bl_idname
        )

    checks = {
        "migration": migrated == expected,
        "set_result": set_result == {"FINISHED"},
        "enabled_after_set": enabled_after_set,
        "clear_result": clear_result == {"FINISHED"},
        "cleared_to_dots": cleared_to_dots,
        "menu_interface": menu_result == {"INTERFACE"},
    }
    print(
        "PME_BRUSH_STROKE_DATA",
        bpy.app.version_string,
        module.bl_info.get("version"),
        migrated,
        flush=True,
    )
    print("PME_BRUSH_STROKE_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    try:
        if registered:
            bpy.utils.unregister_class(PME_MT_brush_stroke_method_smoke)
        if test_brush is not None:
            bpy.data.brushes.remove(test_brush)
        package = getattr(locals().get("module"), "core", None)
        if package is not None:
            prefs = package.addon.get_prefs()
            menu = prefs.pie_menus.get(MENU_NAME)
            if menu is not None:
                prefs.remove_pm(menu)
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_BRUSH_STROKE_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
