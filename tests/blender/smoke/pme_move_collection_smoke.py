import addon_utils
import bpy
import traceback


MENU_NAME = "PME Move Collection Smoke"


def finish(success):
    try:
        from pie_menu_editor.core.addon import get_prefs

        prefs = get_prefs()
        menu = prefs.pie_menus.get(MENU_NAME)
        if menu is not None:
            prefs.remove_pm(menu)
    except Exception:
        traceback.print_exc()
        success = False
    print("PME_MOVE_COLLECTION_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()


def new_object(name):
    mesh = bpy.data.meshes.new(name + " Mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


def run():
    try:
        from pie_menu_editor.core import compatibility_fixes, pme
        from pie_menu_editor.core.addon import get_prefs
        from pie_menu_editor.core.bl_utils import object_move_to_collection

        scene = bpy.context.scene
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for collection in list(bpy.data.collections):
            bpy.data.collections.remove(collection)
        a = bpy.data.collections.new("PME A")
        a1 = bpy.data.collections.new("PME A1")
        b = bpy.data.collections.new("PME B")
        scene.collection.children.link(a)
        a.children.link(a1)
        scene.collection.children.link(b)
        targets = [scene.collection, a, a1, b]

        index_results = []
        for index, target in enumerate(targets):
            obj = new_object("PME Index %d" % index)
            result = object_move_to_collection(collection_index=index)
            index_results.append(
                "FINISHED" in result and list(obj.users_collection) == [target]
            )

        uid_results = []
        for index, target in enumerate(targets):
            obj = new_object("PME UID %d" % index)
            result = object_move_to_collection(collection_uid=target.session_uid)
            uid_results.append(
                "FINISHED" in result and list(obj.users_collection) == [target]
            )

        obj = new_object("PME Global")
        pme.context.exe("object_move_to_collection(collection_index=2)")
        global_result = list(obj.users_collection) == [a1]

        prefs = get_prefs()
        menu = prefs.add_pm(mode="DIALOG", name=MENU_NAME)
        item = menu.pmis[0]
        item.mode = "COMMAND"
        item.text = (
            "[bpy.ops.object.move_to_collection(collection_index=0) "
            "for obj in C.selected_objects]"
        )
        compatibility_fixes.fix(pms=[menu], version=(1, 19, 8))
        migrated = item.text == (
            "[object_move_to_collection(collection_index=0) "
            "for obj in C.selected_objects]"
        )

        try:
            object_move_to_collection(collection_index=99)
            invalid_rejected = False
        except IndexError:
            invalid_rejected = True

        checks = {
            "legacy_indices": all(index_results),
            "session_uids": all(uid_results),
            "global_available": global_result,
            "command_migrated": migrated,
            "invalid_rejected": invalid_rejected,
        }
        print(
            "PME_MOVE_COLLECTION_DATA",
            {
                "blender": bpy.app.version_string,
                "targets": [(target.name, target.session_uid) for target in targets],
                "index_results": index_results,
                "uid_results": uid_results,
                "migrated": item.text,
            },
            flush=True,
        )
        print("PME_MOVE_COLLECTION_CHECKS", checks, flush=True)
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
        print("PME_MOVE_COLLECTION_ENABLE", module.__file__ if module else None, flush=True)
        bpy.app.timers.register(run, first_interval=1.0)
    except Exception:
        traceback.print_exc()
        finish(False)
    return None


bpy.app.timers.register(enable, first_interval=0.2)
