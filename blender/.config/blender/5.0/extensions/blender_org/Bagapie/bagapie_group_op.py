import bpy
import mathutils
import time
import bpy_extras.view3d_utils
import bpy_extras.view3d_utils as v3d_utils
import re
from bpy.types import Operator, Panel
from .utils import get_or_create_collection, is_in_local_view, Warning, is_in_local_view, Get_addon_pref, debug


class BAGAPIE_PT_group_panel(Panel):
    bl_label = "Bagapie Group Panel"
    bl_idname = "BAGAPIE_PT_group_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        obj=context.object
        if obj:
            if is_a_box(obj):
                layout.operator("bagapie.instance", text="Group To Instance", icon="LINKED")
                layout.operator("bagapie.ungroup", text="Ungroup", icon="MOD_EXPLODE")

                if obj and "bagapie_locker" in obj:                    
                    row = layout.row(align=True)
                    split = row.split(factor=0.85, align=True)
                    if obj["bagapie_locker"] == True:
                        split.operator("bagapie.editgroup", text="Make Selectable", icon ="RESTRICT_SELECT_OFF")
                        split.operator("bagapie.editgroup", text="All").all = True
                    else:
                        split.operator("bagapie.lockgroup", text="Make Unlectable",icon="RESTRICT_SELECT_ON")
                        split.operator("bagapie.lockgroup", text="All").all = True

                if is_in_local_view()==True:
                    layout.operator("bagapie.isolategroup", text="Unisolate", icon="ZOOM_PREVIOUS")
                else:
                    layout.operator("bagapie.isolategroup", text="Isolate", icon="ZOOM_PREVIOUS")

            if check_if_instance(obj) and obj.type == 'EMPTY':
                if is_in_local_view()==True:
                    layout.operator("bagapie.editinstancegroup", text= "Exit Editing", icon="GREASEPENCIL")
                else:
                    layout.operator("bagapie.editinstancegroup", text= "Edit Instance Group", icon="GREASEPENCIL")

            if check_parent_group(obj):
                layout.operator("bagapie.move_group_modal", text= "Move Instance Group", icon="EMPTY_ARROWS").is_parent = True


