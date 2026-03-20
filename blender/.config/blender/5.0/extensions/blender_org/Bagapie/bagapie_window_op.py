
# -----------------------------------------------------------------
# NOTICE: The currend Windows system is outdated and will soon be 
# replaced by the new window system (bagapie_windows_v2_op).
# 
# It remains functional for now but will not receive further updates.
# -----------------------------------------------------------------

import bpy
import json
import random
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import get_or_create_collection

class BAGAPIE_OT_window_remove(Operator):
    """ Remove Bagapie Window modifiers """
    bl_idname = "bagapie.window_remove"
    bl_label = 'Remove Bagapie Window'

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
        modifiers = val['modifiers']

        if modifiers[6] == "win":
            win_bool = bpy.data.objects[modifiers[4]]
            wall = bpy.data.objects[modifiers[7]]
            
            # get the line to remove on the wall and modifier to remove
            index = 0
            for i in range(len(wall.bagapieList)):
                value = json.loads(wall.bagapieList[index]['val'])
                target_modifiers = value['modifiers']
                mo_type = val['name']
                if mo_type == "window":
                    if modifiers[5] in target_modifiers:
                        # remove modifier from line
                        wall.bagapieList.remove(index)
                        index -=1
                        wall.modifiers.remove(wall.modifiers[modifiers[5]])
                index = index + i
            bpy.data.objects.remove(win_bool)
            bpy.data.objects.remove(obj)
            print("WIN")

        
        elif modifiers[6] == "wall":
            try:
                win_bool = bpy.data.objects[modifiers[5]]
                win = bpy.data.objects[modifiers[7]]            
                obj.modifiers.remove(obj.modifiers[modifiers[0]])
                bpy.data.objects.remove(win)
                bpy.data.objects.remove(win_bool)
            
                obj.bagapieList.remove(self.index)
            except:
                obj.bagapieList.remove(self.index)
            if len(obj.bagapieList) <= obj.bagapieIndex and obj.bagapieIndex != 0:
                obj.bagapieIndex -= 1

        return {'FINISHED'}

