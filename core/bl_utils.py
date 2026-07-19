import bpy
import _bpy
import os
import re
from .addon import print_exc, ic, get_uprefs
from .screen_utils import get_override_args
from . import constants as CC
from . import pme
from . import c_utils
from .debug_utils import *

cdll = None

re_operator = re.compile(r"^(?:bpy\.ops|O)\.(\w+\.\w+)(\(.*)")
re_prop = re.compile(r"^([^\s]*?)([^.\s]+\.[^.\s]+)(\s*=\s*(.*))$")
re_prop_path = re.compile(r"^([^\s]*?)([^.\s]+\.[^.\s]+)$")
re_prop_set = re.compile(r"^([^\s]*?)([^.\s]+\.[^.\s]+)(\s*=\s*(.*))?$")
re_name_idx = re.compile(r"^(.*)\.(\d+)$")
re_icon = re.compile(r"^([A-Z]*_).*")

CTX_PATHS = {
    "Scene": "C.scene",
    "World": "C.scene.world",
    "Object": "C.object",
    "Material": "C.object.active_material",
    "Area": "C.area",
    "Region": "C.region",
    "SpaceUVEditor": "C.space_data.uv_editor",
    "GPUFXSettings": "C.space_data.fx_settings",
    "GPUSSAOSettings": "C.space_data.fx_settings.ssao",
    "GPUDOFSettings": "C.space_data.fx_settings.dof",
    "DopeSheet": "C.space_data.dopesheet",
    "FileSelectParams": "C.space_data.params",
    "PreferencesInput": "C.preferences.inputs",
    "PreferencesEdit": "C.preferences.edit",
    "PreferencesFilePaths": "C.preferences.filepaths",
    "PreferencesSystem": "C.preferences.system",
    "PreferencesView": "C.preferences.view",
}
CTX_FULLPATHS = dict(
    CompositorNodeComposite="C.active_node",
    View3DShading="C.space_data.shading",
    View3DOverlay="C.space_data.overlay",
    BrushGpencilSettings="paint_settings().brush.gpencil_settings",
    TransformOrientationSlot="C.scene.transform_orientation_slots[0]",
)


def find_context(area_type):
    area = None
    for a in bpy.context.screen.areas:
        if a.type == area_type:
            area = a
            break

    if not area:
        return None

    return {"area": area, "window": bpy.context.window, "screen": bpy.context.screen}


def paint_settings(context=None):
    if not context:
        context = bl_context

    sd = context.space_data
    if sd and sd.type == 'IMAGE_EDITOR':
        return context.tool_settings.image_paint

    if context.mode == 'GPENCIL_PAINT':
        return context.tool_settings.gpencil_paint
    elif context.mode == 'GPENCIL_SCULPT':
        return context.tool_settings.gpencil_sculpt

    return unified_paint_panel().paint_settings(context)


def unified_paint_panel():
    ret = getattr(bpy.types, "VIEW3D_PT_tools_brush", None)
    if ret:
        return ret

    from bl_ui.properties_paint_common import UnifiedPaintPanel

    return UnifiedPaintPanel


def template_palette(layout, data, property, color=True):
    parameters = bpy.types.UILayout.bl_rna.functions["template_palette"].parameters
    if "color" in parameters:
        layout.template_palette(data, property, color=color)
    else:
        layout.template_palette(data, property)


def brush_asset_selector(layout, context=None, settings=None):
    context = context or bl_context
    settings = settings or paint_settings(context)
    if not settings:
        return False

    from bl_ui.properties_paint_common import BrushAssetShelf

    BrushAssetShelf.draw_popup_selector(layout, context, settings.brush)
    return True


def _relative_asset_path(filepath, directory):
    filepath = os.path.normcase(os.path.abspath(filepath))
    directory = os.path.normcase(os.path.abspath(directory))
    try:
        if os.path.commonpath((filepath, directory)) != directory:
            return None
    except ValueError:
        return None
    return os.path.relpath(filepath, directory).replace(os.sep, "/")