class BAGAPIE_OT_group(Operator):
    """Group selected objects. A bounding box is created and the objects are no longer selectable. Use Edit to make them selectable."""
    bl_idname = 'bagapie.group'
    bl_label = 'BagaPieGroup'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.selected_objects
        return (
            len(o)>=1 and is_in_local_view()==False
        )
    
    def invoke(self, context, event):
        if len(context.selected_objects)==1 :
            if is_a_box(context.object) or check_if_instance(context.object):
                bpy.ops.wm.call_panel(name="BAGAPIE_PT_group_panel")
                return {'CANCELLED'}
        return self.execute(context)

    def execute(self, context):
        
        # COLLECTION BagaPie_Manage
        main_coll = get_or_create_collection("BagaPie")
        manage_coll = get_or_create_collection("BagaPie_Manage", main_coll)
        group_coll = get_or_create_collection("BagaPie_Group", manage_coll)

        group_child_coll = bpy.data.collections.new("BagaPie_Group_Child")
        group_coll.children.link(group_child_coll)

        group_child_coll["bagapie"] = "BagaPie_Group_Child"

        objs = bpy.context.selected_objects

        # CREATE BOX
        mesh = bpy.data.meshes.new("Cube")
        target = bpy.data.objects.new("Cube", mesh)
        group_coll.objects.link(target)
        bpy.context.view_layer.objects.active = target
        target.select_set(True)

        target.location=(0, 0, 0)
        target.name = "BagaPie_Group_BoundBox"
        target.display_type = 'SOLID'
        target.visible_camera = False
        target.visible_diffuse = False
        target.visible_glossy = False
        target.visible_transmission = False
        target.visible_volume_scatter = False
        target.visible_shadow = False
        target.hide_render = True

        target["bagapie"] = str("bound_box")
        target["bagapie_locker"] = True
        target["bagapie_locker_initial"] = True

        for o in objs:
            group_child_coll.objects.link(o)

        modifier = target.modifiers.new(name="BagaPie_Group_Bounding_Box", type='NODES')

        # CREATE NODE TREE
        if "BagaPie_Group_Bounding_Box" in bpy.data.node_groups: # check if N_tree already exist
            tree = bpy.data.node_groups["BagaPie_Group_Bounding_Box"]
        else:
            tree = bpy.data.node_groups.new(name="BagaPie_Group_Bounding_Box", type='GeometryNodeTree')
            
            nodes = tree.nodes
            node_input = None
            node_output = None

            # Setup INPUT & OUTPUT
            node_input = nodes.new(type='NodeGroupInput')
            node_input.location = (-600, 0)
            node_output = nodes.new(type='NodeGroupOutput')
            node_output.location = (1400, 0)

            if not any(item.in_out == 'INPUT' for item in tree.interface.items_tree):
                tree.interface.new_socket(socket_type="NodeSocketCollection", name='Geometry', in_out='INPUT')
            if not any(item.in_out == 'OUTPUT' for item in tree.interface.items_tree):
                tree.interface.new_socket(socket_type="NodeSocketGeometry", name='Geometry', in_out='OUTPUT')
                
            # ALL NODES
            node_collection_info = nodes.new(type='GeometryNodeCollectionInfo')
            node_collection_info.location = (-400, 0)
            node_collection_info.transform_space = 'RELATIVE'

            node_bbox1 = nodes.new(type='GeometryNodeBoundBox')
            node_bbox1.location = (-200, 0)

            node_realize = nodes.new(type='GeometryNodeRealizeInstances')
            node_realize.location = (0, 0)
            node_realize.inputs[1].default_value = True

            node_bbox2 = nodes.new(type='GeometryNodeBoundBox')
            node_bbox2.location = (200, 0)

            node_subdiv = nodes.new(type='GeometryNodeSubdivideMesh')
            node_subdiv.location = (1000, 0)
            node_subdiv.inputs[1].default_value = 3

            node_neight = nodes.new(type='GeometryNodeInputMeshVertexNeighbors')
            node_neight.location = (400, -200)

            node_comp = nodes.new(type='FunctionNodeCompare')
            node_comp.location = (600, -200)
            node_comp.data_type = 'INT'
            node_comp.operation = 'EQUAL'
            node_comp.inputs[3].default_value = 3

            node_blur = nodes.new(type='GeometryNodeBlurAttribute')
            node_blur.location = (800, -200)

            node_math = nodes.new(type='ShaderNodeMath')
            node_math.location = (1000, -200)
            node_math.operation = 'LESS_THAN'
            node_math.inputs[1].default_value = 0.1

            node_delete = nodes.new(type='GeometryNodeDeleteGeometry')
            node_delete.location = (1200, 0)
            node_delete.domain = 'POINT'
            node_delete.mode = 'ALL'

            # LINKS
            links = tree.links
            links.new(node_input.outputs[0], node_collection_info.inputs[0])
            links.new(node_collection_info.outputs[0], node_bbox1.inputs[0])
            links.new(node_bbox1.outputs[0], node_realize.inputs[0])
            links.new(node_realize.outputs[0], node_bbox2.inputs[0])
            links.new(node_bbox2.outputs[0], node_subdiv.inputs[0])
            links.new(node_subdiv.outputs[0], node_delete.inputs[0])
            links.new(node_delete.outputs[0], node_output.inputs[0])
            
            links.new(node_neight.outputs[0], node_comp.inputs[2])
            links.new(node_comp.outputs[0], node_blur.inputs[0])
            links.new(node_blur.outputs[0], node_math.inputs[0])
            links.new(node_math.outputs[0], node_delete.inputs[1])

        modifier.node_group = tree
        modifier["Socket_0"] = group_child_coll

        bpy.context.view_layer.objects.active = target

        # SET ORIGIN
        all_bbox_corners = []
        for o in objs:
            bbox_corners = [o.matrix_world @ mathutils.Vector(corner) for corner in o.bound_box]
            all_bbox_corners.extend(bbox_corners)

        min_z = min(v.z for v in all_bbox_corners)
        center_x = sum(v.x for v in all_bbox_corners) / len(all_bbox_corners)
        center_y = sum(v.y for v in all_bbox_corners) / len(all_bbox_corners)

        bottom_center = mathutils.Vector((center_x, center_y, min_z))
        target.location = bottom_center

        # PARENT & LOCK OBJECTS
        for obj in objs:
            if is_a_box(obj.parent):
                for mo in obj.parent.modifiers:
                    if mo.node_group.name.startswith('BagaPie_Group_Bounding_Box'):
                        coll = mo['Socket_0'] # COLL PARENT
                        
                target.parent = obj.parent
                target.location = target.location - obj.parent.location
                coll.objects.link(target)
                break

        for obj in objs:
            if obj.parent is None or is_a_box(obj.parent):
                if is_a_box(obj.parent):
                    obj.location = obj.location - bottom_center + obj.parent.location
                    obj.parent = target
                else:
                    obj.parent = target
                    obj.location = obj.location - bottom_center
            obj.hide_select = True

        bpy.ops.bagapie.double_click_edit("INVOKE_DEFAULT")
        
        return {'FINISHED'}


class BAGAPIE_OT_ungroup(Operator):
    """ Ungroup the selected group """
    bl_idname = "bagapie.ungroup"
    bl_label = 'Ungroup'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )

    def execute(self, context):
        target = bpy.context.active_object
        
        if target and target.get("bagapie") == "bound_box":
            coll = group_coll(target)
            is_instance = False
            dady = target.parent
            coll_dady = None
            dady_is_box = is_a_box(dady)

            # GET COLLECTION        
            main_coll = get_or_create_collection("BagaPie")
            manage_coll = get_or_create_collection("BagaPie_Manage", main_coll)
            instances_coll = get_or_create_collection("BagaPie_Instances", manage_coll)

            # CHECK IF IS INSTANCE
            for instance in instances_coll.objects:
                if instance.type == 'EMPTY':
                    coll_instantiated = instance.instance_collection
                    if coll == coll_instantiated:
                        is_instance = True
                        break

            # CHECK IF BOX IS BOX CHILD
            if dady_is_box:
                coll_dady = group_coll(dady)

            # OBJS MANAGMENT
            for o in coll.objects:
                matrixcopy = o.matrix_world.copy()

                # COLLECTION
                if is_instance == False:
                    coll.objects.unlink(o)
                if coll_dady and o.name not in coll_dady.objects: # if dady's box is box add to his coll
                    coll_dady.objects.link(o)
                elif len(o.users_collection) == 0: # To avoid the obj disapear from the scene
                    bpy.context.scene.collection.objects.link(o)

                # SELECTABILITY
                if dady_is_box:
                    o.hide_select = dady["bagapie_locker"]
                else:
                    o.hide_select = False

                # PARENT
                if o.parent == target:
                    if dady_is_box:
                        o.parent = dady
                    else:
                        o.parent = None

                o.matrix_world = matrixcopy
            
            # REMOVE COLL
            if is_instance == False:
                bpy.data.collections.remove(coll)

            # REMOVE BOUNDING BOX
            bpy.data.objects.remove(target)
        return {'FINISHED'}


