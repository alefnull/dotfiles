import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers

class BAGAPIE_OT_wall_remove(Operator):
    """ Remove Bagapie Wall modifiers """
    bl_idname = "bagapie.wall_remove"
    bl_label = 'Remove Bagapie Wall'

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
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
            print("Wall modifier is missing")
        
        context.object.bagapieList.remove(self.index)

        return {'FINISHED'}


class BAGAPIE_OT_wall(Operator):
    """Creates walls from the edges of the selected object or from curves"""
    bl_idname = 'bagapie.wall'
    bl_label = bagapieModifiers['wall']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )

    wall_height: bpy.props.FloatProperty(
        name="Height",
        default=2.4,
    ) # type: ignore
    wall_depth: bpy.props.FloatProperty(
        name="Depth",
        default=0.2,
    ) # type: ignore
    wall_offset: bpy.props.FloatProperty(
        name="Offset",
        description="Placement du mur vis à vis de son axe.",
        default=0,
        min=0,
        soft_max=1,
    ) # type: ignore

    def execute(self, context):
        target = bpy.context.active_object
        blender_version = bpy.app.version
        if blender_version < (4, 1, 0):
            target.data.use_auto_smooth = True

        wall_weld = target.modifiers.new(name='BagaScrew', type='WELD')
        wall_weld.merge_threshold = 0.01
        
        screw = target.modifiers.new(name='BagaScrew', type='SCREW')
        screw.angle = 0
        screw.steps = 1
        screw.render_steps = 1
        screw.use_smooth_shade = True
        screw.use_normal_calculate = True
        screw.screw_offset = self.wall_height
        
        solid = target.modifiers.new(name='BagaSolidify', type='SOLIDIFY')        
        solid.solidify_mode = 'NON_MANIFOLD'
        solid.thickness = self.wall_depth
        solid.offset = self.wall_offset

        val = {
            'name': 'wall',
            'modifiers':[
                wall_weld.name,
                screw.name,
                solid.name,
            ]
        }

        item = target.bagapieList.add()
        item.val = json.dumps(val)
        
        return {'FINISHED'}

classes = [
    BAGAPIE_OT_wall_remove,
    BAGAPIE_OT_wall
]