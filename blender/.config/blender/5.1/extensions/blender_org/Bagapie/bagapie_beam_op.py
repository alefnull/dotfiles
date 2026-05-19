import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import Add_NodeGroup, get_or_create_collection

class BAGAPIE_OT_beam_remove(Operator):
    """ Remove Bagapie Beam modifiers """
    bl_idname = "bagapie.beam_remove"
    bl_label = 'Remove Bagapie Beam'

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


class BAGAPIE_OT_beam(Operator):
    """Create Beam H"""
    bl_idname = 'bagapie.beam'
    bl_label = bagapieModifiers['beam']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT')

    def execute(self, context):

        beam = bpy.data.meshes.new('BagaPie_Beam')
        beam = bpy.data.objects.new(beam.name, beam)
        
        new = beam.modifiers.new
        nodegroup = "BagaPie_Beam" # GROUP NAME
        modifier = new(name=nodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, nodegroup)  


        main_coll = get_or_create_collection("BagaPie")
        coll = get_or_create_collection("BagaPie_Beam", main_coll)
        # coll = Collection_Add(self,context)
        coll.objects.link(beam)
        beam.location = bpy.context.scene.cursor.location
        bpy.ops.object.select_all(action='DESELECT')
        beam.select_set(True)
        bpy.context.view_layer.objects.active = beam

        val = {
            'name': 'beam', # MODIFIER TYPE
            'modifiers':[
                nodegroup, #Modifier Name
            ]
        }

        item = beam.bagapieList.add()
        item.val = json.dumps(val)
        
        return {'FINISHED'}

classes = [
    BAGAPIE_OT_beam_remove,
    BAGAPIE_OT_beam
]