class BAGAPIE_OT_editinstancegroup(Operator):
    """Edit selected group"""
    bl_idname = 'bagapie.editinstancegroup'
    bl_label = 'Edit Group'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj.type == 'EMPTY' and any(coll.name == "BagaPie_Instances" for coll in obj.users_collection))

    def execute (self, context):

        group = bpy.context.active_object
        coll_instance = group.instance_collection
        objs = coll_instance.objects

        bpy.ops.object.select_all(action='DESELECT')

        for o in objs:
            o.hide_select = False
            o.select_set(True)

        bpy.ops.view3d.localview()

        return {'FINISHED'}


class BAGAPIE_OT_editgroup(Operator):
    """Edit selected group"""
    bl_idname = 'bagapie.editgroup'
    bl_label = 'Edit Group'
    bl_options = {'REGISTER', 'UNDO'}

    all: bpy.props.BoolProperty(default=False) # type: ignore

    def execute (self, context):
        group = bpy.context.active_object
        if group.get("bagapie") == "bound_box":
            coll = group_coll(group)
            for o in coll.objects:
                if self.all == True:
                    o.hide_select = False
                    if is_a_box(o):
                        edit_recursive(o)
                elif is_a_box(o.parent) == False or o.parent == group:
                    o.hide_select = False

            group["bagapie_locker"] = False
        
        bpy.ops.bagapie.double_click_edit("INVOKE_DEFAULT")

        return {'FINISHED'}


def edit_recursive(obj):
    coll = group_coll(obj)
    for o in coll.objects:
        o.hide_select = False
        if is_a_box(o):
            edit_recursive(o)
    obj["bagapie_locker"] = False


class BAGAPIE_OT_moveonlygroup(Operator):
    """Move every group obj into the group coll only. They will be unlinked from every other coll. Be carefull with this one"""
    bl_idname = 'bagapie.moveonlygroup'
    bl_label = 'Add to Group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute (self, context):
        group = context.active_object

        if group["bagapie"] == "bound_box":
            coll = group_coll(group)
            for o in coll.objects:
                o_coll = o.users_collection
                for c in o_coll:
                    if c != coll:
                        c.objects.unlink(o)
        return {'FINISHED'}


class BAGAPIE_OT_addgroup(Operator):
    """Add selected object into the active group"""
    bl_idname = 'bagapie.addgroup'
    bl_label = 'Add to Group'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        objs = context.selected_objects
        return (len(objs)>1)

    def execute (self, context):
        group = context.active_object
        objs = context.selected_objects

        if group.get("bagapie") and group["bagapie"] == "bound_box":
            coll = group_coll(group)
            for o in objs:
                if o != group:
                    if o.name not in coll.objects:
                        coll.objects.link(o)
                    if o.parent == None or is_a_box(o.parent):
                        o.parent = group
                        if is_a_box(group.parent):
                            o.location += (group.parent.location - group.location) - group.parent.location
                        else:
                            o.matrix_parent_inverse = group.matrix_world.inverted()
                    o.hide_select = group["bagapie_locker"]

        return {'FINISHED'}


class BAGAPIE_OT_removegroup(Operator):
    """Remove selected object into the active group"""
    bl_idname = 'bagapie.removegroup'
    bl_label = 'Remove to Group'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        objs = context.selected_objects
        return (len(objs)>1)

    def execute (self, context):
        group = context.active_object
        objs = context.selected_objects

        if group.get("bagapie") and group["bagapie"] == "bound_box":
            coll = group_coll(group)
            for o in objs:
                if o != group:
                    if o.name in coll.objects:
                        coll.objects.unlink(o)
                    if o.parent == group:
                        matrix = o.matrix_world.copy()
                        o.parent = None
                        o.matrix_world = matrix
                    if len(o.users_collection) == 0: # To avoid the obj disapear from the scene
                        bpy.context.scene.collection.objects.link(o)
            if len(coll.objects) == 0:
                bpy.ops.bagapie.ungroup()

        return {'FINISHED'}


class BAGAPIE_OT_isolategroup(Operator):
    """Isolate Group for editing"""
    bl_idname = 'bagapie.isolategroup'
    bl_label = 'Remove to Group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute (self, context):
        group_obj = context.active_object
        
        if is_in_local_view() is False:
            is_group(group_obj)
            bpy.context.view_layer.objects.active = group_obj
        else:
            bpy.ops.bagapie.lockgroup()

        bpy.ops.view3d.localview()

        return {'FINISHED'}


