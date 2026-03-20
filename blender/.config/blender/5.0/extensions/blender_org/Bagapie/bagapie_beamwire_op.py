import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import Import_Nodes

class BAGAPIE_OT_beamwire_remove(Operator):
    """ Remove Bagapie Beam Wire modifiers """
    bl_idname = "bagapie.beamwire_remove"
    bl_label = 'Remove Bagapie Beam Wire'

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

        o = context.object
        o.select_set(True)
        bpy.ops.object.delete()

        return {'FINISHED'}


class BAGAPIE_OT_beamwire(Operator):
    """Create Beam Wire"""
    bl_idname = 'bagapie.beamwire'
    bl_label = bagapieModifiers['beamwire']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT')

    def execute(self, context):

        beam = bpy.data.meshes.new('BagaPie_BeamWire')
        beam = bpy.data.objects.new(beam.name, beam)
        
        new = beam.modifiers.new
        nodegroup = "BagaPie_BeamWire" # GROUP NAME
        modifier = new(name=nodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, nodegroup)  

        main_coll = get_or_create_collection("BagaPie")
        coll = get_or_create_collection("BagaPie_BeamWire", main_coll)
        # coll = Collection_Add(self,context)
        coll.objects.link(beam)
        beam.location = bpy.context.scene.cursor.location
        bpy.ops.object.select_all(action='DESELECT')
        beam.select_set(True)
        bpy.context.view_layer.objects.active = beam

        val = {
            'name': 'beamwire', # MODIFIER TYPE
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
def get_or_create_collection(name, parent_collection=None):
    new_collection = None

    # Si une collection parente est fournie, chercher dans ses enfants
    if parent_collection:
        for coll in parent_collection.children:
            if coll.name.startswith(name):
                new_collection = coll
                break
    else:  # Sinon, chercher dans la scène actuelle
        for coll in bpy.context.scene.collection.children:
            if coll.name.startswith(name):
                new_collection = coll
                break

    # Si aucune collection existante n'a été trouvée, en créer une nouvelle
    if new_collection is None:
        new_collection = bpy.data.collections.new(name)
        if parent_collection:
            parent_collection.children.link(new_collection)
        else:
            bpy.context.scene.collection.children.link(new_collection)

    return new_collection

classes = [
    BAGAPIE_OT_beamwire_remove,
    BAGAPIE_OT_beamwire
]