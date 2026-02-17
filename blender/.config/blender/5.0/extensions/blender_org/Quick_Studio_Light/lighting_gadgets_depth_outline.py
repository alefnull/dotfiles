"""
灯光轮廓描边深度测试实现
兼容Vulkan和OpenGL后端
"""

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix
from bpy_extras import view3d_utils
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_location_3d
import math

# 导入Vulkan兼容性层
from .vulkan_compat import (
    is_vulkan_backend,
    create_compatible_shader,
    create_builtin_shader,
    VulkanCompatibleStateManager,
    create_compatible_batch,
    check_compatibility,
    vulkan_compatible,
    get_vulkan_manager
)

from .lighting_gadgets_utils import is_heavy_geometry_nodes_scene

# 常量定义
TWO_PI = 2.0 * math.pi
CIRCLE_SEGMENTS_LOW = 16      # 低质量圆形段数（远景）
CIRCLE_SEGMENTS_MEDIUM = 32   # 中等质量圆形段数（中景）
CIRCLE_SEGMENTS_HIGH = 64     # 高质量圆形段数（近景）
LINE_SEGMENTS_ANGLE = 5
LIGHT_OUTLINE_RADIUS = 15.0   # 默认灯光轮廓半径（像素）
CONTROL_POINT_RADIUS = 5.0    # 控制点半径（像素）

# 深度测试遮挡参数
CULLING_OPACITY = 0.05        # 被遮挡部分的透明度
RENDERED_CULLING_OPACITY = 0.02

# 简单的缓存系统，避免频繁计算
_pixel_world_cache = {}

# 初始化Vulkan兼容性检查器
_vulkan_state_manager = get_vulkan_manager()
_DEPTH_OUTLINE_SHADER_CACHE = {}

# 检查当前GPU后端兼容性
def check_gpu_compatibility():
    """检查GPU兼容性并在首次运行时输出信息"""
    if not hasattr(check_gpu_compatibility, '_checked'):
        check_gpu_compatibility._checked = True
        return check_compatibility()
    return None

def pixel_to_world_radius(context, center_3d, pixel_radius):
    """Convert pixel radius to world space radius at a given 3D location"""
    region = context.region
    rv3d = context.region_data
    
    if not region or not rv3d:
        return pixel_radius * 0.01  # 备用值
    
    # 检查是否处于正交模式
    is_orthographic = hasattr(rv3d, 'is_perspective') and not rv3d.is_perspective
    
    # Get the center point in screen space
    center_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, center_3d)
    
    if center_2d is None:
        # If off-screen, use a more stable calculation
        if is_orthographic:
            # Orthographic mode: size is independent of distance
            # 使用正交缩放因子
            view_matrix = rv3d.view_matrix
            # 从视图矩阵中提取缩放信息
            scale_x = Vector((view_matrix[0][0], view_matrix[1][0], view_matrix[2][0])).length
            scale_y = Vector((view_matrix[0][1], view_matrix[1][1], view_matrix[2][1])).length
            avg_scale = (scale_x + scale_y) * 0.5
            
            # 基于视口尺寸和像素密度计算
            viewport_scale = min(region.width, region.height) * 0.001 * avg_scale
            return pixel_radius * viewport_scale
        else:
            # Perspective mode: scale with distance
            view_distance = (rv3d.view_location - center_3d).length
            return pixel_radius * view_distance * 0.001
    
    # Create a point offset by pixel_radius in screen space
    offset_2d = Vector((center_2d.x + pixel_radius, center_2d.y))
    
    if is_orthographic:
            # 正交模式：改进的基于平面的计算
        # 使用视图矩阵的逆变换来正确计算正交模式下的世界坐标
        view_matrix = rv3d.view_matrix
        
        # 获取视图平面的法线（相机朝向）
        view_normal = Vector((view_matrix[0][2], view_matrix[1][2], view_matrix[2][2])).normalized()
        
        # 创建一个与视图平面平行的平面，通过中心点
        plane_normal = view_normal
        plane_point = center_3d
        
        # 将屏幕坐标转换为3D世界坐标
        try:
            offset_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, offset_2d, plane_point)
            world_radius = (offset_3d - center_3d).length
            
            # 如果计算失败，使用备用方法
            if world_radius == 0 or world_radius > 1000:  # 异常值检测
                # 基于视图矩阵的备用计算
                pixel_to_world_scale = Vector((view_matrix[0][0], view_matrix[1][0], view_matrix[2][0])).length
                world_radius = pixel_radius * pixel_to_world_scale * 0.001
        except:
            # 异常情况下使用经验值
            world_radius = pixel_radius * 0.01
    else:
        # 透视模式：使用标准计算
        offset_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, offset_2d, center_3d)
        world_radius = (offset_3d - center_3d).length
    
    # Remove cache usage completely to avoid issues with varying distances
    # 移除缓存逻辑因为它没有考虑距离/位置变化
    
    return world_radius


