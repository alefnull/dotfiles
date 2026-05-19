#region Imports
import bpy
from bpy.props import *
from bpy.types import (Panel,StringProperty, EnumProperty,Menu,Operator,PropertyGroup,Scene, WindowManager)
from bpy.app.handlers import persistent
import bpy.utils.previews
import os
import random
from . modules.easybpy import *
#endregion
#region Useful Variables
preview_collections = {}
#endregion
#region Useful Functions
def alistdir(directory):
    '''
    'Alternative / Avoidance List Dir'
    An alternative version of os.listdir function that ignores files beginning
    with a '.', specifically aimed at preventing .DS_Store files on MacOS from 
    disrupting the import process of content packs. Introduced with 9.1.1.
    '''
    filelist = os.listdir(directory)
    return [x for x in filelist if not (x.startswith('.'))]
#endregion

#region V10 WIP
def import_content(type, 
                   name,
                   context,
                   directory,
                   template,
                   single,
                   weight,
                   unique_collection,
                   colpath,
                   colname,
                   objpath,
                   objname, 
                   treepath,
                   treename):
    # Setting up context
    scene = context.scene
    bytool = scene.by_tool
    wm = context.window_manager
        
    # Beginning procedure:
    objs = selected_objects()

    # Getting all useful directories for obtaining data (objects, node trees, etc.) from the content packs.
    directory = directory
    colpath = colpath
    colname = name
    treepath = treepath
    treename = name

#region CASE - TEMPLATE
    if template == True:
        if directory and os.path.exists(directory):
            if name.startswith("(Tr)"):
                #Since this is a complex geometry nodes effect requiring mesh references,
                #we will look for a separate object specifically pre-prepared to be imported
                #as a template object - which is separate from the object container for the
                #effect.

                # Updating the filename to find the complex template.
                objname = name + " Template"

                # Duplicating the appending code in case we need to handle the importing
                # of complex templates slightly differently in the future.
                ret = bpy.ops.wm.append(filename = objname, directory = objpath)
                template = bpy.context.selected_objects[-1]
                for m in template.modifiers:
                    if m.type=='SUBSURF':
                        m.show_viewport = True
                        m.show_render = True
            else:
                #Since this is not a complex effect, we will just be importing the object
                #that contains the modifier stack which constructs the effect.
                ret = bpy.ops.wm.append(filename = objname, directory = objpath)
                template = bpy.context.selected_objects[-1]
                for m in template.modifiers:
                    if m.type=='SUBSURF':
                        m.show_viewport = True
                        m.show_render = True
        return {'FINISHED'}

    else:
#endregion

#region CASE (S)
        # Find blend file with same name as folder (wm.content_packs_ve+'.blend')
        if directory and os.path.exists(directory):
            if name.startswith("(S)"):
                '''
                This is an (S) type effect, meaning a simple geometry node tree with no collection to import.
                This means we can go straight to the importing of the geo nodes tree and assign it to the object/s.
                Weight painting, and whether we can operate on only a single object, are cases that will be considered.
                '''
                if single == True:
                    # TODO Make objs a list with only a single object, being the active one - mainly for weight painting use case.
                    pass
                for o in objs:

                    # Import geo tree from content pack
                    print ("DEBUG::: " + str(treename))
                    print ("DEBUG::: " + str(directory))
                    bpy.ops.wm.append(filename = treename, directory = treepath)

                    # Get the imported tree by name (store in surface_tree)
                    imported_tree = bpy.data.node_groups[treename]

                    # Add geonodes modifier to object (store in geomod)
                    geomod = o.modifiers.new("Geometry Nodes", "NODES")

                    # Assign new surface_effect geonode tree to new geomod
                    geomod.node_group = imported_tree

                    # Change surface_tree name to 'objname_treename_randID'
                    randID = random.randint(1,9999)
                    imported_tree.name = o.name+"_"+treename+"_"+str(randID)

                    # Open the tree nodes
                    nodes = imported_tree.nodes

                    if weight == True:
                        # Do weight paint stuff here
                        select_only(o)
                        bpy.ops.object.vertex_group_add()
                        group = o.vertex_groups[-1]
                        group.name = name

                        # Get the correct input for the attribute toggle
                        id = ""
                        ginput = get_node(nodes, "Group Input")
                        for o in ginput.outputs:
                            if o.name.lower() == "weight":
                                id = o.identifier
                        id_prop_path = "[\""+id+"_use_attribute\"]"
                        id_prop_name = id+"_attribute_name"
                        bpy.ops.object.geometry_nodes_input_attribute_toggle(input_name=id, modifier_name=geomod.name)
                        geomod[id_prop_name] = group.name

                        # Set mode to weight paint
                        bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
                        pass
