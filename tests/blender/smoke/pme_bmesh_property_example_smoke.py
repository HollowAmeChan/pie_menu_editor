import addon_utils
import bpy
import bmesh
import traceback
from pathlib import Path


MENU_NAMES = ("Edge Crease", "Edge Bevel Weight")


def finish(success):
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        for name in MENU_NAMES:
            menu = prefs.pie_menus.get(name)
            if menu is not None:
                prefs.remove_pm(menu)
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_BMESH_EXAMPLE_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def run():
    try:
        from pie_menu_editor.core import compatibility_fixes
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        menus = [prefs.pie_menus[name] for name in MENU_NAMES]
        legacy_item = menus[0].pmis.add()
        legacy_item.name = "Migration Probe"
        legacy_item.mode = "COMMAND"
        legacy_item.text = "l = bm.edges.layers.crease.verify()"
        compatibility_fixes.fix_1_19_14(prefs, menus[0])
        migrated = (
            "bm.edges.layers.float.get(\"crease_edge\")" in legacy_item.text
            and "layers.crease" not in legacy_item.text
        )

        obj = bpy.context.active_object
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")

        initial = [getattr(prefs.props, name) for name in MENU_NAMES]
        setattr(prefs.props, MENU_NAMES[0], 0.35)
        setattr(prefs.props, MENU_NAMES[1], 0.65)
        values = [getattr(prefs.props, name) for name in MENU_NAMES]

        bm = bmesh.from_edit_mesh(obj.data)
        crease = bm.edges.layers.float.get("crease_edge")
        bevel = bm.edges.layers.float.get("bevel_weight_edge")
        selected = [edge for edge in bm.edges if edge.select]
        layer_values = (
            [edge[crease] for edge in selected] if crease else [],
            [edge[bevel] for edge in selected] if bevel else [],
        )
        texts = [item.text for menu in menus for item in menu.pmis]
        checks = {
            "menus_imported": len(menus) == 2,
            "legacy_migrated": migrated,
            "no_legacy_api": not any(
                "layers.crease" in text or "layers.bevel_weight" in text
                for text in texts
            ),
            "initial_zero": all(abs(value) < 1e-6 for value in initial),
            "getters": abs(values[0] - 0.35) < 1e-5
            and abs(values[1] - 0.65) < 1e-5,
            "layers_created": crease is not None and bevel is not None,
            "crease_written": layer_values[0]
            and all(abs(value - 0.35) < 1e-5 for value in layer_values[0]),
            "bevel_written": layer_values[1]
            and all(abs(value - 0.65) < 1e-5 for value in layer_values[1]),
        }
        print(
            "PME_BMESH_EXAMPLE_DATA",
            {
                "blender": bpy.app.version_string,
                "initial": initial,
                "values": values,
                "layers": list(bm.edges.layers.float.keys()),
                "selected": len(selected),
            },
            flush=True,
        )
        print("PME_BMESH_EXAMPLE_CHECKS", checks, flush=True)
        finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


def import_example():
    try:
        import pie_menu_editor

        example_path = (
            Path(pie_menu_editor.__file__).parent
            / "examples"
            / "mesh_edge_crease_and_bevel_weight_properties.json"
        )
        result = bpy.ops.wm.pm_import(
            "EXEC_DEFAULT",
            filepath=str(example_path),
            mode="RENAME",
            tags="PME_BMESH_EXAMPLE_SMOKE",
        )
        print("PME_BMESH_EXAMPLE_IMPORT", result, flush=True)
        if "FINISHED" not in result:
            return finish(False)
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


def enable():
    try:
        module = addon_utils.enable(
            "pie_menu_editor", default_set=True, persistent=False, handle_error=None
        )
        print("PME_BMESH_EXAMPLE_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(import_example, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