def _brush_asset_args(settings, brush):
    reference = getattr(settings, "brush_asset_reference", None)
    if (
        settings.brush == brush
        and reference
        and reference.relative_asset_identifier
    ):
        return dict(
            asset_library_type=reference.asset_library_type,
            asset_library_identifier=reference.asset_library_identifier,
            relative_asset_identifier=reference.relative_asset_identifier,
        )

    if not brush.asset_data:
        return None

    library = brush.library
    if library is None:
        if not bpy.data.filepath:
            return None
        return dict(
            asset_library_type='LOCAL',
            asset_library_identifier="",
            relative_asset_identifier=f"Brush/{brush.name}",
        )

    filepath = bpy.path.abspath(library.filepath)
    essentials = bpy.utils.system_resource('DATAFILES', path="assets")
    relative = _relative_asset_path(filepath, essentials) if essentials else None
    if relative is not None:
        return dict(
            asset_library_type='ESSENTIALS',
            asset_library_identifier="",
            relative_asset_identifier=f"{relative}/Brush/{brush.name}",
        )

    for asset_library in get_uprefs().filepaths.asset_libraries:
        relative = _relative_asset_path(filepath, bpy.path.abspath(asset_library.path))
        if relative is not None:
            return dict(
                asset_library_type='CUSTOM',
                asset_library_identifier=asset_library.name,
                relative_asset_identifier=f"{relative}/Brush/{brush.name}",
            )

    return None


def activate_brush(name, context=None):
    context = context or bl_context
    settings = paint_settings(context)
    if not settings:
        raise RuntimeError("A paint mode with an active brush tool is required")

    brush = bpy.data.brushes.get(name)
    if brush is None:
        raise RuntimeError(f"Brush not found: {name}")
    if settings.brush == brush:
        return {'FINISHED'}

    brush_property = settings.bl_rna.properties["brush"]
    if not brush_property.is_readonly:
        settings.brush = brush
        return {'FINISHED'}

    args = _brush_asset_args(settings, brush)
    if args is None:
        raise RuntimeError(f"Brush is not available as an asset: {name}")
    return bpy.ops.brush.asset_activate(**args)


def mesh_loop_multi_select(*args, ring=False, **kwargs):
    legacy_operator = bpy.ops.mesh.loop_multi_select
    try:
        legacy_operator.get_rna_type()
    except KeyError:
        operator_name = (
            "select_edge_ring_multi" if ring else "select_edge_loop_multi"
        )
        return getattr(bpy.ops.mesh, operator_name)(*args, **kwargs)
    return legacy_operator(*args, ring=ring, **kwargs)


def mesh_faces_mirror_uv(*args, direction='POSITIVE', precision=3, **kwargs):
    legacy_operator = bpy.ops.mesh.faces_mirror_uv
    try:
        legacy_operator.get_rna_type()
    except KeyError:
        mesh_axis = 'POS_X' if direction == 'POSITIVE' else 'NEG_X'
        return bpy.ops.uv.copy_mirrored_faces(
            *args,
            mesh_axis=mesh_axis,
            uv_axis='X',
            precision=precision,
            **kwargs,
        )
    return legacy_operator(
        *args, direction=direction, precision=precision, **kwargs
    )


def sculpt_sample_color(*args, **kwargs):
    legacy_operator = bpy.ops.sculpt.sample_color
    try:
        legacy_operator.get_rna_type()
    except KeyError:
        return bpy.ops.paint.sample_color(*args, **kwargs)
    return legacy_operator(*args, **kwargs)


def _scene_collections(context=None):
    context = context or bpy.context
    collections = []
    visited = set()

    def visit(collection):
        pointer = collection.as_pointer()
        if pointer in visited:
            return
        visited.add(pointer)
        collections.append(collection)
        for child in collection.children:
            visit(child)

    visit(context.scene.collection)
    return collections