#endregion

#region CASE (C)
            elif name.startswith("(C)"):
                '''
                This is a (C) type effect, meaning there is a collection to import with the geometry node tree.
                Weight painting, and whether we can operate on only a single object, are cases that will be considered.
                '''
                # Collection
                col = None

                # If the user wants to create a unique collection.
                if unique_collection == True:
                    # Append collection to file (store ref in col) <- (optional: link)
                    bpy.ops.wm.append(filename = colname, directory = colpath)
                    col = get_collection(name)
                
                # Else: The user does not want to create a unique collection.
                else:

                    # If the collection already exists in the blend file.
                    if collection_exists(name):
                        # Let's grab the collection.
                        col = get_collection(name)
                    
                    # Else: The collection does not already exist in the blend file.
                    else:
                        # Let's create the collection.
                        bpy.ops.wm.append(filename = colname, directory = colpath)
                        col = get_collection(name)
                    
                # if col:
                if col:
                    for o in objs:

                        # Import geo tree from content pack
                        bpy.ops.wm.append(filename = treename, directory = treepath)

                        # Get the imported tree by name (store in surface_tree)
                        imported_tree = bpy.data.node_groups[treename]

                        # Add geonodes modifier to object (store in geomod)
                        geomod = o.modifiers.new("Geometry Nodes", "NODES")

                        # Assign new surface_effect geonode tree to new geomod
                        geomod.node_group = imported_tree

                        # Change surface_tree name to 'objname_treename_randID'
                        randID = random.randint(1,9999)
                        imported_tree.name = o.name+"_"+treename+"_"+str(randID)

                        # Open surface tree nodes
                        nodes = imported_tree.nodes

                        if weight == True:
                            # Do weight paint stuff here
                            select_only(o)
                            bpy.ops.object.vertex_group_add()
                            group = o.vertex_groups[-1]
                            group.name = name

                            # Get the correct input for the attribute toggle
                            id = ""
                            ginput = get_node(nodes, "Group Input")
                            for o in ginput.outputs:
                                if o.name.lower() == "weight":
                                    id = o.identifier
                            id_prop_path = "[\""+id+"_use_attribute\"]"
                            id_prop_name = id+"_attribute_name"
                            bpy.ops.object.geometry_nodes_input_attribute_toggle(input_name=id, modifier_name=geomod.name)
                            geomod[id_prop_name] = group.name

                            # Set mode to weight paint
                            bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
                            pass

                        # Put col in correct node (collection info node)
                        colinfo = get_node(nodes, "Collection Info")
                        colinfo.inputs[0].default_value = col
#endregion

#region CASE (Tr)
            elif name.startswith("(Tr)"): # Currently looking for (G)
                '''
                This is a (Tr) type effect, meaning that once an entire object has been brought in with its modifier stack,
                the originally selected object will become a hidden source, whereas this imported object will become the host
                for the effect. The Tr stands for Target Remote.
                Checks for object references, looking for 'object' inputs in the geometry nodes group inputs / modifier 
                stack inputs, will also be performed where appropriate.
                '''
                # Complex geo nodes stacks which require extra base referencing
                # Assume base object is selected and make a copy.
                base = ao()
                new = copy_object(base)
                select_only(new)

                # Append the template object
                ret = bpy.ops.wm.append(filename = objname, directory = objpath)
                template = bpy.context.selected_objects[-1]

                # Select the object with moodifier stack.
                select_only(new)
                select_object(template) # <- Active selection

                # Copy over modifiers from template.
                bpy.ops.object.make_links_data(type='MODIFIERS')

                # Set active back to base
                select_only(new)

                # Loop modifiers to find geometry nodes:
                for m in new.modifiers:
                    # Get geo node modifiers
                    if m.type == "NODES":
                        nodes = m.node_group.nodes

                        ''' - Assigning the object reference
                        for n in nodes:
                            if n.type == "OBJECT_INFO":
                                # Set all object references to base
                                n.inputs[0].default_value = base
                        '''
                        # Using the modifier input method.
                        id = ""
                        ginput = get_node(nodes, "Group Input")
                        for o in ginput.outputs:
                            if o.name.lower() == "object":
                                id = o.identifier #Input_3 for example
                        m[id] = base

                        # For some reason this hack workaround is needed because
                        # bpy.context.view_layer.update() doesn't work.
                        hide_in_viewport(new)
                        show_in_viewport(new)


                    if m.type == "SKIN":
                        bpy.ops.mesh.customdata_skin_add()
                # Clean up by deleting template and hiding base
                hide_in_viewport(base)
                hide_in_render(base)
                delete_object(template)
                pass
