import addon_utils
import bpy
import traceback


TAG = "PME_POPUP_CONTEXT_MEMORY_SMOKE"
state = {
    "area_calls": 0,
    "region_calls": 0,
    "draw_records": [],
    "registered": False,
}


def create_operator_type(package):
    class PME_OT_popup_context_memory_smoke(
        package.bl_utils.PopupOperator, bpy.types.Operator
    ):
        bl_idname = "pme.popup_context_memory_smoke"
        bl_label = "PME Popup Context Memory Smoke"
        bl_options = {"INTERNAL"}

        def draw(self, context):
            package.bl_utils.PopupOperator.draw(self, context, self.bl_label)
            state["draw_records"].append(
                {
                    "context_area": (
                        context.area.as_pointer() if context.area else 0
                    ),
                    "bpy_area": (
                        bpy.context.area.as_pointer() if bpy.context.area else 0
                    ),
                    "pme_area": (
                        package.bl_utils.bl_context.area.as_pointer()
                        if package.bl_utils.bl_context.area
                        else 0
                    ),
                    "context_region": (
                        context.region.as_pointer() if context.region else 0
                    ),
                    "pme_region": (
                        package.bl_utils.bl_context.region.as_pointer()
                        if package.bl_utils.bl_context.region
                        else 0
                    ),
                }
            )
            self.layout.label(text="Popup context memory smoke")

        def invoke(self, context, event):
            return package.bl_utils.PopupOperator.invoke(self, context, event)

    return PME_OT_popup_context_memory_smoke


def finish(success):
    try:
        package = state.get("package")
        if package:
            package.c_utils.set_area = state["original_set_area"]
            package.c_utils.set_region = state["original_set_region"]
        state["registered"] = False
    except Exception:
        traceback.print_exc()
        success = False
    print(TAG + "_CHECKS", state.get("checks", {}), flush=True)
    print(TAG + "_RESULT", "OK" if success else "FAILED", flush=True)
    bpy.ops.wm.quit_blender()
    return None


def verify():
    try:
        bpy.context.window.screen = bpy.context.window.screen
        source_area = state["source_area"]
        source_region = state["source_region"]
        records = state["draw_records"]
        expects_private_path = bpy.app.version < (5, 0, 0)
        private_calls = state["area_calls"] + state["region_calls"]
        checks = {
            "invoke_started": state["invoke_result"] in (
                {"RUNNING_MODAL"},
                {"INTERFACE"},
            ),
            "draw_ran": bool(records),
            "version_uses_expected_context_path": (
                private_calls > 0 if expects_private_path else private_calls == 0
            ),
            "draw_context_matches_source_area": bool(records)
            and all(
                record["context_area"] == source_area
                and record["bpy_area"] == source_area
                and record["pme_area"] == source_area
                for record in records
            ),
            "pme_region_matches_source": bool(records)
            and all(record["pme_region"] == source_region for record in records),
        }
        state["checks"] = checks
        print(
            TAG + "_DATA",
            bpy.app.version_string,
            "invoke=",
            state["invoke_result"],
            "calls=",
            (state["area_calls"], state["region_calls"]),
            "records=",
            records,
            flush=True,
        )
        return finish(all(checks.values()))
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
    state["package"] = package

    state["original_set_area"] = package.c_utils.set_area
    state["original_set_region"] = package.c_utils.set_region

    def tracked_set_area(context, area=None):
        state["area_calls"] += 1
        return state["original_set_area"](context, area)

    def tracked_set_region(context, region=None):
        state["region_calls"] += 1
        return state["original_set_region"](context, region)

    package.c_utils.set_area = tracked_set_area
    package.c_utils.set_region = tracked_set_region
    state["operator_type"] = create_operator_type(package)
    bpy.utils.register_class(state["operator_type"])
    state["registered"] = True

    area = next(item for item in bpy.context.screen.areas if item.type == "VIEW_3D")
    region = next(item for item in area.regions if item.type == "WINDOW")
    state["source_area"] = area.as_pointer()
    state["source_region"] = region.as_pointer()
    with bpy.context.temp_override(area=area, region=region):
        state["invoke_result"] = bpy.ops.pme.popup_context_memory_smoke(
            "INVOKE_DEFAULT",
            auto_close=True,
            width=320,
        )
    bpy.app.timers.register(verify, first_interval=0.4)
except Exception:
    traceback.print_exc()
    finish(False)
