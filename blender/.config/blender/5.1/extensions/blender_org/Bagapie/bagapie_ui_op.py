import bpy
import json
from bpy.types import Operator
import os
from .utils import Get_addon_pref, Warning
from pathlib import Path

# These classes are used to call some existing operator from the addon panel.
# Some of them may looks stupid and some of them makes sense.

class SwitchMode(Operator):
    """Edit the painting of the last instantiated object"""
    bl_idname = "switch.mode"
    bl_label = "Switch Object Mode"
    def execute(self, context):

        obj = context.object
        val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
        modifiers = val['modifiers']
        scatt_vertex_grp = modifiers[2]

        vertex_group = obj.vertex_groups
        vertex_group.active_index = vertex_group[scatt_vertex_grp].index

        bpy.ops.paint.weight_paint_toggle()
        return {'FINISHED'}

class EditMode(Operator):
    """Switch Object Mode"""
    bl_idname = "bool.mode"
    bl_label = "Switch Object Mode"
    def execute(self, context):

        try:
            obj = context.object
            val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
            type = val['name']
            modifiers = val['modifiers']

            if type == 'boolean':
                bpy.ops.object.select_all(action='DESELECT')
                bool_obj = bpy.data.objects[modifiers[5]]
                bpy.context.view_layer.objects.active = bool_obj
                if bpy.context.object.mode == 'OBJECT':
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.wm.tool_set_by_id(name="builtin.primitive_cube_add")
                elif bpy.context.object.mode == 'EDIT':
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                    bpy.ops.object.editmode_toggle()

            else:
                if bpy.context.object.mode == 'OBJECT':
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.wm.tool_set_by_id(name="builtin.primitive_cube_add")
                elif bpy.context.object.mode == 'EDIT':
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                    bpy.ops.object.editmode_toggle()

        except:
            if bpy.context.object.mode == 'OBJECT':
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.wm.tool_set_by_id(name="builtin.primitive_cube_add")
            elif bpy.context.object.mode == 'EDIT':
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                bpy.ops.object.editmode_toggle()

        return {'FINISHED'}

class UseSolidify(Operator):
    """Enable/Disable Solidify Modifier"""
    bl_idname = "solidify.visibility"
    bl_label = "Switch Object Mode"
    def execute(self, context):

        obj = context.object
        val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
        modifiers = val['modifiers']        
        
        solidify_modifier = bpy.data.objects[modifiers[5]].modifiers[modifiers[4]]

        if not solidify_modifier.show_viewport:
            solidify_modifier.show_viewport=True
            solidify_modifier.show_render=True
            solidify_modifier.show_in_editmode=True
        else:
            solidify_modifier.show_viewport=False
            solidify_modifier.show_render=False
            solidify_modifier.show_in_editmode=False

        return {'FINISHED'}

class InvertPaint(Operator):
    """Invert paint brush influence"""
    bl_idname = "invert.paint"
    bl_label = "Invert Weight Paint"
    def execute(self, context):
        
        if bpy.app.version >= (5, 0, 0):
            weight = bpy.context.scene.tool_settings.weight_paint.brush.weight
            bpy.context.scene.tool_settings.weight_paint.brush.weight = weight*(-1)+1
        else:
            weight = bpy.context.scene.tool_settings.unified_paint_settings.weight
            bpy.context.scene.tool_settings.unified_paint_settings.weight = weight*(-1)+1
        return {'FINISHED'}

class InvertWeight(Operator):
    """Invert paint"""
    bl_idname = "invert.weight"
    bl_label = "Invert Weight Value"
    def execute(self, context):
        bpy.ops.object.vertex_group_invert()
        return {'FINISHED'}

class CleanWPaint(Operator):
    """Lift all the painting"""
    bl_idname = "clean.paint"
    bl_label = "Clean Weight Paint"
    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_remove_from(use_all_groups=False)
        bpy.ops.paint.weight_paint_toggle()
        
        if bpy.app.version >= (5, 0, 0):
            weight = bpy.context.scene.tool_settings.weight_paint.brush.weight
        else:
            weight = bpy.context.scene.tool_settings.unified_paint_settings.weight
        if weight < 1:
            bpy.ops.invert.paint()
        return {'FINISHED'}

