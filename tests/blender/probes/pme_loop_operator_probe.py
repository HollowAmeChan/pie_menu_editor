import bpy


for name in (
    "loop_multi_select",
    "select_edge_loop_multi",
    "select_edge_ring_multi",
    "select_boundary_loop_multi",
):
    operator = getattr(bpy.ops.mesh, name)
    try:
        rna = operator.get_rna_type()
    except KeyError:
        print("PME_LOOP_OPERATOR", name, None, flush=True)
        continue
    properties = [
        (prop.identifier, prop.type, getattr(prop, "default", None))
        for prop in rna.properties
        if prop.identifier != "rna_type"
    ]
    print("PME_LOOP_OPERATOR", name, properties, flush=True)
