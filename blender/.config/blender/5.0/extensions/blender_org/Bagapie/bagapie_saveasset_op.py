import bpy
from bpy.types import Operator
from .presets import bagapieModifiers
import time
import os
from pathlib import Path
from .utils import Warning

class BAGAPIE_OT_saveasset(Operator):
    """Save as asset the selected object (preview generation may fail)"""
    bl_idname = 'bagapie.saveasset'
    bl_label = bagapieModifiers['asset']['label']
    bl_options = {'REGISTER', 'UNDO'}

    rewrite: bpy.props.BoolProperty(default=False)
    check_file: bpy.props.BoolProperty(default=False)
    already_exist: bpy.props.BoolProperty(default=False)
    new_name: bpy.props.StringProperty(default="None")

    @classmethod
    def poll(cls, context):
        o = context.object
        object_types = ['MESH','CURVE']
        return (
            o is not None and 
            o.type in object_types
        )

    def invoke(self, context, event):
        wm = context.window_manager
        ob = bpy.context.active_object

        prefs = bpy.context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries

        try:
            print("Default library : "+ asset_libraries[0].name)
        except:
            Warning("Create Library. Preferences > File Paths > Asset Libraries", "INFO", 'ERROR') 
            return {'FINISHED'}

        self.rewrite = False
        self.check_file = False
        self.already_exist = False
        self.new_name = ob.name

        ob.asset_mark()
        ob.asset_generate_preview()
        time.sleep(0.1)
        bpy.context.scene['Use_library'] = asset_libraries[0]
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        ob = bpy.context.active_object

        prefs = bpy.context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries
        
        layout.label(text = "Select Library")
        for i in range(len(asset_libraries)):
            if asset_libraries[i].name == bpy.context.scene['Use_library']:
                statut = True
            else :
                statut = False

            layout.operator('use.library', text=asset_libraries[i].name,  depress = statut).index = i

        if not self.check_file:
            self.already_exist = False
            for asset_library in asset_libraries:
                path_to_file = os.path.join(asset_library.path, f"{ob.name}.blend")
                path = Path(path_to_file)
                
                idx = 1
                if path.is_file():
                    self.already_exist = True
                    if not self.rewrite:
                        name=ob.name
                        while path.is_file():
                            path_to_file = os.path.join(asset_library.path, f"{ob.name}_{idx}.blend")
                            path = Path(path_to_file)
                            name = ob.name + '_' + str(idx)
                            idx += 1
                    else:
                        name = ob.name
                else:
                    name = ob.name

            self.new_name = name

        self.check_file = True

        if self.already_exist:
            box = layout.box()
            col = box.column(align=True)
            col.label(text = "Object with the same name already exist.")
            if not self.rewrite:
                col.prop(self, 'new_name', text = "New name")
                for asset_library in asset_libraries:
                    if Path(os.path.join(asset_library.path, f"{self.new_name}.blend")).is_file():
                        col.label(text = "This name already exist.", icon ='ERROR')
                        col.label(text = "This asset will replace the existing one.", icon ='ERROR')
                col.label(text = "Current name : "+ob.name)

            col.prop(self, 'rewrite', text = "Replace existing asset.")
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text = "If replace is enabled,")
            col.label(text = "and if an asset of the same name already exists,")
            col.label(text = "it will be replaced by this new asset.")

    def execute(self, context):
        
        prefs = bpy.context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries

        if bpy.context.scene['Use_library'] == "":
            Warning("No library selected", "INFO", 'ERROR') 
            return {'FINISHED'}
        try:
            print(bpy.context.scene['Use_library'][0])
        except:
            Warning("No library selected", "INFO", 'ERROR') 
            return {'FINISHED'}

        for asset_library in asset_libraries:
            ob = bpy.context.active_object
            path_to_file = os.path.join(asset_library.path, f"{ob.name}.blend")
            path = Path(path_to_file)
            
            if path.is_file():
                if not self.rewrite:
                    name = self.new_name
                    ob.name = self.new_name
                else:
                    name = ob.name
            else:
                name = ob.name
            
            if asset_library.name in bpy.context.scene['Use_library']:
                ob.asset_mark()
                ob.asset_generate_preview()
                time.sleep(5)
                bpy.data.libraries.write(os.path.join(asset_library.path, f"{name}.blend"), set([ob]), fake_user=True)
                ob.asset_clear()
        del bpy.context.scene['Use_library']

        return {'FINISHED'}