def object_move_to_collection(
    *args, collection_index=-1, collection_uid=-1, **kwargs
):
    collections = _scene_collections()
    parameters = bpy.ops.object.move_to_collection.get_rna_type().properties
    if collection_index >= len(collections):
        raise IndexError(f"Collection index out of range: {collection_index}")

    if "collection_uid" in parameters:
        if collection_uid < 0 and collection_index >= 0:
            collection_uid = collections[collection_index].session_uid
        if collection_uid >= 0:
            kwargs["collection_uid"] = collection_uid
    else:
        if collection_index < 0 and collection_uid >= 0:
            collection_index = next(
                (
                    index
                    for index, collection in enumerate(collections)
                    if collection.session_uid == collection_uid
                ),
                -1,
            )
            if collection_index < 0:
                raise ValueError(f"Collection UID not found: {collection_uid}")
        if collection_index >= 0:
            kwargs["collection_index"] = collection_index

    return bpy.ops.object.move_to_collection(*args, **kwargs)


def uname(collection, name, sep=".", width=3, check=True):
    is_iterable = True
    try:
        iter(collection)
    except:
        is_iterable = False

    if check:
        if is_iterable:
            if name not in collection:
                return name
        else:
            if not hasattr(collection, name):
                return name

    idx = 1

    mo = re_name_idx.search(name)
    if mo:
        name = mo.group(1)
        idx = int(mo.group(2))

    while True:
        ret = "%s%s%s" % (name, sep, str(idx).zfill(width))
        if is_iterable:
            if ret not in collection:
                return ret
        else:
            if not hasattr(collection, ret):
                return ret

        idx += 1


class BlContext:
    context = None
    bl_area = None
    bl_region = None
    bl_space_data = None

    mods = dict(
        fracture='FRACTURE',
        cloth='CLOTH',
        dynamic_paint='DYNAMIC_PAINT',
        smoke='SMOKE',
        fluid='FLUID_SIMULATION',
        collision='COLLISION',
        soft_body='SOFT_BODY',
        particle_system='PARTICLE_SYSTEM',
    )

    data = dict(
        armature="ARMATURE",
        camera="CAMERA",
        curve="CURVE",
        lamp="LAMP",
        lattice="LATTICE",
        mesh="MESH",
        meta_ball="META",
        speaker="SPEAKER",
    )

    def __init__(self):
        self.texture_context = 'MATERIAL'
        self.areas = []
        self.area_map = {}

    def get_modifier_by_type(self, ao, tp):
        if not ao or not hasattr(ao, "modifiers"):
            return None

        for mod in ao.modifiers:
            if mod.type == tp:
                return mod

    def __getattr__(self, attr):
        # if not BlContext.context:
        #     BlContext.context = bpy.context

        C = bpy.context
        BlContext.context = _bpy.context

        texture_context = self.texture_context

        if attr == "preferences":
            return getattr(_bpy.context, "preferences", None)

        elif attr == "space_data":
            if self.areas:
                value = self.area_map[self.areas[-1]]
            else:
                value = getattr(_bpy.context, attr, None)

            if not value:
                value = BlContext.bl_space_data

        else:
            value = getattr(_bpy.context, attr, None)

        ao = getattr(BlContext.context, "active_object", None)

        if not value:
            try:
                if attr == "region":
                    value = BlContext.bl_region

                elif attr == "area":
                    value = BlContext.bl_area

                elif attr == "material_slot":
                    if ao and ao.active_material_index < len(ao.material_slots):
                        value = ao.material_slots[ao.active_material_index]

                elif attr == "material":
                    if self.areas:
                        sd = self.area_map[self.areas[-1]]
                        if sd.type == 'PROPERTIES':
                            texture_context = getattr(sd, "texture_context", None)

                    # if True:
                    if texture_context == 'MATERIAL':
                        value = ao and ao.active_material

                elif attr == "world":
                    value = (
                        hasattr(BlContext.context, "scene")
                        and BlContext.context.scene.world
                    )

                elif attr == "brush":
                    ps = paint_settings(BlContext.context)
                    value = ps.brush if ps and hasattr(ps, "brush") else None

                elif attr == "bone":
                    value = C.object.data.bones.active

                elif attr == "light":
                    value = C.object.data

                elif attr == "lightprobe":
                    value = C.object.data

                elif attr == "edit_bone":
                    value = C.object.data.edit_bones.active

                elif attr == "texture":
                    if self.areas:
                        sd = self.area_map[self.areas[-1]]
                        if sd.type == 'PROPERTIES':
                            texture_context = sd.texture_context

                    if texture_context == 'WORLD':
                        value = C.scene.world.active_texture
                    elif texture_context == 'MATERIAL':
                        value = ao and ao.active_material.active_texture
                    else:
                        value = None

                elif attr == "texture_slot":
                    if self.areas:
                        sd = self.area_map[self.areas[-1]]
                        if sd.type == 'PROPERTIES':
                            texture_context = sd.texture_context

                    if texture_context == 'WORLD':
                        value = C.scene.world.texture_slots[
                            C.scene.world.active_texture_index]
                    elif texture_context == 'MATERIAL':
                        value = ao and ao.active_material.texture_slots[
                            ao.active_material.active_texture_index]
                    else:
                        value = None

                elif attr == "texture_node":
                    value = None

                elif attr == "line_style":
                    value = None

                elif attr in BlContext.data:
                    if ao and ao.type == BlContext.data[attr]:
                        value = ao.data

                elif attr == "particle_system":
                    if ao and len(ao.particle_systems):
                        value = ao.particle_systems[ao.particle_systems.active_index]
                    else:
                        value = None

                elif attr == "pose_bone":
                    value = BlContext.context.active_pose_bone

                elif attr in BlContext.mods:
                    value = self.get_modifier_by_type(ao, BlContext.mods[attr])

            except:
                print_exc()

        # if not value:
        #     print("PME: 'Context' object has no attribute '%s'" % attr)

        return value

    def set_context(self, context):
        BlContext.context = context

    def reset(self, context):
        BlContext.bl_area = context.area
        BlContext.bl_region = context.region
        BlContext.bl_space_data = context.space_data

    def use_area(self, area):
        self.areas.append(area)
        self.area_map[area] = get_space_data(area)

    def restore_area(self):
        area = self.areas.pop()
        self.area_map.pop(area, None)