#endregion

#region CASE (Ts)
            elif name.startswith("(Ts)"):
                '''
                This is a (Ts) type effect, meaning that once an entire object has been brought in with its modifier stack,
                it is copied over to the originally selected object, and the imported object is deleted.
                The Ts stands for Target Self.
                Checks for object references, looking for 'object' inputs in the geometry nodes group inputs / modifier 
                stack inputs, will also be performed where appropriate.
                '''
                # Append template object
                base = ao()
                ret = bpy.ops.wm.append(filename = objname, directory = objpath)
                template = bpy.context.selected_objects[-1]
                
                # Select the object with moodifier stack.
                select_only(base)
                select_object(template) # <- Active selection
                
                # Copy over modifiers from template.
                bpy.ops.object.make_links_data(type='MODIFIERS')
                
                # Set active back to base
                select_only(base)

                # Loop modifiers to find geometry nodes:
                for m in base.modifiers:
                    # Get geo node modifiers
                    if m.type == "NODES":
                        nodes = m.node_group.nodes

                        ''' - Assigning the object reference
                        for n in nodes:
                            if n.type == "OBJECT_INFO":
                                # Set all object references to base
                                n.inputs[0].default_value = base
                        '''
                        # Using the modifier input method.
                        id = ""
                        ginput = get_node(nodes, "Group Input")
                        for o in ginput.outputs:
                            if o.name.lower() == "object":
                                id = o.identifier #Input_3 for example
                        m[id] = base
                        
                        # For some reason this hack workaround is needed because
                        # bpy.context.view_layer.update() doesn't work.
                        hide_in_viewport(base)
                        show_in_viewport(base)

                    if m.type == "SKIN":
                        bpy.ops.mesh.customdata_skin_add()
                # Clean up by deleting template
                delete_object(template)
                pass
#endregion

#region Ending Import
        else:
            print("Pack file does not exist.")
        return {'FINISHED'}
    pass
#endregion
#endregion

#region SURFACE EFFECTS
def content_packs_se_from_directory(self, context):
    wm = context.window_manager
    enum_items = []
    if context is None:
        return enum_items

    directory = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs'))

    if directory and os.path.exists(directory):
        # Scan directory for folders
        pack_paths = alistdir(directory)
        for p in pack_paths:
            #--- Folder Check
            cpack = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', p))
            folders = alistdir(cpack)
            if 'thumbnails_surface_effects' in folders:
                enum_items.append((p, p, 'Content Pack'))
            #---
    return enum_items
def get_surface_effect_thumbnails(self, context):
    enum_items = []
    wm = context.window_manager

    directory = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', wm.content_packs_se, 'thumbnails_surface_effects'))

    # Get collection defined in register function
    pcoll = preview_collections["main"]

    if directory == pcoll.surface_effects_dir:
        return pcoll.surface_effects

    if directory and os.path.exists(directory):
        # Scan directory for jpg files
        image_paths = []
        for fn in alistdir(directory):
            if fn.lower().endswith(".jpg"):
                image_paths.append(fn)
        
        for i, name in enumerate(image_paths):
            # Generate a thumbnail preview for a file.
            filepath = os.path.join(directory, name)
            icon = pcoll.get(name)
            if not icon:
                thumb = pcoll.load(name, filepath, 'IMAGE')
            else:
                thumb = pcoll[name]
            trimname = name.split('.')
            #enum_items.append((name, name, "", thumb.icon_id, i))
            enum_items.append((trimname[0], trimname[0], "", thumb.icon_id, i))
    
    pcoll.surface_effects = enum_items
    pcoll.surface_effects_dir = directory
    return pcoll.surface_effects
