import bpy


operator = bpy.ops.mesh.loop_multi_select
print(
    "PME_MISSING_PROXY",
    operator,
    operator.idname(),
    hasattr(operator, "get_rna_type"),
    flush=True,
)
try:
    print("PME_MISSING_RNA", operator.get_rna_type(), flush=True)
except Exception as error:
    print(
        "PME_MISSING_RNA_ERROR",
        type(error).__name__,
        str(error),
        flush=True,
    )
