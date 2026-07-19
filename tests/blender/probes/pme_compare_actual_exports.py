from collections import Counter
import json
import os
from pathlib import Path


OLD = Path(os.environ["PME_OLD_EXPORT"])
CURRENT = Path(os.environ["PME_CURRENT_EXPORT"])


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def summarize(payload):
    menus = payload["menus"]
    return {
        "version": payload.get("version"),
        "schema": payload.get("schema"),
        "menus": len(menus),
        "items": sum(len(menu[3]) for menu in menus if len(menu) > 3),
        "enabled": sum(bool(menu[9]) for menu in menus if len(menu) > 9),
        "modes": dict(sorted(Counter(menu[4] for menu in menus if len(menu) > 4).items())),
        "record_lengths": dict(sorted(Counter(len(menu) for menu in menus).items())),
        "duplicate_names": sorted(
            name for name, count in Counter(menu[0] for menu in menus).items() if count > 1
        ),
    }


old = load(OLD)
current = load(CURRENT)
old_menus = old["menus"]
current_menus = current["menus"]
old_by_name = {menu[0]: menu for menu in old_menus}
current_by_name = {menu[0]: menu for menu in current_menus}
old_names = set(old_by_name)
current_names = set(current_by_name)

print("OLD", summarize(old))
print("CURRENT", summarize(current))
print("ONLY_OLD", sorted(old_names - current_names))
print("ONLY_CURRENT", sorted(current_names - old_names))
print("ORDER_EQUAL", [menu[0] for menu in old_menus] == [menu[0] for menu in current_menus])
print("OLD_SHORT", [menu for menu in old_menus if len(menu) < 10])
print("CURRENT_SHORT", [menu for menu in current_menus if len(menu) < 10])

changed_menus = []
changed_items = 0
field_changes = Counter()
examples = []
for name in sorted(old_names & current_names):
    before = old_by_name[name]
    after = current_by_name[name]
    if before == after:
        continue
    changed_menus.append(name)
    for index, (old_value, new_value) in enumerate(zip(before, after)):
        if old_value == new_value:
            continue
        field_changes[index] += 1
        if index == 3:
            changed_items += sum(
                left != right
                for left, right in zip(old_value, new_value)
            ) + abs(len(old_value) - len(new_value))
        if len(examples) < 20:
            examples.append((name, index, old_value, new_value))

print("CHANGED_MENU_COUNT", len(changed_menus))
print("CHANGED_ITEM_COUNT", changed_items)
print("FIELD_CHANGES", dict(sorted(field_changes.items())))
print("CHANGED_MENUS", changed_menus)
for name, index, before, after in examples:
    print("CHANGE", repr(name), "field", index, repr(before), "=>", repr(after))
