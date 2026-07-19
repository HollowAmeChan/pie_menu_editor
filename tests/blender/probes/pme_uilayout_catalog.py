import bpy
import json


catalog = {
    function.identifier: [parameter.identifier for parameter in function.parameters]
    for function in bpy.types.UILayout.bl_rna.functions
}
print("PME_UILAYOUT_CATALOG=" + json.dumps(catalog, sort_keys=True), flush=True)
