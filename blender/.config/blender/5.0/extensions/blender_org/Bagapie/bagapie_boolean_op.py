import bpy
import json
from bpy.types import Operator

class BAGAPIE_OT_boolean_remove(Operator):
    """Remove Bagapie Boolean modifiers"""
    bl_idname = "bagapie.boolean_remove"
    bl_label = 'Remove Bagapie Displace'
    bl_options = {'REGISTER', 'UNDO'}

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
            bool_obj = bpy.data.objects[modifiers[5]]

            for mod in modifiers:        
                if mod.startswith(("BagaBool","BagaBevel")) and not mod.startswith("BagaBevelObj"):
                    obj.modifiers.remove(obj.modifiers[mod])
                else:
                    if mod != modifiers[5]:
                        bool_obj.modifiers.remove(bool_obj.modifiers[mod])
            
            bpy.data.objects.remove(bool_obj)
        except:
            print("Some elements (modifier or objects) were missing.")

        context.object.bagapieList.remove(self.index)
        if len(obj.bagapieList) <= obj.bagapieIndex and obj.bagapieIndex != 0:
            obj.bagapieIndex -= 1

        return {'FINISHED'}

class BAGAPIE_OT_boolean(Operator):
    """Draw quick boolean on the selected object"""
    bl_idname = "wm.boolean"
    bl_label = "Boolean"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )
        
 # UI PROP
    bool_use_self: bpy.props.BoolProperty(
        name="Use Self",
        default=True
    )
    bool_use_bevel_segcount: bpy.props.IntProperty(
        name="Segment Count",
        default=3,
        min=1,
        soft_max=10,
    )
    bool_use_bevel_size: bpy.props.FloatProperty(
        name="Bevel Size",
        default=0,
        min=0.0001,
    )
    bool_use_mirror_x: bpy.props.BoolProperty(
        name="X",
        default=False
        )
    bool_use_mirror_y: bpy.props.BoolProperty(
        name="Y",
        default=False
    )
    bool_use_mirror_z: bpy.props.BoolProperty(
        name="Z",
        default=False
    )
    solver_type: bpy.props.EnumProperty(
        name="Solver",
        items=[('EXACT', "Exact",""),
               ('FAST', "Fast",""),
               ],
        default='EXACT',
    )
    operation_type: bpy.props.EnumProperty(
        name="Type",
        items=[('UNION', "Union",""),
               ('DIFFERENCE', "Difference",""),
               ],
        default='DIFFERENCE',
    )
    thickness: bpy.props.FloatProperty(
        name="Solidify",
        default=0,
        min=0,
    )
    offset: bpy.props.FloatProperty(
        name="Solidify Offset",
        default=1,
        min=-1,
        max=1,
    )
    bevel_width: bpy.props.FloatProperty(
        name="Bevel Size",
        default=0,
        min=0,
    )
    bevel_segments: bpy.props.IntProperty(
        name="Segments",
        default=1,
        min=1,
    )

 # EXE
    def execute(self, context):
    # COLLECTION

        target = bpy.context.active_object

        main_coll = get_or_create_collection("BagaPie")
        bool_coll = get_or_create_collection("BagaPie_Boolean", main_coll)

        new_mo = bpy.data.objects[target.name].modifiers.new
    # TARGET
        bool_bool = new_mo(name='BagaBool', type='BOOLEAN')
        # ADD BEVEL

        bool_bev = new_mo(name='BagaBevel', type='BEVEL')
        bool_bev.segments = self.bool_use_bevel_segcount
        bool_bev.width = self.bool_use_bevel_size

        bool_mesh = bpy.data.meshes.new('BagaPie_Bool_'+str(len(target.bagapieList)))
        bool_obj = bpy.data.objects.new("BagaPie_Bool_"+str(len(target.bagapieList)), bool_mesh)
        # bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=True, align='WORLD',
        #                                  location=target.location, scale=(1, 1, 1))
        # bpy.ops.mesh.delete(type='VERT')
        # bpy.ops.object.editmode_toggle()
        # bool_obj = bpy.context.object
        # bool_obj.name = "BagaPie_Bool_"+str(len(target.bagapieList))
        bool_coll.objects.link(bool_obj)
        bpy.ops.object.select_all(action='DESELECT')

        # Set a given object to be active and selected
        bool_obj.select_set(True)
        bpy.context.view_layer.objects.active = bool_obj
        bool_obj.display_type = 'BOUNDS'
        # bool_obj_vis = bool_obj.cycles_visibility
        bool_obj.visible_camera = False
        bool_obj.visible_diffuse = False
        bool_obj.visible_glossy = False
        bool_obj.visible_transmission = False
        bool_obj.visible_volume_scatter = False
        bool_obj.visible_shadow = False
        # bool_coll = bpy.data.collections["BagaPie_Boolean"]
        # bpy.ops.collection.objects_remove_all()

    # BOOL OBJECT
        bool_add_modifier = bpy.data.objects[bool_obj.name].modifiers.new
        bool_disp = bool_add_modifier(name='BagaDisp', type='DISPLACE')
        # ADD BOOLEAN
        bool_bool.object = bool_obj
        bool_bool.use_self = self.bool_use_self
        bool_bool.solver = self.solver_type
        bool_bool.operation = self.operation_type
        bool_disp.strength = 0.005
        bool_disp.show_in_editmode = True
        # ADD BEVEL
        bool_bev_obj = bool_add_modifier(name='BagaBevelObj', type='BEVEL')
        bool_bev_obj.width = self.bevel_width
        bool_bev_obj.segments = self.bevel_segments
        # ADD SOLIDIFY
        bool_solidify = bool_add_modifier(name='BagaSolidify', type='SOLIDIFY')
        if self.thickness > 0:
            bool_solidify.show_viewport = True
            bool_solidify.show_render = True
            bool_solidify.show_in_editmode = True
        else:
            bool_solidify.show_viewport = False
            bool_solidify.show_render = False
            bool_solidify.show_in_editmode = False
        bool_solidify.thickness = self.thickness
        bool_solidify.offset = self.offset
        # ADD MIRROR
        bool_mirr = bool_add_modifier(name='BagaMirror', type='MIRROR')
        bool_mirr.use_axis[0] = self.bool_use_mirror_x
        bool_mirr.use_axis[1] = self.bool_use_mirror_y
        bool_mirr.use_axis[2] = self.bool_use_mirror_z
        bool_mirr.mirror_object = target

        bpy.context.view_layer.objects.active = bool_obj
        bool_obj.parent = target
        bpy.ops.object.editmode_toggle()
        bpy.ops.wm.tool_set_by_id(name="builtin.primitive_cube_add")

    # CUSTOM PROPERTIES
        val = {
              'name': 'boolean',
              'modifiers':[
                          bool_bool.name,
                          bool_bev.name,
                          bool_mirr.name,
                          bool_bev_obj.name,
                          bool_solidify.name,
                          bool_obj.name,
                          bool_disp.name
                          ]
        }

        item = target.bagapieList.add()
        item.val = json.dumps(val)

        return {'FINISHED'}

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
    BAGAPIE_OT_boolean_remove,
    BAGAPIE_OT_boolean
]