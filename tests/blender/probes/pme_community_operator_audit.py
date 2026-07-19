import bpy
import json
from pathlib import Path
import re


path = Path(__file__).resolve().parents[2] / "fixtures" / "pme_community_51_menus.json"
with path.open("r", encoding="utf-8") as source:
    data = json.load(source)

pattern = re.compile(r"\bbpy\.ops\.([A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*)")
references = {}
for menu in data["menus"]:
    menu_name = menu[0]
    for item in menu[3]:
        for value in item:
            if not isinstance(value, str):
                continue
            for operator_name in pattern.findall(value):
                references.setdefault(operator_name, set()).add(menu_name)

missing = {}
for operator_name, menus in references.items():
    module_name, name = operator_name.split(".")
    operator = getattr(getattr(bpy.ops, module_name), name)
    try:
        operator.get_rna_type()
    except KeyError:
        missing[operator_name] = sorted(menus)

print("PME_COMMUNITY_OPERATOR_COUNT", len(references), flush=True)
print("PME_COMMUNITY_MISSING=" + json.dumps(missing, sort_keys=True), flush=True)
