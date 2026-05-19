import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers
import bmesh
from random import random, randint
from .utils import Get_addon_pref, Import_Nodes, Warning


###################################################################################
# Change bool value depending on the blender version
###################################################################################
def gn_bool_version(value):
    if value == 1:
        if bpy.app.version < (3, 5, 0):
            value = 1
        else:
            value = True
    else:        
        if bpy.app.version < (3, 5, 0):
            value = 0
        else:
            value = False
    return value


###################################################################################
# REMOVE SCATTER
###################################################################################
class BAGAPIE_OT_scatter_remove(Operator):
    """ Remove Bagapie Scatter modifiers """
    bl_idname = "bagapie.scatter_remove"
    bl_label = 'Remove Bagapie Scatter'
    bl_options = {'REGISTER', 'UNDO'}

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
        modifiers = val['modifiers']
        scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
        scatter_node_group = scatter_modifier.node_group
        nodes = scatter_node_group.nodes
        scatter_node_input = nodes.get("Scatter Group Input")
        scatter_node = nodes.get(modifiers[1])
        scatter_coll = scatter_node.inputs[1].default_value
        pref = Get_addon_pref()

        # GET NODES AND COUNT
        scatter_nodes = []
        effector_nodes = []
        for node in nodes:    # get statistics node
            # Get scatter paint and effector are present
            if node.label == "BagaPie_Scatter":
                scatter_nodes.append(node)
            if node.label == "BagaPie_Effector":
                effector_nodes.append(node)

        # REMOVE OBJ FROM SCATTER COLLECTION
        for ob in scatter_coll.objects:
            scatter_coll.objects.unlink(ob)
            if pref.keep_unlinked_assets_in_scene:
                if not any(coll in bpy.context.scene.collection.children_recursive for coll in ob.users_collection):
                    bpy.context.scene.collection.objects.link(ob)
        bpy.data.collections.remove(scatter_coll)

        scatter_node_position = scatter_node.location
        
        for node in scatter_nodes:    
            if node.location[0] > scatter_node_position[0]:
                node.location[0] -= 200
                node.location[1] += 250 
        for node in effector_nodes:    
            if node.location[1] < scatter_node.location[1]-800:
                node.location[0] -= 200
                node.location[1] += 250 


        # GET NODES AND COUNT
        effectors_nodes = []
        if len(scatter_node.inputs[21].links) > 0:
            links_nde = scatter_node.inputs[21].links[0].from_node
            # pos = links_nde.location[1]
            effector_count_real = 0
            while effector_count_real >= 0:
                if len(links_nde.inputs[4].links) > 0:
                    linked_nde = links_nde.inputs[4].links[0].from_node

                    # DO IT HERE
                    effectors_nodes.append(links_nde.name)
                    effector_coll = links_nde.inputs[0].default_value
                    for ob in effector_coll.objects:
                        effector_coll.objects.unlink(ob) 
                    bpy.data.collections.remove(effector_coll)
                    scatter_node_group.nodes.remove(links_nde)


                    links_nde = linked_nde
                else:
                    effectors_nodes.append(links_nde.name)
                    effector_coll = links_nde.inputs[0].default_value
                    for ob in effector_coll.objects:
                        effector_coll.objects.unlink(ob) 
                    bpy.data.collections.remove(effector_coll)
                    scatter_node_group.nodes.remove(links_nde)
                    break

        del_camera = False
        if len(scatter_nodes) == 1:
            del_camera = True
            # DELETE NODE GROUP IS NOT USED ANYMORE
            if scatter_modifier.node_group and scatter_modifier.node_group.users == 0:
                bpy.data.node_groups.remove(scatter_modifier.node_group)
            # REMOVE GEOMETRY NODES MODIFIER
            obj.modifiers.remove(scatter_modifier)
        else:
            scatter_node_group.nodes.remove(scatter_node)


        context.object.bagapieList.remove(self.index)
        

        
        # REMOVE UNUSED GROUP INPUT
        for output in scatter_node_input.outputs:
            if output.is_linked:
                pass
            else:
                for i in scatter_node_group.interface.items_tree:
                    if i.identifier == output.identifier:
                        scatter_node_group.interface.remove(i)
                        
        var = 0 # remove effector from ui list
        for idx in range(len(obj.bagapieList)):
            val = json.loads(obj.bagapieList[var]['val'])
            mo_type = val['name']
            modifiers = val['modifiers']
            if mo_type == "pointeffector":
                for no in effectors_nodes:
                    if modifiers[1] == no:
                        context.object.bagapieList.remove(var)
                        var -=1
                var += 1
            else:
                var += 1
            
        if del_camera:
            var = 0 # remove camera from ui list
            for idx in range(len(obj.bagapieList)):
                val = json.loads(obj.bagapieList[var]['val'])
                mo_type = val['name']
                modifiers = val['modifiers']
                if mo_type == "camera":
                    context.object.bagapieList.remove(var)
                    var -=1
                else:
                    var += 1

        if len(obj.bagapieList) > 0 and obj.bagapieIndex > 0:
            obj.bagapieIndex = len(obj.bagapieList)-1

        return {'FINISHED'}