bl_context = BlContext()


class BlBpy:
    def __getattribute__(self, attr):
        if attr == "context":
            return bl_context

        return getattr(bpy, attr, None)


bl_bpy = BlBpy()


class BlProp:
    def __init__(self):
        self.data = {}

    def get(self, text):
        prop = None
        if text in self.data:
            try:
                prop = eval(self.data[text], pme.context.globals)
            except:
                pass
            return prop

        obj, _, prop_name = text.rpartition(".")

        co = None
        try:
            text = "%s.bl_rna.properties['%s']" % (obj, prop_name)
            co = compile(text, '<string>', 'eval',)
        except:
            pass

        if co:
            self.data[text] = co
            try:
                prop = eval(co, pme.context.globals)
            except:
                pass
            return prop

        return None


bp = BlProp()


class PopupOperator:
    active = 0

    width: bpy.props.IntProperty(
        name="Width",
        description="Width of the popup",
        default=300,
        options={'SKIP_SAVE'},
    )
    auto_close: bpy.props.BoolProperty(
        default=True,
        name="Auto Close",
        description="Auto close the popup",
        options={'SKIP_SAVE'},
    )
    hide_title: bpy.props.BoolProperty(
        default=False, name="Hide Title",
        description=(
            "Hide title.\n"
            "  Used when Auto Close is enabled.\n"
        ), options={'SKIP_SAVE'},
    )
    center: bpy.props.BoolProperty(
        name="Center", description="Center", options={'SKIP_SAVE'}
    )
    title: bpy.props.StringProperty(
        name="Title",
        description=(
            "Title of the popup.\n"
            "  Used when Auto Close is enabled.\n"
        ),
        options={'SKIP_SAVE'},
    )

    def check(self, context):
        return True

    def cancel(self, context):
        PopupOperator.active -= 1

    def draw(self, context, title=None):
        layout = self.layout

        if self.auto_close:
            if not self.hide_title:
                layout.label(text=self.title or title or self.bl_label)
            else:
                col = self.layout.column(align=True)
                row = col.row(align=True)
                row.scale_y = 0.00000000001
                row.label(text=" ")
                layout = col.column()

        if self.mx != -1:
            context.window.cursor_warp(self.mx, self.my)
            self.mx = -1

        c_utils.set_area(context, bl_context.bl_area)
        c_utils.set_region(context, bl_context.bl_region)

        return layout

    def draw_post(self, context):
        c_utils.set_area(context)
        c_utils.set_region(context)

    def execute(self, context):
        PopupOperator.active -= 1
        return {'FINISHED'}

    def invoke(self, context, event):
        PopupOperator.active += 1
        self.mx, self.my = -1, -1
        bl_context.reset(context)

        popup_padding = round(
            2 * CC.POPUP_PADDING * get_uprefs().view.ui_scale + CC.WINDOW_MARGIN
        )
        if self.width > context.window.width - popup_padding:
            self.width = context.window.width - popup_padding

        if self.center:
            mx = context.window.width >> 1
            my = round(0.9 * context.window.height)
            if self.auto_close:
                mx -= self.width >> 1
                mx = max(0, mx)
                self.mx = mx + (self.width >> 1)
                self.my = my
            context.window.cursor_warp(mx, my)

        else:
            offset = round(30 * get_uprefs().view.ui_scale)
            w2 = self.width >> 1
            mid_x = context.window.width >> 1
            min_x = w2 + CC.POPUP_PADDING + offset
            max_x = context.window.width - (self.width >> 1) - CC.POPUP_PADDING - offset
            mx, my = event.mouse_x, event.mouse_y
            if self.auto_close:
                min_x -= w2
                max_x -= w2

            if mid_x < max_x < event.mouse_x:
                if self.auto_close:
                    self.mx, self.my = max_x + w2, my
                context.window.cursor_warp(max_x, my)

            elif mid_x > min_x > event.mouse_x:
                if self.auto_close:
                    self.mx, self.my = min_x + w2, my
                context.window.cursor_warp(min_x, my)

            else:
                if self.auto_close:
                    self.mx, self.my = mx, my
                    context.window.cursor_warp(self.mx - w2, self.my)

        if self.auto_close:
            return context.window_manager.invoke_popup(self, width=self.width)
        else:
            return context.window_manager.invoke_props_dialog(self, width=self.width)


