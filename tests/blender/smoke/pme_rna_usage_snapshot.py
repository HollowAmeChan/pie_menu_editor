import addon_utils
import bpy
import json
import os
from pathlib import Path
import re
import traceback


TAG = "PME_RNA_USAGE_SNAPSHOT"
SOURCE = Path(os.environ["PME_ACTUAL_JSON"])
REPO = Path(os.environ["PME_REPO"])
OUTPUT = Path(os.environ["PME_RNA_OUTPUT"])
ATTRIBUTE_RE = re.compile(r"\.([A-Za-z_][A-Za-z0-9_]*)")


success = False
try:
    module = addon_utils.enable(
        "pie_menu_editor",
        default_set=True,
        persistent=False,
        handle_error=None,
    )
    package = module.core
    if not hasattr(bpy.types.WindowManager, "pme"):
        for waiter in package.PME_OT_wait_context.instances:
            waiter.cancelled = True
        package.on_context()

    result = bpy.ops.wm.pm_import(
        "EXEC_DEFAULT",
        filepath=str(SOURCE),
        mode="REPLACE",
        tags=TAG,
    )
    prefs = package.addon.get_prefs()
    imported = [pm for pm in prefs.pie_menus if pm.has_tag(TAG)]

    texts = []
    for path in sorted((REPO / "core").glob("*.py")):
        if path.name == "compatibility_fixes.py":
            continue
        texts.append(path.read_text(encoding="utf-8"))
    texts.extend(pmi.text for pm in imported for pmi in pm.pmis if pmi.text)
    identifiers = sorted(set(ATTRIBUTE_RE.findall("\n".join(texts))))

    owners = {identifier: [] for identifier in identifiers}
    rna_type_count = 0
    for type_name in dir(bpy.types):
        rna_type = getattr(bpy.types, type_name, None)
        bl_rna = getattr(rna_type, "bl_rna", None)
        if bl_rna is None:
            continue
        rna_type_count += 1
        try:
            properties = {prop.identifier for prop in bl_rna.properties}
        except Exception:
            continue
        for identifier in properties.intersection(owners):
            owners[identifier].append(type_name)

    data = {
        "blender": bpy.app.version_string,
        "addon": module.bl_info.get("version"),
        "imported": len(imported),
        "identifier_count": len(identifiers),
        "rna_type_count": rna_type_count,
        "owners": {key: value for key, value in owners.items() if value},
    }
    OUTPUT.write_text(
        json.dumps(data, ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(
        TAG + "_DATA",
        bpy.app.version_string,
        module.bl_info.get("version"),
        "identifiers=",
        len(identifiers),
        "owned=",
        len(data["owners"]),
        "rna_types=",
        rna_type_count,
        "output=",
        str(OUTPUT),
        flush=True,
    )
    success = result == {"FINISHED"} and len(imported) == 85
except Exception:
    traceback.print_exc()
finally:
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
