# BagaPie
# By Antoine Bagattini / Kiara Bagattini

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

# ___________________________________________ THANKS ! ___________________________________________

# This addon is free, you can use it for any purpose.

# Special thanks to Alexandre Labedade aka Alesk, Franck Demongin and Clovis Flayols which contributed to it's developpment.
# Also thanks to all the people who support the development of this addon.
# Thanks to Dr Sybren A. Stüvel, this addon exist thanks to him.

# ___________________________________________ DEAR DEVS ___________________________________________

# This addon has been developed over the years, and some parts of the code might hurt your eyes.
# The addon is slowly but progressively being rewritten to improve its code quality through updates.
# Any feedback is, of course, welcome. <3


bl_info = {
    "name": "BagaPie Modifier",
    "author": "Antoine Bagattini, Laura Mercadal, BagaCorp, Alexandre Labedade aka Alesk",
    "version": (11, 0, 8),
    "description": "Toolbox for architecture and environment based on Geometry Nodes.",
    "blender": (4, 2, 0),
    "cathegory": "3D view",
    "location": "3D View (Obj Mode): J key | 3D View (Edit Mode): D key | Addon panel",
}

# Import standard
import os
import json
import re

# Import Blender
import bpy
from bpy.types import Operator
from bl_keymap_utils.io import keyconfig_merge

# Import BagaPie
from .bagapie_geopack_create import BAGAPIE_Geopack_ModifierItem, BAGAPIE_Geopack_Item
from . import bagapie_geopack_icon
from .utils import Get_addon_pref, debug
from .bagapie_group_op import group_prefix_menu

addon_keymaps = []
copied_texture_mask_settings = {}


class BagapieSettings(bpy.types.PropertyGroup):
    val: bpy.props.StringProperty() # type: ignore

