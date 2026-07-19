import addon_utils
import bpy
import traceback


errors = []
draw_results = []


class PME_MT_embedded_panels_smoke(bpy.types.Menu):
    bl_idname = "PME_MT_embedded_panels_smoke"
    bl_label = "PME embedded panels smoke"

    def draw(self, context):
        from pie_menu_editor.core import panel_utils, pme

        pme.context.layout = self.layout
        panels = (
            ("OBJECT_PT_transform", "PROPERTIES"),
            ("OBJECT_PT_display", "PROPERTIES"),
            ("OBJECT_PT_relations", "PROPERTIES"),
            ("VIEW3D_PT_view3d_cursor", "VIEW_3D"),
            ("VIEW3D_PT_view3d_properties", "VIEW_3D"),
        )
        for panel_name, area in panels:
            try:
                result = panel_utils.panel(
                    panel_name,
                    frame=True,
                    header=True,
                    area=area,
                    layout=self.layout.column(),
                )
                draw_results.append((panel_name, result))
            except Exception:
                errors.append((panel_name, traceback.format_exc()))


success = False
try:
    module = addon_utils.enable(
        "pie_menu_editor",
        default_set=True,
        persistent=False,
        handle_error=None,
    )
    if not hasattr(bpy.types.WindowManager, "pme"):
        for waiter in module.core.PME_OT_wait_context.instances:
            waiter.cancelled = True
        module.core.on_context()

    panel_utils = module.core.panel_utils
    original_debug = panel_utils.DBG_PANEL
    original_print_exc = panel_utils.print_exc
    panel_utils.DBG_PANEL = True
    panel_utils.print_exc = lambda *args, **kwargs: errors.append(
        ("panel_print_exc", args, kwargs, traceback.format_exc())
    )
    bpy.utils.register_class(PME_MT_embedded_panels_smoke)

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
        result = bpy.ops.wm.call_menu(name=PME_MT_embedded_panels_smoke.bl_idname)

    checks = {
        "interface": result == {"INTERFACE"},
        "all_panels": len(draw_results) == 5,
        "all_returned": all(item[1] is True for item in draw_results),
        "no_errors": not errors,
    }
    print(
        "PME_EMBEDDED_PANELS_CHECKS",
        bpy.app.version_string,
        checks,
        "results=",
        draw_results,
        "errors=",
        errors,
        flush=True,
    )
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    try:
        panel_utils.DBG_PANEL = original_debug
        panel_utils.print_exc = original_print_exc
    except Exception:
        pass
    print("PME_EMBEDDED_PANELS_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
