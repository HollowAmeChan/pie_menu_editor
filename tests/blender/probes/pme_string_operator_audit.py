import json
import os
import re
from pathlib import Path

import bpy


root = Path(os.environ["PME_SOURCE_ROOT"])
references = []
pattern = re.compile(r"\bbpy\.ops\.([a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*)")
for folder in (root / "core", root / "examples", root / "scripts"):
    for filepath in sorted(folder.glob("**/*")):
        if filepath.suffix not in {".py", ".json"}:
            continue
        text = filepath.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            references.append((str(filepath.relative_to(root)), line, match.group(1)))


missing = []
for filepath, line, name in references:
    category, operator = name.split(".", 1)
    if category == "pme" or (
        category == "wm" and operator.startswith(("pme_", "pm_", "pmi_"))
    ):
        continue
    try:
        getattr(getattr(bpy.ops, category), operator).get_rna_type()
    except (AttributeError, KeyError, RuntimeError):
        missing.append((filepath, line, name))


result = {
    "blender": bpy.app.version_string,
    "references": len(references),
    "unique_operators": len({item[2] for item in references}),
    "missing": sorted(set(missing)),
}
print("PME_STRING_OPERATOR_AUDIT", json.dumps(result, sort_keys=True), flush=True)