class SetupAssetBrowser(Operator):
    """Add BagaPie's parametric presets library in the asset browser"""
    bl_idname = "bagapie.parametricpresets"
    bl_label = "Install BagaPie's Parametric Library CC0"

    tool_update: bpy.props.BoolProperty(default=False) # type: ignore

    def execute(self, context):
        # GET THE ASSETS PATH
        file_path = Get_Addon_Path(self, context)
        file_path = file_path.replace("__init__.py","")

        prefs = bpy.context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries

        TEMP_FILE = os.path.join(bpy.app.tempdir, "bagapie_restart_flag.txt")
        with open(TEMP_FILE, "w") as f:
            f.write("restart_blender_required")

        add = True
        for lib in asset_libraries:
            if lib.name == "BagaPie Modifier":
                
                library_path = Path(lib.path)
                target_blend_file = library_path / "BagaPie_Nodes_Tools.blend"

                if not target_blend_file.is_file():
                    lib.path = file_path
                    print("Parametric Library Path Updated")

                if self.tool_update:
                    Warning(message = "Now Restart Blender !", title = "INFO", icon = 'INFO')
                else:
                    Warning(message = "The library is already installed.", title = "INFO", icon = 'INFO')
                add = False
        if add:
            bpy.ops.preferences.asset_library_add(directory = file_path)
            asset_libraries[len(asset_libraries)-1].name = "BagaPie Modifier"
            if self.tool_update:
                Warning(message = "Library installed ! Now Restart Blender !", title = "INFO", icon = 'INFO')
            else:
                Warning(message = "Library installed ! It's now visible in your libraries.", title = "Done !", icon = 'INFO')
        
        return {'FINISHED'}

class SetupAssetBrowserForAssets(Operator):
    """Add BagaPie's parametric presets library in the asset browser"""
    bl_idname = "bagapie.assetsdatabase"
    bl_label = "Install BagaPie Assets as Asset Library"
    def execute(self, context):
        
        # GET THE ASSETS PATH
        file_path = os.path.dirname(__file__)


        prefs = bpy.context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries
        bagapie_pref = Get_addon_pref()
        use_custom_location = bagapie_pref.use_custom_location

        if use_custom_location:
            file_path = bagapie_pref.assets_path
        else:
            file_path = file_path.replace("__init__.py","")

        add = True
        for lib in asset_libraries:
            if lib.name == "BagaPie Assets":
                Warning(message = "The library is already installed.", title = "INFO", icon = 'INFO')
                add = False
                if lib.path != file_path:
                    Warning(message = "Library location updated !.", title = "INFO", icon = 'INFO')
                lib.path = file_path

        if add:
            bpy.ops.preferences.asset_library_add(directory = file_path)
            asset_libraries[len(asset_libraries)-1].name = "BagaPie Assets"
            Warning(message = "Library installed ! It's now visible in your libraries.", title = "Done !", icon = 'INFO')
        
        return {'FINISHED'}

class ADD_Assets(Operator):
    """Add asset to the current scatter layer"""
    bl_idname = "add.asset"
    bl_label = "Add Asset"
    def execute(self, context):
        
        target = bpy.context.active_object
        assets = bpy.context.selected_objects
        if len(assets) < 1:
            Warning(message = "Select your asset(s) then and the surface with the Scatter Layer to add the asset to.", title = "No asset selected.", icon = 'INFO')
            return {'FINISHED'}
        if target not in assets:
            Warning(message = "Select your surface with the Scatter Layer to add the asset to.", title = "No surface/scatter selected.", icon = 'INFO')
            return {'FINISHED'}
        assets.remove(target)

        nodegroup = target.modifiers.get("BagaPie_Scatter").node_group
        index = target.bagapieIndex
        val = json.loads(target.bagapieList[index]['val'])
        modifiers = val['modifiers']
        scatter_node = nodegroup.nodes.get(modifiers[1])

        if scatter_node.label != "BagaPie_Scatter":
            Warning("You must select a Scatter layer.", "WARNING", 'ERROR') 
            return {'FINISHED'}

        scatter_collection = scatter_node.inputs[1].default_value

        for asset in assets:
            if asset.name not in scatter_collection.objects:
                scatter_collection.objects.link(asset)
        
        return {'FINISHED'}

class REMOVE_Assets(Operator):
    """Remove asset to the current scatter layer"""
    bl_idname = "remove.asset"
    bl_label = "Remove Asset"
    def execute(self, context):
        
        target = bpy.context.active_object
        assets = bpy.context.selected_objects
        if len(assets) < 1:
            Warning(message = "Select your asset(s) then and the surface with the Scatter Layer to remove the asset to.", title = "No asset selected.", icon = 'INFO')
            return {'FINISHED'}
        assets.remove(target)

        nodegroup = target.modifiers.get("BagaPie_Scatter").node_group
        index = target.bagapieIndex
        val = json.loads(target.bagapieList[index]['val'])
        modifiers = val['modifiers']
        scatter_node = nodegroup.nodes.get(modifiers[1])

        if scatter_node.label != "BagaPie_Scatter":
            Warning("You must select a Scatter layer.", "WARNING", 'ERROR') 
            return {'FINISHED'}

        scatter_collection = scatter_node.inputs[1].default_value

        not_in_selected_layer = True
        for asset in assets:
            if asset.name in scatter_collection.objects:
                not_in_selected_layer = False
                scatter_collection.objects.unlink(asset)

        if not_in_selected_layer:
            Warning(message = "Asset(s) not in the selected Layer", title = "Wrong layer selected", icon = 'INFO')
            return {'FINISHED'}
        
        return {'FINISHED'}
        
