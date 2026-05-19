import bpy
from ..utils import ShaderNode


class ShaderNodeParallaxClosure(ShaderNode):
    bl_label = "Parallax: Closure"
    bl_icon = "NONE"

    # Constants
    VECT_TRANS_FIX_NAME = ".VectTransFix"
    TEST_PREFIX = "."



    # UV layer selector
    uv_map: bpy.props.StringProperty(
        name="UV Map",
        description="UV layer to use for parallax mapping",
        default="",
        update=lambda self, context: self.valuesUpdate(context),
    )#type: ignore


    def init(self, context):
        self.getNodetree(self.name + "_node_tree")
        self.inputs["Iterations"].default_value = 25
        self.inputs["Depth"].default_value = 2
        self.inputs["Bias"].default_value = 0.5
        self.inputs["Texture Offset"].default_value = (0.0, 0.0)
        self.inputs["Texture Scale"].default_value = (1.0, 1.0)

    def draw_buttons(self, context, layout):
        # Call parent draw_buttons first
        super().draw_buttons(context, layout)

        # Add image selector using template_ID
        #layout.template_ID(self, "elevation_image", open="image.open")

        # Add UV layer selector
        if context.active_object and context.active_object.data and hasattr(context.active_object.data, 'uv_layers'):
            layout.prop_search(
                self, "uv_map", context.active_object.data, "uv_layers", text="UV Map")
        else:
            layout.prop(self, "uv_map", text="UV Map")

        # Add iterations slider
        
        #layout.prop(self, "iterations", text="Steps")
        #layout.prop(self, "stength", text="Strength")
        #layout.prop(self, "bias", text="Bias")

    # Create nodetrees
    def getMapFix(self):

        if self.VECT_TRANS_FIX_NAME in bpy.data.node_groups:
            return bpy.data.node_groups[self.VECT_TRANS_FIX_NAME]

        nt = bpy.data.node_groups.new(self.VECT_TRANS_FIX_NAME, "ShaderNodeTree")
        nt.color_tag = "VECTOR"
        nt.description = "Parallax mapping effect using height map"

        _2_vec_socket = nt.interface.new_socket(
            name="Result", in_out="OUTPUT", socket_type="NodeSocketVector"
        )
        _2_vec_socket.default_value = (0.0, 0.0, 0.0)
        _2_vec_socket.min_value = -3.4028234663852886e38
        _2_vec_socket.max_value = 3.4028234663852886e38
        _2_vec_socket.subtype = "NONE"
        _2_vec_socket.attribute_domain = "POINT"

        # Output socket
        _v_vec_socket = nt.interface.new_socket(
            name="Vector", in_out="INPUT", socket_type="NodeSocketVector"
        )
        _v_vec_socket.default_value = (0.0, 0.0, 0.0)
        _v_vec_socket.min_value = -3.4028234663852886e38
        _v_vec_socket.max_value = 3.4028234663852886e38
        _v_vec_socket.subtype = "NONE"
        _v_vec_socket.attribute_domain = "POINT"

        CombineXYZ_001 = nt.nodes.new("ShaderNodeCombineXYZ")
        CombineXYZ_001.location = (387, -8)

        Geometry_002 = nt.nodes.new("ShaderNodeNewGeometry")
        Geometry_002.location = (-417, 351)

        GroupInput = nt.nodes.new("NodeGroupInput")
        GroupInput.location = (-417, -92)

        GroupOutput = nt.nodes.new("NodeGroupOutput")
        GroupOutput.location = (793, -34)

        Math_006 = nt.nodes.new("ShaderNodeMath")
        Math_006.location = (384, 368)
        Math_006.operation = "LESS_THAN"

        Math_007 = nt.nodes.new("ShaderNodeMath")
        Math_007.location = (178, 89)
        Math_007.operation = "MULTIPLY"

        Mix = nt.nodes.new("ShaderNodeMix")
        Mix.location = (603, -34)
        Mix.data_type = "VECTOR"

        Reroute = nt.nodes.new("NodeReroute")
        Reroute.location = (-22, -214)

        Reroute_001 = nt.nodes.new("NodeReroute")
        Reroute_001.location = (178, -110)

        Reroute_002 = nt.nodes.new("NodeReroute")
        Reroute_002.location = (178, -87)

        SeparateXYZ = nt.nodes.new("ShaderNodeSeparateXYZ")
        SeparateXYZ.location = (178, 351)

        SeparateXYZ_001 = nt.nodes.new("ShaderNodeSeparateXYZ")
        SeparateXYZ_001.location = (-22, -8)

        VectorMath_008 = nt.nodes.new("ShaderNodeVectorMath")
        VectorMath_008.location = (-220, 351)
        VectorMath_008.operation = "SCALE"

        VectorTransform = nt.nodes.new("ShaderNodeVectorTransform")
        VectorTransform.location = (-220, -92)

        VectorTransform_003 = nt.nodes.new("ShaderNodeVectorTransform")
        VectorTransform_003.location = (-22, 351)

        nt.links.new(VectorMath_008.outputs[0],
                     VectorTransform_003.inputs["Vector"])
        nt.links.new(
            VectorTransform_003.outputs["Vector"], SeparateXYZ.inputs["Vector"])
        nt.links.new(Math_006.outputs[0], Mix.inputs["Factor"])
        nt.links.new(SeparateXYZ.outputs["X"], Math_006.inputs[0])
        nt.links.new(CombineXYZ_001.outputs["Vector"], Mix.inputs["A"])
        nt.links.new(SeparateXYZ.outputs["Z"], Math_006.inputs[1])
        nt.links.new(Math_007.outputs[0], CombineXYZ_001.inputs["X"])
        nt.links.new(Mix.outputs["Result"], GroupOutput.inputs["Result"])
        nt.links.new(
            Geometry_002.outputs["Incoming"], VectorMath_008.inputs[0])
        nt.links.new(
            VectorTransform.outputs["Vector"], SeparateXYZ_001.inputs["Vector"])
        nt.links.new(SeparateXYZ_001.outputs["Y"], Math_007.inputs[0])
        nt.links.new(GroupInput.outputs["Vector"],
                     VectorTransform.inputs["Vector"])
        nt.links.new(
            VectorTransform.outputs["Vector"], Reroute.inputs["Input"])
        nt.links.new(Reroute.outputs["Output"], Mix.inputs["B"])
        nt.links.new(SeparateXYZ_001.outputs["X"], Reroute_001.inputs["Input"])
        nt.links.new(Reroute_001.outputs["Output"], CombineXYZ_001.inputs["Z"])
        nt.links.new(SeparateXYZ_001.outputs["Z"], Reroute_002.inputs["Input"])
        nt.links.new(Reroute_002.outputs["Output"], CombineXYZ_001.inputs["Y"])

        for node in nt.nodes:
            if node.type == 'VECT_TRANSFORM':
                node.convert_to = "CAMERA"

        VectorMath_008.inputs['Scale'].default_value = -1
        Math_007.inputs[1].default_value = -1

        return nt

    def createNodetree(self, name):
        nt = self.node_tree = bpy.data.node_groups.new(self.TEST_PREFIX+name, "ShaderNodeTree")
        nt.color_tag = "VECTOR"
        nt.description = "Parallax mapping effect using height map"

        # Output socket
        _2_vec_socket = nt.interface.new_socket(
            name="Vector", in_out="OUTPUT", socket_type="NodeSocketVector"
        )
        _2_vec_socket.default_value = (0.0, 0.0, 0.0)
        _2_vec_socket.min_value = -3.4028234663852886e38
        _2_vec_socket.max_value = 3.4028234663852886e38
        _2_vec_socket.subtype = "NONE"
        _2_vec_socket.attribute_domain = "POINT"

        # input socket
        Closure_socket = nt.interface.new_socket(
            name="Height Texture", in_out="INPUT", socket_type="NodeSocketClosure"
        )


        Iterations_socket = nt.interface.new_socket(
            name="Iterations", in_out="INPUT", socket_type="NodeSocketInt"
        )
        Iterations_socket.default_value = 25
        Iterations_socket.min_value = 1
        Iterations_socket.max_value = 1000
        Iterations_socket.subtype = "NONE"
        Iterations_socket.attribute_domain = "POINT"

        # 
        Depth_socket = nt.interface.new_socket(
            name="Depth", in_out="INPUT", socket_type="NodeSocketFloat"
        )
        Depth_socket.default_value = 2
        Depth_socket.min_value = 0
        Depth_socket.max_value = 1000
        Depth_socket.subtype = "NONE"
        Depth_socket.attribute_domain = "POINT"

        Bias_socket = nt.interface.new_socket(
            name="Bias", in_out="INPUT", socket_type="NodeSocketFloat"
        )
        Bias_socket.default_value = 0.5
        Bias_socket.min_value = -1
        Bias_socket.max_value = 1
        Bias_socket.subtype = "NONE"
        Bias_socket.attribute_domain = "POINT"

        _tc_socket = nt.interface.new_socket(
            name="Texture Offset", in_out="INPUT", socket_type="NodeSocketVector",
        )
        _tc_socket.dimensions = 2
        _tc_socket.default_value = (0.0, 0.0, 0.0)
        _tc_socket.min_value = -3.4028234663852886e38
        _tc_socket.max_value = 3.4028234663852886e38
        _tc_socket.subtype = "NONE"
        _tc_socket.attribute_domain = "POINT"
        

        _tv_socket = nt.interface.new_socket(
            name="Texture Scale", in_out="INPUT", socket_type="NodeSocketVector"
        )
        _tv_socket.dimensions = 2
        _tv_socket.default_value = (1.0, 1.0, 1.0)
        _tv_socket.min_value = -3.4028234663852886e38
        _tv_socket.max_value = 3.4028234663852886e38
        _tv_socket.subtype = "NONE"
        _tv_socket.attribute_domain = "POINT"       
        


        self.rebuildNodetree(None)
        self.valuesUpdate(None)

    def rebuildNodetree(self, context):
        if context!=None:
            if self.node_tree.users > 1:
                self.duplicate()

        nt = self.node_tree

        for node in nt.nodes:
            nt.nodes.remove(node)

        VectTransFixNG = self.getMapFix()

        # Create nodes

        CombineXYZ = nt.nodes.new("ShaderNodeCombineXYZ")
        CombineXYZ.location = (-637, -172)
        
        EvaluateClosure = nt.nodes.new("NodeEvaluateClosure")
        EvaluateClosure.location = (0, 0)
        
        Geometry = nt.nodes.new("ShaderNodeNewGeometry")
        Geometry.location = (-1695, -133)
        
        Geometry_001 = nt.nodes.new("ShaderNodeNewGeometry")
        Geometry_001.location = (-1451, -405)
        
        GroupInput = nt.nodes.new("NodeGroupInput")
        GroupInput.location = (-708, -560)
        
        GroupInput_001 = nt.nodes.new("NodeGroupInput")
        GroupInput_001.location = (-826, 264)
        
        GroupOutput = nt.nodes.new("NodeGroupOutput")
        GroupOutput.location = (1237, -111)
        
        Mapping = nt.nodes.new("ShaderNodeMapping")
        Mapping.location = (-610, 348)
        
        Math = nt.nodes.new("ShaderNodeMath")
        Math.location = (232, -109)
        Math.operation = "MULTIPLY"
        
        Math_001 = nt.nodes.new("ShaderNodeMath")
        Math_001.location = (407, -109)
        Math_001.operation = "ADD"
        
        Math_002 = nt.nodes.new("ShaderNodeMath")
        Math_002.location = (-150, -370)
        Math_002.operation = "MULTIPLY"
        
        Math_003 = nt.nodes.new("ShaderNodeMath")
        Math_003.location = (21, -372)
        Math_003.operation = "MULTIPLY"
        
        Math_004 = nt.nodes.new("ShaderNodeMath")
        Math_004.location = (21, -524)
        Math_004.operation = "MULTIPLY"
        
        Math_005 = nt.nodes.new("ShaderNodeMath")
        Math_005.location = (-320, -368)
        Math_005.operation = "DIVIDE"
        
        RepeatInput = nt.nodes.new("GeometryNodeRepeatInput")
        RepeatInput.location = (-311, -71)
        
        RepeatOutput = nt.nodes.new("GeometryNodeRepeatOutput")
        RepeatOutput.location = (1013, -80)
        #
        RepeatInput.pair_with_output(RepeatOutput)
        RepeatOutput.repeat_items.new('VECTOR','Vector')
        #
        
        Reroute = nt.nodes.new("NodeReroute")
        Reroute.location = (-932, 87)
        
        Reroute_001 = nt.nodes.new("NodeReroute")
        Reroute_001.location = (-1266, -376)
        
        Reroute_002 = nt.nodes.new("NodeReroute")
        Reroute_002.location = (-54, -51)
        
        Reroute_003 = nt.nodes.new("NodeReroute")
        Reroute_003.location = (700, -51)
        
        Reroute_004 = nt.nodes.new("NodeReroute")
        Reroute_004.location = (-42, -362)
        
        Tangent = nt.nodes.new("ShaderNodeTangent")
        Tangent.location = (-1695, 75)
        
        UVMap = nt.nodes.new("ShaderNodeUVMap")
        UVMap.location = (-828, 381)
        
        VectTransFix = nt.nodes.new("ShaderNodeGroup")
        VectTransFix.location = (-1086, -423)
        VectTransFix.node_tree = VectTransFixNG
        
        VectTransFix_001 = nt.nodes.new("ShaderNodeGroup")
        VectTransFix_001.location = (-1496, 121)
        VectTransFix_001.node_tree = VectTransFixNG
        
        VectTransFix_002 = nt.nodes.new("ShaderNodeGroup")
        VectTransFix_002.location = (-1499, -126)
        VectTransFix_002.node_tree = VectTransFixNG
        
        VectorMath = nt.nodes.new("ShaderNodeVectorMath")
        VectorMath.location = (-848, 44)
        VectorMath.operation = "DOT_PRODUCT"
        
        VectorMath_001 = nt.nodes.new("ShaderNodeVectorMath")
        VectorMath_001.location = (-848, -124)
        VectorMath_001.operation = "DOT_PRODUCT"
        
        VectorMath_002 = nt.nodes.new("ShaderNodeVectorMath")
        VectorMath_002.location = (-848, -293)
        VectorMath_002.operation = "DOT_PRODUCT"
        
        VectorMath_003 = nt.nodes.new("ShaderNodeVectorMath")
        VectorMath_003.location = (-1266, 25)
        VectorMath_003.operation = "CROSS_PRODUCT"
        
        VectorMath_004 = nt.nodes.new("ShaderNodeVectorMath")
        VectorMath_004.location = (-1072, 25)
        VectorMath_004.operation = "NORMALIZE"
        
        VectorMath_005 = nt.nodes.new("ShaderNodeVectorMath")
        VectorMath_005.location = (614, -265)
        VectorMath_005.operation = "MULTIPLY"
        
        VectorMath_006 = nt.nodes.new("ShaderNodeVectorMath")
        VectorMath_006.location = (795, -236)
        VectorMath_006.operation = "ADD"
        
        VectorMath_007 = nt.nodes.new("ShaderNodeVectorMath")
        VectorMath_007.location = (-1269, -414)
        VectorMath_007.operation = "SCALE"
        
        nt.links.new(VectorMath_004.outputs[0], VectorMath_001.inputs[0])
        nt.links.new(VectorMath_003.outputs[0], VectorMath_004.inputs[0])
        nt.links.new(VectorMath.outputs[1], CombineXYZ.inputs["X"])
        nt.links.new(VectorMath_001.outputs[1], CombineXYZ.inputs["Y"])
        nt.links.new(VectorMath_002.outputs[1], CombineXYZ.inputs["Z"])
        nt.links.new(Reroute.outputs["Output"], VectorMath.inputs[0])
        nt.links.new(Reroute_001.outputs["Output"], VectorMath_002.inputs[0])
        nt.links.new(RepeatOutput.outputs["Vector"], GroupOutput.inputs["Vector"])
        nt.links.new(GroupInput.outputs["Iterations"], RepeatInput.inputs["Iterations"])
        nt.links.new(VectorMath_005.outputs[0], VectorMath_006.inputs[0])
        nt.links.new(Math_001.outputs[0], VectorMath_005.inputs[0])
        nt.links.new(Math.outputs[0], Math_001.inputs[0])
        nt.links.new(Reroute_002.outputs["Output"], Reroute_003.inputs["Input"])
        nt.links.new(Reroute_003.outputs["Output"], VectorMath_006.inputs[1])
        nt.links.new(Reroute_004.outputs["Output"], VectorMath_005.inputs[1])
        nt.links.new(Math_002.outputs[0], Math_003.inputs[0])
        nt.links.new(Math_003.outputs[0], Math.inputs[1])
        nt.links.new(RepeatInput.outputs["Vector"], Reroute_002.inputs["Input"])
        nt.links.new(CombineXYZ.outputs["Vector"], Reroute_004.inputs["Input"])
        nt.links.new(Math_005.outputs[0], Math_002.inputs[0])
        nt.links.new(VectorMath_006.outputs[0], RepeatOutput.inputs["Vector"])
        nt.links.new(Math_002.outputs[0], Math_004.inputs[0])
        nt.links.new(Math_004.outputs[0], Math_001.inputs[1])
        nt.links.new(GroupInput.outputs["Bias"], Math_004.inputs[1])
        nt.links.new(GroupInput.outputs["Depth"], Math_005.inputs[0])
        nt.links.new(GroupInput.outputs["Iterations"], Math_005.inputs[1])
        nt.links.new(Mapping.outputs["Vector"], RepeatInput.inputs["Vector"])
        nt.links.new(UVMap.outputs["UV"], Mapping.inputs["Vector"])
        nt.links.new(GroupInput_001.outputs["Texture Offset"], Mapping.inputs["Location"])
        nt.links.new(GroupInput_001.outputs["Texture Scale"], Mapping.inputs["Scale"])

        nt.links.new(VectorMath_007.outputs[0], VectTransFix.inputs["Vector"])
        nt.links.new(VectTransFix.outputs["Result"], VectorMath_002.inputs[1])
        nt.links.new(VectTransFix.outputs["Result"], VectorMath_001.inputs[1])
        nt.links.new(VectTransFix.outputs["Result"], VectorMath.inputs[1])
        nt.links.new(Geometry_001.outputs["Incoming"], VectorMath_007.inputs[0])
        nt.links.new(Tangent.outputs["Tangent"], VectTransFix_001.inputs["Vector"])
        nt.links.new(VectTransFix_001.outputs["Result"], Reroute.inputs["Input"])
        nt.links.new(VectTransFix_001.outputs["Result"], VectorMath_003.inputs[0])
        nt.links.new(Geometry.outputs["Normal"], VectTransFix_002.inputs["Vector"])
        nt.links.new(VectTransFix_002.outputs["Result"], VectorMath_003.inputs[1])
        nt.links.new(VectTransFix_002.outputs["Result"], Reroute_001.inputs["Input"])

        

        #

        EvaluateClosure.input_items.new("VECTOR","Vector")
        EvaluateClosure.output_items.new("FLOAT","Value")

        nt.links.new(EvaluateClosure.outputs["Value"], Math.inputs[0])
        nt.links.new(RepeatInput.outputs["Vector"], EvaluateClosure.inputs["Vector"])
        nt.links.new(GroupInput.outputs["Height Texture"], EvaluateClosure.inputs["Closure"]) 

        for node in nt.nodes:
            if node.type == 'VECT_TRANSFORM':
                node.convert_to="CAMERA"

        Math_003.inputs[1].default_value = -1
        Math_002.inputs[1].default_value = 0.01
        VectorMath_007.inputs['Scale'].default_value = -1
        Tangent.direction_type = 'UV_MAP'

    def duplicate(self):
        self.node_tree = self.node_tree.copy()
        
    def valuesUpdate(self, context):

        if self.node_tree.users > 1:
            self.duplicate()

        for node in self.node_tree.nodes:
            if node.type == "TEX_IMAGE":
                node.image = self.elevation_image
            if hasattr(node, 'uv_map') and self.uv_map:
                node.uv_map = self.uv_map


   