@vulkan_compatible
def draw_light_outline_depth(context, obj, color, thickness=2):
    """
    使用GLSL绘制灯光轮廓，并参与深度遮挡
    兼容Vulkan和OpenGL后端
    """
    # 早期退出：如果透明度为0，不进行绘制以节省性能
    if len(color) >= 4 and color[3] <= 0.0:
        return
        
    region = context.region
    rv3d = context.region_data
    if not region or not rv3d:
        return
    
    if obj is None or obj.type != 'LIGHT':
        return
    
    light = obj.data

    is_rendered_view = False
    try:
        space = context.space_data
        if space and space.type == 'VIEW_3D' and hasattr(space, "shading"):
            is_rendered_view = (space.shading.type == 'RENDERED')
    except Exception:
        is_rendered_view = False

    heavy_instances_scene = False
    if is_rendered_view:
        try:
            heavy_instances_scene = is_heavy_geometry_nodes_scene(context)
        except Exception:
            heavy_instances_scene = False
    
    # 生成本地坐标的轮廓顶点
    segments_mul = 2 if is_rendered_view else 1
    local_points = _generate_light_outline_vertices(light, segments_mul=segments_mul)
    
    if not local_points:
        return
    
    # 转为世界坐标
    world_points = []
    for lp in local_points:
        world = obj.matrix_world @ Vector(lp)
        world_points.append(world)
        
    ring_points, line_segments = _split_light_outline_primitives(light, world_points)
    
    # 扩展直线单独处理（为了支持不同的透明度）
    extension_segments = []
    extra_local_segments = _generate_area_outline_extension_segments_local(light)
    if extra_local_segments:
        for p1_local, p2_local in extra_local_segments:
            extension_segments.append((obj.matrix_world @ Vector(p1_local), obj.matrix_world @ Vector(p2_local)))

    if not ring_points and not line_segments and not extension_segments:
        return

    shader = _get_light_outline_solid_shader()
    if shader is None:
        return

    depsgraph = None
    occluded_alpha = 1.0
    if is_rendered_view and not heavy_instances_scene:
        occluded_alpha = float(RENDERED_CULLING_OPACITY)
        try:
            depsgraph = context.evaluated_depsgraph_get()
        except Exception:
            depsgraph = None

    # 构建主轮廓批次
    batch_main = None
    if ring_points or line_segments:
        pos, offset, uv, alpha, indices = _build_light_outline_triangles(
            context, region, rv3d, ring_points, line_segments, thickness, depsgraph, obj, occluded_alpha
        )
        if pos and indices and alpha:
            batch_main = create_compatible_batch(
                shader,
                'TRIS',
                {"pos": pos, "offset": offset, "uv": uv, "a": alpha},
                indices=indices,
            )

    # 构建扩展直线批次
    batch_ext = None
    if extension_segments:
        pos, offset, uv, alpha, indices = _build_light_outline_triangles(
            context, region, rv3d, [], extension_segments, thickness, depsgraph, obj, occluded_alpha
        )
        if pos and indices and alpha:
            batch_ext = create_compatible_batch(
                shader,
                'TRIS',
                {"pos": pos, "offset": offset, "uv": uv, "a": alpha},
                indices=indices,
            )

    if batch_main is None and batch_ext is None:
        return

    prev_depth_test = None
    prev_blend = None
    prev_depth_mask = None

    try:
        if hasattr(gpu.state, "depth_test_get"):
            prev_depth_test = gpu.state.depth_test_get()
        if hasattr(gpu.state, "blend_get"):
            prev_blend = gpu.state.blend_get()
        if hasattr(gpu.state, "depth_mask_get"):
            prev_depth_mask = gpu.state.depth_mask_get()
    except Exception:
        prev_depth_test = None
        prev_blend = None
        prev_depth_mask = None

    try:
        _vulkan_state_manager.set_blend_mode('ALPHA')
        _vulkan_state_manager.set_depth_test('LESS_EQUAL')
        if hasattr(gpu.state, "depth_mask_set"):
            gpu.state.depth_mask_set(False)

        shader.bind()
        shader.uniform_float("ModelViewProjectionMatrix", rv3d.perspective_matrix)
        shader.uniform_float("u_viewport", (region.width, region.height))

        if is_rendered_view and heavy_instances_scene:
            faint_alpha = float(RENDERED_CULLING_OPACITY)
            _vulkan_state_manager.set_depth_test('GREATER')
            if batch_main:
                faint_color = (color[0], color[1], color[2], color[3] * faint_alpha)
                shader.uniform_float("u_color", faint_color)
                batch_main.draw(shader)

            if batch_ext:
                ext_faint_color = (color[0], color[1], color[2], color[3] * 0.25 * faint_alpha)
                shader.uniform_float("u_color", ext_faint_color)
                batch_ext.draw(shader)

            _vulkan_state_manager.set_depth_test('LESS_EQUAL')

        if batch_main:
            shader.uniform_float("u_color", color)
            batch_main.draw(shader)

        if batch_ext:
            ext_color = (color[0], color[1], color[2], color[3] * 0.25)
            shader.uniform_float("u_color", ext_color)
            batch_ext.draw(shader)
    finally:
        if hasattr(gpu.state, "depth_mask_set") and prev_depth_mask is not None:
            try:
                gpu.state.depth_mask_set(prev_depth_mask)
            except Exception:
                pass
        if prev_depth_test is not None:
            try:
                _vulkan_state_manager.set_depth_test(prev_depth_test)
            except Exception:
                pass
        else:
            _vulkan_state_manager.set_depth_test('NONE')
        if prev_blend is not None:
            try:
                _vulkan_state_manager.set_blend_mode(prev_blend)
            except Exception:
                pass
        else:
            _vulkan_state_manager.set_blend_mode('NONE')


def _get_light_outline_solid_shader():
    shader = _DEPTH_OUTLINE_SHADER_CACHE.get("LIGHT_OUTLINE_SOLID")
    if shader is not None:
        return shader

    if not hasattr(gpu, "types") or not hasattr(gpu.types, "GPUShaderCreateInfo"):
        _DEPTH_OUTLINE_SHADER_CACHE["LIGHT_OUTLINE_SOLID"] = None
        return None
    if not hasattr(gpu.shader, "create_from_info"):
        _DEPTH_OUTLINE_SHADER_CACHE["LIGHT_OUTLINE_SOLID"] = None
        return None

    info = gpu.types.GPUShaderCreateInfo()
    info.push_constant("MAT4", "ModelViewProjectionMatrix")
    info.vertex_in(0, "VEC3", "pos")
    info.vertex_in(1, "VEC2", "offset")
    info.vertex_in(2, "VEC2", "uv")
    info.vertex_in(3, "FLOAT", "a")
    info.push_constant("VEC4", "u_color")
    info.push_constant("VEC2", "u_viewport")
    info.fragment_out(0, "VEC4", "fragColor")

    interface = gpu.types.GPUStageInterfaceInfo("light_outline_interface")
    interface.smooth('VEC2', "var_uv")
    interface.smooth('FLOAT', "var_a")
    info.vertex_out(interface)

    info.vertex_source(
        """
        void main() {
            vec4 clip = ModelViewProjectionMatrix * vec4(pos, 1.0);
            vec2 ndc_offset = (offset * 2.0 / u_viewport) * clip.w;
            gl_Position = clip;
            gl_Position.xy += ndc_offset;
            var_uv = uv;
            var_a = a;
        }
        """
    )

    info.fragment_source(
        """
        void main() {
            float dist = abs(var_uv.y);
// 使用fwidth进行自适应抗锯齿
            float delta = fwidth(dist);
            float alpha_edge = 1.0 - smoothstep(max(0.0, 1.0 - delta), 1.0, dist);
            fragColor = vec4(u_color.rgb, u_color.a * alpha_edge * var_a);
        }
        """
    )

    try:
        shader = gpu.shader.create_from_info(info)
    except Exception:
        shader = None
    
    _DEPTH_OUTLINE_SHADER_CACHE["LIGHT_OUTLINE_SOLID"] = shader
    return shader

