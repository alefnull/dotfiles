import bpy
from ..utils import ShaderNode


class ShaderNodeDent(ShaderNode):
    bl_label = "Dent Noise"
    bl_icon = "NONE"

    # ('NodeSocketBool', 'NodeSocketVector', 'NodeSocketInt', 'NodeSocketShader', 'NodeSocketFloat', 'NodeSocketColor')
    def init(self, context):
        self.getNodetree(self.name + "_node_tree")
        self.inputs["Detail"].default_value = 0
        self.inputs["Scale"].default_value = 5
        self.inputs["Distortion"].default_value = 0
        self.inputs["W"].hide = True

    def createNodetree(self, name):
        nt = self.node_tree = bpy.data.node_groups.new(name, "ShaderNodeTree")
        # Socket Value

        nt.color_tag = "TEXTURE"
        nt.description = ""

        # Socket Value
        value_socket = nt.interface.new_socket(
            name="Value", in_out='OUTPUT', socket_type='NodeSocketFloat')
        value_socket.default_value = 0.0
        value_socket.min_value = 0.0
        value_socket.max_value = 0.0
        value_socket.subtype = 'NONE'
        value_socket.attribute_domain = 'POINT'
        value_socket.default_input = 'VALUE'
        value_socket.structure_type = 'AUTO'

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
        detail_socket.default_value = 0.0
        detail_socket.min_value = 0.0
        detail_socket.max_value = 16.0
        detail_socket.subtype = 'NONE'
        detail_socket.attribute_domain = 'POINT'
        detail_socket.default_input = 'VALUE'
        detail_socket.structure_type = 'AUTO'

        # Socket Distortion
        distortion_socket = nt.interface.new_socket(
            name="Distortion", in_out='INPUT', socket_type='NodeSocketFloat')
        distortion_socket.default_value = 0.0
        distortion_socket.min_value = -1000.0
        distortion_socket.max_value = 1000.0
        distortion_socket.subtype = 'NONE'
        distortion_socket.attribute_domain = 'POINT'
        distortion_socket.default_input = 'VALUE'
        distortion_socket.structure_type = 'AUTO'

        # Initialize nt nodes

        # Node Noise Texture.008
        noise_texture_008 = nt.nodes.new(
            "ShaderNodeTexNoise")
        noise_texture_008.name = "Noise Texture.008"
        noise_texture_008.noise_dimensions = '3D'
        noise_texture_008.noise_type = 'FBM'
        noise_texture_008.normalize = True
        # Roughness
        noise_texture_008.inputs[4].default_value = 0.5
        # Lacunarity
        noise_texture_008.inputs[5].default_value = 2.0

        # Node Mix.008
        mix_008 = nt.nodes.new("ShaderNodeMix")
        mix_008.name = "Mix.008"
        mix_008.blend_type = 'SUBTRACT'
        mix_008.clamp_factor = True
        mix_008.clamp_result = False
        mix_008.data_type = 'RGBA'
        mix_008.factor_mode = 'UNIFORM'
        # Factor_Float
        mix_008.inputs[0].default_value = 1.0
        # B_Color
        mix_008.inputs[7].default_value = (0.5, 0.5, 0.5, 1.0)

        # Node Separate RGB.003
        separate_rgb_003 = nt.nodes.new(
            "ShaderNodeSeparateColor")
        separate_rgb_003.name = "Separate RGB.003"
        separate_rgb_003.mode = 'RGB'

        # Node Math.058
        math_058 = nt.nodes.new("ShaderNodeMath")
        math_058.name = "Math.058"
        math_058.operation = 'MAXIMUM'
        math_058.use_clamp = False

        # Node Math.060
        math_060 = nt.nodes.new("ShaderNodeMath")
        math_060.name = "Math.060"
        math_060.operation = 'ABSOLUTE'
        math_060.use_clamp = False

        # Node Math.061
        math_061 = nt.nodes.new("ShaderNodeMath")
        math_061.name = "Math.061"
        math_061.operation = 'ABSOLUTE'
        math_061.use_clamp = False

        # Node Math.062
        math_062 = nt.nodes.new("ShaderNodeMath")
        math_062.name = "Math.062"
        math_062.operation = 'ABSOLUTE'
        math_062.use_clamp = False

        # Node Math.063
        math_063 = nt.nodes.new("ShaderNodeMath")
        math_063.name = "Math.063"
        math_063.operation = 'MULTIPLY'
        math_063.use_clamp = False
        # Value_001
        math_063.inputs[1].default_value = 2.0

        # Node Math.064
        math_064 = nt.nodes.new("ShaderNodeMath")
        math_064.name = "Math.064"
        math_064.operation = 'MAXIMUM'
        math_064.use_clamp = False

        # Node Group Output
        group_output = nt.nodes.new("NodeGroupOutput")
        group_output.name = "Group Output"
        group_output.is_active_output = True

        # Node Math.065
        math_065 = nt.nodes.new("ShaderNodeMath")
        math_065.name = "Math.065"
        math_065.operation = 'POWER'
        math_065.use_clamp = False
        # Value_001
        math_065.inputs[1].default_value = 2.5

        # Node Group Input
        group_input = nt.nodes.new("NodeGroupInput")
        group_input.name = "Group Input"

        # Node Math.004
        math_004 = nt.nodes.new("ShaderNodeMath")
        math_004.name = "Math.004"
        math_004.operation = 'GREATER_THAN'
        math_004.use_clamp = False
        # Value_001
        math_004.inputs[1].default_value = 0.0

        # Node Math.006
        math_006 = nt.nodes.new("ShaderNodeMath")
        math_006.name = "Math.006"
        math_006.operation = 'ABSOLUTE'
        math_006.use_clamp = False

        # Node Texture Coordinate.001
        texture_coordinate_001 = nt.nodes.new(
            "ShaderNodeTexCoord")
        texture_coordinate_001.name = "Texture Coordinate.001"
        texture_coordinate_001.from_instancer = False

        # Node Mix.006
        mix_006 = nt.nodes.new("ShaderNodeMix")
        mix_006.name = "Mix.006"
        mix_006.blend_type = 'MIX'
        mix_006.clamp_factor = True
        mix_006.clamp_result = False
        mix_006.data_type = 'RGBA'
        mix_006.factor_mode = 'UNIFORM'

        # Set locations
        noise_texture_008.location = (-1680.0, 0.0)
        mix_008.location = (-1470.0, 0.0)
        separate_rgb_003.location = (-1260.0, 0.0)
        math_058.location = (-840.0, 0.0)
        math_060.location = (-1050.0, 0.0)
        math_061.location = (-840.0, -217.1999969482422)
        math_062.location = (-1050.0, -195.60000610351562)
        math_063.location = (-420.0, 0.0)
        math_064.location = (-630.0, 0.0)
        group_output.location = (0.0, 0.0)
        math_065.location = (-210.0, 0.0)
        group_input.location = (-2632.307373046875, -99.59502410888672)
        math_004.location = (-2125.50634765625, 184.67416381835938)
        math_006.location = (-2325.25146484375, 110.12789154052734)
        texture_coordinate_001.location = (-2511.01708984375,
                                           232.3938751220703)
        mix_006.location = (-1920.0816650390625, 178.1026153564453)

        # Set dimensions
        noise_texture_008.width, noise_texture_008.height = 140.0, 100.0
        mix_008.width, mix_008.height = 140.0, 100.0
        separate_rgb_003.width, separate_rgb_003.height = 140.0, 100.0
        math_058.width, math_058.height = 140.0, 100.0
        math_060.width, math_060.height = 140.0, 100.0
        math_061.width, math_061.height = 140.0, 100.0
        math_062.width, math_062.height = 140.0, 100.0
        math_063.width, math_063.height = 140.0, 100.0
        math_064.width, math_064.height = 140.0, 100.0
        group_output.width, group_output.height = 140.0, 100.0
        math_065.width, math_065.height = 140.0, 100.0
        group_input.width, group_input.height = 140.0, 100.0
        math_004.width, math_004.height = 140.0, 100.0
        math_006.width, math_006.height = 140.0, 100.0
        texture_coordinate_001.width, texture_coordinate_001.height = 140.0, 100.0
        mix_006.width, mix_006.height = 140.0, 100.0

        # Initialize nt links

        # noise_texture_008.Color -> mix_008.A
        nt.links.new(
            noise_texture_008.outputs[1], mix_008.inputs[6])
        # separate_rgb_003.Red -> math_060.Value
        nt.links.new(
            separate_rgb_003.outputs[0], math_060.inputs[0])
        # mix_008.Result -> separate_rgb_003.Color
        nt.links.new(
            mix_008.outputs[2], separate_rgb_003.inputs[0])
        # math_058.Value -> math_064.Value
        nt.links.new(math_058.outputs[0], math_064.inputs[0])
        # separate_rgb_003.Green -> math_062.Value
        nt.links.new(
            separate_rgb_003.outputs[1], math_062.inputs[0])
        # separate_rgb_003.Blue -> math_061.Value
        nt.links.new(
            separate_rgb_003.outputs[2], math_061.inputs[0])
        # math_064.Value -> math_063.Value
        nt.links.new(math_064.outputs[0], math_063.inputs[0])
        # math_060.Value -> math_058.Value
        nt.links.new(math_060.outputs[0], math_058.inputs[0])
        # math_062.Value -> math_058.Value
        nt.links.new(math_062.outputs[0], math_058.inputs[1])
        # math_061.Value -> math_064.Value
        nt.links.new(math_061.outputs[0], math_064.inputs[1])
        # math_063.Value -> math_065.Value
        nt.links.new(math_063.outputs[0], math_065.inputs[0])
        # group_input.Scale -> noise_texture_008.Scale
        nt.links.new(
            group_input.outputs[2], noise_texture_008.inputs[2])
        # math_065.Value -> group_output.Value
        nt.links.new(
            math_065.outputs[0], group_output.inputs[0])
        # group_input.Detail -> noise_texture_008.Detail
        nt.links.new(
            group_input.outputs[3], noise_texture_008.inputs[3])
        # group_input.Distortion -> noise_texture_008.Distortion
        nt.links.new(
            group_input.outputs[4], noise_texture_008.inputs[8])
        # group_input.W -> noise_texture_008.W
        nt.links.new(
            group_input.outputs[1], noise_texture_008.inputs[1])
        # math_004.Value -> mix_006.Factor
        nt.links.new(math_004.outputs[0], mix_006.inputs[0])
        # texture_coordinate_001.Generated -> mix_006.A
        nt.links.new(
            texture_coordinate_001.outputs[0], mix_006.inputs[6])
        # math_006.Value -> math_004.Value
        nt.links.new(math_006.outputs[0], math_004.inputs[0])
        # mix_006.Result -> noise_texture_008.Vector
        nt.links.new(
            mix_006.outputs[2], noise_texture_008.inputs[0])
        # group_input.Vector -> mix_006.B
        nt.links.new(
            group_input.outputs[0], mix_006.inputs[7])
        # group_input.Vector -> math_006.Value
        nt.links.new(
            group_input.outputs[0], math_006.inputs[0])
        return nt
