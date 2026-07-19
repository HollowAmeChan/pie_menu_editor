import bpy
import re
from . import operator_utils
from .debug_utils import *
from .addon import get_prefs, print_exc
from .bl_utils import uname


_operators = {}
_macros = {}
_macro_proxies = {}
_macro_errors = {}
_macro_execs = []
_exec_base = None
_sticky_op = None
_modal_op = None


def init_macros(exec1, base, sticky, modal):
    _macro_execs.append(exec1)
    global _exec_base, _sticky_op, _modal_op
    _exec_base = base
    _sticky_op = sticky
    _modal_op = modal


def add_macro_exec():
    id = "macro_exec%d" % (len(_macro_execs) + 1)
    tp_name = "PME_OT_" + id
    defs = {
        "bl_idname": "pme." + id,
    }

    tp = type(tp_name, (_exec_base, bpy.types.Operator), defs)

    bpy.utils.register_class(tp)
    _macro_execs.append(tp)


def _gen_tp_id(name):
    def repl(mo):
        c = mo.group(0)
        try:
            cc = ord(c)
        except:
            return "_"

        return chr(97 + cc % 26)

    name = name.replace(" ", "_")
    name = name.lower()
    pre_tp, pre_id = "PME_OT_", "pme."
    id = "macro_" + re.sub(r"[^_a-z0-9]", repl, name, flags=re.I)
    id = uname(bpy.types, pre_tp + id, sep="_")[len(pre_tp) :]
    return pre_tp + id, pre_id + id


def _gen_op(tp, idx, **kwargs):
    tpname = tp.__name__[:-5] + str(idx + 1)
    bl_idname = tp.bl_idname + str(idx + 1)

    if tpname not in _operators:
        defs = dict(bl_idname=bl_idname)
        defs.update(kwargs)
        new_tp = type(tpname, (tp, bpy.types.Operator), defs)
        bpy.utils.register_class(new_tp)
        _operators[tpname] = new_tp

    return tpname


def _gen_modal_op(pm, idx):
    lock = pm.get_data("lock")

    tpname = _modal_op.__name__[:-5]
    bl_idname = _modal_op.bl_idname
    if lock:
        tpname += "_grab"
        bl_idname += "_grab"

    tpname += str(idx + 1)
    bl_idname += str(idx + 1)

    if tpname not in _operators:
        defs = dict(bl_idname=bl_idname)
        if not lock:
            defs["bl_options"] = {'REGISTER'}
        new_tp = type(tpname, (_modal_op, bpy.types.Operator), defs)
        bpy.utils.register_class(new_tp)
        _operators[tpname] = new_tp

    return tpname


def _find_missing_operator(pm, visited=None):
    visited = visited or set()
    if pm.name in visited:
        return None
    visited.add(pm.name)

    pr = get_prefs()
    for pmi in pm.pmis:
        if not pmi.enabled:
            continue

        if pmi.mode == 'COMMAND':
            sub_op_idname, _, _ = operator_utils.find_operator(pmi.text)
            if sub_op_idname and operator_utils.operator(sub_op_idname) is None:
                return pmi, sub_op_idname

        elif pmi.mode == 'MENU':
            sub_pm = pr.pie_menus.get(pmi.text)
            if sub_pm and sub_pm.mode == 'MACRO':
                missing = _find_missing_operator(sub_pm, visited)
                if missing:
                    return missing

    return None


def _report_missing_operator(pm, missing):
    pmi, op_idname = missing
    _macro_errors[pm.name] = (pmi.name, op_idname)
    print(
        "PME: Macro '%s' stopped; operator not found in slot '%s': %s"
        % (pm.name, pmi.name, op_idname)
    )


def _execute_macro_proxy(self, context):
    pm = get_prefs().pie_menus.get(self.__class__._pme_menu_name)
    if pm is None or pm.mode != 'MACRO':
        return {'CANCELLED'}
    if not pm.poll(self.__class__, context):
        return {'CANCELLED'}

    result = execute_macro(pm)
    if result is False or result is None or result == {'CANCELLED'}:
        return {'CANCELLED'}
    return {'FINISHED'}


