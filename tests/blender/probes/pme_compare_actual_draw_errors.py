from collections import Counter
import json
import os
from pathlib import Path


BASE = Path(os.environ["PME_BASE_ERRORS"])
TARGET = Path(os.environ["PME_TARGET_ERRORS"])


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def key(error):
    traceback_text = error.get("traceback", "").strip()
    last_line = traceback_text.splitlines()[-1] if traceback_text else ""
    return (
        error.get("kind", ""),
        error.get("text", ""),
        error.get("message", ""),
        error.get("args", ""),
        error.get("kwargs", ""),
        last_line,
    )


base = Counter(map(key, load(BASE)))
target = Counter(map(key, load(TARGET)))
only_base = base - target
only_target = target - base
print("BASE_TOTAL", sum(base.values()), "UNIQUE", len(base))
print("TARGET_TOTAL", sum(target.values()), "UNIQUE", len(target))
print("EQUAL", base == target)
print("ONLY_BASE", list(only_base.items()))
print("ONLY_TARGET", list(only_target.items()))
print("DISTRIBUTION", Counter(item[0] for item in base.elements()))
print("EXCEPTION_LAST_LINES")
for item, count in sorted(base.items(), key=lambda entry: repr(entry[0])):
    if item[-1]:
        print(count, repr(item[-1]))
