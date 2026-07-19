import addon_utils
import bpy
import traceback


MENU_NAME = "PME Geometry Nodes Compatibility Smoke"


class RecordingLayout:
    def __init__(self):
        self.calls = []

    def prop(self, owner, prop, **kwargs):
        self.calls.append((owner, prop, kwargs))
        if prop.startswith("["):
            return owner[prop[2:-2]]
        return getattr(owner, prop)


def finish(success):
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        menu = prefs.pie_menus.get(MENU_NAME)
        if menu is not None:
            prefs.remove_pm(menu)
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_GN_COMPAT_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def run():
    try:
        from pie_menu_editor.core import compatibility_fixes, pme
        from pie_menu_editor.core.addon import get_prefs
        from pie_menu_editor.core.bl_utils import (
            geometry_nodes_input,
            get_geometry_nodes_input,
        )

        obj = bpy.context.active_object
        group = bpy.data.node_groups.new("PME GN Compat", "GeometryNodeTree")
        group.interface.new_socket(
            name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry"
        )
        socket = group.interface.new_socket(
            name="Value", in_out="INPUT", socket_type="NodeSocketFloat"
        )
        group.interface.new_socket(
            name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry"
        )
        modifier = obj.modifiers.new("PME GN Compat", "NODES")
        modifier.node_group = group
        identifier = socket.identifier
        identifiers = [
            identifier,
            identifier + "_use_attribute",
            identifier + "_attribute_name",
        ]
        initial_values = [0.25, True, "density"]
        final_values = [0.75, False, "weight"]
        if bpy.app.version >= (5, 2, 0):
            input_item = getattr(modifier.properties.inputs, identifier)
            input_item.value = initial_values[0]
            input_item.type = 'ATTRIBUTE'
            input_item.attribute_name = initial_values[2]
        else:
            for key, value in zip(identifiers, initial_values):
                modifier[key] = value

        prefs = get_prefs()
        menu = prefs.add_pm(mode="DIALOG", name=MENU_NAME)
        prop_items = []
        command_items = []
        prop_names = []
        command_names = []
        for key, value in zip(identifiers, final_values):
            path = f'C.object.modifiers["PME GN Compat"]["{key}"]'
            prop_item = menu.pmis.add()
            prop_item.name = key
            prop_item.mode = "PROP"
            prop_item.text = path
            prop_items.append(prop_item)
            prop_names.append(prop_item.name)
            command_item = menu.pmis.add()
            command_item.name = "Set " + key
            command_item.mode = "COMMAND"
            command_item.text = path + " = " + repr(value)
            command_items.append(command_item)
            command_names.append(command_item.name)
        compatibility_fixes.fix_1_19_13(prefs, menu)
        prop_items = [menu.pmis[name] for name in prop_names]
        command_items = [menu.pmis[name] for name in command_names]

        layout = RecordingLayout()
        for key in identifiers:
            geometry_nodes_input(layout, modifier, key, text=key)
        before = [get_geometry_nodes_input(modifier, key) for key in identifiers]
        for command_item in command_items:
            pme.context.exe(command_item.text, use_try=False)
        after = [get_geometry_nodes_input(modifier, key) for key in identifiers]

        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            draw_result = bpy.ops.wm.pme_user_pie_menu_call(
                "INVOKE_DEFAULT",
                pie_menu_name=menu.name,
                invoke_mode="SUB",
                keymap="Window",
            )

        expected_props = (
            ["value", "type", "attribute_name"]
            if bpy.app.version >= (5, 2, 0)
            else [f'["{key}"]' for key in identifiers]
        )
        checks = {
            "props_migrated": all(
                item.mode == "CUSTOM"
                and item.text == (
                    "geometry_nodes_input(L, "
                    f'C.object.modifiers["PME GN Compat"], {key!r})'
                )
                for item, key in zip(prop_items, identifiers)
            ),
            "commands_migrated": all(
                item.text == (
                    "set_geometry_nodes_input("
                    f'C.object.modifiers["PME GN Compat"], {key!r}, {value!r})'
                )
                for item, key, value in zip(
                    command_items, identifiers, final_values
                )
            ),
            "layout_owners": len(layout.calls) == 3,
            "layout_properties": [call[1] for call in layout.calls]
            == expected_props,
            "values_before": before == initial_values,
            "values_after": after == final_values,
            "menu_drawn": "CANCELLED" in draw_result,
        }
        print(
            "PME_GN_COMPAT_DATA",
            {
                "blender": bpy.app.version_string,
                "identifier": identifier,
                "props": [(item.mode, item.text) for item in prop_items],
                "commands": [item.text for item in command_items],
                "layout_properties": [call[1] for call in layout.calls],
                "before": before,
                "after": after,
            },
            flush=True,
        )
        print("PME_GN_COMPAT_CHECKS", checks, flush=True)
        bpy.app.timers.register(
            lambda: finish(all(checks.values())), first_interval=1.0
        )
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_GN_COMPAT_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