###################################################################################
# ADDON PREFERENCES
###################################################################################
class bagapie_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    ###################################################################################
    # GENERAL PREFERENCES
    ###################################################################################
    general_preferences: bpy.props.BoolProperty(name="Preferences", default=False) # type: ignore
    scatter_preferences: bpy.props.BoolProperty(name="Preferences", default=False) # type: ignore
    asset_browser: bpy.props.BoolProperty(name="Preferences", default=False) # type: ignore
    library_location: bpy.props.StringProperty(name="Preferences", default="NONE") # type: ignore
    pie_custom: bpy.props.BoolProperty(name="Preferences", default=False) # type: ignore
    how_it_works: bpy.props.BoolProperty(name="Preferences", default=False) # type: ignore
    nodes_to_addon: bpy.props.BoolProperty(name="Preferences", default=False) # type: ignore
    help_support: bpy.props.BoolProperty(name="Preferences", default=False) # type: ignore
    issues: bpy.props.BoolProperty(name="Preferences", default=False) # type: ignore
    

    ###################################################################################
    # SCATTER PREFERENCES
    ###################################################################################
    security_features: bpy.props.BoolProperty(name="Security Features", default=True) # type: ignore
    use_default_proxy: bpy.props.BoolProperty(name="Use Default Proxy", default=True) # type: ignore
    apply_scale_default: bpy.props.BoolProperty(name="Apply Scale Default", default=True) # type: ignore
    use_camera_culling: bpy.props.BoolProperty(name="Apply Scale Default", default=True) # type: ignore
    maximum_polycount: bpy.props.IntProperty(name="Maximum Polycount", default=10000000, min = 0) # type: ignore
    polycount_for_proxy: bpy.props.IntProperty(name="Minimum Polycount", default=100000, min = 0) # type: ignore
    default_percent_display: bpy.props.IntProperty(name="Display percentage", default=100, min = 0, max = 100) # type: ignore
    keep_unlinked_assets_in_scene: bpy.props.BoolProperty(
        name="Keep assets in scene",
        default=False,
        description="If enabled, objects removed from the scatter collection will be automatically relinked to the main scene collection to prevent them from disappearing"
    ) # type: ignore
    # SCATTER UI
    scatter_posrot: bpy.props.BoolProperty(name="", default=False) # type: ignore
    scatter_tools: bpy.props.BoolProperty(name="", default=False) # type: ignore
    scatter_random: bpy.props.BoolProperty(name="", default=False) # type: ignore
    scatter_mask: bpy.props.BoolProperty(name="", default=False) # type: ignore
    scatter_tuto: bpy.props.BoolProperty(name="", default=False) # type: ignore
    scatter_geopack_export: bpy.props.BoolProperty(name="", default=False) # type: ignore


    ###################################################################################
    # TOOLS VISIBILITY
    ###################################################################################
    tool_flags = {
        "displace": True,
        "instancesdisplace": True,
        "deform": True,
        "line": True,
        "grid": True,
        "circle": True,
        "curve": True,
        "proxy": True,
        "saveasasset": False,
        "savematerial": False,
        "group": True,
        "scatter": True,
        "scatterpaint": True,
        "pointsnapinstance": True,
        "ivy": True,
        "union": True,
        "difference": True,
        "pointeffector": True,
        "camculling": True,
        "wall": True,
        "wallbrick": True,
        "window": False,
        "pipes": True,
        "beamwire": True,
        "beam": True,
        "linearstair": True,
        "stairspiral": True,
        "floor": True,
        "handrail": True,
        "column": True,
        "cable": True,
        "tiles": True,
        "fence": True,
        "siding": True,
        "autoarrayoncurve": True,
        "window_modern": True,
        "window_classic": True,
        "door_simple": True,
        "door_double": True,
        "cable_creator": True,
        "paving": True,
        "perforatedgrid": True,
        "plank": True,
        "draw_curve": True,
        "arrayalongshape": True,
        "bool_through": True,
        "tessellate": True,
        "insert_circle": True,
        "array_along_shape": True,
        "bolt_corner": True,
        "face_to_grid": True,
        "face_to_paving": True,
        "face_to_perforated_grid": True,
        "face_to_plank": True,
    }

    for name, default in tool_flags.items():
        exec(f"{name}: bpy.props.BoolProperty(name='{name}', default={default})  # type: ignore")


    ###################################################################################
    # ADDON UI PROP
    ###################################################################################
    asset_source: bpy.props.BoolProperty(name="Support Preferences", default=False) # type: ignore


    ###################################################################################
    # GROUP PROP
    ###################################################################################
    group_offset: bpy.props.FloatVectorProperty(
        name="Instance Offset",
        description="Move all objects in the selected object's collection and update coll instance offset",
        subtype='TRANSLATION',
        unit='LENGTH'
    ) # type: ignore


    ###################################################################################
    # NODES TO PANEL (DEMO)
    ###################################################################################
    ntp_float_a: bpy.props.FloatProperty(name="InputValue", default=15.4) # type: ignore
    ntp_float_b: bpy.props.FloatProperty(name="InputValue", default=3.14) # type: ignore
    ntp_float_c: bpy.props.FloatProperty(name="InputValue", default=5) # type: ignore
    ntp_float_d: bpy.props.FloatProperty(name="InputValue", default=1000) # type: ignore
    ntp_bool_a: bpy.props.BoolProperty(name="InputValue", default=False) # type: ignore


    ###################################################################################
    # GEOPACK
    ###################################################################################
    hide_geopack: bpy.props.BoolProperty(name="Disable GeoPack", default=False) # type: ignore
    geopack_pref: bpy.props.BoolProperty(name="GeoPack Preferences", default=False) # type: ignore

    @staticmethod
    def geopack_create_pack_method():
        name="Create New Pack"
        default=False
        def update(self, context):
            if not self.geopack_create_pack:
                self.geopack_np_name = ""
                self.geopack_np_description = ""
                self.geopack_np_version = ""
                self.geopack_np_url = ""
                self.geopack_np_blender_version = "3_0"
                self.geopack_np_license = "ROYALTY_FREE"
                self.geopack_np_location = ""

        return locals()
    
    geopack_create_pack: bpy.props.BoolProperty(**geopack_create_pack_method()) # type: ignore
    geopack_storage: bpy.props.BoolProperty(name="Create New Pack", default=False) # type: ignore
    geopack_string: bpy.props.StringProperty(name="String", default="") # type: ignore
    geopack_icon_scale: bpy.props.IntProperty(name="GeoPack Pie Menu Icon Scale", default=7, min = 1, max = 50) # type: ignore
    # CREATE PACK
    geopack_np_name: bpy.props.StringProperty(name="String", default="") # type: ignore
    geopack_np_authors: bpy.props.StringProperty(name="String", default="") # type: ignore
    geopack_np_description: bpy.props.StringProperty(name="String", default="") # type: ignore
    geopack_np_version: bpy.props.StringProperty(name="String", default="") # type: ignore
    geopack_np_url: bpy.props.StringProperty(name="String", default="") # type: ignore
    blender_version = [
        ("3_0","Blender 3.0",""),
        ("3_1","Blender 3.1",""),
        ("3_2","Blender 3.2",""),
        ("3_3","Blender 3.3",""),
        ("3_4","Blender 3.4",""),
        ("3_5","Blender 3.5",""),
        ("3_6","Blender 3.6",""),
        ("4_0","Blender 4.0",""),
        ("4_1","Blender 4.1",""),
        ("4_2","Blender 4.2",""),
        ("4_3","Blender 4.3",""),
    ]
    geopack_np_blender_version: bpy.props.EnumProperty(items=blender_version) # type: ignore
    license = [
        ("ROYALTY_FREE", "Royalty Free", "The author retains all rights to the 3D model but allows users to use it without having to pay additional fees."),
        ("CC0", "CC0", "The author waives all rights to the 3D model, allowing users to freely use, modify, and distribute it without restriction."),
        ("CC-BY", "CC-BY", "A free and legal license that allows users to use, modify, and distribute the 3D model, as long as they give credit to the original author."),
        ("GPL", "GPL", "A free and open-source license that allows users to distribute, modify, and reuse the 3D model, ensuring that it remains accessible to all."),
        ("MIT", "MIT", "An open-source license that allows users to distribute, modify, and reuse the 3D model, often used in free and open-source software projects."),
    ]
    geopack_np_license: bpy.props.EnumProperty(items=license) # type: ignore
    geopack_np_location: bpy.props.StringProperty(name="String", default="") # type: ignore
    # PACK STORAGE
    geopack_packs_location: bpy.props.StringProperty(name="String", default="") # type: ignore
    # HOW GEOPACK WORKS
    geopack_tooltips: bpy.props.BoolProperty(name="TIPS !", default=False) # type: ignore
    geopack_user_tuto: bpy.props.BoolProperty(name="I want to use packs", default=True)    # type: ignore
    geopacks_list: bpy.props.CollectionProperty(
        name="Geopacks List",
        type=BAGAPIE_Geopack_Item) # type: ignore
    # SCATTER PREVIEW RENDER
    geopack_render_ozone: bpy.props.FloatProperty(
        name="",
        default=2,
        description="Amount of ozone in the sky shader (affects sky color)"
    ) # type: ignore
    geopack_render_sunint: bpy.props.FloatProperty(
        name="",
        default=0.7,
        description="Intensity of the sun in the sky shader"
    ) # type: ignore
    geopack_render_resolution: bpy.props.IntProperty(
        name="",
        default=256,
        description="Render resolution in pixels (width and height)"
    ) # type: ignore
    geopack_render_samples: bpy.props.IntProperty(
        name="",
        default=64,
        description="Number of render samples used for preview rendering"
    ) # type: ignore
    geopack_render_exposure: bpy.props.FloatProperty(
        name="",
        default=-1.8,
        description="Exposure value for the render preview"
    ) # type: ignore
    geopack_render_sunelev: bpy.props.FloatProperty(
        name="",
        default=20,
        description="Sun elevation angle (in degrees) for the preview sky"
    ) # type: ignore
    geopack_render_sunrot: bpy.props.FloatProperty(
        name="",
        default=90,
        description="Sun rotation (in degrees) around the Z-axis"
    ) # type: ignore
    geopack_render_generate: bpy.props.BoolProperty(
        name="",
        default=True,
        description="Enable to generate a preview render for the modifier"
    ) # type: ignore
    geopack_render_focal: bpy.props.IntProperty(
        name="",
        default=80,
        description="Fallback focal length (in mm) if the current view lens is unavailable"
    ) # type: ignore
    geopack_render_use_current_focal: bpy.props.BoolProperty(
        name="",
        default=True,
        description="Use the current viewport focal length for camera setup during preview render"
    ) # type: ignore
    geopack_render_use_current_world: bpy.props.BoolProperty(
        name="",
        default=False,
        description="Use the current world as lighting in preview render"
    ) # type: ignore


    ###################################################################################
    # ALPHA & Debug
    ###################################################################################
    alpha_tool: bpy.props.BoolProperty(name="Enable Experimental", default=False) # type: ignore
    feature_enabled: bpy.props.BoolProperty(name="Enable Experimental", default=False) # type: ignore
    debug: bpy.props.BoolProperty(name="Debug Mode", default=False) # type: ignore


    def Initialize(self,context):
        self.ScanGeoPacks(context)
        self.reloadPacks = False

    def load(self,context):
        self.Initialize(context)

    def GetPackPath(self,context,geopack_identifier):
        pref = Get_addon_pref()

        if pref.geopacks_list:
            for gp in pref.geopacks_list:
                if gp.identifier == geopack_identifier:
                    return gp.path
        
        return None
    
    def GetGeopack(self,geopack_identifier):
        #pref = Get_addon_pref()

        if self.geopacks_list:
            for gp in self.geopacks_list:
                if gp.identifier == geopack_identifier:
                    return gp
        
        return None

    def ScanGeoPacks(self,context):
        pref = Get_addon_pref()
        if pref.geopack_packs_location and os.path.isdir(pref.geopack_packs_location):
            self.geopacks_list.clear()
            
            for gp in [ f.path for f in os.scandir(pref.geopack_packs_location) if f.is_dir() ]:
                print(gp)
                config = os.path.join(gp,'geopack.config')
                if os.path.isfile(config):
                    with open(config) as f:
                        config_str = f.read()

                        try:
                            data = json.loads(config_str)

                            new_item = self.geopacks_list.add()
                            new_item.name = data['name']
                            new_item.path = gp
                            new_item.identifier = str(hash(gp))
                            new_item.description = data['description']
                            new_item.config = config_str

                            new_item.scan_modifiers()

                            asset_path = os.path.join(gp,'Assets')
                            if os.path.exists(asset_path):
                                
                                prefs = bpy.context.preferences
                                filepaths = prefs.filepaths
                                asset_libraries = filepaths.asset_libraries
                                update_lib = None
                                for lib in asset_libraries:
                                    if lib.name == new_item.name:
                                        update_lib = lib
                                        break
                                if update_lib:
                                    # update existing library path
                                    update_lib.path = asset_path
                                else:
                                    # add new library path
                                    bpy.ops.preferences.asset_library_add(directory=asset_path)
                                    asset_libraries[len(asset_libraries)-1].name = new_item.name
                        except:
                            print("Error loading GeoPack",gp)

    def PrintPackInfo(self,context,col,pack):
        regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https:// or ftp:// or ftps://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domaine...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...ou adresse IP
        r'(?::\d+)?'  # optionnellement un port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        row = col.row()
        row = row.split(factor=0.05)
        row.separator(factor = 1)
        col = row.box()

        row_edit = col.row()
        row_edit.alignment = 'RIGHT'
        edit_op = row_edit.operator("bagapie.geopack_edit", text="", icon='GREASEPENCIL')
        edit_op.packIdentifier = pack.identifier

        data = json.loads(pack.config)
        if pack.description != "":
            col.label(text="Description : " + pack.description)
        if data['authors'] != "":
            col.label(text="Authors : " + data['authors'])
        if data['version'] != "":
            col.label(text="Version : " + data['version'])
        col.label(text="License : " + data['license'])
        col.label(text="Minimal Blender Version : " + data['blender_version'].replace("_", "."))
        if data['url'] != "":
            if re.match(regex, data['url']):
                col.operator("wm.url_open", text="Creator link", icon ='URL').url = data['url']
            else:
                col.label(text="URL : " + data['url'])

    def PrintPackModifier(self,context,col,pack):
        regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https:// or ftp:// or ftps://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domaine...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...ou adresse IP
        r'(?::\d+)?'  # optionnellement un port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        row = col.row()
        row = row.split(factor=0.05)
        row.separator(factor = 1)
        col = row.column()

        if len(pack.modifiers_list) == 0:
            box=col.box()
            box.label(text="No modifier found")
            box.label(text="You can create modifier via the pie menu ( J ) > 'New GeoPack Modifier'")

        for modifier in pack.modifiers_list:

            if not modifier.displayOptions:
                mo_row = col.row(align=True)
                mo_row.prop(modifier,"pieVisibility", text="", icon = "HIDE_OFF" if modifier.pieVisibility else "HIDE_ON") # icon hide : HIDE_ON
                mo_row.prop(modifier, 'displayOptions', text=modifier.name.removeprefix("BP_"),toggle = True, icon = 'TRIA_RIGHT')
                mo_row.alert = True
                delete_button = mo_row.operator("bagapie.geopack_modifier_delete", text="", depress = False, icon = 'CANCEL')
                delete_button.packIdentifier = pack.identifier
                delete_button.modifierIdentifier = modifier.identifier
                delete_button.modifierName = modifier.name

            else:
                mo_row = col.row(align=True)
                mo_row.scale_y = 1.5
                mo_row.prop(modifier,"pieVisibility", text="", icon = "HIDE_OFF" if modifier.pieVisibility else "HIDE_ON") # icon hide : HIDE_ON
                mo_row.prop(modifier, 'displayOptions', text=modifier.name.removeprefix("BP_"),toggle = True, icon = 'DISCLOSURE_TRI_DOWN')
                mo_row.alert = True
                delete_button = mo_row.operator("bagapie.geopack_modifier_delete", text="", depress = False, icon = 'CANCEL')
                delete_button.packIdentifier = pack.identifier
                delete_button.modifierIdentifier = modifier.identifier
                delete_button.modifierName = modifier.name

                mo_box = col.box()
                mo_box.scale_y = 0.6

                data = json.loads(modifier.config) # waiting to find how to store JSON data

                if data['info']['name'] in bagapie_geopack_icon.previews:
                    row_icon = mo_box.row() # row in the modifier box
                    row_icon = row_icon.split(factor=0.15) #split row
                    row_icon.separator(factor = 1)
                    row_icon = row_icon.split(factor=0.8) #split row
                    box_icon = row_icon.box() # box in the row
                    row_icon_bis = box_icon.row(align=True) #row in the box
                    row_icon_bis.scale_y = 1.6
                    row_icon_bis.template_icon(icon_value = bagapie_geopack_icon.previews[data['info']['name']].icon_id, scale=10)
                    col_icon_bis = row_icon_bis.column(align=True) #row in the box
                    remove_icon = col_icon_bis.operator("bagapie.remove_icon", text="", icon = 'CANCEL')
                    remove_icon.target_folder = pack.path
                    remove_icon.img_mo_name = data['info']['name']
                    col_icon_bis.operator("bagapie.refresh_icons", text="", icon="FILE_REFRESH")

                else:
                    col_icon = mo_box.column()
                    col_icon.scale_y = 1.6
                    row_icon = col_icon.row(align=True)
                    add_icon = row_icon.operator("bagapie.add_icon", text="Add Icon")
                    add_icon.target_folder = pack.path
                    add_icon.img_mo_name = data['info']['name']
                    row_icon.operator("bagapie.refresh_icons", text="", icon="FILE_REFRESH")
                
                if data['info']['description'] != "None":
                    row = mo_box.row()
                    row.scale_y = 1.6
                    row.label(text=f"Description: {data['info']['description']}")
                else:
                    row = mo_box.row()
                    row.scale_y = 1.6
                    row.alignment = 'RIGHT'
                edit_op = row.operator("bagapie.geopack_modifier_edit", text="", icon='GREASEPENCIL')
                edit_op.modifier_path = modifier.path
                edit_op.packIdentifier = pack.identifier
                edit_op.modifierIdentifier = modifier.identifier
                if data['info']['author'] != "None":
                    mo_box.label(text=f"Authors: {data['info']['author']}")
                if data['info']['version'] != "None":
                    mo_box.label(text=f"Version: {data['info']['version']}")
                if data['info'].get('blender_version') not in [None, "None", ""]:
                    mo_box.label(text=f"Blender Min: {data['info']['blender_version'].replace('_', '.')}")
                if data['info']['license'] != "None":
                    mo_box.label(text="License : " + data['info']['license'])
                mo_box.separator(factor=0.1)

                col_URL = mo_box.column(align=True)
                if data['info']['url'] != "None":
                    if re.match(regex, data['info']['url']):
                        rowe = col_URL.row()
                        rowe.scale_y = 1.6
                        rowe.operator("wm.url_open", text="Modifier link", icon ='URL').url = data['info']['url']
                    else:
                        col_URL.label(text="URL : " + data['info']['url'])
                if data['info']['contact'] != "None":
                    if re.match(regex, data['info']['contact']):
                        rowe = col_URL.row()
                        rowe.scale_y = 1.6
                        rowe.operator("wm.url_open", text="Contact", icon ='URL').url = data['info']['contact']
                    else:
                        col_URL.label(text="Contact : " + data['info']['url'])
                        
                    
                target=""
                selection =""
                selection_type =""
                
                # Describe Modifier Workflow
                col.separator(factor = 1)
                box = mo_box.column(align=True)
                box.label(text="How this modifier will work :")
                if data['usage']['active_target'] == 'MESH':
                    target = 'a MESH '
                    if data['usage']['mesh_paint_mode']:
                        box.label(text="- Active object will receive the modifier ")
                        box.label(text="  and switch to Weight Paint.")
                    elif data['usage']['add_hair_curves']:
                        box.label(text="- A new Hair Object will be created")
                        box.label(text="  and will receive the modifier")
                    else:
                        box.label(text="- Active object will receive the modifier ")

                elif data['usage']['active_target'] == 'CURVE':
                    target = 'a CURVE '


                elif data['usage']['active_target'] != 'NEW':
                    target = 'a MESH or CURVE '
                    box.label(text="- Active object will receive the modifier")
                else :
                    target = 'nothing/whatever '
                    if data['usage']['new_object_type'] == 'MESH':
                        new_obj = "mesh"
                        if data['usage']['new_mesh_add_cube']:
                            draw_mode = " and switch to add cube"
                        else:
                            draw_mode = ""
                    elif data['usage']['new_object_type'] == 'CURVE':
                        new_obj = "curve"
                        if data['usage']['new_curve_draw']:
                            draw_mode = " and switch to draw curve"
                        else:
                            draw_mode = ""
                    
                    if data['usage']['use_selection']:
                        target =""
                        selection = 'object from type '

                    box.separator(factor = 1)
                    box.label(text="- A new "+ new_obj +" will be created"+draw_mode)
                    
                if data['usage']['use_selection']:
                    selection = 'and select others object from type '
                    box.separator(factor = 1)
                    box.label(text="- Selected objects will be linked to new coll.")
                    box.separator(factor = 1)

                    if 'MESH' in data['usage']['selection_types']: selection_type += "Mesh, "
                    if 'CURVE' in data['usage']['selection_types']: selection_type += "Curve, "
                    if 'CAMERA' in data['usage']['selection_types']: selection_type += "Camera, "
                    if 'EMPTY' in data['usage']['selection_types']: selection_type += "Empty, "
                    if 'TEXT' in data['usage']['selection_types']: selection_type += "Text, "
                    if 'VOLUME' in data['usage']['selection_types']: selection_type += "Volume, "
                    if 'LIGHT' in data['usage']['selection_types']: selection_type += "Light, "


                # DIRTY STUPID LAZY CODE START
                count = 0
                size = 40
                message = "- In order to use your modifier the user must select " + target + selection + selection_type
                mess = message
                length = int(size)
                caracter = length
                temp = 0
                for i in message:            
                    if count == 0:
                        if mess[0] == " ":
                            o = length
                            if len(mess) > o:
                                while mess[o] != " ":
                                    o += 1
                                    if len(mess) == o:
                                        break
                            box.label(text=mess[1:o])
                            caracter = length

                        elif mess == message:
                            o = length
                            if o >= len(mess):
                                o = len(mess)-1
                            while message[o] != " ":
                                o += 1
                                if len(mess) == o:
                                    break
                            box.label(text=mess[0:o])
                            caracter = length                    
                        else :
                            count = temp
                            caracter += 1
                    count += 1
                    temp = count
                    mess = mess[1:]
                    if count == caracter:
                        count = 0

    def PrintPackAssets(self,context,col,pack,location):

        row = col.row()
        row = row.split(factor=0.05)
        row.separator(factor = 1)
        col = row.column()
        setup_row = col.row(align=True)
        setup_row.scale_y = 1.3

        library = bpy.context.preferences.filepaths.asset_libraries.get(pack.name)
        if library is None:
            set_pack = setup_row.operator("bagapie.geopack_create_assetlib", depress = False, icon = 'ASSET_MANAGER')
            set_pack.pack_name = pack.name
            set_pack.pack_path = pack.path

        else:
            add_assets = setup_row.operator("bagapie.geopack_assetlib_add_file", text="Add blend file to Pack's Assets Library", depress = False, icon = 'ADD')
            add_assets.pack_path = pack.path

            # DEFINED WHEN CREATING THE PACK
            col = col.box()
            col.label(text=pack.name +"'s Asset Library files :")

            # Check if the "Assets" folder exists and list the Blender files if it does
            assets_folder_path = os.path.join(pack.path, "Assets")
            if os.path.exists(assets_folder_path):
                # Read the file names in the folder and sort them alphabetically
                blend_files = sorted([f for f in os.listdir(assets_folder_path) if f.endswith(".blend")])

                # Add a label for each Blender file
                for blend_file in blend_files:
                    col.label(text="     - "+blend_file)
            else:
                col.alert = True
                col.label(text="'Assets' folder not found")

            col.separator(factor = 1)
            loc_row = col.row(align=True)
            loc_row.label(text="Library Location : "+os.path.join(pack.path, "Assets"))

            open_loc = loc_row.operator("bagapie.open_file_explorer", text="", depress = False, icon = 'FILEBROWSER')
            open_loc.filepath = pack.path

    def PrintPackData(self,context,col,pack,location):

        main_row = col.row()
        main_row = main_row.split(factor=0.1)
        main_row.separator(factor = 1)
        main_row = main_row.split(factor=0.85)
        box = main_row.box()

        # INFO
        info_row = box.row()
        info_row = info_row.split(factor=0.3)
        info_row.scale_y = 1.5
        info_row.prop(pack,"displayInfo", text="Info", icon = "INFO")
        if pack.displayInfo:
            self.PrintPackInfo(context,box,pack)
        
        # MODIFIER
        mo_row = box.row()
        mo_row = mo_row.split(factor=0.3)
        mo_row.scale_y = 1.5
        mo_row.prop(pack,"displayModifier", text="Modifier", icon = "GEOMETRY_NODES")
        if pack.displayModifier:
            self.PrintPackModifier(context,box,pack)

        # ASSETS
        as_row = box.row()
        as_row = as_row.split(factor=0.3)
        as_row.scale_y = 1.5
        as_row.prop(pack,"displayAssets", text="Assets", icon = "ASSET_MANAGER")
        if pack.displayAssets:
            self.PrintPackAssets(context,box,pack,location)


        row = box.row()
        row = row.split(factor=0.7)

        if pack.scanModifiers != pack.displayOptions:
            pack.scanModifiers = pack.displayOptions
            pack.scan_modifiers()

    def geopack_settings_draw(self,layout,text,propname):
        row = layout.row(align=False)
        row = row.split(factor=0.7)
        row.label(text=f"   {text}:")
        row.prop(self, propname, text="")

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        pref = Get_addon_pref()

        ###################################################################################
        # GEOPACK
        ###################################################################################
        if not self.hide_geopack:
            box = layout.box()
            row = box.row(align=False)
            row.prop(self, 'geopack_pref', text = "GeoPack", emboss = False, icon = "PACKAGE")
            if self.geopack_pref:
                row.scale_x=2
                row.prop(pref, 'geopack_tooltips', toggle=True, text ="", icon = 'QUESTION')
                col = box.column(align=False)
                if pref.geopack_packs_location == '' or (pref.geopack_packs_location != '' and not os.path.isdir(pref.geopack_packs_location)):
                    
                    col.label(text="First, set the folder where the packs will be stored.")
                    col.label(text="You can always move the packs and their storage locations after this step")
                    row = col.row()
                    row.scale_y=2
                    path_selector = row.operator("bagapie.set_geopacks_location", text="Set packs location", depress = False, icon = 'IMPORT')
                    path_selector.filepath = pref.geopack_packs_location

                else:
                    row = col.row()
                    row.scale_y=2

                    row.operator("bagapie.geopack_import", text="Install Pack", depress = False, icon = 'IMPORT')
                    
                    row.prop(pref, 'geopack_create_pack', text="Create New Pack", icon = 'ADD')
                    col.separator(factor = 2)
                    
                    row.prop(pref, 'geopack_storage', text="Storage", icon = 'FILE_FOLDER')
                    col.separator(factor = 2)
                    
                    if not pref.geopack_create_pack:

                        if bpy.context.preferences.is_dirty:
                            row = col.row()
                            row.operator("wm.save_userpref", text="Save preferences", depress = False, icon = 'IMPORT')

                        # Affichage de la liste des GEOPACKS
                        for pack_item in self.geopacks_list:
                            header_row = col.row(align=True)

                            if pack_item.displayOptions:
                                header_row.scale_y = 2
                                pack_icon = "TRIA_DOWN"
                            else:
                                pack_icon = "TRIA_RIGHT"

                            header_row.scale_x = 2
                            header_row.prop(pack_item,"pieVisibility", text="", icon = "HIDE_OFF" if pack_item.pieVisibility else "HIDE_ON") # icon hide : HIDE_ON
                            header_row.prop(pack_item,"displayOptions", text=pack_item.name, icon = pack_icon)
                            
                            export_button = header_row.operator("bagapie.geopack_export", text="", depress = False, icon = 'EXPORT')
                            export_button.packIdentifier = pack_item.identifier
                            
                            header_row.alert = True

                            delete_button = header_row.operator("bagapie.geopack_delete", text="", depress = False, icon = 'CANCEL')
                            delete_button.packIdentifier = pack_item.identifier
                            delete_button.packName = pack_item.name
                            

                            if pack_item.displayOptions:
                                self.PrintPackData(context,col,pack_item, pref.geopack_packs_location)

                            pack_item.scanModifiers = pack_item.displayOptions

                    else:
                        col.label(text="Pack Name")
                        col.prop(pref, 'geopack_np_name', text="")
                        col.label(text="Pack Author(s)")
                        col.prop(pref, 'geopack_np_authors', text="")
                        col.label(text="Description")
                        col.prop(pref, 'geopack_np_description', text="")
                        col.label(text="Pack Version")
                        col.prop(pref, 'geopack_np_version', text="")
                        col.label(text="Pack URL")
                        col.prop(pref, 'geopack_np_url', text="")
                        col.label(text="Oldest Blender Version Compatible")
                        col.prop(pref, 'geopack_np_blender_version', text="")
                        col.label(text="Pack License")
                        col.prop(pref, 'geopack_np_license', text="")
                        """
                        col.label(text="Pack Location")
                        row = col.row(align=True)
                        row.prop(pref, 'geopack_np_location', text="")
                        tips = row.operator("bagapie.tooltips", text="", depress = False, icon = 'FILEBROWSER')
                        tips.message = 'select path'
                        """

                        if pref.geopack_np_name:
                            col.separator(factor = 2)
                            row=col.row()
                            row.scale_y=1.5
                            create_pack = row.operator("bagapie.geopack_create", text="Create !", depress = False)
                            create_pack.root_path = pref.geopack_packs_location
                            create_pack.pack_name = pref.geopack_np_name

                    if pref.geopack_storage:
                        col.separator(factor = 3)
                        box = col.box()
                        box.label(text="Current Location :", icon = 'FILEBROWSER')
                        col_sto= box.column(align=True)
                        col_sto.scale_y=1.2
                        path_row=col_sto.row(align=True)
                        path_row.prop(pref, 'geopack_packs_location', text="")
                        open_loc = path_row.operator("bagapie.open_file_explorer", text="", depress = False, icon = 'FILEBROWSER')
                        open_loc.filepath = pref.geopack_packs_location
                        col_sto.operator("bagapie.bp_move", text="Move all packs to new location", depress = False).sourcePath = pref.geopack_packs_location
                        
                    
                # TIPS / HELP
                if self.geopack_tooltips:
                    col.separator(factor = 2)
                    box = col.box()
                    box.label(text="How it works ?")
                    row = box.row()
                    row.prop(pref, 'geopack_user_tuto', toggle=True)
                    row.prop(pref, 'geopack_user_tuto', toggle=True, text = "I want to create packs", invert_checkbox = True)
                    if self.geopack_user_tuto:
                        box.label(text="1 - Set the location of your packs; where files will be stored")
                        box.label(text="2 - Install pack(s) (.geopack files)")
                        box.label(text="3 - Go to 3D View > Press V > Select a Pack > Select a modifier")
                        box.separator(factor = 1)
                        box.label(text="The way to use a pack may vary depending on the modifier.")
                        box.label(text="After installing a pack, you can find information on how to use it and descriptions in its properties")
                        row = box.row(align=True)
                        row.scale_y = 1.5
                        row.operator("wm.url_open", text="GeoPack Demo", icon = 'PLAY').url = "https://www.youtube.com/playlist?list=PLSVXpfzibQbiSre0t4ir5Ctw1VHZxZI5P"
                        row.operator("wm.url_open", text="BagaPie Documentation", icon = 'TEXT').url = "https://www.f12studio.fr/bagapiev6"

                    else:
                        box.label(text="1 - Set the location of your packs; where files will be stored")
                        box.label(text="2 - Create a new pack (in this area)")
                        box.label(text="3 - Go to 3D View > Select your object and the GN mofifier you want to save in the modifier stack.")
                        box.label(text="4 - Press J > New GeoPack Modifier")
                        box.label(text="5 - A box apear, select the pack's modifier and follow Instructions > 'OK'")
                        box.label(text="6 - Now your modifier is visible in the GeoPack pie menu (V)")
                        box.label(text="7 - In this panel, you will be able to export your geopack to share it")
                        box.separator(factor = 1)
                        row = box.row(align=True)
                        row.scale_y = 1.5
                        row.operator("wm.url_open", text="Creator Demo", icon = 'PLAY').url = "https://www.youtube.com/playlist?list=PLSVXpfzibQbiSre0t4ir5Ctw1VHZxZI5P"
                        row.operator("wm.url_open", text="BagaPie Documentation", icon = 'TEXT').url = "https://www.f12studio.fr/bagapiev6"

        ###################################################################################
        # GENERAL PREFERENCES
        ###################################################################################
        box = layout.box()
        box.prop(self, 'general_preferences', text = "Preferences", emboss = False, icon = "PREFERENCES")
        if self.general_preferences:
            wm = context.window_manager
            kc_user = wm.keyconfigs.user
            display_keymaps = keyconfig_merge(kc_user, kc_user)
            done_a = True
            done_b = True
            done_c = True
            box.label(text="Menu Shortcuts:")
            col=box.column(align=True)

            found_gp_sh = False
            for km, kc in display_keymaps:
                for kmi in km.keymap_items:
                    if kmi.idname == "bagapie.group":
                        found_gp_sh =True
                        break
                if found_gp_sh ==True:
                    break

            for km, kc in display_keymaps:
                for kmi in km.keymap_items:
                    # PIE MENU MAIN
                    if kmi.name == 'BagaPie':
                        row = col.row(align=False)
                        row = row.split(factor=0.7)
                        row.label(text="   Main Pie (Object Mode):")
                        row.prop(kmi, "type", text="", full_event=True)
                    # PIE MENU TOOLS
                    if kmi.name == 'BagaPie Tools' and done_c:
                        row = col.row(align=False)
                        row = row.split(factor=0.7)
                        row.label(text="   Tools Pie (Edit Mode):")
                        row.prop(kmi, "type", text="", full_event=True)
                        col.separator(factor=0.5)
                    # PIE MENU GEOPACK
                    if kmi.name == 'BagaPie GeoPack' and done_c:
                        row = col.row(align=False)
                        done_c = False
                        row = row.split(factor=0.7)
                        row.label(text="   GeoPack Pie (Object Mode):")
                        row.prop(kmi, "type", text="", full_event=True)

                        row = col.row(align=False)
                        row = row.split(factor=0.7)
                        row.label(text="   GeoPack Icon Scale:")
                        row.prop(self, "geopack_icon_scale", text="")
                        col.separator(factor=0.5)

                    # GROUP SHORTCUT
                    if kmi.idname == "bagapie.group" and found_gp_sh == True:
                        row = col.row(align=False)
                        row = row.split(factor=0.7)
                        row.label(text="   Group Shortcut :")
                        row.prop(kmi, "type", text="", full_event=True)

                    # PANEL POP
                    if kmi.name == "BagaPie Modifier":
                        row = col.row(align=False)
                        row = row.split(factor=0.7)
                        row.label(text="   Main Panel (Popup) :")
                        row.prop(kmi, "type", text="", full_event=True)
            
            if found_gp_sh == False:
                col.operator('bagapie.replace_shortcut', text="Add Group Shortcut")

            box.separator(factor=0.5)            
            box.label(text="Duplicate Group :")
            col=box.column(align=True)
            for km, kc in display_keymaps:
                for kmi in km.keymap_items:
                    # DUPLICATE
                    if kmi.name == 'Duplicate Group' and done_a:
                        done_a = False
                        row = col.row(align=False)
                        row = row.split(factor=0.7)
                        row.label(text="   Simple:")
                        row.prop(kmi, "type", text="", full_event=True)
                    # DUPLICATE LINKED
                    if kmi.name == 'Duplicate Linked Group' and done_b:
                        done_b = False
                        row = col.row(align=False)
                        row = row.split(factor=0.7)
                        row.label(text="   Linked:")
                        row.prop(kmi, "type", text="", full_event=True)
            
            box.separator(factor=0.5)            
            box.label(text="GeoPack Scatter Icon Generator Settings:")
            col=box.column(align=True)
            self.geopack_settings_draw(layout=col,text="Icon Resolution",propname="geopack_render_resolution")
            self.geopack_settings_draw(layout=col,text="Render Samples",propname="geopack_render_samples")
            self.geopack_settings_draw(layout=col,text="Exposure",propname="geopack_render_exposure")
            self.geopack_settings_draw(layout=col,text="Ozone",propname="geopack_render_ozone")
            self.geopack_settings_draw(layout=col,text="Sun Intensity",propname="geopack_render_sunint")
            self.geopack_settings_draw(layout=col,text="Sul Elevation",propname="geopack_render_sunelev")
            self.geopack_settings_draw(layout=col,text="Sul Rotation",propname="geopack_render_sunrot")
            self.geopack_settings_draw(layout=col,text="Camera Default Focal",propname="geopack_render_focal")
            self.geopack_settings_draw(layout=col,text="Use 3D view focal",propname="geopack_render_use_current_focal")
            self.geopack_settings_draw(layout=col,text="Generate Icon by default for Scatter",propname="geopack_render_generate")
            
            box.separator(factor=0.5)    
            box.label(text="Dev :")
            alpha_tools = box.column()
            alpha_tools.alert = True
            alpha_tools.prop(pref, 'alpha_tool', text="Enable Experimental Features")
            if self.alpha_tool:
                alpha_tools.label(text="WORK IN PROGRESS", icon = "ERROR")
                alpha_tools.label(text="ONLY FOR TESTING !", icon = "ERROR")
                
            box.prop(pref, 'debug', text="Debug Mode")

        ###################################################################################
        # ASSETS
        ###################################################################################
        box = layout.box()
        box.prop(self, 'asset_browser', text = "Assets", emboss = False, icon = "ASSET_MANAGER")
        if self.asset_browser:
            col = box.column(align=False)
            col.scale_y = 2
            col.operator('bagapie.parametricpresets', icon = "ASSET_MANAGER", text ="Setup BagaPie's Parametric Library CC-0")
            if self.library_location == "NONE" or not os.path.exists(self.library_location):
                col.operator('bagapie.setuppacklocation', icon = "ASSET_MANAGER", text ="Set BagaPie Assets Packs Storage Location")
            else:
                col.operator('bagapie.installpack', icon = "ASSET_MANAGER", text ="Install BagaPie Asset Pack (.baga files)")

            col_content = box.column(align=True)
            col_content.scale_y = 0.9

            col_content.separator(factor = 1)
            col_content.label(text="NOTE: - Asset Packs are optional to fund developpment.")
            col_content.label(text="            - You can enjoy the same way all BagaPie tools with your own assets, there is no difference.")

            debug(txt="#################################################################")
            debug(txt="                   ASSETS INSTALLATION DEBUG")
            debug(txt="                           - START -")
            debug(txt="LIBRARY LOCATION:          "+self.library_location)
            bagapie_pref = Get_addon_pref()
            if bagapie_pref.debug == True:
                for lib in bpy.context.preferences.filepaths.asset_libraries:
                    if lib.name == "BagaPie Assets":
                        print("Found ‘BagaPie Assets’ at:", lib.path)
                        break
                else:
                    print("No ‘BagaPie Assets’ library found.")
                print("_")

            try:
                color_condition_files = {
                    'Bagapieassets_database_V1.blend': ['Bagapieassets_database_V1.blend'],
                    'Bagapieassets_database_V2.blend': ['Bagapieassets_database_V2.blend', 'Bagapieassets_database_V6.blend'],
                    'Bagapieassets_database_V3.blend': ['Bagapieassets_database_V3.blend', 'Bagapieassets_database_V4.blend'],
                    'Bagapieassets_database_V4.blend': ['Bagapieassets_database_V5.blend'],
                    'Bagapieassets_database_V5.blend': ['Bagapieassets_database_V7.blend'],
                    'Bagapieassets_database_V6.blend': ['Bagapieassets_database_V8.blend'],
                    'Bagapieassets_database_V7.blend': ['Bagapieassets_database_V9.blend'],
                    'Bagapieassets_database_V8.blend': ['Bagapieassets_database_V10.blend'],
                    'Bagapieassets_database_V9.blend': ['Bagapieassets_database_V11.blend'],
                    'Bagapieassets_database_V10.blend': ['Bagapieassets_database_V12.blend']
                }
                color_condition_files_all = {
                    'Bagapieassets_database_V1.blend': ['Bagapieassets_database_V1.blend'],
                    'Bagapieassets_database_V2.blend': ['Bagapieassets_database_V2.blend', 'Bagapieassets_database_V6.blend'],
                    'Bagapieassets_database_V3.blend': ['Bagapieassets_database_V3.blend', 'Bagapieassets_database_V4.blend'],
                    'Bagapieassets_database_V4.blend': ['Bagapieassets_database_V5.blend'],
                    'Bagapieassets_database_V5.blend': ['Bagapieassets_database_V7.blend'],
                    'Bagapieassets_database_V6.blend': ['Bagapieassets_database_V8.blend'],
                    'Bagapieassets_database_V7.blend': ['Bagapieassets_database_V9.blend'],
                    'Bagapieassets_database_V8.blend': ['Bagapieassets_database_V10.blend'],
                    'Bagapieassets_database_V9.blend': ['Bagapieassets_database_V11.blend'],
                    'Bagapieassets_database_V10.blend': ['Bagapieassets_database_V12.blend'],
                    'Bagapieassets_database_essential.blend': ['Bagapieassets_database_essential.blend'],
                    'Bagapieassets_Lite_database_V1.blend': ['Bagapieassets_Lite_database_V1.blend'],
                    'Bagapieassets_Lite_database_V2.blend': ['Bagapieassets_Lite_database_V2.blend'],
                    'Bagapieassets_Lite_database_V3.blend': ['Bagapieassets_Lite_database_V3.blend'],
                    'Bagapieassets_Lite_database_V4.blend': ['Bagapieassets_Lite_database_V4.blend']
                }

                filenames = {
                    'Bagapieassets_database_essential.blend': ('BagaPie Assets Essential :', '     Essential Vol 1'),
                    'Bagapieassets_Lite_database_V1.blend': ('BagaPie Assets Lite :', '     Lite Vol 1'),
                    'Bagapieassets_Lite_database_V2.blend': ('BagaPie Assets Lite :', '     Lite Vol 2'),
                    'Bagapieassets_Lite_database_V3.blend': ('BagaPie Assets Lite :', '     Lite Vol 3'),
                    'Bagapieassets_Lite_database_V4.blend': ('BagaPie Assets Lite :', '     Lite Vol 4')
                }

                # ICON NAME
                # WHY HELL DID YOU CHANGE THAT ???
                if bpy.app.version >= (4, 4, 0):
                    red_icon = "STRIP_COLOR_01"
                    green_icon = "STRIP_COLOR_04"
                else:
                    red_icon = "SEQUENCE_COLOR_01"
                    green_icon = "SEQUENCE_COLOR_04"

                # Add the conditions for full volumes
                filenames.update({filename: ('BagaPie Assets Full :', f'     Vol {i}') for filename, i in zip(color_condition_files, range(1, 21))})
                
                # Initialize the icons with a default color
                icons = {key: red_icon for key in filenames}

                # Keep track of headers already printed
                printed_headers = set()

                # List the files present in the directory
                present_files = set(os.listdir(self.library_location))
                
                debug(txt="Present_files: "+ str(present_files))
                debug(txt="")

                for filename, condition_files in color_condition_files_all.items():
                    # Check if all condition files are present for the given volume
                    if all(cond_file in present_files for cond_file in condition_files):
                        icons[filename] = green_icon

                    bagapie_pref = Get_addon_pref()
                    if bagapie_pref.debug == True:
                        missing = [f for f in condition_files if f not in present_files]
                        print(f"DEBUG ▶ {filename}: condition={condition_files}, missing={missing}")
                        if not missing:
                            icons[filename] = green_icon
                        print(f"       → icon[{filename}] = {icons[filename]}")

                display_lite = False
                display_essential = False
                display_full = False

                for filename, (header, label) in filenames.items():
                    if label.startswith("     Lite") and icons[filename] == green_icon:
                        display_lite = True
                    if label.startswith("     Essential") and icons[filename] == green_icon:
                        display_essential = True
                    if label.startswith("     Vol") and icons[filename] == green_icon:
                        display_full = True


                if display_lite or display_essential or display_full:

                    col_content.label(text="Packs installed: (Green = Installed)")
                    col_content.separator(factor = 1)

                for filename, (header, label) in filenames.items():
                    if header not in printed_headers:
                        if header == "BagaPie Assets Essential :" and display_essential:
                            col_content.label(text=header)
                            printed_headers.add(header)
                        if header == "BagaPie Assets Lite :" and display_lite:
                            col_content.label(text=header)
                            printed_headers.add(header)
                        if header == "BagaPie Assets Full :" and display_full:
                            col_content.label(text=header)
                            printed_headers.add(header)

                    if label.startswith("     Lite Vol") and display_lite:
                        col_content.label(text=label, icon=icons[filename])
                    elif label.startswith("     Essential Vol") and display_essential:
                        col_content.label(text=label, icon=icons[filename])
                    elif label.startswith("     Vol") and display_full:
                        col_content.label(text=label, icon=icons[filename])

            except Exception as e:
                print("ERROR in asset display:", e)
                if self.library_location != "NONE" or os.path.exists(self.library_location):
                    bow_not_found = col_content.box()
                    bow_not_found.label(text="No files found")
                    bow_not_found.label(text="If you've recently updated BagaPie and have previously installed asset packs,")
                    bow_not_found.label(text="update your library's asset file location :")
                    bow_not_found.operator('bagapie.setpacklocation', icon = "COPYDOWN", text = 'Set library location')

            try:
                files = os.listdir(self.library_location)
                col_content.separator(factor = 3)

                col_location = box.column(align=True)
                col_location.scale_y = 1.2
                col_location.label(text="Assets Current Location :", icon = "INFO")
                col_location.label(text=pref.library_location)

                row_location = col_location.row(align=True)
                row_location.operator('bagapie.setpacklocation', icon = "COPYDOWN", text = 'Edit Library Location')
                row_location.operator("bagapie.openlibfolder", text="", icon = 'FILEBROWSER')

                install_tips = any(file.endswith(".blend") for file in files)
            except:
                col_location = box.column(align=True)
                install_tips = True
                
            if install_tips:
                if self.library_location != "NONE" or os.path.exists(self.library_location):
                    box_alert = col.box()
                    box_alert.scale_y = 0.4
                    box_alert.alert = True
                    box_alert.label(text="Pack installation can take several seconds, please be patient.", icon = "INFO")
                    box_alert.label(text="They have to be installed one by one.")
            
            debug(txt="                            - END -")
            debug(txt="#################################################################")

        ###################################################################################
        # SCATTER PREFERENCES
        ###################################################################################
        box = layout.box()
        box.prop(self, 'scatter_preferences', text = "Scattering Preferences", emboss = False, icon = "OUTLINER_OB_CURVES")
        if self.scatter_preferences:

            box.label(text="Scatter from BagaPie V5.0 and previous versions aren't compatible with this version.", icon = "INFO")
            box.prop(pref, 'use_default_proxy', text="Enable proxy by default.")
            if pref.use_default_proxy:
                box.prop(pref, 'polycount_for_proxy', text="Minimum polycount for proxy.")
            box.prop(pref, 'keep_unlinked_assets_in_scene', text = "Keep assets in scene")
                
            box.prop(pref, 'security_features', text="Use security features for scattering :", icon = "LOCKED")
            if pref.security_features:
                row = box.row()
                col = row.column()
                col.separator(factor = 2)

                col = row.column()
                col.prop(pref, 'maximum_polycount', text="Maximum polycount to trigger security features.")
                col.label(text="(Total of average polycount instances * instances count)")
                col.separator(factor = 1)
                col.prop(pref, 'default_percent_display', text="Percentage of instances displayed in the viewport")
                col.prop(pref, 'apply_scale_default', text="Proposes to apply the scale of the target if it is not at 1,1,1.")
                col.prop(pref, 'use_camera_culling', text="Use Camera Culling if available.")

        ###################################################################################
        # ABOUT BAGAPIE
        ###################################################################################
        box = layout.box()
        box.prop(self, 'how_it_works', text = "What's new in V11 ?", emboss = False, icon = "QUESTION")
        if self.how_it_works:
            box = box.column(align=True)
            box.scale_y = 0.8
            box.label(text="     - Node to Panel is now fully recursive :")
            box.label(text="          > Create boxes in boxes, in rows, in boxes, etc.")
            box.label(text="          > Cleaner, more flexible modifier UI.")
            box.separator(factor = 2)

            box.label(text="     - New Scatter System integration with GeoPack :")
            box.label(text="          > Save complete scatter setups as presets,")
            box.label(text="          > Export and share them as .geopack files,")
            box.label(text="          > Assets are packed automatically,")
            box.label(text="          > Auto-generate a preview based on the current view.")
            box.separator(factor = 2)

            box.label(text="     - New Asset Browser Panel :")
            box.label(text="          > Display all scatter layers,")
            box.label(text="          > One-click scatter from selected asset,")
            box.label(text="          > Per asset controls : Proxy, Bounds, Select, Remove,")
            box.label(text="          > Rename layers easily.")
            box.separator(factor = 2)

            box.label(text="     - Group system has been fully rewritten :")
            box.label(text="          > Group inside groups,")
            box.label(text="          > Selection to [Group to] instance tool,")
            box.label(text="          > Bounding box is dynamic,")
            box.label(text="          > Turn group to instances or edit in one click,")
            box.label(text="          > Ctrl+G to create group, double-click to edit (beta).")
            box.separator(factor = 2)

            box.label(text="     - 20 New Tools added :")
            box.label(text="          > Face to Grid / Paving / Perforated Grid / Plank")
            box.label(text="          > Window Modern / Classic, Door Simple / Double")
            box.label(text="          > Cable Creator, Bool Through, Tessellate, Insert Circle")
            box.label(text="          > Array Along Shape, Bolt Corner")
            box.separator(factor = 2)

            box.label(text="     - Scatter Improvements :")
            box.label(text="          > Preview Generator improved,")
            box.label(text="          > Snap Assets uses object offset, Bevel Weight, Vertex Crease")
            box.label(text="          > UI fixes in Scatter Paint, simplified Scatter panel.")
            box.separator(factor = 2)

            box.label(text="     - Many bug fixes, UI improvements and minor improvments...")
            box.separator(factor = 2)

            col = box.column(align=True)
            col.scale_y = 2
            col.operator("wm.url_open", text="Full Changelog", icon = 'BLENDER').url = "https://extensions.blender.org/add-ons/bagapie/versions/"

        ###################################################################################
        # PIE MENU TOOLS
        ###################################################################################
        box = layout.box()
        box.prop(self, 'pie_custom', text = "Pie Menu Tools", emboss = False, icon = "MODIFIER")
        if self.pie_custom:
            
            def add_line(box, prop, text, icon, description1, description2):
                row = box.row(align=True)
                row = row.split(factor=0.3)
                row.prop(self, prop, text = text, icon=icon if getattr(self, prop) else "HIDE_ON")
                row = row.split(factor=0.5)
                row.label(text=description1)
                row.label(text=description2)

            box = box.column(align=True)
            box.scale_y = 1.2
            row = box.row(align=True)
            row = row.split(factor=0.3)
            row.label(text="Tool Visibility :")
            row = row.split(factor=0.5)
            row.label(text="What should be selected :")
            row.label(text="Selection type :")
            box.separator(factor = 2)

        # OBJECT MODE
            box.label(text="Pie Menu Object Mode :", icon ='OBJECT_DATAMODE')
            box.separator(factor = 1)

            # DEFORMATION
            box.label(text="Deformation :", icon ='MOD_DISPLACE')
            add_line(box, 'displace', "Displace", "HIDE_OFF", "One object", "Mesh")
            add_line(box, 'instancesdisplace', "Instances Displace", "HIDE_OFF", "One object with instances on it", "Mesh or curve")
            add_line(box, 'deform', "Deform", "HIDE_OFF", "One object", "Mesh or curve")
            box.separator(factor = 1)

            # ARRAY
            box.label(text="Array :", icon = "MOD_ARRAY")
            add_line(box, 'curve', "Curve", "HIDE_OFF", "Multiple objects & Curve as active object", "Mesh and Curve")
            add_line(box, 'autoarrayoncurve', "Curve Deform", "HIDE_OFF", "Two objects", "Mesh and curve")
            add_line(box, 'draw_curve', "Draw", "HIDE_OFF", "One objects", "Mesh")
            add_line(box, 'arrayalongshape', "Array Along Shape", "HIDE_OFF", "Two objects", "Mesh")
            box.separator(factor = 1)

            # MANAGE
            box.label(text="Manage :", icon = "PACKAGE")
            add_line(box, 'proxy', "Proxy", "HIDE_OFF", "One or multiple object(s)", "Mesh")
            add_line(box, 'saveasasset', "Save as Asset", "HIDE_OFF", "One object", "Mesh or curve")
            add_line(box, 'savematerial', "Save Material", "HIDE_OFF", "One object", "Mesh or curve")
            add_line(box, 'group', "Group", "HIDE_OFF", "One or multiple object(s)", "Mesh or curve")
            box.separator(factor = 1)

            # SCATTERING
            box.label(text="Scattering :", icon = "OUTLINER_OB_CURVES")
            add_line(box, 'scatter', "Scatter", "HIDE_OFF", "Multiple object(s) and target", "Mesh")
            add_line(box, 'scatterpaint', "Scatter Paint", "HIDE_OFF", "Multiple object(s) and target", "Mesh")
            add_line(box, 'pointsnapinstance', "Snap Asset", "HIDE_OFF", "Multiple object(s) and target", "Mesh")
            add_line(box, 'ivy', "Ivy", "HIDE_OFF", "One or multiple object(s)", "Mesh")
            box.separator(factor = 1)

            # EFFECTOR
            box.label(text="Effector :", icon = "PARTICLES")
            add_line(box, 'pointeffector', "Point Effector", "HIDE_OFF", "One or multiple object(s) and target", "Mesh")
            add_line(box, 'camculling', "CamCulling", "HIDE_OFF", "Camera and target and a scatter layer", "Camera or empty")
            box.separator(factor = 1)

            # ARCHITECTURE
            box.label(text="Architecture :", icon = "HOME")
            add_line(box, 'wall', "Wall", "HIDE_OFF", "One object", "Mesh or curve")
            add_line(box, 'wallbrick', "Wall Brick", "HIDE_OFF", "One object", "Mesh or curve")
            add_line(box, 'window', "Window (Old)", "HIDE_OFF", "One object", "Mesh")
            add_line(box, 'pipes', "Pipes", "HIDE_OFF", "One or multiple object(s)", "Mesh")
            add_line(box, 'beamwire', "Beam Wire", "HIDE_OFF", "Nothing", "No selection")
            add_line(box, 'beam', "Beam", "HIDE_OFF", "Nothing", "No selection")
            add_line(box, 'linearstair', "Stair Linear", "HIDE_OFF", "Nothing", "No selection")
            add_line(box, 'stairspiral', "Stair Spiral", "HIDE_OFF", "Nothing", "No selection")
            add_line(box, 'floor', "Floor", "HIDE_OFF", "Nothing", "No selection")
            add_line(box, 'handrail', "Handrail", "HIDE_OFF", "One object or Nothing", "Curve")
            add_line(box, 'column', "Column", "HIDE_OFF", "Nothing", "No selection")
            add_line(box, 'cable', "Cable", "HIDE_OFF", "One or multiple object(s)", "Mesh")
            add_line(box, 'tiles', "Tiles", "HIDE_OFF", "Nothing", "No selection")
            add_line(box, 'fence', "Fence", "HIDE_OFF", "One object or Nothing", "Curve")
            add_line(box, 'siding', "Siding", "HIDE_OFF", "One object", "Mesh")
            add_line(box, 'paving', "Paving", "HIDE_OFF", "One objects", "Mesh")
            add_line(box, 'grid', "Grid", "HIDE_OFF", "One objects", "Mesh")
            add_line(box, 'perforatedgrid', "Perforated Grid", "HIDE_OFF", "One objects", "Mesh")
            add_line(box, 'plank', "Plank", "HIDE_OFF", "One objects", "Mesh")
            box.separator(factor = 3)

        # EDIT MODE
            box.label(text="Pie Menu Edit Mode :", icon ='EDITMODE_HLT')
            box.separator(factor = 1.5)

            # ARCHITECTURE
            box.label(text="Architecture :", icon = "HOME")
            add_line(box, 'window_modern', "Window Modern", "HIDE_OFF", "Mesh Edit Mode", "Face(s)")
            add_line(box, 'window_classic', "Window Classic", "HIDE_OFF", "Mesh Edit Mode", "Face(s)")
            add_line(box, 'door_simple', "Door Simple", "HIDE_OFF", "Mesh Edit Mode", "Face(s)")
            add_line(box, 'door_double', "Door Double", "HIDE_OFF", "Mesh Edit Mode", "Face(s)")
            add_line(box, 'cable_creator', "Cable Creator", "HIDE_OFF", "Mesh Edit Mode", "Edge(s)")

            # GENERATE
            box.label(text="Generate :", icon = "RESTRICT_SELECT_OFF")
            add_line(box, 'face_to_grid', "Face to Grid", "HIDE_OFF", "Mesh Edit Mode", "Face(s)")
            add_line(box, 'face_to_paving', "Face to Paving", "HIDE_OFF", "Mesh Edit Mode", "Face(s)")
            add_line(box, 'face_to_perforated_grid', "Face to Perforated Grid", "HIDE_OFF", "Mesh Edit Mode", "Face(s)")
            add_line(box, 'face_to_plank', "Face to Plank", "HIDE_OFF", "Mesh Edit Mode", "Face(s)")

            # EDIT MESH
            box.label(text="Edit Mesh :", icon = "EDGESEL")
            add_line(box, 'bool_through', "Bool Through", "HIDE_OFF", "Mesh Edit Mode", "Face(s)")
            add_line(box, 'tessellate', "Tessellate", "HIDE_OFF", "Mesh Edit Mode", "Face(s)")
            add_line(box, 'insert_circle', "Insert Circle", "HIDE_OFF", "Mesh Edit Mode", "Face(s)")

            # ARRAY
            box.label(text="Array :", icon = "MOD_ARRAY")
            add_line(box, 'array_along_shape', "Array Along Shape", "HIDE_OFF", "Mesh Edit Mode", "Face/Edge(s)")
            add_line(box, 'bolt_corner', "Bolt Corner", "HIDE_OFF", "Mesh Edit Mode", "Face(s)")

        ###################################################################################
        # NODES TO PANEL
        ###################################################################################
        box = layout.box()
        box.prop(self, 'nodes_to_addon', text = "Nodes to Panel", emboss = False, icon = "NODETREE")
        if self.nodes_to_addon:
            box.label(text="BagaPie can turn your geometry nodes modifier and shader nodegroup into a user-freindly UI.")
            row = box.row(align=True)
            row.scale_y = 1.5
            row.operator("wm.url_open", text="Documentation", icon = 'HELP').url = "https://www.f12studio.fr/bagapiev6"
            row.operator("wm.url_open", text="Node To Panel Quick Demo", icon = 'PLAY').url = "https://youtu.be/LWdByXpfTLY?t=20"
            col = box.column()
            col.scale_y = 0.7
            col.label(text="By adding prefixes to your input names, Bagapie will be able to interpret them and")
            col.label(text="generate an interface in the BagaPie panel.")
            col.label(text="Add 'BP_' as prefix to the node tree name/description/label for BagaPie to recognize it.")
            box = box.column(align=True)
            box.separator(factor = 2)
            box.scale_y = 0.8
            box.label(text="Prefix list :")
            box.separator(factor = 1)
            box.label(text="BP_  =    You must add this previx to your nodetree name")
            box.separator(factor = 2)
            box.label(text="B_   =    Create a new box")
            box.label(text="B    =    Add in the previous box")
            box.label(text="R_   =    Create a new row")
            box.label(text="R    =    Add in the previous row")
            box.label(text="2_   =    Scale button/input")
            box.separator(factor = 2)
            box.label(text="L    =    Displayed as Label")
            box.label(text="V    =    Displayed as Value (any types)")
            box.label(text="P    =    Displayed as a Button (must be a bool)")
            box.label(text="P2   =    Displayed as a Button with identifier 2 (must be between 0 - 9). Can control other values display.")
            box.label(text="S    =    Displayed as Separator")
            box.label(text="_    =    End of prefix, then add the name of your Value/Label/Button")
            box.label(text="URL  =    External link (for Tutorials, Documentation, ...). Must be a String input. Add URL in input default value.")
            
            box.separator(factor = 4)
            box.label(text="Exemples :")

            box.separator(factor = 4)
            ex_box = box.box()
            row = ex_box.row(align=True)
            col_ex_name = row.column(align=True)
            col_inp_name = row.column(align=True)
            col_visual = row.column(align=True)
            col_ex_name.label(text="What's created :")
            col_inp_name.label(text="Input Name :")
            col_visual.label(text="How it looks in the panel :")
            col_visual.separator(factor = 1)

            ex_box = box.box()
            ex_box.separator(factor = 0.5)
            row = ex_box.row(align=True)
            col_ex_name = row.column(align=True)
            col_inp_name = row.column(align=True)
            col_visual = row.column(align=True)
            col_ex_name.label(text="New Box with label")
            col_inp_name.label(text="B_L_MyLabelName")
            col_visual.box().label(text="MyLabelName")
            ex_box.separator(factor = 0.5)

            ex_box = box.box()
            ex_box.separator(factor = 0.5)
            row = ex_box.row(align=True)
            col_ex_name = row.column(align=True)
            col_inp_name = row.column(align=True)
            col_visual = row.column(align=True)
            col_visual.scale_y = 1.5
            col_ex_name.label(text="Switch Button")
            col_inp_name.label(text="P_MyButtonName")
            tips = col_visual.operator("bagapie.tooltips", text="MyButtonName", depress = False)
            tips.message = 'Switch input value (Must be boolean)'
            ex_box.separator(factor = 0.5)

            ex_box = box.box()
            ex_box.separator(factor = 0.5)
            row = ex_box.row(align=True)
            col_ex_name = row.column(align=True)
            col_inp_name = row.column(align=True)
            col_visual = row.column(align=True)
            col_visual.scale_y = 1.5
            col_visual.scale_x = 0.5
            col_ex_name.label(text="Display values on a row")
            col_inp_name.label(text="R_V_MyValueName A")
            col_inp_name.label(text="RV_MyValueName B")
            row_val = col_visual.row(align=True)
            row_val.prop(self, 'ntp_float_a', text = "MyValueName A",)
            row_val.prop(self, 'ntp_float_b', text = "MyValueName B",)
            ex_box.separator(factor = 0.5)

            ex_box = box.box()
            ex_box.separator(factor = 0.5)
            row = ex_box.row(align=True)
            col_ex_name = row.column(align=True)
            col_inp_name = row.column(align=True)
            col_visual = row.column(align=True)
            col_visual.scale_y = 1.5
            col_ex_name.label(text="Button control values display")
            col_inp_name.label(text="P1_Hit me !")
            col_inp_name.label(text="1V_MyValueName_A")
            col_inp_name.label(text="1V_MyValueName_B")
            col_visual.prop(self, 'ntp_bool_a', text = "Hit me !", toggle = True)
            if self.ntp_bool_a:
                col_visual.prop(self, 'ntp_float_c', text = "MyValueName A",)
                col_visual.prop(self, 'ntp_float_d', text = "MyValueName B",)
            ex_box.separator(factor = 0.5)

        ###################################################################################
        # HELP SUPPORT DOC
        ###################################################################################
        box = layout.box()
        box.prop(self, 'help_support', text = "Help & Documentation", emboss = False, icon = "COMMUNITY")
        if self.help_support:
            box = box.column(align=True)
            box.separator(factor = 2)
            box.scale_y = 1.5
            box.operator("wm.url_open", text="BagaPie Documentation", icon = 'TEXT').url = "https://www.f12studio.fr/bagapiev6"
            box.operator("wm.url_open", text="Help - Support - Bug Report on Discord", icon = 'COMMUNITY').url = "https://discord.gg/YtagqdPW6G"
            box.operator("wm.url_open", text="Youtube Tutorials", icon = 'PLAY').url = "https://www.youtube.com/playlist?list=PLSVXpfzibQbh_qjzCP2buB2rK1lQtkQvu"

        ###################################################################################
        # COMMON ISSUES
        ###################################################################################
        box = layout.box()
        box.prop(self, 'issues', text = "Common Issues !", emboss = False, icon = "ERROR")
        if self.issues:
            col = box.column(align=True)
            col.label(text=" 1| When I apply my modifier, everything disappears.")
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text="         You must apply the BagaPie modifiers via the addon's panel. (N key)")
            col.label(text="         On top of the BagaPie panel press the apply Button : ✓")
            col.label(text="         Keep in mind that modifiers have an order, apply the ones before your modifier first.")
            box.separator(factor = 2)
            
            col = box.column(align=True)
            col.label(text="2| My Scattering/Ivy isn't stabble during my animation.")
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text="         The scattering/ivy is based on the surface (area) of the object to calculate the position of the instances.")
            col.label(text="         As your object is animated, the surface (area) may be modified/distorted.")
            col.label(text="         There are currently no solutions for this issue in BagaPie.")
            box.separator(factor = 2)
            
            col = box.column(align=True)
            col.label(text="3| My Scattering/Ivy is different when rendered.")
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text="         The scattering/ivy is based on the surface (area) of the object to calculate the position of the instances.")
            col.label(text="         Check that your surface does not change at the time of rendering (Ex: Modify Subdivision).")
            col.label(text="         OR")
            col.label(text="         It is possible that the number of particles displayed in the viewport and in the rendering is different.")
            col.label(text="         Check the % Displayed parameter.")
            box.separator(factor = 2)
            
            col = box.column(align=True)
            col.label(text="4| The Pie Menu is not working.")
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text="         Check that you are in Object Mode (J key).")
            col.label(text="         Or in Edit Mode for the pie menu tools (D key).")
            col.label(text="         Check that the version of BagaPie is compatible with your Blender version.")
            box.separator(factor = 2)
            
            col = box.column(align=True)
            col.label(text="5| 'Save in GeoPack' is grayed out ?")
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text="         Go to the GeoPack tab and set its location if prompted.")
            col.label(text="         Select your object (must be a Curve or Mesh).")
            col.label(text="         In the modifier stack, select the Geometry Nodes modifier to save (a blue outline will appear).")
            box.separator(factor=2)

            col = box.column(align=True)
            col.label(text="Still get an issue ?")
            col.operator("wm.url_open", text="Contact us on Discord", icon = 'COMMUNITY').url = "https://discord.gg/YtagqdPW6G"


