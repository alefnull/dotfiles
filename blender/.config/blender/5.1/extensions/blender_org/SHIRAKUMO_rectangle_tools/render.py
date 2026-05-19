import gpu
from mathutils import Matrix
from gpu_extras.batch import batch_for_shader
from struct import pack

vert_out = gpu.types.GPUStageInterfaceInfo("my_interface")
vert_out.smooth('VEC3', "pos")

shader_info = gpu.types.GPUShaderCreateInfo()
shader_info.push_constant('MAT4', "u_ViewProjectionMatrix")
shader_info.push_constant('VEC3', "u_v", 4)
shader_info.push_constant('VEC4', "u_Color")
shader_info.vertex_in(0, 'INT', "n")
shader_info.vertex_out(vert_out)
shader_info.fragment_out(0, 'VEC4', "FragColor")

shader_info.vertex_source(
    "void main()"
    "{"
    "  gl_Position = u_ViewProjectionMatrix * vec4("
    "    u_v[n],"
    "    1.0f);"
    "}"
)

shader_info.fragment_source(
    "void main()"
    "{"
    "  FragColor = u_Color;"
    "}"
)

shader = gpu.shader.create_from_info(shader_info)
del vert_out
del shader_info

batch = batch_for_shader(shader, 'TRIS', {
    "n": [0,1,2,0,2,3]
})

def rect(context, points, matrix=Matrix.Identity(4)):
    shader.bind()
    shader.uniform_float("u_ViewProjectionMatrix", context.region_data.perspective_matrix @ matrix)
    shader.uniform_vector_float(shader.uniform_from_name("u_v"), pack("12f",*points), 3, 4)
    shader.uniform_float("u_Color", (0.5,0.5,0.9,0.5))
    batch.draw(shader)
