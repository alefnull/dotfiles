import bpy
import json
from bpy.types import Operator
from .utils import Import_Nodes, Warning

class BAGAPIE_OT_array_remove(Operator):
    """ Remove Bagapie Array modifiers """
    bl_idname = "bagapie.array_remove"
    bl_label = 'Remove Bagapie Array'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH' or 'CURVE'
        )
    
    index: bpy.props.IntProperty(default=0) # type: ignore
    
    def execute(self, context):
        
        obj = context.object
        val = json.loads(obj.bagapieList[self.index]['val'])
        modifiers = val['modifiers']
        try:
            array = obj.modifiers[modifiers[0]]
            array_nde_group = array.node_group

            for node in array_nde_group.nodes:
                if node.type == 'POINT_INSTANCE':
                    coll = node.inputs[2].default_value
                    for ob in coll.objects:
                        coll.objects.unlink(ob) 
            
                        bpy.data.collections.remove(coll)
        except:
            print("Missing Collection in Array Modifier")

        try:
            obj.modifiers.remove(array)
        except:
            print("Array modifier is missing")

        print(len(obj.bagapieList))
        print(obj.bagapieIndex)

        if len(obj.bagapieList) > 0 and obj.bagapieIndex > 0:
            obj.bagapieIndex = obj.bagapieIndex-1
        
        context.object.bagapieList.remove(self.index)

        return {'FINISHED'}