###################################################################################
# ADD SCATTER
###################################################################################
class BAGAPIE_OT_scatter(Operator):
    """Scatter selected objects to the active object (last selected)"""
    bl_idname = 'wm.scatter'
    bl_label = bagapieModifiers['scatter']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )

    paint_mode: bpy.props.BoolProperty(default=False) # type: ignore
    use_proxy: bpy.props.BoolProperty(default=False) # type: ignore
    apply_scale: bpy.props.BoolProperty(default=False) # type: ignore
    use_security_features: bpy.props.BoolProperty(default=False) # type: ignore
    use_camera_culling: bpy.props.BoolProperty(default=False) # type: ignore
    count_displayed: bpy.props.IntProperty(default=100, min=0, max=100) # type: ignore
    proxy_used_anyway: bpy.props.BoolProperty(default=False) # type: ignore

    def invoke(self, context, event):
        wm = context.window_manager
        bagapie_pref = Get_addon_pref()
        target = bpy.context.active_object
        self.use_proxy = False
        self.proxy_used_anyway = False

        try:
            obj = bpy.context.selected_objects
            obj.remove(target)
        except:
            Warning(message="No surfaces selected.", title='Warning', icon='ERROR')
            return {'FINISHED'}
        
        if len(obj) == 0:
            Warning(message = "No object for scatter", title = "Warning", icon = 'INFO')
            return {'FINISHED'}

        self.count_displayed = bagapie_pref.default_percent_display
        self.use_camera_culling = bagapie_pref.use_camera_culling

        for o in obj:
            if o.type == 'MESH':
                if len(o.data.polygons) > bagapie_pref.polycount_for_proxy and bagapie_pref.use_default_proxy:
                    self.proxy_used_anyway = True
                    break
            
        bm = bmesh.new()
        bm.from_mesh(target.data)
        area = sum(f.calc_area() for f in bm.faces)
        point_count = area * 10
        dimmension = OBJ_Dimension(self,context,obj,target)
        particle_area_square = ((dimmension*1.5)*4)*((dimmension*1.5)*4)
        if particle_area_square == 0:
            particle_area_square = 1
        particles_count_square = point_count/particle_area_square
        polycount = 0
        for ob in obj:
            if ob.type == 'MESH':
                polycount += len(ob.data.polygons)
        instances_polycount_square = polycount * particles_count_square

        if instances_polycount_square > bagapie_pref.maximum_polycount or target.scale[0] != 1 or target.scale[1] != 1 or target.scale[2] != 1:
            self.use_security_features = True
            return wm.invoke_props_dialog(self)
        else:
            return self.execute(context)
    
    def draw(self, context):
        layout = self.layout
        target = bpy.context.active_object
        obj = bpy.context.selected_objects
        if len(obj)>0 and target in obj:
            obj.remove(target)
        bm = bmesh.new()
        bm.from_mesh(target.data)
        area = sum(f.calc_area() for f in bm.faces)
        point_count = area * 10
        dimmension = OBJ_Dimension(self,context,obj,target)
        particle_area_circle = 3.14*(((dimmension*1.5)*2)*((dimmension*1.5)*2))
        particle_area_square = ((dimmension*1.5)*4)*((dimmension*1.5)*4)
        if particle_area_circle == 0:
            particle_area_circle = 3.14
        if particle_area_square == 0:
            particle_area_square = 1
        particles_count_circle = point_count/particle_area_circle
        particles_count_square = point_count/particle_area_square

        if self.use_security_features:
            layout.label(text = "Performance optimization :")
            layout.label(text = "Scatter create "+ str(round(particles_count_square))+" to "+str(round(particles_count_circle))+ " instances (approximation).")

            layout.prop(self, 'use_proxy', text = "Use Proxy")
            layout.prop(self, 'count_displayed', text = "Displayed Instances in %")
            if self.proxy_used_anyway:
                layout.label(text="One or more object polycount surpasses limit in preferences")
                layout.label(text="Proxy will be auto-applied on them.")
                layout.label(text="To disable: Addon Panel > Scatter > Proxy")

            if target.modifiers.get("BagaPie_Scatter") is not None: 
                scatter_modifier = target.modifiers.get("BagaPie_Scatter")
                nodegroup = scatter_modifier.node_group
                nodes = nodegroup.nodes
                if nodes.get("BagaPie_Camera_Culling") is not None:
                    layout.prop(self, 'use_camera_culling', text = "Use Camera Culling")
                
        else:
            layout.label(text = "Scatter create  "+ str(round(particles_count_square))+" to "+str(round(particles_count_circle))+ " instances (approximation).")
        if target.scale[0] != 1 or target.scale[1] != 1 or target.scale[2] != 1:
            box = layout.box()
            box.label(text = "The scale of your target is not applied.")
            box.prop(self, 'apply_scale', text = "Apply Scale")
            box.label(text = "Affects particules count and avoid instances deformation.")

    def execute(self, context):
        bagapie_pref = Get_addon_pref()
        target = bpy.context.active_object
        obj = bpy.context.selected_objects
        obj.remove(target)
        # check if selection is correct

        go_scatter = False
        for ob in obj:
            if ob.type == 'MESH' or ob.type == 'CURVE' or ob.type == 'EMPTY':
                go_scatter = True
            else:
                obj.remove(ob)
        if not go_scatter:
            Warning(message="No selected meshes for scattering.", title='WARNING', icon='ERROR')
            return {'FINISHED'}
        else:
            # 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
            #                            IF SCATTER MODIFIER IS NOT PRESENT
            # 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
            if target.modifiers.get("BagaPie_Scatter") is None: 

                # CREATE SCATTER MODIFIER
                new = bpy.data.objects[target.name].modifiers.new
                scatter_modifier = new(name='BagaPie_Scatter', type='NODES')
                group = bpy.data.node_groups.new("Geometry Nodes", 'GeometryNodeTree')
                scatter_modifier.node_group = group
                scatter_modifier.node_group.name = "BagaPie_Scatter_Main"
                nodegroup = scatter_modifier.node_group
                
                nodes = nodegroup.nodes
                scatter_nodes = []
                scatt_nde_inp = nodes.new(type='NodeGroupInput')
                scatt_nde_out = nodes.new(type='NodeGroupOutput')
                scatt_nde_inp.name = "Scatter Group Input"
                scatt_nde_out.name = "Scatter Group Output"
                scatt_nde_inp.label = "Scatter Group Input"
                scatt_nde_out.label = "Scatter Group Output"

                scatt_nde_join = nodes.new(type='GeometryNodeJoinGeometry')
                scatt_nde_join.name = "Join Layer"
                scatt_nde_join.label = "0"

                # Create Geometry Inputs and Outputs
                create_socket(nodegroup, 'INPUT', 'Geometry', "NodeSocketGeometry")
                create_socket(nodegroup, 'OUTPUT', 'Geometry', "NodeSocketGeometry")

                is_new = True
                    
            # 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
            #                            IF SCATTER MODIFIER IS PRESENT
            # 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
            else:
                scatter_modifier = target.modifiers.get("BagaPie_Scatter")
                nodegroup = scatter_modifier.node_group
                nodes = nodegroup.nodes
                scatter_nodes = []
                for node in nodes:
                    if node.label == 'BagaPie_Scatter':
                        scatter_nodes.append(node)
                scatt_nde_inp = nodes.get("Scatter Group Input")
                scatt_nde_out = nodes.get("Scatter Group Output")
                scatt_nde_join = nodes.get("Join Layer")

                is_new = False

            # 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
            #                            IF SCATTER NODE IS NOT PRESENT
            # 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
            
            # COLLECTION
            scatt_coll = Collection_Setup(self,context,target)
            for ob in obj: # Add to scatter collection
                scatt_coll.objects.link(ob)

                if self.use_proxy and ob.type == 'MESH':
                    Add_ProxyOnMesh(self,context,ob)
                    print("Proxy : Forced")
                elif ob.type == 'MESH':
                    polycount = len(ob.data.polygons)
                    if polycount > bagapie_pref.polycount_for_proxy:
                        Add_ProxyOnMesh(self,context,ob)
                        print("Proxy : Poly limit reached")

            # Apply Target Scale
            if self.apply_scale:
                target.select_set(True)
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

            # Get instance dimensions and scale
            scale = OBJ_Scale(self,context,obj,target)
            dimmension = OBJ_Dimension(self,context,obj,target)
            if dimmension == 0:
                dimmension = 1
            # use_bagapie_assets = BagaPie_Assets_Check(self,context,obj)

            # ADD NODES
            Import_Nodes(self,context,"BagaPie_Scatter")
            scatter_node = nodes.new(type='GeometryNodeGroup')
            scatter_node.node_tree = bpy.data.node_groups['BagaPie_Scatter']
            scatter_node.name = "BagaPie_Scatter"
            scatter_node.label = "BagaPie_Scatter"

            # POSITION NODES
            if is_new:
                scatt_nde_inp.location = (0, 0)
                scatter_node.location = (200,0)
                scatt_nde_join.location = (400,0)
                scatt_nde_out.location = (600, 0)
            else:
                scatter_node.location = (200+200*len(scatter_nodes),-250*len(scatter_nodes))
                scatt_nde_join.location = (400+200*len(scatter_nodes), 0)
                scatt_nde_out.location = (600+200*len(scatter_nodes), 0)

            # CONFIGURATION NODES
            scatter_node.inputs[1].default_value = scatt_coll
            scatter_node.inputs[6].default_value = randint(0,10000)
            if self.paint_mode:
                scatter_node.inputs[2].default_value = dimmension*0.6
            else:
                scatter_node.inputs[2].default_value = dimmension*0.8
            # if use_bagapie_assets:
            scatter_node.inputs[3].default_value = 10
            if self.use_security_features:
                scatter_node.inputs[4].default_value = self.count_displayed
            scatter_node.inputs[5].default_value = 1
            scatter_node.inputs[13].default_value[2] = -100
            scatter_node.inputs[14].default_value[2] = 100
            scatter_node.inputs[9].default_value = scale*0.8
            scatter_node.inputs[10].default_value = scale*1.2

            # LINK NODES
            new_link = nodegroup.links
            # Geometry path
            if is_new:
                new_link.new(scatt_nde_inp.outputs[0], scatt_nde_join.inputs[0])
                new_link.new(scatt_nde_join.outputs[0], scatt_nde_out.inputs[0])
            
            new_link.new(scatt_nde_inp.outputs[0], scatter_node.inputs[0])
            new_link.new(scatter_node.outputs[0], scatt_nde_join.inputs[0])

            # UI MODIFIER SETUP VERTEX GROUP
            scatter_node_count_real = int(scatt_nde_join.label)
            nodegroup.interface.new_socket(socket_type="NodeSocketFloat", name="Vertex Group", in_out='INPUT')
            scatt_vertex_grp = target.vertex_groups.new(name="BagaVertGrp")
            new_link.new(scatt_nde_inp.outputs[len(scatter_nodes)+1], scatter_node.inputs[25])
            bpy.ops.object.geometry_nodes_input_attribute_toggle(input_name="Socket_{}".format(str(scatter_node_count_real+2)), modifier_name="BagaPie_Scatter")
            
            scatter_modifier["Socket_{}_attribute_name".format(str(scatter_node_count_real+2))] = scatt_vertex_grp.name
            scatt_nde_join.label = str(int(scatt_nde_join.label)+1)

            if self.paint_mode:
                scatter_node.inputs[26].default_value = True
                bpy.ops.paint.weight_paint_toggle()
                bpy.context.tool_settings.weight_paint.brush.blend = 'MIX'
                if bpy.app.version >= (5, 0, 0):
                    bpy.context.tool_settings.weight_paint.brush.curve_distance_falloff_preset = 'CONSTANT'
                else:
                    bpy.context.tool_settings.weight_paint.brush.curve_preset = 'CONSTANT'

            # CUSTOM PROPERTY
            val = {
                'name': 'scatter',
                'modifiers':[
                            scatter_modifier.name,  # MODIFIER NAME
                            scatter_node.name,
                            scatt_vertex_grp.name,
                            "Scatter",  # LAYER NAME
                            ]
            }
            item = target.bagapieList.add()
            item.val = json.dumps(val)
            
            target.bagapieIndex = len(target.bagapieList)-1

            
            val = json.loads(target.bagapieList[target.bagapieIndex]['val'])
            modifiers = val['modifiers']
            if target.modifiers[modifiers[0]].node_group.nodes.get('BagaPie_Camera_Culling') and self.use_camera_culling and self.use_security_features:
                bpy.ops.use.cameracullingonlayer()

            return {'FINISHED'}


