import bpy
import json
from bpy.types import Operator
from .utils import Import_Nodes, get_or_create_collection


def exception_tool_door(self, context, mo_name="NONE", wall_thickness=0.2, boolean_mode=True):
    # There are 3 objects to distinguish:
    #   - Wall: the mesh on which the user selects the faces to transform into door
    #   - Door: the faces extracted from the wall that serve as a base for the door modifier
    #   - Door Bool: an object duplicated and linked to Door that will serve as a boolean on the wall (solidify modifier)

    ops = bpy.ops
    ops.object.editmode_toggle()

    # Get a list of selected walls
    objs_wall = context.selected_objects.copy()

    # Create a dictionary to map walls to their corresponding door_bool
    wall_to_door_bool = {}

    # Deselect all objects to start fresh
    bpy.ops.object.select_all(action='DESELECT')

    # Process each wall individually
    for wall in objs_wall:
        # Select and activate the current wall
        wall.select_set(True)
        context.view_layer.objects.active = wall

        # Create Door object by duplicating the wall
        ops.object.duplicate(linked=False)
        door = context.active_object

        # Only keep the faces that will be used for the doors
        ops.object.editmode_toggle()
        initial_select_mode = bpy.context.tool_settings.mesh_select_mode[:]
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        ops.mesh.select_all(action='INVERT')
        ops.mesh.delete(type='FACE')
        bpy.context.tool_settings.mesh_select_mode = initial_select_mode
        ops.object.editmode_toggle()

        # Duplicate the door to get the Door Bool
        door.select_set(True)
        ops.object.duplicate(linked=True)
        door_bool = context.active_object 

        # Parent Door Bool to Door
        door_bool.parent = door
        door_bool.matrix_parent_inverse = door.matrix_world.inverted()

        # Store the mapping from wall to door_bool
        wall_to_door_bool[wall] = door_bool

        # Deselect all for the next iteration
        bpy.ops.object.select_all(action='DESELECT')

    # Setup collection
    main_coll = get_or_create_collection("BagaPie")
    coll = get_or_create_collection("BagaPie_Door", main_coll)

    #######################################################################################
    # DOORS AND DOORS BOOLEAN SETUP
    #######################################################################################

    # Import Door node tree
    nodegroup_door = mo_name.replace(" ", "_")
    if nodegroup_door not in bpy.data.node_groups:
        Import_Nodes(self, context, nodegroup_door, blend_file="BagaPie_Nodes_Tools.blend")

    for wall, door_bool in wall_to_door_bool.items():
        door = door_bool.parent

        # DOORS SETUP
        door.name = "BagaPie_Door"
        door.data.name = "BagaPie_Door"
        for d_coll in door.users_collection:
            d_coll.objects.unlink(door)
        coll.objects.link(door)

        modifier = door.modifiers.new(name=nodegroup_door, type='NODES')
        modifier.node_group = bpy.data.node_groups[nodegroup_door]

        # DOORS BOOLEAN SETUP
        door_bool.name = "BagaPie_Door_Bool"
        for obj_coll in door_bool.users_collection:
            obj_coll.objects.unlink(door_bool)
        coll.objects.link(door_bool)

        solidify_modifier = door_bool.modifiers.new(name="Solidify", type='SOLIDIFY')
        solidify_modifier.thickness = wall_thickness
        solidify_modifier.offset = -0.99

        door_bool.display_type = 'WIRE'
        door_bool.hide_render = True
        door_bool.hide_render = True
        door_bool.visible_shadow = False
        door_bool.visible_volume_scatter = False
        door_bool.visible_transmission = False
        door_bool.visible_glossy = False
        door_bool.visible_diffuse = False
        door_bool.visible_camera = False
        door_bool.data.materials.clear()

        # Add custom property to door
        val = {
            'name': 'door',  # MODIFIER TYPE
            'modifiers': [
                nodegroup_door,  # Modifier Name
            ]
        }
        item = door.bagapieList.add()
        item.val = json.dumps(val)

    #######################################################################################
    # WALL BOOLEAN
    #######################################################################################

    for wall, door_bool in wall_to_door_bool.items():
        # Ensure the wall is selected and active
        bpy.ops.object.select_all(action='DESELECT')
        wall.select_set(True)
        context.view_layer.objects.active = wall

        # Add boolean modifier
        boolean_modifier = wall.modifiers.new(name="Boolean", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = door_bool
        if boolean_mode:
            boolean_modifier.solver = 'EXACT'
        else:
            boolean_modifier.solver = 'FAST'

    #######################################################################################
    # GO TO EDIT MODE ON DOORS
    #######################################################################################

    # Select all door objects
    bpy.ops.object.select_all(action='DESELECT')
    for wall, door_bool in wall_to_door_bool.items():
        door = door_bool.parent
        door.select_set(True)
    # Set one of the doors as active
    context.view_layer.objects.active = next(iter(wall_to_door_bool.values())).parent
    ops.object.editmode_toggle()


class BAGAPIE_OT_door_remove(Operator):
    """ Remove Bagapie Door modifiers """
    bl_idname = "bagapie.door_remove"
    bl_label = 'Remove Bagapie Door'

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
            print("Some elements (modifier or objects) were missing.")
        
        context.object.bagapieList.remove(self.index)
        return {'FINISHED'}

classes = [
    BAGAPIE_OT_door_remove,
]