class ConfirmBoxHandler:
    bl_label = "Confirm"
    confirm: bpy.props.BoolProperty(default=True, options={'SKIP_SAVE'})
    box: bpy.props.BoolProperty(default=False, options={'SKIP_SAVE'})

    def on_input(self, value):
        self.confirm_value = value

    def on_confirm(self, value):
        pass

    def modal(self, context, event):
        if event.type == 'TIMER':
            if self.confirm_value is not None:
                self.on_confirm(self.confirm_value)
                context.window_manager.event_timer_remove(self.timer)
                self.timer = None
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        self.on_confirm(True)
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.confirm:
            self.confirm_value = None
            if not self.box:
                return context.window_manager.invoke_confirm(self, event)

            self.timer = context.window_manager.event_timer_add(
                0.1, window=context.window
            )
            context.window_manager.modal_handler_add(self)
            msg = getattr(self, "title", self.bl_label) or "OK?"

            confirm_box(msg, self.on_input)
            return {'RUNNING_MODAL'}

        else:
            self.on_confirm(True)

        return {'FINISHED'}


class PME_OT_confirm_box(bpy.types.Operator):
    bl_idname = "pme.confirm_box"
    bl_label = "Pie Menu Editor"
    bl_options = {'INTERNAL'}

    func = None

    message: bpy.props.StringProperty(default="Confirm", options={'SKIP_SAVE'})
    icon: bpy.props.StringProperty(default='QUESTION', options={'SKIP_SAVE'})
    width: bpy.props.IntProperty(default=0, options={'SKIP_SAVE'})

    def draw(self, context):
        row = self.layout.row(align=True)
        row.separator()
        row.label(text=self.message, icon=ic(self.icon))

    def cancel(self, context):
        if self.__class__.func:
            self.__class__.func(False)
            self.__class__.func = None

    def execute(self, context):
        if self.__class__.func:
            self.__class__.func(True)
            self.__class__.func = None
        return {'FINISHED'}

    def invoke(self, context, event):
        kwargs = dict()
        if self.width:
            kwargs.update(width=self.width)

        return context.window_manager.invoke_props_dialog(self, **kwargs)


