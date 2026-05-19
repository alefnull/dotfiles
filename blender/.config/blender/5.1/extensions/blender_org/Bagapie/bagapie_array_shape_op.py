import bpy
import json
from bpy.types import Operator
from .presets import bagapieModifiers
from .utils import get_or_create_collection, Add_NodeGroup

class BAGAPIE_OT_array_along_shape_remove(Operator):
    """ Remove Bagapie Array Along Shape modifiers """
    bl_idname = "bagapie.array_along_shape_remove"
    bl_label = 'Remove Bagapie Array Along Shape'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object
        return (
            o is not None and 
            o.type == 'MESH'
        )
    
    index: bpy.props.IntProperty(default=0) # type: ignore
    
    def execute(self, context):
        obj = context.object
        val = json.loads(obj.bagapieList[self.index]['val'])
        try:
            modifiers = val['modifiers']
            modifier = obj.modifiers[modifiers[0]]
            obj.modifiers.remove(modifier)
        except:
            print("Array deform modifier is missing.")
        
        context.object.bagapieList.remove(self.index)
        
        if len(obj.bagapieList) > 0 and obj.bagapieIndex > 0:
            obj.bagapieIndex = obj.bagapieIndex-1

        return {'FINISHED'}


class BAGAPIE_OT_array_along_shape(Operator):
    """Create Array Along Shape"""
    bl_idname = 'bagapie.array_along_shape'
    bl_description = "Select your object(s) then the surface to project"
    bl_label = bagapieModifiers['array_along_shape']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object
        return (
            o is not None and 
            o.type == 'MESH' and
            len(bpy.context.selected_objects)>1
        )

    def execute(self, context):
        # GET OBJECTS
        obj = bpy.context.active_object
        targets = bpy.context.selected_objects
        targets.remove(obj)

        array_coll, array_coll_target = Collection_Instancer(self,context)
        if obj not in list(array_coll_target.objects):
            array_coll_target.objects.link(obj)

        for ob in targets:

            # SETUP COLLECTION
            if ob not in list(array_coll.objects):
                array_coll.objects.link(ob)
            
            # ADD & SETUP MODIFIER
            new = ob.modifiers.new
            nodegroup = "BagaPie_Array_Along_Shape" # GROUP NAME
            modifier = new(name=nodegroup, type='NODES')
            Add_NodeGroup(self,context,modifier, nodegroup)

            modifier['Socket_16'] = array_coll_target

            val = {
                'name': 'array_along_shape', # MODIFIER TYPE
                'modifiers':[
                    modifier.name, #Modifier Name
                ]
            }
            item = ob.bagapieList.add()
            item.val = json.dumps(val)   

        return {'FINISHED'}


###################################################################################
# MANAGE COLLECTION
###################################################################################
def Collection_Instancer(self, context):
    main_coll = get_or_create_collection("BagaPie")
    array_coll = get_or_create_collection("BagaPie_Array_Along_Shape", main_coll)
    array_coll_target = get_or_create_collection("BagaPie_Array_Along_Shape_Target", array_coll)
    return [array_coll, array_coll_target]

###################################################################################
# Remove obj and delete collection
###################################################################################
def RemoveOBJandDeleteColl(self, context, collection):
    for obj in collection.all_objects:
        collection.objects.unlink(obj)
    bpy.data.collections.remove(collection)

classes = [
    BAGAPIE_OT_array_along_shape_remove,
    BAGAPIE_OT_array_along_shape
]