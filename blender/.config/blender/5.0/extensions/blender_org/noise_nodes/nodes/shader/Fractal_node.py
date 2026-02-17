import bpy
from ..utils import ShaderNode


class ShaderNodeFractal(ShaderNode):
    bl_label = "Fractal Noise"
    bl_icon = "NONE"

    # ('NodeSocketBool', 'NodeSocketVector', 'NodeSocketInt', 'NodeSocketShader', 'NodeSocketFloat', 'NodeSocketColor')
    def init(self, context):
        self.getNodetree(self.name + "_node_tree")
        self.inputs["Detail"].default_value = 1
        self.inputs["Scale"].default_value = 10
        self.inputs["Roughness"].default_value = 1
        self.inputs["Distortion"].default_value = 0.1
        self.inputs["From Max"].default_value = 1
        self.inputs["From Min"].default_value = 0.1
        self.inputs["W"].hide = True

    def createNodetree(self, name):
        nt = self.node_tree = bpy.data.node_groups.new(name, "ShaderNodeTree")
        # Socket Result
        nt.color_tag = "TEXTURE"

        nt.description = ""

        # nt interface
        # Socket Result
        result_socket = nt.interface.new_socket(
            name="Result", in_out='OUTPUT', socket_type='NodeSocketFloat')
        result_socket.default_value = 0.0
        result_socket.min_value = 0.0
        result_socket.max_value = 0.0
        result_socket.subtype = 'NONE'
        result_socket.attribute_domain = 'POINT'
        result_socket.default_input = 'VALUE'
        result_socket.structure_type = 'AUTO'

        # Socket Vector
        vector_socket = nt.interface.new_socket(
            name="Vector", in_out='INPUT', socket_type='NodeSocketVector')
        vector_socket.default_value = (0.0, 0.0, 0.0)
        vector_socket.min_value = 0.0
        vector_socket.max_value = 1.0
        vector_socket.subtype = 'NONE'
        vector_socket.attribute_domain = 'POINT'
        vector_socket.hide_value = True
        vector_socket.default_input = 'VALUE'
        vector_socket.structure_type = 'AUTO'

        # Socket W
        w_socket = nt.interface.new_socket(
            name="W", in_out='INPUT', socket_type='NodeSocketFloat')
        w_socket.default_value = 0.0
        w_socket.min_value = -1000.0
        w_socket.max_value = 1000.0
        w_socket.subtype = 'NONE'
        w_socket.attribute_domain = 'POINT'
        w_socket.default_input = 'VALUE'
        w_socket.structure_type = 'AUTO'

        # Socket Scale
        scale_socket = nt.interface.new_socket(
            name="Scale", in_out='INPUT', socket_type='NodeSocketFloat')
        scale_socket.default_value = 5.0
        scale_socket.min_value = -1000.0
        scale_socket.max_value = 1000.0
        scale_socket.subtype = 'NONE'
        scale_socket.attribute_domain = 'POINT'
        scale_socket.default_input = 'VALUE'
        scale_socket.structure_type = 'AUTO'

        # Socket Detail
        detail_socket = nt.interface.new_socket(
            name="Detail", in_out='INPUT', socket_type='NodeSocketFloat')
        detail_socket.default_value = 2.3999998569488525
        detail_socket.min_value = 0.0
        detail_socket.max_value = 16.0
        detail_socket.subtype = 'NONE'
        detail_socket.attribute_domain = 'POINT'
        detail_socket.default_input = 'VALUE'
        detail_socket.structure_type = 'AUTO'

        # Socket Roughness
        roughness_socket = nt.interface.new_socket(
            name="Roughness", in_out='INPUT', socket_type='NodeSocketFloat')
        roughness_socket.default_value = 1.0
        roughness_socket.min_value = 0.0
        roughness_socket.max_value = 1.0
        roughness_socket.subtype = 'FACTOR'
        roughness_socket.attribute_domain = 'POINT'
        roughness_socket.default_input = 'VALUE'
        roughness_socket.structure_type = 'AUTO'

        # Socket Distortion
        distortion_socket = nt.interface.new_socket(
            name="Distortion", in_out='INPUT', socket_type='NodeSocketFloat')
        distortion_socket.default_value = 1.0
        distortion_socket.min_value = -1000.0
        distortion_socket.max_value = 1000.0
        distortion_socket.subtype = 'NONE'
        distortion_socket.attribute_domain = 'POINT'
        distortion_socket.default_input = 'VALUE'
        distortion_socket.structure_type = 'AUTO'

        # Socket From Min
        from_min_socket = nt.interface.new_socket(
            name="From Min", in_out='INPUT', socket_type='NodeSocketFloat')
        from_min_socket.default_value = 0.0
        from_min_socket.min_value = -10000.0
        from_min_socket.max_value = 10000.0
        from_min_socket.subtype = 'NONE'
        from_min_socket.attribute_domain = 'POINT'
        from_min_socket.default_input = 'VALUE'
        from_min_socket.structure_type = 'AUTO'

        # Socket From Max
        from_max_socket = nt.interface.new_socket(
            name="From Max", in_out='INPUT', socket_type='NodeSocketFloat')
        from_max_socket.default_value = 1.0
        from_max_socket.min_value = -10000.0
        from_max_socket.max_value = 10000.0
        from_max_socket.subtype = 'NONE'
        from_max_socket.attribute_domain = 'POINT'
        from_max_socket.default_input = 'VALUE'
        from_max_socket.structure_type = 'AUTO'

        # Initialize nt nodes

        # Node Noise Texture.004
        noise_texture_004 = nt.nodes.new("ShaderNodeTexNoise")
        noise_texture_004.name = "Noise Texture.004"
        noise_texture_004.noise_dimensions = '3D'
        noise_texture_004.noise_type = 'FBM'
        noise_texture_004.normalize = True
        # Lacunarity
        noise_texture_004.inputs[5].default_value = 2.0

        # Node Separate HSV.001
        separate_hsv_001 = nt.nodes.new(
            "ShaderNodeSeparateColor")
        separate_hsv_001.name = "Separate HSV.001"
        separate_hsv_001.mode = 'HSV'

        # Node Map Range
        map_range = nt.nodes.new("ShaderNodeMapRange")
        map_range.name = "Map Range"
        map_range.clamp = True
        map_range.data_type = 'FLOAT'
        map_range.interpolation_type = 'LINEAR'
        # To Min
        map_range.inputs[3].default_value = 0.0
        # To Max
        map_range.inputs[4].default_value = 1.0

        # Node Group Input
        group_input = nt.nodes.new("NodeGroupInput")
        group_input.name = "Group Input"

        # Node Group Output
        group_output = nt.nodes.new("NodeGroupOutput")
        group_output.name = "Group Output"
        group_output.is_active_output = True

        # Node Clamp
        clamp = nt.nodes.new("ShaderNodeClamp")
        clamp.name = "Clamp"
        clamp.hide = True
        clamp.clamp_type = 'MINMAX'
        # Min
        clamp.inputs[1].default_value = 0.0
        # Max
        clamp.inputs[2].default_value = 1.0

        # Node Math.004
        math_004 = nt.nodes.new("ShaderNodeMath")
        math_004.name = "Math.004"
        math_004.hide = True
        math_004.operation = 'GREATER_THAN'
        math_004.use_clamp = False
        # Value_001
        math_004.inputs[1].default_value = 0.0

        # Node Math.006
        math_006 = nt.nodes.new("ShaderNodeMath")
        math_006.name = "Math.006"
        math_006.hide = True
        math_006.operation = 'ABSOLUTE'
        math_006.use_clamp = False

        # Node Texture Coordinate.001
        texture_coordinate_001 = nt.nodes.new(
            "ShaderNodeTexCoord")
        texture_coordinate_001.name = "Texture Coordinate.001"
        texture_coordinate_001.hide = True
        texture_coordinate_001.from_instancer = False

        # Node Mix.006
        mix_006 = nt.nodes.new("ShaderNodeMix")
        mix_006.name = "Mix.006"
        mix_006.hide = True
        mix_006.blend_type = 'MIX'
        mix_006.clamp_factor = True
        mix_006.clamp_result = False
        mix_006.data_type = 'RGBA'
        mix_006.factor_mode = 'UNIFORM'

        # Set locations
        noise_texture_004.location = (-630.0, 0.0)
        separate_hsv_001.location = (-420.0, 0.0)
        map_range.location = (-210.0, 0.0)
        group_input.location = (-1830.934814453125, -47.273258209228516)
        group_output.location = (0.0, 0.0)
        clamp.location = (-840.0, -3.8333332538604736)
        math_004.location = (-1358.337646484375, 157.1769561767578)
        math_006.location = (-1550.9273681640625, 86.21224212646484)
        texture_coordinate_001.location = (-1793.934326171875, 147.591796875)
        mix_006.location = (-1081.3421630859375, 47.4207763671875)

        # Set dimensions
        noise_texture_004.width, noise_texture_004.height = 140.0, 100.0
        separate_hsv_001.width, separate_hsv_001.height = 140.0, 100.0
        map_range.width, map_range.height = 140.0, 100.0
        group_input.width, group_input.height = 140.0, 100.0
        group_output.width, group_output.height = 140.0, 100.0
        clamp.width, clamp.height = 140.0, 100.0
        math_004.width, math_004.height = 140.0, 100.0
        math_006.width, math_006.height = 140.0, 100.0
        texture_coordinate_001.width, texture_coordinate_001.height = 140.0, 100.0
        mix_006.width, mix_006.height = 140.0, 100.0

        # Initialize nt links

        # noise_texture_004.Color -> separate_hsv_001.Color
        nt.links.new(
            noise_texture_004.outputs[1], separate_hsv_001.inputs[0])
        # group_input.Scale -> noise_texture_004.Scale
        nt.links.new(
            group_input.outputs[2], noise_texture_004.inputs[2])
        # group_input.Detail -> noise_texture_004.Detail
        nt.links.new(
            group_input.outputs[3], noise_texture_004.inputs[3])
        # group_input.Distortion -> noise_texture_004.Distortion
        nt.links.new(
            group_input.outputs[5], noise_texture_004.inputs[8])
        # group_input.From Min -> map_range.From Min
        nt.links.new(
            group_input.outputs[6], map_range.inputs[1])
        # group_input.From Max -> map_range.From Max
        nt.links.new(
            group_input.outputs[7], map_range.inputs[2])
        # map_range.Result -> group_output.Result
        nt.links.new(
            map_range.outputs[0], group_output.inputs[0])
        # group_input.Roughness -> clamp.Value
        nt.links.new(group_input.outputs[4], clamp.inputs[0])
        # clamp.Result -> noise_texture_004.Roughness
        nt.links.new(
            clamp.outputs[0], noise_texture_004.inputs[4])
        # separate_hsv_001.Red -> map_range.Value
        nt.links.new(
            separate_hsv_001.outputs[0], map_range.inputs[0])
        # group_input.W -> noise_texture_004.W
        nt.links.new(
            group_input.outputs[1], noise_texture_004.inputs[1])
        # math_004.Value -> mix_006.Factor
        nt.links.new(math_004.outputs[0], mix_006.inputs[0])
        # texture_coordinate_001.Generated -> mix_006.A
        nt.links.new(
            texture_coordinate_001.outputs[0], mix_006.inputs[6])
        # math_006.Value -> math_004.Value
        nt.links.new(math_006.outputs[0], math_004.inputs[0])
        # mix_006.Result -> noise_texture_004.Vector
        nt.links.new(
            mix_006.outputs[2], noise_texture_004.inputs[0])
        # group_input.Vector -> mix_006.B
        nt.links.new(
            group_input.outputs[0], mix_006.inputs[7])
        # group_input.Vector -> math_006.Value
        nt.links.new(
            group_input.outputs[0], math_006.inputs[0])

        return nt
