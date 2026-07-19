import addon_utils
import bpy
import os
import traceback


MENU_NAME = "PME Special UI Smoke"
errors = []
menu_name = None
TEST_MODE = os.environ.get("PME_PAINT_MODE", "SCULPT")
MODE_CONFIG = {
    "SCULPT": ("SCULPT", "mesh_sculpt", "Draw"),
    "VERTEX_PAINT": ("PAINT_VERTEX", "mesh_vertex", "Paint Hard"),
    "WEIGHT_PAINT": ("PAINT_WEIGHT", "mesh_weight", "Paint"),
    "TEXTURE_PAINT": ("PAINT_TEXTURE", "mesh_texture", "Paint Hard"),
    "PAINT_GREASE_PENCIL": (
        "PAINT_GREASE_PENCIL",
        "gp_draw",
        "Pencil",
    ),
    "SCULPT_GREASE_PENCIL": (
        "SCULPT_GREASE_PENCIL",
        "gp_sculpt",
        "Smooth",
    ),
}


CUSTOM_ITEMS = (
    (
        "PALETTES",
        "ps = paint_settings(); L.template_ID(ps, 'palette', new='palette.new') if ps else None",
    ),
    (
        "ACTIVE_PALETTE",
        "ps = paint_settings(); L.template_palette(ps, 'palette', color=True) if ps else None",
    ),
    (
        "COLOR_PICKER",
        "ps = paint_settings(); unified_paint_panel().prop_unified_color_picker(L, bl_context, ps.brush, 'color') if ps and ps.brush else None",
    ),
    (
        "BRUSH",
        "ps = paint_settings(); L.template_ID_preview(ps, 'brush', new='brush.add', rows=3, cols=8) if ps else None",
    ),
    (
        "BRUSH_COLOR",
        "ps = paint_settings(); unified_paint_panel().prop_unified_color(L, bl_context, ps.brush, 'color') if ps and ps.brush else None",
    ),
    (
        "BRUSH_COLOR2",
        "ps = paint_settings(); unified_paint_panel().prop_unified_color(L, bl_context, ps.brush, 'secondary_color') if ps and ps.brush else None",
    ),
    ("OBJ_DATA", "ao = C.active_object; L.template_ID(ao, 'data') if ao else None"),
    (
        "TEXTURE",
        "ps = paint_settings(); L.template_ID_preview(ps.brush, 'texture', new='texture.new', rows=3, cols=8) if ps and ps.brush else None",
    ),
    (
        "TEXTURE_MASK",
        "ps = paint_settings(); L.template_ID_preview(ps.brush, 'mask_texture', new='texture.new', rows=3, cols=8) if ps and ps.brush else None",
    ),
    (
        "RECENT_FILES",
        "L.menu('TOPBAR_MT_file_open_recent', text=text, icon=icon, icon_value=icon_value)",
    ),
    ("MODIFIERS", "panel('DATA_PT_modifiers', frame=True, header=True)"),
)


