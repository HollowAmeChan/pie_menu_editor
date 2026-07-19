import addon_utils
import bpy
import traceback


menu_name = None
errors = []


class CaptureState:
    prop = ""
    operator = ""
    name = ""

    def draw_menu(self, menu, context):
        pass


class TypeSelection:
    mode = ""
    pm_item = -1
    text = ""


def finish(success):
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        if menu_name and menu_name in prefs.pie_menus:
            prefs.remove_pm(prefs.pie_menus[menu_name])
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_BUTTON_CAPTURE_ERRORS", errors, flush=True)
    print("PME_BUTTON_CAPTURE_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def verify_draw(checks):
    checks["draw_errors"] = not errors
    print("PME_BUTTON_CAPTURE_CHECKS", checks, flush=True)
    return finish(all(checks.values()))


def run():
    global menu_name
    try:
        from pie_menu_editor.core import layout_helper, pme
        from pie_menu_editor.core.addon import get_prefs
        from pie_menu_editor.core.bl_utils import gen_prop_path
        from pie_menu_editor.core.preferences import PME_OT_context_menu
        from pie_menu_editor.core.ed_base import WM_OT_pmi_type_select

        prefs = get_prefs()
        original_error = layout_helper.lh.error

        def tracked_error(text, message=None):
            errors.append((getattr(pme.context.pmi, "name", ""), message))
            return original_error(text, message)

        layout_helper.lh.error = tracked_error

        obj = bpy.context.active_object
        material = bpy.data.materials.new("PME Button Capture")
        obj.data.materials.append(material)
        obj.active_material_index = len(obj.data.materials) - 1
        modifier = obj.modifiers.new("PME Button Capture", "BEVEL")
        pointers = (
            ("Frame", bpy.context.scene, "frame_current"),
            ("Viewport", obj, "hide_viewport"),
            ("Mesh", obj.data, "use_auto_texspace"),
            ("Modifier", modifier, "show_viewport"),
            ("Material", material, "diffuse_color"),
        )
        paths = []
        comparisons = []
        values_ok = True
        for name, pointer, property_name in pointers:
            prop = pointer.bl_rna.properties[property_name]
            path = gen_prop_path(pointer, prop)
            value = pme.context.eval(path)
            expected = getattr(pointer, property_name)
            if hasattr(value, "to_list"):
                value = value.to_list()
            if hasattr(expected, "to_list"):
                expected = expected.to_list()
            equal = value == expected
            comparisons.append((name, value, expected, equal))
            values_ok = values_ok and equal
            paths.append((name, path))

        scene_prop = bpy.context.scene.bl_rna.properties["frame_current"]
        with bpy.context.temp_override(
            button_pointer=bpy.context.scene,
            button_prop=scene_prop,
        ):
            prop_capture = CaptureState()
            prop_result = PME_OT_context_menu.execute(prop_capture, bpy.context)
            captured_prop = prop_capture.prop

        keymap = bpy.context.window_manager.keyconfigs.user.keymaps.new(
            name="PME Button Capture Smoke",
            space_type="EMPTY",
        )
        keymap_item = keymap.keymap_items.new(
            "object.select_all", "F24", "PRESS"
        )
        keymap_item.properties.action = "DESELECT"
        with bpy.context.temp_override(button_operator=keymap_item.properties):
            operator_capture = CaptureState()
            operator_result = PME_OT_context_menu.execute(
                operator_capture, bpy.context
            )
            captured_operator = operator_capture.operator
        keymap.keymap_items.remove(keymap_item)
        bpy.context.window_manager.keyconfigs.user.keymaps.remove(keymap)

        menu = prefs.add_pm(mode="DIALOG", name="PME Button Capture Smoke")
        menu_name = menu.name
        generated_prop = menu.pmis.add()
        prop_index = len(menu.pmis) - 1
        prop_selection = TypeSelection()
        prop_selection.mode = "PROP"
        prop_selection.pm_item = prop_index
        prop_selection.text = captured_prop
        prop_selection_result = WM_OT_pmi_type_select.execute(
            prop_selection, bpy.context
        )

        generated_operator = menu.pmis.add()
        operator_index = len(menu.pmis) - 1
        operator_selection = TypeSelection()
        operator_selection.mode = "COMMAND"
        operator_selection.pm_item = operator_index
        operator_selection.text = captured_operator
        operator_selection_result = WM_OT_pmi_type_select.execute(
            operator_selection, bpy.context
        )

        for name, path in paths:
            item = menu.pmis.add()
            item.name = name
            item.mode = "PROP"
            item.text = path

        generated_prop = menu.pmis[prop_index]
        generated_operator = menu.pmis[operator_index]
        print(
            "PME_BUTTON_CAPTURE_CONFIRMED",
            prop_selection_result,
            generated_prop.mode,
            generated_prop.text,
            operator_selection_result,
            generated_operator.mode,
            generated_operator.text,
            flush=True,
        )

        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            draw_result = bpy.ops.wm.pme_user_pie_menu_call(
                "INVOKE_DEFAULT",
                pie_menu_name=menu.name,
                invoke_mode="SUB",
                keymap="Window",
            )

        checks = {
            "all_paths": all(path for _, path in paths),
            "values": values_ok,
            "prop_context": "FINISHED" in prop_result,
            "prop_capture": captured_prop.startswith("C.scene.frame_current = "),
            "operator_context": "FINISHED" in operator_result,
            "operator_capture": (
                captured_operator == "bpy.ops.object.select_all(action='DESELECT')"
            ),
            "prop_confirmed": (
                "CANCELLED" in prop_selection_result
                and generated_prop.mode == "PROP"
                and generated_prop.text == "C.scene.frame_current"
            ),
            "operator_confirmed": (
                "CANCELLED" in operator_selection_result
                and generated_operator.mode == "COMMAND"
                and generated_operator.text == captured_operator
            ),
            "dialog_drawn": "CANCELLED" in draw_result,
        }
        print("PME_BUTTON_CAPTURE_PATHS", paths, flush=True)
        print("PME_BUTTON_CAPTURE_VALUES", comparisons, flush=True)
        print("PME_BUTTON_CAPTURE_PROP", captured_prop, flush=True)
        print("PME_BUTTON_CAPTURE_OPERATOR", captured_operator, flush=True)
        bpy.app.timers.register(
            lambda: verify_draw(checks), first_interval=1.0
        )
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_BUTTON_CAPTURE_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