@vulkan_compatible
def draw_crosshair_glsl(context, center, target, size_px, color, thickness=1):
    """
    使用GLSL绘制指向目标的3D十字准星
    模仿LightControl的风格
    """
    if center is None or target is None:
        return

    region = context.region
    rv3d = context.region_data
    if not region or not rv3d:
        return

    # 计算世界空间大小，保持屏幕大小一致
    size = pixel_to_world_radius(context, center, size_px)
    
    # 计算朝向目标的旋转
    direction = (target - center)
    if direction.length_squared < 0.0001:
        return
    direction = direction.normalized()
    
    # 创建旋转矩阵，将Z轴对齐到目标方向
    # 我们希望准星位于局部空间的XY平面上
    rot_mat = direction.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    
    # 生成线条
    # 中间留空隙
    gap = size * 0.25
    extent = size * 2.0 # 加长准星长度 (约为原来的3倍)
    
    # 十字准星的4个线段 (位于局部XY平面)
    # 每一对是 (起始点, 结束点)
    local_starts = [
        Vector((0, gap, 0)), 
        Vector((0, -gap, 0)), 
        Vector((gap, 0, 0)), 
        Vector((-gap, 0, 0)), 
    ]
    
    local_ends = [
        Vector((0, extent, 0)),
        Vector((0, -extent, 0)),
        Vector((extent, 0, 0)),
        Vector((-extent, 0, 0)),
    ]
    
    world_lines = []
    alpha_factors = [] # 每个顶点的透明度因子
    
    for start, end in zip(local_starts, local_ends):
        # 起点 (靠近中心) - 不透明
        world_lines.append(rot_mat @ start + center)
        alpha_factors.append(0.6)
        
        # 终点 (远离中心) - 透明 (淡出)
        world_lines.append(rot_mat @ end + center)
        alpha_factors.append(0.0)

    # 检查是否应该显示背面半圆
    # 如果准星指向用户（方向与视线方向点积 > 0），则隐藏半圆
    # 使用夹角淡出算法：
    # dot > 0.2：完全隐藏（指向用户）
    # dot < -0.2：完全显示（背离用户）
    # -0.2 < dot < 0.2：线性淡出
    arc_alpha_scale = 1.0
    
    if context.region_data:
        # 获取相机位置和视线方向
        view_inv = context.region_data.view_matrix.inverted()
        cam_pos = view_inv.translation
        to_cam = (cam_pos - center).normalized()
        
        # direction 是准星指向目标的向量 (Z轴)
        # to_cam 是指向相机的向量
        dot = direction.dot(to_cam)
        
        if dot > 0.2:
            arc_alpha_scale = 0.0
        elif dot < -0.2:
            arc_alpha_scale = 1.0
        else:
            # 线性插值: mapping [-0.2, 0.2] -> [1.0, 0.0]
            # t = (dot - (-0.2)) / (0.2 - (-0.2)) = (dot + 0.2) / 0.4
            t = (dot + 0.2) / 0.4
            arc_alpha_scale = 1.0 - t

    if arc_alpha_scale > 0.001:
        # 添加背面半圆 (Arc 1: XZ plane, Arc 2: YZ plane)
        # 半圆缩小至20%，不再连接最远端，而是作为中心装饰
        arc_radius = extent * 0.8
        
        num_segments = 16
        for i in range(num_segments):
            t1 = math.pi * (i / num_segments)
            t2 = math.pi * ((i + 1) / num_segments)
            
            # 计算插值因子 (用于alpha和坐标)
            # alpha: 两端为0 (连接到隐形端点)，中间为1 (背面最远处)
            # 应用整体淡出因子 arc_alpha_scale
            a1 = math.sin(t1)
            a2 = math.sin(t2)
            
            c1 = math.cos(t1)
            c2 = math.cos(t2)
            
            s1 = math.sin(t1)
            s2 = math.sin(t2)
            
            # Arc 1: 连接 +X 和 -X 方向 (在XZ平面)
            p1_x = Vector((arc_radius * c1, 0, -arc_radius * s1))
            p2_x = Vector((arc_radius * c2, 0, -arc_radius * s2))
            
            world_lines.append(rot_mat @ p1_x + center)
            alpha_factors.append(a1 * 0.5 * arc_alpha_scale) # 半圆稍微暗一点，最大alpha 0.5
            world_lines.append(rot_mat @ p2_x + center)
            alpha_factors.append(a2 * 0.5 * arc_alpha_scale)

            # Arc 2: 连接 +Y 和 -Y 方向 (在YZ平面)
            p1_y = Vector((0, arc_radius * c1, -arc_radius * s1))
            p2_y = Vector((0, arc_radius * c2, -arc_radius * s2))
            
            world_lines.append(rot_mat @ p1_y + center)
            alpha_factors.append(a1 * 0.5 * arc_alpha_scale)
            world_lines.append(rot_mat @ p2_y + center)
            alpha_factors.append(a2 * 0.5 * arc_alpha_scale)
        
    # 着色器设置 (使用类似LightControl的简单自定义着色器)
    # 注意：我们为此特定着色器使用缓存键
    shader_key = "CROSSHAIR_SHADER_FADE"
    shader = _DEPTH_OUTLINE_SHADER_CACHE.get(shader_key)
    
    if shader is None:
        try:
            if not hasattr(gpu, "types") or not hasattr(gpu.types, "GPUShaderCreateInfo"):
                return
                
            vert_out = gpu.types.GPUStageInterfaceInfo("lightCross3D")
            vert_out.smooth('VEC3', "pos")
            vert_out.smooth('FLOAT', "v_alpha")
            
            shader_info = gpu.types.GPUShaderCreateInfo()
            shader_info.push_constant('MAT4', "u_ViewProjectionMatrix")
            shader_info.push_constant('VEC4', "u_color")
            shader_info.vertex_in(0, 'VEC3', "position")
            shader_info.vertex_in(1, 'FLOAT', "alpha_factor")
            shader_info.vertex_out(vert_out)
            shader_info.fragment_out(0, 'VEC4', "FragColor")
            
            shader_info.vertex_source(
                "void main()"
                "{"
                "  pos = position;"
                "  v_alpha = alpha_factor;"
                "  gl_Position = u_ViewProjectionMatrix * vec4(position, 1.0f);"
                "}"
            )
            shader_info.fragment_source(
                "void main()"
                "{"
                "  FragColor = vec4(u_color.rgb, u_color.a * v_alpha);"
                "}"
            )
            shader = gpu.shader.create_from_info(shader_info)
            _DEPTH_OUTLINE_SHADER_CACHE[shader_key] = shader
        except Exception:
            return

    if shader is None:
        return

    batch = batch_for_shader(shader, 'LINES', {"position": world_lines, "alpha_factor": alpha_factors})
    
    # 保存GL状态
    prev_depth_test = None
    prev_blend = None
    try:
        if hasattr(gpu.state, "depth_test_get"):
            prev_depth_test = gpu.state.depth_test_get()
        if hasattr(gpu.state, "blend_get"):
            prev_blend = gpu.state.blend_get()
    except:
        pass
        
    try:
        _vulkan_state_manager.set_blend_mode('ALPHA')
        gpu.state.line_width_set(thickness)
        
        shader.bind()
        shader.uniform_float("u_ViewProjectionMatrix", rv3d.perspective_matrix)
        
        # 1. 绘制被遮挡部分 (淡色)
        _vulkan_state_manager.set_depth_test('GREATER')
        faint_color = (color[0], color[1], color[2], color[3] * 0.1) # 10% 透明度用于被遮挡部分
        shader.uniform_float("u_color", faint_color)
        batch.draw(shader)
        
        # 2. 绘制可见部分
        _vulkan_state_manager.set_depth_test('LESS_EQUAL')
        shader.uniform_float("u_color", color)
        batch.draw(shader)
        
    finally:
        # 恢复GL状态
        if prev_depth_test:
            try:
                _vulkan_state_manager.set_depth_test(prev_depth_test)
            except:
                pass
        else:
            _vulkan_state_manager.set_depth_test('NONE')
            
        if prev_blend:
            try:
                _vulkan_state_manager.set_blend_mode(prev_blend)
            except:
                pass
        else:
            _vulkan_state_manager.set_blend_mode('NONE')


