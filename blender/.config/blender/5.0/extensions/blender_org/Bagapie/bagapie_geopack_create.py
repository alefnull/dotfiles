from math import floor
import bpy
import json
import math
import shutil
import os
import ntpath
import inspect
import tempfile
from pathlib import Path
import time
from bpy.types import Operator, Menu
from .utils import sanitize_filename
import re
from .bagapie_assetbrowser_import_op import find_areas, find_window
from . import bagapie_geopack_icon
from .utils import Get_addon_pref, Warning, debug
from .bagapie_geopack_icon import import_icons

previews = bpy.utils.previews.new()

class BAGAPIE_Geopack_ModifierItem(bpy.types.PropertyGroup):
    pieVisibility:bpy.props.BoolProperty(name="pieVisibility",description="Toggle this Modifier visibility in the Pie menu",default=True)
    displayOptions: bpy.props.BoolProperty(name="Enabled",description="Toggle this Modifier options",default=False)
    name:bpy.props.StringProperty(name="name",default="")
    identifier:bpy.props.StringProperty(name="identifier",default="")
    description:bpy.props.StringProperty(name="description",default="")
    path:bpy.props.StringProperty(name="path",default="")
    config:bpy.props.StringProperty(name="config",default="")

    def apply(self,context):
        pass

class BAGAPIE_Geopack_Item(bpy.types.PropertyGroup):
    pieVisibility:bpy.props.BoolProperty(name="pieVisibility",description="Toggle this GeoPack visibility in the Pie menu",default=True) # type: ignore
    displayOptions: bpy.props.BoolProperty(name="Enabled",description="Toggle this GeoPack options",default=False) # type: ignore
    displayInfo: bpy.props.BoolProperty(name="Enabled",description="Toggle this GeoPack Info section",default=False) # type: ignore
    displayModifier: bpy.props.BoolProperty(name="Enabled",description="Toggle this GeoPack Modifier section",default=False) # type: ignore
    displayAssets: bpy.props.BoolProperty(name="Enabled",description="Toggle this GeoPack Assets section",default=False) # type: ignore
    name:bpy.props.StringProperty(name="name",default="") # type: ignore
    identifier:bpy.props.StringProperty(name="identifier",default="") # type: ignore
    description:bpy.props.StringProperty(name="description",default="") # type: ignore
    path:bpy.props.StringProperty(name="path",default="") # type: ignore
    config:bpy.props.StringProperty(name="config",default="") # type: ignore
    scanModifiers: bpy.props.BoolProperty(name="scanModifiers",description="",default=False) # type: ignore

    modifiers_list: bpy.props.CollectionProperty(
        name="Modifiers List",
        type=BAGAPIE_Geopack_ModifierItem
    ) # type: ignore

    def getModifier(self,identifier):
        for mod in self.modifiers_list:
            if mod.identifier == identifier:
                return mod
        return None

    def scan_modifiers(self):
        modifier_files = [os.path.join(dirpath, filename)
            for dirpath, _, filenames in os.walk(self.path)
            for filename in filenames
            if filename.endswith('.json')]

        # mémorisation de la visibilité dans le pie menu
        mod_count = len(self.modifiers_list)

        pieVis = None
        originalMods = None
        if mod_count > 0:
            originalMods = [mod.identifier for mod in self.modifiers_list]
            pieVis = [mod.identifier for mod in self.modifiers_list if mod.pieVisibility]

        self.modifiers_list.clear()

        for config in modifier_files:
            with open(config) as f:
                config_str = f.read()

                try:
                    data = json.loads(config_str)

                    new_item = self.modifiers_list.add()
                    new_item.name = data['info']['name']
                    new_item.path = config
                    new_item.identifier = config
                    if mod_count > 0:
                        if new_item.identifier in originalMods:
                            # récupération de la visibilité dans le pie menu si le modifier était affiché précédemment
                            new_item.pieVisibility = new_item.identifier in pieVis

                    new_item.description = data['info']['description']

                    format_version = data['info'].get('format_version')
                    if not format_version:
                        format_version = '1.0.0'

                    if format_version != "1.0.0":
                        # version initiale

                        #version 1.1.0 -> ajout des data des assets
                        data['assets_data'] = []

                        config_str = json.dumps(data)

                    new_item.config = config_str

                    #new_item.jsonData = data #TODO c'est pas conservé !
                except:
                    print("Error loading GeoPack",config)

def update_list(self, context):
    obj = bpy.context.object
    modifier = obj.modifiers.active if obj.modifiers else None
    inputs = modifier.node_group.interface.items_tree
    inputs_list = []
    for input in inputs:
        if input.bl_socket_idname == 'NodeSocketCollection':
            inputs_list.append((
                input.identifier,
                input.name +' ('+ input.identifier +')',
                ""
            ))
    return inputs_list

def update_object_list(self, context):
    obj = bpy.context.object
    modifier = obj.modifiers.active if obj.modifiers else None
    inputs = modifier.node_group.interface.items_tree
    inputs_list = []
    for input in inputs:
        if input.bl_socket_idname == 'NodeSocketObject':
            inputs_list.append((
                input.identifier,
                input.name +' ('+ input.identifier +')',
                ""
            ))
    return inputs_list

def update_field_list(self, context):
    obj = bpy.context.object
    modifier = obj.modifiers.active if obj.modifiers else None
    inputs = modifier.node_group.interface.items_tree
    inputs_list = []
    value = ["NodeSocketBool","NodeSocketString","NodeSocketVector","NodeSocketInt","NodeSocketFloat","NodeSocketColor","NodeSocketRotation"]
    for input in inputs:
        if input.bl_socket_idname in value:
            inputs_list.append((
                input.identifier,
                input.name +' ('+ input.identifier +')',
                ""
            ))
    return inputs_list

def get_active_geometry_node():
    """Returns the currently active geometry node in Blender."""
    node = None
    for area in bpy.context.screen.areas:
        if area.type == 'NODE_EDITOR':
            node_space = area.spaces.active
            if node_space.tree_type == 'GeometryNodeTree':
                node = node_space.node_tree.nodes.active
                break
    return node

def get_active_geometry_node_modifier():
    """Returns the currently active geometry node modifier in Blender."""   
    if not bpy.context.active_object.modifiers:
        return None
    
    if not bpy.context.active_object.modifiers.active:
        return None
    
    if bpy.context.active_object.modifiers.active.type != "NODES":
        return None
    
    return bpy.context.active_object.modifiers.active.node_group
    
class BAGAPIE_OT_geopack_delete(Operator):
    """ Delete a GeoPack """
    bl_idname = "bagapie.geopack_delete"
    bl_label = 'Delete a Geopack'

    packName:bpy.props.StringProperty(name="packName") # type: ignore
    packIdentifier:bpy.props.StringProperty(name="packIdentifier") # type: ignore
    confirm: bpy.props.BoolProperty(name="confirm",default=False) # type: ignore

    def invoke(self, context, event):
        self.confirm = False
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        
        col = layout.column()
        col.label(text=f"Are you sure to delete pack '{self.packName}'?")
        col.label(text="ALL ASSETS linked to this pack will also be LOST.", icon='ERROR')
        col.label(text="This operation cannot be undone.")
        col.label(text="(Make sure you have a copy)")
        
        layout.separator()
        layout.prop(self, "confirm", text="Yes, I'm sure")

    def execute(self, context):
        # 1. Security
        if not self.confirm:
            self.report({'ERROR'}, "Operation cancelled: You must confirm the checkbox.")
            return {'CANCELLED'}

        # 2. Delete
        pref = Get_addon_pref()
        pack = pref.GetGeopack(self.packIdentifier)
        pack_name = pack.name

        # delete folder
        if os.path.isdir(pack.path) and os.path.isfile(os.path.join(pack.path, "geopack.config")):
            shutil.rmtree(pack.path)

        # delete asset library
        prefs = bpy.context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries

        index_to_remove = -1
        for i, lib in enumerate(asset_libraries):
            if lib.name == pack_name:
                index_to_remove = i
                break

        if index_to_remove != -1:
            bpy.ops.preferences.asset_library_remove(index=index_to_remove)
        
        # remove from addon list
        pack_index = pref.geopacks_list.find(pack_name)
        if pack_index != -1:
            pref.geopacks_list.remove(pack_index)

        self.report({'INFO'}, f"GeoPack '{pack_name}' deleted.")
        return {'FINISHED'}

class BAGAPIE_OT_geopack_modifier_delete(Operator):
    """ Delete a GeoPack Modifier """
    bl_idname = "bagapie.geopack_modifier_delete"
    bl_label = 'Delete a Geopack Modifier'

    packIdentifier:bpy.props.StringProperty(name="packIdentifier") # type: ignore
    modifierIdentifier:bpy.props.StringProperty(name="modifierIdentifier") # type: ignore
    modifierName:bpy.props.StringProperty(name="modifierName") # type: ignore

    def execute(self, context):
        pref = Get_addon_pref()
        pack = pref.GetGeopack(self.packIdentifier)
        
        if os.path.isdir(pack.path) and os.path.isfile(os.path.join(pack.path,"geopack.config")):
            mod = pack.getModifier(self.modifierIdentifier)

            if os.path.isfile(mod.path):
                # 1. Delete json
                os.remove(mod.path)
                pre, ext = os.path.splitext(mod.path)

                # 2. Delete blend file
                blend_path = pre + ".blend"
                if os.path.isfile(blend_path):
                    os.remove(blend_path)
                
                # 3. Delete icons
                base_name = os.path.basename(pre)
                name_variations = [base_name, base_name.replace(" ", "_")]
                extensions = [".png", ".jpg", ".jpeg"]
                icon_removed = False
                
                for name in name_variations:
                    for ext in extensions:
                        icon_name = name + ext
                        icon_path = os.path.join(pack.path, icon_name)
                        
                        if os.path.isfile(icon_path):
                            os.remove(icon_path)
                            icon_removed = True
                            break
                    
                    if icon_removed:
                        break

                # 4. Update List
                index = pack.modifiers_list.find(mod.name)
                if index != -1:
                    pack.modifiers_list.remove(index)
        
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)
        
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text=f"Are you sure to delete modifier '{self.modifierName}'?")
        col.label(text="This operation cannot be undone.", icon='ERROR')

class BAGAPIE_OT_geopack_create(Operator):
    """ Create New GeoPack """
    bl_idname = "bagapie.geopack_create"
    bl_label = 'New GeoPack Modifier'

    root_path: bpy.props.StringProperty(default="") # type: ignore
    pack_name: bpy.props.StringProperty(default="NewPack") # type: ignore

    @classmethod
    def poll(cls, context):
        pref = Get_addon_pref()
        for pack_item in pref.geopacks_list:
            if pack_item.name.lower() == pref.geopack_np_name.lower():
                return False
        return True

    def execute(self, context):
        if os.path.isdir(self.root_path):
            self.writePack(context)
        else:
            Warning(
                message=f"Error while creating !{self.pack_name}: invalid destination directory",
                title="New GeoPack",
                icon='INFO',
            )

        return {'FINISHED'}
    
    def writePack(self,context):

        sanitized_name = f'GP_{sanitize_filename(self.pack_name)}'

        path = os.path.join(self.root_path , sanitized_name)

        if not os.path.isdir(path):
            os.mkdir(path)
            Warning(
                message=f"Create path folder: {path}", title="New Pack", icon='INFO'
            )

            pref = Get_addon_pref()

            data = {}
            data['name'] = pref.geopack_np_name
            data['authors'] = pref.geopack_np_authors
            data['description'] = pref.geopack_np_description
            data['version'] = pref.geopack_np_version
            data['url'] = pref.geopack_np_url
            data['blender_version'] = pref.geopack_np_blender_version
            data['license'] = pref.geopack_np_license

            json_file = os.path.join(path,'geopack.config')

            with open(json_file, 'w',encoding='utf-8') as f:
                f.write(json.dumps(data))

            pref.Initialize(context)

            pref.geopack_create_pack = False
        else:
            Warning(message=f"Directory already exists: {path}", title = "NOPE", icon = 'INFO')