def is_group(group_obj):
    if group_obj.get("bagapie") and group_obj["bagapie"] == "bound_box":
        bpy.context.view_layer.objects.active = group_obj
        bpy.ops.bagapie.editgroup()
        coll = group_coll(group_obj)
        for o in coll.objects:
            o.select_set(True)
            is_group(o)


class BAGAPIE_OT_lockgroup(Operator):
    """Make group objects non selectable"""
    bl_idname = 'bagapie.lockgroup'
    bl_label = 'Lock Group'
    bl_options = {'REGISTER', 'UNDO'}

    all: bpy.props.BoolProperty(default=False) # type: ignore

    def execute (self, context):
        group_obj = bpy.context.active_object
        if self.all == True: # Lock everything
            lock_recursive(group_obj)
        else:
            coll = group_coll(group_obj)
            for o in coll.objects:
                o.hide_select = True
            group_obj["bagapie_locker"] = True
        return {'FINISHED'}


def lock_recursive(group_obj):
    coll = group_coll(group_obj)
    for o in coll.objects:
        o.hide_select = True
        if is_a_box(o):
            lock_recursive(o)
    group_obj["bagapie_locker"] = True


class BAGAPIE_OT_duplicategroup(Operator):
    """Duplicate Group"""
    bl_idname = 'bagapie.duplicategroup'
    bl_label = 'Duplicate Group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute (self, context):
        duplicate_group(mode=False)
        return {'FINISHED'}


class BAGAPIE_OT_duplicatelinkedgroup(Operator):
    """Duplicate Group witk link"""
    bl_idname = 'bagapie.duplicatelinkedgroup'
    bl_label = 'Duplicate Linked Group'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object
        return (o is not None)

    def execute (self, context):
        group = bpy.context.active_object
        if "bagapie" in group and group["bagapie"]:
            duplicate_group(mode=True)
        return {'FINISHED'}


def duplicate_group(mode=False):
    group = bpy.context.active_object
    objs = group_child(group)
    coll=None

    if group["bagapie"] == "bound_box":
        bpy.ops.object.select_all(action='DESELECT')
        coll = group_coll(group)

        for obj in objs:
            obj.hide_select = False
            obj.select_set(True)

        group.select_set(True)

        # DUPLICATE
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked": mode, "mode":'TRANSLATION'})
        
        group_new = bpy.context.active_object

        main_coll = get_or_create_collection("BagaPie")
        manage_coll = get_or_create_collection("BagaPie_Manage", main_coll)
        newgroup_coll = get_or_create_collection("BagaPie_Group", manage_coll)
        group_child_coll = bpy.data.collections.new("BagaPie_Group_Child")
        newgroup_coll.children.link(group_child_coll)

        objs = bpy.context.selected_objects
        for o in objs:
            if o != group_new:
                coll.objects.unlink(o)
                group_child_coll.objects.link(o)
        
        for mo2 in group_new.modifiers:
            if mo2.node_group.name.startswith('BagaPie_Group_Bounding_Box'):
                mo2['Socket_0'] = group_child_coll

        if group_new["bagapie_locker"] == True:
            bpy.ops.bagapie.lockgroup()

        bpy.ops.transform.translate("INVOKE_DEFAULT")


class BAGAPIE_OT_deletegroup(Operator):
    """Delete group and it's content"""
    bl_idname = 'bagapie.deletegroup'
    bl_label = 'Delete Group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute (self, context):
        
        group = bpy.context.active_object
        bpy.ops.object.select_all(action='DESELECT')
        for obj in group_child(group):
                obj.hide_select = False
                bpy.data.objects.remove(obj, do_unlink=True)

        coll = group_coll(group)
        if len(coll.objects) ==0:
            bpy.data.collections.remove(coll)

        bpy.context.view_layer.objects.active = group
        group.select_set(True)
        bpy.ops.object.delete()

        return {'FINISHED'}


def group_child(group):
    if group["bagapie"] == "bound_box":
        coll = group_coll(group)
        objs=coll.objects
        return(objs)


def is_a_box(obj):
    if obj is not None:
        if obj.type == 'MESH':
            for mo in obj.modifiers:
                if mo.type == 'NODES':
                    if mo.node_group.name.startswith('BagaPie_Group_Bounding_Box'):
                        return True
    return False


