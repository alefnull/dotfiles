import bpy
import bmesh
from .utils import get_addon_prefs, invert_rotation_in_node_groupe, show_hide_gizmos_in_node_group
from.mesh_utils import calculate_scale, AddModCylinder
from .addon_preferences import CONST_ITEMS
from bpy_extras import object_utils
from bpy.app.handlers import persistent

node_group_versions = {}

def set_scale(self, context, mod):
    prefs = get_addon_prefs()
    # scale object
    scale = calculate_scale(context, self.scale, self.auto_scale, self.scale_auto_scale, custom_scale_factor=1.0)
    # set scale to geometry node modifier based on socket name
    double_scale = []
    full_scale = ["Depth", "Size", "Size X", "Size Y","Height"]
    half_scale = ["Radius", "Radius Bottom", "Start Radius", "End Radius"]
    one_fourth_scale = ["Minor Radius"]
    one_eight_scale = ["Ring Radius", "Offset Scale"]
    if self.type == 'Torus':
        full_scale = ["Major Radius"]
        scale = scale / 2.4
    if self.type == 'Quad Sphere':
        full_scale = []
        half_scale = ["Size"]
    if self.type == 'Capsule' or self.type == 'Quad Capsule':
        double_scale = ["Height"]
        half_scale = []
        one_fourth_scale = ["Radius"]

    node_group = mod.node_group
    input_node = next((node for node in node_group.nodes if node.type == 'GROUP_INPUT'),None)

    for node_output in input_node.outputs[:-1]:
        if not node_output.type == 'GEOMETRY':
            socket_id = node_output.identifier
            socket_type = node_output.type

            if socket_type == 'VECTOR':
                scale = scale, scale, scale

            if node_output.name in double_scale:
                mod[socket_id] = scale * 2
            if node_output.name in full_scale:
                mod[socket_id] = scale
            elif node_output.name in half_scale:
                mod[socket_id] = scale / 2
            elif node_output.name in one_fourth_scale:
                mod[socket_id] = scale / 4
            elif node_output.name in one_eight_scale:
                mod[socket_id] = scale / 8

    show_hide_gizmos_in_node_group(node_group, prefs.show_gizmo)
    invert_rotation_in_node_groupe(node_group, prefs.invert_rotation_gizmo_direction)

def new_mesh_with_single_vert(name):
    new_mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bm.from_mesh(new_mesh)
    bm.verts.new((0,0,0)) # add single vert so we get a material index
    bm.to_mesh(new_mesh)
    bm.free()
    return new_mesh

def load_prim_type_and_versioning(file_path, name):
    global node_group_versions
    all_node_groups = bpy.data.node_groups
    data = None
    latest_version = None
    
    if not name in all_node_groups or not name in node_group_versions:
        with bpy.data.libraries.load(file_path, link=False) as (data_from, data_to):
            data = data_to.node_groups = [node_group for node_group in data_from.node_groups if name in node_group]
    # get latest known currently available version of node group
    latest_known_up_to_data_version = name
    for node_group in all_node_groups:
        if node_group.name.startswith(name + "_v"):
            latest_known_up_to_data_version = node_group.name

    if name in bpy.data.node_groups and not name in node_group_versions:
        if data:
            node_group_name = data[0].name
            node_group = bpy.data.node_groups[node_group_name]
        
            if name not in node_group_versions:
                node_group_versions[name] = node_group.description
            latest_version = node_group_versions.get(name, None)
            
        # if name in all_node_groups, but it has a lower version number, update it
        if name in all_node_groups:
            # get current version of node group
            if latest_version:
                current_version = bpy.data.node_groups[name].description
                if current_version == "":
                    current_version = "0"

                if float(current_version) < float(latest_version) and not name in node_group_versions:
                    print(f"Getting {name} latest primitive version node group {latest_version}")
                    # update node group
                    new_name = f"{name}_v{latest_version}"
                    # rename the newly appended node group
                    data[0].name = new_name
                    node_group_versions[name] = latest_version
                    latest_known_up_to_data_version = new_name
                else:
                    if name + ".001" in all_node_groups:
                        # remove the appended node group
                        bpy.data.node_groups.remove(bpy.data.node_groups[name + ".001"])
                        
    # Remap and clean up node groups with suffixes
    node_groups_to_remap = ["Set Material to Index 0", "Fix Pivot"]
    node_groups_to_check = {
        "Set Material to Index 0": "Set Material to Index 0",
        "Fix Pivot": "Fix Pivot"
    }

    for key, value in node_groups_to_check.items():
        for node_group in all_node_groups:
            if node_group.name.startswith(value + "_v"):
                # add to the dict
                node_groups_to_remap.append(node_group.name)

    for node_group_name in node_groups_to_remap:
        suffix = 1
        while True:
            full_name = f"{node_group_name}.{suffix:03d}"
            if full_name in bpy.data.node_groups:
                #get the orgianl none .001 description to get the current version
                current_version = bpy.data.node_groups[node_group_name].description
                
                # get the newly import .001+ node group description to get the latest version
                latest_version = bpy.data.node_groups[full_name].description

                node_group = bpy.data.node_groups[full_name]
                if current_version == "":
                    current_version = "0"

                if float(current_version) < float(latest_version) and not node_group.name in node_group_versions:
                    new_name = f"{node_group_name}_v{latest_version}"
                    node_group.name = new_name
                    node_group_versions[node_group_name] = node_groups_to_check[node_group_name]
                    
                else:
                    node_group.user_remap(bpy.data.node_groups[node_group_name])
                    bpy.data.node_groups.remove(node_group)
                suffix += 1
            else:
                break

    return latest_known_up_to_data_version

