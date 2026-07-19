import bpy


queries = {
    "mesh": ("mirror", "uv"),
    "brush": ("curve", "preset", "falloff"),
    "sculpt": ("sample", "color"),
    "paint": ("sample", "color"),
}

for module_name, terms in queries.items():
    module = getattr(bpy.ops, module_name)
    for name in sorted(dir(module)):
        if not any(term in name for term in terms):
            continue
        operator = getattr(module, name)
        try:
            rna = operator.get_rna_type()
        except KeyError:
            continue
        properties = [
            (prop.identifier, prop.type, getattr(prop, "default", None))
            for prop in rna.properties
            if prop.identifier != "rna_type"
        ]
        print("PME_CANDIDATE", module_name, name, properties, flush=True)
