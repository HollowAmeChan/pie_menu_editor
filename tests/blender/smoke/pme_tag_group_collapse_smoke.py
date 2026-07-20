import addon_utils
import bpy
import traceback


TAG = "PME_TAG_GROUP_COLLAPSE_SMOKE"
MENU_ALPHA = "PME Tag Collapse Alpha"
MENU_BETA = "PME Tag Collapse Beta"
success = False
module = None
original = {}


def filter_links(package, temp):
    dummy = type("PMETreeFilter", (), {"bitflag_filter_item": 1})()
    return package.preferences.PME_UL_pm_tree.filter_items(
        dummy,
        bpy.context,
        temp,
        "links",
    )[0]


def menu_visibility(temp, filtered, menu_name):
    return [
        filtered[index]
        for index, link in enumerate(temp.links)
        if link.pm_name == menu_name
    ]


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

    prefs = package.addon.get_prefs()
    temp = package.addon.temp_prefs()
    tree_type = package.preferences.PME_UL_pm_tree
    original.update(
        tree_mode=prefs.tree_mode,
        group_by=prefs.group_by,
        use_filter=prefs.use_filter,
        save_tree=prefs.save_tree,
        collapsed_groups=set(tree_type.collapsed_groups),
        expanded_folders=set(tree_type.expanded_folders),
    )

    for name in (MENU_ALPHA, MENU_BETA):
        menu = prefs.pie_menus.get(name)
        if menu is not None:
            prefs.remove_pm(menu)
    alpha = prefs.add_pm(mode="SCRIPT", name=MENU_ALPHA)
    beta = prefs.add_pm(mode="SCRIPT", name=MENU_BETA)
    alpha.tag = "Alpha"
    beta.tag = "Beta"

    prefs.save_tree = False
    prefs.tree_mode = True
    prefs.use_filter = False
    prefs.group_by = "TAG"
    tree_type.collapsed_groups.clear()
    tree_type.expanded_folders.clear()
    tree_type.update_tree()

    alpha_group_index = next(
        index
        for index, link in enumerate(temp.links)
        if link.label == "Alpha"
    )
    collapse_result = bpy.ops.pme.tree_group_toggle(
        "EXEC_DEFAULT",
        group="Alpha",
        idx=alpha_group_index,
        all=False,
    )
    collapsed_before_rebuild = "Alpha" in tree_type.collapsed_groups
    tree_type.update_tree()
    collapsed_after_rebuild = "Alpha" in tree_type.collapsed_groups
    collapsed_filter = filter_links(package, temp)
    alpha_hidden = menu_visibility(temp, collapsed_filter, MENU_ALPHA)
    beta_visible = menu_visibility(temp, collapsed_filter, MENU_BETA)

    alpha_group_index = next(
        index
        for index, link in enumerate(temp.links)
        if link.label == "Alpha"
    )
    expand_result = bpy.ops.pme.tree_group_toggle(
        "EXEC_DEFAULT",
        group="Alpha",
        idx=alpha_group_index,
        all=False,
    )
    expanded_filter = filter_links(package, temp)
    alpha_visible = menu_visibility(temp, expanded_filter, MENU_ALPHA)

    checks = {
        "tag_groups_built": {"Alpha", "Beta"}.issubset(tree_type.groups),
        "collapse_finished": collapse_result == {"FINISHED"},
        "collapsed_before_rebuild": collapsed_before_rebuild,
        "collapsed_after_rebuild": collapsed_after_rebuild,
        "alpha_link_hidden": bool(alpha_hidden) and all(
            value == 0 for value in alpha_hidden
        ),
        "beta_link_visible": bool(beta_visible) and all(
            value != 0 for value in beta_visible
        ),
        "expand_finished": expand_result == {"FINISHED"},
        "alpha_group_expanded": "Alpha" not in tree_type.collapsed_groups,
        "alpha_link_visible": bool(alpha_visible) and all(
            value != 0 for value in alpha_visible
        ),
    }
    print(
        TAG + "_DATA",
        bpy.app.version_string,
        module.bl_info.get("version"),
        list(tree_type.groups),
        alpha_hidden,
        beta_visible,
        alpha_visible,
        flush=True,
    )
    print(TAG + "_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    try:
        if module is not None:
            package = module.core
            prefs = package.addon.get_prefs()
            tree_type = package.preferences.PME_UL_pm_tree
            for name in (MENU_ALPHA, MENU_BETA):
                menu = prefs.pie_menus.get(name)
                if menu is not None:
                    prefs.remove_pm(menu)
            if original:
                prefs.save_tree = False
                prefs.tree_mode = original["tree_mode"]
                prefs.use_filter = original["use_filter"]
                prefs.group_by = original["group_by"]
                prefs.save_tree = original["save_tree"]
                tree_type.collapsed_groups.clear()
                tree_type.collapsed_groups.update(
                    original["collapsed_groups"]
                )
                tree_type.expanded_folders.clear()
                tree_type.expanded_folders.update(
                    original["expanded_folders"]
                )
                tree_type.update_tree()
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
