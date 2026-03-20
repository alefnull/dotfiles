import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import Add_NodeGroup

class BAGAPIE_OT_deform_remove(Operator):
    """ Remove Bagapie Deform modifiers """
    bl_idname = "bagapie.deform_remove"
    bl_label = 'Remove Bagapie Deform'

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
            print("Blend modifier is missing")
        
        context.object.bagapieList.remove(self.index)

        return {'FINISHED'}


class BAGAPIE_OT_deform(Operator):
    """Create convex hull visible only in the viewport"""
    bl_idname = 'bagapie.deform'
    bl_label = bagapieModifiers['deform']['label']
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

        nodegroup = "BagaPie_BlendTwist" # GROUP NAME

        modifier = new(name=nodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, nodegroup)
            
        val = {
            'name': 'deform', # MODIFIER TYPE
            'modifiers':[
                nodegroup, #Modifier Name
            ]
        }

        item = target.bagapieList.add()
        item.val = json.dumps(val)
        
        return {'FINISHED'}



classes = [
    BAGAPIE_OT_deform_remove,
    BAGAPIE_OT_deform
]