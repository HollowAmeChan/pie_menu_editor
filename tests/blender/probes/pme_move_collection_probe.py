import bpy


scene = bpy.context.scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)

a = bpy.data.collections.new("A")
a1 = bpy.data.collections.new("A1")
b = bpy.data.collections.new("B")
scene.collection.children.link(a)
a.children.link(a1)
scene.collection.children.link(b)

collections = [scene.collection, a, a1, b]
print(
    "PME_MOVE_COLLECTION_TREE",
    [(collection.name, collection.session_uid) for collection in collections],
    flush=True,
)

for index, collection in enumerate(collections):
    mesh = bpy.data.meshes.new("Mesh%d" % index)
    obj = bpy.data.objects.new("Object%d" % index, mesh)
    scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if bpy.app.version < (5, 0, 0):
        try:
            result = bpy.ops.object.move_to_collection(collection_index=index)
        except Exception as exc:
            result = repr(exc)
    else:
        try:
            result = bpy.ops.object.move_to_collection(
                collection_uid=collection.session_uid
            )
        except Exception as exc:
            result = repr(exc)
    print(
        "PME_MOVE_COLLECTION_CASE",
        index,
        collection.name,
        result,
        [item.name for item in obj.users_collection],
        flush=True,
    )
    obj.select_set(False)
