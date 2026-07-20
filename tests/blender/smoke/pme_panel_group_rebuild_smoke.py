import addon_utils
import bpy
import os
from pathlib import Path
import traceback


TAG = "PME_PANEL_GROUP_REBUILD_SMOKE"
FIXTURE = Path(
    os.environ.get(
        "PME_PANEL_FIXTURE",
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "pme_panel_group_fixture.json",
    )
)
checks = {}
warnings = []
success = False


def panel_state(panel_utils, name):
    panels = list(panel_utils._panels.get(name, ()))
    return panels, [
        getattr(bpy.types, panel.__name__, None) is panel and hasattr(panel, "bl_rna")
        for panel in panels
    ]


try:
    module = addon_utils.enable(
        "pie_menu_editor",
        default_set=True,
        persistent=False,
        handle_error=None,
    )
    package = module.core
    if not hasattr(bpy.types.WindowManager, "pme"):
        for waiter in package.PME_OT_wait_context.instances:
            waiter.cancelled = True
        package.on_context()

    panel_utils = package.panel_utils
    original_logw = panel_utils.logw
    panel_utils.logw = lambda *args, **kwargs: warnings.append((args, kwargs))
    try:
        result = bpy.ops.wm.pm_import(
            "EXEC_DEFAULT",
            filepath=str(FIXTURE),
            mode="REPLACE",
            tags=TAG,
        )
        prefs = package.addon.get_prefs()
        pm = next(pm for pm in prefs.pie_menus if pm.has_tag(TAG))
        panels, registered = panel_state(panel_utils, pm.name)
        checks["import_finished"] = result == {"FINISHED"}
        checks["initial_registered"] = len(panels) == 2 and all(registered)

        rebuild_states = []
        for _ in range(3):
            pm.update_panel_group()
            panels, registered = panel_state(panel_utils, pm.name)
            rebuild_states.append((len(panels), all(registered)))
        checks["repeated_rebuild"] = rebuild_states == [(2, True)] * 3

        prefs.active_pie_menu_idx = prefs.pie_menus.find(pm.name)
        move_result = bpy.ops.pme.panel_item_move(
            "EXEC_DEFAULT",
            old_idx=0,
            old_idx_last=-1,
            new_idx=1,
            swap=False,
        )
        panels, registered = panel_state(panel_utils, pm.name)
        checks["move_rebuild"] = (
            move_result == {"FINISHED"}
            and len(panels) == 2
            and all(registered)
            and [panel.bl_label for panel in panels] == ["Collections", "View"]
        )

        panel_utils.remove_panel_group(pm.name)
        panel_utils.remove_panel_group(pm.name)
        leaked = [
            panel.__name__
            for panel in panels
            if getattr(bpy.types, panel.__name__, None) is panel
        ]
        checks["remove_idempotent"] = pm.name not in panel_utils._panels and not leaked
        checks["no_unregister_warnings"] = not warnings
        print(
            TAG + "_DATA",
            bpy.app.version_string,
            module.bl_info.get("version"),
            "rebuilds=",
            rebuild_states,
            "warnings=",
            warnings,
            "leaked=",
            leaked,
            flush=True,
        )
        success = all(checks.values())
    finally:
        panel_utils.logw = original_logw
except Exception:
    traceback.print_exc()
finally:
    print(TAG + "_CHECKS", checks, flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