class BYGEN_OT_surface_effect_import(bpy.types.Operator):
    bl_idname = "object.bygen_surface_effect_import"
    bl_label = "Import Surface Effect"
    bl_description = "Imports and adds the selected surface effect."
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):
        # Setting up context
        scene = context.scene
        bytool = scene.by_tool
        wm = context.window_manager

        # Getting all useful directories for obtaining data (objects, node trees, etc.) from the content packs.
        directory = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', wm.content_packs_se, wm.content_packs_se+'.blend'))
        colpath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', wm.content_packs_se, wm.content_packs_se+'.blend','Collection'))
        colname = wm.surface_effects
        treepath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', wm.content_packs_se, wm.content_packs_se+'.blend','NodeTree'))
        treename = wm.surface_effects

        import_content(
            type = "N/A",
            name = colname,
            context = context,
            directory = directory,
            template = False,
            single = False,
            weight = False,
            unique_collection = bytool.unique_collection,
            colpath = colpath,
            colname = colname,
            objpath = "",
            objname = "",
            treepath = treepath,
            treename = treename
        )
        return {'FINISHED'}
class BYGEN_OT_surface_effect_weight_paint(bpy.types.Operator):
    bl_idname = "object.bygen_surface_effect_weight_paint"
    bl_label = "Apply (Vertex Paint)"
    bl_description = "Imports the effect and sets it up for vertex painting."
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):
        # Setting up context
        scene = context.scene
        bytool = scene.by_tool
        wm = context.window_manager

        # Getting all useful directories for obtaining data (objects, node trees, etc.) from the content packs.
        directory = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', wm.content_packs_se, wm.content_packs_se+'.blend'))
        colpath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', wm.content_packs_se, wm.content_packs_se+'.blend', 'Collection'))
        colname = wm.surface_effects
        treepath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', wm.content_packs_se, wm.content_packs_se+'.blend','NodeTree'))
        treename = wm.surface_effects

        import_content(
            type = "N/A",
            name = colname,
            context = context,
            directory = directory,
            template = False,
            single = True,
            weight = True,
            unique_collection = bytool.unique_collection,
            colpath = colpath,
            colname = colname,
            objpath = "",
            objname = "",
            treepath = treepath,
            treename = treename
        )
        return {'FINISHED'}   
class BYGEN_OT_refresh_effect_properties(bpy.types.Operator):
    bl_idname = "object.bygen_refresh_effect_properties"
    bl_label = "Refresh Effect Properties"
    bl_description = "Refreshes the effect properties"

    def execute(self, context):
        thumbnail_update_call(self, context)
        return {'FINISHED'}
class BYGEN_PT_SurfaceEffects(Panel):
    bl_idname = "BYGEN_PT_SurfaceEffects"
    bl_label = "Surface"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BY-GEN"

    def draw_header(self, context):
        self.layout.label(text = "", icon = "OUTLINER_OB_SURFACE")
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        bytool = scene.by_tool
        wm = context.window_manager

        column = layout.column()
        row = column.row()
        #row.scale_y = 1.2
        row.prop(wm, "content_packs_se", text = "")
        #row.operator("wm.url_open", text="", icon='FILEBROWSER').url = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs'))
        #row.operator("wm.url_open", text="", icon='URL').url = "https://curtisholt.online/by-gen"
        row.operator("object.bygen_refresh_effect_properties", text="", icon='FILE_REFRESH')

        # Displaying the thumbnail selection window:
        row = layout.row()
        row.template_icon_view(wm, "surface_effects", show_labels=True, scale=8, scale_popup=8)
        
        box = layout.box()
        col = box.column()

        #row = layout.row()
        colrow = col.row(align=True)
        colrow.operator("object.bygen_surface_effect_import", text = "Apply")
        colrow = col.row(align=True)
        colrow.operator("object.bygen_surface_effect_weight_paint", text = "Apply (Weight Paint)")#, icon = "MOD_VERTEX_WEIGHT"
