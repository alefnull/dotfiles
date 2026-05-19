import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import get_or_create_collection, Add_NodeGroup

class BAGAPIE_OT_cable_remove(Operator):
    """ Remove Bagapie Cable modifiers """
    bl_idname = "bagapie.cable_remove"
    bl_label = 'Remove Bagapie Cable'

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'CURVE'
        )
    
    index: bpy.props.IntProperty(default=0)
    
    def execute(self, context):
        
        obj = context.object
        val = json.loads(obj.bagapieList[self.index]['val'])
        try:
            modifiers = val['modifiers']
            modifier = obj.modifiers[modifiers[0]]
            
            coll = modifier["Input_28"]
            RemoveOBJandDeleteColl(self, context, coll)

            for mod in modifiers:
                obj.modifiers.remove(obj.modifiers[mod])
        except:
            print("Some elements (modifier or objects) were missing.")
        
        context.object.bagapieList.remove(self.index)


        return {'FINISHED'}


class BAGAPIE_OT_cable(Operator):
    """Add Cable"""
    bl_idname = 'bagapie.cable'
    bl_label = bagapieModifiers['cable']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )

    def execute(self, context):

        # FIRST STEP

        curve = bpy.data.curves.new('BagaPie_Cable', 'CURVE')
        curve_obj = bpy.data.objects.new(curve.name, curve)
        curve_obj.data.dimensions = '3D'

        targets = bpy.context.selected_objects

        new = curve_obj.modifiers.new

        nodegroup = "BagaPie_Cable" # GROUP NAME

        modifier = new(name=nodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, nodegroup)
        coll_target, coll_cable = Collection_Instancer(self, context, targets[0].name)

        for target in targets:
            if target.name not in coll_cable.objects:
                coll_cable.objects.link(target)
        coll_target.objects.link(curve_obj)

        # SET VALUES
        modifier["Input_28"] = coll_cable

        bpy.context.view_layer.objects.active = curve_obj
        bpy.ops.object.editmode_toggle()
        bpy.context.scene.tool_settings.curve_paint_settings.depth_mode = 'SURFACE'
        bpy.ops.wm.tool_set_by_id(name="builtin.draw")

        val = {
            'name': 'cable', # MODIFIER TYPE
            'modifiers':[
                nodegroup, #Modifier Name
            ]
        }

        item = curve_obj.bagapieList.add()
        item.val = json.dumps(val)
        
        return {'FINISHED'}


###################################################################################
# MANAGE COLLECTION
###################################################################################
def Collection_Instancer(self, context, name):
    main_coll = get_or_create_collection("BagaPie")
    cable_coll = get_or_create_collection("BagaPie_Cable", main_coll)

    cable_coll_target = None
    cable_coll_target_name = f"BagaPie_Cable_{name}"
    collection = cable_coll or bpy.context.scene.collection

    if any(coll.name.startswith(cable_coll_target_name) for coll in collection.children):
        cable_coll_target_name = get_unique_name(collection, cable_coll_target_name)

    if cable_coll_target is None:
        cable_coll_target = bpy.data.collections.new(cable_coll_target_name)
        (cable_coll or bpy.context.scene.collection).children.link(cable_coll_target)

    return [cable_coll, cable_coll_target]

def get_unique_name(collection, target_name):
    counter = 1
    new_name = f"{target_name}_{counter:03d}"
    while any(coll.name == new_name for coll in collection.children):
        counter += 1
        new_name = f"{target_name}_{counter:03d}"
    return new_name


###################################################################################
# Remove obj and delete collection
###################################################################################
def RemoveOBJandDeleteColl(self, context, collection):

    for obj in collection.all_objects:
        collection.objects.unlink(obj)

    bpy.data.collections.remove(collection)

classes = [
    BAGAPIE_OT_cable_remove,
    BAGAPIE_OT_cable
]