def _ensure_macro_proxy(pm):
    tp = _macro_proxies.get(pm.name)
    if tp is not None:
        return tp

    tp_name, tp_bl_idname = _gen_tp_id(pm.name)
    defs = {
        "bl_label": pm.name,
        "bl_idname": tp_bl_idname,
        "bl_options": {'REGISTER', 'UNDO'},
        "_pme_menu_name": pm.name,
        "execute": _execute_macro_proxy,
    }
    tp = type(tp_name, (bpy.types.Operator,), defs)
    bpy.utils.register_class(tp)
    _macro_proxies[pm.name] = tp
    return tp


def _gen_native_tp_id(proxy_tp):
    tp_name = uname(bpy.types, proxy_tp.__name__ + "_native", sep="_")
    return tp_name, "pme." + tp_name[len("PME_OT_") :]


def _remove_native_macro(pm):
    tp = _macros.pop(pm.name, None)
    if tp is not None:
        bpy.utils.unregister_class(tp)


def add_macro(pm):
    if not pm.enabled:
        return False

    if pm.name in _macros:
        return True

    missing = _find_missing_operator(pm)
    if missing:
        _report_missing_operator(pm, missing)
        return False

    _macro_errors.pop(pm.name, None)

    pr = get_prefs()
    proxy_tp = _ensure_macro_proxy(pm)
    tp_name, tp_bl_idname = _gen_native_tp_id(proxy_tp)

    DBG_MACRO and logh("Add Macro: %s (%s)" % (pm.name, tp_name))

    defs = {
        "bl_label": pm.name,
        "bl_idname": tp_bl_idname,
        "bl_options": {'INTERNAL', 'REGISTER', 'UNDO'},
    }

    tp = type(tp_name, (bpy.types.Macro,), defs)

    try:
        bpy.utils.register_class(tp)
        _macros[pm.name] = tp

        idx, sticky_idx, modal_idx = 1, 0, 0
        for pmi in pm.pmis:
            if not pmi.enabled:
                continue

            pmi.icon = ''
            if pmi.mode == 'COMMAND':
                sub_op_idname, _, pos_args = operator_utils.find_operator(pmi.text)

                sub_op_exec_ctx, _ = operator_utils.parse_pos_args(pos_args)

                if sub_op_idname and sub_op_exec_ctx.startswith('INVOKE'):
                    sub_op = operator_utils.operator(sub_op_idname)
                    if sub_op is None:
                        raise RuntimeError("Operator not found: " + sub_op_idname)
                    sub_tp = sub_op.idname()
                    pmi.icon = 'BLENDER'
                    DBG_MACRO and logi("Type", sub_tp)
                    tp.define(sub_tp)
                else:
                    while len(_macro_execs) < idx:
                        add_macro_exec()
                    pmi.icon = 'TEXT'
                    DBG_MACRO and logi("Command", pmi.text)
                    tp.define("PME_OT_macro_exec%d" % idx)
                    idx += 1

            elif pmi.mode == 'MENU':
                if pmi.text not in pr.pie_menus:
                    continue
                sub_pm = pr.pie_menus[pmi.text]
                if sub_pm.mode == 'MACRO':
                    sub_tp = _macros.get(sub_pm.name, None)
                    if sub_tp:
                        DBG_MACRO and logi("Macro", sub_pm.name)
                        tp.define(sub_tp.__name__)

                elif sub_pm.mode == 'MODAL':
                    DBG_MACRO and logi("Modal", sub_pm.name)
                    idname = _gen_modal_op(sub_pm, modal_idx)
                    tp.define(idname)
                    modal_idx += 1

                elif sub_pm.mode == 'STICKY':
                    DBG_MACRO and logi("Sticky", sub_pm.name)
                    idname = _gen_op(_sticky_op, sticky_idx)
                    tp.define(idname)
                    sticky_idx += 1

        return True
    except:
        print_exc()
        registered_tp = _macros.pop(pm.name, None)
        if registered_tp:
            try:
                bpy.utils.unregister_class(registered_tp)
            except Exception:
                print_exc()
        return False


