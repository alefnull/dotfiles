import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import Add_NodeGroup, get_or_create_collection

class BAGAPIE_OT_floor_remove(Operator):
    """ Remove Bagapie Floor modifiers """
    bl_idname = "bagapie.floor_remove"
    bl_label = 'Remove Bagapie Floor'

    @classmethod
    def poll(cls, context):
        o = context.object
        return (
            o is not None and 
            o.type == 'MESH'
        )
    
    index: bpy.props.IntProperty(default=0) # type: ignore
    
    def execute(self, context):
        o = context.object
        o.select_set(True)
        bpy.ops.object.delete()

        return {'FINISHED'}


class BAGAPIE_OT_floor(Operator):
    """Create Spiral Stair"""
    bl_idname = 'bagapie.floor'
    bl_label = bagapieModifiers['floor']['label']
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        beam = bpy.data.meshes.new('BagaPie_Floor')
        beam = bpy.data.objects.new(beam.name, beam)
        
        new = beam.modifiers.new
        nodegroup = "BagaPie_Floor" # GROUP NAME
        modifier = new(name=nodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, nodegroup)  

        main_coll = get_or_create_collection("BagaPie")
        coll = get_or_create_collection("BagaPie_Floor", main_coll)
        coll.objects.link(beam)
        beam.location = bpy.context.scene.cursor.location
        bpy.ops.object.select_all(action='DESELECT')
        beam.select_set(True)
        bpy.context.view_layer.objects.active = beam

        val = {
            'name': 'floor', # MODIFIER TYPE
            'modifiers':[
                nodegroup, #Modifier Name
            ]
        }
        item = beam.bagapieList.add()
        item.val = json.dumps(val)
        
        return {'FINISHED'}

classes = [
    BAGAPIE_OT_floor_remove,
    BAGAPIE_OT_floor
]