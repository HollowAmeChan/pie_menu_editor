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
references = {"context": [], "data": []}
for filepath in sorted((root / "core").glob("*.py")):
    tree = ast.parse(filepath.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        path = chain(node)
        if len(path) < 3 or path[0] != "bpy" or path[1] not in references:
            continue
        references[path[1]].append((filepath.name, node.lineno, path[2]))


missing = {}
for owner_name, items in references.items():
    owner = getattr(bpy, owner_name)
    missing[owner_name] = sorted(
        {item for item in items if not hasattr(owner, item[2])}
    )

result = {
    "blender": bpy.app.version_string,
    "references": {key: len(value) for key, value in references.items()},
    "unique_members": {
        key: len({item[2] for item in value})
        for key, value in references.items()
    },
    "missing": missing,
}
print("PME_CORE_BPY_MEMBERS_AUDIT", json.dumps(result, sort_keys=True), flush=True)