class BAGAPIE_OT_window(Operator):
    """Create windows. First draw its dimensions then give it a depth that corresponds to that of the wall. Tool made to work with the Wall tool"""
    bl_idname = "bagapie.window"
    bl_label = bagapieModifiers['window']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )

    win_offset: bpy.props.FloatProperty(
        name="Offset",
        description="Position de la fenêtre.",
        default=0,
        soft_min=0,
        soft_max=10,
    ) # type: ignore
    win_men_size: bpy.props.FloatProperty(
        name="Wire Size",
        description="Taille de menuiseries.",
        default=0.1,
        min=0,
        soft_max=0.5,
    ) # type: ignore

    def execute(self, context):

    # CHECK AND CREATE COLLECTION
        main_coll = get_or_create_collection("BagaPie")
        win_coll = get_or_create_collection("BagaPie_Window", main_coll)

    # CREATE AND GET OBJECT
        target = bpy.context.object
        bpy.ops.mesh.primitive_plane_add()
        win = bpy.context.object
        win.name = "Baga_Window" + str(random.randint(0,9999999))
        bpy.ops.object.duplicate_move_linked()
        win_bool = bpy.context.object
        win_bool.name = "Baga_Window_Bool" + str(random.randint(0,9999999))

    # WINDOWS PRESET
        new = bpy.data.objects[win.name].modifiers.new
        win_weld = new(name='BagaWindow_Weld', type='WELD')
        win_disp = new(name='BagaWindow_Displace', type='DISPLACE')
        win_wire = new(name='BagaWindow_Wire', type='WIREFRAME')
        win_beve = new(name='BagaWindow_Bevel', type='BEVEL')
        win.parent = target

        obj_old_coll = win.users_collection
        for ob in obj_old_coll:
            ob.objects.unlink(win)
        win_coll.objects.link(win)

        win_weld.merge_threshold = 0.3
        win_weld.mode = 'CONNECTED'
        win_weld.show_on_cage = True

        win_disp.show_in_editmode = True
        win_disp.strength = self.win_offset

        win_wire.show_in_editmode = True
        win_wire.thickness = self.win_men_size
        win_wire.use_boundary = True
        win_wire.use_replace = False
        win_wire.material_offset = 1

        win_beve.width = 0.5
        win_beve.angle_limit = 1.55
        win_beve.profile_type = 'CUSTOM'

    # BOOLEAN PRESET
        new = bpy.data.objects[win_bool.name].modifiers.new
        win_bool_disp = new(name='BagaWindowBool_Displace', type='DISPLACE')
        win_bool_disp.show_in_editmode = True
        win_bool_disp.strength = 0.01
        win_bool.display_type = 'BOUNDS'
        win_bool.visible_camera = False
        win_bool.visible_diffuse = False
        win_bool.visible_glossy = False
        win_bool.visible_transmission = False
        win_bool.visible_volume_scatter = False
        win_bool.visible_shadow = False
        win_bool.parent = target

        obj_old_coll = win_bool.users_collection
        for ob in obj_old_coll:
            ob.objects.unlink(win_bool)
        win_coll.objects.link(win_bool)

    # BOOLEAN ON TARGET (WALL)
        new = bpy.data.objects[target.name].modifiers.new
        target_bool = new(name='BagaWindow_Boolean' + str(random.randint(0,9999999)), type='BOOLEAN')
        target_bool.show_in_editmode = True
        target_bool.object = win_bool

    # ADD MATERIAL
            # Glass
        mat_glass = bpy.data.materials.new(name="BagaPie_Glass")
        mat_glass.blend_method = 'HASHED'
        mat_glass.use_nodes = True
        mat_glass.diffuse_color = (0.34, 0.6, 0.8, 0.75)
        principled_node = mat_glass.node_tree.nodes.get('Principled BSDF')
        mat_glass_nodeout = mat_glass.node_tree.nodes.get('Material Output')
        mat_glass.node_tree.nodes.remove(principled_node)

        mat_glass_nodegloss = mat_glass.node_tree.nodes.new('ShaderNodeBsdfGlossy')
        mat_glass_nodetrans = mat_glass.node_tree.nodes.new('ShaderNodeBsdfTransparent')
        mat_glass_nodemix = mat_glass.node_tree.nodes.new('ShaderNodeMixShader')

        mat_glass_nodegloss.location = (-200, 150)
        mat_glass_nodetrans.location = (-200, 450)
        mat_glass_nodemix.location = (100, 300)

        mat_glass.node_tree.links.new(mat_glass_nodetrans.outputs[0], mat_glass_nodemix.inputs[1])
        mat_glass.node_tree.links.new(mat_glass_nodegloss.outputs[0], mat_glass_nodemix.inputs[2])
        mat_glass.node_tree.links.new(mat_glass_nodemix.outputs[0], mat_glass_nodeout.inputs[0])

        mat_glass_nodegloss.inputs[1].default_value = 0
        mat_glass_nodemix.inputs[0].default_value = 0.25

            #Window
        mat_win = bpy.data.materials.new(name="BagaPie_Window")
        mat_win.use_nodes = True
        mat_win.diffuse_color = (0.4, 0.4, 0.4, 1)
        mat_win_nodebsdf = mat_win.node_tree.nodes.get('Principled BSDF')
        mat_win_nodebsdf.inputs[0].default_value = (0.1, 0.1, 0.1, 1)

            #Assign material
        win.active_material = mat_glass
        win.data.materials.append(mat_win)

    # NOW ADD WINDOWS WITH ADD OBJECT TOOL
        bpy.context.view_layer.objects.active = win_bool
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.wm.tool_set_by_id(name="builtin.primitive_cube_add")

    # CUSTOM PROPERTIES
        val = {
            'name': 'window',
            'modifiers':[
                win_weld.name,
                win_disp.name,
                win_wire.name,
                win_beve.name,
                win_bool.name, #boolean object 4
                target_bool.name, #modifier 5
                "win",
                target.name,
            ]
        }
        
        item = win.bagapieList.add()
        item.val = json.dumps(val)

        val = {
            'name': 'window',
            'modifiers':[
                target_bool.name, #modifier
                win_weld.name,
                win_disp.name,
                win_wire.name,
                win_beve.name,
                win_bool.name, #boolean object 5
                "wall",
                win.name,
            ]
        }
        
        item = target.bagapieList.add()
        item.val = json.dumps(val)
        
        return {'FINISHED'}
    
classes = [
    BAGAPIE_OT_window_remove,
    BAGAPIE_OT_window
]