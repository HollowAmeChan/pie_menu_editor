import addon_utils
import bpy
import os
import traceback
from pathlib import Path


addon_root = None
runtime_script = None
lifecycle_scripts = []
version_suffix = "%d%d" % bpy.app.version[:2]


def marker_id(name):
    return "%s_%s" % (name, version_suffix)


def marker(name):
    return bpy.app.driver_namespace.get(marker_id(name), 0)


def prepare_lifecycle_scripts():
    global addon_root
    addon_root = Path(__file__).resolve().parents[3]
    for folder, name in (
        ("autorun", "PME_AUTORUN_SMOKE"),
        ("register", "PME_REGISTER_SMOKE"),
        ("unregister", "PME_UNREGISTER_SMOKE"),
    ):
        script_dir = addon_root / "scripts" / folder
        script_dir.mkdir(parents=True, exist_ok=True)
        script = script_dir / ("pme_lifecycle_smoke_%s.py" % version_suffix)
        marker_name = marker_id(name)
        script.write_text(
            "key = %r\n"
            "bpy.app.driver_namespace[key] = "
            "bpy.app.driver_namespace.get(key, 0) + 1\n" % marker_name,
            encoding="utf-8",
        )
        lifecycle_scripts.append(script)


def cleanup():
    paths = list(lifecycle_scripts)
    for folder in ("autorun", "register", "unregister"):
        paths.extend(
            (addon_root / "scripts" / folder).glob(
                "__pycache__/pme_lifecycle_smoke_*.*.pyc"
            )
        )
    if runtime_script:
        paths.append(runtime_script)
        paths.extend(
            runtime_script.parent.glob(
                "__pycache__/%s.*.pyc" % runtime_script.stem
            )
        )
    for filepath in paths:
        try:
            filepath.unlink(missing_ok=True)
        except Exception:
            traceback.print_exc()


def finish(success):
    cleanup()
    print(
        "PME_SCRIPT_LIFECYCLE_MARKERS",
        {
            "autorun": marker("PME_AUTORUN_SMOKE"),
            "register": marker("PME_REGISTER_SMOKE"),
            "unregister": marker("PME_UNREGISTER_SMOKE"),
        },
        flush=True,
    )
    print("PME_SCRIPT_LIFECYCLE_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify_second_disable():
    checks = {
        "addon_disabled": "pie_menu_editor" not in bpy.context.preferences.addons,
        "unregister_twice": marker("PME_UNREGISTER_SMOKE") == 2,
    }
    print("PME_SCRIPT_SECOND_DISABLE", checks, flush=True)
    return finish(all(checks.values()))


def second_disable():
    try:
        addon_utils.disable("pie_menu_editor", default_set=True, handle_error=None)
        bpy.app.timers.register(verify_second_disable, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def verify_reenabled():
    checks = {
        "addon_enabled": "pie_menu_editor" in bpy.context.preferences.addons,
        "autorun_twice": marker("PME_AUTORUN_SMOKE") == 2,
        "register_twice": marker("PME_REGISTER_SMOKE") == 2,
        "unregister_once": marker("PME_UNREGISTER_SMOKE") == 1,
    }
    print("PME_SCRIPT_REENABLE", checks, flush=True)
    if not all(checks.values()):
        return finish(False)
    bpy.app.timers.register(second_disable, first_interval=0.5)
    return None


def reenable():
    try:
        addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        bpy.app.timers.register(verify_reenabled, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def first_disable():
    try:
        addon_utils.disable("pie_menu_editor", default_set=True, handle_error=None)
        checks = {
            "unregister_once": marker("PME_UNREGISTER_SMOKE") == 1,
            "addon_disabled": "pie_menu_editor" not in bpy.context.preferences.addons,
        }
        print("PME_SCRIPT_FIRST_DISABLE", checks, flush=True)
        if not all(checks.values()):
            return finish(False)
        bpy.app.timers.register(reenable, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def run_cached_script_checks():
    global addon_root, runtime_script
    try:
        import pie_menu_editor
        from pie_menu_editor.core.addon import get_prefs
        from pie_menu_editor.core.ui_utils import execute_script

        addon_root = Path(pie_menu_editor.__file__).parent
        runtime_script = addon_root / "scripts" / (
            "pme_runtime_smoke_%s.py" % version_suffix
        )

        preferences = get_prefs()
        preferences.cache_scripts = True
        runtime_script.write_text("return_value = kwargs['value'] + 1\n", encoding="utf-8")
        first = execute_script(str(runtime_script), value=10)
        pycs = list(
            runtime_script.parent.glob(
                "__pycache__/%s.*.pyc" % runtime_script.stem
            )
        )

        runtime_script.write_text("return_value = kwargs['value'] + 2\n", encoding="utf-8")
        future = runtime_script.stat().st_mtime + 2
        os.utime(runtime_script, (future, future))
        second = execute_script(str(runtime_script), value=10)

        preferences.cache_scripts = False
        runtime_script.write_text("return_value = kwargs['value'] + 3\n", encoding="utf-8")
        third = execute_script(str(runtime_script), value=10)

        checks = {
            "autorun_once": marker("PME_AUTORUN_SMOKE") == 1,
            "register_once": marker("PME_REGISTER_SMOKE") == 1,
            "cache_created": len(pycs) == 1 and pycs[0].stat().st_size > 16,
            "first_result": first == 11,
            "source_recompiled": second == 12,
            "uncached_result": third == 13,
        }
        print("PME_SCRIPT_CACHE_CHECKS", checks, flush=True)
        print(
            "PME_SCRIPT_CACHE_DATA",
            {"python": tuple(os.sys.version_info[:3]), "pyc": [p.name for p in pycs]},
            flush=True,
        )
        if not all(checks.values()):
            return finish(False)
        bpy.app.timers.register(first_disable, first_interval=0.5)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


def enable():
    for name in (
        "PME_AUTORUN_SMOKE",
        "PME_REGISTER_SMOKE",
        "PME_UNREGISTER_SMOKE",
    ):
        bpy.app.driver_namespace.pop(marker_id(name), None)
    try:
        prepare_lifecycle_scripts()
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_SCRIPT_LIFECYCLE_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run_cached_script_checks, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        return finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
