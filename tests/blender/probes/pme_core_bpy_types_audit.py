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
references = []
parse_failures = []
for filepath in sorted((root / "core").glob("*.py")):
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        parse_failures.append((filepath.name, exc.lineno, exc.msg))
        continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        path = chain(node)
        if len(path) < 3 or path[:2] != ("bpy", "types"):
            continue
        references.append((filepath.name, node.lineno, path[2]))


missing = sorted(
    {
        reference
        for reference in references
        if not hasattr(bpy.types, reference[2])
        and not reference[2].startswith(("PME_", "WM_OT_pme"))
    }
)
result = {
    "blender": bpy.app.version_string,
    "references": len(references),
    "unique_types": len({item[2] for item in references}),
    "missing": missing,
    "parse_failures": parse_failures,
}
print("PME_CORE_BPY_TYPES_AUDIT", json.dumps(result, sort_keys=True), flush=True)
