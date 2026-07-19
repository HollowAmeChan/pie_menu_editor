import bpy
import json
import os
import traceback
from pathlib import Path


def finish(success):
    print("PME_VIEW_CAMERA_EXAMPLE_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def run():
    try:
        filepath = Path(os.environ["PME_SOURCE_ROOT"]) / "examples" / "3d_view_numpad_pie.json"
        data = json.loads(filepath.read_text(encoding="utf-8"))
        commands = [item[3] for item in data["menus"][0][3] if len(item) >= 4]
        json_ok = "bpy.ops.view3d.view_camera()" in commands

        window = bpy.context.window
        area = next((item for item in window.screen.areas if item.type == "VIEW_3D"), None)
        region = next((item for item in area.regions if item.type == "WINDOW"), None)
        if not area or not region:
            return finish(False)
        with bpy.context.temp_override(
            window=window, screen=window.screen, area=area, region=region
        ):
            result = bpy.ops.view3d.view_camera()
        checks = {"json": json_ok, "operator": "FINISHED" in result}
        print("PME_VIEW_CAMERA_EXAMPLE_CHECKS", checks, flush=True)
        print("PME_VIEW_CAMERA_EXAMPLE_RETURN", result, flush=True)
        return finish(all(checks.values()))
    except Exception:
        traceback.print_exc()
        return finish(False)


bpy.app.timers.register(run, first_interval=0.5)
