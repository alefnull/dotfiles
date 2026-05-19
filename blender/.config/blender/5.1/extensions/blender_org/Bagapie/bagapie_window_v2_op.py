import bpy
import json
import math
import bmesh
from mathutils import Vector
from bpy.types import Operator
from .utils import Import_Nodes, get_or_create_collection

def face_is_valid(face, tolerence_angle_deg=5):
    # check if face is quad
    if len(face.verts) != 4:
        return False
    tolerence_angle = math.radians(tolerence_angle_deg)
    vertical_edges = []

    # check each edge verticality
    for edge in face.edges:
        v1 = edge.verts[0].co
        v2 = edge.verts[1].co
        edge_vec = v2 - v1

        # avoid 0 division if edge length is 0
        if edge_vec.length == 0:
            continue

        # Check verticality
        edge_dir = edge_vec.normalized()
        if abs(edge_dir.dot(Vector((0, 0, 1)))) >= math.cos(tolerence_angle):
            vertical_edges.append(edge)

    # check if 2 vertical edges
    if len(vertical_edges) != 2:
        return False

    # check they do not share a vertice
    if set(vertical_edges[0].verts) & set(vertical_edges[1].verts):
        return False

    return True

def exception_tool_window(self, context, mo_name="NONE", wall_thickness=0.2, boolean_mode=True):
    # There are 3 objects to distinguish:
    #   - Wall: the mesh on which the user selects the faces to transform into window
    #   - Window: the faces extracted from the wall that serve as a base for the window modifier
    #   - Window Bool: an object duplicated and linked to Window that will serve as a boolean on the wall (solidify modifier)

    ops = bpy.ops
    ops.object.editmode_toggle()
    objs_wall = context.selected_objects.copy()

    # Create a dictionary to map walls to their corresponding window_bool
    wall_to_window_bool = {}
    bpy.ops.object.select_all(action='DESELECT')

    # For each wall, duplicate it to create the window, then duplicate the window to create window_bool
    for wall in objs_wall:
        wall.select_set(True)
        context.view_layer.objects.active = wall

        ops.object.duplicate(linked=False)
        window = context.active_object  # The duplicated object becomes the active object
        bpy.ops.object.shade_flat()

        # Only keep the faces that will be used for the windows
        ops.object.editmode_toggle()
        initial_select_mode = bpy.context.tool_settings.mesh_select_mode[:]
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

        # Check if shutters must be used
        me = window.data
        bm = bmesh.from_edit_mesh(me)
        faces = [face for face in bm.faces if face.select]
        use_shutters = True
        for face in faces:
            if not face_is_valid(face):
                use_shutters = False

        ops.mesh.select_all(action='INVERT')
        ops.mesh.delete(type='FACE')
        bpy.context.tool_settings.mesh_select_mode = initial_select_mode
        ops.object.editmode_toggle()

        # Duplicate the window to get the Window Bool
        window.select_set(True)
        ops.object.duplicate(linked=True)
        window_bool = context.active_object  # The duplicated object becomes the active object

        window_bool.parent = window
        window_bool.matrix_parent_inverse = window.matrix_world.inverted()

        wall_to_window_bool[wall] = window_bool
        bpy.ops.object.select_all(action='DESELECT')

    # Setup collection
    main_coll = get_or_create_collection("BagaPie")
    coll = get_or_create_collection("BagaPie_Window", main_coll)

    #######################################################################################
    # WINDOWS AND WINDOWS BOOLEAN SETUP
    #######################################################################################

    # Import Window node tree
    nodegroup_win = mo_name.replace(" ", "_")
    if nodegroup_win not in bpy.data.node_groups:
        Import_Nodes(self, context, nodegroup_win, blend_file="BagaPie_Nodes_Tools.blend")

    for wall, window_bool in wall_to_window_bool.items():
        window = window_bool.parent

        # WINDOWS SETUP
        window.name = "BagaPie_Window"
        window.data.name = "BagaPie_Window"
        for w_coll in window.users_collection:
            w_coll.objects.unlink(window)
        coll.objects.link(window)

        modifier = window.modifiers.new(name=nodegroup_win, type='NODES')
        modifier.node_group = bpy.data.node_groups[nodegroup_win]
        modifier["Socket_14"] = use_shutters

        # WINDOWS BOOLEAN SETUP
        window_bool.name = "BagaPie_Window_Bool"
        for obj_coll in window_bool.users_collection:
            obj_coll.objects.unlink(window_bool)
        coll.objects.link(window_bool)

        solidify_modifier = window_bool.modifiers.new(name="Solidify", type='SOLIDIFY')
        solidify_modifier.thickness = wall_thickness
        solidify_modifier.offset = -0.99

        window_bool.display_type = 'WIRE'
        window_bool.hide_render = True
        window_bool.visible_shadow = False
        window_bool.visible_volume_scatter = False
        window_bool.visible_transmission = False
        window_bool.visible_glossy = False
        window_bool.visible_diffuse = False
        window_bool.visible_camera = False
        window_bool.data.materials.clear()

        # Add custom property to window
        val = {
            'name': 'window_v2',  # MODIFIER TYPE
            'modifiers': [
                nodegroup_win,  # Modifier Name
            ]
        }
        item = window.bagapieList.add()
        item.val = json.dumps(val)

    #######################################################################################
    # WALL BOOLEAN
    #######################################################################################

    for wall, window_bool in wall_to_window_bool.items():
        # Ensure the wall is selected and active
        bpy.ops.object.select_all(action='DESELECT')
        wall.select_set(True)
        context.view_layer.objects.active = wall

        # Add boolean modifier
        boolean_modifier = wall.modifiers.new(name="Boolean", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = window_bool
        if boolean_mode:
            boolean_modifier.solver = 'EXACT'
        else:
            boolean_modifier.solver = 'FAST'

    #######################################################################################
    # GO TO EDIT MODE ON WINDOWS
    #######################################################################################

    # Select all window objects
    bpy.ops.object.select_all(action='DESELECT')
    for wall, window_bool in wall_to_window_bool.items():
        window = window_bool.parent
        window.select_set(True)
    context.view_layer.objects.active = list(wall_to_window_bool.values())[0].parent
    ops.object.editmode_toggle()

class BAGAPIE_OT_window_v2_remove(Operator):
    """ Remove Bagapie Window V2 modifiers """
    bl_idname = "bagapie.window_v2_remove"
    bl_label = 'Remove Bagapie Window'

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
            for mod in modifiers:
                obj.modifiers.remove(obj.modifiers[mod])
        except:
            print("Some elements (modifier or objects) were missing.")
        
        context.object.bagapieList.remove(self.index)
        return {'FINISHED'}

classes = [
    BAGAPIE_OT_window_v2_remove,
]