class Rename_Layer(Operator):
    """Rename the current modifier layer"""
    bl_idname = "rename.layer"
    bl_label = "Rename Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_name: bpy.props.StringProperty(default="None")

    def invoke(self, context, event):
        wm = context.window_manager
        bpy.context.scene['Layer_Name'] = "None"
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'layer_name', text = "New name")

    def execute(self, context):
        
        target = bpy.context.active_object
        index = target.bagapieIndex
        val = json.loads(target.bagapieList[index]['val'])
        modifiers = val['modifiers']
        context.object.bagapieList.remove(index)
        val = {
            'name': 'scatter',
            'modifiers':[
                        modifiers[0],  # MODIFIER NAME
                        modifiers[1],
                        modifiers[2],
                        self.layer_name #bpy.context.scene['Layer_Name'],  # LAYER NAME
                        ]
        }

        # Rename Collection
        nodegroup = target.modifiers.get("BagaPie_Scatter").node_group
        modifiers = val['modifiers']
        scatter_node = nodegroup.nodes.get(modifiers[1])
        scatter_collection = scatter_node.inputs[1].default_value
        scatter_collection.name = self.layer_name

        item = target.bagapieList.add()
        item.val = json.dumps(val)
        target.bagapieIndex = len(target.bagapieList)-1
        
        return {'FINISHED'}

def gn_bool_version(value):
    if value == 1:
        if bpy.app.version < (3, 5, 0):
            value = 1
        else:
            value = True
    else:        
        if bpy.app.version < (3, 5, 0):
            value = 0
        else:
            value = False
    return value

class SwitchBoolCustom(Operator):
    """Switch the selected input, only for Bool"""
    bl_idname = "switch.boolcustom"
    bl_label = "Switch Bool Custom"

    index: bpy.props.StringProperty(name="None")
    modifier: bpy.props.StringProperty(name="None")

    def execute(self, context):

        obj = context.object
        modifier = obj.modifiers[self.modifier]
        if modifier[self.index] == gn_bool_version(1):
            modifier[self.index] = gn_bool_version(0)
        else:
            modifier[self.index] = gn_bool_version(1)
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        
        return {'FINISHED'}

class SelectLayerContent(Operator):
    """Select assets from the active scatter layer"""
    bl_idname = "select.content"
    bl_label = "Select assets layer"

    index: bpy.props.StringProperty(name="None")
    modifier: bpy.props.StringProperty(name="None")

    def execute(self, context):

        target = bpy.context.active_object
        nodegroup = target.modifiers.get("BagaPie_Scatter").node_group
        index = target.bagapieIndex
        val = json.loads(target.bagapieList[index]['val'])
        modifiers = val['modifiers']
        scatter_node = nodegroup.nodes.get(modifiers[1])
        scatter_collection = scatter_node.inputs[1].default_value

        for asset in scatter_collection.objects:
            asset.select_set(True)

        return {'FINISHED'}

class BAGAPIE_OT_add_remove_target(Operator):
    """ Add/Remove object to the modifier target """
    bl_idname = "bagapie.add_remove_target"
    bl_label = 'Add Remove Target'
    bl_options = {'REGISTER', 'UNDO'}

    socket: bpy.props.StringProperty(default='NONE', options={'HIDDEN'}) # type: ignore
    mode: bpy.props.BoolProperty(default=True, options={'HIDDEN'}) # type: ignore

    @classmethod
    def poll(cls, context):
        o = context.object
        return (
            o is not None
        )
    def execute(self, context):
        obj = context.object
        objs = context.selected_objects

        if obj.bagapieIndex < len(obj.bagapieList):
            val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
            modifiers = val['modifiers']
            modifier = obj.modifiers[modifiers[0]]
            coll = modifier[self.socket]
            if self.mode:
                for o in objs:
                    if o.name not in coll.objects and o != obj:
                        coll.objects.link(o)
            else:
                for o in objs:
                    if o.name in coll.objects and o != obj:
                        coll.objects.unlink(o)
        return {'FINISHED'}

