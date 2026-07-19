import ast
import json
import os
from pathlib import Path

import bpy


def chain(node):
    names = []
    while isinstance(node, ast.Attribute):
        names.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        names.append(node.id)
    return tuple(reversed(names))


root = Path(os.environ["PME_SOURCE_ROOT"])
operator_calls = {}
type_attrs = set()
context_attrs = set()
app_attrs = set()
utils_attrs = set()

for source in sorted((root / "core").glob("*.py")):
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    for node in ast.walk(tree):
        path = chain(node)
        if len(path) == 4 and path[:2] == ("bpy", "types"):
            type_attrs.add((path[2], path[3]))
        elif len(path) == 3 and path[:2] == ("bpy", "context"):
            context_attrs.add(path[2])
        elif len(path) == 3 and path[:2] == ("bpy", "app"):
            app_attrs.add(path[2])
        elif len(path) == 3 and path[:2] == ("bpy", "utils"):
            utils_attrs.add(path[2])

        if isinstance(node, ast.Call):
            call_path = chain(node.func)
            if len(call_path) == 4 and call_path[:2] == ("bpy", "ops"):
                name = f"{call_path[2]}.{call_path[3]}"
                keywords = operator_calls.setdefault(name, set())
                keywords.update(kw.arg for kw in node.keywords if kw.arg)


missing_operator_keywords = {}
operator_signatures = {}
for name, keywords in sorted(operator_calls.items()):
    category, operator = name.split(".", 1)
    op = getattr(getattr(bpy.ops, category), operator)
    try:
        rna = op.get_rna_type()
    except KeyError:
        continue
    available = sorted(prop.identifier for prop in rna.properties)
    operator_signatures[name] = available
    missing = sorted(keywords - set(available))
    if missing:
        missing_operator_keywords[name] = missing


def missing_attrs(owner, attrs):
    return sorted(name for name in attrs if not hasattr(owner, name))


missing_type_attrs = []
for type_name, attr in sorted(type_attrs):
    owner = getattr(bpy.types, type_name, None)
    if owner is None or not hasattr(owner, attr):
        missing_type_attrs.append(f"{type_name}.{attr}")


result = {
    "blender": bpy.app.version_string,
    "context_missing": missing_attrs(bpy.context, context_attrs),
    "app_missing": missing_attrs(bpy.app, app_attrs),
    "utils_missing": missing_attrs(bpy.utils, utils_attrs),
    "type_attr_missing": missing_type_attrs,
    "operator_keyword_missing": missing_operator_keywords,
    "operator_signatures": operator_signatures,
}
output = Path(os.environ["PME_AUDIT_OUTPUT"])
output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
print(
    "PME_API_AUDIT_V2",
    json.dumps({key: value for key, value in result.items() if key != "operator_signatures"}, sort_keys=True),
    flush=True,
)
