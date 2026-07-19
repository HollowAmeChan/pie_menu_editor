import addon_utils
import bpy
import traceback


def finish(success):
    print("PME_GN_PROBE_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def run():
    try:
        from pie_menu_editor.core import pme
        from pie_menu_editor.core.bl_utils import gen_prop_path
        from pie_menu_editor.core.preferences import PME_OT_context_menu

        obj = bpy.context.active_object
        group = bpy.data.node_groups.new("PME GN Probe", "GeometryNodeTree")
        group.interface.new_socket(
            name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry"
        )
        value_socket = group.interface.new_socket(
            name="Value", in_out="INPUT", socket_type="NodeSocketFloat"
        )
        group.interface.new_socket(
            name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry"
        )
        modifier = obj.modifiers.new("PME GN Probe", "NODES")
        modifier.node_group = group

        try:
            modifier_keys = list(modifier.keys())
        except TypeError as exc:
            modifier_keys = type(exc).__name__
        data = {
            "blender": bpy.app.version_string,
            "socket_identifier": value_socket.identifier,
            "modifier_keys": modifier_keys,
            "has_properties": hasattr(modifier, "properties"),
        }
        checks = {"modifier_created": modifier.node_group == group}

        if bpy.app.version >= (5, 2, 0):
            inputs = modifier.properties.inputs
            indexed_item = inputs[value_socket.identifier]
            item = getattr(inputs, value_socket.identifier)
            prop = item.bl_rna.properties["value"]
            path = gen_prop_path(item, prop)
            value = pme.context.eval(path)

            class Capture:
                prop = ""
                operator = ""
                name = ""

                def draw_menu(self, menu, context):
                    pass

            with bpy.context.temp_override(button_pointer=item, button_prop=prop):
                capture = Capture()
                capture_result = PME_OT_context_menu.execute(capture, bpy.context)

            data.update(
                inputs_type=type(inputs).__name__,
                inputs_rna=inputs.bl_rna.identifier,
                indexed_type=type(indexed_item).__name__,
                attribute_type=type(item).__name__,
                item_repr=repr(item),
                item_path=item.path_from_id("value"),
                generated_path=path,
                generated_value=value,
                captured=capture.prop,
            )
            checks.update(
                path_generated=bool(path),
                path_evaluates=value == item.value,
                capture_finished="FINISHED" in capture_result,
                captured_assignment=capture.prop.startswith(path + " = "),
            )
        else:
            identifier = value_socket.identifier
            modifier[identifier] = 0.25
            data.update(
                legacy_identifier=identifier,
                legacy_value=modifier[identifier],
            )
            checks.update(legacy_value=modifier[identifier] == 0.25)

        print("PME_GN_PROBE_DATA", data, flush=True)
        print("PME_GN_PROBE_CHECKS", checks, flush=True)
        finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_GN_PROBE_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