addon_keymaps = []
classes = [BAGAPIE_Geopack_ModifierItem,BAGAPIE_Geopack_Item,bagapie_Preferences, BagapieSettings]

for script in [
                "bagapie_ui",
                "bagapie_ui_op",
                "bagapie_boolean_op",
                "bagapie_wall_op",
                "bagapie_array_op",
                "bagapie_scatter_op",
                "bagapie_displace_op",
                "bagapie_curvearray_op",
                "bagapie_window_op",
                "bagapie_group_op",
                "bagapie_instance_op",
                "bagapie_pointeffector_op",
                "bagapie_proxy_op",
                "bagapie_wallbrick_op",
                "bagapie_ivy_op",
                "bagapie_pointsnapinstance",
                "bagapie_instancesdisplace_op",
                "bagapie_saveasset_op",
                "bagapie_pipes_op",
                "bagapie_beamwire_op",
                "bagapie_stairlinear_op",
                "bagapie_stairspiral_op",
                "bagapie_beam_op",
                "bagapie_floor_op",
                "bagapie_handrail_op",
                "bagapie_column_op",
                "bagapie_twist_op",
                "bagapie_camera_op",
                "bagapie_cable_op",
                "bagapie_fence_op",
                "bagapie_siding_op",
                "bagapie_tiles_op",
                "bagapie_install_package",
                "bagapie_assetbrowser_import_op",
                "bagapie_geopack_create",
                "bagapie_geopack_ui",
                "bagapie_geopack_assets",
                "bagapie_geopack_icon",
                "bagapie_tools_ui",
                "bagapie_window_v2_op",
                "bagapie_door_op",
                "bagapie_plank_op",
                "bagapie_grid_op",
                "bagapie_paving_op",
                "bagapie_perforated_grid_op",
                "bagapie_array_shape_op",
                "bagapie_geopack_edit"
            ]:
    exec(f"from . import {script}")
    exec(f"for cls in {script}.classes: classes.append(cls)")

