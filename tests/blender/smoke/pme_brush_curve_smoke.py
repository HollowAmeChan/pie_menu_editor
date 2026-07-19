import addon_utils
import bpy
from pathlib import Path
import traceback


TAG = "PME_BRUSH_CURVE_SMOKE"
MENU_NAME = "Popup: (Sculpt) Control Alt"
FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "pme_community_51_menus.json"
)


class RecordingLayout:
    def __init__(self):
        self.properties = []

    def prop(self, owner, prop, **kwargs):
        self.properties.append((owner, prop, kwargs))
        return getattr(owner, prop)


def finish(success):
    try:
        from pie_menu_editor.core import compatibility_fixes
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        for menu in list(prefs.pie_menus):
            if menu.has_tag(TAG):
                prefs.remove_pm(menu)
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_BRUSH_CURVE_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def run():
    try:
        from pie_menu_editor.core import compatibility_fixes
        from pie_menu_editor.core.addon import get_prefs
        from pie_menu_editor.core.bl_utils import (
            brush_curve_preset,
            set_brush_curve_preset,
        )

        prefs = get_prefs()
        menu = prefs.pie_menus[MENU_NAME]
        migrated = [
            item.text for item in menu.pmis if "brush_curve_preset" in item.text
        ]
        synthetic = []
        for mode, text in (
            ("PROP", "paint_settings().brush.curve_preset"),
            ("PROP", "paint_settings().brush.curve"),
            ("COMMAND", "bpy.ops.brush.curve_preset(shape='ROUND')"),
            (
                "CUSTOM",
                "L.template_curve_mapping(paint_settings().brush, 'curve', brush=True)",
            ),
        ):
            item = menu.pmis.add()
            item.mode = mode
            item.text = text
            synthetic.append(item)
        compatibility_fixes.fix_1_19_11(prefs, menu)
        synthetic_values = [(item.mode, item.text) for item in synthetic]
        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.object.mode_set(mode="SCULPT")
            settings = bpy.context.scene.tool_settings.sculpt
            if settings.brush is None:
                bpy.ops.brush.asset_activate(
                    asset_library_type="ESSENTIALS",
                    relative_asset_identifier=(
                        "brushes/essentials_brushes-mesh_sculpt.blend/Brush/Draw"
                    ),
                )
            brush = settings.brush
            layout = RecordingLayout()
            brush_curve_preset(layout, brush, expand=True)
            expected_property = (
                "curve_distance_falloff_preset"
                if "curve_distance_falloff_preset" in brush.bl_rna.properties
                else "curve_preset"
            )
            shape_results = []
            shape_values = []
            expected_shapes = {
                "SHARP": "SHARP",
                "SMOOTH": "SMOOTH",
                "MAX": "CONSTANT",
                "LINE": "LIN",
                "ROUND": "SPHERE",
                "ROOT": "ROOT",
            }
            for shape, current in expected_shapes.items():
                result = set_brush_curve_preset(shape=shape)
                expected = current
                actual = getattr(brush, expected_property)
                shape_values.append((shape, actual, expected))
                shape_results.append("FINISHED" in result and actual == expected)
            draw_result = bpy.ops.wm.pme_user_pie_menu_call(
                "INVOKE_DEFAULT",
                pie_menu_name=MENU_NAME,
                invoke_mode="SUB",
                keymap="Window",
            )

        checks = {
            "community_migrated": len(migrated) == 1,
            "property_migrated": synthetic_values[0] == (
                "CUSTOM",
                "brush_curve_preset(L, paint_settings().brush)",
            ),
            "mapping_property_migrated": synthetic_values[1] == (
                "CUSTOM",
                "brush_curve_mapping(L, paint_settings().brush, brush=True)",
            ),
            "command_migrated": synthetic_values[2] == (
                "COMMAND",
                "set_brush_curve_preset(shape='ROUND')",
            ),
            "custom_mapping_migrated": synthetic_values[3] == (
                "CUSTOM",
                "brush_curve_mapping(L, paint_settings().brush, brush=True)",
            ),
            "property_selected": layout.properties[0][1] == expected_property,
            "shape_mapping": all(shape_results),
            "menu_called": "CANCELLED" in draw_result,
        }
        print("PME_BRUSH_CURVE_MIGRATED", migrated, flush=True)
        print("PME_BRUSH_CURVE_SYNTHETIC", synthetic_values, flush=True)
        print("PME_BRUSH_CURVE_LAYOUT", layout.properties[0][1], flush=True)
        print("PME_BRUSH_CURVE_SHAPES", shape_results, flush=True)
        print("PME_BRUSH_CURVE_VALUES", shape_values, flush=True)
        print("PME_BRUSH_CURVE_CHECKS", checks, flush=True)
        bpy.app.timers.register(
            lambda: finish(all(checks.values())), first_interval=1.0
        )
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


def import_config():
    try:
        result = bpy.ops.wm.pm_import(
            "EXEC_DEFAULT",
            filepath=str(FIXTURE),
            mode="RENAME",
            tags=TAG,
        )
        print("PME_BRUSH_CURVE_IMPORT", result, flush=True)
        if "FINISHED" not in result:
            return finish(False)
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_BRUSH_CURVE_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(import_config, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