def confirm_box(message, func=None, icon='QUESTION', width=0):
    PME_OT_confirm_box.func = func
    bpy.ops.pme.confirm_box(
        'INVOKE_DEFAULT', message=message, icon=ic(icon), width=width
    )


class PME_OT_message_box(bpy.types.Operator):
    bl_idname = "pme.message_box"
    bl_label = ""
    bl_description = "Message Box"
    bl_options = {'INTERNAL'}

    title: bpy.props.StringProperty(default="Pie Menu Editor", options={'SKIP_SAVE'})
    message: bpy.props.StringProperty(options={'SKIP_SAVE'})
    icon: bpy.props.StringProperty(default='INFO', options={'SKIP_SAVE'})

    def draw_message_box(self, menu, context):
        lines = self.message.split("\n")
        icon = self.icon
        for line in lines:
            menu.layout.label(text=line, icon=ic(icon))
            icon = 'NONE'

    def execute(self, context):
        context.window_manager.popup_menu(self.draw_message_box, title=self.title)
        return {'FINISHED'}


def message_box(text, icon='INFO', title="Pie Menu Editor"):
    bpy.ops.pme.message_box(message=text, icon=ic(icon), title=title)
    return True


class PME_OT_input_box(bpy.types.Operator):
    bl_idname = "pme.input_box"
    bl_label = "Input Box"
    bl_options = {'INTERNAL'}
    bl_property = "value"
    func = None
    prev_value = ""

    value: bpy.props.StringProperty()
    prop: bpy.props.StringProperty(options={'SKIP_SAVE'})

    def draw(self, context):
        if self.prop:
            data_path, _, prop = self.prop.rpartition(".")
            data = pme.context.eval(data_path)
            col = self.layout.column()
            col.prop(data, prop)

        else:
            self.layout.prop(self, "value", text="")

    def execute(self, context):
        if PME_OT_input_box.func:
            PME_OT_input_box.func(self.value)

        PME_OT_input_box.prev_value = self.value
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.prop:
            value = pme.context.eval(self.prop)
            if isinstance(value, str):
                self.value = value
        else:
            self.value = PME_OT_input_box.prev_value

        return context.window_manager.invoke_props_dialog(self)


def input_box(func=None, prop=None):
    PME_OT_input_box.func = func
    bpy.ops.pme.input_box('INVOKE_DEFAULT', prop=prop or "")
    return True


def _gen_prop_path(ptr, prop, prefix):
    path = prefix + "."
    try:
        path += ptr.path_from_id(prop.identifier)
    except:
        path += prop.identifier

    return path


def gen_prop_path(ptr, prop):
    if isinstance(ptr, bpy.types.Space):
        return _gen_prop_path(ptr, prop, "C.space_data")

    if isinstance(ptr, bpy.types.Brush):
        return "paint_settings().brush." + prop.identifier

    ptr_clname = ptr.__class__.__name__
    id_data = ptr.id_data
    id_data_clname = id_data.__class__.__name__
    DBG_PROP_PATH and logi("PTR", ptr_clname)
    DBG_PROP_PATH and logi("ID_DATA", id_data_clname)
    DBG_PROP_PATH and logi("PROP", prop)

    ao = bpy.context.object
    if ao and ao.data and ao.data == id_data:
        return _gen_prop_path(ptr, prop, "C.object.data")

    if ptr_clname in CTX_FULLPATHS:
        return "%s.%s" % (CTX_FULLPATHS[ptr_clname], prop.identifier)

    if id_data_clname in CTX_PATHS:
        return _gen_prop_path(ptr, prop, CTX_PATHS[id_data_clname])

    if ptr_clname in CTX_PATHS:
        return _gen_prop_path(ptr, prop, CTX_PATHS[ptr_clname])

    if id_data:
        ptr_path = repr(ptr)
        if "..." in ptr_path:
            return None

        try:
            if eval(ptr_path) != ptr:
                return None
        except:
            return None

        return "%s.%s" % (ptr_path, prop.identifier)

    return None