class BYGEN_PT_SurfaceHelperTools(Panel):
    bl_idname = "BYGEN_PT_SurfaceHelperTools"
    bl_label = "Helper Tools"
    bl_parent_id = "BYGEN_PT_SurfaceEffects"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BY-GEN"

    def draw_header(self, context):
        self.layout.label(text = "", icon = "TOOL_SETTINGS")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        bytool = scene.by_tool

        box = layout.box()

        col = box.column()
        colrow = col.row(align=True)
        colrow.label(text = "Vertex Group Operations")
        colrow = col.row(align=True)
        colrow.operator("object.vertex_group_assign_new", text = "Vertex Group from Selected")
#endregion

#region MESH EFFECTS
def content_packs_me_from_directory(self, context):
    wm = context.window_manager
    enum_items = []
    if context is None:
        return enum_items

    #directory = "content_packs_md"
    directory = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs'))

    #pcoll = preview_collections["categories"]
    if directory and os.path.exists(directory):
        # Scan directory for folders
        pack_paths = alistdir(directory)
        for p in pack_paths:
            #--- Folder Check
            cpack = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', p))
            folders = alistdir(cpack)
            if 'thumbnails_mesh_effects' in folders:
                enum_items.append((p, p, 'Content Pack'))
            #---
    return enum_items
def get_mesh_effect_thumbnails(self, context):
    enum_items = []
    wm = context.window_manager

    directory = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', wm.content_packs_me, 'thumbnails_mesh_effects'))

    # Get collection defined in register function
    pcoll = preview_collections["main"]

    if directory == pcoll.mesh_effects_dir:
        return pcoll.mesh_effects

    if directory and os.path.exists(directory):
        # Scan directory for jpg files
        image_paths = []
        for fn in alistdir(directory):
            if fn.lower().endswith(".jpg"):
                image_paths.append(fn)
        
        for i, name in enumerate(image_paths):
            # Generate a thumbnail preview for a file.
            filepath = os.path.join(directory, name)
            icon = pcoll.get(name)
            if not icon:
                thumb = pcoll.load(name, filepath, 'IMAGE')
            else:
                thumb = pcoll[name]
            trimname = name.split('.')
            #enum_items.append((name, name, "", thumb.icon_id, i))
            enum_items.append((trimname[0], trimname[0], "", thumb.icon_id, i))

    pcoll.mesh_effects = enum_items
    return pcoll.mesh_effects
class BYGEN_OT_mesh_effect_import(bpy.types.Operator):
    bl_idname = "object.bygen_mesh_effect_import"
    bl_label = "Import Mesh Effect"
    bl_description = "Imports and adds the selected mesh effect."
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):
        # Setting up context
        scene = context.scene
        bytool = scene.by_tool
        wm = context.window_manager

        # Getting all useful directories for obtaining data (objects, node trees, etc.) from the content packs.
        directory = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', wm.content_packs_me, wm.content_packs_me+'.blend'))
        objpath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', wm.content_packs_me, wm.content_packs_me+'.blend','NodeTree'))
        objname = wm.mesh_effects

        import_content(
            type = "N/A",
            name = objname,
            context = context,
            directory = directory,
            template = False,
            single = False,
            weight = False,
            unique_collection = bytool.unique_collection,
            colpath = "",
            colname = "",
            objpath = "",
            objname = "",
            treepath = objpath,
            treename = objname
        )
        return {'FINISHED'}
class BYGEN_PT_MeshEffects(Panel):
    bl_idname = "BYGEN_PT_MeshEffects"
    bl_label = "Mesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BY-GEN"

    def draw_header(self, context):
        self.layout.label(text = "", icon = "OUTLINER_OB_MESH")
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        scene = context.scene
        bytool = scene.by_tool

        column = layout.column()
        row = column.row()
        #row.scale_y = 1.2
        row.prop(wm, "content_packs_me", text = "")
        #row.operator("wm.url_open", text="", icon='FILEBROWSER').url = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs'))
        #row.operator("wm.url_open", text="", icon='URL').url = "https://curtisholt.online/by-gen"
        row.operator("object.bygen_refresh_effect_properties", text="", icon='FILE_REFRESH')

        # Displaying the thumbnail selection window:
        row = layout.row()
        row.template_icon_view(wm, "mesh_effects", show_labels=True, scale=8, scale_popup=8)

        box = layout.box()
        col = box.column()

        colrow = col.row(align=True)
        colrow.operator("object.bygen_mesh_effect_import", text = "Apply")
