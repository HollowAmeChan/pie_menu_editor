import json
import os
import re
from pathlib import Path

import bpy


payload = json.loads(Path(os.environ["PME_ACTUAL_JSON"]).read_text(encoding="utf-8"))
pattern = re.compile(r"\bbpy\.ops\.([a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*)")
references = []
for menu in payload["menus"]:
    for index, item in enumerate(menu[3]):
        if len(item) < 4:
            continue
        for match in pattern.finditer(item[3]):
            references.append((menu[0], index, match.group(1)))

availability = {}
for _, _, name in references:
    if name in availability:
        continue
    category, operator = name.split(".", 1)
    try:
        getattr(getattr(bpy.ops, category), operator).get_rna_type()
        availability[name] = True
    except (AttributeError, KeyError, RuntimeError):
        availability[name] = False

result = {
    "blender": bpy.app.version_string,
    "references": len(references),
    "unique": len(availability),
    "available": sorted(name for name, value in availability.items() if value),
    "missing": sorted(name for name, value in availability.items() if not value),
}
print("PME_ACTUAL_OPERATOR_AUDIT", json.dumps(result, ensure_ascii=False), flush=True)