def _split_light_outline_primitives(light, world_points):
    if not world_points:
        return [], []

    if light.type == 'SPOT':
        segments = CIRCLE_SEGMENTS_MEDIUM
        circle_points_count = segments + 1
        ring = []
        if len(world_points) >= circle_points_count:
            ring = list(world_points[:circle_points_count])
        lines = []
        for i in range(circle_points_count, len(world_points), 2):
            if i + 1 < len(world_points):
                lines.append((world_points[i], world_points[i + 1]))
        return ring, lines

    return list(world_points), []


def _generate_area_outline_extension_segments_local(light):
    try:
        if light.type != 'AREA':
            return []

        shape = getattr(light, 'shape', 'SQUARE')
        points = []
        extension_length = 0.0

        if shape == 'SQUARE':
            size = float(getattr(light, 'size', 1.0)) * 0.5
            extension_length = size
            points = [
                (size, 0.0, 0.0),
                (-size, 0.0, 0.0),
                (0.0, size, 0.0),
                (0.0, -size, 0.0),
            ]
        elif shape == 'RECTANGLE':
            size_x = float(getattr(light, 'size', 1.0)) * 0.5
            size_y = float(getattr(light, 'size_y', 1.0)) * 0.5
            extension_length = min(size_x, size_y)
            points = [
                (size_x, 0.0, 0.0),
                (-size_x, 0.0, 0.0),
                (0.0, size_y, 0.0),
                (0.0, -size_y, 0.0),
            ]
        elif shape in {'DISK', 'ELLIPSE'}:
            radius_x = float(getattr(light, 'size', 1.0)) * 0.5
            radius_y = float(getattr(light, 'size_y', getattr(light, 'size', 1.0))) * 0.5
            extension_length = min(radius_x, radius_y)
            points = [
                (radius_x, 0.0, 0.0),
                (0.0, radius_y, 0.0),
                (-radius_x, 0.0, 0.0),
                (0.0, -radius_y, 0.0),
            ]

        extension_length *= 0.5

        if extension_length <= 1e-8 or not points:
            return []

        segments = []
        for p in points:
            p_vec = Vector(p)
            if p_vec.length_squared <= 1e-12:
                continue
            direction = -p_vec.normalized()
            end_vec = p_vec + direction * extension_length
            segments.append((p, (float(end_vec.x), float(end_vec.y), float(end_vec.z))))

        return segments
    except Exception:
        return []


