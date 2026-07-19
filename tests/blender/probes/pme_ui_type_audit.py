import json
import os
import re
from pathlib import Path

import bpy


root = Path(os.environ["PME_SOURCE_ROOT"])
pattern = re.compile(r"\b[A-Z][A-Z0-9_]+_(?:PT|MT|HT|UL)_[A-Za-z0-9_]+\b")
references = {}
for folder, glob in ((root / "core", "*.py"), (root / "examples", "*.json")):
    for filepath in sorted(folder.glob(glob)):
        text = filepath.read_text(encoding="utf-8")
        for name in pattern.findall(text):
            references.setdefault(name, []).append(filepath.name)

missing = {
    name: sorted(set(files))
    for name, files in sorted(references.items())
    if not hasattr(bpy.types, name)
    and not name.startswith(("PME_", "WM_"))
}
result = {
    "blender": bpy.app.version_string,
    "references": len(references),
    "missing": missing,
}
print("PME_UI_TYPE_AUDIT", json.dumps(result, sort_keys=True), flush=True)
