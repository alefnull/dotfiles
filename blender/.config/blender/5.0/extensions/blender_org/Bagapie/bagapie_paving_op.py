import bpy
import json
from bpy.types import Operator
from .presets import bagapieModifiers
from .utils import get_or_create_collection, Add_NodeGroup

class BAGAPIE_OT_paving_remove(Operator):
    """ Remove Bagapie Paving modifiers """
    bl_idname = "bagapie.paving_remove"
    bl_label = 'Remove Bagapie Paving'
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


class BAGAPIE_OT_paving(Operator):
    """Turn faces into Paving"""
    bl_idname = 'bagapie.paving'
    bl_label = bagapieModifiers['paving']['label']
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
        
        nodegroup = "BagaPie_Face_to_Paving" # GROUP NAME
        modifier = new(name=nodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, nodegroup)  

        coll = Collection_Add(self,context)
        coll.objects.link(target)

        val = {
            'name': 'paving', # MODIFIER TYPE
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
    sub_coll = get_or_create_collection("BagaPie_Paving", main_coll)
    return sub_coll

classes = [
    BAGAPIE_OT_paving_remove,
    BAGAPIE_OT_paving
]