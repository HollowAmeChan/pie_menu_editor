import bpy
import traceback

from pie_menu_editor.core import c_utils


class PME_MT_is_row_probe(bpy.types.Menu):
    bl_idname = "PME_MT_is_row_probe"
    bl_label = "PME is_row probe"

    def draw(self, context):
        layouts = {
            "root": self.layout,
            "row": self.layout.row(),
            "column": self.layout.column(),
            "split": self.layout.split(),
            "box": self.layout.box(),
        }
        print(
            "PME_IS_ROW_VALUES",
            bpy.app.version_string,
            {name: c_utils.is_row(layout) for name, layout in layouts.items()},
            flush=True,
        )


try:
    bpy.utils.register_class(PME_MT_is_row_probe)
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
        print(
            "PME_IS_ROW_CALL",
            bpy.ops.wm.call_menu(name=PME_MT_is_row_probe.bl_idname),
            flush=True,
        )
except Exception:
    traceback.print_exc()
finally:
    bpy.ops.wm.quit_blender()
