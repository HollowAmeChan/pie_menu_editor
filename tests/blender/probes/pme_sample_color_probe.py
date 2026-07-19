import bpy
import traceback


def probe():
    try:
        area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.object.mode_set(mode="SCULPT")
            bpy.ops.brush.asset_activate(
                asset_library_type="ESSENTIALS",
                relative_asset_identifier=(
                    "brushes/essentials_brushes-mesh_sculpt.blend/Brush/Paint Hard"
                ),
            )
            for module_name, operator_name in (
                ("sculpt", "sample_color"),
                ("paint", "sample_color"),
            ):
                operator = getattr(getattr(bpy.ops, module_name), operator_name)
                try:
                    rna = operator.get_rna_type()
                except KeyError:
                    print("PME_SAMPLE_OPERATOR", module_name, None, flush=True)
                    continue
                print(
                    "PME_SAMPLE_OPERATOR",
                    module_name,
                    rna.description,
                    "poll=",
                    operator.poll(),
                    flush=True,
                )
                try:
                    result = operator(location=(area.width // 2, area.height // 2))
                except TypeError:
                    result = operator()
                print("PME_SAMPLE_EXEC", module_name, result, flush=True)
    except Exception:
        traceback.print_exc()
    bpy.ops.wm.quit_blender()


bpy.app.timers.register(probe, first_interval=0.5)