###################################################################################
# CREATE GEOMETRY SOCKET
###################################################################################
def create_socket(nodegroup, socket_input, name, socket_type):
    if not any(item.in_out == socket_input for item in nodegroup.interface.items_tree):
        nodegroup.interface.new_socket(socket_type=socket_type, name=name, in_out=socket_input)


###################################################################################
# GET OBJECTS SCALE
###################################################################################
def OBJ_Scale(self,context,obj,target):
    instances_visual_scale = 0
    for ob in obj:
        instances_visual_scale += ob.scale[0]
        instances_visual_scale += ob.scale[1]
        instances_visual_scale += ob.scale[2]
    instances_visual_scale = instances_visual_scale/(len(obj)*3)

    target_scale = (target.scale[0] + target.scale[0] + target.scale[0])/3
    
    scale = instances_visual_scale / target_scale
    
    return scale
    

###################################################################################
# GET OBJECTS DIMMENSION
###################################################################################
def OBJ_Dimension(self,context,obj,target):
    instances_max_dimensions = 0
    inc_dim = 1
    target_scale = 1
    for ob in obj:  # Get instance max dimensions
        if ob.dimensions.x > instances_max_dimensions:
            instances_max_dimensions = ob.dimensions.x
            if ob.dimensions.x < ob.dimensions.y:
                instances_max_dimensions = ob.dimensions.y
        if ob.name.startswith("BagaPie_Grass"):
            inc_dim = 0.5

    target_scale = (target.scale[0] + target.scale[0] + target.scale[0])/3
    try:
        dimmension = ((instances_max_dimensions / target_scale)*0.65)*inc_dim #0.8 because it looks good
    except:
        Warning(message = "Scattered object can be empty or procedural", title = "Wrong Selection", icon = 'INFO')
        return {'FINISHED'}

    return dimmension


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
        scatt_coll = bpy.data.collections.new("BagaPie_Scatter_" + target.name)
        scatter_master_coll.children.link(scatt_coll)
    # If the main collection Bagapie already exist
    elif bpy.data.collections.get("BagaPie_Scatter") is None:
        main_coll = bpy.data.collections["BagaPie"]
        scatter_master_coll = bpy.data.collections.new("BagaPie_Scatter")
        main_coll.children.link(scatter_master_coll)
        scatt_coll = bpy.data.collections.new("BagaPie_Scatter_" + target.name)
        scatter_master_coll.children.link(scatt_coll)
    # If the main collection Bagapie_Scatter already exist
    else:
        scatt_coll = bpy.data.collections.new("BagaPie_Scatter_" + target.name)
        scatter_master_coll = bpy.data.collections["BagaPie_Scatter"]
        scatter_master_coll.children.link(scatt_coll)

    return scatt_coll