#endregion

#region VOLUME EFFECTS
def content_packs_ve_from_directory(self, context):
    wm = context.window_manager
    enum_items = []
    if context is None:
        return enum_items

    #directory = "content_packs_md"
    directory = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs'))

    #pcoll = preview_collections["categories"]
    if directory and os.path.exists(directory):
        # Scan directory for folders
        pack_paths = alistdir(directory)
        for p in pack_paths:
            #--- Folder Check
            cpack = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', p))
            folders = alistdir(cpack)
            if 'thumbnails_volume_effects' in folders:
                enum_items.append((p, p, 'Content Pack'))
            #---
    return enum_items
def get_volume_effect_thumbnails(self, context):
    enum_items = []
    #if context is None:
    #    return enum_items
    wm = context.window_manager

    #directory = wm.surface_effects_dir
    #directory = "content_packs\\"+wm.content_packs_md+"\\thumbnails_surface_effects"
    directory = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', wm.content_packs_ve, 'thumbnails_volume_effects'))

    # Get collection defined in register function
    pcoll = preview_collections["main"]

    if directory == pcoll.volume_effects_dir:
        return pcoll.volume_effects

    if directory and os.path.exists(directory):
        # Scan directory for jpg files
        image_paths = []
        for fn in alistdir(directory):
            if fn.lower().endswith(".jpg"):
                image_paths.append(fn)
        
        for i, name in enumerate(image_paths):
            # Generate a thumbnail preview for a file.
            filepath = os.path.join(directory, name)
            icon = pcoll.get(name)
            if not icon:
                thumb = pcoll.load(name, filepath, 'IMAGE')
            else:
                thumb = pcoll[name]
            trimname = name.split('.')
            #enum_items.append((name, name, "", thumb.icon_id, i))
            enum_items.append((trimname[0], trimname[0], "", thumb.icon_id, i))

    pcoll.volume_effects = enum_items
    #pcoll.volume_effects_dir = directory
    return pcoll.volume_effects
class BYGEN_OT_volume_effect_import(bpy.types.Operator):
    bl_idname = "object.bygen_volume_effect_import"
    bl_label = "Import Volume Effect"
    bl_description = "Imports and adds the selected volume effect."
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):
        # Setting up context
        scene = context.scene
        bytool = scene.by_tool
        wm = context.window_manager

        # Getting all useful directories for obtaining data (objects, node trees, etc.) from the content packs.
        directory = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', wm.content_packs_ve, wm.content_packs_ve+'.blend'))
        colpath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', wm.content_packs_ve, wm.content_packs_ve+'.blend','Collection'))
        colname = wm.volume_effects
        treepath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs', wm.content_packs_ve, wm.content_packs_ve+'.blend','NodeTree'))
        treename = wm.volume_effects

        import_content(
            type = "N/A",
            name = colname,
            context = context,
            directory = directory,
            template = False,
            single = False,
            weight = False,
            unique_collection = bytool.unique_collection,
            colpath = colpath,
            colname = colname,
            objpath = "",
            objname = "",
            treepath = treepath,
            treename = treename
        )
        return {'FINISHED'}
class BYGEN_PT_VolumeEffects(Panel):
    bl_idname = "BYGEN_PT_VolumeEffects"
    bl_label = "Volume"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BY-GEN"

    def draw_header(self, context):
        self.layout.label(text = "", icon = "OUTLINER_OB_VOLUME")

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        scene = context.scene
        bytool = scene.by_tool

        column = layout.column()
        row = column.row()
        #row.scale_y = 1.2
        row.prop(wm, "content_packs_ve", text = "")
        #row.operator("wm.url_open", text="", icon='FILEBROWSER').url = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs'))
        #row.operator("wm.url_open", text="", icon='URL').url = "https://curtisholt.online/by-gen"
        row.operator("object.bygen_refresh_effect_properties", text="", icon='FILE_REFRESH')

        # Displaying the thumbnail selection window:
        row = layout.row()
        row.template_icon_view(wm, "volume_effects", show_labels=True, scale=8, scale_popup=8)

        box = layout.box()
        col = box.column()

        colrow = col.row(align=True)
        colrow.operator("object.bygen_volume_effect_import", text = "Apply")
