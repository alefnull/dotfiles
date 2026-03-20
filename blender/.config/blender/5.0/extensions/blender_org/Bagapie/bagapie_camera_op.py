import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import Import_Nodes, Warning

class BAGAPIE_OT_camera_remove(Operator):
    """ Remove Bagapie Camera Culling """
    bl_idname = "bagapie.camera_remove"
    bl_label = 'Remove Bagapie Camera Culling'

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
            scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
            scatt_nde_group = scatter_modifier.node_group
            camera_cull_node = scatt_nde_group.nodes.get(modifiers[1])
            
            if len(camera_cull_node.outputs[0].links) > 0:
                scatter_node = camera_cull_node.outputs[0].links[0].to_node
                scatter_node_seed = scatter_node.inputs[6].default_value
                scatter_node.inputs[6].default_value = scatter_node_seed+1
                scatter_node.inputs[6].default_value = scatter_node_seed-1
            
            scatt_nde_group.nodes.remove(camera_cull_node)
        except:
            print("Some elements (modifier, nodes or objects) were missing.")

        # REMOVE FROM LIST
        context.object.bagapieList.remove(self.index)
        
        if obj.bagapieIndex > 0:
            obj.bagapieIndex = obj.bagapieIndex-1

        return {'FINISHED'}


class BAGAPIE_OT_camera(Operator):
    """Add Camera Culling"""
    bl_idname = 'bagapie.camera'
    bl_label = bagapieModifiers['camera']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )

    def execute(self, context):

        # IF SCATTER MODIFIER IS PRESENT
        target = bpy.context.active_object
        if target.modifiers.get("BagaPie_Scatter"):

            # IF SCATTER NODES ARE PRESENT
            nodegroup = target.modifiers.get("BagaPie_Scatter").node_group
            index = target.bagapieIndex
            if index >= len(target.bagapieList):
                Warning("You must select a Scatter layer.", "WARNING", 'ERROR') 
                return {'FINISHED'}

            val = json.loads(target.bagapieList[index]['val'])
            modifiers = val['modifiers']
            scatt_nde_main = nodegroup.nodes.get(modifiers[1])
                    
            if scatt_nde_main.label != "BagaPie_Scatter":
                Warning("You must select a Scatter layer.", "WARNING", 'ERROR') 
                return {'FINISHED'}

            if scatt_nde_main:

                
                target = context.object
                val = json.loads(target.bagapieList[target.bagapieIndex]['val'])
                modifiers = val['modifiers']

                objs = bpy.context.selected_objects #Add objects to coll instance
                objs.remove(target)
                if not objs:
                    Warning("No camera detected, you must select a camera.", "WARNING", 'ERROR') 
                    return {'FINISHED'}
                
                else:
                    # GET CAMERA
                    for obj in objs:
                        if obj.type == 'CAMERA' or obj.type == 'EMPTY':
                            camera = obj
                            break
                        else:
                            Warning("No camera detected, you must select a camera.", "WARNING", 'ERROR') 
                            return {'FINISHED'}

                    # GET NODES
                    scatt_nde = nodegroup.nodes
                    scatter_nodes = 0
                    effector_count = 0
                    scatter_latest = None
                    effector_latest = None
                    camera_cull_node = None

                    for node in scatt_nde:
                        # Count how many scatter and effector exist
                        if node.label == "BagaPie_Scatter":
                            scatter_nodes += 1
                            if scatter_latest is None:
                                scatter_latest = node
                            else:
                                if node.location[0] < scatter_latest.location[0]:
                                    scatter_latest = node
                        if node.label == "BagaPie_Effector":
                            effector_count += 1
                            if effector_latest is None:
                                effector_latest = node
                            else:
                                if node.location[0] < effector_latest.location[0]:
                                    effector_latest = node
                        if node.label == "BagaPie_Camera_Culling":
                            camera_cull_node = node

                    if camera_cull_node is None:
                        # ADD NODE
                        Import_Nodes(self,context,"BagaPie_Camera_Culling")
                        camera_cull_node = nodegroup.nodes.new(type='GeometryNodeGroup')
                        camera_cull_node.node_tree = bpy.data.node_groups['BagaPie_Camera_Culling']
                        camera_cull_node.name = "BagaPie_Camera_Culling"
                        camera_cull_node.label = "BagaPie_Camera_Culling"

                        # POSITION NODE
                        camera_cull_node.location = (0, 260)

                    # LINK NODES CONFIG
                    new_link = nodegroup.links
                    new_link.new(camera_cull_node.outputs[0], scatt_nde_main.inputs[24])
                    camera_cull_node.inputs[0].default_value = camera

                    add_cam_prop = True
                    for idx in range(len(target.bagapieList)):
                        val = json.loads(target.bagapieList[idx]['val'])
                        mo_type = val['name']
                        modifiers = val['modifiers']
                        if mo_type == "camera":
                            add_cam_prop = False
                            
                    if add_cam_prop:
                        # CUSTOM PROPERTY
                        val = {
                            'name': 'camera',
                            'modifiers':[
                                        "BagaPie_Scatter",              # MODIFIER NAME
                                        camera_cull_node.name,     # NODE NAME
                                        ]
                        }
                        item = target.bagapieList.add()
                        item.val = json.dumps(val)
                
                        target.bagapieIndex = len(target.bagapieList)-1

        return {'FINISHED'}



classes = [
    BAGAPIE_OT_camera_remove,
    BAGAPIE_OT_camera
]