class BAGAPIE_OT_array(Operator):
    """Create an array with the selected object (s)"""
    bl_idname = "wm.array"
    bl_label = "Array"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type in ['MESH','CURVE']
        )

    # UI PANEL
    array_type: bpy.props.EnumProperty(
        name="Array Type",
        items=[('LINE', "Line",""),
               ('GRID', "Grid",""),
               ('CIRCLE', "Circle",""),
               ('CURVE', "Curve","")
               ],
        default='LINE'
    ) # type: ignore
    array_count: bpy.props.IntProperty( # COUNT
        name="Count",
        default=2,
        min=1
    ) # type: ignore
    array_count_x: bpy.props.IntProperty(
        name="Count X",
        default=2,
        min=1
    ) # type: ignore
    array_count_y: bpy.props.IntProperty(
        name="Count Y",
        default=2,
        min=1
    ) # type: ignore
    array_count_circle: bpy.props.IntProperty(
        name="Count",
        default=8,
        min=1
    ) # type: ignore
    array_ring_count_circle: bpy.props.IntProperty(
        name="Ring Count",
        default=1,
        min=1
    ) # type: ignore
    array_constant_distance: bpy.props.FloatProperty(
        name="Constant Distance",
        default=1,
        min=0.01
    ) # type: ignore
    array_relative_offset: bpy.props.FloatVectorProperty( # RELATIVE OFFSET
        name="Relative Offset",
        default=[1, 0, 0]
    ) # type: ignore
    array_relative_offset_x: bpy.props.FloatProperty(
        name="Relative Offset X",
        default=1,
    ) # type: ignore
    array_relative_offset_y: bpy.props.FloatProperty(
        name="Relative Offset Y",
        default=1,
    ) # type: ignore
    array_constant_offset: bpy.props.FloatVectorProperty( # CONSTANT OFFSET
        name="Constant Offset",
        default=[0, 0, 0]
    ) # type: ignore
    array_constant_offset_x: bpy.props.FloatProperty(
        name="Constant Offset X",
        default=0,
    ) # type: ignore
    array_constant_offset_y: bpy.props.FloatProperty(
        name="Constant Offset Y",
        default=0,
    ) # type: ignore
    array_radius: bpy.props.FloatProperty(
        name="Radius",
        default=1,
        min=0
    ) # type: ignore
    array_rings_offset: bpy.props.FloatProperty(
        name="Rings Offset",
        default=1,
        min=0
    ) # type: ignore
    array_rings_offset_z: bpy.props.FloatProperty(
        name="Rings Offset Z",
        default=0,
        min=0
    ) # type: ignore
    array_curve_length: bpy.props.FloatProperty(
        name="Length",
        default=1,
        min=0
    ) # type: ignore
    array_randpos: bpy.props.FloatVectorProperty( # RANDOM
        name="Random Position",
        default=[0, 0, 0]
    ) # type: ignore
    array_randrot: bpy.props.FloatVectorProperty(
        name="Random Rotation",
        default=[0, 0, 0]
    ) # type: ignore
    array_randscale: bpy.props.FloatProperty(
        name="Random Scale",
        default=0,
        min=0
    ) # type: ignore
    array_align: bpy.props.BoolProperty( # OTHER
        name="Align to Center",
        default=True
    ) # type: ignore
    array_align_float: bpy.props.FloatProperty(
        name="Align to Center",
        default=1,
        min=0,
        max=1
    ) # type: ignore
    array_vector_to_be_aligned: bpy.props.FloatVectorProperty(
        name="Vector to be Aligned",
        default=[0, 0, 1]
    ) # type: ignore
    array_midlevel_x: bpy.props.FloatProperty(
        name="Midlevel X",
        default=0.5,
        min=-0.5,
        max=0.5
    ) # type: ignore
    array_midlevel_y: bpy.props.FloatProperty(
        name="Midlevel Y",
        default=0.5,
        min=-0.5,
        max=0.5
    ) # type: ignore
    array_rotation: bpy.props.FloatVectorProperty(
        name="Rotation",
        default=[0, 0, 0]
    ) # type: ignore
    array_use_constant_distance: bpy.props.BoolProperty(
        name="Use Constant Distance",
        default=True
    ) # type: ignore
    array_use_count: bpy.props.BoolProperty(
        name="Use Count",
        default=False
    ) # type: ignore
    seed: bpy.props.IntProperty(
        name="Seed",
        default=1,
        min=0
    ) # type: ignore

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, "array_type")

        if self.array_type == 'LINE':
            box.prop(self, "array_count")
            box = layout.box()
            box.prop(self, "array_constant_offset")
            box.prop(self, "array_relative_offset")
            box.prop(self, "array_randpos")
            box.prop(self, "array_randrot")
            box.prop(self, "array_randscale")
            box.prop(self, "seed")

        if self.array_type == 'GRID':
            box.prop(self, "array_count_x")
            box.prop(self, "array_count_y")
            box = layout.box()
            box = box.column(align=True)
            box.prop(self, "array_constant_offset_x")
            box.prop(self, "array_constant_offset_y")
            box.prop(self, "array_relative_offset_x")
            box.prop(self, "array_relative_offset_y")
            box.prop(self, "array_midlevel_x")
            box.prop(self, "array_midlevel_y")
            box = layout.box()
            box.prop(self, "array_randpos")
            box.prop(self, "array_randrot")
            box.prop(self, "array_randscale")
            box.prop(self, "seed")

        if self.array_type == 'CIRCLE':
            box.prop(self, "array_count_circle")
            box.prop(self, "array_ring_count_circle")
            box.prop(self, "array_use_constant_distance")
            box = layout.box()
            box.prop(self, "array_radius")
            box.prop(self, "array_rings_offset")
            box.prop(self, "array_rings_offset_z")
            box.prop(self, "array_constant_distance")
            box = layout.box()
            box.prop(self, "array_rotation")
            box.prop(self, "array_align")
            box = layout.box()
            box.prop(self, "array_randpos")
            box.prop(self, "array_randrot")
            box.prop(self, "array_randscale")
            box.prop(self, "seed")
            
        if self.array_type == 'CURVE':
            box.prop(self, "array_curve_length")
            box.prop(self, "array_use_count")
            box.prop(self, "array_count")
            box = layout.box()
            box.prop(self, "array_rotation")
            box.prop(self, "array_align_float")
            box.prop(self, "array_vector_to_be_aligned")
            box = layout.box()
            box.prop(self, "array_randpos")
            box.prop(self, "array_randrot")
            box.prop(self, "array_randscale")
            box.prop(self, "seed")

    def execute(self, context):

        # FIRST STEP
        array_target = bpy.context.active_object # Get active object
        array_selected = bpy.context.selected_objects

        # WARNING AND TOOLTIPS
        if self.array_type == 'CURVE' and array_target.type != 'CURVE' and len(array_selected) == 0:
            Warning(message = "No object selected.", title = "Warning", icon = 'ERROR')
            return {'FINISHED'}

        if self.array_type == 'CURVE' and array_target.type != 'CURVE' and len(array_selected) == 1:
            Warning(message = "You must select a curve last.", title = "Warning", icon = 'ERROR')
            return {'FINISHED'}
        
        if self.array_type == 'CURVE' and array_target.type != 'CURVE' and len(array_selected) > 1:
            Warning(message = "Active object must be a curve.", title = "Warning", icon = 'ERROR')
            return {'FINISHED'}

        for ob in array_selected:
            if ob != array_target:
                array_curve = array_target
                array_target = ob
                break
        
        if self.array_type == 'CURVE' and len(array_selected) == 1:
            Warning(message = "You must select a source object.", title = "Warning", icon = 'ERROR')
            return {'FINISHED'}

        if len(array_selected) > 2:
            Warning(message = "Array only supports one object. You must repeat the action for each object.", title = "Tips", icon = 'INFO')


        # CREATE MODIFIER
        new = bpy.data.objects[array_target.name].modifiers.new
        array = new(name="BagaArray_" + array_target.name, type='NODES')

        # LINE TYPE ARRAY
        if self.array_type == 'LINE':
            nodegroup = "BagaPie_Array_Line"
            Add_NodeGroup(self,context,array, nodegroup)

            # SET VALUES
            array["Input_4"] = self.array_count
            array["Input_3"][0] = self.array_constant_offset[0]
            array["Input_5"][0] = self.array_relative_offset[0]
            array["Input_6"][0] = self.array_randpos[0]
            array["Input_7"][0] = self.array_randrot[0]
            array["Input_3"][1] = self.array_constant_offset[1]
            array["Input_5"][1] = self.array_relative_offset[1]
            array["Input_6"][1] = self.array_randpos[1]
            array["Input_7"][1] = self.array_randrot[1]
            array["Input_3"][2] = self.array_constant_offset[2]
            array["Input_5"][2] = self.array_relative_offset[2]
            array["Input_6"][2] = self.array_randpos[2]
            array["Input_7"][2] = self.array_randrot[2]
            array["Input_8"] = self.array_randscale
            array["Input_9"] = self.seed
            
        # GRID TYPE ARRAY
        elif self.array_type == 'GRID':
            nodegroup = "BagaPie_Array_Grid"
            Add_NodeGroup(self,context,array, nodegroup)

            # SET VALUES
            array["Input_2"] = self.array_count_x
            array["Input_9"] = self.array_count_y
            array["Input_3"] = self.array_constant_offset_x
            array["Input_11"] = self.array_constant_offset_y
            array["Input_4"] = self.array_relative_offset_x
            array["Input_10"] = self.array_relative_offset_y
            array["Input_12"] = self.array_midlevel_x
            array["Input_13"] = self.array_midlevel_y
            array["Input_5"][0] = self.array_randpos[0]
            array["Input_6"][0] = self.array_randrot[0]
            array["Input_5"][1] = self.array_randpos[1]
            array["Input_6"][1] = self.array_randrot[1]
            array["Input_5"][2] = self.array_randpos[2]
            array["Input_6"][2] = self.array_randrot[2]
            array["Input_8"] = self.array_randscale
            array["Input_7"] = self.seed

        # CIRCLE TYPE ARRAY
        elif self.array_type == 'CIRCLE':
            nodegroup = "BagaPie_Array_Circle"
            Add_NodeGroup(self,context,array, nodegroup)

            # SET VALUES
            array["Input_2"] = self.array_count_circle
            array["Input_3"] = self.array_ring_count_circle
            array["Input_19"] = self.array_use_constant_distance
            array["Input_20"] = self.array_constant_distance
            array["Input_4"] = self.array_radius
            array["Input_8"] = self.array_rings_offset
            array["Input_9"] = self.array_rings_offset_z

            array["Input_14"][0] = self.array_rotation[0]
            array["Input_14"][1] = self.array_rotation[1]
            array["Input_14"][2] = self.array_rotation[2]
            array["Input_10"] = self.array_align
            
            array["Input_17"][0] = self.array_randpos[0]
            array["Input_17"][1] = self.array_randpos[1]
            array["Input_17"][2] = self.array_randpos[2]
            array["Input_15"][0] = self.array_randrot[0]
            array["Input_15"][1] = self.array_randrot[1]
            array["Input_15"][2] = self.array_randrot[2]
            array["Input_16"] = self.array_randscale
            array["Input_18"] = self.seed
        
        # CURVE TYPE ARRAY
        else:
            nodegroup = "BagaPie_Array_Curve"
            Add_NodeGroup(self,context,array, nodegroup)

            # SET VALUES
            array["Input_2"] = array_curve
            array["Input_5"] = self.array_curve_length
            array["Input_4"] = self.array_use_count
            array["Input_6"] = self.array_count

            array["Input_3"][0] = self.array_rotation[0]
            array["Input_3"][1] = self.array_rotation[1]
            array["Input_3"][2] = self.array_rotation[2]
            array["Input_10"] = self.array_align_float
            array["Input_11"][0] = self.array_vector_to_be_aligned[0]
            array["Input_11"][1] = self.array_vector_to_be_aligned[1]
            array["Input_11"][2] = self.array_vector_to_be_aligned[2]

            
            array["Input_7"][0] = self.array_randpos[0]
            array["Input_7"][1] = self.array_randpos[1]
            array["Input_7"][2] = self.array_randpos[2]
            array["Input_8"][0] = self.array_randrot[0]
            array["Input_8"][1] = self.array_randrot[1]
            array["Input_8"][2] = self.array_randrot[2]
            array["Input_9"] = self.array_randscale
            array["Input_12"] = self.seed
            array["Input_10"] = 0

        # CUSTOM PROPERTY
        array_variables = ["ARRAY",  
                            array_target.name,
                            self.array_type,
                            array.name,
                            ]
        context.scene.bagapieValue = ""
        for var in array_variables:
            context.scene.bagapieValue = context.scene.bagapieValue + var + " "

        # DISPLAY IN MODIFIER LIST
        val = {
            'name': 'array',
            'modifiers':[
                            array.name,
                            self.array_type, # The array type is present as a modifier (in UI to display line, grid or circle)
                        ]
            }

        if len(array_target.bagapieList) > 0:
            array_target.bagapieIndex = array_target.bagapieIndex+1

        item = array_target.bagapieList.add()
        item.val = json.dumps(val)

        array_target.select_set(True)
        bpy.context.view_layer.objects.active = array_target
    
        return {'FINISHED'}

