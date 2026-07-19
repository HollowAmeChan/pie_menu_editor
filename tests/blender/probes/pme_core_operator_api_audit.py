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
calls = []
parse_failures = []
for filepath in sorted((root / "core").glob("*.py")):
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        parse_failures.append((filepath.name, exc.lineno, exc.msg))
        continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        path = chain(node.func)
        if len(path) != 4 or path[:2] != ("bpy", "ops"):
            continue
        calls.append((filepath.name, node.lineno, f"{path[2]}.{path[3]}", node))


missing = []
invalid_keywords = []
invalid_enums = []
for filepath, lineno, name, node in calls:
    category, operator = name.split(".", 1)
    try:
        rna = getattr(getattr(bpy.ops, category), operator).get_rna_type()
    except (AttributeError, KeyError, RuntimeError):
        if category != "pme":
            missing.append((filepath, lineno, name))
        continue
    props = rna.properties
    for keyword in node.keywords:
        if not keyword.arg:
            continue
        if keyword.arg not in props:
            invalid_keywords.append((filepath, lineno, name, keyword.arg))
            continue
        prop = props[keyword.arg]
        if prop.type != "ENUM" or not isinstance(keyword.value, ast.Constant):
            continue
        value = keyword.value.value
        if isinstance(value, str) and value not in prop.enum_items:
            invalid_enums.append(
                (filepath, lineno, name, keyword.arg, value)
            )


result = {
    "blender": bpy.app.version_string,
    "calls": len(calls),
    "unique_operators": len({item[2] for item in calls}),
    "missing": sorted(set(missing)),
    "invalid_keywords": sorted(set(invalid_keywords)),
    "invalid_enums": sorted(set(invalid_enums)),
    "parse_failures": parse_failures,
}
print("PME_CORE_OPERATOR_API_AUDIT", json.dumps(result, sort_keys=True), flush=True)
