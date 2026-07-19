import bpy


def quit_blender():
    bpy.ops.wm.quit_blender()


def inspect_duplicate(initial_windows):
    windows = list(bpy.context.window_manager.windows)
    new_windows = [window for window in windows if window not in initial_windows]
    print(
        "PME_WINDOW_DUPLICATE",
        [(window.x, window.y, window.width, window.height) for window in new_windows],
        flush=True,
    )
    bpy.app.timers.register(quit_blender, first_interval=0.1)


def probe():
    window = bpy.context.window
    for name in ("x", "y", "width", "height"):
        prop = window.bl_rna.properties[name]
        print(
            "PME_WINDOW_PROP",
            name,
            "readonly=",
            prop.is_readonly,
            "value=",
            getattr(window, name),
            flush=True,
        )

    initial_windows = set(bpy.context.window_manager.windows)
    with bpy.context.temp_override(area=bpy.context.area):
        result = bpy.ops.screen.area_dupli("INVOKE_DEFAULT")
    print("PME_WINDOW_DUPLICATE_CALL", result, flush=True)
    bpy.app.timers.register(
        lambda: inspect_duplicate(initial_windows), first_interval=1.0
    )


bpy.app.timers.register(probe, first_interval=0.2)