def check_if_restarted():
    # The temporary file ("bagapie_restart_flag.txt") is used to detect whether Blender 
    # has been restarted after executing a specific operator that requires a restart. This mechanism 
    # addresses an issue where certain assets (Node Tree) in the Asset Browser are not immediately 
    # available (via geometry.execute_node_group) after their creation without restarting Blender.
    #
    # How it works:
    # - When bagapie.parametricpresets is executed, a file is created to signal that a restart is required.
    # - Up to the next startup, the addon checks for the existence of this file to confirm the restart.
    # - Once detected, the file is deleted here to prevent conflicts or false positives.
    #
    # also see : bagapie_tools_ui > BAGAPIE_MT_pie_menu_tools

    TEMP_FILE = os.path.join(bpy.app.tempdir, "bagapie_restart_flag.txt")
    if os.path.exists(TEMP_FILE):
        print("Blender has restarted after operator execution.")
        os.remove(TEMP_FILE)
        return True
    return False

def register():
    check_if_restarted()

    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except:
            print(f"Find a way to fix the double resitering of {cls}")
    
    ###################################################################################
    # ADD SHORTCUTS
    ###################################################################################
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        # PIE MENU OBJECT MODE
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new("wm.call_menu_pie", type='J', value='PRESS')
        kmi.properties.name = "BAGAPIE_MT_pie_menu"
        addon_keymaps.append((km,kmi))
        
        # PIE MENU GEOPACK
        km_gp = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi_gp = km_gp.keymap_items.new("wm.call_menu_pie", type='V', value='PRESS')
        kmi_gp.properties.name = "BAGAPIE_MT_pie_menu_geopack"
        addon_keymaps.append((km_gp,kmi_gp))

        # Duplicate Group
        dupli = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        dupli_id = km.keymap_items.new("bagapie.duplicategroup", type='J', alt=True, value='PRESS')
        addon_keymaps.append((dupli,dupli_id))

        # Duplicate Group linked
        dupli_link = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        dupli_id_link = km.keymap_items.new("bagapie.duplicatelinkedgroup", type='N', alt=True, value='PRESS')
        addon_keymaps.append((dupli_link,dupli_id_link))

        # CREATE GROUP
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new("bagapie.group", type='G', ctrl=True, value='PRESS')
        addon_keymaps.append((km, kmi))

        # PIE MENU TOOL
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new("wm.call_menu_pie", type='D', value='PRESS')
        kmi.properties.name = "BAGAPIE_MT_pie_menu_tools"
        addon_keymaps.append((km,kmi))

        # PANEL POPUP        
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new("wm.call_panel", type='J', alt=True, ctrl=True, value='PRESS')
        kmi.properties.name = "BAGAPIE_PT_modifier_panel"
        addon_keymaps.append((km,kmi))

    bpy.types.Scene.bagapieValue = bpy.props.StringProperty(name="My List", default="none")
    bpy.types.Object.bagapieList = bpy.props.CollectionProperty(type=BagapieSettings)
    bpy.types.Object.bagapieIndex = bpy.props.IntProperty(name="Index", default=0)

    prefs = Get_addon_pref()
    prefs.ScanGeoPacks(bpy.context)

    bagapie_geopack_icon.import_icons()

    bpy.types.NODE_MT_node_tree_interface_context_menu.append(group_prefix_menu)

    check_if_restarted()


def unregister():
    global addon_keymaps

    for km,kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bagapie_geopack_icon.unload_icons()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.NODE_MT_node_tree_interface_context_menu.remove(group_prefix_menu)
         
if __name__ == "__main__":
    register()
