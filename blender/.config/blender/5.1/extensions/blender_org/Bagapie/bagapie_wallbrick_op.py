import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import Import_Nodes

class BAGAPIE_OT_wallbrick_remove(Operator):
    """ Remove Bagapie Wall Brick modifiers """
    bl_idname = "bagapie.wallbrick_remove"
    bl_label = 'Remove Bagapie Wall Brick'

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH' or 'CURVE'
        )
    
    index: bpy.props.IntProperty(default=0)
    
    def execute(self, context):
        
        obj = context.object
        val = json.loads(obj.bagapieList[self.index]['val'])
        try:
            modifiers = val['modifiers']

            if obj.type == 'MESH':
                obj.modifiers.remove(obj.modifiers[modifiers[0]])
            else:
                obj.modifiers.remove(obj.modifiers[modifiers[1]])
        except:
            print("Wall modifier is missing")
        
        context.object.bagapieList.remove(self.index)

        return {'FINISHED'}


class BAGAPIE_OT_wallbrick(Operator):
    """Create Wall Brick from edges or curve"""
    bl_idname = 'bagapie.wallbrick'
    bl_label = bagapieModifiers['wallbrick']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object
        allowed_types = ['MESH','CURVE']
        return (
            o is not None and 
            o.type in allowed_types 
        )

    def execute(self, context):
        target = bpy.context.active_object
        new = bpy.data.objects[target.name].modifiers.new

        if target.type == 'MESH':
            nodegroup = "BagaPie_Wall_Brick_Mesh" # GROUP NAME
        else:
            nodegroup = "BagaPie_Wall_Brick_Curve"

        modifier = new(name=nodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, nodegroup)


        val = {
            'name': 'wallbrick', # MODIFIER TYPE
            'modifiers':[
                "BagaPie_Wall_Brick_Mesh", #Modifier Name
                "BagaPie_Wall_Brick_Curve",
            ]
        }

        item = target.bagapieList.add()
        item.val = json.dumps(val)
        
        return {'FINISHED'}


###################################################################################
# ADD NODEGROUP TO THE MODIFIER
###################################################################################
def Add_NodeGroup(self,context,modifier, nodegroup_name):
    try:
        modifier.node_group = bpy.data.node_groups[nodegroup_name]
    except:
        Import_Nodes(self,context,nodegroup_name)
        modifier.node_group = bpy.data.node_groups[nodegroup_name]

classes = [
    BAGAPIE_OT_wallbrick_remove,
    BAGAPIE_OT_wallbrick
]