def Display_Button(row, mo, pack_item, assetname):
    
    row.context_pointer_set('my_modifier', mo)
    assign_button = row.operator(operator="bagapie.geopack_assign_modifier",text=mo.name.removeprefix("BP_"), icon = 'TRIA_RIGHT')
    assign_button.packName = pack_item.name
    data = json.loads(mo.config)
    if data['usage'].setdefault('asset_browser',False) and data['usage'].get('use_selection'):
        row.operator(operator ="geopack.asset_browser",text=assetname, icon='ASSET_MANAGER').pack_item_pass= pack_item.name
    return None

class BAGAPIE_MT_geopack_select_modifier(Menu):
    """ Create New GeoPack Modifier """
    bl_idname = "BAGAPIE_MT_geopack_select_modifier"
    bl_label = 'Select Modifier'

    first_display = True
    my_pack = None

    def draw(self, context:bpy.types.Context):
        layout = self.layout
        pie = layout.menu_pie()
        pref = Get_addon_pref()

        # Retrieve the PropertyGroup assigned to the context from the panel
        # see in BAGAPIE_MT_pie_menu_geopack
        if self.my_pack is None:
            pack_item = context.my_pack
            self.my_pack = context.my_pack
        else:
            pack_item = self.my_pack

        pie_branch_count = len(pack_item.modifiers_list)
        if pie_branch_count > 8:
            pie_branch_count = 8
                
        modifiers_avec_icon = [mo for mo in pack_item.modifiers_list if mo.name in bagapie_geopack_icon.previews and mo.pieVisibility]
        modifiers_sans_icon = [mo for mo in pack_item.modifiers_list if mo.name not in bagapie_geopack_icon.previews and mo.pieVisibility]

        amount = round(len(modifiers_sans_icon)/6)

        for id in range(8):
            col = pie.column(align=True)

            # WITH ICON
            if id == 2: # BAS
                row = col.row(align=False)
                for index, mo in enumerate(modifiers_avec_icon):
                    if (index+1) % 1 != -1:

                        col_mo = row.column(align=True)
                        if len(modifiers_sans_icon) != 0:
                            col_mo.separator(factor =5)
                        col_mo.template_icon(icon_value=bagapie_geopack_icon.previews[mo.name].icon_id, scale=pref.geopack_icon_scale)
                        row_name = col_mo.row(align=True)
                        Display_Button(row_name, mo, pack_item, "")
                        modifiers_avec_icon.remove(mo)

            elif id == 3: # HAUT
                row = col.row(align=False)
                for index, mo in enumerate(modifiers_avec_icon):

                    col_mo = row.column(align=True)
                    col_mo.template_icon(icon_value=bagapie_geopack_icon.previews[mo.name].icon_id, scale=pref.geopack_icon_scale)
                    row_name = col_mo.row(align=True)
                    Display_Button(row_name, mo, pack_item, "")
                    if len(modifiers_sans_icon) != 0:
                        col_mo.separator(factor =5)

            # WITHOUT ICON
            else:
                row = col.row(align=True)
                if id==6 or id==7:
                    col.separator(factor =5)
                for idx, mo in enumerate(modifiers_sans_icon[0:amount]):
                    if (idx + 1) % 1 == 0 : # Add property to control the number of collections
                        col.separator(factor = 0.3)
                        row = col.row(align=True)
                    row.separator(factor = 0.5)
                    Display_Button(row, mo, pack_item, "Asset")   
                    modifiers_sans_icon.remove(mo)
                if id==7:
                    for mo in modifiers_sans_icon:
                        Display_Button(row, mo, pack_item, "Asset")   
                if id==4 or id==5:
                    col.separator(factor =5)

class BAGAPIE_OT_geopack_assetbrowser(Operator):
    """ Import assets based on the asset browser selection and use the geopack tool (left) """
    bl_idname = "geopack.asset_browser"
    bl_label = 'import from asset browser'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not hasattr(context,"my_modifier"):
            return False
        data = json.loads(context.my_modifier.config)
        if data['usage'].get('asset_browser'):
            if context.object:
                ob_ty = context.object.type
            else:
                ob_ty = "None"
            if data['usage'].get('active_target') == "NEW" or ob_ty in data['usage'].get('active_target'):
                area = find_areas('ASSETS')
                if area is not None:
                    win = find_window('ASSETS')
                    if area.ui_type == 'ASSETS':
                        with context.temp_override(window=win, area = area):
                            return cls.check_data(cls,context), context.selected_assets
                else:
                    return False
            else:
                return False
        else:
            return False

    pack_item_pass: bpy.props.StringProperty(
            name = 'None',
            default = ''
            ) # type: ignore

    def check_data(self,context):
        if not hasattr(context,"my_modifier"):
            return False
        
        data = json.loads(context.my_modifier.config)

        if data['usage'].get('active_target') == "NEW":
            ...
        # Detection of the active object's type
        elif not context.object:
            return False
        
        elif context.object.type not in data['usage'].get('active_target'):
            
            if data['usage'].get('add_hair_curves',False) and context.active_object.type == "CURVES":
                # Direct assignment of the modifier allowed on a hair-type object
                ...
            else:
                return False

        # Detection of selected object types
        if data['usage'].get('use_selection'):                

            area = find_areas('ASSETS')
            if area is not None:
                win = find_window('ASSETS')
                if area.ui_type == 'ASSETS':
                    with context.temp_override(window=win, area = area):
                        if len(context.selected_assets) == 0:
                            return False

        return True
                
    def execute(self, context):
        area = find_areas('ASSETS')
        win = find_window('ASSETS')

        current_library_name = area.spaces.active.params.asset_library_reference
        if current_library_name == "LOCAL":
            library_path = Path(bpy.data.filepath)
        else:
            try:
                library_path = Path(context.preferences.filepaths.asset_libraries.get(current_library_name).path) 
            except:
                Warning(message = "The library 'All' isn't valid. Go to the library that contains the assets to select them.", title = "Asset Browser : Library not supported", icon = 'INFO')
                return {'FINISHED'}
        
        if not hasattr(context,"my_modifier"):
            return False
        data = json.loads(context.my_modifier.config)
        mo_supported_types=data['usage'].get('selection_types')

        # SETUP COLLECTIONS
        if bpy.data.collections.get("GeoPack") is None:
            main_coll = bpy.data.collections.new("GeoPack")
            bpy.context.scene.collection.children.link(main_coll)
            if bpy.data.collections.get("GeoPack_Assets") is None:
                asset_coll = bpy.data.collections.new("GeoPack_Assets")
                main_coll.children.link(asset_coll)
            else:
                asset_coll = bpy.data.collections["GeoPack_Assets"]
        else:
            main_coll = bpy.data.collections["GeoPack"]
            if bpy.data.collections.get("GeoPack_Assets") is None:
                asset_coll = bpy.data.collections.new("GeoPack_Assets")
                main_coll.children.link(asset_coll)
            else:
                asset_coll = bpy.data.collections["GeoPack_Assets"]

        # GET CURRENT CONTEXT AND SELECTION
        current_window = bpy.context.window
        current_area = None
        for cr_area in current_window.screen.areas:
            if cr_area.type == 'VIEW_3D':
                current_area = cr_area
                break

        #FIX SELECTION
        for o in context.selected_objects:
            o.select_set(False)

        # OVERRIDE CONTEXTE
        with context.temp_override(window=win, area=area):
            print("Imported Assets :")
            assets_imported = []
            for asset_file in context.selected_assets:
                asset_fullpath = library_path / asset_file.full_path
                if current_library_name == "LOCAL":
                    asset_fullpath /= asset_file.local_id.name

                asset_filepath = asset_fullpath.parent.parent
                inner_path = ntpath.basename(ntpath.dirname(asset_fullpath))
                asset_name = ntpath.basename(asset_fullpath)
                print('"'+asset_name+'"' + " from type : " + inner_path)
                time.sleep(1)
                try:
                    bpy.data.objects[asset_name].select_set(True)
                    objs = bpy.context.selected_objects
                    for a in objs:
                        assets_imported.append(a)

                except:
                    if inner_path == 'Collection' or inner_path == 'Object':
                        bpy.ops.wm.append(
                            filepath=os.path.join(asset_filepath, inner_path, asset_name),
                            directory=os.path.join(asset_filepath, inner_path),
                            filename=asset_name
                            )
                        objs = bpy.context.selected_objects
                        for a in objs:
                            for col in a.users_collection:
                                col.objects.unlink(a)
                            asset_coll.objects.link(a)
                            assets_imported.append(a)
                            
                        if inner_path == 'Collection':
                            bpy.data.collections.remove(bpy.data.collections[asset_name])
                    else:
                        print('"'+asset_name+'"' + " isn't a Collection or Object")

            if len(assets_imported) == 0:
                Warning(message = "You must select assets in the asset browser", title = "Asset Browser : No assets selected", icon = 'INFO')
                return {'FINISHED'}
            non_suported = False
            for ob in assets_imported:
                if ob.type in mo_supported_types:
                    ob.select_set(True)
                else:
                    non_suported=True

                    
            if context.object is not None:
                context.object.select_set(True)
            if non_suported:
                Warning(message = "Some objects you've selected aren't supported by this modifier because of theyr types (mesh, curves, light, ...). They've been imported in this scene but ignored.", title = "Asset Browser : No assets selected", icon = 'INFO')

            with context.temp_override(window=current_window, area = current_area):
                bpy.ops.bagapie.geopack_assign_modifier('INVOKE_DEFAULT', packName = self.pack_item_pass, from_asset_browser=True)

        return {'FINISHED'}

