import bpy
import mathutils


mat = bpy.data.materials.new(name="Material.001")
mat.use_nodes = True


def crackle_noise_node_tree_node_group():
    """Initialize Crackle Noise_node_tree node group"""
    crackle_noise_node_tree = bpy.data.node_groups.new(
        type='CompositorNodeTree', name="Crackle Noise_node_tree")

    crackle_noise_node_tree.color_tag = 'TEXTURE'
    crackle_noise_node_tree.description = ""
    crackle_noise_node_tree.default_group_node_width = 140

    # crackle_noise_node_tree interface

    # Socket Color
    color_socket = crackle_noise_node_tree.interface.new_socket(
        name="Color", in_out='OUTPUT', socket_type='NodeSocketColor')
    color_socket.default_value = (0.0, 0.0, 0.0, 1.0)
    color_socket.attribute_domain = 'POINT'
    color_socket.default_input = 'VALUE'
    color_socket.structure_type = 'AUTO'

    # Socket Fac
    fac_socket = crackle_noise_node_tree.interface.new_socket(
        name="Fac", in_out='OUTPUT', socket_type='NodeSocketFloat')
    fac_socket.default_value = 0.0
    fac_socket.min_value = 0.0
    fac_socket.max_value = 0.0
    fac_socket.subtype = 'NONE'
    fac_socket.attribute_domain = 'POINT'
    fac_socket.default_input = 'VALUE'
    fac_socket.structure_type = 'AUTO'

    # Socket Vector
    vector_socket = crackle_noise_node_tree.interface.new_socket(
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
    w_socket = crackle_noise_node_tree.interface.new_socket(
        name="W", in_out='INPUT', socket_type='NodeSocketFloat')
    w_socket.default_value = 0.0
    w_socket.min_value = -1000.0
    w_socket.max_value = 1000.0
    w_socket.subtype = 'NONE'
    w_socket.attribute_domain = 'POINT'
    w_socket.default_input = 'VALUE'
    w_socket.structure_type = 'AUTO'

    # Socket Scale
    scale_socket = crackle_noise_node_tree.interface.new_socket(
        name="Scale", in_out='INPUT', socket_type='NodeSocketFloat')
    scale_socket.default_value = 5.0
    scale_socket.min_value = -1000.0
    scale_socket.max_value = 1000.0
    scale_socket.subtype = 'NONE'
    scale_socket.attribute_domain = 'POINT'
    scale_socket.default_input = 'VALUE'
    scale_socket.structure_type = 'AUTO'

    # Socket Detail
    detail_socket = crackle_noise_node_tree.interface.new_socket(
        name="Detail", in_out='INPUT', socket_type='NodeSocketFloat')
    detail_socket.default_value = 5.0
    detail_socket.min_value = 0.0
    detail_socket.max_value = 16.0
    detail_socket.subtype = 'NONE'
    detail_socket.attribute_domain = 'POINT'
    detail_socket.default_input = 'VALUE'
    detail_socket.structure_type = 'AUTO'

    # Socket Range
    range_socket = crackle_noise_node_tree.interface.new_socket(
        name="Range", in_out='INPUT', socket_type='NodeSocketFloat')
    range_socket.default_value = 0.5
    range_socket.min_value = 0.0
    range_socket.max_value = 3.4028234663852886e+38
    range_socket.subtype = 'NONE'
    range_socket.attribute_domain = 'POINT'
    range_socket.default_input = 'VALUE'
    range_socket.structure_type = 'AUTO'

    # Initialize crackle_noise_node_tree nodes

    # Node Mix.007
    mix_007 = crackle_noise_node_tree.nodes.new("ShaderNodeMix")
    mix_007.name = "Mix.007"
    mix_007.blend_type = 'SUBTRACT'
    mix_007.clamp_factor = True
    mix_007.clamp_result = False
    mix_007.data_type = 'RGBA'
    mix_007.factor_mode = 'UNIFORM'
    # Factor_Float
    mix_007.inputs[0].default_value = 1.0
    # B_Color
    mix_007.inputs[7].default_value = (0.5, 0.5, 0.5, 1.0)

    # Node Mix.008
    mix_008 = crackle_noise_node_tree.nodes.new("ShaderNodeMix")
    mix_008.name = "Mix.008"
    mix_008.blend_type = 'MULTIPLY'
    mix_008.clamp_factor = True
    mix_008.clamp_result = False
    mix_008.data_type = 'RGBA'
    mix_008.factor_mode = 'UNIFORM'
    # Factor_Float
    mix_008.inputs[0].default_value = 1.0

    # Node Mix.014
    mix_014 = crackle_noise_node_tree.nodes.new("ShaderNodeMix")
    mix_014.name = "Mix.014"
    mix_014.blend_type = 'MULTIPLY'
    mix_014.clamp_factor = True
    mix_014.clamp_result = False
    mix_014.data_type = 'RGBA'
    mix_014.factor_mode = 'UNIFORM'
    # Factor_Float
    mix_014.inputs[0].default_value = 1.0

    # Node Group Output
    group_output = crackle_noise_node_tree.nodes.new("NodeGroupOutput")
    group_output.name = "Group Output"
    group_output.is_active_output = True

    # Node Math.007
    math_007 = crackle_noise_node_tree.nodes.new("ShaderNodeMath")
    math_007.name = "Math.007"
    math_007.operation = 'POWER'
    math_007.use_clamp = False

    # Node Group Input
    group_input = crackle_noise_node_tree.nodes.new("NodeGroupInput")
    group_input.name = "Group Input"

    # Node Math.016
    math_016 = crackle_noise_node_tree.nodes.new("ShaderNodeMath")
    math_016.name = "Math.016"
    math_016.operation = 'MULTIPLY'
    math_016.use_clamp = False
    # Value_001
    math_016.inputs[1].default_value = 10.0

    # Node Math.018
    math_018 = crackle_noise_node_tree.nodes.new("ShaderNodeMath")
    math_018.name = "Math.018"
    math_018.operation = 'POWER'
    math_018.use_clamp = False
    # Value_001
    math_018.inputs[1].default_value = 4.0

    # Node Noise Texture.005
    noise_texture_005 = crackle_noise_node_tree.nodes.new("ShaderNodeTexNoise")
    noise_texture_005.name = "Noise Texture.005"
    noise_texture_005.noise_dimensions = '3D'
    noise_texture_005.noise_type = 'FBM'
    noise_texture_005.normalize = True
    # Roughness
    noise_texture_005.inputs[4].default_value = 0.5
    # Lacunarity
    noise_texture_005.inputs[5].default_value = 2.0
    # Distortion
    noise_texture_005.inputs[8].default_value = 0.0

    # Node Separate RGB.002
    separate_rgb_002 = crackle_noise_node_tree.nodes.new(
        "CompositorNodeSeparateColor")
    separate_rgb_002.name = "Separate RGB.002"
    separate_rgb_002.mode = 'RGB'

    # Node Math.005
    math_005 = crackle_noise_node_tree.nodes.new("ShaderNodeMath")
    math_005.name = "Math.005"
    math_005.operation = 'POWER'
    math_005.use_clamp = False

    # Node Math.017
    math_017 = crackle_noise_node_tree.nodes.new("ShaderNodeMath")
    math_017.name = "Math.017"
    math_017.operation = 'POWER'
    math_017.use_clamp = False


    # Node Combine RGB
    combine_rgb = crackle_noise_node_tree.nodes.new(
        "CompositorNodeCombineColor")
    combine_rgb.name = "Combine RGB"
    combine_rgb.mode = 'RGB'

    # Set locations
    mix_007.location = (-47.364013671875, -28.9608154296875)
    mix_008.location = (164.960205078125, -11.03729248046875)
    mix_014.location = (338.26611328125, -6.556396484375)
    group_output.location = (1399.126708984375, 56.21197509765625)
    math_007.location = (710.6947021484375, -38.49488067626953)
    group_input.location = (-693.909423828125, -55.266014099121094)
    math_016.location = (47.37983703613281, -352.3478088378906)
    math_018.location = (-492.56671142578125, -335.04498291015625)
    noise_texture_005.location = (-239.151611328125, -89.97918701171875)
    separate_rgb_002.location = (516.0333251953125, 12.352848052978516)
    math_005.location = (717.56689453125, 131.79165649414062)
    math_017.location = (889.7227783203125, -66.03863525390625)
    combine_rgb.location = (1107.0928955078125, 99.53492736816406)

    # Set dimensions
    mix_007.width, mix_007.height = 140.0, 100.0
    mix_008.width, mix_008.height = 140.0, 100.0
    mix_014.width, mix_014.height = 140.0, 100.0
    group_output.width, group_output.height = 140.0, 100.0
    math_007.width, math_007.height = 140.0, 100.0
    group_input.width, group_input.height = 140.0, 100.0
    math_016.width, math_016.height = 140.0, 100.0
    math_018.width, math_018.height = 140.0, 100.0
    noise_texture_005.width, noise_texture_005.height = 140.0, 100.0
    separate_rgb_002.width, separate_rgb_002.height = 140.0, 100.0
    math_005.width, math_005.height = 140.0, 100.0
    math_017.width, math_017.height = 140.0, 100.0
    combine_rgb.width, combine_rgb.height = 140.0, 100.0

    # Initialize crackle_noise_node_tree links

    # noise_texture_005.Color -> mix_007.A
    crackle_noise_node_tree.links.new(
        noise_texture_005.outputs[1], mix_007.inputs[6])
    # mix_007.Result -> mix_008.A
    crackle_noise_node_tree.links.new(mix_007.outputs[2], mix_008.inputs[6])
    # mix_008.Result -> mix_014.A
    crackle_noise_node_tree.links.new(mix_008.outputs[2], mix_014.inputs[6])
    # mix_007.Result -> mix_008.B
    crackle_noise_node_tree.links.new(mix_007.outputs[2], mix_008.inputs[7])
    # mix_014.Result -> separate_rgb_002.Color
    crackle_noise_node_tree.links.new(
        mix_014.outputs[2], separate_rgb_002.inputs[0])
    # separate_rgb_002.Red -> math_005.Value
    crackle_noise_node_tree.links.new(
        separate_rgb_002.outputs[0], math_005.inputs[0])
    # group_input.Detail -> noise_texture_005.Detail
    crackle_noise_node_tree.links.new(
        group_input.outputs[3], noise_texture_005.inputs[3])
    # separate_rgb_002.Green -> math_005.Value
    crackle_noise_node_tree.links.new(
        separate_rgb_002.outputs[1], math_005.inputs[1])
    # separate_rgb_002.Blue -> math_007.Value
    crackle_noise_node_tree.links.new(
        separate_rgb_002.outputs[2], math_007.inputs[1])
    # separate_rgb_002.Green -> math_007.Value
    crackle_noise_node_tree.links.new(
        separate_rgb_002.outputs[1], math_007.inputs[0])
    # separate_rgb_002.Blue -> math_017.Value
    crackle_noise_node_tree.links.new(
        separate_rgb_002.outputs[2], math_017.inputs[0])
    # separate_rgb_002.Red -> math_017.Value
    crackle_noise_node_tree.links.new(
        separate_rgb_002.outputs[0], math_017.inputs[1])
    # math_005.Value -> combine_rgb.Red
    crackle_noise_node_tree.links.new(
        math_005.outputs[0], combine_rgb.inputs[0])
    # math_007.Value -> combine_rgb.Green
    crackle_noise_node_tree.links.new(
        math_007.outputs[0], combine_rgb.inputs[1])
    # math_017.Value -> combine_rgb.Blue
    crackle_noise_node_tree.links.new(
        math_017.outputs[0], combine_rgb.inputs[2])
    # group_input.Scale -> noise_texture_005.Scale
    crackle_noise_node_tree.links.new(
        group_input.outputs[2], noise_texture_005.inputs[2])
    # group_input.Range -> math_018.Value
    crackle_noise_node_tree.links.new(
        group_input.outputs[4], math_018.inputs[0])
    # math_016.Value -> mix_014.B
    crackle_noise_node_tree.links.new(math_016.outputs[0], mix_014.inputs[7])
    # combine_rgb.Color -> group_output.Color
    crackle_noise_node_tree.links.new(
        combine_rgb.outputs[0], group_output.inputs[0])
    # math_018.Value -> math_016.Value
    crackle_noise_node_tree.links.new(math_018.outputs[0], math_016.inputs[0])
    # math_007.Value -> group_output.Fac
    crackle_noise_node_tree.links.new(
        math_007.outputs[0], group_output.inputs[1])
    # group_input.W -> noise_texture_005.W
    crackle_noise_node_tree.links.new(
        group_input.outputs[1], noise_texture_005.inputs[1])
    # group_input.Vector -> noise_texture_005.Vector
    crackle_noise_node_tree.links.new(
        group_input.outputs[0], noise_texture_005.inputs[0])

    return crackle_noise_node_tree