class BAGAPIE_OT_move_group_modal(Operator):
    """Move the obj group collection and it's content. Allow you to move a group without affecting it's instances. Use only if instances of this group exist"""
    bl_idname = "bagapie.move_group_modal"
    bl_label = "Move Group Instances Offset"
    bl_options = {'REGISTER', 'UNDO'}

    is_parent: bpy.props.BoolProperty(default=False) # type: ignore

    def modal(self, context, event):
        region = context.region
        rv3d = context.space_data.region_3d

        # CANCEL MOVE
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            for o in self.real_coll.objects:
                o.location = self.init_positions[o]
            self.collection.instance_offset = self.init_instance_offset
            return {'CANCELLED'}

        # AXIS CONSTRAINT
        if event.type in {'X', 'Y', 'Z'} and event.value == 'PRESS':
            axis = {'X': 0, 'Y': 1, 'Z': 2}[event.type]
            self.constraint = [0, 0, 0]
            self.constraint[axis] = 1
        if event.type in {'X', 'Y', 'Z'} and event.shift and event.value == 'PRESS':
            axis = {'X': 0, 'Y': 1, 'Z': 2}[event.type]
            self.constraint = [1, 1, 1]
            self.constraint[axis] = 0

        # MOTION MOUSE BASED
        if event.type == 'MOUSEMOVE':
            # REAL MOUSE MOTION
            dx = event.mouse_region_x - self.last_mouse_x
            dy = event.mouse_region_y - self.last_mouse_y

            # IGRORE WRAP (IF MOUSE MOVED OUTSIDE 3D VIEW)
            if abs(dx) > self.warp_threshold or abs(dy) > self.warp_threshold:
                dx = 0
                dy = 0

            # CONVERT MOTION TO 3D
            delta = bpy_extras.view3d_utils.region_2d_to_location_3d(
                region, rv3d, (event.mouse_region_x, event.mouse_region_y), self.init_positions[self.obj]
            ) - bpy_extras.view3d_utils.region_2d_to_location_3d(
                region, rv3d, (self.last_mouse_x, self.last_mouse_y), self.init_positions[self.obj]
            )

            # APPLY CONSTRAINT AXIS
            delta.x *= self.constraint[0]
            delta.y *= self.constraint[1]
            delta.z *= self.constraint[2]

            # MOVE OBJECT
            if self.is_parent == False:
                parent = None
                for o in self.collection.objects:
                    if parent is None and o.parent.get("bagapie") == "bound_box":
                        parent = o.parent
                        break
                if parent is not None: # MOVE GROUP BOX TOO
                    parent.location += delta
                else:
                    for o in self.collection.objects:
                        o.location += delta
            else:
                self.obj.location += delta

            self.collection.instance_offset += delta

            # STORE MOUSE POS BEFORE WRAP
            self.last_mouse_x = event.mouse_region_x
            self.last_mouse_y = event.mouse_region_y

            # CURSOR WRAP IF NECESSARY
            area = context.area
            width, height = area.width, area.height
            warp_x, warp_y = event.mouse_region_x, event.mouse_region_y

            if warp_x <= 2:
                warp_x = width - 3
            elif warp_x >= width - 2:
                warp_x = 3

            if warp_y <= 2:
                warp_y = height - 3
            elif warp_y >= height - 2:
                warp_y = 3

            # MOVE CURSOR BUT IGNORE IN WRAP DELTA
            bpy.context.window.cursor_warp(area.x + warp_x, area.y + warp_y)
            self.last_mouse_x = warp_x  # KEEP OLD POS TO IGNORE WRAP
            self.last_mouse_y = warp_y

        # END MOVING
        if event.type in {'LEFTMOUSE', 'RET'}:
            return {'FINISHED'}
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        # GET OBJ
        self.obj = context.active_object
        if not self.obj or not self.obj.users_collection:
            self.report({'WARNING'}, "No active object or collection found!")
            return {'CANCELLED'}

        # GET COLL
        self.collection = None
        self.real_coll = None
        for coll in self.obj.users_collection:
            if coll.name.startswith("BagaPie_Group_Child"):
                self.collection = coll
                self.real_coll = coll
                break
        if self.collection is None:
            for o in self.obj.children:
                for coll in o.users_collection:
                    if coll.name.startswith("BagaPie_Group_Child"):
                        self.collection = coll
                        for c in self.obj.users_collection:
                            if c.name.startswith("BagaPie_Group"):
                                self.real_coll = c
                        break
        if self.collection is None:
            self.report({'WARNING'}, "No active collection found!")
            return {'CANCELLED'}


        self.init_positions = {o: o.location.copy() for o in self.real_coll.objects}
        self.init_instance_offset = self.collection.instance_offset.copy()
        self.constraint = [1, 1, 1]  # NO CONSTRAINT BY DEFAULT
        self.sensitivity = 0.01  # MOTION SENSIBILITY
        self.warp_threshold = 100  # THRESHOLD TO IGNORE CURSOR WRAP

        # KEEP MOUSE INITIAL POS
        self.last_mouse_x = event.mouse_region_x
        self.last_mouse_y = event.mouse_region_y

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


def check_area(context, event):
    window = context.window
    if window:
        for area in window.screen.areas:
            if area.x <= event.mouse_x <= area.x + area.width and \
                area.y <= event.mouse_y <= area.y + area.height:
                if area.type == 'VIEW_3D':
                    return True
    return False


class BAGAPIE_OT_double_click_edit(Operator):
    """Double clic will isolate group or instances for editing"""
    bl_idname = "bagapie.double_click_edit"
    bl_label = "Double clic Edit Group/Instance"
    bl_options = {'REGISTER', 'UNDO'}

    _last_click_time = 0
    _double_click_threshold = 0.3  # Seuil en secondes pour détecter un double clic
    pref = Get_addon_pref()
    
    def modal(self, context, event):
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and check_area(context, event) == True:
            current_time = time.time()
            delta = current_time - self._last_click_time
            if delta < self._double_click_threshold:
                region = context.region
                rv3d = context.space_data.region_3d
                coord = (event.mouse_region_x, event.mouse_region_y)
                
                view_vector = v3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
                ray_origin = v3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
                
                depsgraph = context.evaluated_depsgraph_get()
                result, location, normal, index, obj, matrix = context.scene.ray_cast(depsgraph, ray_origin, view_vector)
                obj = bpy.context.object
                if obj.type == 'MESH' and is_a_box(obj) == True and context.mode == "OBJECT":
                    bpy.ops.bagapie.isolategroup()
                elif obj.type == 'EMPTY' and check_if_instance(obj) == True and context.mode == "OBJECT":
                    bpy.ops.bagapie.editinstancegroup()
                elif is_in_local_view() == True and context.mode == "OBJECT":
                    bpy.ops.view3d.localview()
                return {'RUNNING_MODAL'}
            self._last_click_time = current_time

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            Get_addon_pref().feature_enabled = False
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        bagapie_pref = Get_addon_pref()
        if context.area.type != 'VIEW_3D':
            self.report({'WARNING'}, "Op must be run from the 3d view.")
            return {'CANCELLED'}
        if context.mode != 'OBJECT':
            self.report({'WARNING'}, "Only in Object Mode.")
            return {'CANCELLED'}

        bagapie_pref.feature_enabled = True
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