#endregion

#region SETTINGS PANEL
class BYGEN_PT_Settings(Panel):
    bl_idname = "BYGEN_PT_Settings"
    bl_label = "Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BY-GEN"

    def draw_header(self, context):
        self.layout.label(text = "", icon = "SETTINGS")

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        scene = context.scene
        bytool = scene.by_tool

        box = layout.box()
        col = box.column()

        colrow = col.row(align=True)
        colrow.prop(bytool, "unique_collection")
        colrow = col.row(align=True)
        colrow.operator("wm.url_open", text="Local Content Packs", icon='FILEBROWSER').url = os.path.abspath(os.path.join(os.path.dirname(__file__), 'content_packs'))
#endregion

#region App Handling
def thumbnail_update_call(self, context):
    # Flush and Reconstruct Thumbnails with new selection
    register_props()
    return None
'''
The following app handler makes sure that the catgories
and thumbnails are recalculated every time a blend file is
loaded. This prevents a bug where the thumbnails would not
represent the category shown in the selection, meaning that
when the user goes to apply the mode, it fails, as the mode
does not exist in the selected content pack.
'''
@persistent
def load_reset(temp):
    thumbnail_update_call(None, bpy.context)
bpy.app.handlers.load_post.append(load_reset)
#endregion
#region Registration
classes = (
    # Preoperation Functions / Classes

    # Surface Effects
    BYGEN_PT_SurfaceEffects,
    BYGEN_OT_surface_effect_import,
    BYGEN_OT_surface_effect_weight_paint,
    BYGEN_OT_refresh_effect_properties,

    # Mesh Effects
    #BYGEN_OT_mesh_structural_import,
    BYGEN_OT_mesh_effect_import,
    BYGEN_PT_MeshEffects,
    
    # Volume Effects
    BYGEN_OT_volume_effect_import,
    BYGEN_PT_VolumeEffects,

    # Settings
    BYGEN_PT_Settings,
)
def register_props():
    #region Info and Imports
    '''
    Here we destroy the original props for the interface and reconstruct them
    using the new selection for the content_packs property.
    Realistically we only need to reconstruct the thumbnails in this phase, but
    I have left it so content_packs also updates because this would allow
    people to install and select new packs while Blender is running.
    (New content packs will only display when the user has selected a different
    pre-existing content pack in the interface, causing the value to update and
    run the directory search again.)
    '''
    import bpy
    from bpy.utils import register_class
    from bpy.types import WindowManager
    from bpy.props import (
        StringProperty,
        EnumProperty,
        BoolProperty,
    )
    import bpy.utils.previews
    #endregion
    #region Deleting Window Manager Properties
    # Flush Original Props
    del WindowManager.volume_effects
    del WindowManager.surface_effects
    del WindowManager.content_packs_se # Surface Effects
    del WindowManager.content_packs_me # Mesh Effects
    del WindowManager.content_packs_ve # Volume Effects

    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    #endregion
    #region Creating pcoll Properties
    # Reconstruct Props
    pcoll = bpy.utils.previews.new()
    pcoll.surface_effects_dir = ""
    pcoll.mesh_effects_dir = ""
    pcoll.volume_effects_dir = ""
    pcoll.surface_effects = ()
    pcoll.mesh_effects = ()
    pcoll.volume_effects = ()
    preview_collections["main"] = pcoll
    #endregion
    #region Creating WindowManager Properties
    WindowManager.content_packs_se = EnumProperty( # Surface Effects
        items = content_packs_se_from_directory(None, bpy.context),
        update = thumbnail_update_call,
    )
    WindowManager.content_packs_me = EnumProperty( # Mesh Displacement
        items = content_packs_me_from_directory(None, bpy.context),
        update = thumbnail_update_call,
    )
    WindowManager.content_packs_ve = EnumProperty( # Volume Effects
        items = content_packs_ve_from_directory(None, bpy.context),
        update = thumbnail_update_call,
    )
    WindowManager.surface_effects_dir = StringProperty( # Surface Effects
        name = "Folder Path",
        subtype = 'DIR_PATH',
        default="images"
    )
    WindowManager.mesh_effects_dir = StringProperty( # Mesh Displacement
        name = "Folder Path",
        subtype = 'DIR_PATH',
        default="images"
    )
    WindowManager.volume_effects_dir = StringProperty( # Volume Effects
        name = "Folder Path",
        subtype = 'DIR_PATH',
        default="images"
    )
    WindowManager.surface_effects = EnumProperty( # Surface Effects
        items = get_surface_effect_thumbnails(None, bpy.context),
    )
    WindowManager.mesh_effects = EnumProperty( # Surface Effects
        items = get_mesh_effect_thumbnails(None, bpy.context),
    )
    WindowManager.volume_effects = EnumProperty( # Volume Effects
        items = get_volume_effect_thumbnails(None, bpy.context),
    )
    #endregion