def _build_light_outline_triangles(context, region, rv3d, ring_points, line_segments, thickness_px, depsgraph, ignore_obj, occluded_alpha):
    # Ensure minimum width for anti-aliasing (at least 2px total width)
    half_w = max(1.0, float(thickness_px) * 0.5)

    pos = []
    offset = []
    uv = []
    alpha = []
    indices = []

    factor_cache = {}

    def occlusion_factor(p3d):
        if depsgraph is None:
            return 1.0

        key = (round(float(p3d.x), 6), round(float(p3d.y), 6), round(float(p3d.z), 6))
        cached = factor_cache.get(key)
        if cached is not None:
            return cached

        try:
            p2d = location_3d_to_region_2d(region, rv3d, p3d)
            if p2d is None:
                factor_cache[key] = 1.0
                return 1.0

            origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, p2d)
            direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, p2d)
            if direction.length <= 1e-12:
                factor_cache[key] = 1.0
                return 1.0
            direction.normalize()

            t = (p3d - origin).dot(direction)
            if t <= 1e-6:
                factor_cache[key] = 1.0
                return 1.0

            hit, hit_loc, hit_no, hit_index, hit_obj, hit_mat = context.scene.ray_cast(
                depsgraph, origin, direction, distance=max(0.0, t - 1e-4)
            )
            if not hit:
                factor_cache[key] = 1.0
                return 1.0
            if ignore_obj is not None and hit_obj == ignore_obj:
                factor_cache[key] = 1.0
                return 1.0

            factor_cache[key] = float(occluded_alpha)
            return factor_cache[key]
        except Exception:
            factor_cache[key] = 1.0
            return 1.0

    def add_vertex(p3d, off2d, side, a):
        pos.append((float(p3d.x), float(p3d.y), float(p3d.z)))
        offset.append((float(off2d.x), float(off2d.y)))
        uv.append((0.0, float(side)))
        alpha.append(float(a))
        return len(pos) - 1

    def safe_project(p3d):
        p2d = location_3d_to_region_2d(region, rv3d, p3d)
        if p2d is None:
            return None
        return Vector((float(p2d.x), float(p2d.y)))

    def add_segment_quad(p1_3d, p2_3d):
        p1_2d = safe_project(p1_3d)
        p2_2d = safe_project(p2_3d)
        if p1_2d is None or p2_2d is None:
            return

        d = p2_2d - p1_2d
        if d.length <= 1e-6:
            return
        d.normalize()
        n = Vector((-d.y, d.x)) * half_w

        a1 = occlusion_factor(p1_3d)
        a2 = occlusion_factor(p2_3d)

        i0 = add_vertex(p1_3d, n, 1.0, a1)
        i1 = add_vertex(p1_3d, -n, -1.0, a1)
        i2 = add_vertex(p2_3d, n, 1.0, a2)
        i3 = add_vertex(p2_3d, -n, -1.0, a2)

        indices.append((i0, i1, i2))
        indices.append((i1, i3, i2))

    def add_ring_as_miter(ring3d):
        if len(ring3d) < 3:
            return False

        ring3d_clean = list(ring3d)
        if (ring3d_clean[0] - ring3d_clean[-1]).length <= 1e-10:
            ring3d_clean.pop()
        if len(ring3d_clean) < 3:
            return False

        ring2d = []
        for p in ring3d_clean:
            p2d = safe_project(p)
            if p2d is None:
                return False
            ring2d.append(p2d)

        miter_offsets = []
        n = len(ring3d_clean)
        for i in range(n):
            prev = ring2d[(i - 1) % n]
            curr = ring2d[i]
            nxt = ring2d[(i + 1) % n]

            d1 = curr - prev
            d2 = nxt - curr
            if d1.length <= 1e-6 or d2.length <= 1e-6:
                miter_offsets.append(Vector((0.0, 0.0)))
                continue
            d1.normalize()
            d2.normalize()
            n1 = Vector((-d1.y, d1.x))
            n2 = Vector((-d2.y, d2.x))
            m = n1 + n2
            if m.length <= 1e-6:
                m = n2
            m.normalize()

            denom = m.dot(n2)
            if abs(denom) <= 1e-3:
                m_len = half_w
            else:
                m_len = half_w / denom
            m_len = max(-half_w * 4.0, min(half_w * 4.0, m_len))
            miter_offsets.append(m * m_len)

        base = len(pos)
        for i, p3d in enumerate(ring3d_clean):
            off = miter_offsets[i]
            a = occlusion_factor(p3d)
            add_vertex(p3d, off, 1.0, a)
            add_vertex(p3d, -off, -1.0, a)

        for i in range(n):
            j = (i + 1) % n
            li = base + 2 * i
            ri = base + 2 * i + 1
            lj = base + 2 * j
            rj = base + 2 * j + 1
            indices.append((li, ri, lj))
            indices.append((ri, rj, lj))

        return True

    def add_ring_as_segments(ring3d):
        if len(ring3d) < 2:
            return
        ring3d_clean = list(ring3d)
        if len(ring3d_clean) >= 2 and (ring3d_clean[0] - ring3d_clean[-1]).length <= 1e-10:
            ring3d_clean.pop()
        if len(ring3d_clean) < 2:
            return

        for i in range(len(ring3d_clean)):
            p1 = ring3d_clean[i]
            p2 = ring3d_clean[(i + 1) % len(ring3d_clean)]
            add_segment_quad(p1, p2)

    if ring_points:
        if not add_ring_as_miter(ring_points):
            add_ring_as_segments(ring_points)

    for seg in line_segments:
        add_segment_quad(seg[0], seg[1])

    return pos, offset, uv, alpha, indices


def _process_segment_for_draw(context, region, rv3d, view_matrix, clip_start, p1, p2, batch_list):
    """处理单条线段：投影、裁剪、加入批次"""
    # 优先尝试直接投影
    p1_2d = location_3d_to_region_2d(region, rv3d, p1)
    p2_2d = location_3d_to_region_2d(region, rv3d, p2)
    
    needs_clipping = False
    if p1_2d is None or p2_2d is None:
        needs_clipping = True
        
    final_p1, final_p2 = p1, p2
    
    if needs_clipping:
        clipped_points = _clip_line_segment_to_view(p1, p2, view_matrix, clip_start)
        if not clipped_points:
            return
        final_p1, final_p2 = clipped_points
        # 重新投影
        p1_2d = location_3d_to_region_2d(region, rv3d, final_p1)
        p2_2d = location_3d_to_region_2d(region, rv3d, final_p2)
        
    if p1_2d is not None and p2_2d is not None:
        batch_list.extend([p1_2d, p2_2d])



