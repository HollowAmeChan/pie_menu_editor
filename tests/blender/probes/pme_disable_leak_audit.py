import addon_utils
import bpy
import traceback


TAG = "PME_DISABLE_LEAK_AUDIT"
state = {"step": 0, "success": False}


def registered_class_names(core):
    classes = list(core.get_classes())
    classes.extend((core.PME_OT_wait_context, core.PME_OT_wait_keymaps))
    return sorted(
        cls.__name__
        for cls in classes
        if getattr(bpy.types, cls.__name__, None) is cls
    )


def finish(success):
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
            state["module"] = module
            state["step"] = 1
            return 0.25

        module = state["module"]
        core = module.core
        if state["step"] == 1:
            if not hasattr(bpy.types.WindowManager, "pme"):
                return 0.1
            before = registered_class_names(core)
            addon_utils.disable("pie_menu_editor", default_set=True, handle_error=None)
            state["before"] = before
            state["step"] = 2
            return 0.25

        leaked = registered_class_names(core)
        handlers = {
            "load_pre": core.load_pre_handler in bpy.app.handlers.load_pre,
            "load_post": core.load_post_handler in bpy.app.handlers.load_post,
            "load_post_context": core.load_post_context in bpy.app.handlers.load_post,
        }
        checks = {
            "classes_were_registered": len(state["before"]) > 100,
            "no_registered_classes": not leaked,
            "window_manager_pointer_removed": not hasattr(
                bpy.types.WindowManager, "pme"
            ),
            "handlers_removed": not any(handlers.values()),
            "addon_disabled": addon_utils.check("pie_menu_editor") == (False, False),
        }
        print(
            TAG + "_DATA",
            bpy.app.version_string,
            "before=",
            len(state["before"]),
            "leaked=",
            leaked,
            "handlers=",
            handlers,
            flush=True,
        )
        print(TAG + "_CHECKS", checks, flush=True)
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


bpy.app.timers.register(run_step, first_interval=0.1)