###################################################################################
# USE PROXY
###################################################################################
class UseProperty(Operator):
    """Enable/Disable Library"""
    bl_idname = "use.property"
    bl_label = "Use Property"

    property: bpy.props.StringProperty(default="None") # type: ignore

    def execute(self, context):
        target = bpy.context.active_object
        
        if target[self.property] == gn_bool_version(0):
            target[self.property] = gn_bool_version(1)
        else :
            target[self.property] = gn_bool_version(0)

        return {'FINISHED'}


###################################################################################
# ADD NODEGROUP TO THE MODIFIER  ONLY FOR PROXY
###################################################################################
def Add_NodeGroup(self,context,modifier, nodegroup_name):
    try:
        modifier.node_group = bpy.data.node_groups[nodegroup_name]
    except:
        Import_Nodes(self,context,nodegroup_name)
        modifier.node_group = bpy.data.node_groups[nodegroup_name]


###################################################################################
# ADD PROXY MODIFIER ON MESH
###################################################################################
def Add_ProxyOnMesh(self,context,ob):

    var = 0
    proxy_exist = False
    for idx in range(len(ob.bagapieList)):
        val = json.loads(ob.bagapieList[var]['val'])
        mo_type = val['name']
        if mo_type == "proxy":
            proxy_exist = True
        else:
            var += 1

    if not proxy_exist:
        new = bpy.data.objects[ob.name].modifiers.new
        proxynodegroup = "BagaPie_Proxy" # GROUP NAME
        modifier = new(name=proxynodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, proxynodegroup)
        ob.modifiers[proxynodegroup].show_render = False
        mat_proxy = bpy.data.materials.new(name="BagaPie_Proxy")
        mat_proxy.diffuse_color = (random(), random(), random(), 1)  
        modifier["Input_6"] = mat_proxy
        val = {
            'name': 'proxy', # MODIFIER TYPE
            'modifiers':[
            proxynodegroup, #Modifier Name
            ]
        }
        item = ob.bagapieList.add()
        item.val = json.dumps(val)

    else:
        var = 0 # remove effector from ui list
        for idx in range(len(ob.bagapieList)):
            val = json.loads(ob.bagapieList[var]['val'])
            mo_type = val['name']
            modifiers = val['modifiers']
            if mo_type == "proxy":
                
                modifier = ob.modifiers[modifiers[0]]
                modifier.show_viewport = True
                break
            else:
                var += 1