class BAGAPIE_OT_geopack_assign_modifier(Operator):
    """ Assign GeoPack Modifier """
    bl_idname = "bagapie.geopack_assign_modifier"
    bl_label = 'Assign GeoPack Modifier to the current object'
    bl_options = {'REGISTER', 'UNDO'}

    packName:bpy.props.StringProperty(name="packName") # type: ignore
    from_asset_browser:bpy.props.BoolProperty(default=False) # type: ignore
    is_scatter: bpy.props.BoolProperty(name="is scatter", default=False) # type: ignore
    replace_scatter:bpy.props.BoolProperty(name="merge scatter", default=False) # type: ignore
    ignore_replace_scatter_popup:bpy.props.BoolProperty(name="ignore replace scatter", default=False) # type: ignore

    @classmethod
    def poll(cls, context):
        obj = context.object
        
        # Check if is_scatter
        if obj and obj.bagapieList is not None:
            for value in obj.bagapieList:
                val = json.loads(value['val'])
                if val.get('name') == 'scatter':
                    return True

        return cls.check_data(cls,context)

    def check_data(self,context):
        
        data = json.loads(context.my_modifier.config)

        if data['usage'].get('active_target') == "NEW":
            ...
        # Detection of the active object's type
        elif not context.object:
            return False
        
        elif context.object.type not in data['usage'].get('active_target'):
            
            if data['usage'].get('add_hair_curves',False) and context.active_object.type == "CURVES":
                # Direct assignment of the modifier allowed on a hair-type object
                ...
            else:
                return False

        # Detect types of selected objects
        if data['usage'].get('use_selection'):

            if data['usage'].get('active_target') == "NEW":
                if len(context.selected_objects) < 1:
                    return False
            else:
                if len(context.selected_objects) < 2:
                    return False
            
            types = {}
            for t in data['usage'].get('selection_types'):
                types[t] = 0

            for o in context.selected_objects:
                if o.type in data['usage'].get('selection_types'):
                    types[o.type] += 1
                    # bypass to validate the selection if only one of the required types is present
                    return True
            
            for value in types.values():
                if value == 0:
                    return False

        return True

    def invoke(self, context, event):
        if not hasattr(context,"my_modifier"):
            debug("No hasattr(context,'my_modifier')")
            return {'FINISHED'}

        self.my_modifier = context.my_modifier

        obj = context.object
        is_scatter = False
        # Check if is_scatter
        if obj and obj.bagapieList is not None:
            for value in obj.bagapieList:
                val = json.loads(value['val'])
                if val.get('name') == 'scatter':
                    is_scatter = True
                    break
        if is_scatter == True and self.ignore_replace_scatter_popup == False:
            modifier = self.my_modifier
            data = json.loads(modifier.config)
            if data.get('custom_prop'):
                return context.window_manager.invoke_props_dialog(self)
            else:
                return self.execute(context)
        else:
            return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Scatter detected:")
        layout.prop(self, 'replace_scatter', text = "Replace")
        if self.replace_scatter == True:
            layout.label(text="New scatter system will override the current")
            layout.label(text="Current CamCulling/Effectorwill be lost !")
            layout.prop(self, 'ignore_replace_scatter_popup', text = "Don't ask again")
        else:
            layout.label(text="Operation Ignored")

    def execute(self, context):
        modifier = self.my_modifier
        data = json.loads(modifier.config)

        if self.from_asset_browser and data['usage'].get('active_target') == "NEW" and context.active_object is not None:
            context.active_object.select_set(False)

        selection = context.selected_objects
        active = context.active_object

        # ----- CHECK IF is_scatter -----
        is_scatter = False
        if active and active.bagapieList is not None:
            for value in active.bagapieList:
                val = json.loads(value['val'])
                if val.get('name') == 'scatter':
                    is_scatter = True

        json_file = modifier.path
        pre, ext = os.path.splitext(json_file)
        blend_file = f"{pre}.blend"

        assets_path = os.path.join(os.path.dirname(json_file),'Assets')

        obj = context.object

        with open(json_file) as f:
            data = json.loads(f.read())

            group_name = data['info']['group_name']
            debug("Import : "+group_name)

            # REPLACE SCATTER DISABLED WHILE SCATTER IS PRESENT AND THE CURRENT IMPORT
            if self.replace_scatter == False and is_scatter == True and group_name.startswith("BagaPie_Scatter"):
                debug("Replace disabled, operation cancelled")
                return {'FINISHED'}

            # CHECK IF A SCATTER IS IMPORTED
            is_nodegroup_scatter = False
            if group_name.startswith("BagaPie_Scatter"):
                is_nodegroup_scatter = True
                debug("Scatter type modifier")
                
            if bpy.data.node_groups.get(group_name,None) is None or is_nodegroup_scatter == True:
                with bpy.data.libraries.load(blend_file) as (data_from, data_to):
                    data_to.node_groups = [group_name]

            # GET THE IMPORTED SCATTER NODE GROUP
            if is_nodegroup_scatter == True:
                group_name = data_to.node_groups[0].name
                # Blender will replace data_to.node_groups with the files imported by NodeGroups

            # Check if a collection named "GeoPack" already exists
            if "GeoPack" in bpy.data.collections:
                # Retrieve the existing collection
                geopack_collection = bpy.data.collections["GeoPack"]
            else:
            
                # Create a new collection
                geopack_collection = bpy.data.collections.new("GeoPack")

                # Add the collection to the active scene
                bpy.context.scene.collection.children.link(geopack_collection)

            pack_collection_name = self.packName

            # Check if the sub-collection already exists in "GeoPack", otherwise create it
            if pack_collection_name in geopack_collection.children:
                pack_collection = geopack_collection.children[pack_collection_name]
            else:
                pack_collection = bpy.data.collections.new(name=pack_collection_name)
                geopack_collection.children.link(pack_collection)


            if data['usage']['active_target'] == "NEW":
                if data['usage']['new_object_type'] == "MESH":
                    # Create a new mesh data block
                    mesh_data = bpy.data.meshes.new(name=data['info']['name'])

                    # Create a new mesh object
                    mesh_object = bpy.data.objects.new(name=data['info']['name'], object_data=mesh_data)

                    # Add the new mesh object to the scene
                    bpy.context.scene.collection.objects.link(mesh_object)

                    # Select the new mesh object
                    bpy.context.view_layer.objects.active = mesh_object

                    obj = mesh_object
                
                if data['usage']['new_object_type'] == "CURVE":
                    # Create a new curve data block
                    curve_data = bpy.data.curves.new(name=data['info']['name'], type='CURVE')
                    
                    if not data['usage'].get('new_curve_draw_dimension'):
                        curve_data.dimensions = '3D'

                    # Create a new curve object
                    curve_object = bpy.data.objects.new(name=data['info']['name'], object_data=curve_data)

                    # Add the new curve object to the scene
                    bpy.context.scene.collection.objects.link(curve_object)

                    # Select the new curve object
                    bpy.context.view_layer.objects.active = curve_object

                    obj = curve_object

                # Déplace l'objet dans la nouvelle sous-collection
                if obj and obj.users_collection[0] != pack_collection:
                    obj_collection = obj.users_collection[0]
                    obj_collection.objects.unlink(obj)
                    pack_collection.objects.link(obj)

        if data['usage']['add_hair_curves'] and data['usage'].get('active_target') != "NEW" and data['usage'].get('active_target') != "CURVE":
            # assignation du modifier directement autorisée sur un objet de tyep hair
            if obj.type != "CURVE":
                bpy.ops.object.curves_empty_hair_add(align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            obj = bpy.context.active_object
            bpy.ops.object.mode_set(mode='SCULPT_CURVES')
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.add")

            brush = bpy.context.tool_settings.curves_sculpt.brush
            brush.curves_sculpt_settings.curve_length = data['usage'].get('hair_curves_length',1)
            brush.curves_sculpt_settings.points_per_curve = data['usage'].get('hair_curves_points_count',2)
            brush.curves_sculpt_settings.add_amount = data['usage'].get('hair_curves_count',10)

        # ----- REMOVE OLD SCATTER -----
        if is_scatter == True and self.replace_scatter == True:
            found=True
            while found:
                found = False
                for idx, value in enumerate(obj.bagapieList):
                    if "val" in value:
                        try:
                            val = json.loads(value['val'])
                            if val.get('name') == 'scatter':
                                bpy.ops.bagapie.scatter_remove(index=idx)
                                found = True
                                break  # restart from beginning
                        except:
                            continue


        # ----- ADD MODIFIER -----
        mod = obj.modifiers.new(name=data['info']['name'], type='NODES')
        mod.node_group = bpy.data.node_groups[group_name]
        obj_type = obj.type

        if data['usage']['active_target'] == "NEW":
            bpy.context.view_layer.objects.active = None
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            obj.location = bpy.context.scene.cursor.location

            if data['usage'].get('new_mesh_add_cube') and obj.type == 'MESH':
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.wm.tool_set_by_id(name="builtin.primitive_cube_add")

            if data['usage'].get('new_curve_draw') and obj.type == 'CURVE':
                obj.data.resolution_u = 64
                obj.data.render_resolution_u = 64

                bpy.ops.object.mode_set(mode='EDIT')
                if data['usage'].get("new_curve_draw_mode"):
                    bpy.context.scene.tool_settings.curve_paint_settings.depth_mode = 'CURSOR'
                else:
                    bpy.context.scene.tool_settings.curve_paint_settings.depth_mode = 'SURFACE'
                bpy.ops.wm.tool_set_by_id(name="builtin.draw")

        else:
            if active in selection:
                selection.remove(active)

        if data['usage']['use_selection'] and data['usage']['coll_name']:
            pack_collection = bpy.data.collections.get(self.packName)
            if pack_collection is None:
                pack_collection = bpy.data.collections.new(self.packName)    
                bpy.context.scene.collection.children.link(pack_collection)

            new_collection = bpy.data.collections.new(data['usage']['coll_name'])
            pack_collection.children.link(new_collection)
            for obj in selection:
                new_collection.objects.link(obj)

            if data['usage']['coll_input']:
                mod[data['usage']['coll_input']] = new_collection

        if data['usage']['mesh_paint_mode'] and obj_type == 'MESH':
            input_name = data['usage']['paint_inputs_list']
            vg = obj.vertex_groups.new(name=data['usage']['paint_v_group_name'])
            bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
            bpy.ops.object.geometry_nodes_input_attribute_toggle(input_name = input_name, modifier_name=mod.name)
            mod[f"{input_name}_attribute_name"] = vg.name

        # ADD CURVE AND DRAW
        if (
            not data['usage'].get('mesh_paint_mode')
            and not data['usage'].get('add_hair_curves')
            and data['usage'].get('active_target') in {'MESH', 'CURVE', 'MESH_CURVE'}
            and data['usage'].get('add_curve_and_draw')
            ):
            
            # Create a new curve data block
            curve_data = bpy.data.curves.new(name=data['info']['name'], type='CURVE')
            
            if not data['usage'].get('new_curve_draw_dimension'):
                curve_data.dimensions = '3D'

            # Create a new curve object
            curve_object = bpy.data.objects.new(name=data['usage']['object_name'], object_data=curve_data)

            # Add the new curve object to the scene
            bpy.context.scene.collection.objects.link(curve_object)

            # Select the new curve object
            bpy.context.view_layer.objects.active = curve_object

            curve_object.data.resolution_u = 64
            curve_object.data.render_resolution_u = 64

            mod[data['usage']['object_input']] = curve_object

            bpy.ops.object.mode_set(mode='EDIT')
            if data['usage'].get("new_curve_draw_mode"):
                bpy.context.scene.tool_settings.curve_paint_settings.depth_mode = 'CURSOR'
            else:
                bpy.context.scene.tool_settings.curve_paint_settings.depth_mode = 'SURFACE'
            bpy.ops.wm.tool_set_by_id(name="builtin.draw")

        assets_data = data.get('assets_data')
        if assets_data:
            # préchargement des assets s'il ne sont pas déjà référencés
            for asset_data in assets_data:
                if asset_data['datablock_name'] is None:
                    continue
                
                sub_assets = []
                if asset_data['socket_type'] == 'NodeSocketCollection':
                    sub_list = asset_data.get('sub_assets')
                    if sub_list:
                        for s,sub_asset_name in enumerate(asset_data['sub_assets']):
                            sub_assets.append({
                                "socket_type": "NodeSocketObject",
                                "datablock_name": sub_asset_name,
                                "filename": asset_data['sub_assets_files'][s]
                            })
                else:
                    sub_assets = [asset_data]

                for sub_asset_data in sub_assets:
                    if bpy.data.objects.get(sub_asset_data['datablock_name']) is not None:
                        # asset déjà chargé    
                        continue

                    filename = sub_asset_data.get('filename')
                    if filename is None:
                        # pas de fichier asset défini dans les data
                        continue

                    asset_file = os.path.join(assets_path,filename)
                    if not os.path.isfile(asset_file):
                        print(f"Error ! Missing asset file {asset_file}")
                        continue

                    with bpy.data.libraries.load(asset_file, assets_only=False) as (file_contents, data_to):

                        if sub_asset_data['socket_type'] == 'NodeSocketObject':
                            for object_name in file_contents.objects:
                                if bpy.data.objects.get(object_name) is None:
                                    data_to.objects.append(object_name)

                        elif sub_asset_data['socket_type'] == 'NodeSocketMaterial':
                            for material_name in file_contents.materials:
                                if bpy.data.materials.get(material_name) is None:
                                    data_to.materials.append(material_name)

                        # elif asset_data['socket_type'] == 'NodeSocketCollection':
                        #     for collection_name in file_contents.collections:
                        #         if bpy.data.collections.get(collection_name) is None:
                        #             data_to.collections.append(collection_name)

                if asset_data['datablock_name'] is None:
                    # utilisation de la valeur par défaut de l'input
                    continue

                elif asset_data['socket_type'] == 'NodeSocketObject':
                    mod[asset_data['socket_identifier']] = bpy.data.objects.get(asset_data['datablock_name'])

                elif asset_data['socket_type'] == 'NodeSocketMaterial':
                    mod[asset_data['socket_identifier']] =  bpy.data.materials.get(asset_data['datablock_name'])

                elif asset_data['socket_type'] == 'NodeSocketCollection':
                    main_coll =  bpy.data.collections.get(asset_data['datablock_name'])

                    if main_coll is None:
                        main_coll = bpy.data.collections.new(asset_data['datablock_name'])
                        bpy.context.scene.collection.children.link(main_coll)

                    sub_list = asset_data.get('sub_assets')
                    if sub_list:
                        for sub_asset_name in sub_list:
                            sub_asset = bpy.data.objects.get(sub_asset_name)
                            if sub_asset and not main_coll.objects.get(sub_asset_name):
                                main_coll.objects.link(sub_asset)

                    mod[asset_data['socket_identifier']] = main_coll


        # ----- FIX MODIFIER REFRESH ----- 
        mod.show_viewport = False
        mod.show_viewport = True


        # ----- SCATTER EXCEPTION ----- 
        if data.get('custom_prop'): #must be done after refresh
            setup_scatter = False
            for val in data['custom_prop']:
                if val.get('name') == 'scatter':
                    item = active.bagapieList.add()
                    item.val = json.dumps(val)
                    setup_scatter = True
                    mod.name = val['modifiers'][0]

            if setup_scatter == True:
                nodes = mod.node_group.nodes

                # ----- COLLECTION -----
                for nd in nodes:
                    if nd.type == 'GROUP' and nd.label == "BagaPie_Scatter":
                        debug("Node found : "+nd.name)
                        if nd.inputs[1].default_value is not None:
                            debug("Node content : "+ nd.inputs[1].default_value.name)
                            Collection_Setup_Scatter(self,context,nd.inputs[1].default_value)
                            for o in nd.inputs[1].default_value.objects:
                                o.asset_clear()

                # ----- VERTEX GROUP ----- 
                for item in mod.node_group.interface.items_tree:
                    if item.in_out != 'INPUT':
                        continue
                    modifier_key = item.identifier
                    if modifier_key.startswith("Socket_"):
                        attr_key = f"{modifier_key}_attribute_name"
                        if attr_key in mod.keys():
                            vg = active.vertex_groups.new(name="BagaVertGrp")
                            
                            mod[attr_key] = vg.name

                            bpy.ops.object.geometry_nodes_input_attribute_toggle(
                                input_name=modifier_key,
                                modifier_name=mod.name
                                )
                
                # ----- CAM CULL & EFFECTOR ----- 
                for no in nodes:
                    if no.type == 'GROUP':
                        name = no.name
                        label = no.label
                        if (
                            name.startswith("BagaPie_Effector") or 
                            label.startswith("BagaPie_Effector") or 
                            name.startswith("BagaPie_Camera_Culling") or 
                            label.startswith("BagaPie_Camera_Culling")
                        ):
                            nodes.remove(no)

        return {'FINISHED'}

def Collection_Setup_Scatter(self,context,coll):
    # Create collection and check if the main "Baga Collection" does not already exist
    debug("Coll linked :" + coll.name)
    scatt_coll = bpy.data.collections[coll.name]
    if bpy.data.collections.get("BagaPie") is None:
        main_coll = bpy.data.collections.new("BagaPie")
        bpy.context.scene.collection.children.link(main_coll)
        scatter_master_coll = bpy.data.collections.new("BagaPie_Scatter")
        main_coll.children.link(scatter_master_coll)
        scatter_master_coll.children.link(scatt_coll)
    # If the main collection Bagapie already exist
    elif bpy.data.collections.get("BagaPie_Scatter") is None:
        main_coll = bpy.data.collections["BagaPie"]
        scatter_master_coll = bpy.data.collections.new("BagaPie_Scatter")
        main_coll.children.link(scatter_master_coll)
        scatter_master_coll.children.link(scatt_coll)
    # Just link it to the main scatter coll
    else:
        scatter_master_coll = bpy.data.collections["BagaPie_Scatter"]
        scatter_master_coll.children.link(scatt_coll)

    return scatt_coll

class BAGAPIE_OT_geopack_create_modifier(Operator):
    """ Create New GeoPack Modifier """
    bl_idname = "bagapie.geopack_create_modifier"
    bl_label = 'New GeoPack Modifier'

    @classmethod
    def poll(cls, context):
        o = context.object
        pref=Get_addon_pref()

        return (
            o is not None and 
            o.type in ['MESH','CURVE','CURVES'] and
            len(pref.geopacks_list) > 0
        )

    @staticmethod
    def update_step_state(self,context,propName,propValue):
        if propValue:
            if propName == "info":
                self.usage = False
                self.package = False
                self.setdata = False

            elif propName == "package":
                self.info = False
                self.usage = False
                self.setdata = False

            elif propName == "usage":
                self.info = False
                self.package = False
                self.setdata = False
            
            elif propName == "setdata":
                self.info = False
                self.package = False
                self.usage = False

    def close_panel(self,context,event):
        x, y = event.mouse_x, event.mouse_y
        win = context.window
        win.cursor_warp(10, 10)
        move_back = lambda: win.cursor_warp(x, y)
        bpy.app.timers.register(move_back, first_interval=0.01)

    #CREATION STEPS
    info: bpy.props.BoolProperty(default=True,update=lambda self,context: BAGAPIE_OT_geopack_create_modifier.update_step_state(self,context,"info",self.info)) # type: ignore
    usage: bpy.props.BoolProperty(default=False,update=lambda self,context: BAGAPIE_OT_geopack_create_modifier.update_step_state(self,context,"usage",self.usage)) # type: ignore
    package: bpy.props.BoolProperty(default=False,update=lambda self,context: BAGAPIE_OT_geopack_create_modifier.update_step_state(self,context,"package",self.package)) # type: ignore
    setdata: bpy.props.BoolProperty(default=False,update=lambda self,context: BAGAPIE_OT_geopack_create_modifier.update_step_state(self,context,"setdata",self.setdata)) # type: ignore

    select_pack: bpy.props.EnumProperty(items=[]) # type: ignore
    
    # INFO
    modifier_name: bpy.props.StringProperty(default="None") # type: ignore
    modifier_author: bpy.props.StringProperty(default="None") # type: ignore
    modifier_description: bpy.props.StringProperty(default="None") # type: ignore
    modifier_version: bpy.props.StringProperty(default="1.0.0") # type: ignore

    #VERSION DES MODIFIERS
    modifier_file_format_version: bpy.props.StringProperty(default="1.1.0") # type: ignore

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
        ("4_4","Blender 4.4",""),
        ("4_5","Blender 4.5",""),
    ]
    modifier_blender_version: bpy.props.EnumProperty(items=blender_version) # type: ignore
    modifier_contact: bpy.props.StringProperty(default="None") # type: ignore
    modifier_url: bpy.props.StringProperty(default="None") # type: ignore
    license = [
        ("ROYALTY_FREE", "Royalty Free", "The author retains all rights to the 3D model but allows users to use it without having to pay additional fees."),
        ("CC0", "CC0", "The author waives all rights to the 3D model, allowing users to freely use, modify, and distribute it without restriction."),
        ("CC-BY", "CC-BY", "A free and legal license that allows users to use, modify, and distribute the 3D model, as long as they give credit to the original author."),
        ("GPL", "GPL", "A free and open-source license that allows users to distribute, modify, and reuse the 3D model, ensuring that it remains accessible to all."),
        ("MIT", "MIT", "An open-source license that allows users to distribute, modify, and reuse the 3D model, often used in free and open-source software projects."),
    ]
    modifier_license: bpy.props.EnumProperty(items=license) # type: ignore

    # USAGE
    obj_type = [
        ("MESH","Mesh","The selected object must be of mesh type, otherwise the modifier button will be grayed out."),
        ("CURVE","Curve","The selected object must be of curve type, otherwise the modifier button will be grayed out."),
        ("MESH_CURVE","Mesh or Curve","The selected object must be of mesh or curve type, otherwise the modifier button will be grayed out."),
        ("NEW","None - Create new object","Ignore the selected object and create a new 'empty' one."),
    ]
    modifier_active_target: bpy.props.EnumProperty(items=obj_type) # type: ignore
    modifier_use_selection: bpy.props.BoolProperty(default=False) # type: ignore
    modifier_allow_asset_browser: bpy.props.BoolProperty(default=False) # type: ignore
    modifier_selection_type_mesh: bpy.props.BoolProperty(default=False) # type: ignore
    modifier_selection_type_curve: bpy.props.BoolProperty(default=False) # type: ignore
    modifier_selection_type_camera: bpy.props.BoolProperty(default=False) # type: ignore
    modifier_selection_type_empty: bpy.props.BoolProperty(default=False) # type: ignore
    modifier_selection_type_text: bpy.props.BoolProperty(default=False) # type: ignore
    modifier_selection_type_volume: bpy.props.BoolProperty(default=False) # type: ignore
    modifier_selection_type_light: bpy.props.BoolProperty(default=False) # type: ignore
    modifier_coll_name: bpy.props.StringProperty(default="None")    # type: ignore
    modifier_inputs_list: bpy.props.EnumProperty(items=update_list) # type: ignore
    modifier_add_curve_with_draw_mode: bpy.props.BoolProperty(default=False) # type: ignore
    modifier_object_name: bpy.props.StringProperty(default="Curve") # type: ignore
    modifier_object_inputs_list: bpy.props.EnumProperty(items=update_object_list) # type: ignore

    new_obj_type = [
        ("MESH","Mesh","The selected object must be of mesh type, otherwise the modifier button will be grayed out."),
        ("CURVE","Curve","The selected object must be of curve type, otherwise the modifier button will be grayed out.")
    ]
    modifier_new_obj_type: bpy.props.EnumProperty(items=new_obj_type) # type: ignore
    modifier_new_mesh_add_cube: bpy.props.BoolProperty(default=False) # type: ignore
    modifier_new_mesh_weight_paint: bpy.props.BoolProperty(default=False) # type: ignore
    modifier_new_curve_draw: bpy.props.BoolProperty(default=False) # type: ignore
    modifier_new_curve_draw_dimension: bpy.props.BoolProperty(default=False) # type: ignore
    modifier_new_curve_draw_mode: bpy.props.BoolProperty(default=False) # type: ignore

    @staticmethod
    def modifier_add_hair_curves_method():
        default=False
        def update(self, context):
            if self.modifier_add_hair_curves:
                self.modifier_mesh_paint_mode = False

        return locals()
    modifier_add_hair_curves: bpy.props.BoolProperty(**modifier_add_hair_curves_method()) # type: ignore

    modifier_add_hair_curves_length:bpy.props.FloatProperty(default=1, min = 0) # type: ignore
    modifier_add_hair_curves_points_count:bpy.props.IntProperty(default=2, min = 2) # type: ignore
    modifier_add_hair_curves_count:bpy.props.IntProperty(default=10, min = 1) # type: ignore

    # Weight Paint Mode
    @staticmethod
    def modifier_mesh_paint_mode_method():
        default=False
        def update(self, context):
            if self.modifier_mesh_paint_mode:
                self.modifier_add_hair_curves = False

        return locals()
    modifier_mesh_paint_mode: bpy.props.BoolProperty(**modifier_mesh_paint_mode_method()) # type: ignore

    modifier_weight_paint_inputs_list: bpy.props.EnumProperty(items=update_field_list) # type: ignore
    modifier_mesh_paint_v_group_name: bpy.props.StringProperty(default="GP_Group")    # type: ignore

    def geopack_list(self,context):
        pref = Get_addon_pref()
        items = []
        for pack in pref.geopacks_list:
            items.append((pack.identifier,pack.name,pack.description))
        return items
    
    modifier_geopack: bpy.props.EnumProperty(items=geopack_list) # type: ignore

    # PACKING
    modifier_pack_path: bpy.props.StringProperty(default="None")    # type: ignore
    modifier_pack_name: bpy.props.StringProperty(default="None") # type: ignore
    modifier_pack_authors: bpy.props.StringProperty(default="None") # type: ignore
    modifier_pack_pack_url: bpy.props.StringProperty(default="None") # type: ignore
    modifier_pack_description: bpy.props.StringProperty(default="None") # type: ignore
    modifier_pack_license: bpy.props.EnumProperty(items=license) # type: ignore
    modifier_pack_blender_version: bpy.props.EnumProperty(items=blender_version) # type: ignore
    modifier_pack_version: bpy.props.StringProperty(default="None") # type: ignore

    export_data = {"info":{} , "usage":{} , "package":{} }

    cancel:bpy.props.BoolProperty(name="cancel",default=False) # type: ignore

    override_existing_modifier:bpy.props.BoolProperty(default=False) # type: ignore

    # DATA
    # export individual modifier assets
    modifier_data_export_items0: bpy.props.BoolVectorProperty(
        name="modifier_data_export_items0",
        size=32,
        default=(True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True)
    ) # type: ignore
    modifier_data_export_items1: bpy.props.BoolVectorProperty(
        name="modifier_data_export_items1",
        size=32,
        default=(True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True)
    ) # type: ignore
    modifier_data_export_items2: bpy.props.BoolVectorProperty(
        name="modifier_data_export_items2",
        size=32,
        default=(True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True)
    ) # type: ignore

    # keep default values in input assets
    modifier_data_keep_default0: bpy.props.BoolVectorProperty(
        name="modifier_data_keep_default0",
        size=32
    ) # type: ignore

    modifier_data_keep_default1: bpy.props.BoolVectorProperty(
        name="modifier_data_keep_default1",
        size=32
    ) # type: ignore

    modifier_data_keep_default2: bpy.props.BoolVectorProperty(
        name="modifier_data_keep_default2",
        size=32
    ) # type: ignore

    # keep default values in input assets
    modifier_data_is_asset0: bpy.props.BoolVectorProperty(
        name="modifier_data_is_asset0",
        size=32
    ) # type: ignore

    modifier_data_is_asset1: bpy.props.BoolVectorProperty(
        name="modifier_is_asset1",
        size=32
    ) # type: ignore

    modifier_data_is_asset2: bpy.props.BoolVectorProperty(
        name="modifier_data_is_asset2",
        size=32
    ) # type: ignore
    
    data_into_tooltip:bpy.props.BoolProperty(name="data_into_tooltip",default=False) # type: ignore
    data_into_tooltip_plus:bpy.props.BoolProperty(name="data_into_tooltip",default=False) # type: ignore

    is_scatter: bpy.props.BoolProperty(name="is_scatter", default=False) # type: ignore

    modifier_data_export = []

    def invoke(self, context, event):
        obj = context.object
        if obj is None:
            Warning(message = "No object selected", title = "Warning", icon = 'INFO')
            return {'FINISHED'}
        modifiers = obj.modifiers
        if len(modifiers) <= 0:
            Warning(message = "No modifiers found", title = "Warning", icon = 'INFO')
            return {'FINISHED'}
        modifier = modifiers.active if obj.modifiers else None
        if modifier.type != 'NODES':
            Warning(message = "No nodes group found. Select the geometry nodes modifier in the modifier stack", title = "Warning", icon = 'INFO')
            return {'FINISHED'}
        
        wm = context.window_manager

        obj = context.object
        modifiers = obj.modifiers
        modifier = modifiers.active if obj.modifiers else None
        if modifier:
            self.modifier_name = modifier.node_group.name

        # Check if is scatter
        self.is_scatter = False
        if obj.bagapieList is not None:
            for value in obj.bagapieList:
                val = json.loads(value['val'])
                if val.get('name') == 'scatter':
                    self.is_scatter = True
        
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        obj = context.object
        modifiers = obj.modifiers
        modifier = modifiers.active if obj.modifiers else None

        if not modifier:
            col = layout.column()
            box = col.box()
            row = box.row(align=True)
            row.label(text="No modifier selected")        
            return
        
        col = layout.column()
        box = col.box()
        row = box.row(align=True)
        row.label(text="Add to pack :")
        row.prop(self, 'modifier_geopack', text="")
        box.label(text='Modifier : ' + modifier.node_group.name)

        row = box.row(align=True)

        self.cancel = False
        currentPack = self.modifier_geopack
        bagapie_pref = Get_addon_pref()

        """
        if bpy.data.node_groups.get(modifier.node_group.name) if is_scatter == False:
            box.label(text=f'Modifier name "{modifier.node_group.name}"')
            box.label(text=f'is already in use')
            box.label(text='Please, rename your node tree.')
            box.prop(self,'override_existing_modifier',text="Override",toggle = True)

            if not self.override_existing_modifier:
                self.cancel = True
                return
        """

        for pack_item in bagapie_pref.geopacks_list:
            if pack_item.identifier == currentPack:
                for mo in pack_item.modifiers_list:
                    if mo.name.lower() == modifier.node_group.name.lower():
                        box.label(text=f'Modifier name "{modifier.node_group.name}"')
                        box.label(text=f'already used in pack {pack_item.name}!')
                        box.label(text='Please, rename your node tree.')
                        self.cancel = True
                        return

        col = layout.column()
        row = col.row(align=True)
        row.scale_y = 2
        row.prop(self, 'info', text = "Info",toggle = True)

        row.label(text='', icon = 'TRIA_RIGHT')
        row.prop(self, 'usage', text = "Usage",toggle = True)

        row.label(text='', icon = 'TRIA_RIGHT')
        row.prop(self, 'setdata', text = "Data",toggle = True)

        col.separator(factor = 1)

        ###########################################################################################
        #           INFO
        ###########################################################################################
        if self.info:
            col.label(text="Modifier name")
            col.prop(self, 'modifier_name', text = "")
            col.separator(factor = 0.6)
            
            obj = context.active_object
            if self.is_scatter == True:
                pref = Get_addon_pref()
                if pref.geopack_render_generate == True:
                    res = pref.geopack_render_resolution
                    samples = pref.geopack_render_samples
                    txt = f'Generate Preview ({res}x{res}px / {samples} samples)'
                    col.prop(pref, 'geopack_render_generate', text=txt)
                    col.separator(factor = 0.6)

            col.label(text="Author(s)")
            col.prop(self, 'modifier_author', text="")
            col.separator(factor = 0.6)

            col.label(text="Description")
            col.prop(self, 'modifier_description', text="")
            col.separator(factor = 0.6)

            col.label(text="Modifier Version (e.g : 1.0.0)")
            col.prop(self, 'modifier_version', text="")
            col.separator(factor = 0.6)

            col.label(text="Minimal Blender version")
            col.prop(self, 'modifier_blender_version', text="")
            col.separator(factor = 0.6)

            col.label(text="Contact")
            col.prop(self, 'modifier_contact', text="")
            col.separator(factor = 0.6)

            col.label(text="URL")
            col.prop(self, 'modifier_url', text="")
            col.separator(factor = 0.6)

            col.label(text="NodeTree License")
            col.prop(self, 'modifier_license', text="")

        ###########################################################################################
        #           USAGE
        ###########################################################################################
        if self.usage:
            target="NONE"
            selection ="NONE"
            selection_type =""
            asset_browser_selection_msg =""
            col.label(text="Define how the Modifier is setup :")
            col.separator(factor = 0.5)
            col.label(text='Active Object Must Be :')
            col.prop(self, 'modifier_active_target', text="")

            ###########################################################################################
            #           NEW
            ###########################################################################################
            if self.modifier_active_target == 'NEW':
                target = 'nothing/whatever '
                row = col.row(align=True)
                split = row.split(factor=0.5)
                row.label(text='New object type :')
                row.prop(self, 'modifier_new_obj_type', text = "")
                col.separator(factor = 1)

                if self.modifier_new_obj_type == 'MESH':
                    col.prop(self, 'modifier_new_mesh_add_cube', text = "Switch to Edit Mode and enable Add Cube tool")

                elif self.modifier_new_obj_type == 'CURVE':
                    col.prop(self, 'modifier_new_curve_draw', text = "Switch to draw curve mode")
                    if  self.modifier_new_curve_draw:
                        col.label(text='Curve Mode :')
                        row = col.row(align=True)
                        row.prop(self, 'modifier_new_curve_draw_dimension', text = "2D", toggle = True)
                        row.prop(self, 'modifier_new_curve_draw_dimension', text = "3D", toggle = True, invert_checkbox = True)
                        col.label(text='Curve Projection :')
                        row = col.row(align=True)
                        row.prop(self, 'modifier_new_curve_draw_mode', text = "Cursor", toggle = True)
                        row.prop(self, 'modifier_new_curve_draw_mode', text = "Surface", toggle = True, invert_checkbox = True)

            ###########################################################################################
            #           MESH
            ###########################################################################################
            elif self.modifier_active_target == 'MESH':
                target = 'a MESH '
                row = col.row(align=True)
                split = row.split(factor=0.5)
                row.prop(self, 'modifier_mesh_paint_mode', text = "Switch to Weight Paint",toggle = True)
                row.prop(self, 'modifier_add_hair_curves', text = "Add Hair Curves",toggle = True)
                if self.modifier_add_hair_curves == False and self.modifier_mesh_paint_mode == False:
                    col.prop(self, 'modifier_add_curve_with_draw_mode', text = "Add Curve and switch to draw mode",toggle = True)
                
                if self.modifier_mesh_paint_mode:
                    box = col.box()
                    inputs = modifier.node_group.interface.items_tree
                    val_input_found = False
                    value = ["NodeSocketBool","NodeSocketString","NodeSocketVector","NodeSocketInt","NodeSocketFloat","NodeSocketColor","NodeSocketRotation"]
                    for input in inputs:
                        if input.bl_socket_idname in value:
                            val_input_found = True
                    if not val_input_found:
                        box_alert = box.box()
                        box_alert.alert = True
                        box_alert.label(text="No attribute input found")
                    else:
                        box.scale_y = 0.9
                        box.label(text='A new Vertex group will be created')
                        box.label(text='Verter Group Name :')
                        box.prop(self, 'modifier_mesh_paint_v_group_name', text = "")
                        box.label(text='Verter Group Input :')
                        box.prop(self, 'modifier_weight_paint_inputs_list', text = "")

                if self.modifier_add_hair_curves:
                    box = col.box()
                    box.prop(self, 'modifier_add_hair_curves_length', text = "Hair Length")
                    box.prop(self, 'modifier_add_hair_curves_points_count', text = "Hair Point")
                    box.prop(self, 'modifier_add_hair_curves_count', text = "Hair Count")

            ###########################################################################################
            #           CURVE
            ###########################################################################################
            elif self.modifier_active_target == 'CURVE':
                target = 'a CURVE '
                col.prop(self, 'modifier_add_curve_with_draw_mode', text = "Add Curve and switch to draw mode",toggle = True)

            ###########################################################################################
            #           MESH OR CURVE
            ###########################################################################################
            elif self.modifier_active_target == 'MESH_CURVE':
                target = 'a MESH or CURVE '
                col.prop(self, 'modifier_add_curve_with_draw_mode', text = "Add Curve and switch to draw mode",toggle = True)

            ###########################################################################################
            #           ADD CURVE AND DRAW
            ###########################################################################################
            if self.modifier_active_target in {'MESH', 'CURVE', 'MESH_CURVE'} and self.modifier_add_curve_with_draw_mode:
                if self.modifier_add_hair_curves == False and self.modifier_mesh_paint_mode == False:
                    box = col.box()
                    box_c = box.column(align=True)
                    box_c.label(text='Modifier will be set on Active Object')
                    box_c.label(text='New Curve is created and set in the Modifier')
                    box_c.label(text='New Curve switch to Edit Mode > Draw Mode')

                    inputs = modifier.node_group.interface.items_tree
                    val_input_found = False
                    for input in inputs:
                        if input.bl_socket_idname == "NodeSocketObject":
                            val_input_found = True
                    if val_input_found==False:
                        box_c.label(text='Object input missing in modifier!')
                    else:
                        box_c.label(text="Curve Name :")
                        box_c.prop(self, 'modifier_object_name', text="")
                        box_c.label(text="Object Inputs :")
                        box_c.prop(self, 'modifier_object_inputs_list', text="")

                        box_c.label(text='Curve Mode :')
                        row = box_c.row(align=True)
                        row.prop(self, 'modifier_new_curve_draw_dimension', text = "2D", toggle = True)
                        row.prop(self, 'modifier_new_curve_draw_dimension', text = "3D", toggle = True, invert_checkbox = True)
                        box_c.label(text='Curve Projection :')
                        row = box_c.row(align=True)
                        row.prop(self, 'modifier_new_curve_draw_mode', text = "Cursor", toggle = True)
                        row.prop(self, 'modifier_new_curve_draw_mode', text = "Surface", toggle = True, invert_checkbox = True)

            ###########################################################################################
            #           USE SELECTION
            ###########################################################################################
            col.prop(self, 'modifier_use_selection', text = "Use Selection",toggle = True)
            if self.modifier_use_selection:
                box = col.box()
                box.separator(factor = 0.5)
                box.scale_y = 0.9
                selection = 'and select others object from type '
                
                inputs = modifier.node_group.interface.items_tree
                coll_found = False
                for input in inputs:
                    if input.bl_socket_idname == 'NodeSocketCollection':
                        coll_found = True
                if coll_found:
                    box.prop(self, 'modifier_allow_asset_browser', text = "Allow asset browser selection", icon='ASSET_MANAGER') # Use asset browser button
                    row = box.row(align=True)
                    split = row.split(factor=0.7)
                    split.label(text='Selected object(s) Must be :')
                    col_type = split.column(align=True)
                    col_type.prop(self, 'modifier_selection_type_mesh', text = "Mesh")
                    if self.modifier_selection_type_mesh:
                        selection_type += "Mesh, "
                    col_type.prop(self, 'modifier_selection_type_curve', text = "Curve")
                    if self.modifier_selection_type_curve:
                        selection_type += "Curve, "
                    col_type.prop(self, 'modifier_selection_type_camera', text = "Camera")
                    if self.modifier_selection_type_camera:
                        selection_type += "Camera, "
                    col_type.prop(self, 'modifier_selection_type_empty', text = "Empty")
                    if self.modifier_selection_type_empty:
                        selection_type += "Empty, "
                    col_type.prop(self, 'modifier_selection_type_text', text = "Text")
                    if self.modifier_selection_type_text:
                        selection_type += "Text, "
                    col_type.prop(self, 'modifier_selection_type_volume', text = "Volume")
                    if self.modifier_selection_type_volume:
                        selection_type += "Volume, "
                    col_type.prop(self, 'modifier_selection_type_light', text = "Light")
                    if self.modifier_selection_type_light:
                        selection_type += "Light, "
                if selection_type == "":
                    selection_type += 'NONE'

                if not coll_found:
                    box_alert = box.box()
                    box_alert.alert = True
                    box_alert.label(text="No Collection input found")
                else:
                    box.label(text="Collection Name")
                    box.prop(self, 'modifier_coll_name', text="")
                    box.label(text="Collection Input")
                    box.prop(self, 'modifier_inputs_list', text="")
                if self.modifier_active_target == 'NEW':
                    target =""
                    selection = 'object from type '
            else:
                selection = '.'

            # CREATOR INFORMATION
            col.separator(factor = 1)
            box = col.box()
            box.scale_y = 0.5
            box.label(text="How your modifier will work :")
            if self.modifier_active_target == 'MESH':
                if self.modifier_mesh_paint_mode:
                    box.label(text="- Active object will receive the modifier ")
                    box.label(text="  and switch to Weight Paint, ")
                    box.label(text="  and a new vertex group will be created,")
                    box.label(text="  and it will be assigned to :")
                    if self.modifier_weight_paint_inputs_list != '':
                        match = re.search(r'_([0-9]+)$', self.modifier_weight_paint_inputs_list)
                        if match:
                            input_index = int(match.group(1)) - 1
                        box.label(text="  "+ modifier.node_group.interface.items_tree[input_index].name+" ("+self.modifier_weight_paint_inputs_list +")")                  
                    else:
                        box.label(text="  No input selected")
                elif self.modifier_add_hair_curves:
                    box.label(text="- A new Hair Object will be created")
                    box.label(text="  and will receive the modifier")
                else:
                    box.label(text="- Active object will receive the modifier ")


            elif self.modifier_active_target != 'NEW':
                box.label(text="- Active object will receive the modifier")
            else :
                if self.modifier_new_obj_type == 'MESH':
                    new_obj = "mesh"
                    if self.modifier_new_mesh_add_cube:
                        draw_mode = " and switch to add cube"
                    else:
                        draw_mode = ""
                elif self.modifier_new_obj_type == 'CURVE':
                    new_obj = "curve"
                    if self.modifier_new_curve_draw:
                        draw_mode = " and switch to draw curve"
                    else:
                        draw_mode = ""

                box.separator(factor = 1)
                box.label(text="- A new "+ new_obj +" will be created"+draw_mode)

            if self.modifier_add_curve_with_draw_mode:
                box.label(text="- New Curve will be created")
                box.label(text="- New Curve will be set in the modifier")
                box.label(text="- New Curve will switch to edit mode")
                if self.modifier_new_curve_draw_mode:
                    box.label(text="- New Curve: draw based on 3D Cursor")
                else:
                    box.label(text="- New Curve: draw based on Surface")
                
            if self.modifier_use_selection:
                box.separator(factor = 1)
                box.label(text="- Selected objects will be linked to new coll named :")
                box.label(text="  "+self.modifier_coll_name)
                box.separator(factor = 1)
                box.label(text="- The new collection will be set in the input :")
                if self.modifier_inputs_list != '':
                    try:
                        match = re.search(r'_([0-9]+)$', self.modifier_inputs_list)
                        if match:
                            input_index = int(match.group(1)) - 1
                        box.label(text="  "+modifier.node_group.interface.items_tree[input_index].name +" (" + self.modifier_inputs_list +")")
                    except:
                        pass
                else:
                    box.label(text="  No input selected")
                if self.modifier_allow_asset_browser:
                    asset_browser_selection_msg = '. Selecting object(s) directly in the Asset Browser is allowed (object types non supported will be ignored).'
                box.separator(factor = 1)

            # DIRTY LAZY CODE START
            count = 0
            size = 40
            message = "- In order to use your modifier the user must select " + target + selection + selection_type + asset_browser_selection_msg
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

        ###########################################################################################
        #           ASSETS DATA
        ###########################################################################################

        count_per_group = len(self.modifier_data_keep_default0)

        items = [[],[],[]]

        # boucle sur tous les inputs du modifier
        export_input_index = 0
        for i,modifier_input in enumerate(modifier.node_group.interface.items_tree):
            # on ignore les outputs et l'input "Geometry" en première position
            if modifier_input.in_out == 'OUTPUT' or modifier_input.identifier == 'Socket_0':
                continue
            
            #type de datablocks autorisés à l'export
            if modifier_input.socket_type not in ['NodeSocketObject' , 'NodeSocketCollection' , 'NodeSocketMaterial']:
                continue

            #récupération du datablock assigné à l'input
            input_datablock = modifier.get(modifier_input.identifier)

            # nom du datablock assigné
            assigned_name = None
            if input_datablock is not None:
                assigned_name = input_datablock.name
            
            # stockage des données utiles
            group_index = floor(export_input_index / count_per_group)
            export_input_index = export_input_index + 1
            items[group_index].append({'input_socket':modifier_input , 'socket_type':modifier_input.socket_type , 'input_datablock_name':assigned_name, 'input_datablock':input_datablock})


        self.modifier_data_export = items

        # variable needed for upcoming dev
        # keep_groups = [self.modifier_data_keep_default0 , self.modifier_data_keep_default1 , self.modifier_data_keep_default2]
        # isasset_groups = [self.modifier_data_is_asset0 , self.modifier_data_is_asset1 , self.modifier_data_is_asset2]

        if self.setdata:
            
            col_but=col.column(align=True)
            col_but.scale_y=1.5
            col_but.prop(self,'data_into_tooltip', text="Info !", icon= 'INFO',toggle = True)
            if self.data_into_tooltip:
                col_info=col.column(align=True)
                col_info.scale_y=0.7
                col_info.separator(factor=1)
                col_info.label(text="Your modifier may contain data (Obj, Mat, Coll).")
                col_info.label(text="You can choose to save these with the modifier.")
                col_info.separator(factor=4)
                col_info.label(text="Legend:")
                col_info.separator(factor=2)
                col_info.label(text="Modifier Inputs:")
                col_info.label(text="   Data = Name of Obj/Mat/Coll currently set in the input.")
                col_info.label(text="   Input = Input name and type.")
                col_info.label(text="   Save = Saves the current input Data.")
                col_info.separator(factor=2)
                col_info.label(text="Default Val:")
                col_info.label(text="   Options to keep or remove default values (Obj/Mat/Coll).")
                col_info.label(text="   Purge = Removes the input's default value.")
                col_info.separator(factor=2)
                col_info.label(text="Is Asset:")
                col_info.label(text="   Marks data currently set in the input as an asset.")
                col_info.label(text="   Preview will NOT be generated!")

                col_info2=col_info.column(align=True)
                col_info2.scale_y=1.42
                col_info2.prop(self, 'data_into_tooltip_plus', text="More info !", icon='INFO', toggle=True)
                if self.data_into_tooltip_plus:
                    col_info.separator(factor=1)
                    col_info.label(text="Data set directly in the node tree")
                    col_info.label(text="will be saved with the Node Tree.")
                    col_info.label(text="")
                    col_info.label(text="Data set in modifier inputs will be")
                    col_info.label(text="saved separately as blend files.")
                    col_info.label(text="They will be stored in the GeoPack.")
                    col_info.label(text="")
                    col_info.label(text="If an object has already been saved (e.g. Cube.001),")
                    col_info.label(text="it will not be saved again (name based).")
                    col_info.label(text="This method prevents duplicate data saving.")
                    col_info.label(text="GeoPack will track each input's data")
                    col_info.label(text="and restore them when the modifier is used.")


            col.separator(factor =2)
            row = col.row(align=True)
            split_ttl = row.split(factor=0.6)
            split_ttl.label(text="Modifier Inputs") # INPUT NAME
            row_ttl2 = split_ttl.row(align=True)
            
            split_ttl2 = row_ttl2.split(factor=0.55)
            split_ttl2.label(text="Default Val") # INPUT SAVE DEFAULT VALUE
            split_ttl2.label(text="Is Asset")
            col.separator(factor =0.5)
            for g,group in enumerate(items):
                for i, item in enumerate(group):
                    
                    row_main = col.row(align=True) # MAIN
                    split_main = row_main.split(factor=0.6)

                    rowsub1 = split_main.row(align=True) # SUB 1
                    split1 = rowsub1.split(factor=0.82)
                    co_detail = split1.column(align=True)
                    co_detail.scale_y=0.6
                    co_detail.label(text="Data:  "+ str(item['input_datablock_name']))
                    co_detail.label(text= "Input: "+ item['input_socket'].name +" ("+item['socket_type'].replace('NodeSocket','') +") ") # + str(item['input_datablock_name'])
                    split1.prop(self,f"modifier_data_export_items{g}", index=i, text="Save",toggle = True)
                    
                    rowsub2 = split_main.row(align=False) # SUB 2
                    split2 = rowsub2.split(factor=0.6)
                    split2.prop(self,f"modifier_data_keep_default{g}",index=i, text="Purge",toggle = True)

                    split2.prop(self,f"modifier_data_is_asset{g}", index=i, text="", icon='ASSET_MANAGER')
                    col.separator(factor =0.4)
                    
    def get_objects_in_collection(self,collection_name):
        """Récupère tous les objets d'une collection et de ses sous-collections."""
        objects = []

        def recurse_collection(collection):
            for obj in collection.objects:
                objects.append(obj)
            for subcol in collection.children:
                recurse_collection(subcol)

        # IF COLL EXISTE
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]
            recurse_collection(collection)

        return objects
    
    def write_asset_file(self,destination_folder , element,mark_asset):
        #datablock_filename = f'{sanitize_filename(element["input_datablock_name"])}.blend'
        datablock_filename = f'{sanitize_filename(element.name)}.blend'

        assets_folder_path = os.path.join(destination_folder,'Assets')

        if not os.path.isdir(assets_folder_path):
            # création du dossier des Asset s'il n'existe pas déjà
            prefs = bpy.context.preferences
            filepaths = prefs.filepaths
            asset_libraries = filepaths.asset_libraries
            os.mkdir(assets_folder_path)

            pack_config = os.path.join(destination_folder,'geopack.config')
            with open(pack_config) as f:
                pack_data = json.loads(f.read())

            # Ajoute le nouveau dossier comme une bibliothèque d'actifs
            bpy.ops.preferences.asset_library_add(directory=assets_folder_path)
            asset_libraries[len(asset_libraries)-1].name = pack_data['name']

        datablock_filepath = os.path.join(assets_folder_path,datablock_filename)
                            
        if not os.path.isfile(datablock_filepath):
            
            is_already_asset = element.asset_data is not None
            if mark_asset:
                element.asset_mark()
            
            bpy.data.libraries.write(filepath = datablock_filepath , datablocks = {element} , fake_user = True , compress = True)
            
            if not is_already_asset and mark_asset:
                element.asset_clear()

        return datablock_filename

    def render_scatter_icon_for_active_obj(self, filepath):
        print("Generate Preview : True")
        pref = Get_addon_pref()
        original_scene = bpy.context.scene
        preview_scene = None
        camera_data = bpy.data.cameras.new(name="ScatterPreviewCam")
        camera = bpy.data.objects.new("ScatterPreviewCam", camera_data)

        try:# Needed in case of error
        # === OBJET SELECTED ===
            obj = bpy.context.active_object
            debug("OBJECT : " + obj.name)

        # === SCATTER MODIFIER ===
            scatter_mod = None
            for mod in obj.modifiers:
                if mod.type == 'NODES' and "Scatter" in mod.name:
                    scatter_mod = mod
                    break
            if scatter_mod == None:
                print("[GeoPack] No scatter modifier on the object.")
                return
            debug("Scatter Modifier Succeed")

        # === SCENE TEMPORAIRE ===
            preview_scene = bpy.data.scenes.new("ScatterPreview")
            bpy.context.window.scene = preview_scene
            debug("Temp Scene Succeed")

        # === LINK OBJ COPY ===
            obj_copy = obj.copy()
            obj_copy.data = obj.data.copy()
            obj_copy.modifiers.clear()
            mod = obj_copy.modifiers.new(name=scatter_mod.name, type='NODES')
            mod.node_group = scatter_mod.node_group
            preview_scene.collection.objects.link(obj_copy)
            debug("Link Object Copy Succeed")

        # === CAMERA FROM CURRENT VIEW ===
            preview_scene.collection.objects.link(camera)
            preview_scene.camera = camera
            bpy.context.view_layer.objects.active = camera
            bpy.ops.view3d.camera_to_view()

            focal_found = False
            if pref.geopack_render_use_current_focal:
                for area in bpy.context.screen.areas:
                    if area.type == 'VIEW_3D':
                        for space in area.spaces:
                            if space.type == 'VIEW_3D':
                                camera_data.lens = space.lens
                                focal_found = True
                                break
                        if focal_found:
                            break

            if not focal_found or pref.geopack_render_use_current_focal:
                camera_data.lens = pref.geopack_render_focal
            debug("Camera From Current View Succeed")

        # === SKY LIGHT SIMPLE ===
            if pref.geopack_render_use_current_world == False:
                world = bpy.data.worlds.new("PreviewWorld")
                world.use_nodes = True
                ntree = world.node_tree
                ntree.nodes.clear()

                bg = ntree.nodes.new("ShaderNodeBackground")
                sky = ntree.nodes.new("ShaderNodeTexSky")
                sky.sky_type = 'NISHITA' if bpy.app.version < (5, 0, 0) else 'SINGLE_SCATTERING'
                out = ntree.nodes.new("ShaderNodeOutputWorld")

                ntree.links.new(sky.outputs[0], bg.inputs[0])
                ntree.links.new(bg.outputs[0], out.inputs[0])

                sky.sun_rotation = -camera.rotation_euler.z - math.radians(pref.geopack_render_sunrot)
                preview_scene.world = world
                sky.sun_elevation = math.radians(pref.geopack_render_sunelev)
                sky.ozone_density = pref.geopack_render_ozone
                sky.sun_intensity = pref.geopack_render_sunint
                debug("Lignting using new world succeed")
            else:
                preview_scene.world = original_scene.world
                debug("Lignting from current scene succeed")

        # === RENDER SETTINGS ===
            preview_scene.render.engine = 'CYCLES'
            preview_scene.cycles.samples = pref.geopack_render_samples
            preview_scene.render.resolution_x = pref.geopack_render_resolution
            preview_scene.render.resolution_y = pref.geopack_render_resolution
            preview_scene.render.image_settings.file_format = 'PNG'
            preview_scene.render.film_transparent = True
            if pref.geopack_render_use_current_world == False:
                exposure = pref.geopack_render_exposure
            else:
                exposure = original_scene.view_settings.exposure
            preview_scene.view_settings.exposure = exposure
            debug("Render settings succeed")

        # === TEMP FILE OUTPUT ===
            icon_name = self.modifier_name + ".png"
            render_dir = os.path.dirname(filepath)  # dossier contenant le .blend
            render_path = os.path.join(render_dir, icon_name)

            preview_scene.render.filepath = render_path
            debug("Render Path succeed")

        # === RENDER ===
            bpy.ops.render.render(write_still=True, scene=preview_scene.name)
            debug("Render Succeed")

        # === SET ICON ===
            import_icons()
            debug("Import Icons Succeed")

            # === CLEANUP ===
            bpy.ops.view3d.view_camera()
            bpy.context.window.scene = original_scene
            bpy.data.objects.remove(camera)
            bpy.data.cameras.remove(camera_data)
            if pref.geopack_render_use_current_world == False:
                bpy.data.worlds.remove(world)
            else:
                preview_scene.world = None
            bpy.data.scenes.remove(preview_scene)
            tpe = obj_copy.type
            data = obj_copy.data
            bpy.data.objects.remove(obj_copy, do_unlink=True)
            if tpe == 'MESH':
                bpy.data.meshes.remove(data, do_unlink=True)
            elif tpe == 'CURVE':
                bpy.data.curves.remove(data, do_unlink=True)
            
            print("Generate Preview : Success")

        except:
            print(f"GeoPack: Render failed. Can be set manually in Pref > Addon > BagaPie > GeoPack > [your pack] > Modifier")

            # === RESTORE CLEAN CONTEXT ===
            bpy.context.window.scene = original_scene
            if preview_scene:
                if camera:
                    bpy.data.objects.remove(camera, do_unlink=True)
                if camera_data:
                    bpy.data.cameras.remove(camera_data, do_unlink=True)
                bpy.data.scenes.remove(preview_scene)
            if 'world' in locals() and pref.geopack_render_use_current_world == False:
                bpy.data.worlds.remove(world)
            if 'obj_copy' in locals():
                tpe = obj_copy.type
                data = obj_copy.data
                bpy.data.objects.remove(obj_copy, do_unlink=True)
                if tpe == 'MESH':
                    bpy.data.meshes.remove(data, do_unlink=True)
                elif tpe == 'CURVE':
                    bpy.data.curves.remove(data, do_unlink=True)
        
    def save_group(self,context,destination_folder,data):
        node_group = get_active_geometry_node_modifier() #get_active_geometry_node()

        obj = context.active_object
        custom_props = []
        if obj.bagapieList is not None:
            for value in obj.bagapieList:
                val = json.loads(value['val'])
                if val.get('name') == 'scatter':
                    custom_props.append(val)

        depsgraph = context.evaluated_depsgraph_get()
        node_group_eval = node_group.id_data.evaluated_get(depsgraph)
        node_tree_eval = node_group_eval.id_data
        node_tree_eval.use_fake_user = True

        nodes = list(node_tree_eval.nodes)

        filepath = os.path.join(destination_folder,f'{sanitize_filename(self.modifier_name)}.blend')

        linked_groups = [
            node.node_tree
            for node in nodes
            if node.type == 'GROUP' and node.node_tree.library
        ]
        
        previous_data = obj.data
        mesh_data = None

        # export data assets
        modifiers = obj.modifiers
        modifier = modifiers.active if obj.modifiers else None
        items_data = data.get('assets_data',[])
        default_values = {}
        
        bool_groups = [self.modifier_data_export_items0 , self.modifier_data_export_items1 , self.modifier_data_export_items2] # SAVE
        keep_groups = [self.modifier_data_keep_default0 , self.modifier_data_keep_default1 , self.modifier_data_keep_default2] # PURGE
        isasset_groups = [self.modifier_data_is_asset0,self.modifier_data_is_asset1,self.modifier_data_is_asset2] # IS ASSET

        for g, export_group in enumerate(self.modifier_data_export):
            for i, element in enumerate(export_group):

                datab_name = element['input_datablock_name']
                if bool_groups[g][i] == False:
                    datab_name = None

                item = {
                    "socket_name":element['input_socket'].name,
                    "socket_identifier":element['input_socket'].identifier,
                    "socket_type":element['socket_type'],
                    "datablock_name":datab_name # Current data name set in the input (eg coll.name)
                }

                sub_assets = []
                if bool_groups[g][i] == True and element['input_datablock'] is not None:

                    mark_asset = isasset_groups[g][i]

                    # cas spécial des collections, sauvegarde des sous éléments
                    if element['socket_type'] == 'NodeSocketCollection':
                        sub_assets = self.get_objects_in_collection(element['input_datablock'].name)

                        if len(sub_assets) > 0:
                            item['sub_assets'] = [sb.name for sb in sub_assets]
                            item['sub_assets_files'] = []
                            for sb in sub_assets:
                                item['sub_assets_files'].append(self.write_asset_file(destination_folder , sb,mark_asset))

                    elif element['input_datablock'] is not None:
                        # sauvegarde de l'asset
                        item['filename'] = self.write_asset_file(destination_folder , element['input_datablock'],mark_asset)

                items_data.append(item)

                # mémorisation de la default value de l'input
                default_values[element['input_socket'].identifier] = element['input_socket'].default_value

                # remove input default value if purge is True
                if keep_groups[g][i] == True:
                    element['input_socket'].default_value = None

                # remove modifier input content
                modifier[element['input_socket'].identifier] = None

                print("Input : " + element['input_socket'].name)
                print("Purge : "+str(keep_groups[g][i]))
                print("Default Value  : "+str(element['input_socket'].default_value))
                print("Save Input Val : "+str(bool_groups[g][i]))
                print("Modifier Value : "+str(modifier[element['input_socket'].identifier]))

        data['assets_data'] = items_data
        #----------------------------

        if obj.type == "MESH":
            mesh_data = bpy.data.meshes.new(name="EmptyMesh")
            obj.data = mesh_data
        
        if obj.type == "CURVE":
            mesh_data = bpy.data.curves.new(name="EmptyCurve", type='CURVE')
            obj.data = mesh_data
        
        if obj.type == "CURVES":
            mesh_data = bpy.data.hair_curves.new(name="EmptyHairCurve")
            obj.data = mesh_data
        
        # REMOVE SCATTER NODE CONTENT
        no_effect_and_cull = []
        if self.is_scatter == True:
            nodes = modifier.node_group.nodes
            for no in nodes:
                if no.type == 'GROUP':
                    name = no.node_tree.name
                    label = no.label
                    if (
                        name.startswith("BagaPie_Effector") or 
                        label.startswith("BagaPie_Effector") or 
                        name.startswith("BagaPie_Camera_Culling") or 
                        label.startswith("BagaPie_Camera_Culling")
                    ):
                        node_tree = no.node_tree
                        no.node_tree = None
                        no_effect_and_cull.append([no, node_tree])

        # EXPORT NODE TREE
        export_set = set([obj])
        bpy.data.libraries.write(filepath=filepath, datablocks=export_set, fake_user=True,compress=True)



        # RESTORE SCATTER NODE CONTENT
        if self.is_scatter == True:
            for no, node_tree in no_effect_and_cull:
                no.node_tree = node_tree



        obj.data = previous_data

        if obj.type == "MESH":
            bpy.data.meshes.remove(mesh_data)
        
        if obj.type == "CURVE":
            bpy.data.curves.remove(mesh_data)

        if obj.type == "CURVES":
            bpy.data.hair_curves.remove(mesh_data)
        #---------------------------------

        path_no_ext = os.path.splitext(filepath)[0]

        json_file = f"{path_no_ext}.json"
        
        data['info']['group_name'] = node_tree_eval.name

        data['custom_prop'] = custom_props

        with open(json_file, 'w') as f:
            f.write(json.dumps(data, indent=4))

        # Unlink all linked node groups
        for group in linked_groups:
            group.user_clear()

        #restore assets in inputs
        for g,export_group in enumerate(self.modifier_data_export):
            for i, element in enumerate(export_group):
                element['input_socket'].default_value = default_values[element['input_socket'].identifier] # DEFAULT VALUE
                modifier[element['input_socket'].identifier] = element['input_datablock'] # MODIFIER INPUT
        
        
        if self.is_scatter == True:
            pref = Get_addon_pref()
            if pref.geopack_render_generate == True:
                self.render_scatter_icon_for_active_obj(filepath=filepath)

    def execute(self, context):
        if self.cancel:
            Warning(message = "New modifier cancelled !", title = "Cancel Modifier", icon = 'ERROR')
            return {'CANCELLED'}
        
        geopack = self.modifier_geopack

        data = {}

        info = {}
        info['format_version'] = self.modifier_file_format_version
        info['name'] = self.modifier_name
        info['author'] = self.modifier_author
        info['description'] = self.modifier_description
        info['version'] = self.modifier_version
        info['blender_version'] = self.modifier_blender_version
        info['contact'] = self.modifier_contact
        info['url'] = self.modifier_url
        info['license'] = self.modifier_license

        usage = {}
        # OBJE TYPE
        usage['active_target'] = self.modifier_active_target

        # MESH ADD HAIR CURVES
        usage['add_hair_curves'] = self.modifier_add_hair_curves
        if self.modifier_add_hair_curves:
            usage['hair_curves_length']=self.modifier_add_hair_curves_length
            usage['hair_curves_points_count']=self.modifier_add_hair_curves_points_count
            usage['hair_curves_count']=self.modifier_add_hair_curves_count
        
        # MESH SWITCH WEIGHT PAINT
        usage['mesh_paint_mode'] = self.modifier_mesh_paint_mode
        usage['paint_v_group_name'] = self.modifier_mesh_paint_v_group_name
        usage['paint_inputs_list'] = self.modifier_weight_paint_inputs_list

        # ADD CURVE AND DRAW
        usage['add_curve_and_draw'] = self.modifier_add_curve_with_draw_mode
        usage['object_input'] = self.modifier_object_inputs_list
        usage['object_name'] = self.modifier_object_name

        # USE SELECTION
        usage['use_selection'] = self.modifier_use_selection
        usage['asset_browser'] = self.modifier_allow_asset_browser
        usage['selection_types'] = []
        if self.modifier_selection_type_mesh:
            usage['selection_types'].append('MESH')
        if self.modifier_selection_type_curve:
            usage['selection_types'].append('CURVE')
        if self.modifier_selection_type_camera:
            usage['selection_types'].append('CAMERA')
        if self.modifier_selection_type_empty:
            usage['selection_types'].append('EMPTY')
        if self.modifier_selection_type_text:
            usage['selection_types'].append('TEXT')
        if self.modifier_selection_type_volume:
            usage['selection_types'].append('VOLUME')
        if self.modifier_selection_type_light:
            usage['selection_types'].append('LIGHT')
        usage['coll_name'] = self.modifier_coll_name
        usage['coll_input'] = self.modifier_inputs_list

        # NEW OBJECT
        if usage['active_target'] == 'NEW':
            usage['new_object_type'] = self.modifier_new_obj_type

            if usage['new_object_type'] == 'MESH':
                usage['new_mesh_add_cube'] = self.modifier_new_mesh_add_cube

            if usage['new_object_type'] == 'CURVE':
                usage['new_curve_draw'] = self.modifier_new_curve_draw
                usage['new_curve_draw_dimension'] = self.modifier_new_curve_draw_dimension
                usage['new_curve_draw_mode'] = self.modifier_new_curve_draw_mode

        data['info'] = info
        data['usage'] = usage

        pref = Get_addon_pref()

        pack = pref.GetGeopack(geopack)
        
        if pack:
            self.save_group(context,pack.path,data)
            pack.scan_modifiers()
            Warning(message = "New modifier added !", title = "New Modifier", icon = 'INFO')
        else:
            Warning(message = "New modifier NOT added ! Pack not found", title = "Error", icon = 'INFO')

        bpy.ops.bagapie.refresh_icons() # Can be removes once the remove modifier properly remove Icons

        return {'FINISHED'}
    

classes = [
    BAGAPIE_OT_geopack_create,
    BAGAPIE_OT_geopack_assign_modifier,
    BAGAPIE_OT_geopack_create_modifier,
    BAGAPIE_MT_geopack_select_modifier,
    BAGAPIE_OT_geopack_delete,
    BAGAPIE_OT_geopack_modifier_delete,
    BAGAPIE_OT_geopack_assetbrowser
]