def register():
    #region Info and Imports
    import bpy
    from bpy.utils import register_class
    from bpy.types import WindowManager
    from bpy.props import (
        StringProperty,
        EnumProperty,
        BoolProperty,
    )
    import bpy.utils.previews
    #endregion
    #region Creating pcoll Properties
    pcoll = bpy.utils.previews.new()
    pcoll.surface_effects_dir = ""
    pcoll.mesh_effects_dir = ""
    pcoll.volume_effects_dir = ""
    pcoll.surface_effects = ()
    pcoll.mesh_effects = ()
    pcoll.volume_effects = ()
    preview_collections["main"] = pcoll
    #endregion
    #region Creating WindowManager Properties
    WindowManager.content_packs_se = EnumProperty( # Surface Effects
        items = content_packs_se_from_directory(None, bpy.context),
        update = thumbnail_update_call,
    )
    WindowManager.content_packs_me = EnumProperty( # Mesh Displacement
        items = content_packs_me_from_directory(None, bpy.context),
        update = thumbnail_update_call,
    )
    WindowManager.content_packs_ve = EnumProperty( # Volume Effects
        items = content_packs_ve_from_directory(None, bpy.context),
        update = thumbnail_update_call,
    )
    WindowManager.surface_effects_dir = StringProperty( # Surface Effects
        name = "Folder Path",
        subtype = 'DIR_PATH',
        default="images"
    )
    WindowManager.mesh_effects_dir = StringProperty( # Mesh Displacement
        name = "Folder Path",
        subtype = 'DIR_PATH',
        default="images"
    )
    WindowManager.volume_effects_dir = StringProperty( # Volume Effects
        name = "Folder Path",
        subtype = 'DIR_PATH',
        default="images"
    )
    WindowManager.surface_effects = EnumProperty( # Surface Effects
        items = get_surface_effect_thumbnails(None, bpy.context),
    )
    WindowManager.mesh_effects = EnumProperty( # Mesh Displacement
        items = get_mesh_effect_thumbnails(None, bpy.context),
    )
    WindowManager.volume_effects = EnumProperty( # Volume Effects
        items = get_volume_effect_thumbnails(None, bpy.context),
    )
    #endregion
    #region Registering Classes
    for cls in classes:
        register_class(cls)
    #endregion
def unregister():
    #region Info and Imports
    from bpy.utils import unregister_class
    #endregion
    #region Deleting WindowManager Properties
    del WindowManager.volume_effects
    del WindowManager.mesh_effects
    del WindowManager.surface_effects
    del WindowManager.volume_effects_dir
    del WindowManager.mesh_effects_dir
    del WindowManager.surface_effects_dir
    del WindowManager.content_packs_ve
    del WindowManager.content_packs_me
    del WindowManager.content_packs_se
    #endregion
    #region Deleting pcoll Properties
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    #endregion
    #region Unregistering Classes
    for cls in reversed(classes):
        unregister_class(cls)
    #endregion
#endregion