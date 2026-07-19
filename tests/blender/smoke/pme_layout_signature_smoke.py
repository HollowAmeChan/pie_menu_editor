import addon_utils
import bpy
import inspect
import traceback


TAG = "PME_LAYOUT_SIGNATURE_SMOKE"


def finish(success, checks=None):
    print(TAG + "_CHECKS", checks or {}, flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def run():
    try:
        from pie_menu_editor.core.panel_utils import PLayout

        missing = {}
        for name, function in bpy.types.UILayout.bl_rna.functions.items():
            wrapper = getattr(PLayout, name, None)
            if wrapper is None:
                continue
            signature = inspect.signature(wrapper)
            parameters = signature.parameters
            if any(
                parameter.kind == inspect.Parameter.VAR_KEYWORD
                for parameter in parameters.values()
            ):
                continue
            native = [parameter.identifier for parameter in function.parameters]
            absent = [parameter for parameter in native if parameter not in parameters]
            if absent:
                missing[name] = absent

        calls = []
        original_btn_operator = PLayout.btn_operator
        PLayout.btn_operator = lambda *args, **kwargs: calls.append((args, kwargs))
        try:
            PLayout.prop(
                bpy.context.scene,
                "frame_start",
                placeholder="Frame",
                invert_checkbox=True,
                text_align='RIGHT',
            )
            PLayout.prop_search(
                bpy.context.scene,
                "camera",
                bpy.data,
                "objects",
                results_are_suggestions=True,
                item_search_property="name",
            )
            PLayout.template_curve_mapping(
                bpy.context.scene,
                "frame_start",
                show_tone=True,
                show_presets=True,
            )
            PLayout.operator(
                "wm.save_mainfile",
                depress=True,
                search_weight=1.0,
                properties=None,
            )
            PLayout.operator_enum("object.mode_set", "mode", icon_only=True)
            PLayout.operator_menu_enum(
                "object.mode_set",
                "mode",
                properties=None,
            )
            PLayout.template_ID(
                bpy.context.scene,
                "camera",
                filter='AVAILABLE',
                live_icon=True,
                text="Camera",
            )
            PLayout.template_ID_preview(
                bpy.context.scene,
                "camera",
                filter='AVAILABLE',
                hide_buttons=True,
            )
            PLayout.template_icon_view(
                bpy.context.scene,
                "frame_start",
                scale_popup=4.0,
            )
            PLayout.template_list(
                "UI_UL_list",
                "",
                bpy.context.scene,
                "objects",
                bpy.context.scene,
                "frame_current",
                sort_reverse=True,
                sort_lock=True,
            )
            PLayout.template_palette(
                bpy.context.scene,
                "camera",
                color=True,
            )
        finally:
            PLayout.btn_operator = original_btn_operator

        checks = {
            "native_parameters_covered": not missing,
            "new_keywords_accepted": len(calls) == 11,
        }
        print(TAG + "_MISSING", missing, flush=True)
        print(TAG + "_VERSION", bpy.app.version_string, flush=True)
        return finish(all(checks.values()), checks)
    except Exception:
        traceback.print_exc()
        return finish(False)


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor",
            default_set=True,
            persistent=False,
            handle_error=None,
        )
        print(TAG + "_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