def check_if_instance(obj):
    bagapie_instances = bpy.data.collections.get("BagaPie_Instances")

    if bagapie_instances:
        for empty in bagapie_instances.objects:
            if empty.type == 'EMPTY':
                if empty.instance_collection is not None:
                    condition_met = True
                    break
        else:
            condition_met = False
    else:
        condition_met = False
    return(condition_met)


def check_parent_group(obj):
    child_collections = {child.users_collection[0] for child in obj.children if child.users_collection}
    bagapie_instances = bpy.data.collections.get("BagaPie_Instances")

    if bagapie_instances:
        for empty in bagapie_instances.objects:
            if empty.type == 'EMPTY':
                if empty.instance_collection in child_collections:
                    condition_met = True
                    break
        else:
            condition_met = False
    else:
        condition_met = False
    return(condition_met)


def check_group_instance(obj):
    obj_collections = set(obj.users_collection)
    bagapie_instances = bpy.data.collections.get("BagaPie_Instances")

    if bagapie_instances:
        for empty in bagapie_instances.objects:
            if empty.type == 'EMPTY':
                if empty.instance_collection in obj_collections:
                    condition_met = True
                    break
        else:
            condition_met = False
    else:
        condition_met = False
    return(condition_met)


# class BAGAPIE_OT_replace_shortcut(Operator):
#     """Replace the Blender Group shortcut by the BagaPie Group Shortcut. Pref can be restored"""
#     bl_idname = 'bagapie.replace_shortcut'
#     bl_label = 'Replace Shortcut'

#     def execute (self, context):
#         global addon_keymaps
#         addon_keymaps = []
#         wm = bpy.context.window_manager
#         kc = wm.keyconfigs.addon
#         kc_u = wm.keyconfigs.user

#         for km in kc_u.keymaps:
#             for kmi in km.keymap_items:
#                 if kmi.idname == "collection.create" and kmi.type == 'G' and kmi.ctrl:
#                     kmi.active=False
#                     debug("Collection.create disabled")

#         add=True
#         for km in kc_u.keymaps:
#             for kmi in km.keymap_items:
#                 if kmi.idname == "bagapie.group" and kmi.type == 'G' and kmi.ctrl:
#                     add=False
#                     debug("Shortcut already exist")

#         if add == True:
#             km = kc.keymaps.new(name='3D View', space_type='VIEW_3D', region_type = "WINDOW")
#             kmi = km.keymap_items.new("bagapie.group", type='G', ctrl=True, value='PRESS')
#             addon_keymaps.append((km,kmi))
#             debug("Shortcut Added")

#         Warning(message="Select Objects, Ctrl + G to group them ! Don't forget to save preferences.")
#         return {'FINISHED'}

class BAGAPIE_OT_replace_shortcut(bpy.types.Operator):
    """Replace the Blender Group shortcut by the BagaPie Group Shortcut. Pref can be restored"""
    bl_idname = 'bagapie.replace_shortcut'
    bl_label = 'Replace Shortcut'

    def execute(self, context):
        global addon_keymaps
        addon_keymaps = []
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon

        if not kc:
            self.report({'WARNING'}, "Failed to access addon keyconfig.")
            return {'CANCELLED'}

        # check if shortcut already exist
        already_exists = False
        for km in kc.keymaps:
            for kmi in km.keymap_items:
                if kmi.idname == "bagapie.group" and kmi.type == 'G' and kmi.ctrl:
                    already_exists = True
                    debug("Shortcut already exists")

        if not already_exists:
            km = kc.keymaps.new(name='3D View', space_type='VIEW_3D', region_type='WINDOW')
            kmi = km.keymap_items.new("bagapie.group", type='G', ctrl=True, value='PRESS')
            addon_keymaps.append((km, kmi))
            debug("Shortcut Added")

        Warning(message="Select Objects, Ctrl + G to group them! Preferences will now persist.")
        return {'FINISHED'}



def group_coll(group_obj):
    for mo in group_obj.modifiers:
        if mo.node_group.name.startswith('BagaPie_Group_Bounding_Box'):
            coll = mo['Socket_0']
            return coll


