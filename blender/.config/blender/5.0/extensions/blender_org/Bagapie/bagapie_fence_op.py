import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import get_or_create_collection, Add_NodeGroup

class BAGAPIE_OT_fence_remove(Operator):
    """ Remove Bagapie Fence modifiers """
    bl_idname = "bagapie.fence_remove"
    bl_label = 'Remove Bagapie Fence'

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

            for mod in modifiers:
                obj.modifiers.remove(obj.modifiers[mod])
        except:
            print("Some elements (modifier or objects) were missing.")
        
        context.object.bagapieList.remove(self.index)
        return {'FINISHED'}


class BAGAPIE_OT_fence(Operator):
    """Add Fence"""
    bl_idname = 'bagapie.fence'
    bl_label = bagapieModifiers['fence']['label']
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        curve_obj = bpy.context.active_object
        selected = bpy.context.selected_objects
            
        if curve_obj is not None and curve_obj.type == 'CURVE' and curve_obj in selected:
            new = bpy.data.objects[curve_obj.name].modifiers.new
        else:
            curve = bpy.data.curves.new('BagaPie_Fence', 'CURVE')
            curve_obj = bpy.data.objects.new(curve.name, curve)
            curve_obj.data.dimensions = '3D'
            curve_obj.data.resolution_u = 64
            curve_obj.data.render_resolution_u = 64
            curve_obj.location = bpy.context.scene.cursor.location

            new = bpy.data.objects[curve.name].modifiers.new

        nodegroup = "BagaPie_Fence" # GROUP NAME

        modifier = new(name=nodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, nodegroup)

        main_coll = get_or_create_collection("BagaPie")
        coll_target = get_or_create_collection("BagaPie_Fence", main_coll)
        # coll_target = Collection_Add(self,context,"BagaPie_Fence")
        if coll_target not in curve_obj.users_collection:
            coll_target.objects.link(curve_obj)

        bpy.context.view_layer.objects.active = curve_obj
        bpy.ops.object.editmode_toggle()
        bpy.context.scene.tool_settings.curve_paint_settings.depth_mode = 'SURFACE'
        bpy.context.scene.tool_settings.curve_paint_settings.error_threshold = 15
        bpy.ops.wm.tool_set_by_id(name="builtin.draw")
        
        val = {
            'name': 'fence', # MODIFIER TYPE
            'modifiers':[
                nodegroup, #Modifier Name
            ]
        }

        item = curve_obj.bagapieList.add()
        item.val = json.dumps(val)
        
        return {'FINISHED'}

classes = [
    BAGAPIE_OT_fence_remove,
    BAGAPIE_OT_fence
]