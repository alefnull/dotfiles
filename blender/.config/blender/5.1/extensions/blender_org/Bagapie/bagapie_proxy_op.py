import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
from random import random
from .utils import Add_NodeGroup

class BAGAPIE_OT_proxy_remove(Operator):
    """ Remove Bagapie Proxy modifiers """
    bl_idname = "bagapie.proxy_remove"
    bl_label = 'Remove Bagapie Proxy'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object
        object_types = ['MESH','CURVE']
        return (
            o is not None and 
            o.type in object_types
        )
    
    index: bpy.props.IntProperty(default=0)
    
    def execute(self, context):
        
        obj = context.object
        val = json.loads(obj.bagapieList[self.index]['val'])
        try:
            modifiers = val['modifiers']
            print(modifiers)
            for mod in modifiers:
                obj.modifiers.remove(obj.modifiers[mod])
        except:
            print("Proxy modifier is missing")
            
        context.object.bagapieList.remove(self.index)

        return {'FINISHED'}


class BAGAPIE_OT_proxy(Operator):
    """Create convex hull visible only in the viewport"""
    bl_idname = 'bagapie.proxy'
    bl_label = bagapieModifiers['proxy']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object
        object_types = ['MESH','CURVE']
        return (
            o is not None and 
            o.type in object_types
        )

    disable_proxy:  bpy.props.BoolProperty(default=False)
    found_proxy:  bpy.props.BoolProperty(default=False)
    
    def invoke(self, context, event):
        self.found_proxy = False
        wm = context.window_manager
        targets = bpy.context.selected_objects
        for target in targets:
            if target.type  in ['MESH','CURVE']:
                for modifier in target.modifiers:
                    if modifier.name.startswith("BagaPie_Proxy"):
                        if modifier.show_viewport:
                            print('Proxy Modifier already present on : '+ target.name)
                            self.found_proxy = True
                        else :
                            self.disable_proxy = False
                    elif modifier.type == 'NODES':
                        if modifier.node_group.name.startswith("BagaPie_Proxy") and modifier.show_viewport:
                            print('Proxy Modifier already present on : '+ target.name)
                            self.found_proxy = True
                        else :
                            self.disable_proxy = False
        if self.found_proxy:
            return wm.invoke_props_dialog(self)
        else:
            return self.execute(context)

                        
    def draw(self, context):
        layout = self.layout
        if self.found_proxy:
            layout.label(text = "Proxy found on one or more of the selected objects")
            layout.prop(self, 'disable_proxy', text = "Disable proxy on selected objects ?")

    def execute(self, context):
        targets = bpy.context.selected_objects
        for target in targets:
            if self.disable_proxy:
                if target.type in ['MESH','CURVE']:
                    for modifier in target.modifiers:
                        if modifier.name.startswith("BagaPie_Proxy"):
                            modifier.show_viewport = False
                        elif modifier.type == 'NODES':
                            if modifier.node_group.name.startswith("BagaPie_Proxy"):
                                modifier.show_viewport = False

            elif target.type in ['MESH','CURVE']:
                skip = False
                for modifier in target.modifiers:
                    if modifier.name.startswith("BagaPie_Proxy"):
                        print('Proxy Modifier already present on : '+ target.name)
                        skip = True
                        modifier.show_viewport = True
                    elif modifier.type == 'NODES':
                        if modifier.node_group.name.startswith("BagaPie_Proxy"):
                            print('Proxy Modifier already present on : '+ target.name)
                            skip = True
                            modifier.show_viewport = True

                if skip:
                    continue

                new = bpy.data.objects[target.name].modifiers.new

                nodegroup = "BagaPie_Proxy" # GROUP NAME

                modifier = new(name=nodegroup, type='NODES')
                Add_NodeGroup(self,context,modifier, nodegroup)
                target.modifiers[nodegroup].show_render = False

                mat_proxy = bpy.data.materials.new(name="BagaPie_Proxy")
                mat_proxy.diffuse_color = (random(), random(), random(), 1)

                #Assign material        
                modifier["Input_6"] = mat_proxy
                
                val = {
                    'name': 'proxy', # MODIFIER TYPE
                    'modifiers':[
                        modifier.name, #Modifier Name
                    ]
                }

                item = target.bagapieList.add()
                item.val = json.dumps(val)
        
        return {'FINISHED'}


class BAGAPIE_OT_proxy_add_from_ui(bpy.types.Operator):
    """Add a Proxy Modifier"""
    bl_idname = "bagapie.proxy_add_from_ui"
    bl_label = "Add Proxy Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: bpy.props.StringProperty() # type: ignore

    def execute(self, context):
        from random import random
        obj = bpy.data.objects.get(self.obj_name)
        if not obj:
            return {'CANCELLED'}

        # Check if proxy already exists
        for mod in obj.modifiers:
            if mod.name.startswith("BagaPie_Proxy") or (mod.type == 'NODES' and mod.node_group and mod.node_group.name.startswith("BagaPie_Proxy")):
                mod.show_viewport = True
                return {'FINISHED'}

        # Add new proxy
        nodegroup = "BagaPie_Proxy"
        modifier = obj.modifiers.new(name=nodegroup, type='NODES')
        Add_NodeGroup(self, context, modifier, nodegroup)
        modifier.show_render = False

        mat_proxy = bpy.data.materials.new(name="BagaPie_Proxy")
        mat_proxy.diffuse_color = (random(), random(), random(), 1)
        modifier["Input_6"] = mat_proxy

        val = {
            'name': 'proxy',
            'modifiers': [modifier.name]
        }
        item = obj.bagapieList.add()
        item.val = json.dumps(val)

        return {'FINISHED'}


classes = [
    BAGAPIE_OT_proxy_remove,
    BAGAPIE_OT_proxy,
    BAGAPIE_OT_proxy_add_from_ui,
]