class PME_OT_popup_close(bpy.types.Operator):
    bl_idname = "pme.popup_close"
    bl_label = "Close All Popups"

    def execute(self, context):
        close_popups()
        return {'FINISHED'}


def close_popups():
    # global cdll
    # if not cdll:
    #     cdll = ctypes.CDLL("")

    # NC_SCREEN = 3 << 24
    # ND_SCREENBROWSE = 1 << 16
    # cdll.WM_event_add_notifier(
    #     ctypes.c_void_p(bpy.context.as_pointer()),
    #     NC_SCREEN | ND_SCREENBROWSE, None)
    bpy.context.window.screen = bpy.context.window.screen

    return True


def is_read_only():
    try:
        # bpy.utils.register_class(PME_OT_popup_close)
        # bpy.utils.unregister_class(PME_OT_popup_close)
        bpy.types.WindowManager.pme_temp = bpy.props.BoolProperty()
        del bpy.types.WindowManager.pme_temp
    except:
        return True

    return False


def get_space_data(area_type):
    C = bpy.context
    win = C.window
    area = C.area or bl_context.bl_area

    if area and area.type == area_type:
        return area.spaces.active

    for a in win.screen.areas:
        if a.type == area_type:
            return a.spaces.active

    cur_type = area.type
    area.type = area_type
    ret = area.spaces.active
    area.type = cur_type
    return ret


# def get_context_data(area_type):  # B4.0: Replace dictionary override with context.temp_override
#     ret = dict()
#     ret["space_data"] = get_space_data(area_type)
#     return ret


# MIGRATION_TODO: Replace dictionary override with context.temp_override
def ctx_dict(
    window=None, screen=None, area=None, region=None, scene=None, workspace=None
):
    import warnings

    warnings.warn(
        "ctx_dict() is deprecated, use get_override_args() instead",
        DeprecationWarning,
        stacklevel=2,
    )

    d = get_override_args(
        area=area,
        region=region,
        screen=screen,
        window=window,
        scene=scene,
        workspace=workspace,
    )

    # default_kwargs = {
    #     "window": bl_context.window,
    #     "screen": bl_context.screen,
    #     "area": bl_context.area,
    #     "region": bl_context.region,
    #     "scene": bl_context.scene,
    #     "workspace": bl_context.workspace,
    # }

    # # MIGRATION_TODO:  Investigate the need for bl_context here and make sure to remove it.
    # for k, v in default_kwargs.items():
    #     if k not in d:
    #         d[k] = v

    return d


def area_header_text_set(text=None, area=None):
    if area is None:
        area = bpy.context.area

    if area is None:
        # Note: bpy.context.area becomes None during modal execution if `screen.screen_full_area` is called.
        areas = _find_areas_with_header_text_support(bpy.context)
        if not areas:
            logw(
                "area_header_text_set",
                "No valid areas with 'header_text_set' available in current context. Exiting function.",
            )
            return
    else:
        areas = [area]

    for area in areas:
        if text:
            area.header_text_set(text=text)
        else:
            area.header_text_set(text=None)


def _find_areas_with_header_text_support(context):
    return [area for area in context.screen.areas if hasattr(area, 'header_text_set')]