def _generate_light_outline_vertices(light, segments_mul=1):
    """生成灯光轮廓的本地坐标顶点"""
    local_points = []
    mul = int(max(1, segments_mul))
    
    try:
        if light.type == 'AREA':
            shape = getattr(light, 'shape', 'SQUARE')
            if shape == 'SQUARE':
                size = getattr(light, 'size', 1.0) * 0.5
                local_points = [
                    (-size, -size, 0.0), (size, -size, 0.0), (size, size, 0.0), (-size, size, 0.0), (-size, -size, 0.0)
                ]
            elif shape == 'RECTANGLE':
                size_x = getattr(light, 'size', 1.0) * 0.5
                size_y = getattr(light, 'size_y', 1.0) * 0.5
                local_points = [
                    (-size_x, -size_y, 0.0), (size_x, -size_y, 0.0), (size_x, size_y, 0.0), (-size_x, size_y, 0.0), (-size_x, -size_y, 0.0)
                ]
            elif shape in {'DISK', 'ELLIPSE'}:
                rx = getattr(light, 'size', 1.0) * 0.5
                ry = getattr(light, 'size_y', getattr(light, 'size', 1.0)) * 0.5
                segments = CIRCLE_SEGMENTS_HIGH * mul
                for i in range(segments + 1):
                    angle = TWO_PI * i / segments
                    x = rx * math.cos(angle)
                    y = ry * math.sin(angle)
                    local_points.append((x, y, 0.0))
        elif light.type == 'POINT':
            # 点光源：使用半径或软阴影尺寸作为圆半径
            radius = getattr(light, 'radius', getattr(light, 'shadow_soft_size', 0.25))
            r = max(radius, 0.001)
            segments = CIRCLE_SEGMENTS_HIGH * mul
            for i in range(segments + 1):
                angle = TWO_PI * i / segments
                x = r * math.cos(angle)
                y = r * math.sin(angle)
                local_points.append((x, y, 0.0))
        elif light.type == 'SPOT':
            # 聚光灯：绘制圆锥轮廓和角度线
            # 1. 绘制圆形轮廓（基于软阴影尺寸或半径）
            radius = getattr(light, 'shadow_soft_size', getattr(light, 'radius', 0.25))
            r = max(radius, 0.001)
            segments = CIRCLE_SEGMENTS_MEDIUM * mul
            for i in range(segments + 1):
                angle = TWO_PI * i / segments
                x = r * math.cos(angle)
                y = r * math.sin(angle)
                local_points.append((x, y, 0.0))
            
            # 2. 添加角度线（圆锥边缘线）
            spot_size = getattr(light, 'spot_size', math.pi / 4)  # 默认45度
            spot_blend = getattr(light, 'spot_blend', 0.15)  # 软边混合
            
            # 计算角度线长度（基于距离或固定长度）
            angle_line_length = 2.0  # 固定长度
            
            # 外圆锥边缘线（主要角度）- 分段绘制
            angle_half = spot_size * 0.5
            segments = LINE_SEGMENTS_ANGLE * mul
            
            # 四个方向的边缘线
            directions = [
                (1.0, 0.0),   # 右
                (-1.0, 0.0),  # 左
                (0.0, 1.0),   # 上
                (0.0, -1.0)   # 下
            ]
            
            for dir_x, dir_y in directions:
                x_edge = dir_x * math.sin(angle_half) * angle_line_length
                y_edge = dir_y * math.sin(angle_half) * angle_line_length
                z_edge = math.cos(angle_half) * angle_line_length
                
                # 分段绘制每条边缘线
                for i in range(segments):
                    start_ratio = i / segments
                    end_ratio = (i + 1) / segments
                    
                    start_x = x_edge * start_ratio
                    start_y = y_edge * start_ratio
                    start_z = -z_edge * start_ratio
                    
                    end_x = x_edge * end_ratio
                    end_y = y_edge * end_ratio
                    end_z = -z_edge * end_ratio
                    
                    local_points.extend([(start_x, start_y, start_z), (end_x, end_y, end_z)])
        else:
            # 其他类型，绘制一个小圆表示
            r = 0.25
            segments = CIRCLE_SEGMENTS_HIGH * mul
            for i in range(segments + 1):
                angle = TWO_PI * i / segments
                x = r * math.cos(angle)
                y = r * math.sin(angle)
                local_points.append((x, y, 0.0))
    except Exception as e:
        return []
    
    return local_points





@vulkan_compatible
def draw_center_dot_depth(context, light_obj, color, radius_pixels=5.0):
    """
    使用GLSL绘制中心圆点（灯光位置标记）
    兼容Vulkan和OpenGL后端
    """
    # 早期退出：如果透明度为0，不进行绘制以节省性能
    if len(color) >= 4 and color[3] <= 0.0:
        return
        
    region = context.region
    rv3d = context.region_data
    if not region or not rv3d:
        return
    
    shader = _get_center_dot_shader()
    if shader is None:
        return

    is_rendered_view = False
    try:
        space = context.space_data
        if space and space.type == 'VIEW_3D' and hasattr(space, "shading"):
            is_rendered_view = (space.shading.type == 'RENDERED')
    except Exception:
        is_rendered_view = False

    heavy_instances_scene = False
    if is_rendered_view:
        try:
            heavy_instances_scene = is_heavy_geometry_nodes_scene(context)
        except Exception:
            heavy_instances_scene = False

    depsgraph = None
    if is_rendered_view and not heavy_instances_scene:
        try:
            depsgraph = context.evaluated_depsgraph_get()
        except Exception:
            depsgraph = None

        if _is_point_occluded(context, region, rv3d, depsgraph, light_obj.location, light_obj):
            return

    batch = _build_center_dot_batch(light_obj.location, float(radius_pixels))
    if batch is None:
        return

    prev_depth_test = None
    prev_blend = None
    prev_depth_mask = None

    try:
        if hasattr(gpu.state, "depth_test_get"):
            prev_depth_test = gpu.state.depth_test_get()
        if hasattr(gpu.state, "blend_get"):
            prev_blend = gpu.state.blend_get()
        if hasattr(gpu.state, "depth_mask_get"):
            prev_depth_mask = gpu.state.depth_mask_get()
    except Exception:
        prev_depth_test = None
        prev_blend = None
        prev_depth_mask = None

    try:
        _vulkan_state_manager.set_blend_mode('ALPHA')
        if is_rendered_view:
            if heavy_instances_scene:
                _vulkan_state_manager.set_depth_test('LESS_EQUAL')
                if hasattr(gpu.state, "depth_mask_set"):
                    gpu.state.depth_mask_set(False)
            else:
                _vulkan_state_manager.set_depth_test('NONE')
        else:
            _vulkan_state_manager.set_depth_test('LESS_EQUAL')
            if hasattr(gpu.state, "depth_mask_set"):
                gpu.state.depth_mask_set(False)

        shader.bind()
        shader.uniform_float("ModelViewProjectionMatrix", rv3d.perspective_matrix)
        shader.uniform_float("u_color", color)
        shader.uniform_float("u_viewport", (region.width, region.height))
        batch.draw(shader)
    finally:
        if hasattr(gpu.state, "depth_mask_set") and prev_depth_mask is not None:
            try:
                gpu.state.depth_mask_set(prev_depth_mask)
            except Exception:
                pass
        if prev_depth_test is not None:
            try:
                _vulkan_state_manager.set_depth_test(prev_depth_test)
            except Exception:
                pass
        else:
            _vulkan_state_manager.set_depth_test('NONE')
        if prev_blend is not None:
            try:
                _vulkan_state_manager.set_blend_mode(prev_blend)
            except Exception:
                pass
        else:
            _vulkan_state_manager.set_blend_mode('NONE')