class NODE_OT_add_custom_socket(bpy.types.Operator):
    bl_idname = "bagapie.add_custom_socket"
    bl_label = "Add Node to Panel Socket"
    bl_description = "Add a custom socket to the BagaPie Panel"
    bl_options = {'REGISTER', 'UNDO'}
    
    prefix: bpy.props.StringProperty(default = "L_") # type: ignore
    val: bpy.props.IntProperty(default=1, min=1, max=9) # type: ignore

    def invoke(self, context, event):
        if self.prefix == "S_" or self.prefix == 'SCALE' or self.prefix == 'PX_':
            return context.window_manager.invoke_props_dialog(self)
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        label = "Scale"
        if self.prefix == "PX_":
            label = "ID :"
            layout.label(text="Add the ID number as prefix")
            layout.label(text="to inputs descriptions to control visibility.")
        layout.prop(self, "val", text=label)

    def execute(self, context):

        space = bpy.context.space_data
        if space.tree_type == 'GeometryNodeTree':
            modifier = bpy.context.object.modifiers.active
            node_group_tree = space.edit_tree
            desc = node_group_tree.interface.active.description
        elif space.tree_type == 'ShaderNodeTree':
            if hasattr(space.node_tree.nodes.active, "node_tree"):
                node_group_tree = space.node_tree.nodes.active.node_tree
                desc = node_group_tree.interface.active.description
        if not node_group_tree:
            return {'FINISHED'}
        prefix = self.prefix

        # IF BP DISPLAY NOT PRESENT
        if space.tree_type == 'GeometryNodeTree' and node_group_tree:
            if not modifier.name.startswith("BP_") and not node_group_tree.name.startswith("BP_") and not node_group_tree.description.startswith("BP_"):
                space.edit_tree.description = "BP_"+space.edit_tree.description
        elif space.tree_type == 'ShaderNodeTree' and node_group_tree:
            if not node_group_tree.name.startswith("BP_") and not node_group_tree.name.startswith("BP_") and not node_group_tree.description.startswith("BP_"):
                node_group_tree.description = "BP_"+node_group_tree.description

        # IF RESET
        if prefix == "RESET":
            node_group_tree.interface.active.description = ""
            return {'FINISHED'}

        # IF SIMPLE TYPE CHANGE
        simple_prefix = ["URL_", "L_", "C_", "V_", "P_", "PX_"]
        if prefix in simple_prefix:
            if prefix == "PX_":
                prefix = "P"+str(self.val)+"_"

            for sp in simple_prefix:
                if sp in desc:
                    desc = desc.replace(sp, prefix)
                    node_group_tree.interface.active.description = desc
                    if prefix == "C_":
                        node = node_group_tree.nodes.active
                        if node and node.type == 'CURVE_FLOAT':
                            node.label =  node_group_tree.interface.active.name
                        else:
                            Warning(message="Set input name as label in your Float Curve Node. Or select node and retry.")
                    return {'FINISHED'}
            node_group_tree.interface.active.description = prefix
            if prefix == "C_":
                node = node_group_tree.nodes.active
                if node and node.type == 'CURVE_FLOAT':
                    node.label = node_group_tree.interface.active.name
                else:
                    Warning(message="Set input name as label in your Float Curve Node. Or select node and retry.")
            return {'FINISHED'}

        # IF SEPARATOR
        if prefix == 'S_':
            node_group_tree.interface.active.description = prefix + str(self.val) + "_"
            return {'FINISHED'}

        # IF SCALE
        if prefix == 'SCALE':
            if desc.endswith("_") and desc[:-1][-1:].isdigit():
                desc = desc[:-2]
            node_group_tree.interface.active.description = desc + str(self.val) + "_"
            return {'FINISHED'}

        # IF REMOVE FROM
        if prefix == "-B" or prefix == "-R":
            pf =""
            if "URL_" in desc:
                desc = desc[:-4]
                pf="URL_"
            elif "L_" in desc:
                desc = desc[:-2]
                pf="L_"
            elif "C_" in desc:
                desc = desc[:-2]
                pf="C_"
            elif "V_" in desc:
                desc = desc[:-2]
                pf="V_"
            elif "S_" in desc:
                pf = desc[-4:]
                desc = desc[:-4]

            if prefix == "-B":
                if desc.endswith("B_"):
                    desc = desc[:-2]
                elif desc.endswith("B"):
                    desc = desc[:-1]
                        
            if prefix == "-R":
                if desc.endswith("R_"):
                    desc = desc[:-2]
                elif desc.endswith("R"):
                    desc = desc[:-1]

            node_group_tree.interface.active.description = desc + pf
            return {'FINISHED'}

        # IF BOX OR ROW
        if prefix in ['B', 'B_', 'R', 'R_']:
            new_desc=""
            if "URL_" in desc:
                desc = desc[:-4]
                new_desc = desc + prefix + "URL_"
            elif "L_" in desc:
                desc = desc[:-2]
                new_desc = desc + prefix + "L_"
            elif "C_" in desc:
                desc = desc[:-2]
                new_desc = desc + prefix + "C_"
            elif "V_" in desc:
                desc = desc[:-2]
                new_desc = desc + prefix + "V_"
            elif "S_" in desc:
                pf = desc[-4:]
                desc = desc[:-4]
                new_desc = desc + prefix + pf

            node_group_tree.interface.active.description = new_desc

        return {'FINISHED'}