###################################################################################
# ENABLE/DISABLE PROXY FOR ALL LAYER
###################################################################################
class Use_Proxy_On_Assets(Operator):
    """Enable/Disable Proxy in collection"""
    bl_idname = "use.proxyonassets"
    bl_label = "Use Proxy On Assets"

    use_proxy: bpy.props.BoolProperty(default=True) # type: ignore

    def execute(self, context):
        target = bpy.context.active_object
        
        val = json.loads(target.bagapieList[target.bagapieIndex]['val'])
        modifiers = val['modifiers']
        scatter_modifier = target.modifiers.get("BagaPie_Scatter")
        scatter_node_group = scatter_modifier.node_group
        nodes = scatter_node_group.nodes
        scatter_node = nodes.get(modifiers[1])
        scatter_coll = scatter_node.inputs[1].default_value
        
        for ob in scatter_coll.objects:
            if self.use_proxy:
                Add_ProxyOnMesh(self,context,ob)
            else:
                var = 0
                for idx in range(len(ob.bagapieList)):
                    val = json.loads(ob.bagapieList[var]['val'])
                    mo_type = val['name']
                    modifiers = val['modifiers']
                    if mo_type == "proxy":
                        
                        modifier = ob.modifiers[modifiers[0]]
                        modifier.show_viewport = False
                        break
                    else:
                        var += 1

        return {'FINISHED'}
        
        