def _is_point_occluded(context, region, rv3d, depsgraph, point_3d, ignore_obj):
    if depsgraph is None:
        return False

    try:
        p2d = location_3d_to_region_2d(region, rv3d, point_3d)
        if p2d is None:
            return False

        origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, p2d)
        direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, p2d)
        if direction.length <= 1e-12:
            return False
        direction.normalize()

        t = (point_3d - origin).dot(direction)
        if t <= 1e-6:
            return False

        hit, hit_loc, hit_no, hit_index, hit_obj, hit_mat = context.scene.ray_cast(
            depsgraph, origin, direction, distance=max(0.0, t - 1e-4)
        )
        if not hit:
            return False
        if ignore_obj is not None and hit_obj == ignore_obj:
            return False
        return True
    except Exception:
        return False


def _get_center_dot_shader():
    shader = _DEPTH_OUTLINE_SHADER_CACHE.get("CENTER_DOT")
    if shader is not None:
        return shader

    if not hasattr(gpu, "types") or not hasattr(gpu.types, "GPUShaderCreateInfo"):
        _DEPTH_OUTLINE_SHADER_CACHE["CENTER_DOT"] = None
        return None
    if not hasattr(gpu.shader, "create_from_info"):
        _DEPTH_OUTLINE_SHADER_CACHE["CENTER_DOT"] = None
        return None

    info = gpu.types.GPUShaderCreateInfo()
    info.push_constant("MAT4", "ModelViewProjectionMatrix")
    info.vertex_in(0, "VEC3", "pos")
    info.vertex_in(1, "VEC2", "offset")
    info.vertex_in(2, "VEC2", "uv")
    info.push_constant("VEC4", "u_color")
    info.push_constant("VEC2", "u_viewport")
    info.fragment_out(0, "VEC4", "fragColor")

    interface = gpu.types.GPUStageInterfaceInfo("center_dot_interface")
    interface.smooth('VEC2', "var_uv")
    info.vertex_out(interface)

    info.vertex_source(
        """
        void main() {
            vec4 clip = ModelViewProjectionMatrix * vec4(pos, 1.0);
            vec2 ndc_offset = (offset * 2.0 / u_viewport) * clip.w;
            gl_Position = clip;
            gl_Position.xy += ndc_offset;
            var_uv = uv;
        }
        """
    )

    info.fragment_source(
        """
        void main() {
            float dist = length(var_uv);
            float alpha_edge = 1.0 - smoothstep(0.85, 1.0, dist);
            fragColor = vec4(u_color.rgb, u_color.a * alpha_edge);
        }
        """
    )

    try:
        shader = gpu.shader.create_from_info(info)
    except Exception:
        shader = None

    _DEPTH_OUTLINE_SHADER_CACHE["CENTER_DOT"] = shader
    return shader


def _build_center_dot_batch(center_3d, radius_pixels):
    segments = 32
    r = max(0.5, float(radius_pixels))

    pos = []
    offset = []
    uv = []
    indices = []

    pos.append((float(center_3d.x), float(center_3d.y), float(center_3d.z)))
    offset.append((0.0, 0.0))
    uv.append((0.0, 0.0))

    for i in range(segments + 1):
        a = TWO_PI * i / segments
        x = math.cos(a) * r
        y = math.sin(a) * r
        pos.append((float(center_3d.x), float(center_3d.y), float(center_3d.z)))
        offset.append((float(x), float(y)))
        uv.append((float(x / r), float(y / r)))

    for i in range(1, segments + 1):
        indices.append((0, i, i + 1))

    shader = _get_center_dot_shader()
    if shader is None:
        return None

    return create_compatible_batch(shader, 'TRIS', {"pos": pos, "offset": offset, "uv": uv}, indices=indices)


