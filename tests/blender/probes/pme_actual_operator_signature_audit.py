import addon_utils
import ast
import bpy
import json
import os
from pathlib import Path
import traceback


TAG = "PME_ACTUAL_OPERATOR_SIGNATURE_AUDIT"
SOURCE = Path(os.environ["PME_ACTUAL_JSON"])


def dotted_name(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def literal_value(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return None


def enum_identifiers(prop):
    try:
        return {item.identifier for item in prop.enum_items}
    except Exception:
        return set()


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

    calls = {}
    parse_errors = []
    for pm in imported:
        for index, pmi in enumerate(pm.pmis):
            text = pmi.text.strip()
            if not text or "bpy.ops." not in text:
                continue
            try:
                tree = ast.parse(text)
            except SyntaxError as exc:
                parse_errors.append((pm.name, index, exc.msg, text))
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = dotted_name(node.func)
                if not name.startswith("bpy.ops.") or name.count(".") != 3:
                    continue
                signature = (
                    name,
                    tuple(
                        sorted(
                            (kw.arg, repr(literal_value(kw.value)))
                            for kw in node.keywords
                            if kw.arg is not None
                        )
                    ),
                )
                calls.setdefault(signature, []).append((pm.name, index, text))

    missing_operators = {}
    missing_parameters = {}
    invalid_enums = {}
    checked = 0
    for signature, locations in sorted(calls.items()):
        name, keyword_literals = signature
        _, _, category, operator_name = name.split(".")
        try:
            operator = getattr(getattr(bpy.ops, category), operator_name)
            properties = operator.get_rna_type().properties
        except Exception as exc:
            missing_operators[name] = (type(exc).__name__, str(exc), locations)
            continue

        checked += 1
        for keyword_name, value_repr in keyword_literals:
            if keyword_name not in properties:
                missing_parameters.setdefault(name, set()).add(keyword_name)
                continue
            prop = properties[keyword_name]
            if prop.type != "ENUM":
                continue
            value = ast.literal_eval(value_repr)
            if value is None:
                continue
            values = value if isinstance(value, set) else {value}
            valid = enum_identifiers(prop)
            bad = sorted(item for item in values if item not in valid)
            if bad:
                invalid_enums.setdefault(name, {}).setdefault(keyword_name, set()).update(bad)

    missing_parameters = {
        name: sorted(values) for name, values in sorted(missing_parameters.items())
    }
    invalid_enums = {
        name: {prop: sorted(values) for prop, values in sorted(props.items())}
        for name, props in sorted(invalid_enums.items())
    }
    missing_names = sorted(missing_operators)
    data = {
        "blender": bpy.app.version_string,
        "addon": module.bl_info.get("version"),
        "imported": len(imported),
        "unique_calls": len(calls),
        "checked": checked,
        "missing_operators": missing_names,
        "missing_parameters": missing_parameters,
        "invalid_enums": invalid_enums,
        "parse_error_count": len(parse_errors),
    }
    print(TAG + "_DATA", json.dumps(data, ensure_ascii=True, sort_keys=True), flush=True)
    print(TAG + "_PARSE_ERRORS", parse_errors, flush=True)
    success = (
        result == {"FINISHED"}
        and len(imported) == 85
        and not missing_parameters
        and not invalid_enums
    )
except Exception:
    traceback.print_exc()
finally:
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