primitive_properties = {}

def primitive_properties_get(self, context, mod):
    primitive_properties.clear()
    if self.type in bpy.data.node_groups:
        node_group = bpy.data.node_groups[self.type]
        input_node = next((node for node in node_group.nodes if node.type == 'GROUP_INPUT'), None)
        if input_node:
            md = context.object.modifiers.get(self.type)

            for input_socket in input_node.outputs:
                if input_socket.type != 'GEOMETRY' and not input_socket.identifier == '__extend__':
                    primitive_properties[input_socket.name] = (input_socket.identifier, input_socket.type)

first_time_run_from_prefrences = True

def primitive_properties_set(self, context, mod):
    global first_time_run_from_prefrences
    prefs = get_addon_prefs()

    for prop in primitive_properties:
        if prop == "Origin at Bottom":
            if first_time_run_from_prefrences:
                self.origin_at_bottom = prefs.origin_at_bottom
                first_time_run_from_prefrences = False
            mod[primitive_properties[prop][0]] = self.origin_at_bottom
        if prop == "Adaptive Resolution":
            mod[primitive_properties[prop][0]] = self.adaptive_resolution
        if prop == "Origin at Corner":
            mod[primitive_properties[prop][0]] = self.origin_at_corner
        
            
class Add_ND_Primitive(bpy.types.Operator, object_utils.AddObjectHelper):
    bl_idname = "mesh.add_nd_primitive"
    bl_label = "Add ND Primitive"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Adds a non-destructive primitive"

    type: bpy.props.StringProperty() # type: ignore
    auto_scale: bpy.props.BoolProperty(name="Auto Scale", default=True) # type: ignore
    scale: bpy.props.FloatProperty(name="Scale", default=1.0, min=0.1, max=10.0, unit='LENGTH') # type: ignore
    scale_auto_scale: bpy.props.FloatProperty(name="Relative Scale", default=6.0, min=0.1, max=16.0) # type: ignore
    origin_at_bottom: bpy.props.BoolProperty(name="Origin at Bottom", default=False) # type: ignore
    origin_at_corner: bpy.props.BoolProperty(name="Origin at Corner", default=False) # type: ignore
    adaptive_resolution: bpy.props.BoolProperty(name="Adaptive Resolution", default=False) # type: ignore
    
    
    def invoke(self, context, event):
        prefs = get_addon_prefs()
        if prefs.auto_swith_to_modifier_tab: # register timer to switch to modifier context¨
            bpy.app.timers.register(switch_to_modifier_context, first_interval=0.025) # workaround to switch to modifier context, otherwise error if it does not exist already
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        col = layout.column(align=True)
        sub = col.column()

        icon = next((item[1] for item in CONST_ITEMS if item[0] == self.type), 'FILE_3D')

        sub.label(text=self.type, icon=icon)
        sub.prop(self, "auto_scale")
        if not self.auto_scale:
            sub.prop(self, "scale")
        else:
            sub.prop(self, "scale_auto_scale")
        
        col = layout.column(align=True)
        col.prop(self, 'align')
        col = layout.column(align=True)
        col.prop(self, 'location', expand=True)
        col = layout.column(align=True)
        col.prop(self, 'rotation', expand=True)

        col = layout.column(align=True)
        col.label(text="Primitive Properties")

        # Get geometry node inputs
        if "Adaptive Resolution" in primitive_properties:
            col.prop(self, "adaptive_resolution")
        if "Origin at Bottom" in primitive_properties:
            col.prop(self, "origin_at_bottom")
        if "Origin at Corner" in primitive_properties:
            col.prop(self, "origin_at_corner")

    def execute(self, context):
        global node_group_versions

        name = self.type

        bpy.ops.object.select_all(action='DESELECT') # do we whant it to deselect?

        if self.type == 'Mod Cylinder':
            new_mesh = AddModCylinder(context, 16,  self.auto_scale, 6.0, self.scale)   
            # new_obj = object_utils.object_data_add(context, new_mesh, operator=self)
            return {'FINISHED'}

        node_gruope = load_prim_type_and_versioning(__file__.replace('add_nd_primitive.py', 'Primitives.blend'), name)
        
        new_mesh = new_mesh_with_single_vert(name)
        new_obj = object_utils.object_data_add(context, new_mesh, operator=self)

        # add geometry node modifier to object
        mod = new_obj.modifiers.new(name=name, type='NODES')
        mod.node_group = bpy.data.node_groups[node_gruope]

        new_obj['non_destructive_primitive'] = name # add object properties

        set_scale(self, context, mod)
        primitive_properties_get(self, context, mod)
        primitive_properties_set(self, context, mod)

        return {'FINISHED'}
    
    def register():
        bpy.app.handlers.load_post.append(reset_node_group_versions)

    def unregister():
        if reset_node_group_versions in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(reset_node_group_versions)

def switch_to_modifier_context():
    for area in bpy.context.screen.areas:
        if area.type == 'PROPERTIES':
            if area.spaces[0].context != 'MODIFIER':
                area.spaces[0].context = 'MODIFIER'

@persistent
def reset_node_group_versions(dummy):
    global node_group_versions
    node_group_versions = {}