def group_prefix_menu(self, context):
    
    space = bpy.context.space_data
    desc = "None"
    if space.tree_type == 'GeometryNodeTree':
        node_group_tree = space.edit_tree
        desc = node_group_tree.interface.active.description
    elif space.tree_type == 'ShaderNodeTree':
        if hasattr(space.node_tree.nodes.active, "node_tree"):
            group_tree = space.node_tree.nodes.active.node_tree
            desc = group_tree.interface.active.description

    if desc != "None":
        layout = self.layout
        layout.separator()
        layout.label(text='BagaPie Node to Panel')
        # VALUES
        layout.operator("bagapie.add_custom_socket",text="As Value", icon='HIDE_OFF').prefix = "V_"
        layout.operator("bagapie.add_custom_socket",text="As Label", icon='HIDE_OFF').prefix = "L_"
        layout.operator("bagapie.add_custom_socket",text="As Curve", icon='HIDE_OFF').prefix = "C_"
        layout.operator("bagapie.add_custom_socket",text="As Separator", icon='HIDE_OFF').prefix = "S_"
        layout.operator("bagapie.add_custom_socket",text="As Simple Button", icon='HIDE_OFF').prefix = "P_"
        layout.operator("bagapie.add_custom_socket",text="As ID Button", icon='HIDE_OFF').prefix = "PX_"
        layout.separator()
        # MANAGE
        if not desc.startswith("P"):
            if "URL_" in desc or "L_" in desc or "C_" in desc or "V_" in desc or "S_" in desc:
                if desc.endswith("URL_") or desc.startswith("S_"):
                    desc = desc[:-4]
                elif any(desc.endswith(prefix) for prefix in ("L_", "C_", "V_")):
                    desc = desc[:-2]

                layout.operator("bagapie.add_custom_socket",text="In New Box", icon='ADD').prefix = "B_"
                layout.operator("bagapie.add_custom_socket",text="In Box", icon='ADD').prefix = "B"
                if desc.endswith("B") or desc.endswith("B_"):
                    layout.operator("bagapie.add_custom_socket",text="Out Box", icon='REMOVE').prefix = "-B"
                layout.operator("bagapie.add_custom_socket",text="In New Row", icon='ADD').prefix = "R_"
                layout.operator("bagapie.add_custom_socket",text="In Row", icon='ADD').prefix = "R"
                if desc.endswith("R") or desc.endswith("R_"):
                    layout.operator("bagapie.add_custom_socket",text="Out Row", icon='REMOVE').prefix = "-R"
                layout.separator()

        layout.operator("bagapie.add_custom_socket",text="Scale", icon='FULLSCREEN_ENTER').prefix = "SCALE"
        layout.separator()

        layout.operator("bagapie.add_custom_socket",text="Reset", icon='FILE_REFRESH').prefix = "RESET"


class BAGAPIE_OT_auto_instance(Operator):
    """Turn automatically the selection into instance"""
    bl_idname = 'bagapie.autoinstance'
    bl_label = 'Replace Shortcut'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.selected_objects
        return (
            len(o)>=1 and is_in_local_view()==False
        )

    def execute (self, context):
        bpy.ops.bagapie.group()
        bpy.ops.bagapie.instance()
        return {'FINISHED'}


# FOR FUTURE BLENDER VERSIONS :

# class BAGAPIE_OT_bake_single_node(bpy.types.Operator):
#     bl_idname = "node.bake_single_node"
#     bl_label = "Bake Node"
#     node_name: bpy.props.StringProperty()
#     modifier_name: bpy.props.StringProperty()

#     def execute(self, context):
#         modifier = context.object.modifiers.get(self.modifier_name)
#         node = modifier.node_group.nodes.get(self.node_name)

#         session_uid = modifier.bake_settings.session_uid
#         bake_id = node.bake_id

#         bpy.ops.object.geometry_node_bake_single(
#             session_uid=session_uid,
#             modifier_name=self.modifier_name,
#             bake_id=bake_id
#         )
#         return {'FINISHED'}


# class BAGAPIE_OT_clear_bake_node(bpy.types.Operator):
#     bl_idname = "node.clear_bake_node"
#     bl_label = "Clear Bake Node"
#     node_name: bpy.props.StringProperty()
#     modifier_name: bpy.props.StringProperty()

#     def execute(self, context):
#         modifier = context.object.modifiers.get(self.modifier_name)
#         node = modifier.node_group.nodes.get(self.node_name)

#         session_uid = modifier.bake_settings.session_uid
#         bake_id = node.bake_id

#         bpy.ops.object.geometry_node_bake_delete_single(
#             session_uid=session_uid,
#             modifier_name=self.modifier_name,
#             bake_id=bake_id
#         )
#         return {'FINISHED'}


classes = [
    BAGAPIE_OT_ungroup,
    BAGAPIE_OT_group,
    BAGAPIE_OT_editgroup,
    BAGAPIE_OT_lockgroup,
    BAGAPIE_OT_duplicategroup,
    BAGAPIE_OT_duplicatelinkedgroup,
    BAGAPIE_OT_deletegroup,
    BAGAPIE_OT_addgroup,
    BAGAPIE_OT_removegroup,
    BAGAPIE_OT_isolategroup,
    BAGAPIE_OT_editinstancegroup,
    BAGAPIE_OT_moveonlygroup,
    BAGAPIE_OT_move_group_modal,
    BAGAPIE_OT_double_click_edit,
    BAGAPIE_OT_replace_shortcut,
    BAGAPIE_PT_group_panel,
    NODE_OT_add_custom_socket,
    BAGAPIE_OT_auto_instance,
]