import bpy
import os
import traceback

import pie_menu_editor
from pie_menu_editor.core import c_utils
from pie_menu_editor.core.layout_helper import LayoutHelper
from pie_menu_editor.core import panel_utils


calls = 0
draw_success = False
original_is_row = c_utils.is_row


def checked_is_row(layout):
    global calls
    calls += 1
    if bpy.app.version >= (5, 0, 0):
        raise RuntimeError("Blender 5.x accessed the private uiLayout memory probe")
    return original_is_row(layout)


class PME_PT_layout_memory_probe(bpy.types.Panel):
    bl_idname = "PME_PT_layout_memory_probe"
    bl_label = "PME layout memory probe"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PME"

    def draw(self, context):
        self.layout.label(text="Panel content")


class PME_MT_layout_memory_probe(bpy.types.Menu):
    bl_idname = "PME_MT_layout_memory_probe"
    bl_label = "PME layout memory probe"

    def draw(self, context):
        global draw_success
        try:
            helper = LayoutHelper()
            helper.lt(self.layout.box())
            helper.prop_compact(context.scene.render, "film_transparent")
            panel_utils.panel(
                PME_PT_layout_memory_probe,
                header=False,
                poll=False,
                layout=self.layout.box(),
            )
            draw_success = True
        except Exception:
            traceback.print_exc()


success = False
try:
    c_utils.is_row = checked_is_row
    bpy.utils.register_class(PME_PT_layout_memory_probe)
    bpy.utils.register_class(PME_MT_layout_memory_probe)

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
        result = bpy.ops.wm.call_menu(name=PME_MT_layout_memory_probe.bl_idname)

    expected_calls = 0 if bpy.app.version >= (5, 0, 0) else 2
    checks = {
        "interface": result == {"INTERFACE"},
        "draw": draw_success,
        "calls": calls == expected_calls,
        "installed_path": not os.environ.get("PME_EXPECTED_ADDON_ROOT")
        or os.path.normcase(pie_menu_editor.__file__).startswith(
            os.path.normcase(os.environ["PME_EXPECTED_ADDON_ROOT"])
        ),
    }
    print(
        "PME_LAYOUT_MEMORY_GUARD_CHECKS",
        bpy.app.version_string,
        checks,
        "calls=",
        calls,
        pie_menu_editor.__file__,
        flush=True,
    )
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    print(
        "PME_LAYOUT_MEMORY_GUARD_RESULT",
        "OK" if success else "FAILED",
        flush=True,
    )
    bpy.ops.wm.quit_blender()