def remove_macro(pm):
    _macro_errors.pop(pm.name, None)
    _remove_native_macro(pm)
    tp = _macro_proxies.pop(pm.name, None)
    if tp is not None:
        bpy.utils.unregister_class(tp)


def remove_all_macros():
    for v in _macros.values():
        bpy.utils.unregister_class(v)
    _macros.clear()
    for v in _macro_proxies.values():
        bpy.utils.unregister_class(v)
    _macro_proxies.clear()
    _macro_errors.clear()

    while len(_macro_execs) > 1:
        bpy.utils.unregister_class(_macro_execs.pop())
    _macro_execs.clear()


def update_macro(pm):
    remove_macro(pm)
    return add_macro(pm)


def _fill_props(props, pm, idx=1):
    pr = get_prefs()

    sticky_idx, modal_idx = 0, 0
    for pmi in pm.pmis:
        if not pmi.enabled:
            continue

        if pmi.mode == 'COMMAND':
            sub_op_idname, args, pos_args = operator_utils.find_operator(pmi.text)

            sub_op_exec_ctx, _ = operator_utils.parse_pos_args(pos_args)

            if sub_op_idname and sub_op_exec_ctx.startswith('INVOKE'):
                args = ",".join(args)
                sub_op = operator_utils.operator(sub_op_idname)
                if sub_op is None:
                    raise RuntimeError("Operator not found: " + sub_op_idname)
                sub_tp = sub_op.idname()

                props[sub_tp] = eval("dict(%s)" % args)
            else:
                # while len(_macro_execs) < idx:
                #     add_macro_exec()
                props["PME_OT_macro_exec%d" % idx] = dict(cmd=pmi.text)
                idx += 1

        elif pmi.mode == 'MENU':
            sub_pm = pr.pie_menus[pmi.text]
            if sub_pm.mode == 'STICKY':
                props[_gen_op(_sticky_op, sticky_idx)] = dict(pm_name=sub_pm.name)
                sticky_idx += 1

            elif sub_pm.mode == 'MODAL':
                idname = _gen_modal_op(sub_pm, modal_idx)
                props[idname] = dict(pm_name=sub_pm.name)
                modal_idx += 1

            elif sub_pm.mode == 'MACRO':
                sub_props = {}
                _fill_props(sub_props, sub_pm)
                props[_macros[sub_pm.name].__name__] = sub_props


def execute_macro(pm):
    missing = _find_missing_operator(pm)
    if missing:
        _remove_native_macro(pm)
        _report_missing_operator(pm, missing)
        return False

    if pm.name not in _macros:
        # Macro class not built yet (e.g., right after json import); build now
        if not add_macro(pm):
            return False
        print("Macro built successfully")

    def _do_call():
        tp = _macros[pm.name]
        op = eval("bpy.ops." + tp.bl_idname)
        props = {}
        _fill_props(props, pm)
        return op('INVOKE_DEFAULT', True, **props)

    try:
        return _do_call()
    except TypeError as e:
        print("Type error: ", e)
        # Handle timing/registration mismatch right after creation/import
        # Example: "keyword 'PME_OT_macro_exec1' unrecognized" or "WM_OT_call_menu"
        msg = str(e)
        if "unrecognized" in msg and ("PME_OT_" in msg or "_OT_" in msg):
            try:
                _remove_native_macro(pm)
                if not add_macro(pm):
                    return False
                ret = _do_call()
                print("Macro updated and executed successfully")
                return ret
            except Exception:
                print_exc()
                return False
        print_exc()
        return False
    except Exception:
        print_exc()
        return False


def rename_macro(old_name, name):
    native_tp = _macros.pop(old_name, None)
    if native_tp is not None:
        bpy.utils.unregister_class(native_tp)

    proxy_tp = _macro_proxies.pop(old_name, None)
    if proxy_tp is not None:
        bpy.utils.unregister_class(proxy_tp)

    _macro_errors.pop(old_name, None)
    pm = get_prefs().pie_menus.get(name)
    if pm is not None:
        add_macro(pm)


def register():
    pass


def unregister():
    remove_all_macros()

    for v in _operators.values():
        bpy.utils.unregister_class(v)
    _operators.clear()
