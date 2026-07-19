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


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


root = Path(os.environ["PME_SOURCE_ROOT"])
calls = []
parse_failures = []
for filepath in sorted((root / "examples").glob("*.json")):
    data = json.loads(filepath.read_text(encoding="utf-8"))
    for text in strings(data):
        if "bpy.ops." not in text:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            parse_failures.append((filepath.name, text))
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            path = chain(node.func)
            if len(path) != 4 or path[:2] != ("bpy", "ops"):
                continue
            calls.append((filepath.name, f"{path[2]}.{path[3]}", node))


missing = []
invalid_keywords = []
invalid_enums = []
for filepath, name, node in calls:
    category, operator = name.split(".", 1)
    try:
        rna = getattr(getattr(bpy.ops, category), operator).get_rna_type()
    except KeyError:
        if category != "pme":
            missing.append((filepath, name))
        continue
    props = rna.properties
    for keyword in node.keywords:
        if not keyword.arg:
            continue
        if keyword.arg not in props:
            invalid_keywords.append((filepath, name, keyword.arg))
            continue
        prop = props[keyword.arg]
        if prop.type == "ENUM" and isinstance(keyword.value, ast.Constant):
            value = keyword.value.value
            if isinstance(value, str) and value not in prop.enum_items:
                invalid_enums.append((filepath, name, keyword.arg, value))


result = {
    "blender": bpy.app.version_string,
    "calls": len(calls),
    "missing": sorted(set(missing)),
    "invalid_keywords": sorted(set(invalid_keywords)),
    "invalid_enums": sorted(set(invalid_enums)),
    "parse_failures": parse_failures,
}
print("PME_EXAMPLE_API_AUDIT", json.dumps(result, sort_keys=True), flush=True)