def add_remove_ui(layout, socket):
    box=layout.box()
    row=box.row()
    row.label(text="Targets :")
    tips = row.operator("bagapie.tooltips", text="", depress = False, icon = 'INFO')
    tips.message = "Targets are objects the modifier interacts with. To add/remove them, select the objects, then reselect the object with the modifier."

    row = box.row(align=True)
    row.scale_y = 1.3
    addremove = row.operator('bagapie.add_remove_target', text='Add', depress = False, icon='ADD')
    addremove.socket = socket
    addremove.mode = True
    addremove = row.operator('bagapie.add_remove_target', text='Remove', depress = False, icon='ADD')
    addremove.socket = socket
    addremove.mode = False

def Get_Addon_Path(self, context):
    filepath = os.path.dirname(__file__)
    return filepath

def Draw_Scatter_Layer_Content(layout, scatter_modifier):
    box = layout.box()
    box.label(text="Assets in this Layer:")
    col = box.column(align=True)
    coll = scatter_modifier.inputs[1].default_value
    if coll and isinstance(coll, bpy.types.Collection):
        for ob in coll.objects:
            row = col.row(align=True)
            row.label(text=ob.name, icon='OBJECT_DATA')

            op = row.operator("bagapie.select_asset", text="", icon='RESTRICT_SELECT_OFF', depress = ob.select_get())
            op.asset_name = ob.name

            icon_bounds = 'SHADING_BBOX' if ob.display_type != 'BOUNDS' else 'SNAP_FACE'
            op_bounds = row.operator("object.display_as_bounds_toggle", text="", icon=icon_bounds, depress= False if ob.display_type != 'BOUNDS' else True)
            op_bounds.name = ob.name

            proxy_found = False
            proxy_mod = None
            for mod in ob.modifiers:
                if mod.name.startswith("BagaPie_Proxy") or (mod.type == 'NODES' and mod.node_group and mod.node_group.name.startswith("BagaPie_Proxy")):
                    proxy_found = True
                    proxy_mod = mod
                    break

            if proxy_found:
                op_proxy_toggle = row.operator("bagapie.proxy_toggle_from_ui", text="", icon='MESH_ICOSPHERE', depress= True if proxy_mod.show_viewport else False)
                op_proxy_toggle.obj_name = ob.name
                op_proxy_toggle.modifier_name = proxy_mod.name

            else:
                op_add_proxy = row.operator("bagapie.proxy_add_from_ui", text="", icon='MESH_ICOSPHERE')
                op_add_proxy.obj_name = ob.name

            op = row.operator("bagapie.remove_asset_from_layer", text="", icon="X")
            op.asset_name = ob.name
            op.collection_name = coll.name

