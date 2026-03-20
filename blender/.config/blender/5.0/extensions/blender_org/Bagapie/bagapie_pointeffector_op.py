import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import Import_Nodes, Warning

class BAGAPIE_OT_pointeffector_remove(Operator):
    """ Remove Bagapie Point Effector modifiers """
    bl_idname = "bagapie.pointeffector_remove"
    bl_label = 'Remove Bagapie Point Effector'

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
            scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
            scatt_nde_group = scatter_modifier.node_group
            effector_nde_main = scatt_nde_group.nodes.get(modifiers[1])
            effector_coll = effector_nde_main.inputs[0].default_value

            # GET NODES AND COUNT
            effectors_nodes = []
            links_nde = effector_nde_main
                
            while len(effectors_nodes) >= 0:
                if len(links_nde.inputs[4].links) > 0:
                    links_nde = links_nde.inputs[4].links[0].from_node
                    effectors_nodes.append(links_nde)
                else:
                    break

            # Actualise Node Position
            for node in effectors_nodes:
                node.location[0] += 200

            # DELETE NODES
            link_input_node = None
            link_output_node = None
            
            # get in and out link for this effector
            try:
                link_input_node = effector_nde_main.inputs[4].links[0].from_node
            except:
                link_input_node = None
            link_output_node = effector_nde_main.outputs[0].links[0].to_node

            scatt_nde_group.nodes.remove(effector_nde_main)

            # remove obj from coll and coll
            for ob in effector_coll.objects:
                effector_coll.objects.unlink(ob) 
            bpy.data.collections.remove(effector_coll)

            # RELINK EXISTENT NODES
            if link_input_node is not None:
                new_link = scatt_nde_group.links
                if link_output_node.label == "BagaPie_Scatter":
                    new_link.new(link_input_node.outputs[0], link_output_node.inputs[21])
                else:
                    new_link.new(link_input_node.outputs[0], link_output_node.inputs[4])

        except:
            Warning(message="Check in the node tree that the node effector is removed.", title='Warning', icon='ERROR')
            print("Something went wrong.")
            print("Check in the node tree that the node effector is removed.")

        # REMOVE FROM LIST
        context.object.bagapieList.remove(self.index)
        
        if obj.bagapieIndex > 0:
            obj.bagapieIndex = obj.bagapieIndex-1

        return {'FINISHED'}


class BAGAPIE_OT_pointeffector(Operator):
    """Creates walls from the edges of the selected object or from curves"""
    bl_idname = 'bagapie.pointeffector'
    bl_label = bagapieModifiers['pointeffector']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )

 # EXECUTED SCRIPT
    def execute(self, context):

            # IF SCATTER MODIFIER IS PRESENT
            target = bpy.context.active_object
            if target.modifiers.get("BagaPie_Scatter"):

             # IF SCATTER NODES ARE PRESENT
                nodegroup = target.modifiers.get("BagaPie_Scatter").node_group
                nodes = nodegroup.nodes
                index = target.bagapieIndex
                val = json.loads(target.bagapieList[index]['val'])
                modifiers = val['modifiers']
                scatter_node = nodegroup.nodes.get(modifiers[1])
                if scatter_node.label != "BagaPie_Scatter":
                    Warning("You must select a Scatter layer.", "WARNING", 'ERROR') 
                    return {'FINISHED'}
                scatter_nodes = []
                for node in nodes:
                    if node.label == 'BagaPie_Scatter':
                        scatter_nodes.append(node)

                if scatter_node:

                    obj = bpy.context.selected_objects #Add objects to coll instance
                    obj.remove(target)
                    if not obj:
                        Warning("No valid effector selected.", "WARNING", 'ERROR') 
                        return {'FINISHED'}
                    
                    else:
                        # COLLECTION
                        effector_coll = Collection_Setup(self,context,target)
                        for ob in obj:
                            if ob.name not in effector_coll.objects:
                                effector_coll.objects.link(ob)


                        # GET NODES AND COUNT
                        nodes = nodegroup.nodes
                        effector_count_real = 0
                        effector_latest = scatter_node

                        if len(scatter_node.inputs[21].links) > 0:
                            links_nde = scatter_node.inputs[21].links[0].from_node
                            effector_count_real += 1
                            
                            while effector_count_real >= 1:
                                if len(links_nde.inputs[4].links) > 0:
                                    links_nde = links_nde.inputs[4].links[0].from_node
                                    effector_latest = links_nde
                                    effector_count_real += 1
                                else:
                                    effector_latest = links_nde
                                    break
                                

                        # ADD NODES
                        Import_Nodes(self,context,"BagaPie_Effector")
                        effector_nde_main = nodegroup.nodes.new(type='GeometryNodeGroup')
                        effector_nde_main.node_tree = bpy.data.node_groups['BagaPie_Effector']
                        effector_nde_main.name = "BagaPie_Effector"
                        effector_nde_main.label = "BagaPie_Effector"

                        # POSITION NODES
                        effector_nde_main.location = (scatter_node.location[0]-200-(effector_count_real*200), scatter_node.location[1]-930)

                        # LINK NODES,UI & CONFIG
                        new_link = nodegroup.links

                        if effector_latest != scatter_node:
                            new_link.new(effector_nde_main.outputs[0], effector_latest.inputs[4])
                        else:
                            new_link.new(effector_nde_main.outputs[0], scatter_node.inputs[21])
                        
                        effector_nde_main.inputs[0].default_value = effector_coll

                        # CUSTOM PROPERTY
                        val = {
                            'name': 'pointeffector',
                            'modifiers':[
                                        "BagaPie_Scatter",              # MODIFIER NAME
                                        effector_nde_main.name,     # NODE NAME
                                        ]
                        }
                        item = target.bagapieList.add()
                        item.val = json.dumps(val)
                
                        target.bagapieIndex = len(target.bagapieList)-1

                        return {'FINISHED'}

###################################################################################
# MANAGE COLLECTION
###################################################################################
def Collection_Setup(self,context,target):
    # Create collection and check if the main "Baga Collection" does not already exist
    if bpy.data.collections.get("BagaPie") is None:
        main_coll = bpy.data.collections.new("BagaPie")
        bpy.context.scene.collection.children.link(main_coll)
        scatter_master_coll = bpy.data.collections.new("BagaPie_Scatter")
        main_coll.children.link(scatter_master_coll)
        effector_coll = bpy.data.collections.new("BagaPie_Effector_" + target.name)
        scatter_master_coll.children.link(effector_coll)
    # If the main collection Bagapie already exist
    elif bpy.data.collections.get("BagaPie_Scatter") is None:
        main_coll = bpy.data.collections["BagaPie"]
        scatter_master_coll = bpy.data.collections.new("BagaPie_Scatter")
        main_coll.children.link(scatter_master_coll)
        effector_coll = bpy.data.collections.new("BagaPie_Effector_" + target.name)
        scatter_master_coll.children.link(effector_coll)
    # If the main collection Bagapie_Scatter already exist
    else:
        effector_coll = bpy.data.collections.new("BagaPie_Effector_" + target.name)
        scatter_master_coll = bpy.data.collections["BagaPie_Scatter"]
        scatter_master_coll.children.link(effector_coll)

    return effector_coll


classes = [
    BAGAPIE_OT_pointeffector_remove,
    BAGAPIE_OT_pointeffector,
]