class BAGAPIE_OT_drawarray(Operator):
    """Draw Array with the selected mesh"""
    bl_idname = "bagapie.drawarray"
    bl_label = "Draw Array"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = bpy.context.object

        return (
            o is not None and 
            o.type in ['MESH','CURVE']
        )

    def execute(self, context):

        # FIRST STEP
        array_targets = bpy.context.selected_objects # Get active object

        curve = bpy.data.curves.new('Draw_Curve_Array', 'CURVE')
        curve_obj = bpy.data.objects.new(curve.name, curve)
        curve_obj.data.dimensions = '3D'

        # CREATE MODIFIER
        new = curve_obj.modifiers.new
        array = new(name="BagaArray_Draw_Assets", type='NODES')

        nodegroup = "BagaPie_Array_Draw_Curve"
        Add_NodeGroup(self,context,array, nodegroup)

        main_coll = get_or_create_collection("BagaPie")
        array_coll = get_or_create_collection("BagaPie_Draw_Curve_Array", main_coll)
        asset_coll = bpy.data.collections.new("BagaPie_Draw_Curve_Array_Assets")
        main_coll.children.link(asset_coll)

        # array_coll, asset_coll = Collection_Instancer(self,context)
        array_coll.objects.link(curve_obj)

        for ob in array_targets:
            asset_coll.objects.link(ob)


        obj_dimm = OBJ_Dimension(self,context,array_targets)
        # SET VALUES
        array["Input_2"] = asset_coll
        array["Input_5"] = obj_dimm
        array["Input_7"][1] = obj_dimm/2
        array["Input_8"][2] = 10

        bpy.context.view_layer.objects.active = curve_obj
        bpy.ops.object.editmode_toggle()
        bpy.context.scene.tool_settings.curve_paint_settings.depth_mode = 'SURFACE'
        # bpy.context.area.type = 'VIEW_3D'#############################################################
        bpy.ops.wm.tool_set_by_id(name="builtin.draw")

        # CUSTOM PROPERTY
        array_variables = ["ARRAY",  
                            asset_coll.name,
                            'CURVE',
                            array.name,
                            ]
        context.scene.bagapieValue = ""
        for var in array_variables:
            context.scene.bagapieValue = context.scene.bagapieValue + var + " "

        # DISPLAY IN MODIFIER LIST
        val = {
            'name': 'array',
            'modifiers':[
                            array.name,
                            'CURVE_DRAW',
                        ]
            }

        item = curve_obj.bagapieList.add()
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
  
###################################################################################
# GET OBJECTS DIMMENSIONS
###################################################################################
def OBJ_Dimension(self,context,obj):
    instances_max_dimensions_total = 0
    for ob in obj:
        instances_max_dimensions = 0
        if ob.dimensions.x > instances_max_dimensions:
            instances_max_dimensions = ob.dimensions.x
            if ob.dimensions.x < ob.dimensions.y:
                instances_max_dimensions = ob.dimensions.y
        if ob.name.startswith("BagaPie_Grass"):
            inc_dim = 0.5
        else:
            inc_dim = 1
        instances_max_dimensions_total += instances_max_dimensions

    dimmension = (instances_max_dimensions_total/len(obj))*inc_dim
    
    return dimmension

classes = [
    BAGAPIE_OT_array_remove,
    BAGAPIE_OT_array,
    BAGAPIE_OT_drawarray
]