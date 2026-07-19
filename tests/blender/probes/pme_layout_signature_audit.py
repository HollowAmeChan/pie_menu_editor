import ast
import bpy
import json
from pathlib import Path


path = Path(__file__).resolve().parents[3] / "core" / "panel_utils.py"
with path.open("r", encoding="utf-8") as source:
    tree = ast.parse(source.read(), filename=str(path))

layout = next(
    node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PLayout"
)
python_methods = {}
for node in layout.body:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    args = node.args
    python_methods[node.name] = {
        "params": [arg.arg for arg in args.posonlyargs + args.args + args.kwonlyargs],
        "varargs": args.vararg is not None,
        "kwargs": args.kwarg is not None,
    }

rna_functions = bpy.types.UILayout.bl_rna.functions
missing_result = {}
compat_extra = {}
for name, signature in python_methods.items():
    if name not in rna_functions:
        continue
    rna_params = [p.identifier for p in rna_functions[name].parameters]
    missing = [name for name in rna_params if name not in signature["params"]]
    extra = [name for name in signature["params"] if name not in rna_params]
    if missing and not signature["kwargs"]:
        missing_result[name] = missing
    if extra:
        compat_extra[name] = extra

result = {
    "blender": bpy.app.version_string,
    "missing": missing_result,
    "compat_extra": compat_extra,
}
print("PME_LAYOUT_SIGNATURES=" + json.dumps(result, sort_keys=True), flush=True)
print(
    "PME_LAYOUT_SIGNATURE_RESULT",
    "OK" if not missing_result else "FAILED",
    flush=True,
)
