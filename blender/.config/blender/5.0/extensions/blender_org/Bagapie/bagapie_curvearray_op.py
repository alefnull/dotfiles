import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import Warning

class BAGAPIE_OT_curvearray_remove(Operator):
    """ Remove Bagapie Wall modifiers """
    bl_idname = "bagapie.curvearray_remove"
    bl_label = 'Remove Bagapie Array On Curve'

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'CURVE' or 'MESH'
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

class BAGAPIE_OT_curvearray(Operator):
    """Creates an array of the selected object on the active object (it must be a curve). Select the curve last. Note: This function applies the transform and remove the multi-user data"""
    bl_idname = "wm.curvearray"
    bl_label = bagapieModifiers['curvearray']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'CURVE'
        )

# PANEL INPUT
    curvearray_relative_offset: bpy.props.BoolProperty(
        name="Relative Offset",
        default=True,
    ) # type: ignore
    rovec: bpy.props.FloatProperty(
        name="Distance",
        description="Distance between objects based on the size of the instance.",
        default=1,
        min=0,
        soft_max=1000,
    ) # type: ignore
    con: bpy.props.BoolProperty(
        name="Constant Offset",
        default=True,
    ) # type: ignore
    covec: bpy.props.FloatProperty(
        name="Distance",
        description="Constant distance between objects.",
        default=0,
        min=0,
        soft_max=1000,
    ) # type: ignore
    curvearray_axis: bpy.props.EnumProperty(
        name="Dirrection",
        items=[('POS_X', "X", ""),
               ('POS_Y', "Y", ""),
               ('POS_Z', "Z", ""),
               ('NEG_X', "-X", ""),
               ('NEG_Y', "-Y", ""),
               ('NEG_Z', "-Z", ""),
               ],
        default='POS_X'
    ) # type: ignore

    def execute(self, context):

        # FILTERING SELECTED
        selected_curve = bpy.context.selected_objects
        target = bpy.context.active_object
        selected_curve_valid = []
        error = True

        for mesh in selected_curve:
            if mesh.type == 'MESH' or mesh.type == 'CURVE':
                selected_curve_valid.append(mesh)
                if mesh != target:
                    error = False

        if error:
            Warning("Wrong selection. Select objects then curve.", "WARNING", 'ERROR') 
            return {'FINISHED'}

        elif not error: 
            bpy.ops.object.select_all(action='DESELECT')
            for ob in selected_curve_valid:
                ob.select_set(True)
            if selected_curve_valid is not None:
                selected_curve_valid.remove(target)


                # PREPARE MESH
                if target.type == "CURVE" and selected_curve_valid is not None:
                    try:
                        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
                    except:
                        Warning("Multi User data detected. If necessary apply object rotation and scale", "INFO", 'ERROR') 
                    bpy.ops.view3d.snap_cursor_to_active()
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.curve.select_all(action='SELECT')
                    bpy.ops.curve.radius_set(radius=1.0)
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)

                # ADD MODIFIER
                    for instance in selected_curve_valid:
                        new = bpy.data.objects[instance.name].modifiers.new
                        arr = new(name='BagaArray', type='ARRAY')
                        cur = new(name='BagaCurve', type='CURVE')
                        arr.fit_type = 'FIT_CURVE'
                        arr.curve = target
                        cur.object = target
                        cur.deform_axis = self.curvearray_axis

                        arr.use_relative_offset = self.curvearray_relative_offset
                        arr.use_constant_offset = self.con
                        arr.relative_offset_displace[0] = self.rovec
                        arr.constant_offset_displace[0] = self.covec

                    bpy.context.view_layer.objects.active = target

                # CUSTOM PROPERTIES
                    val = {
                        'name': 'curvearray',
                        'modifiers':[
                            arr.name,
                            cur.name,
                        ]
                    }

                    for ob in selected_curve_valid:
                        item = ob.bagapieList.add()
                        item.val = json.dumps(val)
                    
                    return {'FINISHED'}


# def Warning(message = "", title = "Message Box", icon = 'INFO'):

#     def draw(self, context):
#         self.layout.label(text=message)

#     bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

classes = [
    BAGAPIE_OT_curvearray_remove,
    BAGAPIE_OT_curvearray
]