@vulkan_compatible
def draw_reflection_line_depth(context, hit_point, light_pos, color, opacity=1.0, thickness=1.0):
    """
    使用2D屏幕空间绘制从命中点到灯光的指示线
    不进行深度遮挡测试，确保线条始终可见且宽度一致
    兼容Vulkan和OpenGL
    """
    # 早期退出：如果透明度为0，不进行绘制
    if opacity <= 0.0:
        return
        
    region = context.region
    rv3d = context.region_data
    if not region or not rv3d:
        return

    # 获取视图矩阵和裁剪距离
    view_matrix = rv3d.view_matrix
    clip_start = 0.01 # 默认值
    
    # 获取正确的近裁剪面距离
    if context.space_data and context.space_data.type == 'VIEW_3D':
        # 如果是摄像机视图，使用摄像机的裁剪距离
        if rv3d.view_perspective == 'CAMERA' and context.space_data.camera:
            clip_start = context.space_data.camera.data.clip_start
        # 否则使用视口的裁剪距离
        elif hasattr(context.space_data, 'clip_start'):
            clip_start = context.space_data.clip_start
        
    # 优先尝试直接投影，如果成功则直接使用，避免不必要的裁剪
    # 只有当投影失败（点在相机后方）时才进行手动裁剪
    p1_2d = location_3d_to_region_2d(region, rv3d, hit_point)
    p2_2d = location_3d_to_region_2d(region, rv3d, light_pos)
    
    final_p1 = hit_point
    final_p2 = light_pos
    needs_clipping = False
    
    # 检查是否有点投影失败（即在视图后方）
    if p1_2d is None or p2_2d is None:
        needs_clipping = True
    
    # 只有在必要时才进行裁剪
    if needs_clipping:
        # 裁剪线段至近裁剪面
        clipped_points = _clip_line_segment_to_view(hit_point, light_pos, view_matrix, clip_start)
        
        if not clipped_points:
            return
            
        final_p1, final_p2 = clipped_points
        
        # 重新投影裁剪后的点
        p1_2d = location_3d_to_region_2d(region, rv3d, final_p1)
        p2_2d = location_3d_to_region_2d(region, rv3d, final_p2)
    
    # 如果仍然有无效点，则无法绘制
    if p1_2d is None or p2_2d is None:
        return
        
    draw_2d_lines_batch(context, [p1_2d, p2_2d], color, thickness, opacity)


@vulkan_compatible
def draw_2d_lines_batch(context, points_2d, color, thickness, opacity=1.0):
    """
    批量绘制2D线段
    points_2d: [p1, p2, p3, p4, ...] 格式的2D点列表
    """
    if not points_2d:
        return
        
    region = context.region
    
    # 3. 使用POLYLINE_UNIFORM_COLOR绘制高质量2D宽线
    try:
        # 尝试使用高质量2D线着色器（Blender 3.4+）
        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        
        batch = batch_for_shader(shader, 'LINES', {"pos": points_2d})
        
        shader.bind()
        # 设置颜色 (包含透明度)
        shader.uniform_float("color", (color[0], color[1], color[2], color[3] * opacity))
        # 设置线宽
        shader.uniform_float("lineWidth", thickness)
        # 设置视口尺寸 (用于抗锯齿计算)
        shader.uniform_float("viewportSize", (region.width, region.height))
        
        # 启用混合以支持透明度和抗锯齿
        gpu.state.blend_set('ALPHA')
        batch.draw(shader)
        gpu.state.blend_set('NONE')
        
    except Exception as e:
        # 回退方案：普通2D线
        try:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            batch = batch_for_shader(shader, 'LINES', {"pos": points_2d})
            
            shader.bind()
            shader.uniform_float("color", (color[0], color[1], color[2], color[3] * opacity))
            
            gpu.state.blend_set('ALPHA')
            gpu.state.line_width_set(thickness)
            batch.draw(shader)
            gpu.state.line_width_set(1.0)
            gpu.state.blend_set('NONE')
        except:
            pass


def _clip_line_segment_to_view(p1, p2, view_matrix, clip_start):
    """
    将线段(p1, p2)裁剪到视图近裁剪面
    返回裁剪后的世界坐标点(p1_clipped, p2_clipped)或None
    """
    # 转换到视图空间
    v1 = view_matrix @ p1
    v2 = view_matrix @ p2
    
    # 视图空间中，相机在原点，看向-Z方向
    # 近裁剪面在 z = -clip_start
    # 可见区域为 z < -clip_start
    actual_near_z = -clip_start
    
    # 检查点是否在近裁剪面后方 (z > actual_near_z)
    # 注意：Z轴向后，所以"后方"意味着Z值更大
    d1 = v1.z - actual_near_z
    d2 = v2.z - actual_near_z
    
    # 两个点都在近裁剪面后方，完全不可见
    if d1 > 0 and d2 > 0:
        return None
        
    # 两个点都在前方，完全可见，不需要裁剪
    if d1 <= 0 and d2 <= 0:
        return p1, p2
        
    # 一个在前后，一个在后，需要裁剪
    # 为了确保裁剪后的点能被location_3d_to_region_2d正确处理，
    # 我们使用一个稍微偏向可见区域的安全裁剪面
    safe_margin = 0.001 # 1mm安全距离
    safe_near_z = -(clip_start + safe_margin)
    
    # 如果可见点的Z值比安全裁剪面还要靠近相机（但在实际裁剪面内），
    # 说明整个可见线段都在"危险区域"，此时直接返回可见点作为起点/终点
    # 这种情况通常发生在非常靠近裁剪面的时候
    
    # 计算插值因子 t，使得 z(t) = safe_near_z
    # v1.z + t * (v2.z - v1.z) = safe_near_z
    denom = (v2.z - v1.z)
    if abs(denom) < 1e-6:
        return None # 平行于视平面，理论上不会进入此分支
        
    t = (safe_near_z - v1.z) / denom
    
    # 限制t在[0, 1]范围内，防止外插
    # 如果t超出范围，说明safe_near_z在这个线段之外（意味着可见点比safe_near_z更靠近相机）
    # 此时我们应该直接使用边界点
    
    if d1 > 0: # p1 在后方（不可见），裁剪 p1
        if t < 0 or t > 1:
             # safe_near_z不可达，说明p2虽然可见，但位于safe_near_z和actual_near_z之间
             # 这种情况下，我们尽量靠近actual_near_z
             # 再次尝试使用actual_near_z - small_epsilon
             fallback_z = actual_near_z - 1e-5
             t = (fallback_z - v1.z) / denom
             t = max(0.0, min(1.0, t))
             
        p_clip = p1.lerp(p2, t)
        return p_clip, p2
    else: # p2 在后方（不可见），裁剪 p2
        if t < 0 or t > 1:
             fallback_z = actual_near_z - 1e-5
             t = (fallback_z - v1.z) / denom
             t = max(0.0, min(1.0, t))
             
        p_clip = p1.lerp(p2, t)
        return p1, p_clip

# 导出函数供外部调用
__all__ = ['draw_light_outline_depth', 'draw_center_dot_depth', 'draw_reflection_line_depth', 'pixel_to_world_radius', 'draw_2d_lines_batch']