class BAGAPIE_OT_savematerial(Operator):
    """Save active material from selected object (preview generation may fail)"""
    bl_idname = 'bagapie.savematerial'
    bl_label = bagapieModifiers['material']['label']
    bl_options = {'REGISTER', 'UNDO'}

    rewrite: bpy.props.BoolProperty(default=False)
    check_file: bpy.props.BoolProperty(default=False)
    already_exist: bpy.props.BoolProperty(default=False)
    new_name: bpy.props.StringProperty(default="None")
    mat_index: bpy.props.IntProperty(default=0)


    @classmethod
    def poll(cls, context):
        o = context.object
        object_types = ['MESH','CURVE']
        return (
            o is not None and 
            o.type in object_types
        )

    def invoke(self, context, event):
        wm = context.window_manager
        obj = bpy.context.active_object
        idx = obj.active_material_index

        try:
            mat = obj.material_slots[idx].material
        except:
            Warning("No material on selected object", "INFO", 'ERROR') 
            return {'FINISHED'}

        prefs = bpy.context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries

        try:
            print("Default library : "+ asset_libraries[0].name)
        except:
            Warning("Create Library. Preferences > File Paths > Asset Libraries", "INFO", 'ERROR') 
            return {'FINISHED'}

        self.rewrite = False
        self.check_file = False
        self.already_exist = False
        self.new_name = obj.name
        self.mat_index = idx
            
        mat = obj.material_slots[idx].material
        mat.asset_mark()
        mat.asset_generate_preview()
        time.sleep(0.1)

        bpy.context.scene['Use_library'] = asset_libraries[0]
        

        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        obj = context.object
        idx = obj.active_material_index
        mat = obj.material_slots[idx].material

        layout.template_list("BAGAPIE_UL_saveasset_list", "", obj, "material_slots", obj, "active_material_index")

        prefs = bpy.context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries
        
        layout.label(text = "Select Library")

        for i in range(len(asset_libraries)):

                if asset_libraries[i].name == bpy.context.scene['Use_library']:
                    statut = True
                else :
                    statut = False
            
                layout.operator('use.library', text=asset_libraries[i].name,  depress = statut).index = i
              

        if self.mat_index != idx:
            self.mat_index = idx
            self.check_file = False

        if not self.check_file:
            self.already_exist = False
            for asset_library in asset_libraries:
                path_to_file = os.path.join(asset_library.path, f"{mat.name}.blend")
                path = Path(path_to_file)
                
                idx = 1
                if path.is_file():
                    self.already_exist = True
                    if not self.rewrite:
                        while path.is_file():
                            path_to_file = os.path.join(asset_library.path, f"{mat.name}_{idx}.blend")
                            path = Path(path_to_file)
                            name = mat.name + '_' + str(idx)
                            idx += 1
                    else:
                        name = mat.name

                else:
                    name = mat.name

            self.new_name = name
        self.check_file = True

        if self.already_exist:
            box = layout.box()
            col = box.column(align=True)
            col.label(text = "Material with the same name already exist.")
            if not self.rewrite:
                col.prop(self, 'new_name', text = "New Name")
                for asset_library in asset_libraries:
                    if Path(os.path.join(asset_library.path, f"{self.new_name}.blend")).is_file():
                        col.label(text = "This name already exist.", icon ='ERROR')
                        col.label(text = "This asset will replace the existing one.", icon ='ERROR')
                col.label(text = "Current name : "+mat.name)
            col.prop(self, 'rewrite', text = "Replace existing asset.")
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text = "If replace is enabled,")
            col.label(text = "and if an asset of the same name already exists,")
            col.label(text = "it will be replaced by this new asset.")

    def execute(self, context):
        
        prefs = bpy.context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries

        if bpy.context.scene['Use_library'] == "":
            Warning("No library selected", "INFO", 'ERROR') 
            return {'FINISHED'}
        try:
            print(bpy.context.scene['Use_library'][0])
        except:
            Warning("No library selected", "INFO", 'ERROR') 
            return {'FINISHED'}

        for asset_library in asset_libraries:

            obj = bpy.context.active_object
            idx = obj.active_material_index
            mat = obj.material_slots[idx].material
            path_to_file = os.path.join(asset_library.path, f"{mat.name}.blend")
            path = Path(path_to_file)
            
            if path.is_file():
                if not self.rewrite:
                    name = self.new_name
                    mat.name = name
                else:
                    name = mat.name
            else:
                name = mat.name

            if asset_library.name in bpy.context.scene['Use_library']:
                mat.asset_mark()
                time.sleep(3)
                bpy.data.libraries.write(os.path.join(asset_library.path, f"{name}.blend"), set([mat]), fake_user=True)
                mat.asset_clear()
        del bpy.context.scene['Use_library']

        return {'FINISHED'}


class BAGAPIE_UL_saveasset_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        slot = item
        ma = slot.material
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if ma:
                layout.prop(ma, "name", text="", emboss=False, icon_value=icon)
            else:
                layout.label(text="", translate=False, icon_value=icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class UseLibrary(Operator):
    """Enable/Disable Library"""
    bl_idname = "use.library"
    bl_label = "Use Library"

    index: bpy.props.IntProperty(default=0)

    def execute(self, context):
        prefs = bpy.context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries
        
        if asset_libraries[self.index].name in bpy.context.scene['Use_library']:
            bpy.context.scene['Use_library'] = bpy.context.scene['Use_library'].replace(asset_libraries[self.index].name, "", 1)
        else :
            bpy.context.scene['Use_library'] = asset_libraries[self.index].name

        return {'FINISHED'}

classes = [
    BAGAPIE_OT_saveasset,
    BAGAPIE_OT_savematerial,
    BAGAPIE_UL_saveasset_list,
    UseLibrary
]