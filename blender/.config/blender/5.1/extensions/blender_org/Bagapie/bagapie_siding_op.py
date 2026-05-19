import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import Import_Nodes

class BAGAPIE_OT_siding_remove(Operator):
    """ Remove Bagapie Siding modifiers """
    bl_idname = "bagapie.siding_remove"
    bl_label = 'Remove Bagapie Siding'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH' and 
            context.mode == 'OBJECT'
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
            print("Siding modifier is missing")
        
        context.object.bagapieList.remove(self.index)

        return {'FINISHED'}


class BAGAPIE_OT_siding(Operator):
    """Add Siding generator on the selected mesh. Only on tangent faces with X/Y/Z axis."""
    bl_idname = 'bagapie.siding'
    bl_label = bagapieModifiers['siding']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH' and 
            context.mode == 'OBJECT'
        )

    def execute(self, context):
        target = bpy.context.active_object
        new = bpy.data.objects[target.name].modifiers.new

        nodegroup = "BagaPie_Siding" # GROUP NAME

        modifier = new(name=nodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, nodegroup)
            

        val = {
            'name': 'siding', # MODIFIER TYPE
            'modifiers':[
                modifier.name, #Modifier Name
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
    BAGAPIE_OT_siding_remove,
    BAGAPIE_OT_siding
]