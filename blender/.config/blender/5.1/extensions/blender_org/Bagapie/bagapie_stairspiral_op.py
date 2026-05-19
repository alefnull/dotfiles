import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import get_or_create_collection
from .utils import Import_Nodes

class BAGAPIE_OT_stairspiral_remove(Operator):
    """ Remove Bagapie Spiral Stair modifiers """
    bl_idname = "bagapie.spiralstair_remove"
    bl_label = 'Remove Bagapie Stair Spiral'

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )
    
    index: bpy.props.IntProperty(default=0)
    
    def execute(self, context):

        o = context.object
        o.select_set(True)
        bpy.ops.object.delete()

        return {'FINISHED'}


class BAGAPIE_OT_stairspiral(Operator):
    """Create Spiral Stair"""
    bl_idname = 'bagapie.spiralstair'
    bl_label = bagapieModifiers['spiralstair']['label']
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        beam = bpy.data.meshes.new('BagaPie_StairSpiral')
        beam = bpy.data.objects.new(beam.name, beam)
        
        new = beam.modifiers.new
        nodegroup = "BagaPie_StairSpiral" # GROUP NAME
        modifier = new(name=nodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, nodegroup)  

        coll = Collection_Add(self,context)
        coll.objects.link(beam)
        beam.location = bpy.context.scene.cursor.location
        bpy.ops.object.select_all(action='DESELECT')
        beam.select_set(True)
        bpy.context.view_layer.objects.active = beam

        val = {
            'name': 'spiralstair', # MODIFIER TYPE
            'modifiers':[
                nodegroup, #Modifier Name
            ]
        }

        item = beam.bagapieList.add()
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



###################################################################################
# MANAGE COLLECTION
###################################################################################
def Collection_Add(self, context):
    main_coll = get_or_create_collection("BagaPie")
    array_coll = get_or_create_collection("BagaPie_Stair", main_coll)
    
    return array_coll

classes = [
    BAGAPIE_OT_stairspiral_remove,
    BAGAPIE_OT_stairspiral
]