import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import Import_Nodes

class BAGAPIE_OT_instancesdisplace_remove(Operator):
    """ Remove Bagapie Instance Displace modifiers """
    bl_idname = "bagapie.instancesdisplace_remove"
    bl_label = 'Remove Bagapie Wall Brick'

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

            obj.modifiers.remove(obj.modifiers[modifiers[0]])
        except:
            print("Some elements (modifier or objects) were missing.")
        
        context.object.bagapieList.remove(self.index)
        
        if len(obj.bagapieList) > 0 and obj.bagapieIndex > 0:
            obj.bagapieIndex = obj.bagapieIndex-1

        return {'FINISHED'}


class BAGAPIE_OT_instancesdisplace(Operator):
    """Create Bagapie Instance Displace"""
    bl_idname = 'bagapie.instancesdisplace'
    bl_label = bagapieModifiers['instancesdisplace']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object
        object_types = ['MESH','CURVE']
        return (
            o is not None and 
            o.type in object_types
        )

    def execute(self, context):
        target = bpy.context.active_object
        new = bpy.data.objects[target.name].modifiers.new

        nodegroup = "BagaPie_Instances_Displace"

        modifier = new(name=nodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, nodegroup)
        

        val = {
            'name': 'instancesdisplace', # MODIFIER TYPE
            'modifiers':[
                        modifier.name, #Modifier Name
            ]
        }

        if len(target.bagapieList) > 0:
            target.bagapieIndex = target.bagapieIndex+1
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
    BAGAPIE_OT_instancesdisplace_remove,
    BAGAPIE_OT_instancesdisplace,
]