def finish(success):
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        if menu_name and menu_name in prefs.pie_menus:
            prefs.remove_pm(prefs.pie_menus[menu_name])
    except Exception:
        traceback.print_exc()
        success = False

    print("PME_SPECIAL_ERRORS", errors, flush=True)
    print("PME_SPECIAL_RESULT", "OK" if success and not errors else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify():
    return finish(True)


def create_and_open():
    global menu_name
    try:
        from pie_menu_editor.core import compatibility_fixes, layout_helper, pme
        from pie_menu_editor.core.addon import get_prefs
        from pie_menu_editor.core.bl_utils import paint_settings as get_paint_settings

        prefs = get_prefs()
        prefs.show_error_trace = True

        original_error = layout_helper.lh.error

        def tracked_error(text, message=None):
            item = getattr(pme.context.pmi, "name", "<unknown>")
            errors.append((item, message or "draw exception"))
            return original_error(text, message)

        layout_helper.lh.error = tracked_error

        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            obj = bpy.context.active_object
            expected_mode, asset_file, brush_name = MODE_CONFIG[TEST_MODE]
            if TEST_MODE.endswith("GREASE_PENCIL"):
                bpy.ops.object.mode_set(mode="OBJECT")
                bpy.ops.object.select_all(action="SELECT")
                bpy.ops.object.delete(use_global=False)
                bpy.ops.object.grease_pencil_add()
                obj = bpy.context.active_object
            if TEST_MODE == "WEIGHT_PAINT" and not obj.vertex_groups:
                obj.vertex_groups.new(name="PME Weight Smoke")
            if TEST_MODE == "TEXTURE_PAINT":
                material = bpy.data.materials.new("PME Texture Smoke")
                material.use_nodes = True
                obj.data.materials.append(material)
                image = bpy.data.images.new("PME Texture Smoke", width=32, height=32)
                node = material.node_tree.nodes.new("ShaderNodeTexImage")
                node.image = image
                material.node_tree.nodes.active = node
            bpy.ops.object.mode_set(mode=TEST_MODE)
            settings = get_paint_settings(bpy.context)
            if settings is None:
                raise RuntimeError(f"No paint settings for {TEST_MODE}")
            if settings.brush is None:
                activate_result = bpy.ops.brush.asset_activate(
                    asset_library_type="ESSENTIALS",
                    relative_asset_identifier=(
                        f"brushes/essentials_brushes-{asset_file}.blend/Brush/{brush_name}"
                    ),
                )
                print("PME_SPECIAL_BRUSH_ACTIVATE", activate_result, flush=True)

            menu = prefs.add_pm(mode="DIALOG", name=MENU_NAME)
            menu_name = menu.name
            generator_result = bpy.ops.pme.pmi_custom_set(mode="BRUSH")
            generated = prefs.pmi_data.custom == (
                "ps = paint_settings(); "
                "brush_asset_selector(L, bl_context, ps) if ps else None"
            )
            print(
                "PME_SPECIAL_BRUSH_GENERATED",
                generated,
                generator_result,
                prefs.pmi_data.custom,
                flush=True,
            )
            if not generated:
                return finish(False)
            for name, command in CUSTOM_ITEMS:
                item = menu.pmis.add()
                item.name = name
                item.mode = "CUSTOM"
                item.text = command

            compatibility_fixes.fix_1_19_3(prefs, menu)
            compatibility_fixes.fix_1_19_4(prefs, menu)
            palette_item = next(item for item in menu.pmis if item.name == "ACTIVE_PALETTE")
            brush_item = next(item for item in menu.pmis if item.name == "BRUSH")
            migrated = palette_item.text == (
                "ps = paint_settings(); "
                "template_palette(L, ps, 'palette') if ps else None"
            )
            print("PME_SPECIAL_PALETTE_MIGRATED", migrated, palette_item.text, flush=True)
            brush_migrated = brush_item.text == (
                "ps = paint_settings(); "
                "brush_asset_selector(L, bl_context, ps) if ps else None"
            )
            print("PME_SPECIAL_BRUSH_MIGRATED", brush_migrated, brush_item.text, flush=True)
            if not migrated or not brush_migrated:
                return finish(False)

            result = bpy.ops.wm.pme_user_pie_menu_call(
                "INVOKE_DEFAULT",
                pie_menu_name=menu.name,
                invoke_mode="SUB",
                keymap="Window",
            )
            print("PME_SPECIAL_CALL", result, flush=True)
            print(
                "PME_SPECIAL_CONTEXT",
                bpy.context.mode,
                expected_mode,
                bool(settings.brush),
                hasattr(bpy.types, "DATA_PT_modifiers"),
                hasattr(bpy.types, "OBJECT_PT_modifiers"),
                hasattr(bpy.types, "TOPBAR_MT_file_open_recent"),
                flush=True,
            )

        bpy.app.timers.register(verify, first_interval=1.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_SPECIAL_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(create_and_open, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
