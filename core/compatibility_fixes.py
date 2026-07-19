import re
from . import addon
from .addon import get_prefs
from .debug_utils import *
from . import constants as CC


_PALETTE_TEMPLATE_RE = re.compile(
    r"\b(L(?:\.box\(\))?)\.template_palette\(ps, 'palette', color=True\)"
)
_BRUSH_TEMPLATE_RE = re.compile(
    r"\b(L(?:\.box\(\))?)\.template_ID_preview\("
    r"ps, 'brush', new='brush\.add', rows=3, cols=8\)"
)
_BRUSH_ASSIGN_RE = re.compile(
    r'paint_settings\(C\)\.brush = D\.brushes\["((?:\\.|[^"\\])*)"\]'
)
_AUTOMASKING_PROPERTIES = {
    "use_automasking_topology": "use_automasking_topology",
    "use_automasking_face_sets": "use_automasking_face_sets",
    "use_automasking_boundary_edges": "use_automasking_boundary_edges",
    "use_automasking_boundary_face_sets": "use_automasking_boundary_face_sets",
    "use_automasking_cavity": "use_automasking_cavity",
    "use_automasking_cavity_inverted": "use_automasking_cavity_inverted",
    "use_automasking_start_normal": "use_automasking_start_normal",
    "use_automasking_view_normal": "use_automasking_view_normal",
    "automasking_boundary_edges_propagation_steps": (
        "boundary_edges_propagation_steps"
    ),
    "automasking_cavity_factor": "cavity_factor",
    "automasking_cavity_blur_steps": "cavity_blur_steps",
    "automasking_cavity_curve": "cavity_curve",
    "automasking_cavity_curve_op": "cavity_curve_op",
    "automasking_start_normal_limit": "start_normal_limit",
    "automasking_start_normal_falloff": "start_normal_falloff",
    "automasking_view_normal_limit": "view_normal_limit",
    "automasking_view_normal_falloff": "view_normal_falloff",
}
_AUTOMASKING_PATH_RE = re.compile(
    r"(?P<owner>"
    r"paint_settings\([^)]*\)(?:\.brush)?|"
    r"(?:bpy\.)?context(?:\.scene)?\.tool_settings\.sculpt(?:\.brush)?|"
    r"C(?:\.scene)?\.tool_settings\.sculpt(?:\.brush)?"
    r")\.(?P<property>"
    + "|".join(map(re.escape, _AUTOMASKING_PROPERTIES))
    + r")\b"
)
_BRUSH_PATH = (
    r"paint_settings\([^)]*\)\.brush|"
    r"(?:bpy\.)?context(?:\.scene)?\.tool_settings\.[A-Za-z_]+\.brush|"
    r"C(?:\.scene)?\.tool_settings\.[A-Za-z_]+\.brush"
)
_CURVE_PRESET_PROP_RE = re.compile(
    r"(?P<layout>\bL(?:\.\w+\([^()\n]*\))*)\.prop\("
    r"(?P<brush>[^,\n]+?),\s*['\"]curve_preset['\"]"
    r"(?P<kwargs>(?:,\s*[^()\n]*)?)\)"
)
_CURVE_MAPPING_RE = re.compile(
    r"(?P<layout>\bL(?:\.\w+\([^()\n]*\))*)\.template_curve_mapping\("
    r"(?P<brush>[^,\n]+?),\s*['\"]curve['\"]"
    r"(?P<kwargs>(?:,\s*[^()\n]*)?)\)"
)
_CURVE_PRESET_PATH_RE = re.compile(
    rf"^(?P<brush>{_BRUSH_PATH})\.curve_preset$"
)
_CURVE_PATH_RE = re.compile(rf"^(?P<brush>{_BRUSH_PATH})\.curve$")
_INPUT_SAMPLES_PATH_RE = re.compile(
    r"(?P<owner>"
    r"paint_settings\([^)]*\)|"
    r"(?:bpy\.)?context(?:\.scene)?\.tool_settings\.sculpt|"
    r"C(?:\.scene)?\.tool_settings\.sculpt"
    r")\.input_samples\b"
)


def _replace_automasking_path(match):
    owner = match.group("owner")
    prop = _AUTOMASKING_PROPERTIES[match.group("property")]
    return f"mesh_automasking_settings({owner}).{prop}"


def _replace_curve_control(match, helper):
    return (
        f"{helper}({match.group('layout')}, {match.group('brush')}"
        f"{match.group('kwargs')})"
    )


def fix(pms=None, version=None):
    DBG_INIT and logh("PME Fixes")
    pr = get_prefs()
    pr_version = version or tuple(pr.version)
    if pr_version == addon.VERSION:
        return

    fixes = []
    re_fix = re.compile(r"fix_(\d+)_(\d+)_(\d+)")
    for k, v in globals().items():
        mo = re_fix.search(k)
        if not mo:
            continue

        fix_version = (int(mo.group(1)), int(mo.group(2)), int(mo.group(3)))
        if fix_version <= pr_version or fix_version > addon.VERSION:
            continue
        fixes.append((fix_version, v))

    fixes.sort(key=lambda item: item[0])

    if pms is None:
        pms = pr.pie_menus

    for pm in pms:
        for fix_version, fix_func in fixes:
            fix_func(pr, pm)

    pr.version = addon.VERSION


def fix_json(pm, menu, version):
    DBG_INIT and logh("PME JSON Fixes")
    pr = get_prefs()
    fixes = []
    re_fix = re.compile(r"fix_json_(\d+)_(\d+)_(\d+)")
    for k, v in globals().items():
        mo = re_fix.search(k)
        if not mo:
            continue

        fix_version = (int(mo.group(1)), int(mo.group(2)), int(mo.group(3)))
        if fix_version <= version:
            continue
        fixes.append((fix_version, v))

    fixes.sort(key=lambda item: item[0])

    for fix_version, fix_func in fixes:
        fix_func(pr, pm, menu)


