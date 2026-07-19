import addon_utils
import bpy
import traceback


success = False
try:
    module = addon_utils.enable(
        "pie_menu_editor",
        default_set=True,
        persistent=False,
        handle_error=None,
    )
    package = getattr(module, "core", module)
    if not hasattr(bpy.types.WindowManager, "pme"):
        for waiter in package.PME_OT_wait_context.instances:
            waiter.cancelled = True
        package.on_context()

    window = bpy.context.window_manager.windows[0]
    screen = window.screen
    area = next(item for item in screen.areas if item.type == "VIEW_3D")
    region = next(item for item in area.regions if item.type == "WINDOW")
    with bpy.context.temp_override(
        window=window,
        screen=screen,
        area=area,
        region=region,
    ):
        bpy.context.view_layer.objects.active = bpy.data.objects.get("Cube")
        bpy.data.objects["Cube"].select_set(True)
        bpy.ops.object.mode_set(mode="SCULPT")
        settings = package.bl_utils.paint_settings(bpy.context)
        ups = package.pme.context.globals["ups"]()

    prefs = package.addon.get_prefs()
    menu = prefs.add_pm(mode="DIALOG", name="PME UPS Runtime Smoke")
    menu.pmis.clear()
    before = [
        "C.tool_settings.unified_paint_settings.size",
        "bpy.context.scene.tool_settings.unified_paint_settings.strength = 0.5",
        "context.tool_settings.unified_paint_settings.use_unified_size",
        "ups().weight",
    ]
    for text in before:
        item = menu.pmis.add()
        item.mode = "COMMAND"
        item.text = text
    package.compatibility_fixes.fix_1_19_19(prefs, menu)
    after = [item.text for item in menu.pmis]
    prefs.remove_pm(menu)
    checks = {
        "sculpt_mode": bpy.context.mode == "SCULPT",
        "paint_settings": (
            settings.as_pointer()
            == bpy.context.tool_settings.sculpt.as_pointer()
        ),
        "ups_present": ups is not None,
        "ups_owner": (
            ups.as_pointer()
            == bpy.context.tool_settings.sculpt.unified_paint_settings.as_pointer()
            if hasattr(bpy.context.tool_settings.sculpt, "unified_paint_settings")
            else ups.as_pointer()
            == bpy.context.tool_settings.unified_paint_settings.as_pointer()
        ),
        "size_available": hasattr(ups, "size"),
        "migration": after == [
            "ups().size",
            "ups().strength = 0.5",
            "ups().use_unified_size",
            "ups().weight",
        ],
    }
    print(
        "PME_UPS_RUNTIME_DATA",
        bpy.app.version_string,
        module.bl_info.get("version"),
        type(settings).__name__,
        type(ups).__name__,
        "migration=",
        after,
        flush=True,
    )
    print("PME_UPS_RUNTIME_CHECKS", checks, flush=True)
    success = all(checks.values())
except Exception:
    traceback.print_exc()
finally:
    print("PME_UPS_RUNTIME_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