###################################################################################
# ENABLE CAMERA CULLING IF NODE IS PRESENT
###################################################################################
class Use_Camera_Culling_On_Layer(Operator):
    """Enable/Disable/Add Camera Culling"""
    bl_idname = "use.cameracullingonlayer"
    bl_label = "Use Camera Culling"

    index: bpy.props.IntProperty(default=0) # type: ignore
    from_list: bpy.props.BoolProperty(default=False) # type: ignore

    def execute(self, context):
        target = bpy.context.active_object
        
        if self.from_list == True:
            val = json.loads(target.bagapieList[self.index]['val'])
        else:
            val = json.loads(target.bagapieList[target.bagapieIndex]['val'])
        
        modifiers = val['modifiers']
        scatter_modifier = target.modifiers.get("BagaPie_Scatter")
        scatter_node_group = scatter_modifier.node_group
        nodes = scatter_node_group.nodes
        scatter_node = nodes.get(modifiers[1])
        scatter_links = scatter_node.inputs[24].links

        if len(scatter_links) > 0:
            scatter_modifier.node_group.links.remove(scatter_node.inputs[24].links[0])
            scatter_node_seed = scatter_node.inputs[6].default_value
            scatter_node.inputs[6].default_value = scatter_node_seed+1
            scatter_node.inputs[6].default_value = scatter_node_seed-1
        else:
        
            var = 0
            for idx in range(len(target.bagapieList)):
                val = json.loads(target.bagapieList[var]['val'])
                mo_type = val['name']
                modifiers = val['modifiers']
                if mo_type == "camera":
                    
                    new_link = scatter_node_group.links
                    cam_node = nodes.get('BagaPie_Camera_Culling')
                    new_link.new(cam_node.outputs[0], scatter_node.inputs[24])
                    break
                else:
                    var += 1

        return {'FINISHED'}
        
        
