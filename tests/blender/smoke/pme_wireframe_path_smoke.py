import addon_utils
import bpy
import traceback


MENU_NAME = "PME Wireframe Path Smoke"
errors = []
drawn = []


class PME_MT_wireframe_path_smoke(bpy.types.Menu):
    bl_idname = "PME_MT_wireframe_path_smoke"
    bl_label = "PME wireframe path smoke"

    def draw(self, context):
        from pie_menu_editor.core.addon import get_prefs
        from pie_menu_editor.core.layout_helper import lh
        from pie_menu_editor.core.operators import WM_OT_pme_user_pie_menu_call

        prefs = get_prefs()
        menu = prefs.pie_menus[MENU_NAME]
        lh.lt(self.layout.column(), operator_context="INVOKE_DEFAULT")
        for index, item in enumerate(menu.pmis):
            try:
                WM_OT_pme_user_pie_menu_call._draw_item(
                    prefs, menu, item, index
                )
                drawn.append(index)
            except Exception:
                errors.append(traceback.format_exc())


success = False
registered = False
original_layout_error = None
original_print_exc = None
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
        ("PROP", "C.space_data.shading.show_wireframes"),
        (
            "CUSTOM",
            'L.prop(C.area.spaces.active.shading, "show_wireframes", '
            'text="Wireframes")',
        ),
        (
            "COMMAND",
            "bpy.context.space_data.shading.show_wireframes = not "
            "context.space_data.shading.show_wireframes",
        ),
        ("PROP", "C.space_data.shading.type"),
    ]
    for mode, text in source:
        item = menu.pmis.add()
        item.mode = mode
        item.text = text
    package.compatibility_fixes.fix_1_19_21(prefs, menu)
    migrated = [(item.mode, item.text) for item in menu.pmis]
    expected = [
        ("PROP", "C.space_data.overlay.show_wireframes"),
        (
            "CUSTOM",
            'L.prop(C.area.spaces.active.overlay, "show_wireframes", '
            'text="Wireframes")',
        ),
        (
            "COMMAND",
            "bpy.context.space_data.overlay.show_wireframes = not "
            "context.space_data.overlay.show_wireframes",
        ),
        ("PROP", "C.space_data.shading.type"),
    ]

    original_layout_error = package.layout_helper.LayoutHelper.error
    original_print_exc = package.operators.print_exc

    def capture_layout_error(self, text, message=None):
        errors.append((text, message))

    def capture_print_exc(*args, **kwargs):
        errors.append((args, kwargs, traceback.format_exc()))

    package.layout_helper.LayoutHelper.error = capture_layout_error
    package.operators.print_exc = capture_print_exc

    bpy.utils.register_class(PME_MT_wireframe_path_smoke)
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
        menu_result = bpy.ops.wm.call_menu(name=PME_MT_wireframe_path_smoke.bl_idname)

    checks = {
        "migration": migrated == expected,
        "menu_interface": menu_result == {"INTERFACE"},
        "all_drawn": drawn == list(range(len(source))),
        "no_errors": not errors,
    }
    print(
        "PME_WIREFRAME_PATH_DATA",
        bpy.app.version_string,
        module.bl_info.get("version"),
        migrated,
        flush=True,
    )
    print("PME_WIREFRAME_PATH_ERRORS", errors, flush=True)
    print("PME_WIREFRAME_PATH_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    try:
        if original_layout_error is not None:
            package.layout_helper.LayoutHelper.error = original_layout_error
        if original_print_exc is not None:
            package.operators.print_exc = original_print_exc
        if registered:
            bpy.utils.unregister_class(PME_MT_wireframe_path_smoke)
        package = getattr(locals().get("module"), "core", None)
        if package is not None:
            prefs = package.addon.get_prefs()
            menu = prefs.pie_menus.get(MENU_NAME)
            if menu is not None:
                prefs.remove_pm(menu)
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_WIREFRAME_PATH_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
