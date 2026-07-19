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
operators = set()
types = set()
for source in sorted((root / "core").glob("*.py")):
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    for node in ast.walk(tree):
        path = chain(node)
        if len(path) == 4 and path[:2] == ("bpy", "ops"):
            operators.add("%s.%s" % (path[2], path[3]))
        elif len(path) == 3 and path[:2] == ("bpy", "types"):
            types.add(path[2])

missing_operators = sorted(
    name for name in operators
    if not hasattr(getattr(bpy.ops, name.split(".", 1)[0]), name.split(".", 1)[1])
)
missing_types = sorted(name for name in types if not hasattr(bpy.types, name))

print(
    "PME_API_AUDIT",
    json.dumps(
        {
            "blender": bpy.app.version_string,
            "operators": len(operators),
            "missing_operators": missing_operators,
            "types": len(types),
            "missing_types": missing_types,
        },
        sort_keys=True,
    ),
    flush=True,
)
