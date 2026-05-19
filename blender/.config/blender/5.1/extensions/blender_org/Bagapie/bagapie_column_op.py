import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import get_or_create_collection, Add_NodeGroup

class BAGAPIE_OT_column_remove(Operator):
    """ Remove Bagapie Column modifiers """
    bl_idname = "bagapie.column_remove"
    bl_label = 'Remove Bagapie Column'

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


class BAGAPIE_OT_column(Operator):
    """Create Column"""
    bl_idname = 'bagapie.column'
    bl_label = bagapieModifiers['column']['label']
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        beam = bpy.data.meshes.new('BagaPie_Column')
        beam = bpy.data.objects.new(beam.name, beam)
        
        new = beam.modifiers.new
        nodegroup = "BagaPie_Column" # GROUP NAME
        modifier = new(name=nodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, nodegroup)  

        main_coll = get_or_create_collection("BagaPie")
        coll = get_or_create_collection("BagaPie_Column", main_coll)
        # coll = Collection_Add(self,context,"BagaPie_Column")
        coll.objects.link(beam)
        beam.location = bpy.context.scene.cursor.location
        bpy.ops.object.select_all(action='DESELECT')
        beam.select_set(True)
        bpy.context.view_layer.objects.active = beam

        val = {
            'name': 'column', # MODIFIER TYPE
            'modifiers':[
                nodegroup, #Modifier Name
            ]
        }

        item = beam.bagapieList.add()
        item.val = json.dumps(val)
        
        return {'FINISHED'}

classes = [
    BAGAPIE_OT_column_remove,
    BAGAPIE_OT_column
]