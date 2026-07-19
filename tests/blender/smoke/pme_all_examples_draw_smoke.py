import addon_utils
import bpy
import json
import traceback
from pathlib import Path


TAG = "PME_ALL_EXAMPLES_DRAW_SMOKE"
errors = []
drawn = []


class PME_MT_all_examples_draw_smoke(bpy.types.Menu):
    bl_idname = "PME_MT_all_examples_draw_smoke"
    bl_label = "PME all examples draw smoke"

    def draw(self, context):
        from pie_menu_editor.core.addon import get_prefs
        from pie_menu_editor.core.layout_helper import lh
        from pie_menu_editor.core.operators import WM_OT_pme_user_pie_menu_call

        prefs = get_prefs()
        for pm in prefs.pie_menus:
            if not pm.has_tag(TAG) or pm.mode not in {"PMENU", "DIALOG", "RMENU"}:
                continue
            layout = self.layout.column()
            lh.lt(layout, operator_context="INVOKE_DEFAULT")
            for index, item in enumerate(pm.pmis):
                if item.mode == "EMPTY":
                    continue
                try:
                    WM_OT_pme_user_pie_menu_call._draw_item(
                        prefs, pm, item, index
                    )
                    drawn.append((pm.name, index, item.mode))
                except Exception:
                    errors.append((pm.name, index, item.mode, traceback.format_exc()))


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

    operators = module.core.operators
    layout_helper = module.core.layout_helper
    original_print_exc = operators.print_exc
    original_layout_error = layout_helper.LayoutHelper.error

    def capture_print_exc(*args, **kwargs):
        errors.append(("print_exc", args, kwargs, traceback.format_exc()))

    def capture_layout_error(self, text, message=None):
        errors.append(("layout_error", text, message))

    operators.print_exc = capture_print_exc
    layout_helper.LayoutHelper.error = capture_layout_error

    examples = Path(module.__file__).parent / "examples"
    expected_count = 0
    import_results = {}
    for filepath in sorted(examples.glob("*.json")):
        payload = json.loads(filepath.read_text(encoding="utf-8"))
        expected_count += len(payload["menus"])
        result = bpy.ops.wm.pm_import(
            "EXEC_DEFAULT",
            filepath=str(filepath),
            mode="RENAME",
            tags=TAG,
        )
        import_results[filepath.name] = sorted(result)

    prefs = module.core.addon.get_prefs()
    imported = [pm for pm in prefs.pie_menus if pm.has_tag(TAG)]
    visible = [
        pm for pm in imported if pm.mode in {"PMENU", "DIALOG", "RMENU"}
    ]
    expected_drawn = sum(
        item.mode != "EMPTY" for pm in visible for item in pm.pmis
    )

    bpy.utils.register_class(PME_MT_all_examples_draw_smoke)
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
        menu_result = bpy.ops.wm.call_menu(
            name=PME_MT_all_examples_draw_smoke.bl_idname
        )

    property_names = {"Edge Crease", "Edge Bevel Weight"}
    checks = {
        "all_import_calls": all(
            result == ["FINISHED"] for result in import_results.values()
        ),
        "menu_count": len(imported) == expected_count,
        "visible_count": len(visible) == 8,
        "properties_registered": all(
            hasattr(prefs.props, name) for name in property_names
        ),
        "menu_interface": menu_result == {"INTERFACE"},
        "items_drawn": len(drawn) == expected_drawn,
        "no_draw_errors": not errors,
    }
    print(
        "PME_ALL_EXAMPLES_DRAW_DATA",
        bpy.app.version_string,
        "imports=",
        import_results,
        "menus=",
        len(imported),
        "visible=",
        len(visible),
        "drawn=",
        len(drawn),
        flush=True,
    )
    print("PME_ALL_EXAMPLES_DRAW_ERRORS", errors, flush=True)
    print("PME_ALL_EXAMPLES_DRAW_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    try:
        operators.print_exc = original_print_exc
        layout_helper.LayoutHelper.error = original_layout_error
    except Exception:
        pass
    print(
        "PME_ALL_EXAMPLES_DRAW_RESULT",
        "OK" if success else "FAILED",
        flush=True,
    )
    bpy.ops.wm.quit_blender()