def popup_area(area, width=320, height=400, x=None, y=None):
    """
    Create a popup window by duplicating an area with specified dimensions.

    This function temporarily modifies the source area's size parameters to control
    the resulting popup window size, then restores the original values.

    Args:
        area: Source area to duplicate
        width: Desired width for the popup window
        height: Desired height for the popup window
        x: X position for window placement (optional)
        y: Y position for window placement (optional)
    """
    C = bpy.context
    window = C.window

    # Get direct access to ScrArea structure via c_utils
    try:
        from ctypes import cast, POINTER
        carea = cast(area.as_pointer(), POINTER(c_utils.ScrArea))
        area_struct = carea.contents

        # Store original area dimensions
        orig_totrct = {
            'xmin': area_struct.totrct.xmin,
            'xmax': area_struct.totrct.xmax, 
            'ymin': area_struct.totrct.ymin,
            'ymax': area_struct.totrct.ymax
        }
        orig_winx = area_struct.winx
        orig_winy = area_struct.winy

        # Apply UI scaling temporarily for consistent duplication
        upr = get_uprefs()
        ui_scale = upr.view.ui_scale
        ui_line_width = upr.view.ui_line_width
        upr.view.ui_scale = 1
        upr.view.ui_line_width = 'THIN'

        try:
            # Calculate position if specified, otherwise use current area position
            if x is not None and y is not None:
                pos_x = max(0, x - (width // 2))
                pos_y = max(0, y - (height // 2))

                # Ensure window stays within screen bounds
                max_x = window.width - min(width, 200)
                max_y = window.height - min(height, 150)
                pos_x = min(pos_x, max_x)
                pos_y = min(pos_y, max_y)
            else:
                pos_x = orig_totrct['xmin']
                pos_y = orig_totrct['ymin']

            # Temporarily modify area size parameters that area_dupli uses
            area_struct.totrct.xmin = pos_x
            area_struct.totrct.ymin = pos_y
            area_struct.totrct.xmax = pos_x + width
            area_struct.totrct.ymax = pos_y + height
            area_struct.winx = width
            area_struct.winy = height

            # Store current window count to identify new window
            initial_windows = set(C.window_manager.windows)

            # Create the duplicate window with modified area dimensions
            with C.temp_override(area=area):
                bpy.ops.screen.area_dupli('INVOKE_DEFAULT')

            # Log results for debugging
            new_windows = set(C.window_manager.windows) - initial_windows
            if new_windows:
                new_window = list(new_windows)[0]
                actual_width = new_window.width
                actual_height = new_window.height

                if actual_width != width or actual_height != height:
                    logw("Size difference detected - this may be due to DPI scaling or window manager constraints")

        finally:
            # Always restore original area dimensions
            area_struct.totrct.xmin = orig_totrct['xmin']
            area_struct.totrct.xmax = orig_totrct['xmax']
            area_struct.totrct.ymin = orig_totrct['ymin'] 
            area_struct.totrct.ymax = orig_totrct['ymax']
            area_struct.winx = orig_winx
            area_struct.winy = orig_winy

            # Restore UI settings
            upr.view.ui_scale = ui_scale
            upr.view.ui_line_width = ui_line_width

    except Exception as e:
        print(f"Error in popup_area: {e}")
        print("Falling back to basic area duplication")

        # Fallback to basic duplication if memory manipulation fails
        upr = get_uprefs()
        ui_scale = upr.view.ui_scale
        ui_line_width = upr.view.ui_line_width
        upr.view.ui_scale = 1
        upr.view.ui_line_width = 'THIN'

        try:
            with C.temp_override(area=area):
                bpy.ops.screen.area_dupli('INVOKE_DEFAULT')
        finally:
            upr.view.ui_scale = ui_scale
            upr.view.ui_line_width = ui_line_width


def enum_item_idx(data, prop, identifier):
    items = data.bl_rna.properties[prop].enum_items
    for i, e in enumerate(items):
        if e.identifier == identifier:
            return i

    return -1


def register():
    bl_context.set_context(bpy.context)

    pme.context.add_global("C", bl_context)
    pme.context.add_global("context", bl_context)
    pme.context.add_global("bl_context", bl_context)
    pme.context.add_global("bpy", bl_bpy)
    pme.context.add_global("paint_settings", paint_settings)
    pme.context.add_global("unified_paint_panel", unified_paint_panel)
    pme.context.add_global("template_palette", template_palette)
    pme.context.add_global("brush_asset_selector", brush_asset_selector)
    pme.context.add_global("activate_brush", activate_brush)
    pme.context.add_global("mesh_loop_multi_select", mesh_loop_multi_select)
    pme.context.add_global("mesh_faces_mirror_uv", mesh_faces_mirror_uv)
    pme.context.add_global("sculpt_sample_color", sculpt_sample_color)
    pme.context.add_global("object_move_to_collection", object_move_to_collection)
    pme.context.add_global("re", re)
    pme.context.add_global("message_box", message_box)
    pme.context.add_global("input_box", input_box)
    pme.context.add_global("close_popups", close_popups)
    # pme.context.add_global("ctx", get_context_data)