class BAGAPIE_PT_asset_browser_tools(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "BagaPie Scatter Tools"
    bl_category = "Asset"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.space_data.browse_mode == 'ASSETS'

    def draw(self, context):
        layout = self.layout
        obj = context.object
        if obj and obj.type == 'MESH':
            col = layout.column()
            col.scale_y=2
            col.operator("bagapie.asset_browser", text="Scatter Selection", icon = "GEOMETRY_NODES").import_mode= 'Scatter'

            col = layout.column()
            if obj.bagapieIndex < len(obj.bagapieList):
                val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
                mo_type = val['name']
                modifiers = val['modifiers']
                if mo_type == "scatter":
                    col = layout.column(align=True)
                    col2=col.column(align=True)
                    col2.scale_y=2
                    col2.operator("bagapie.asset_browser", text="Add Assets to layer :", icon='ADD').import_mode = 'AddAssets'
                    col.template_list("BAGAPIE_UL_List", "The_List", obj,
                                    "bagapieList", obj, "bagapieIndex")
                    
                    col.operator("rename.layer", text= "Rename Layer", icon = 'GREASEPENCIL')

                    scatter_modifier = obj.modifiers[modifiers[0]].node_group.nodes[modifiers[1]]
                    col.prop(scatter_modifier.inputs[2], 'default_value', text = "Distance Min")
                    col.prop(scatter_modifier.inputs[3], 'default_value', text = "Density Max")
                    row = col.row(align=True)
                    row.prop(scatter_modifier.inputs[9], 'default_value', text = "Scale Min")
                    row.prop(scatter_modifier.inputs[10], 'default_value', text = "Scale Max")
                    col.prop(scatter_modifier.inputs[14], 'default_value', index=2, text="Random Rot Z")

                    Draw_Scatter_Layer_Content(layout, scatter_modifier)

class BAGAPIE_OT_remove_asset_from_layer(bpy.types.Operator):
    bl_idname = "bagapie.remove_asset_from_layer"
    bl_label = "Remove Asset from Layer"
    bl_options = {'REGISTER', 'UNDO'}

    asset_name: bpy.props.StringProperty() # type: ignore
    collection_name: bpy.props.StringProperty() # type: ignore

    def execute(self, context):
        coll = bpy.data.collections.get(self.collection_name)
        if coll and self.asset_name in coll.objects:
            coll.objects.unlink(coll.objects[self.asset_name])
        return {'FINISHED'}

class BAGAPIE_OT_select_asset(bpy.types.Operator):
    bl_idname = "bagapie.select_asset"
    bl_label = "Select Asset in View"
    bl_options = {'REGISTER', 'UNDO'}

    asset_name: bpy.props.StringProperty() # type: ignore

    def execute(self, context):
        obj = bpy.data.objects.get(self.asset_name)
        if obj:
            obj.select_set(True)
        return {'FINISHED'}

class BAGAPIE_OT_proxy_toggle_from_ui(bpy.types.Operator):
    """Toggle Proxy Modifier visibility"""
    bl_idname = "bagapie.proxy_toggle_from_ui"
    bl_label = "Toggle Proxy Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: bpy.props.StringProperty() # type: ignore
    modifier_name: bpy.props.StringProperty() # type: ignore

    def execute(self, context):
        obj = bpy.data.objects.get(self.obj_name)
        if not obj:
            return {'CANCELLED'}
        mod = obj.modifiers.get(self.modifier_name)
        if not mod:
            return {'CANCELLED'}
        mod.show_viewport = not mod.show_viewport
        return {'FINISHED'}

class OBJECT_OT_display_as_bounds_toggle(bpy.types.Operator):
    """Toggle object display as BOUNDS"""
    bl_idname = "object.display_as_bounds_toggle"
    bl_label = "Toggle Bounds Display"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty() # type: ignore

    def execute(self, context):
        obj = bpy.data.objects.get(self.name)
        if obj:
            obj.display_type = 'BOUNDS' if obj.display_type != 'BOUNDS' else 'TEXTURED'
        return {'FINISHED'}

class BAGAPIE_OT_texturemask_copy(bpy.types.Operator):
    bl_idname = "bagapie.texturemask_copy"
    bl_label = "Copy Texture Mask Settings"

    def execute(self, context):
        global copied_texture_mask_settings

        obj = context.object
        val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
        modifiers = val['modifiers']
        node = obj.modifiers[modifiers[0]].node_group.nodes[modifiers[1]]
        copied_texture_mask_settings = {
            "fac": node.inputs[17].default_value,
            "scale": node.inputs[18].default_value,
            "offset": node.inputs[19].default_value,
            "smooth": node.inputs[20].default_value,
            "position": node.inputs[27].default_value,
        }
        return {'FINISHED'}

class BAGAPIE_OT_texturemask_paste(bpy.types.Operator):
    bl_idname = "bagapie.texturemask_paste"
    bl_label = "Paste Texture Mask Settings"

    def execute(self, context):
        global copied_texture_mask_settings
        if not copied_texture_mask_settings:
            self.report({'WARNING'}, "No texture mask settings copied.")
            return {'CANCELLED'}

        obj = context.object
        val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
        modifiers = val['modifiers']
        node = obj.modifiers[modifiers[0]].node_group.nodes[modifiers[1]]
        
        node.inputs[17].default_value = copied_texture_mask_settings["fac"]
        node.inputs[18].default_value = copied_texture_mask_settings["scale"]
        node.inputs[19].default_value = copied_texture_mask_settings["offset"]
        node.inputs[20].default_value = copied_texture_mask_settings["smooth"]
        node.inputs[27].default_value = copied_texture_mask_settings["position"]

        return {'FINISHED'}

classes = [
    SwitchMode,
    EditMode,
    UseSolidify,
    InvertPaint,
    InvertWeight,
    CleanWPaint,
    SetupAssetBrowser,
    SetupAssetBrowserForAssets,
    ADD_Assets,
    REMOVE_Assets,
    Rename_Layer,
    SwitchBoolCustom,
    SelectLayerContent,
    BAGAPIE_OT_add_remove_target,
    BAGAPIE_PT_asset_browser_tools,
    BAGAPIE_OT_remove_asset_from_layer,
    BAGAPIE_OT_select_asset,
    BAGAPIE_OT_proxy_toggle_from_ui,
    OBJECT_OT_display_as_bounds_toggle,
    BAGAPIE_OT_texturemask_copy,
    BAGAPIE_OT_texturemask_paste,
]