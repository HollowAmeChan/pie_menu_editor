import bpy
import ctypes
import os
import traceback
from ctypes import wintypes


def native_windows():
    user32 = ctypes.windll.user32
    handles = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def callback(hwnd, _lparam):
        process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if process_id.value != os.getpid() or not user32.IsWindowVisible(hwnd):
            return True

        length = user32.GetWindowTextLengthW(hwnd)
        title = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title, len(title))
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        handles.append(
            (
                int(hwnd),
                title.value,
                (rect.left, rect.top, rect.right, rect.bottom),
            )
        )
        return True

    user32.EnumWindows(callback, 0)
    return sorted(handles)


def quit_blender():
    bpy.ops.wm.quit_blender()


def inspect_duplicate(initial_windows, native_before):
    try:
        windows = list(bpy.context.window_manager.windows)
        new_windows = [window for window in windows if window not in initial_windows]
        print(
            "PME_WINDOW_DUPLICATE",
            [
                (window.x, window.y, window.width, window.height)
                for window in new_windows
            ],
            flush=True,
        )
        after = native_windows()
        print("PME_NATIVE_WINDOWS_BEFORE", native_before, flush=True)
        print("PME_NATIVE_WINDOWS_AFTER", after, flush=True)
        print(
            "PME_NATIVE_WINDOWS_NEW",
            [item for item in after if item[0] not in {v[0] for v in native_before}],
            flush=True,
        )
    except Exception:
        traceback.print_exc()
    finally:
        bpy.app.timers.register(quit_blender, first_interval=0.1)


def probe():
    try:
        window = bpy.context.window_manager.windows[0]
        screen = window.screen
        area = screen.areas[0]
        region = next(
            (item for item in area.regions if item.type == "WINDOW"),
            None,
        )
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
        native_before = native_windows()
        with bpy.context.temp_override(
            window=window,
            screen=screen,
            area=area,
            region=region,
        ):
            result = bpy.ops.screen.area_dupli("INVOKE_DEFAULT")
        print("PME_WINDOW_DUPLICATE_CALL", result, flush=True)
        bpy.app.timers.register(
            lambda: inspect_duplicate(initial_windows, native_before),
            first_interval=1.0,
        )
    except Exception:
        traceback.print_exc()
        bpy.app.timers.register(quit_blender, first_interval=0.1)


bpy.app.timers.register(probe, first_interval=0.2)
