import addon_utils
import bpy
import traceback


TAG = "PME_STACK_KEY_OVERLAY_VISIBILITY_SMOKE"
MENU_NAME = "PME Stack Key Overlay Visibility Smoke"
MARKER = "pme_stack_key_overlay_visibility_smoke"
state = {"step": 0, "checks": {}}
menu_name = None
original_overlay_enabled = True
original_duration = 2.0


def call_stack(stack_key, menu, area, region, slot=-1):
    with bpy.context.temp_override(area=area, region=region):
        return stack_key.next(menu, slot)


def finish(success):
    global menu_name
    try:
        prefs = state.get("prefs")
        if prefs:
            prefs.overlay.overlay = original_overlay_enabled
            prefs.overlay.duration = original_duration
            if menu_name and menu_name in prefs.pie_menus:
                prefs.remove_pm(prefs.pie_menus[menu_name])
        bpy.context.scene.pop(MARKER, None)
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_CHECKS", state["checks"], flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def run_step():
    try:
        overlay = state["overlay"]
        prefs = state["prefs"]
        stack_key = state["stack_key"]
        menu = state["menu"]
        area = state["area"]
        region = state["region"]
        space = overlay.space_groups["VIEW_3D"]

        if state["step"] == 0:
            prefs.overlay.overlay = False
            prefs.overlay.duration = 1.0
            call_stack(stack_key, menu, area, region)
            state["checks"]["disabled_does_not_start"] = (
                not overlay.PME_OT_overlay.is_running and space.handler is None
            )
            state["step"] = 1
            return 1.3 if overlay.PME_OT_overlay.is_running else 0.1

        if state["step"] == 1:
            state["checks"]["disabled_overlay_cleans_up"] = (
                not overlay.PME_OT_overlay.is_running and space.handler is None
            )
            prefs.overlay.overlay = True
            stack_key.name = None
            call_stack(stack_key, menu, area, region, 0)
            state["checks"]["explicit_slot_does_not_start"] = (
                not overlay.PME_OT_overlay.is_running and space.handler is None
            )
            stack_key.name = None
            call_stack(stack_key, menu, area, region)
            state["checks"]["enabled_starts_overlay"] = (
                overlay.PME_OT_overlay.is_running and space.handler is not None
            )
            state["step"] = 2
            return 1.3

        state["checks"]["enabled_overlay_expires"] = (
            not overlay.PME_OT_overlay.is_running and space.handler is None
        )
        return finish(all(state["checks"].values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


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
    original_overlay_enabled = prefs.overlay.overlay
    original_duration = prefs.overlay.duration
    menu = prefs.add_pm("SCRIPT", MENU_NAME)
    menu_name = menu.name
    menu.pmis[0].name = "First"
    menu.pmis[0].mode = "COMMAND"
    menu.pmis[0].text = f'C.scene["{MARKER}"] = 1'
    second = menu.pmis.add()
    second.name = "Second"
    second.mode = "COMMAND"
    second.text = f'C.scene["{MARKER}"] = 2'
    bpy.context.scene[MARKER] = 0

    area = next(item for item in bpy.context.screen.areas if item.type == "VIEW_3D")
    region = next(item for item in area.regions if item.type == "WINDOW")
    state.update(
        prefs=prefs,
        overlay=package.overlay,
        stack_key=package.keymap_helper.StackKey,
        menu=menu,
        area=area,
        region=region,
    )
    bpy.app.timers.register(run_step, first_interval=0.1)
except Exception:
    traceback.print_exc()
    finish(False)