def fix_1_14_0(pr, pm):
    if pm.mode == 'PMENU':
        for pmi in pm.pmis:
            if pmi.mode == 'MENU':
                sub_pm = pmi.text in pr.pie_menus and pr.pie_menus[pmi.text]

                if (
                    sub_pm
                    and sub_pm.mode == 'DIALOG'
                    and sub_pm.get_data("pd_panel") == 0
                ):
                    pmi.text = CC.F_EXPAND + pmi.text

                    if sub_pm.get_data("pd_box"):
                        pmi.text = CC.F_EXPAND + pmi.text

    elif pm.mode == 'DIALOG':
        if pm.get_data("pd_expand"):
            pm.set_data("pd_expand", False)
            for pmi in pm.pmis:
                if pmi.mode == 'MENU':
                    sub_pm = pmi.text in pr.pie_menus and pr.pie_menus[pmi.text]
                    if sub_pm and sub_pm.mode == 'DIALOG':
                        pmi.text = CC.F_EXPAND + pmi.text


def fix_1_14_9(pr, pm):
    if pm.mode == 'STICKY':
        pm.data = re.sub(r"([^_])block_ui", r"\1sk_block_ui", pm.data)


def fix_1_17_0(pr, pm):
    if pm.mode == 'PMENU':
        for i in range(len(pm.pmis), 10):
            pm.pmis.add()


def fix_1_17_1(pr, pm):
    if not pm.ed.has_hotkey:
        return

    pm.km_name = (CC.KEYMAP_SPLITTER + " ").join(pm.km_name.split(","))


def fix_1_19_3(pr, pm):
    for pmi in pm.pmis:
        if pmi.mode != 'CUSTOM':
            continue
        pmi.text = _PALETTE_TEMPLATE_RE.sub(
            r"template_palette(\1, ps, 'palette')", pmi.text
        )


def fix_1_19_4(pr, pm):
    for pmi in pm.pmis:
        if pmi.mode == 'CUSTOM':
            pmi.text = _BRUSH_TEMPLATE_RE.sub(
                r"brush_asset_selector(\1, bl_context, ps)", pmi.text
            )
        elif pmi.mode == 'COMMAND':
            pmi.text = _BRUSH_ASSIGN_RE.sub(r'activate_brush("\1")', pmi.text)


def fix_1_19_6(pr, pm):
    for pmi in pm.pmis:
        if pmi.mode == 'COMMAND':
            pmi.text = pmi.text.replace(
                "bpy.ops.mesh.loop_multi_select", "mesh_loop_multi_select"
            )


def fix_1_19_7(pr, pm):
    for pmi in pm.pmis:
        if pmi.mode == 'COMMAND':
            pmi.text = pmi.text.replace(
                "bpy.ops.mesh.faces_mirror_uv", "mesh_faces_mirror_uv"
            )


def fix_1_19_8(pr, pm):
    for pmi in pm.pmis:
        if pmi.mode == 'COMMAND':
            pmi.text = pmi.text.replace(
                "bpy.ops.sculpt.sample_color", "sculpt_sample_color"
            )


def fix_1_19_9(pr, pm):
    for pmi in pm.pmis:
        if pmi.mode != 'COMMAND':
            continue
        pmi.text = pmi.text.replace(
            "bpy.ops.object.move_to_collection", "object_move_to_collection"
        )
        pmi.text = pmi.text.replace(
            "O.object.move_to_collection", "object_move_to_collection"
        )


def fix_1_19_10(pr, pm):
    for pmi in pm.pmis:
        pmi.text = _AUTOMASKING_PATH_RE.sub(
            _replace_automasking_path, pmi.text
        )


def fix_1_19_11(pr, pm):
    for pmi in pm.pmis:
        pmi.text = _CURVE_PRESET_PROP_RE.sub(
            lambda match: _replace_curve_control(
                match, "brush_curve_preset"
            ),
            pmi.text,
        )
        pmi.text = _CURVE_MAPPING_RE.sub(
            lambda match: _replace_curve_control(
                match, "brush_curve_mapping"
            ),
            pmi.text,
        )

        if pmi.mode == 'PROP':
            match = _CURVE_PRESET_PATH_RE.fullmatch(pmi.text)
            if match:
                pmi.mode = 'CUSTOM'
                pmi.text = f"brush_curve_preset(L, {match.group('brush')})"
                continue
            match = _CURVE_PATH_RE.fullmatch(pmi.text)
            if match:
                pmi.mode = 'CUSTOM'
                pmi.text = (
                    f"brush_curve_mapping(L, {match.group('brush')}, "
                    "brush=True)"
                )
                continue

        if pmi.mode == 'COMMAND':
            pmi.text = pmi.text.replace(
                "bpy.ops.brush.curve_preset", "set_brush_curve_preset"
            )
            pmi.text = pmi.text.replace(
                "O.brush.curve_preset", "set_brush_curve_preset"
            )


def fix_1_19_12(pr, pm):
    for pmi in pm.pmis:
        pmi.text = _INPUT_SAMPLES_PATH_RE.sub(
            lambda match: (
                f"paint_input_samples_owner({match.group('owner')})."
                "input_samples"
            ),
            pmi.text,
        )


def fix_json_1_17_1(pr, pm, menu):
    if not pm.ed.has_hotkey:
        return

    menu[1] = (CC.KEYMAP_SPLITTER + " ").join(menu[1].split(","))
