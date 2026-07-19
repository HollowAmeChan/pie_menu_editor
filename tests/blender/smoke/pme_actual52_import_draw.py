from collections import Counter
import addon_utils
import bpy
import json
import os
from pathlib import Path
import traceback


TAG = "PME_ACTUAL52_IMPORT"
SOURCE = Path(os.environ["PME_ACTUAL_JSON"])
OUTPUT = Path(os.environ["PME_ACTUAL_ROUNDTRIP"])
ERROR_OUTPUT = Path(os.environ["PME_ACTUAL_ERRORS"])
errors = []
drawn = []


class PME_MT_actual52_draw(bpy.types.Menu):
    bl_idname = "PME_MT_actual52_draw"
    bl_label = "PME actual configuration draw"

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
                    WM_OT_pme_user_pie_menu_call._draw_item(prefs, pm, item, index)
                    drawn.append((pm.name, index, item.mode))
                except Exception:
                    errors.append(
                        {
                            "kind": "exception",
                            "menu": pm.name,
                            "index": index,
                            "mode": item.mode,
                            "traceback": traceback.format_exc(),
                        }
                    )


success = False
registered = False
original_print_exc = None
original_layout_error = None
try:
    expected = json.loads(SOURCE.read_text(encoding="utf-8"))
    expected_menus = expected["menus"]
    expected_names = [menu[0] for menu in expected_menus]
    expected_item_count = sum(len(menu[3]) for menu in expected_menus)
    expected_modes = Counter(menu[4] for menu in expected_menus)

    dependency_results = {}
    for dependency in filter(None, os.environ.get("PME_DEPENDENCIES", "").split(",")):
        try:
            dependency_module = addon_utils.enable(
                dependency,
                default_set=True,
                persistent=False,
                handle_error=None,
            )
            dependency_results[dependency] = {
                "enabled": dependency_module is not None,
                "path": getattr(dependency_module, "__file__", ""),
            }
        except Exception:
            dependency_results[dependency] = {
                "enabled": False,
                "last_line": traceback.format_exc().strip().splitlines()[-1],
            }

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
        errors.append(
            {
                "kind": "print_exc",
                "args": repr(args),
                "kwargs": repr(kwargs),
                "traceback": traceback.format_exc(),
            }
        )

    def capture_layout_error(self, text, message=None):
        errors.append(
            {
                "kind": "layout_error",
                "text": str(text),
                "message": str(message),
            }
        )

    operators.print_exc = capture_print_exc
    layout_helper.LayoutHelper.error = capture_layout_error

    prefs = module.core.addon.get_prefs()
    before_names = [pm.name for pm in prefs.pie_menus]
    import_result = bpy.ops.wm.pm_import(
        "EXEC_DEFAULT",
        filepath=str(SOURCE),
        mode="REPLACE",
        tags=TAG,
    )
    imported = [pm for pm in prefs.pie_menus if pm.has_tag(TAG)]
    imported_names = [pm.name for pm in imported]
    imported_item_count = sum(len(pm.pmis) for pm in imported)
    imported_modes = Counter(pm.mode for pm in imported)
    texts = [item.text for pm in imported for item in pm.pmis]

    roundtrip = prefs.get_export_data(export_tags=False, mode="ALL")
    OUTPUT.write_text(
        json.dumps(roundtrip, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    bpy.utils.register_class(PME_MT_actual52_draw)
    registered = True
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
        menu_result = bpy.ops.wm.call_menu(name=PME_MT_actual52_draw.bl_idname)

    visible = [pm for pm in imported if pm.mode in {"PMENU", "DIALOG", "RMENU"}]
    expected_drawn = sum(
        item.mode != "EMPTY" for pm in visible for item in pm.pmis
    )
    checks = {
        "expected_addon_path": os.path.normcase(module.__file__).startswith(
            os.path.normcase(os.environ["PME_EXPECTED_ADDON_ROOT"])
        ),
        "import_finished": import_result == {"FINISHED"},
        "menu_count": len(imported) == len(expected_menus),
        "menu_names": set(imported_names) == set(expected_names),
        "item_count": imported_item_count == expected_item_count,
        "mode_distribution": imported_modes == expected_modes,
        "legacy_curve_removed": not any(
            "bpy.ops.brush.curve_preset" in text for text in texts
        ),
        "curve_migration_count": sum(
            "set_brush_curve_preset" in text for text in texts
        ) == 6,
        "legacy_automasking_removed": not any(
            "paint_settings().brush.use_automasking_boundary_edges" in text
            for text in texts
        ),
        "automasking_migration_count": sum(
            "mesh_automasking_settings(paint_settings().brush).use_automasking_boundary_edges"
            in text
            for text in texts
        ) == 1,
        "roundtrip_written": OUTPUT.is_file() and OUTPUT.stat().st_size > 0,
        "menu_interface": menu_result == {"INTERFACE"},
        "items_drawn": len(drawn) == expected_drawn,
    }
    error_counts = Counter(error["kind"] for error in errors)
    print(
        "PME_ACTUAL52_IMPORT_DATA",
        bpy.app.version_string,
        "addon=",
        module.bl_info.get("version"),
        "before=",
        len(before_names),
        "imported=",
        len(imported),
        "items=",
        imported_item_count,
        "modes=",
        dict(sorted(imported_modes.items())),
        "visible=",
        len(visible),
        "drawn=",
        len(drawn),
        "errors=",
        dict(error_counts),
        "dependencies=",
        dependency_results,
        flush=True,
    )
    ERROR_OUTPUT.write_text(
        json.dumps(errors, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    error_samples = []
    for error in errors[:12]:
        sample = {key: value for key, value in error.items() if key != "traceback"}
        if "traceback" in error:
            lines = error["traceback"].strip().splitlines()
            sample["last_line"] = lines[-1] if lines else ""
        error_samples.append(sample)
    print(
        "PME_ACTUAL52_IMPORT_ERROR_SAMPLES",
        json.dumps(error_samples, ensure_ascii=False),
        "file=",
        str(ERROR_OUTPUT),
        flush=True,
    )
    print("PME_ACTUAL52_IMPORT_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    try:
        if original_print_exc is not None:
            operators.print_exc = original_print_exc
        if original_layout_error is not None:
            layout_helper.LayoutHelper.error = original_layout_error
        if registered:
            bpy.utils.unregister_class(PME_MT_actual52_draw)
    except Exception:
        traceback.print_exc()
    print("PME_ACTUAL52_IMPORT_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