###################################################################################
# APPLY MODIFIER SCATTER
###################################################################################
class Apply_Scatter_OP(Operator):
    """Apply Scatter Modifier"""
    bl_idname = "use.applyscatter"
    bl_label = "Apply Scatter"
    bl_options = {'REGISTER', 'UNDO'}

    release: bpy.props.BoolProperty(default=True) # type: ignore
    index: bpy.props.IntProperty(default=0) # type: ignore

    @classmethod
    def poll(cls, context):
        return (
            bpy.context.mode == 'OBJECT'
        )

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text = "All scatter layers will be converted.")
        row = col.row(align=True)
        if self.release:
            row.prop(self, 'release', text = "Convert To Mesh", emboss = True, icon = "OUTLINER_OB_MESH", invert_checkbox = self.release)
            row.prop(self, 'release', text = "Make Instances Real", emboss = True, icon = "OBJECT_DATA", invert_checkbox = not self.release)
            col.label(text = "Recommended option.")
            col.label(text = "All scatter layers will be applied.")
            col.label(text = "Instances will be converted into objects.")

        else:
            row.prop(self, 'release', text = "Convert To Mesh", emboss = True, icon = "OUTLINER_OB_MESH", invert_checkbox = not self.release)
            row.prop(self, 'release', text = "Make Instances Real", emboss = True, icon = "OBJECT_DATA", invert_checkbox = self.release)
            col.label(text = "All scatter layers will be applied.")
            col.label(text = "All instances will be merged into a single mesh.")
            col.label(text = "Warning :", icon = "ERROR")
            col.label(text = "Convert to mesh turn UVs to Attribute.")
            col.label(text = "You can restore UVs in the attribute panel :")
            col.label(text = "Object Data Properties > Attributes")
            col.label(text = "Also, pay attention to the polycount.")

    def execute(self, context):
        target = bpy.context.active_object
        val = json.loads(target.bagapieList[target.bagapieIndex]['val'])
        modifiers = val['modifiers']
        modifier = target.modifiers[modifiers[0]]

        # REALIZE INSTANCES
        if not self.release:
            scatter_node_group = modifier.node_group
            nodes = scatter_node_group.nodes
            scatter_node_output = nodes.get("Scatter Group Output")
            scatt_nde_join = nodes.get("Join Layer")
            link = scatt_nde_join.outputs[0].links[0]
            scatter_node_group.links.remove(link)
            scatt_nde_ri = nodes.new(type='GeometryNodeRealizeInstances')

            # LINK NODES
            new_link = scatter_node_group.links
            new_link.new(scatt_nde_join.outputs[0], scatt_nde_ri.inputs[0])
            new_link.new(scatt_nde_ri.outputs[0], scatter_node_output.inputs[0])
            
        # COLLECTION MANAGMENT AND CUSTOM PROPERTY
        obj = context.object
        val = json.loads(obj.bagapieList[self.index]['val'])
        modifiers = val['modifiers']
        scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
        scatter_node_group = scatter_modifier.node_group
        nodes = scatter_node_group.nodes

        # GET NODES AND COUNT
        scatter_nodes = []
        effector_nodes = []
        camera_nodes = []
        for node in nodes:    # get statistics node
            # Get scatter paint and effector are present
            if node.label == "BagaPie_Scatter":
                scatter_nodes.append(node)
            if node.label == "BagaPie_Effector":
                effector_nodes.append(node)
            if node.label == "BagaPie_Camera_Culling":
                camera_nodes.append(node)

        # SCATTER
        idx = 0
        for id in range(len(obj.bagapieList)):
            val = json.loads(obj.bagapieList[idx]['val'])
            mo_type = val['name']
            modifiers = val['modifiers']
            if mo_type == "scatter":
                context.object.bagapieList.remove(idx)
            else:
                idx += 1
                        
        # EFFECTOR
        idx = 0
        for id in range(len(obj.bagapieList)):
            val = json.loads(obj.bagapieList[idx]['val'])
            mo_type = val['name']
            modifiers = val['modifiers']
            if mo_type == "pointeffector":
                context.object.bagapieList.remove(idx)
            else:
                idx += 1
            
        # CAMERA
        idx = 0
        for id in range(len(obj.bagapieList)):
            val = json.loads(obj.bagapieList[idx]['val'])
            mo_type = val['name']
            modifiers = val['modifiers']
            if mo_type == "camera":
                context.object.bagapieList.remove(idx)
            else:
                idx += 1

        # REALIZE INSTANCES
        if not self.release:
            # APPLY MODIFIER
            bpy.ops.object.modifier_apply(modifier=modifier.name)

        # MAKE INSTANCES REAL
        else: 
            bpy.ops.object.duplicates_make_real()
            obj.modifiers.remove(scatter_modifier)


        # REMOVE OBJ FROM COLLECTIONS
        # SCATTER
        for node in scatter_nodes:
            scatter_coll = node.inputs[1].default_value
            for ob in scatter_coll.objects:
                scatter_coll.objects.unlink(ob) 
            bpy.data.collections.remove(scatter_coll)
        # EFFECTOR
        for node in effector_nodes:
            effector_coll = node.inputs[0].default_value
            for ob in effector_coll.objects:
                effector_coll.objects.unlink(ob) 
            bpy.data.collections.remove(effector_coll)
        
        return {'FINISHED'}


classes = [
    BAGAPIE_OT_scatter_remove,
    BAGAPIE_OT_scatter,
    UseProperty,
    Use_Proxy_On_Assets,
    Use_Camera_Culling_On_Layer,
    Apply_Scatter_OP,
]