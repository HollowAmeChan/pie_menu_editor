import addon_utils
import bpy
from bpy.app.handlers import persistent
import hashlib
import json
import os
from pathlib import Path
import traceback


TAG = "PME_APP_TEMPLATE_SESSION_SMOKE"
SOURCE = Path(os.environ["PME_ACTUAL_JSON"])
state = {"step": 0, "checks": {}, "loaded": False, "success": False}


def export_digest(prefs):
    data = prefs.get_export_data(export_tags=False, mode="ALL")
    payload = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@persistent
def after_load(_):
    state["loaded"] = True
    print(TAG + "_LOAD_POST", bpy.app.version_string, bpy.context.scene.name, flush=True)


def finish(success):
    state["success"] = success
    if after_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(after_load)
    print(TAG + "_CHECKS", state["checks"], flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def run_step():
    try:
        if state["step"] == 0:
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

            result = bpy.ops.wm.pm_import(
                "EXEC_DEFAULT",
                filepath=str(SOURCE),
                mode="REPLACE",
                tags=TAG,
            )
            prefs = package.addon.get_prefs()
            imported = [pm for pm in prefs.pie_menus if pm.has_tag(TAG)]
            icon_names = sorted(package.previews_helper.ph.get_names())
            state.update(
                module=module,
                package=package,
                digest=export_digest(prefs),
                names=[pm.name for pm in imported],
                items=sum(len(pm.pmis) for pm in imported),
                icon_names=icon_names,
            )
            state["checks"]["import_finished"] = result == {"FINISHED"}
            state["checks"]["before_counts"] = (
                len(imported) == 85 and state["items"] == 759
            )
            state["checks"]["icons_loaded_before"] = (
                bool(icon_names)
                and all(package.previews_helper.ph.get_icon(name) > 0 for name in icon_names)
            )
            bpy.app.handlers.load_post.append(after_load)
            state["step"] = 1
            print(
                TAG + "_BEFORE",
                bpy.app.version_string,
                module.bl_info.get("version"),
                state["digest"],
                "icons=",
                len(icon_names),
                flush=True,
            )
            result = bpy.ops.wm.read_homefile(
                "EXEC_DEFAULT",
                app_template="2D_Animation",
                use_empty=False,
            )
            state["checks"]["read_homefile_finished"] = result == {"FINISHED"}
            return 0.5

        if not state["loaded"]:
            return 0.2

        package = state["package"]
        prefs = package.addon.get_prefs()
        imported = [pm for pm in prefs.pie_menus if pm.has_tag(TAG)]
        icon_names = sorted(package.previews_helper.ph.get_names())
        state["checks"]["addon_still_enabled"] = addon_utils.check(
            "pie_menu_editor"
        ) == (True, True)
        state["checks"]["preferences_available"] = prefs is not None
        state["checks"]["window_manager_state"] = hasattr(
            bpy.types.WindowManager, "pme"
        )
        state["checks"]["menu_names_preserved"] = (
            [pm.name for pm in imported] == state["names"]
        )
        state["checks"]["item_count_preserved"] = (
            sum(len(pm.pmis) for pm in imported) == state["items"]
        )
        state["checks"]["export_preserved"] = export_digest(prefs) == state["digest"]
        state["checks"]["icons_preserved"] = (
            icon_names == state["icon_names"]
            and all(package.previews_helper.ph.get_icon(name) > 0 for name in icon_names)
        )

        menu_name = next(pm.name for pm in imported if pm.mode == "PMENU")
        invoke_result = bpy.ops.wm.pme_user_pie_menu_call(
            "INVOKE_DEFAULT",
            pie_menu_name=menu_name,
            invoke_mode="SUB",
        )
        state["checks"]["pie_invoked_after_template"] = invoke_result in (
            {"CANCELLED"},
            {"RUNNING_MODAL"},
        )
        bpy.context.window.screen = bpy.context.window.screen
        print(
            TAG + "_AFTER",
            bpy.app.version_string,
            bpy.context.scene.name,
            export_digest(prefs),
            "menus=",
            len(imported),
            "icons=",
            len(icon_names),
            "pie=",
            invoke_result,
            flush=True,
        )
        return finish(all(state["checks"].values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


bpy.app.timers.register(run_step, first_interval=0.1, persistent=True)
