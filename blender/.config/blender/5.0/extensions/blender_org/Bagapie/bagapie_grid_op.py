import bpy
import json
from bpy.types import Operator
from .presets import bagapieModifiers
from .utils import get_or_create_collection, Add_NodeGroup

class BAGAPIE_OT_grid_remove(Operator):
    """ Remove Bagapie Grid modifiers """
    bl_idname = "bagapie.grid_remove"
    bl_label = 'Remove Bagapie Grid'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object
        return (
            o is not None and 
            o.type == 'MESH'
        )
    
    index: bpy.props.IntProperty(default=0)
    
    def execute(self, context):        
        obj = context.object
        val = json.loads(obj.bagapieList[self.index]['val'])
        try:
            modifiers = val['modifiers']
            for mod in modifiers:
                obj.modifiers.remove(obj.modifiers[mod])
        except:
            print("Modifier is missing.")
        
        context.object.bagapieList.remove(self.index)
        return {'FINISHED'}


class BAGAPIE_OT_grid(Operator):
    """Turn faces into Grid"""
    bl_idname = 'bagapie.grid'
    bl_label = bagapieModifiers['grid']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object
        return (
            o is not None and 
            o.type == 'MESH'
        )

    def execute(self, context):
        target = bpy.context.active_object
        new = bpy.data.objects[target.name].modifiers.new
        
        nodegroup = "BagaPie_Face_to_Grid" # GROUP NAME
        modifier = new(name=nodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, nodegroup)  

        coll = Collection_Add(self,context)
        coll.objects.link(target)

        val = {
            'name': 'grid', # MODIFIER TYPE
            'modifiers':[nodegroup] #Modifier Name
        }
        item = target.bagapieList.add()
        item.val = json.dumps(val)
        
        return {'FINISHED'}


###################################################################################
# MANAGE COLLECTION
###################################################################################
def Collection_Add(self, context):
    main_coll = get_or_create_collection("BagaPie")
    array_coll = get_or_create_collection("BagaPie_Grid", main_coll)
    return array_coll

classes = [
    BAGAPIE_OT_grid_remove,
    BAGAPIE_OT_grid
]