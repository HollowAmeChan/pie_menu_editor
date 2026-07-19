import addon_utils
import bpy
import shutil
import traceback
from pathlib import Path


created = None


def finish(success):
    try:
        if created and created.exists():
            created.unlink()
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_ICON_REFRESH_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def run():
    global created
    try:
        from pie_menu_editor.core.previews_helper import ph

        source = Path(ph.path) / "p1.png"
        created = Path(ph.path) / "pme_refresh_smoke.png"
        if created.exists():
            created.unlink()
        old_id = ph.get_icon("pPress")
        shutil.copyfile(source, created)
        before = ph.has_icon("pme_refresh_smoke")
        result = bpy.ops.pme.icons_refresh()
        after = ph.has_icon("pme_refresh_smoke")
        new_id = ph.get_icon("pme_refresh_smoke")
        stable_id = ph.get_icon("pPress")
        checks = {
            "not_loaded_before": not before,
            "operator_finished": "FINISHED" in result,
            "loaded_after": after and new_id > 0,
            "existing_id_stable": old_id > 0 and stable_id == old_id,
        }
        print("PME_ICON_REFRESH_CHECKS", checks, flush=True)
        print(
            "PME_ICON_REFRESH_IDS",
            {"old": old_id, "stable": stable_id, "new": new_id},
            flush=True,
        )
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_ICON_REFRESH_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
