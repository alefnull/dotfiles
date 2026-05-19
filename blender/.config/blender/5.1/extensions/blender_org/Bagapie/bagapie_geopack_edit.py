import bpy
import json
import os
import re
from bpy.types import Operator
from .utils import Get_addon_pref

class BAGAPIE_OT_geopack_modifier_edit(Operator):
    bl_idname = "bagapie.geopack_modifier_edit"
    bl_label = "Edit GeoPack Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    modifier_path: bpy.props.StringProperty() # type: ignore
    packIdentifier: bpy.props.StringProperty() # type: ignore
    modifierIdentifier: bpy.props.StringProperty() # type: ignore

    show_info: bpy.props.BoolProperty(default=True) # type: ignore

    # === INFO ===
    name: bpy.props.StringProperty() # type: ignore
    author: bpy.props.StringProperty() # type: ignore
    description: bpy.props.StringProperty() # type: ignore
    version: bpy.props.StringProperty() # type: ignore
    contact: bpy.props.StringProperty() # type: ignore
    url: bpy.props.StringProperty() # type: ignore
    license: bpy.props.EnumProperty(
        items=[
            ("ROYALTY_FREE", "Royalty Free", ""),
            ("CC0", "CC0", ""),
            ("CC-BY", "CC-BY", ""),
            ("GPL", "GPL", ""),
            ("MIT", "MIT", "")
        ]
    ) # type: ignore
    blender_version: bpy.props.EnumProperty(
        items=[
            ("3_0", "Blender 3.0", ""),
            ("3_1", "Blender 3.1", ""),
            ("3_2", "Blender 3.2", ""),
            ("3_3", "Blender 3.3", ""),
            ("3_4", "Blender 3.4", ""),
            ("3_5", "Blender 3.5", ""),
            ("3_6", "Blender 3.6", ""),
            ("4_0", "Blender 4.0", ""),
            ("4_1", "Blender 4.1", ""),
            ("4_2", "Blender 4.2", ""),
            ("4_3", "Blender 4.3", ""),
            ("4_4", "Blender 4.4", ""),
            ("4_5", "Blender 4.5", "")
        ]
    ) # type: ignore

    # === USAGE ===
    modifier_active_target: bpy.props.EnumProperty(
        items=[
            ("MESH", "Mesh", ""),
            ("CURVE", "Curve", ""),
            ("MESH_CURVE", "Mesh or Curve", ""),
            ("NEW", "None - Create new object", "")
        ]
    ) # type: ignore
    modifier_use_selection: bpy.props.BoolProperty() # type: ignore
    modifier_allow_asset_browser: bpy.props.BoolProperty() # type: ignore
    modifier_selection_type_mesh: bpy.props.BoolProperty() # type: ignore
    modifier_selection_type_curve: bpy.props.BoolProperty() # type: ignore
    modifier_selection_type_camera: bpy.props.BoolProperty() # type: ignore
    modifier_selection_type_empty: bpy.props.BoolProperty() # type: ignore
    modifier_selection_type_text: bpy.props.BoolProperty() # type: ignore
    modifier_selection_type_volume: bpy.props.BoolProperty() # type: ignore
    modifier_selection_type_light: bpy.props.BoolProperty() # type: ignore

    modifier_coll_name: bpy.props.StringProperty() # type: ignore
    modifier_inputs_list: bpy.props.StringProperty() # type: ignore

    modifier_add_hair_curves: bpy.props.BoolProperty() # type: ignore
    modifier_add_hair_curves_length: bpy.props.FloatProperty() # type: ignore
    modifier_add_hair_curves_points_count: bpy.props.IntProperty() # type: ignore
    modifier_add_hair_curves_count: bpy.props.IntProperty() # type: ignore

    modifier_mesh_paint_mode: bpy.props.BoolProperty() # type: ignore
    modifier_weight_paint_inputs_list: bpy.props.StringProperty() # type: ignore
    modifier_mesh_paint_v_group_name: bpy.props.StringProperty() # type: ignore

    modifier_new_obj_type: bpy.props.EnumProperty(
        items=[
            ("MESH", "Mesh", ""),
            ("CURVE", "Curve", "")
        ]
    ) # type: ignore
    modifier_new_mesh_add_cube: bpy.props.BoolProperty() # type: ignore
    modifier_new_curve_draw: bpy.props.BoolProperty() # type: ignore
    modifier_new_curve_draw_dimension: bpy.props.BoolProperty() # type: ignore
    modifier_new_curve_draw_mode: bpy.props.BoolProperty() # type: ignore

    def invoke(self, context, event):
        if not os.path.isfile(self.modifier_path):
            self.report({'ERROR'}, "Modifier JSON not found")
            return {'CANCELLED'}

        with open(self.modifier_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        info = data.get("info", {})
        usage = data.get("usage", {})

        self.author = info.get("author", "")
        self.description = info.get("description", "")
        self.version = info.get("version", "")
        self.contact = info.get("contact", "")
        self.url = info.get("url", "")
        self.license = info.get("license", "ROYALTY_FREE")
        self.blender_version = info.get("blender_version", "4_0")

        self.modifier_active_target = usage.get("active_target", "MESH")
        self.modifier_use_selection = usage.get("use_selection", False)
        self.modifier_allow_asset_browser = usage.get("asset_browser", False)
        self.modifier_selection_type_mesh = 'MESH' in usage.get("selection_types", [])
        self.modifier_selection_type_curve = 'CURVE' in usage.get("selection_types", [])
        self.modifier_selection_type_camera = 'CAMERA' in usage.get("selection_types", [])
        self.modifier_selection_type_empty = 'EMPTY' in usage.get("selection_types", [])
        self.modifier_selection_type_text = 'TEXT' in usage.get("selection_types", [])
        self.modifier_selection_type_volume = 'VOLUME' in usage.get("selection_types", [])
        self.modifier_selection_type_light = 'LIGHT' in usage.get("selection_types", [])

        self.modifier_coll_name = usage.get("coll_name", "")
        self.modifier_inputs_list = usage.get("coll_input", "")

        self.modifier_add_hair_curves = usage.get("add_hair_curves", False)
        self.modifier_add_hair_curves_length = usage.get("hair_curves_length", 1.0)
        self.modifier_add_hair_curves_points_count = usage.get("hair_curves_points_count", 2)
        self.modifier_add_hair_curves_count = usage.get("hair_curves_count", 10)

        self.modifier_mesh_paint_mode = usage.get("mesh_paint_mode", False)
        self.modifier_mesh_paint_v_group_name = usage.get("paint_v_group_name", "")
        self.modifier_weight_paint_inputs_list = usage.get("paint_inputs_list", "")

        self.modifier_new_obj_type = usage.get("new_object_type", "MESH")
        self.modifier_new_mesh_add_cube = usage.get("new_mesh_add_cube", False)
        self.modifier_new_curve_draw = usage.get("new_curve_draw", False)
        self.modifier_new_curve_draw_dimension = usage.get("new_curve_draw_dimension", False)
        self.modifier_new_curve_draw_mode = usage.get("new_curve_draw_mode", False)

        return context.window_manager.invoke_props_dialog(self, width=450)

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        row = col.row(align=True)
        row.prop(self, "show_info", toggle=True, text="Info")
        row.prop(self, "show_info", toggle=True, text="Usage", invert_checkbox=True)
        col.separator(factor=1.0)

        if self.show_info:
            col.label(text="Author(s)")
            col.prop(self, 'author', text="")
            col.separator(factor=0.6)

            col.label(text="Description")
            col.prop(self, 'description', text="")
            col.separator(factor=0.6)

            col.label(text="Modifier Version (e.g : 1.0.0)")
            col.prop(self, 'version', text="")
            col.separator(factor=0.6)

            col.label(text="Minimal Blender version")
            col.prop(self, 'blender_version', text="")
            col.separator(factor=0.6)

            col.label(text="Contact")
            col.prop(self, 'contact', text="")
            col.separator(factor=0.6)

            col.label(text="URL")
            col.prop(self, 'url', text="")
            col.separator(factor=0.6)

            col.label(text="NodeTree License")
            col.prop(self, 'license', text="")

        else:
            col.label(text="Define how the Modifier works.")
            col.separator(factor=0.5)
            col.label(text='Active Object Must Be :')
            col.prop(self, 'modifier_active_target', text="")

            if self.modifier_active_target == 'NEW':
                row = col.row(align=True)
                split = row.split(factor=0.5)
                row.label(text='New object type :')
                row.prop(self, 'modifier_new_obj_type', text="")
                col.separator(factor=1)

                if self.modifier_new_obj_type == 'MESH':
                    col.prop(self, 'modifier_new_mesh_add_cube', text="Switch to Edit Mode and enable Add Cube tool")
                elif self.modifier_new_obj_type == 'CURVE':
                    col.prop(self, 'modifier_new_curve_draw', text="Switch to draw curve mode")
                    if self.modifier_new_curve_draw:
                        col.label(text='Curve Mode :')
                        row = col.row(align=True)
                        row.prop(self, 'modifier_new_curve_draw_dimension', text="2D", toggle=True)
                        row.prop(self, 'modifier_new_curve_draw_dimension', text="3D", toggle=True, invert_checkbox=True)
                        col.label(text='Curve Projection :')
                        row = col.row(align=True)
                        row.prop(self, 'modifier_new_curve_draw_mode', text="Cursor", toggle=True)
                        row.prop(self, 'modifier_new_curve_draw_mode', text="Surface", toggle=True, invert_checkbox=True)

            elif self.modifier_active_target == 'MESH':
                row = col.row(align=True)
                split = row.split(factor=0.5)
                row.prop(self, 'modifier_mesh_paint_mode', text="Switch to Weight Paint", toggle=True)
                row.prop(self, 'modifier_add_hair_curves', text="Add Hair Curves", toggle=True)

                if self.modifier_mesh_paint_mode:
                    box = col.box()
                    box.label(text='A new Vertex group will be created')
                    box.label(text='Verter Group Name :')
                    box.prop(self, 'modifier_mesh_paint_v_group_name', text="")
                    box.label(text='Verter Group Input :')
                    box.prop(self, 'modifier_weight_paint_inputs_list', text="")

                if self.modifier_add_hair_curves:
                    box = col.box()
                    box.prop(self, 'modifier_add_hair_curves_length', text="Hair Length")
                    box.prop(self, 'modifier_add_hair_curves_points_count', text="Hair Point")
                    box.prop(self, 'modifier_add_hair_curves_count', text="Hair Count")

            col.prop(self, 'modifier_use_selection', text="Use Selection", toggle=True)
            if self.modifier_use_selection:
                box = col.box()
                box.separator(factor=0.5)
                box.scale_y = 0.9
                box.label(text="Collection Name")
                box.prop(self, 'modifier_coll_name', text="")
                box.label(text="Collection Input")
                box.prop(self, 'modifier_inputs_list', text="")

                box.prop(self, 'modifier_allow_asset_browser', text="Allow asset browser selection", icon='ASSET_MANAGER')
                row = box.row(align=True)
                split = row.split(factor=0.7)
                split.label(text='Selected object(s) Must be :')
                col_type = split.column(align=True)
                col_type.prop(self, 'modifier_selection_type_mesh', text="Mesh")
                col_type.prop(self, 'modifier_selection_type_curve', text="Curve")
                col_type.prop(self, 'modifier_selection_type_camera', text="Camera")
                col_type.prop(self, 'modifier_selection_type_empty', text="Empty")
                col_type.prop(self, 'modifier_selection_type_text', text="Text")
                col_type.prop(self, 'modifier_selection_type_volume', text="Volume")
                col_type.prop(self, 'modifier_selection_type_light', text="Light")


    def execute(self, context):
        try:
            with open(self.modifier_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            data['info']['author'] = self.author
            data['info']['description'] = self.description
            data['info']['version'] = self.version
            data['info']['contact'] = self.contact
            data['info']['url'] = self.url
            data['info']['license'] = self.license
            data['info']['blender_version'] = self.blender_version

            data['usage']['active_target'] = self.modifier_active_target
            data['usage']['use_selection'] = self.modifier_use_selection
            data['usage']['asset_browser'] = self.modifier_allow_asset_browser
            data['usage']['selection_types'] = []

            if self.modifier_selection_type_mesh:
                data['usage']['selection_types'].append('MESH')
            if self.modifier_selection_type_curve:
                data['usage']['selection_types'].append('CURVE')
            if self.modifier_selection_type_camera:
                data['usage']['selection_types'].append('CAMERA')
            if self.modifier_selection_type_empty:
                data['usage']['selection_types'].append('EMPTY')
            if self.modifier_selection_type_text:
                data['usage']['selection_types'].append('TEXT')
            if self.modifier_selection_type_volume:
                data['usage']['selection_types'].append('VOLUME')
            if self.modifier_selection_type_light:
                data['usage']['selection_types'].append('LIGHT')

            data['usage']['coll_name'] = self.modifier_coll_name
            data['usage']['coll_input'] = self.modifier_inputs_list

            if self.modifier_active_target == 'MESH': # Add hair curve only if it's a mesh
                data['usage']['add_hair_curves'] = self.modifier_add_hair_curves
            else:
                data['usage']['add_hair_curves'] = False
            data['usage']['hair_curves_length'] = self.modifier_add_hair_curves_length
            data['usage']['hair_curves_points_count'] = self.modifier_add_hair_curves_points_count
            data['usage']['hair_curves_count'] = self.modifier_add_hair_curves_count

            if self.modifier_active_target == 'MESH':
                data['usage']['mesh_paint_mode'] = self.modifier_mesh_paint_mode
            data['usage']['paint_v_group_name'] = self.modifier_mesh_paint_v_group_name
            data['usage']['paint_inputs_list'] = self.modifier_weight_paint_inputs_list

            data['usage']['new_object_type'] = self.modifier_new_obj_type
            if self.modifier_new_obj_type == 'MESH':
                data['usage']['new_mesh_add_cube'] = self.modifier_new_mesh_add_cube
            else:
                data['usage']['new_mesh_add_cube'] = False
            if self.modifier_new_obj_type == 'CURVE':
                data['usage']['new_curve_draw'] = self.modifier_new_curve_draw
            else:
                data['usage']['new_curve_draw'] = False
            data['usage']['new_curve_draw_dimension'] = self.modifier_new_curve_draw_dimension
            data['usage']['new_curve_draw_mode'] = self.modifier_new_curve_draw_mode

            with open(self.modifier_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)

            pref = Get_addon_pref()
            pack = pref.GetGeopack(self.packIdentifier)
            pack.scan_modifiers()

            self.report({'INFO'}, "Modifier updated successfully")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to update: {e}")
            return {'CANCELLED'}

class BAGAPIE_OT_geopack_edit(Operator):
    bl_idname = "bagapie.geopack_edit"
    bl_label = "Edit GeoPack Info"
    bl_options = {'REGISTER', 'UNDO'}

    packIdentifier: bpy.props.StringProperty() # type: ignore

    name: bpy.props.StringProperty() # type: ignore
    authors: bpy.props.StringProperty() # type: ignore
    description: bpy.props.StringProperty() # type: ignore
    version: bpy.props.StringProperty() # type: ignore
    url: bpy.props.StringProperty() # type: ignore
    license: bpy.props.EnumProperty(
        items=[
            ("ROYALTY_FREE", "Royalty Free", ""),
            ("CC0", "CC0", ""),
            ("CC-BY", "CC-BY", ""),
            ("GPL", "GPL", ""),
            ("MIT", "MIT", "")
        ]
    ) # type: ignore
    blender_version: bpy.props.EnumProperty(
        items=[
            ("3_0", "Blender 3.0", ""),
            ("3_1", "Blender 3.1", ""),
            ("3_2", "Blender 3.2", ""),
            ("3_3", "Blender 3.3", ""),
            ("3_4", "Blender 3.4", ""),
            ("3_5", "Blender 3.5", ""),
            ("3_6", "Blender 3.6", ""),
            ("4_0", "Blender 4.0", ""),
            ("4_1", "Blender 4.1", ""),
            ("4_2", "Blender 4.2", ""),
            ("4_3", "Blender 4.3", ""),
            ("4_4", "Blender 4.4", ""),
            ("4_5", "Blender 4.5", ""),
        ]
    ) # type: ignore

    def invoke(self, context, event):
        pref = Get_addon_pref()
        pack = pref.GetGeopack(self.packIdentifier)

        if not os.path.isfile(os.path.join(pack.path, "geopack.config")):
            self.report({'ERROR'}, "Pack config not found")
            return {'CANCELLED'}

        with open(os.path.join(pack.path, "geopack.config"), 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.name = data.get("name", "")
        self.authors = data.get("authors", "")
        self.description = data.get("description", "")
        self.version = data.get("version", "")
        self.url = data.get("url", "")
        self.license = data.get("license", "ROYALTY_FREE")
        self.blender_version = data.get("blender_version", "4_0")

        return context.window_manager.invoke_props_dialog(self, width=450)

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.label(text="Authors")
        col.prop(self, 'authors', text="")
        col.separator(factor=0.5)

        col.label(text="Description")
        col.prop(self, 'description', text="")
        col.separator(factor=0.5)

        col.label(text="Version")
        col.prop(self, 'version', text="")
        col.separator(factor=0.5)

        col.label(text="Minimal Blender Version")
        col.prop(self, 'blender_version', text="")
        col.separator(factor=0.5)

        col.label(text="URL")
        col.prop(self, 'url', text="")
        col.separator(factor=0.5)

        col.label(text="License")
        col.prop(self, 'license', text="")

    def execute(self, context):
        pref = Get_addon_pref()
        pack = pref.GetGeopack(self.packIdentifier)
        config_path = os.path.join(pack.path, "geopack.config")

        if not os.path.isfile(config_path):
            self.report({'ERROR'}, "Pack config not found")
            return {'CANCELLED'}

        data = {
            "name": self.name,
            "authors": self.authors,
            "description": self.description,
            "version": self.version,
            "url": self.url,
            "license": self.license,
            "blender_version": self.blender_version
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

        self.report({'INFO'}, "Pack updated")
        Get_addon_pref().Initialize(bpy.context)
        return {'FINISHED'}

classes = [
    BAGAPIE_OT_geopack_modifier_edit,
    BAGAPIE_OT_geopack_edit
    ]