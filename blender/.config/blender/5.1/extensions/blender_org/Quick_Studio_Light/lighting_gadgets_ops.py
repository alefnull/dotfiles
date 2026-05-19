import math
import time
import colorsys

import bpy
import blf
import gpu
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import PointerProperty
from bpy_extras import view3d_utils
from bpy_extras.view3d_utils import location_3d_to_region_2d
# Vulkan兼容性导入
from .vulkan_compat import (
    is_vulkan_backend,
    create_compatible_shader,
    create_compatible_batch,
    create_builtin_shader,
    VulkanCompatibleStateManager,
    vulkan_compatible,
    get_vulkan_manager
)

from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix

from .constants import (
    CIRCLE_SEGMENTS_HIGH, CIRCLE_SEGMENTS_MEDIUM, CIRCLE_SEGMENTS_LOW, CIRCLE_SEGMENTS_MINIMAL,
    LINE_SEGMENTS_DEFAULT, LINE_SEGMENTS_ANGLE, BORDER_SEGMENTS,
    CONTROL_POINT_RADIUS, LIGHT_OUTLINE_RADIUS,
    SCALE_FACTOR_HALF, SCALE_FACTOR_QUARTER, SCALE_FACTOR_TENTH, SCALE_FACTOR_HUNDREDTH, SCALE_FACTOR_THOUSANDTH,
    ALPHA_OPAQUE, ALPHA_SEMI_TRANSPARENT, ALPHA_TRANSPARENT, ALPHA_OCCLUDED, ALPHA_VISIBLE,
    PI, TWO_PI, HALF_PI, QUARTER_PI,
    PIXEL_WORLD_CACHE_MAX_SIZE, PIXEL_WORLD_CACHE_KEEP_SIZE,
    MULTI_FACE_SAMPLE_RADIUS, MULTI_FACE_SAMPLE_COUNT,
    FADE_DURATION_DEFAULT, DRAW_DURATION_DEFAULT, TIMER_INTERVAL_FAST, TIMER_INTERVAL_NORMAL,
    EPSILON_SMALL, EPSILON_TINY, EPSILON_ALIGN_POS, EPSILON_ALIGN_NORM,
    EDGE_THRESHOLD_DEFAULT,
    ANGLE_SIMILARITY_HIGH, ANGLE_SIMILARITY_MEDIUM, ANGLE_SIMILARITY_LOW,
    COLOR_YELLOW, COLOR_RED, COLOR_PURPLE, COLOR_GRAY_LIGHT, COLOR_GRAY_DARK,
    LAYOUT_SPLIT_FACTOR, LINE_HEIGHT_FACTOR, MARGIN_DEFAULT,
    TEXT_LENGTH_LONG, INPUT_COUNT_THRESHOLD,
    LIGHT_ENERGY_DEFAULT, LIGHT_SIZE_DEFAULT, LIGHT_SPOT_SIZE_DEFAULT, LIGHT_SPOT_BLEND_DEFAULT, LIGHT_RADIUS_DEFAULT,
    CLIP_END_DEFAULT, CLIP_START_DEFAULT,
    LERP_FACTOR_SMOOTH, LERP_FACTOR_NORMAL, LERP_FACTOR_FAST,
    RATIO_CHANGE_THRESHOLD, SMOOTHING_FACTOR
)

from .lighting_gadgets_utils import (
    update_light_transform, 
    calculate_hit_distance, 
    find_closest_surface_point, 
    update_light_precise_transform, 
    is_point_occluded,
    calculate_light_orientation,
    check_light_linking,
    find_visible_hit,
    is_light_visible_and_in_view_layer,
    calculate_average_normal,
    is_heavy_geometry_nodes_scene,
    get_light_world_location,
    set_light_world_orientation,
    set_light_world_location
)

# 导入深度轮廓描边实现
from .lighting_gadgets_depth_outline import (
    draw_light_outline_depth,
    draw_center_dot_depth,
    draw_reflection_line_depth,
    pixel_to_world_radius,
    draw_2d_lines_batch,
    draw_crosshair_glsl
)

_QSL_SHADER_CACHE = {}
_QSL_BATCH_CACHE = {}

def _get_smooth_color_shader():
    shader = _QSL_SHADER_CACHE.get("CUSTOM_SMOOTH_COLOR")
    if shader is not None:
        return shader

    if not hasattr(gpu, "types") or not hasattr(gpu.types, "GPUShaderCreateInfo"):
        return None

    info = gpu.types.GPUShaderCreateInfo()
    info.push_constant("MAT4", "ModelViewProjectionMatrix")
    info.vertex_in(0, "VEC2", "pos")
    info.vertex_in(1, "VEC4", "color")
    info.fragment_out(0, "VEC4", "fragColor")

    interface = gpu.types.GPUStageInterfaceInfo("smooth_color_interface")
    interface.smooth('VEC4', "v_color")
    info.vertex_out(interface)

    info.vertex_source(
        """
        void main() {
            gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
            v_color = color;
        }
        """
    )

    info.fragment_source(
        """
        void main() {
            fragColor = v_color;
        }
        """
    )

    try:
        shader = gpu.shader.create_from_info(info)
    except Exception:
        shader = None

    _QSL_SHADER_CACHE["CUSTOM_SMOOTH_COLOR"] = shader
    return shader


def _get_rainbow_border_shader():
    shader = _QSL_SHADER_CACHE.get("RAINBOW_BORDER")
    if shader is not None:
        return shader

    if not hasattr(gpu, "types") or not hasattr(gpu.types, "GPUShaderCreateInfo"):
        _QSL_SHADER_CACHE["RAINBOW_BORDER"] = None
        return None

    info = gpu.types.GPUShaderCreateInfo()
    info.push_constant("MAT4", "ModelViewProjectionMatrix")
    info.vertex_in(0, "VEC2", "pos")
    info.vertex_in(1, "VEC2", "uv")
    info.push_constant("FLOAT", "u_time")
    info.push_constant("FLOAT", "u_alpha")
    info.fragment_out(0, "VEC4", "fragColor")

    interface = gpu.types.GPUStageInterfaceInfo("rainbow_interface")
    interface.smooth('VEC2', "var_uv")
    info.vertex_out(interface)

    info.vertex_source(
        """
        void main() {
            gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
            var_uv = uv;
        }
        """
    )

    info.fragment_source(
        """
        vec3 hsv2rgb(vec3 c) {
            vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
            vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
            return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
        }

        void main() {
            float v_progress = fract(var_uv.x);
            float v_side = var_uv.y;

            float tau = 6.28318530718;
            float t = u_time * 0.5;
            float flow_phase = t * 3.0 - v_progress * tau;
            float hue = fract(flow_phase / tau);

            float saturation = 0.9;
            float value = 0.95;

            float pulse_t = u_time * 1.0;
            float pulse_center = fract(pulse_t);
            float raw_dist = fract(pulse_center - v_progress);
            float pulse = 0.0;

            if (raw_dist > 0.5) {
                float front_dist = 1.0 - raw_dist;
                pulse = exp(-(front_dist * front_dist) / (2.0 * 0.01 * 0.01));
            } else {
                pulse = exp(-(raw_dist * raw_dist) / (2.0 * 0.2 * 0.2));
            }

            float boost = 1.0 + 0.6 * pulse;
            float sat_damp = 1.0 - 0.2 * pulse;

            vec3 rgb = hsv2rgb(vec3(hue, saturation * sat_damp, min(1.0, value * boost)));

            float dist = abs(v_side);
            float alpha_edge = 1.0 - smoothstep(0.85, 1.0, dist);
            fragColor = vec4(rgb, u_alpha * alpha_edge);
        }
        """
    )

    try:
        shader = gpu.shader.create_from_info(info)
    except Exception:
        shader = None

    _QSL_SHADER_CACHE["RAINBOW_BORDER"] = shader
    return shader

def _get_pulse_border_shader():
    shader = _QSL_SHADER_CACHE.get("PULSE_BORDER")
    if shader is not None:
        return shader

    if not hasattr(gpu, "types") or not hasattr(gpu.types, "GPUShaderCreateInfo"):
        _QSL_SHADER_CACHE["PULSE_BORDER"] = None
        return None

    info = gpu.types.GPUShaderCreateInfo()
    info.push_constant("MAT4", "ModelViewProjectionMatrix")
    info.vertex_in(0, "VEC2", "pos")
    info.vertex_in(1, "VEC2", "uv")
    info.push_constant("FLOAT", "u_time")
    info.push_constant("VEC4", "u_color")
    info.fragment_out(0, "VEC4", "fragColor")

    interface = gpu.types.GPUStageInterfaceInfo("pulse_interface")
    interface.smooth('VEC2', "var_uv")
    info.vertex_out(interface)

    info.vertex_source(
        """
        void main() {
            gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
            var_uv = uv;
        }
        """
    )

    info.fragment_source(
        """
        void main() {
            float v_progress = fract(var_uv.x);
            float v_side = var_uv.y;

            float tau = 6.28318530718;
            float t = u_time;

            float pulse_t = t * 0.4;
            float pulse_center = fract(pulse_t);
            float raw_dist = fract(pulse_center - v_progress);
            float pulse = 0.0;

            if (raw_dist > 0.5) {
                float front_dist = 1.0 - raw_dist;
                pulse = exp(-(front_dist * front_dist) / (2.0 * 0.012 * 0.012));
            } else {
                pulse = exp(-(raw_dist * raw_dist) / (2.0 * 0.22 * 0.22));
            }

            float dist = abs(v_side);
            float alpha_edge = 1.0 - smoothstep(0.85, 1.0, dist);

            float boost = 1.0 + 1.5 * pulse;
            vec3 rgb = min(vec3(1.0), u_color.rgb * boost);

            float a = u_color.a * alpha_edge * (0.6 + 0.4 * pulse);
            fragColor = vec4(rgb, a);
        }
        """
    )

    try:
        shader = gpu.shader.create_from_info(info)
    except Exception:
        shader = None

    _QSL_SHADER_CACHE["PULSE_BORDER"] = shader
    return shader

def _rounded_rect_path(x0, y0, x1, y1, radius, corner_segments):
    w = max(0.0, float(x1) - float(x0))
    h = max(0.0, float(y1) - float(y0))
    r = max(0.0, float(radius))
    r = min(r, w * 0.5, h * 0.5)

    if r <= 1e-6:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    seg = int(max(1, corner_segments))

    def arc(cx, cy, a0, a1):
        pts = []
        for i in range(seg + 1):
            t = i / seg
            a = a0 + (a1 - a0) * t
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        return pts

    pts = []
    pts.append((x0 + r, y0))
    pts.append((x1 - r, y0))
    pts.extend(arc(x1 - r, y0 + r, -math.pi * 0.5, 0.0)[1:])
    pts.append((x1, y1 - r))
    pts.extend(arc(x1 - r, y1 - r, 0.0, math.pi * 0.5)[1:])
    pts.append((x0 + r, y1))
    pts.extend(arc(x0 + r, y1 - r, math.pi * 0.5, math.pi)[1:])
    pts.append((x0, y0 + r))
    pts.extend(arc(x0 + r, y0 + r, math.pi, math.pi * 1.5)[1:])

    return pts

def _expand_closed_polyline_strip(points, width_px):
    if not points or len(points) < 3:
        return [], []

    half_w = max(0.5, float(width_px) * 0.5)
    verts = [Vector((p[0], p[1])) for p in points]
    n = len(verts)

    total_len = 0.0
    seg_lens = []
    for i in range(n):
        a = verts[i]
        b = verts[(i + 1) % n]
        d = (b - a).length
        seg_lens.append(d)
        total_len += d

    if total_len <= 1e-8:
        return [], []

    cum = [0.0] * n
    acc = 0.0
    for i in range(1, n):
        acc += seg_lens[i - 1]
        cum[i] = acc

    pos_data = []
    uv_data = []

    for i in range(n):
        prev_p = verts[(i - 1) % n]
        curr_p = verts[i]
        next_p = verts[(i + 1) % n]

        v1 = curr_p - prev_p
        v2 = next_p - curr_p

        t1 = v1.normalized() if v1.length > 1e-8 else None
        t2 = v2.normalized() if v2.length > 1e-8 else None

        if t1 and t2:
            tangent = (t1 + t2)
            if tangent.length <= 1e-8:
                tangent = t2
            else:
                tangent.normalize()
        elif t2:
            tangent = t2
        elif t1:
            tangent = t1
        else:
            continue

        normal = Vector((-tangent.y, tangent.x))
        p0 = curr_p + normal * half_w
        p1 = curr_p - normal * half_w

        u = cum[i] / total_len
        pos_data.append((p0.x, p0.y))
        pos_data.append((p1.x, p1.y))
        uv_data.append((u, 1.0))
        uv_data.append((u, -1.0))

    if pos_data:
        pos_data.append(pos_data[0])
        pos_data.append(pos_data[1])
        uv_data.append((1.0, 1.0))
        uv_data.append((1.0, -1.0))

    return pos_data, uv_data

def _draw_rainbow_border_glsl(context, thickness, alpha):
    if alpha <= 0.0:
        return False

    region = getattr(context, "region", None)
    width = region.width if region else context.area.width
    height = region.height if region else context.area.height
    t = max(1.0, float(thickness))

    shader = _get_rainbow_border_shader()
    if not shader:
        return False

    # 检查缓存
    cache_key = ("RAINBOW_BORDER", width, height, t)
    batch = _QSL_BATCH_CACHE.get(cache_key)

    if batch is None:
        half = t * 0.5
        x0 = 0.0 + half
        y0 = 0.0 + half
        x1 = max(x0, float(width) - half)
        y1 = max(y0, float(height) - half)

        corner_r = max(1.0, t * 0.75)
        seg = max(6, min(48, int(corner_r * 0.6)))
        points = _rounded_rect_path(x0, y0, x1, y1, corner_r, seg)
        pos_data, uv_data = _expand_closed_polyline_strip(points, t)
        if not pos_data:
            return False

        try:
            batch = batch_for_shader(shader, "TRI_STRIP", {"pos": pos_data, "uv": uv_data})
            # 简单缓存管理: 如果缓存过大则清理
            if len(_QSL_BATCH_CACHE) > 10:
                keys_to_remove = [k for k in _QSL_BATCH_CACHE.keys() if k[0] == "RAINBOW_BORDER"]
                for k in keys_to_remove:
                    del _QSL_BATCH_CACHE[k]
            _QSL_BATCH_CACHE[cache_key] = batch
        except Exception:
            return False

    try:
        shader.bind()
        shader.uniform_float("u_time", time.time() % 1000.0)
        shader.uniform_float("u_alpha", float(alpha))

        _vulkan_state_manager.set_blend_mode("ALPHA")
        batch.draw(shader)
    except Exception:
        return False
    finally:
        _vulkan_state_manager.set_blend_mode("NONE")

    return True

def _draw_pulse_border_glsl(context, thickness, color):
    if len(color) >= 4 and color[3] <= 0.0:
        return False

    region = getattr(context, "region", None)
    width = region.width if region else context.area.width
    height = region.height if region else context.area.height
    t = max(1.0, float(thickness))

    shader = _get_pulse_border_shader()
    if not shader:
        return False

    # 检查缓存
    cache_key = ("PULSE_BORDER", width, height, t)
    batch = _QSL_BATCH_CACHE.get(cache_key)

    if batch is None:
        half = t * 0.5
        x0 = 0.0 + half
        y0 = 0.0 + half
        x1 = max(x0, float(width) - half)
        y1 = max(y0, float(height) - half)

        corner_r = max(1.0, t * 0.75)
        seg = max(6, min(48, int(corner_r * 0.6)))
        points = _rounded_rect_path(x0, y0, x1, y1, corner_r, seg)
        pos_data, uv_data = _expand_closed_polyline_strip(points, t)
        if not pos_data:
            return False

        try:
            batch = batch_for_shader(shader, "TRI_STRIP", {"pos": pos_data, "uv": uv_data})
            # 简单缓存管理
            if len(_QSL_BATCH_CACHE) > 10:
                keys_to_remove = [k for k in _QSL_BATCH_CACHE.keys() if k[0] == "PULSE_BORDER"]
                for k in keys_to_remove:
                    del _QSL_BATCH_CACHE[k]
            _QSL_BATCH_CACHE[cache_key] = batch
        except Exception:
            return False

    if len(color) == 3:
        col = (float(color[0]), float(color[1]), float(color[2]), 1.0)
    else:
        col = (float(color[0]), float(color[1]), float(color[2]), float(color[3]))

    try:
        shader.bind()
        shader.uniform_float("u_time", time.time() % 1000.0)
        shader.uniform_float("u_color", col)

        _vulkan_state_manager.set_blend_mode("ALPHA")
        batch.draw(shader)
    except Exception:
        return False
    finally:
        _vulkan_state_manager.set_blend_mode("NONE")

    return True

def _draw_rainbow_border_gradient(context, thickness, alpha=1.0, segments=12):
    try:
        if alpha <= 0.0:
            return

        width = context.area.width
        height = context.area.height
        t = max(1.0, float(thickness))

        stops = []
        for i in range(segments + 1):
            frac = i / segments
            r, g, b = colorsys.hsv_to_rgb(frac, 1.0, 1.0)
            stops.append((frac, (r, g, b, alpha)))

        draw_gradient_rect(0.0, 0.0, float(width), t, stops, orientation='horizontal')
        draw_gradient_rect(0.0, float(height) - t, float(width), float(height), stops, orientation='horizontal')
        draw_gradient_rect(0.0, t, t, float(height) - t, stops, orientation='vertical')
        draw_gradient_rect(float(width) - t, t, float(width), float(height) - t, stops, orientation='vertical')
    except Exception:
        pass


# 全局Vulkan状态管理器
_vulkan_state_manager = get_vulkan_manager()

# 状态管理器类 - 封装所有全局状态，避免跨函数的隐式依赖
class LightingGadgetsStateManager:
    """管理所有灯光工具的全局状态"""
    
    def __init__(self):
        self._studio_light_controls_handle = None
        self._modal_operator_running = False
        self._modal_session_id = 0
        self._original_visibility = {}
        self._original_ui_state = {}
        self._temp_disabled_light = None
        self._original_energy = None
        self._world_output_node = None
        self._world_output_muted = False
        self._performance_material = None
        self._original_material_override = None
        self._solo_mode = False
        self._active_area = None  # 记录激活视口
        
        # 循环选择灯光的状态变量
        self._light_selection_candidates = []  # 候选灯光列表
        self._light_selection_current_index = 0  # 当前选择索引
        self._light_selection_last_hit_location = None  # 上次命中位置
        self._light_selection_last_view_matrix = None  # 上次视图矩阵
        
        # 灯光颜色闪烁状态
        self._temp_color_lights = {}  # {灯光名称: {'原始颜色': (r,g,b), '恢复时间': 时间戳}}
        self._restore_colors_timer = None
    
    # 属性访问器
    @property
    def studio_light_controls_handle(self):
        return self._studio_light_controls_handle
    
    @studio_light_controls_handle.setter
    def studio_light_controls_handle(self, value):
        self._studio_light_controls_handle = value
    
    @property
    def modal_operator_running(self):
        return self._modal_operator_running
    
    @modal_operator_running.setter
    def modal_operator_running(self, value):
        self._modal_operator_running = value

    @property
    def modal_session_id(self):
        return self._modal_session_id
    
    @modal_session_id.setter
    def modal_session_id(self, value):
        self._modal_session_id = int(value)
    
    @property
    def original_visibility(self):
        return self._original_visibility
    
    @property
    def original_ui_state(self):
        return self._original_ui_state
    
    @property
    def temp_disabled_light(self):
        return self._temp_disabled_light
    
    @temp_disabled_light.setter
    def temp_disabled_light(self, value):
        self._temp_disabled_light = value
    
    @property
    def original_energy(self):
        return self._original_energy
    
    @original_energy.setter
    def original_energy(self, value):
        self._original_energy = value
    
    @property
    def world_output_node(self):
        return self._world_output_node
    
    @world_output_node.setter
    def world_output_node(self, value):
        self._world_output_node = value
    
    @property
    def world_output_muted(self):
        return self._world_output_muted
    
    @world_output_muted.setter
    def world_output_muted(self, value):
        self._world_output_muted = value
    
    @property
    def performance_material(self):
        return self._performance_material
    
    @performance_material.setter
    def performance_material(self, value):
        self._performance_material = value
    
    @property
    def original_material_override(self):
        return self._original_material_override
    
    @original_material_override.setter
    def original_material_override(self, value):
        self._original_material_override = value
    
    @property
    def solo_mode(self):
        return self._solo_mode
    
    @solo_mode.setter
    def solo_mode(self, value):
        self._solo_mode = value
    
    @property
    def active_area(self):
        return self._active_area
    
    @active_area.setter
    def active_area(self, value):
        self._active_area = value
    
    @property
    def light_selection_candidates(self):
        return self._light_selection_candidates
    
    @light_selection_candidates.setter
    def light_selection_candidates(self, value):
        self._light_selection_candidates = value
    
    @property
    def light_selection_current_index(self):
        return self._light_selection_current_index
    
    @light_selection_current_index.setter
    def light_selection_current_index(self, value):
        self._light_selection_current_index = value
    
    @property
    def light_selection_last_hit_location(self):
        return self._light_selection_last_hit_location
    
    @light_selection_last_hit_location.setter
    def light_selection_last_hit_location(self, value):
        self._light_selection_last_hit_location = value
    
    @property
    def light_selection_last_view_matrix(self):
        return self._light_selection_last_view_matrix
    
    @light_selection_last_view_matrix.setter
    def light_selection_last_view_matrix(self, value):
        self._light_selection_last_view_matrix = value
    
    def set_temp_color(self, light_data, color, duration):
        """设置灯光临时颜色，并在指定时间后恢复"""
        if not light_data:
            return
            
        current_time = time.time()
        restore_time = current_time + duration
        
        # 使用灯光数据名称作为键
        name = light_data.name
        
        # 如果已经在临时状态，只需更新恢复时间
        if name in self._temp_color_lights:
            self._temp_color_lights[name]['restore_time'] = restore_time
            # 重新应用颜色，以防万一
            light_data.color = color
        else:
            # 保存原始颜色
            self._temp_color_lights[name] = {
                'original_color': light_data.color.copy(),
                'restore_time': restore_time
            }
            # 设置新颜色
            light_data.color = color
            
            # 如果这是列表中的第一个灯光，启动检查计时器
            # 使用 bpy.app.timers 确保即使操作符结束也能恢复颜色
            if len(self._temp_color_lights) == 1:
                if self._restore_colors_timer is None:
                    self._restore_colors_timer = self._check_restore_colors_timer
                if not bpy.app.timers.is_registered(self._restore_colors_timer):
                    bpy.app.timers.register(self._restore_colors_timer)

    def _check_restore_colors_timer(self):
        """计时器回调：检查并恢复颜色"""
        if not self._temp_color_lights:
            return None # 停止计时器
            
        current_time = time.time()
        restored_lights = []
        
        for name, data in self._temp_color_lights.items():
            if current_time >= data['restore_time']:
                # 正确从 bpy.data.lights 获取灯光数据
                light_data = bpy.data.lights.get(name)
                if light_data:
                    try:
                        light_data.color = data['original_color']
                    except:
                        pass
                restored_lights.append(name)
        
        # 从字典中移除已恢复的灯光
        for name in restored_lights:
            del self._temp_color_lights[name]
            
        # 如果还有待恢复的灯光，继续运行计时器 (0.05s 检查一次)
        if self._temp_color_lights:
            return 0.05
            
        return None # 停止计时器

    def check_restore_colors(self):
        """检查并恢复需要恢复颜色的灯光"""
        # 手动调用一次计时器逻辑（用于兼容性或立即更新）
        self._check_restore_colors_timer()

    def clear_all_states(self):
        """清理所有状态 - 在操作符退出时调用"""
        
        # 立即恢复所有临时颜色的灯光
        if self._temp_color_lights:
            for name, data in self._temp_color_lights.items():
                light_data = bpy.data.lights.get(name)
                if light_data:
                    try:
                        light_data.color = data['original_color']
                    except:
                        pass
            self._temp_color_lights.clear()

        if self._restore_colors_timer is not None:
            try:
                if bpy.app.timers.is_registered(self._restore_colors_timer):
                    bpy.app.timers.unregister(self._restore_colors_timer)
            except Exception:
                pass
            self._restore_colors_timer = None
            
        # 清理绘制句柄 - 增强错误处理和资源释放
        if self._studio_light_controls_handle is not None:
            try:
                bpy.types.SpaceView3D.draw_handler_remove(self._studio_light_controls_handle, 'WINDOW')
            except Exception as e:
                # 尝试备用清理方法
                try:
                    # 检查句柄是否仍然有效
                    if hasattr(bpy.types.SpaceView3D, 'draw_handler_remove'):
                        # 尝试重新注册并立即移除
                        temp_handle = bpy.types.SpaceView3D.draw_handler_add(lambda: None, (), 'WINDOW', 'POST_PIXEL')
                        bpy.types.SpaceView3D.draw_handler_remove(temp_handle, 'WINDOW')
                except Exception as e2:
                    pass
            finally:
                self._studio_light_controls_handle = None
        
        # 清理临时灯光状态
        if self._temp_disabled_light and self._original_energy is not None:
            try:
                # 检查灯光对象是否仍然有效
                if hasattr(self._temp_disabled_light, 'data') and hasattr(self._temp_disabled_light.data, 'energy'):
                    self._temp_disabled_light.data.energy = self._original_energy
            except Exception as e:
                pass
            finally:
                self._temp_disabled_light = None
                self._original_energy = None
        
        # 恢复世界输出节点
        if self._world_output_node is not None:
            try:
                # 检查节点是否仍然有效
                if hasattr(self._world_output_node, 'mute'):
                    self._world_output_node.mute = self._world_output_muted
            except Exception as e:
                pass
            finally:
                self._world_output_node = None
                self._world_output_muted = False
        
        # 重置状态变量
        self._modal_operator_running = False
        self._original_visibility.clear()
        self._original_ui_state.clear()
        self._solo_mode = False
        self._active_area = None  # 重置激活视口记录
        
        # 注意：不重置循环选择状态变量，以支持多次调用操作符时的循环选择功能
        # self._light_selection_candidates = []  # 候选灯光列表
        # self._light_selection_current_index = 0  # 当前选择索引
        # self._light_selection_last_hit_location = None  # 上次命中位置
        # self._light_selection_last_view_matrix = None  # 上次视图矩阵
        
        # 清理材质覆盖 - 确保材质被正确删除
        if self._original_material_override is not None:
            self._original_material_override = None
            
        if self._performance_material is not None:
            # 检查材质是否在bpy.data中，如果是则删除
            try:
                if (hasattr(self._performance_material, 'name') and 
                    self._performance_material.name in bpy.data.materials):
                    bpy.data.materials.remove(self._performance_material)
                else:
                    # 如果材质不在bpy.data中，尝试其他清理方法
                    self._performance_material.user_clear()
                    self._performance_material = None
            except Exception as e:
                # 确保无论如何都设置为None
                self._performance_material = None
        
        # 强制垃圾回收
        try:
            import gc
            gc.collect()
        except Exception as e:
            pass
        
        # 添加资源泄漏检测
        self._check_resource_leaks()
    
    def _check_resource_leaks(self):
        """检查资源泄漏"""
        # 生产版本中不输出调试信息，仅执行检查逻辑
        leaks_found = False
        
        # 检查绘制句柄是否已清理
        if self._studio_light_controls_handle is not None:
            leaks_found = True
        
        # 检查材质是否已清理
        if self._performance_material is not None:
            leaks_found = True
        
        # 检查其他资源
        if self._temp_disabled_light is not None:
            leaks_found = True
            
        if self._world_output_node is not None:
            leaks_found = True


# 创建全局状态管理器实例
_state_manager = LightingGadgetsStateManager()

def update_studio_light_controls_display(self, context):
    """更新灯光操控点显示状态"""
    global _state_manager
    
    if self.show_studio_light_controls:
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        if not (area and area.type == 'VIEW_3D' and region and rv3d):
            return
        # 启用灯光操控点显示
        if _state_manager.studio_light_controls_handle is None:
            # 记录激活视口
            _state_manager.active_area = context.area
            _state_manager.studio_light_controls_handle = bpy.types.SpaceView3D.draw_handler_add(
                draw_studio_light_controls, (context,), 'WINDOW', 'POST_PIXEL'
            )
            # 只有在模态操作符未运行时才启动
            if not _state_manager.modal_operator_running:
                bpy.ops.lighting_gadgets.studio_light_control_modal('INVOKE_DEFAULT')
            # 强制刷新视图
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
    else:
        # 禁用灯光操控点显示
        if _state_manager.studio_light_controls_handle is not None:
            # 检查当前上下文是否在3D视图中，避免在其他空间类型中移除区域类型
            if hasattr(context, 'area') and context.area and context.area.type == 'VIEW_3D':
                bpy.types.SpaceView3D.draw_handler_remove(_state_manager.studio_light_controls_handle, 'WINDOW')
            _state_manager.studio_light_controls_handle = None
            # 重置模态操作符状态
            _state_manager.modal_session_id += 1
            _state_manager.modal_operator_running = False
            # 恢复临时关闭的灯光强度
            if _state_manager.temp_disabled_light and _state_manager.original_energy is not None:
                _state_manager.temp_disabled_light.data.energy = _state_manager.original_energy
                _state_manager.temp_disabled_light = None
                _state_manager.original_energy = None
            # 恢复UI元素（工具栏、侧面板、覆盖层、小工具）
            restore_ui_elements(context, target_area=context.area)
            # 强制刷新视图
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        # 恢复所有灯光的可见性
        restore_all_lights_visibility()

@vulkan_compatible
def draw_studio_light_controls(context):
    """绘制所有灯光的操控点（最前显示，不使用深度测试）"""
    global _state_manager
    
    # 即使是极短的sleep(0.0015)也能触发布局/绘制线程的上下文切换，
    # 显著减少输入延迟，让操作更"跟手"
    # 无论是否绘制文本，这个让步必须执行
    if is_vulkan_backend():
        time.sleep(0.0015)  # Vulkan后端需要让步以避免Cycles渲染卡顿
    # time.sleep(0.0015)  # 移除 sleep 以避免影响帧率
    
    # 只在激活视口绘制，减少性能开销
    if not hasattr(_state_manager, 'active_area') or context.area != _state_manager.active_area:

        return
    
    # 获取3D视图的区域和空间
    region = context.region
    rv3d = context.region_data
    
    if not region or not rv3d:
        return
    
    # 获取插件首选项中的颜色设置
    try:
        prefs = context.preferences.addons[__package__].preferences
        control_color = (*prefs.studio_light_control_color, 0.8)  # 添加透明度
    except:
        control_color = (1.0, 1.0, 0.0, 0.8)  # 默认黄色，如果获取首选项失败
    
    # 使用Vulkan兼容的状态管理
    _vulkan_state_manager.set_blend_mode('ALPHA')
    _vulkan_state_manager.set_depth_test('NONE')  # 禁用深度测试
    
    # 创建着色器（使用兼容的创建方法）
    uniform_shader = create_builtin_shader('UNIFORM_COLOR')
    if uniform_shader is None:
        return
    
    try:
        selected_objects = getattr(context, "selected_objects", None) or []
        for obj in selected_objects:
            if obj.type == 'LIGHT' and obj.visible_get():
                # 将3D坐标转换为2D屏幕坐标
                world_pos = obj.matrix_world.translation
                screen_pos = location_3d_to_region_2d(
                    region, rv3d, world_pos
                )
                
                if screen_pos:
                    # 绘制实心圆形操控点，使用自定义颜色
                    draw_solid_circle(screen_pos, CONTROL_POINT_RADIUS, control_color, uniform_shader)
                    
                    # 灯光独显时只显示核心黄点，不绘制轮廓边缘
    
    except Exception as e:
        print(f"Vulkan兼容操控点绘制失败: {e}")
    
    finally:
        # 恢复GPU状态
        _vulkan_state_manager.set_blend_mode('NONE')
        _vulkan_state_manager.set_depth_test('NONE')

@vulkan_compatible
def draw_solid_circle(center, radius, color, shader):
    """绘制实心圆形，兼容Vulkan和OpenGL"""
    # 生成圆形顶点
    vertices = [center]  # 中心点
    segments = CIRCLE_SEGMENTS_HIGH
    for i in range(segments + 1):
        angle = TWO_PI * i / segments
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        vertices.append((x, y))
    
    # 生成三角形索引
    indices = []
    for i in range(segments):
        indices.append((0, i + 1, i + 2))
    
    # 使用兼容的批次创建
    batch = create_compatible_batch(shader, 'TRIS', {"pos": vertices}, indices=indices)
    if batch is None:
        return
    
    # 绑定着色器并绘制
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


@vulkan_compatible
def draw_stroke_circle_2d(context, center, radius_px, color, thickness=1):
    """在屏幕空间绘制描边圆（用于fallback），兼容Vulkan和OpenGL"""
    # 准备2D线段点列表 [p1, p2, p2, p3, ...]
    segments = 64
    points_2d = []
    cx, cy = center
    
    # 生成圆周点
    circle_points = []
    for i in range(segments + 1):
        angle = 2.0 * math.pi * i / segments
        x = cx + radius_px * math.cos(angle)
        y = cy + radius_px * math.sin(angle)
        circle_points.append((x, y))
        
    # 转换为线段对
    for i in range(len(circle_points) - 1):
        points_2d.extend([circle_points[i], circle_points[i+1]])
        
    # 使用新的高质量2D线绘制函数
    try:
        # 如果颜色是(r,g,b)格式，添加alpha=1.0
        draw_color = list(color)
        if len(draw_color) == 3:
            draw_color.append(1.0)
            
        draw_2d_lines_batch(context, points_2d, draw_color, thickness, draw_color[3])
    except Exception as e:
        print(f"描边圆绘制失败: {e}")





def restore_all_lights_visibility():
    """恢复所有灯光的原始可见性"""
    global _state_manager
    
    for obj_name, visibility in _state_manager.original_visibility.items():
        obj = bpy.data.objects.get(obj_name)
        if obj and obj.type == 'LIGHT':
            obj.hide_viewport = not visibility
    
    _state_manager.original_visibility.clear()

def hide_ui_elements(context):
    """隐藏UI元素（工具栏、侧面板、覆盖层、小工具）- 只影响当前活动的3D视口（使用状态栈，且幂等）"""
    global _state_manager
    
    # 获取插件首选项
    try:
        prefs = context.preferences.addons[__package__].preferences
    except Exception:
        return  # 如果无法获取首选项，直接返回
    
    # 只对当前活动的3D视口进行操作
    if not (context.area and context.area.type == 'VIEW_3D' and isinstance(context.space_data, bpy.types.SpaceView3D)):
        return
    
    space = context.space_data
    area_ptr = context.area.as_pointer()
    
    # 为该视口建立状态栈
    if area_ptr not in _state_manager.original_ui_state:
        _state_manager.original_ui_state[area_ptr] = []
    
    saved = {}
    
    # 隐藏工具栏和侧面板（仅在状态发生变化时保存并修改）
    if getattr(prefs, 'hide_all_overlays_in_lighting', False):
        if space.show_region_toolbar:
            saved['toolbar'] = space.show_region_toolbar
            space.show_region_toolbar = False
        if space.show_region_ui:
            saved['ui'] = space.show_region_ui
            space.show_region_ui = False
    
    # 隐藏覆盖层和小工具（仅在状态发生变化时保存并修改）
    if getattr(prefs, 'hide_all_overlays_in_lighting', False):
        if space.overlay.show_overlays:
            saved['overlays'] = space.overlay.show_overlays
            space.overlay.show_overlays = False
        if space.show_gizmo:
            saved['gizmo'] = space.show_gizmo
            space.show_gizmo = False
        # 隐藏线框叠加
        if space.overlay.show_wireframes:
            saved['wireframes'] = space.overlay.show_wireframes
            space.overlay.show_wireframes = False
    
    # 如果本次确实有修改，则压入栈
    if saved:
        _state_manager.original_ui_state[area_ptr].append(saved)
    
    # 对所有3D视口处理线框叠加（多视口支持）
    if getattr(prefs, 'hide_all_overlays_in_lighting', False):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if isinstance(space, bpy.types.SpaceView3D):
                        area_ptr = area.as_pointer()
                        # 为该视口建立状态栈（如果不存在）
                        if area_ptr not in _state_manager.original_ui_state:
                            _state_manager.original_ui_state[area_ptr] = []
                        
                        # 检查是否已经保存过该视口的状态
                        saved_for_area = None
                        for saved_state in _state_manager.original_ui_state[area_ptr]:
                            if 'wireframes' in saved_state:
                                saved_for_area = saved_state
                                break
                        
                        # 如果没有保存过线框状态，则保存并修改
                        if saved_for_area is None and space.overlay.show_wireframes:
                            new_saved = {'wireframes': space.overlay.show_wireframes}
                            space.overlay.show_wireframes = False
                            _state_manager.original_ui_state[area_ptr].append(new_saved)

def restore_ui_elements(context, target_area=None):
    """恢复UI元素的原始状态 - 支持多视口恢复（修复线框叠加层恢复问题）"""
    global _state_manager
    
    # 如果指定了目标区域，只恢复该区域
    if target_area is not None:
        areas_to_restore = [target_area]
    else:
        # 如果没有指定目标区域，恢复所有3D视口
        areas_to_restore = [area for area in context.screen.areas if area.type == 'VIEW_3D']
    
    for area in areas_to_restore:
        if not (area and area.type == 'VIEW_3D'):
            continue
        
        # 找到该区域对应的SpaceView3D
        space = None
        for sp in area.spaces:
            if isinstance(sp, bpy.types.SpaceView3D):
                space = sp
                break
        if space is None:
            continue
        
        area_ptr = area.as_pointer()
        
        # 从栈中取出最近一次保存的状态
        stack = _state_manager.original_ui_state.get(area_ptr)
        if not stack:
            continue
        
        saved = stack.pop()
        
        # 恢复工具栏和侧面板
        if 'toolbar' in saved:
            space.show_region_toolbar = saved['toolbar']
        if 'ui' in saved:
            space.show_region_ui = saved['ui']
        
        # 恢复覆盖层和小工具
        if 'overlays' in saved:
            space.overlay.show_overlays = saved['overlays']
        if 'gizmo' in saved:
            space.show_gizmo = saved['gizmo']
        # 恢复线框叠加
        if 'wireframes' in saved:
            space.overlay.show_wireframes = saved['wireframes']
        
        # 如果栈清空了，移除该视口的记录
        if not stack:
            del _state_manager.original_ui_state[area_ptr]

def create_performance_material():
    """创建性能模式材质：光泽BSDF(#BCBCBCFF)与透明BSDF(#7C7C7CFF)混合，系数由光程的射线深度>0控制"""
    global _state_manager
    
    # 若已有缓存材质且材质仍然有效，直接复用
    if (_state_manager.performance_material is not None and 
        _state_manager.performance_material.name in bpy.data.materials):
        return _state_manager.performance_material
    
    # 若场景已有同名材质，直接引用并复用（不重建节点）
    if "QSL_PerformanceMaterial_Shuimeng" in bpy.data.materials:
        _state_manager.performance_material = bpy.data.materials["QSL_PerformanceMaterial_Shuimeng"]
        # 确保材质有fake_user标记，防止被清理
        _state_manager.performance_material.use_fake_user = True
        return _state_manager.performance_material
    
    # 创建新的性能模式材质（仅首次创建时构建节点）
    _state_manager.performance_material = bpy.data.materials.new(name="QSL_PerformanceMaterial_Shuimeng")
    _state_manager.performance_material.use_nodes = True
    # 设置fake_user标记，防止材质被Blender自动清理
    _state_manager.performance_material.use_fake_user = True
    
    # 获取材质节点
    nodes = _state_manager.performance_material.node_tree.nodes
    links = _state_manager.performance_material.node_tree.links
    
    # 清除所有节点，重建为目标结构
    nodes.clear()
    
    # 添加输出节点
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (500, 0)
    
    # 添加混合着色器
    mix_node = nodes.new(type='ShaderNodeMixShader')
    mix_node.location = (300, 0)
    
    # 添加光泽BSDF并设置颜色与粗糙度
    glossy_node = nodes.new(type='ShaderNodeBsdfGlossy')
    glossy_node.location = (100, 100)
    glossy_node.inputs['Color'].default_value = (0.7372549, 0.7372549, 0.7372549, 1.0)  # #BCBCBCFF
    glossy_node.inputs['Roughness'].default_value = 0.0
    
    # 添加透明BSDF并设置颜色
    transparent_node = nodes.new(type='ShaderNodeBsdfTransparent')
    transparent_node.location = (100, -120)
    transparent_node.inputs['Color'].default_value = (0.4862745, 0.4862745, 0.4862745, 1.0)  # #7C7C7CFF
    
    # 添加光程与数学比较节点
    light_path = nodes.new(type='ShaderNodeLightPath')
    light_path.location = (-200, 100)
    
    math_node = nodes.new(type='ShaderNodeMath')
    math_node.location = (0, 200)
    math_node.operation = 'GREATER_THAN'  # 大于
    math_node.inputs[1].default_value = 0.0  # 阈值=0
    
    # 连接：光程的射线深度 -> 大于(0) -> 混合着色器系数
    links.new(light_path.outputs['Ray Depth'], math_node.inputs[0])
    links.new(math_node.outputs[0], mix_node.inputs[0])  # Fac 输入
    
    # 连接：光泽BSDF 与 透明BSDF -> 混合着色器 -> 材质输出
    links.new(glossy_node.outputs['BSDF'], mix_node.inputs[1])
    links.new(transparent_node.outputs['BSDF'], mix_node.inputs[2])
    links.new(mix_node.outputs['Shader'], output_node.inputs['Surface'])
    
    return _state_manager.performance_material

def apply_performance_material_override(context):
    """应用性能模式材质覆盖"""
    global _state_manager
    
    try:
        # 保存原始材质覆盖（使用当前活动视图层）
        view_layer = context.view_layer
        if view_layer:
            _state_manager.original_material_override = view_layer.material_override
            
            # 只在需要时创建性能模式材质
            if (_state_manager.performance_material is None or 
                _state_manager.performance_material.name not in bpy.data.materials):
                create_performance_material()
            
            # 应用材质覆盖
            view_layer.material_override = _state_manager.performance_material
            
    except Exception as e:
        pass

def remove_performance_material_override(context):
    """移除性能模式材质覆盖（保留材质用于复用）"""
    global _state_manager
    
    try:
        # 恢复原始材质覆盖（使用当前活动视图层）
        view_layer = context.view_layer
        if view_layer:
            view_layer.material_override = _state_manager.original_material_override
        _state_manager.original_material_override = None
        
        # 不删除性能模式材质，保留缓存，以便下次直接复用
        # 材质已设置fake_user标记，不会被Blender自动清理
        # 仅重置引用，不触发数据块删除
        # _state_manager.performance_material 保留
        
    except Exception as e:
        # 即使出错也要重置全局变量（保留材质缓存）
        _state_manager.original_material_override = None

class QuickStudioLightProperties(PropertyGroup):
    """Property group for storing light hit data"""
    last_hit_location: bpy.props.FloatVectorProperty(
        name="Last Hit Location",
        description="Last position where the ray hit",
        subtype='XYZ',
        size=3
    )
    last_hit_distance: bpy.props.FloatProperty(
        name="Last Hit Distance",
        description="Distance of the last ray hit"
    )
    last_hit_normal: bpy.props.FloatVectorProperty(
        name="Last Hit Normal",
        description="Normal vector of the last ray hit surface",
        subtype='XYZ',
        size=3
    )
    show_studio_light_controls: bpy.props.BoolProperty(
        name="Show Light Controls",
        description="Show interactive control points for all lights in the scene",
        default=False,
        update=update_studio_light_controls_display,
        options={'SKIP_SAVE'}  # 不保存到文件，每次启动都默认关闭
    )
    performance_mode: bpy.props.BoolProperty(
        name="Performance Mode",
        description="Enable performance mode: applies black material override during lighting mode for better performance",
        default=False
    )
    
    mirror_axis: bpy.props.EnumProperty(
        name="Mirror Axis",
        description="Axis to mirror across",
        items=[
            ('0', "X", "Mirror along X axis"),
            ('1', "Y", "Mirror along Y axis"),
            ('2', "Z", "Mirror along Z axis"),
        ],
        default='0'
    )

@vulkan_compatible
def draw_reflection_hit_line(self, context):
    """绘制从命中点到灯光的指示线（反射模式和精确模式专用），并处理视锥剪裁和遮挡效果，兼容Vulkan和OpenGL。"""
    # 即使是极短的sleep(0.0015)也能触发布局/绘制线程的上下文切换，
    # 显著减少输入延迟，让操作更"跟手"
    # 无论是否绘制文本，这个让步必须执行
    if is_vulkan_backend():
        time.sleep(0.0015)  # Vulkan后端需要让步以避免Cycles渲染卡顿
    # time.sleep(0.0015)  # 移除 sleep 以避免影响帧率
    
    try:
        # 检查是否有命中点和活动灯光
        if not hasattr(self, "_last_hit_location") or self._last_hit_location is None:
            return
        
        light_obj = context.active_object
        if not light_obj or light_obj.type != 'LIGHT':
            return
            
        # 检查灯光对象是否仍然有效（未被删除）
        try:
            # 尝试访问对象的名称来检查对象是否仍然有效
            _ = light_obj.name
            # 检查对象是否仍在场景中
            if light_obj.name not in context.scene.objects:
                return
        except ReferenceError:
            # 对象已被删除，返回
            return
            
        # 3D坐标点
        hit_3d = self._last_hit_location
        light_3d = light_obj.matrix_world.translation
        
        # 投影逻辑已移除，直接使用3D坐标绘制




                

                    

        

            

        
        # 根据模式使用不同的颜色
        prefs = context.preferences.addons[__package__].preferences
        if self._precise_mode:
            line_base_color = prefs.precise_color
        else:
            line_base_color = prefs.reflection_color
        
        # 使用深度测试绘制反射线，参与遮挡计算
        line_color = (*line_base_color, 0.8)  # 固定透明度0.8
        
        # 使用深度测试实现绘制反射线
        draw_reflection_line_depth(context, hit_3d, light_3d, line_color, self._line_opacity)
        
    except Exception as e:
        pass

@vulkan_compatible
def draw_callback_px(self, context):
    """Draw viewport border and mode hint text，兼容Vulkan和OpenGL"""
    # 即使是极短的sleep(0.0015)也能触发布局/绘制线程的上下文切换，
    # 显著减少输入延迟，让操作更"跟手"
    # 无论是否绘制文本，这个让步必须执行
    if is_vulkan_backend():
        time.sleep(0.0015)  # Vulkan后端需要让步以避免Cycles渲染卡顿
    # time.sleep(0.0015)

    try:
        # 安全检查：确保操作器实例仍然有效
        try:
            _ = self.is_active
        except ReferenceError:
            # 操作器已被删除，直接返回
            return
            
        # 检查是否应该绘制
        if not self.is_active or context.area != self._active_area:
            return
            
        prefs = context.preferences.addons[__package__].preferences
        
        # 获取视口区域和区域数据
        region = context.region
        rv3d = context.region_data
        
        # 处理淡入淡出效果（用于2D UI：边框和文本）
        current_time = time.time()
        fade_alpha = 1.0
        
        if self._is_fading_in and self._fade_start_time:
            elapsed = current_time - self._fade_start_time
            if elapsed < self._fade_duration:
                fade_alpha = elapsed / self._fade_duration
                self._current_fade_alpha = fade_alpha
            else:
                self._is_fading_in = False
                self._current_fade_alpha = 1.0
                fade_alpha = 1.0
        elif self._is_fading_out and self._fade_start_time:
            elapsed = current_time - self._fade_start_time
            if elapsed < self._fade_duration:
                fade_alpha = 1.0 - (elapsed / self._fade_duration)
                self._current_fade_alpha = fade_alpha
            else:
                self._is_fading_out = False
                self._current_fade_alpha = 0.0
                fade_alpha = 0.0
                # 淡出完成，标记需要清理（在下一个计时器事件中处理）
                self._needs_final_cleanup = True
        else:
            fade_alpha = self._current_fade_alpha
        
        # 设置颜色
        if self._precise_mode:
            mode_color = prefs.precise_color
        else:
            mode_color = prefs.reflection_color
            
        # 应用淡入淡出到透明度
        border_alpha = prefs.border_opacity * fade_alpha
        text_alpha = prefs.text_opacity * fade_alpha
        
        # 设置文本颜色（无论边框是否绘制，文本颜色都需要设置）
        text_color = (*mode_color[:3], text_alpha)
        
        # 绘制边框（支持彩虹边框）
        # 早期退出：如果边框透明度为0，不进行绘制以节省性能
        if border_alpha <= 0.0:
            pass  # 跳过边框绘制
        elif getattr(prefs, "rainbow_border", False):
            # 彩虹边框使用渐变颜色，透明度随淡入淡出变化
            draw_rainbow_border(context, prefs.border_thickness, border_alpha)
        else:
            color = (*mode_color, border_alpha)
            draw_border(context, color, prefs.border_thickness)
        
        # 击中点现在通过独立的绘制处理器在3D中绘制
                
        # 绘制从命中点到灯光的连接线
        draw_reflection_hit_line(self, context)
        
        # 准备模式文本
        if self._distance_mode:
            mode_text = bpy.app.translations.pgettext("Distance Mode (G) | LMB: Confirm, RMB: Cancel")
        elif self._scale_mode:
            mode_text = bpy.app.translations.pgettext("Scale Mode (S) | LMB: Confirm, RMB: Cancel")
        elif self._precise_mode:
            mode_text = bpy.app.translations.pgettext("Precise Mode (Space) | Hold Shift to Slow Down")
        else:
            mode_text = bpy.app.translations.pgettext("Reflection Mode | Press:\nSpace: Precise Mode\nG: Distance Mode\nS: Scale Mode\nHold Shift for Multi-surface Reflection")
        
        # 计算文本位置
        font_id = 0
        text_size = prefs.text_size
        blf.size(font_id, text_size)
        
        # 获取文本尺寸
        text_lines = mode_text.split('\n')
        max_width = 0
        total_height = 0
        line_height = (blf.dimensions(font_id, "Tg")[1] * 1.5)  # 1.5倍行距
        
        for line in text_lines:
            width = blf.dimensions(font_id, line)[0]
            max_width = max(max_width, width)
            total_height += line_height
        
        # 计算文本框位置（左下角，留出边距）
        margin = 20
        text_x = margin
        text_y = margin + total_height  # 从底部向上放置文本
        
        # 绘制文本（带描边）
        # 我们不再因为透明度为0而提前退出，因为这会跳过 sleep(0.0015)
        # 从而导致输入处理线程失去让步机会，引起操作卡顿
        # if text_alpha <= 0.0:
        #    return
            
        current_y = text_y  # 从底部开始向上绘制每行
        for line in text_lines:
            # 只有当透明度大于0时才真正执行绘制操作
            if text_alpha > 0.0:
                # 绘制描边（使用多个偏移）
                offsets = ((-1, -1), (-1, 1), (1, -1), (1, 1),
                          (-1, 0), (1, 0), (0, -1), (0, 1))
                
                # 绘制黑色描边（透明度也受淡入淡出影响）
                blf.color(font_id, 0.0, 0.0, 0.0, text_alpha)
                for offset_x, offset_y in offsets:
                    blf.position(font_id, text_x + offset_x, current_y - line_height + offset_y, 0)
                    blf.draw(font_id, line)
                
                # 绘制主文本
                blf.position(font_id, text_x, current_y - line_height, 0)
                blf.color(font_id, *text_color) 
            
            # 移除这里的 sleep(0.0015)，避免在循环中叠加导致延迟
            # 已经在函数开始处统一 sleep
            
            if text_alpha > 0.0:
                blf.draw(font_id, line)
            
            current_y -= line_height
            
    except Exception as e:
        pass


@vulkan_compatible
def draw_callback_view(self, context):
    """Draw light outline with depth test，兼容Vulkan和OpenGL"""
    try:
        try:
            _ = self.is_active
        except ReferenceError:
            return

        if not self.is_active or context.area != self._active_area:
            return

        prefs = context.preferences.addons[__package__].preferences

        if self._precise_mode:
            mode_color = prefs.precise_color
        else:
            mode_color = prefs.reflection_color

        light_obj = context.active_object
        if not (light_obj and light_obj.type == 'LIGHT'):
            light_obj = getattr(self, '_selected_light', None)
            if light_obj and light_obj.type != 'LIGHT':
                light_obj = None

        if not light_obj:
            return

        outline_color = (mode_color[0], mode_color[1], mode_color[2], 1.0)
        # 灯光边缘轮廓粗细固定为1像素，不随视口边框厚度变化
        outline_thickness = 1.0 
        draw_light_outline_depth(context, light_obj, outline_color, outline_thickness)

        center_dot_color = (mode_color[0], mode_color[1], mode_color[2], 0.9)
        draw_center_dot_depth(context, light_obj, center_dot_color, CONTROL_POINT_RADIUS)

        # 绘制鼠标落点指向灯光的准星（模仿LightControl）
        if hasattr(self, "_last_hit_location") and self._last_hit_location is not None:
            # 使用稍微透明一点的颜色
            crosshair_color = (mode_color[0], mode_color[1], mode_color[2], 0.8)
            # 大小设置为灯光轮廓半径的1.5倍
            draw_crosshair_glsl(context, self._last_hit_location, light_obj.matrix_world.translation, 
                               LIGHT_OUTLINE_RADIUS * 1.5, crosshair_color, thickness=2)
    except Exception:
        pass

@vulkan_compatible
def draw_border(context, color, thickness):
    """绘制视口边框（兼容Vulkan和OpenGL）"""
    # 早期退出：如果透明度为0，不进行绘制以节省性能
    if len(color) >= 4 and color[3] <= 0.0:
        return

    if _draw_pulse_border_glsl(context, thickness, color):
        return

    width = context.area.width
    height = context.area.height

    t = max(1.0, float(thickness))

    draw_box(((0, 0), (width, t)), color)
    draw_box(((0, height - t), (width, height)), color)
    draw_box(((0, t), (t, height - t)), color)
    draw_box(((width - t, t), (width, height - t)), color)

@vulkan_compatible
def draw_box(corners, color):
    """绘制一个填充的矩形，兼容Vulkan和OpenGL"""
    try:
        uniform_shader = create_builtin_shader('UNIFORM_COLOR')
        if uniform_shader is None:
            return
            
        _vulkan_state_manager.set_blend_mode('ALPHA')
        
        x1, y1 = corners[0]
        x2, y2 = corners[1]
        
        vertices = (
            (x1, y1), (x2, y1),
            (x2, y2), (x1, y2)
        )
        
        batch = create_compatible_batch(uniform_shader, 'TRI_FAN', {"pos": vertices})
        if batch is None:
            return
            
        uniform_shader.bind()
        uniform_shader.uniform_float("color", color)
        batch.draw(uniform_shader)
        
    except Exception as e:
        print(f"绘制填充矩形失败: {e}")
    finally:
        _vulkan_state_manager.set_blend_mode('NONE')


@vulkan_compatible
def draw_gradient_rect(x1, y1, x2, y2, color_stops, orientation='horizontal'):
    """绘制线性渐变填充的矩形，兼容Vulkan和OpenGL"""
    try:
        if not color_stops:
            return

        # 按t排序，避免传入无序停靠点
        stops = sorted(color_stops, key=lambda s: s[0])

        # 使用自定义的平滑颜色着色器以兼容Vulkan
        smooth_shader = _get_smooth_color_shader()
        if smooth_shader is None:
            # 回退到内置
            smooth_shader = create_builtin_shader('SMOOTH_COLOR')
            
        if smooth_shader is None:
            return
            
        _vulkan_state_manager.set_blend_mode('ALPHA')

        verts = []
        colors = []

        if orientation == 'vertical':
            # 沿Y方向渐变：为每个停靠点创建两行顶点
            for t, col in stops:
                y = y1 + t * (y2 - y1)
                verts.extend([(x1, y), (x2, y)])
                colors.extend([col, col])
        else:
            # 沿X方向渐变：为每个停靠点创建两列顶点
            for t, col in stops:
                x = x1 + t * (x2 - x1)
                verts.extend([(x, y1), (x, y2)])
                colors.extend([col, col])

        # 使用TRI_STRIP构建梯形带，实现平滑渐变填充
        batch = create_compatible_batch(smooth_shader, 'TRI_STRIP', {"pos": verts, "color": colors})
        if batch is None:
            return
            
        smooth_shader.bind()
        batch.draw(smooth_shader)
        
    except Exception as e:
        print(f"绘制渐变矩形失败: {e}")
    finally:
        _vulkan_state_manager.set_blend_mode('NONE')


@vulkan_compatible
def draw_rainbow_border(context, thickness, alpha=1.0, segments=12):
    """绘制彩虹流动视口边框，兼容Vulkan和OpenGL"""
    if _draw_rainbow_border_glsl(context, thickness, alpha):
        return
    _draw_rainbow_border_gradient(context, thickness, alpha, segments)


@vulkan_compatible
def draw_reflection_line(self, context):
    """使用深度遮挡方式绘制从命中点到灯光的指示线，兼容Vulkan和OpenGL"""
    try:
        if not hasattr(self, "_hit_location") or not hasattr(self, "_selected_light") or self._hit_location is None or self._selected_light is None:
            return
            
        # 检查灯光对象是否仍然有效（未被删除）
        try:
            # 尝试访问对象的名称来检查对象是否仍然有效
            _ = self._selected_light.name
            # 检查对象是否仍在场景中
            if self._selected_light.name not in context.scene.objects:
                return
        except ReferenceError:
            # 对象已被删除，清理引用并返回
            self._selected_light = None
            return
            
        # 3D坐标点
        hit_3d = self._hit_location
        light_3d = self._selected_light.location
        
        # 使用深度遮挡方式绘制反射线（亮黄色）
        line_color = (1.0, 1.0, 0.2, 1.0)  # 亮黄色
        draw_reflection_line_depth(context, hit_3d, light_3d, line_color, self._line_opacity)
            
    except Exception as e:
        print(f"绘制反射线失败: {e}")

class LIGHTING_GADGETS_OT_REFLECTION_MODE(Operator):
    bl_idname = "lighting_gadgets.reflection_mode"
    bl_label = "Reflection Mode"
    bl_description = (
        "Enable Reflection Mode (Shortcut: Shift + R)\n"
        "Hold Shift to enable multi-surface reflection\n"
        "Press Space to enter precise mode, hold Shift to slow down in precise mode\n"
        "Enhanced performance mode with optimized viewport refresh"
    )
    bl_options = {'REGISTER', 'UNDO'}
    
    # 类属性
    EDGE_THRESHOLD = EDGE_THRESHOLD_DEFAULT
    MULTI_FACE_SAMPLE_RADIUS = MULTI_FACE_SAMPLE_RADIUS  # 多面采样的像素半径（由 10 降低到 6）
    MULTI_FACE_SAMPLE_COUNT = MULTI_FACE_SAMPLE_COUNT     # 多面采样数量（由 5 降低到 3）
    
    @classmethod
    def poll(cls, context):
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        return (
            area and area.type == 'VIEW_3D' and region and rv3d and
            context.active_object and context.active_object.type == 'LIGHT'
        )
        
    _timers = []
    _draw_handles = []
    is_active = False
    _initial_transform = None
    _initial_distance = None
    _last_hit_location = None
    _last_hit_normal = None
    _active_area = None  # 记录激活视口
    _precise_mode = False  # 是否处于精确控制模式
    _last_mouse_pos = None  # 鼠标位置用于精确控制模式
    _hit_point = None  # 击中点
    _last_hit_distance = None  # 上次击中距离
    _initial_location = None
    _initial_rotation = None
    _original_scale = None
    _distance_mode = False
    _initial_distance = None
    _initial_mouse_x = None
    _scale_mode = False
    _initial_scale = None
    _line_opacity = 1.0  # 线条不透明度
    # 淡入淡出相关属性
    _fade_start_time = None
    _fade_duration = 0.3  # 淡入淡出持续时间（秒）
    _is_fading_in = False
    _is_fading_out = False
    _current_fade_alpha = 0.0
    _needs_final_cleanup = False
    _finishing = False  # 标记是否正在结束过程中
    
    def modal(self, context, event):
        # 检查是否需要执行最终清理
        if self._needs_final_cleanup:
            self.final_cleanup(context)
            return {'FINISHED'}
            
        # 如果正在结束过程中，检查淡出是否完成
        if self._finishing and self._is_fading_out:
            if event.type == 'TIMER':
                current_time = time.time()
                fade_progress = (current_time - self._fade_start_time) / self._fade_duration
                if fade_progress >= 1.0:
                    # 淡出完成，执行最终清理并结束
                    self.final_cleanup(context)
                    return {'FINISHED'}
                # 计时器阶段保持运行以继续淡出，只在需要时重绘
                if context.area == self._active_area and getattr(self, '_needs_redraw', True):
                    context.area.tag_redraw()
                    # 重置重绘标志
                    self._needs_redraw = False
                return {'RUNNING_MODAL'}
            # 非计时器事件直接放行，避免短暂不可操作
            if context.area == self._active_area and getattr(self, '_needs_redraw', False):
                context.area.tag_redraw()
                # 重置重绘标志
                self._needs_redraw = False
            return {'PASS_THROUGH'}
            
        if not context.active_object or context.active_object.type != 'LIGHT':
            # 如果灯光对象不再活动或不是灯光，必须立即清理所有资源，防止Timer和回调泄漏
            self.final_cleanup(context)
            return {'CANCELLED'}

        # 强制让步：在每次 modal 处理的开始就执行一次微小睡眠
        # 这确保了无论处理什么事件，Blender 主循环都有机会呼吸
        # 解决精确模式和其他模式下可能的卡顿
        if is_vulkan_backend():
            time.sleep(0.0015)  # Vulkan后端需要让步以避免Cycles渲染卡顿
        # time.sleep(0.0015)  # 移除 sleep 以避免影响帧率

        # 优化的视口刷新机制 - 只在真正需要时重绘

        if context.area == self._active_area:
            base_needs_redraw = (
                self._precise_mode
                or self._distance_mode
                or self._scale_mode
                or not getattr(self, "_aligned", False)
                or getattr(self, "_needs_redraw", False)
            )

            rainbow_needs_redraw = False
            pulse_needs_redraw = False
            try:
                prefs = context.preferences.addons[__package__].preferences
                border_opacity = float(getattr(prefs, "border_opacity", 0.0))
                rainbow_enabled = bool(getattr(prefs, "rainbow_border", False))
                rainbow_needs_redraw = bool(rainbow_enabled and border_opacity > 0.0)
                if (not rainbow_enabled) and border_opacity > 0.0:
                    pulse_needs_redraw = _QSL_SHADER_CACHE.get("PULSE_BORDER") is not None
            except Exception:
                rainbow_needs_redraw = False
                pulse_needs_redraw = False

            needs_redraw = base_needs_redraw or rainbow_needs_redraw or pulse_needs_redraw

            current_time = time.time()
            min_interval = 0.016 if base_needs_redraw else 0.05
            if needs_redraw:
                if not hasattr(self, "_last_redraw_time") or (current_time - self._last_redraw_time) >= min_interval:
                    context.area.tag_redraw()
                    self._last_redraw_time = current_time
                    self._needs_redraw = False

        # 处理空格键切换精确控制模式
        if event.type == 'SPACE' and event.value == 'PRESS':
            # sleep(0.0015) 已在 modal 开始处统一执行，此处移除以避免叠加
            
            if self._last_hit_location is not None:  # 只有存在击中点时才切换
                self._precise_mode = not self._precise_mode
                self._last_mouse_pos = (event.mouse_region_x, event.mouse_region_y)
                # 强制重绘以更新边框颜色
                if context.area:
                    context.area.tag_redraw()
                return {'RUNNING_MODAL'}
            return {'RUNNING_MODAL'}  # 如果没有击中点，保持当前模式

        if event.type == 'S' and event.value == 'PRESS' and not self._distance_mode and not self._scale_mode:
            light_obj = context.active_object
            self._scale_mode = True
            self._initial_scale = light_obj.scale.copy()
            self._initial_mouse_x = event.mouse_region_x
            return {'RUNNING_MODAL'}

        if self._scale_mode:
            if event.type in {'LEFT_SHIFT', 'RIGHT_SHIFT'}:
                light_obj = context.active_object
                self._initial_scale = light_obj.scale.copy()
                self._initial_mouse_x = event.mouse_region_x
                return {'RUNNING_MODAL'}
            
            if event.type == 'MOUSEMOVE':
                # 计算鼠标在X轴上的移动距离
                delta_x = event.mouse_region_x - self._initial_mouse_x
                # 将移动距离转换为缩放因子（可以调整系数来控制灵敏度）
                scale_step = 0.01
                if event.shift:
                    scale_step *= 0.1
                scale_factor = 1.0 + (delta_x * scale_step)
                # 确保缩放不会太小
                scale_factor = max(0.1, scale_factor)
                
                light_obj = context.active_object
                light_obj.scale = self._initial_scale * scale_factor
                
                # time.sleep(0.0015) 已在 modal 开始处执行
                return {'RUNNING_MODAL'}
                
            elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                # 确认缩放并返回之前的模式
                self._scale_mode = False
                self._initial_scale = None
                self._initial_mouse_x = None
                return {'RUNNING_MODAL'}
                
            elif event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
                # 取消缩放，恢复初始大小并返回之前的模式
                light_obj = context.active_object
                if self._initial_scale is not None:
                    light_obj.scale = self._initial_scale.copy()
                
                # 只退出缩放模式，保持在反射/精确模式中
                self._scale_mode = False
                self._initial_scale = None
                self._initial_mouse_x = None
                return {'RUNNING_MODAL'}
            
            # 在缩放模式下，阻止其他模式的处理
            return {'RUNNING_MODAL'}

        if event.type == 'G' and event.value == 'PRESS' and not self._distance_mode and not self._scale_mode:
            # 进入距离调整模式
            self._distance_mode = True
            light_obj = context.active_object
            self._initial_distance = (self._last_hit_location - light_obj.matrix_world.translation).length
            self._initial_mouse_x = event.mouse_region_x
            return {'RUNNING_MODAL'}

        if self._distance_mode:
            if event.type in {'LEFT_SHIFT', 'RIGHT_SHIFT'}:
                light_obj = context.active_object
                self._initial_distance = (self._last_hit_location - light_obj.matrix_world.translation).length
                self._initial_mouse_x = event.mouse_region_x
                return {'RUNNING_MODAL'}
            
            if event.type == 'MOUSEMOVE':
                # 计算鼠标在X轴上的移动距离
                delta_x = event.mouse_region_x - self._initial_mouse_x
                # 将移动距离转换为实际距离变化（可以调整系数来控制灵敏度）
                distance_factor = 0.01
                if event.shift:
                    distance_factor *= 0.1
                new_distance = self._initial_distance + (delta_x * distance_factor)
                # 确保距离不会变为负值
                new_distance = max(0.1, new_distance)
                
                # 更新灯光位置
                light_obj = context.active_object
                direction = (self._last_hit_location - light_obj.matrix_world.translation).normalized()
                new_world_pos = self._last_hit_location - direction * new_distance
                set_light_world_location(light_obj, new_world_pos)
                
                # time.sleep(0.0015) 已在 modal 开始处执行
                return {'RUNNING_MODAL'}
                
            elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                # 确认距离调整并返回之前的模式
                self._distance_mode = False
                self._initial_distance = None
                self._initial_mouse_x = None
                return {'RUNNING_MODAL'}
                
            elif event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
                # 取消距离调整，恢复初始位置并返回之前的模式
                light_obj = context.active_object
                direction = (self._last_hit_location - light_obj.matrix_world.translation).normalized()
                restored_world_pos = self._last_hit_location - direction * self._initial_distance
                set_light_world_location(light_obj, restored_world_pos)
                
                # 只退出距离调整模式，保持在反射/精确模式中
                self._distance_mode = False
                self._initial_distance = None
                self._initial_mouse_x = None
                
                # 防止事件传递到其他处理器
                return {'RUNNING_MODAL'}
            
            # 在距离调整模式下，阻止其他模式的处理
            return {'RUNNING_MODAL'}

        if event.type == 'TIMER':
            light_obj = context.active_object
            current_time = time.time()
            
            # 智能重绘控制：检查是否有待处理的重绘请求
            if hasattr(self, "_pending_redraw") and self._pending_redraw:
                # 检查是否达到最小重绘间隔（约60FPS）
                if not hasattr(self, "_last_timer_redraw") or (current_time - self._last_timer_redraw) >= 0.016:
                    if context.area == self._active_area:
                        context.area.tag_redraw()
                    self._last_timer_redraw = current_time
                    self._pending_redraw = False
            
            if self._precise_mode:
                # 精确控制模式
                if self._last_mouse_pos is None:
                    self._last_mouse_pos = (event.mouse_region_x, event.mouse_region_y)
                    return {'RUNNING_MODAL'}
                
                # 获取当前鼠标位置
                mouse_pos = (event.mouse_region_x, event.mouse_region_y)
                
                # 只有当鼠标位置真正发生变化时才进行更新
                if mouse_pos != self._last_mouse_pos:
                    # 执行灯光变换
                    update_light_precise_transform(
                        context,
                        light_obj,
                        self._last_hit_location,
                        self._last_hit_normal,
                        mouse_pos,
                        self._last_mouse_pos,
                        event.shift
                    )
                    
                    # 更新最后鼠标位置
                    self._last_mouse_pos = mouse_pos
                    # 标记需要重绘（灯光属性已变化）
                    self._needs_redraw = True
                    self._pending_redraw = True
                    
                    # sleep(0.0015) 已在 modal 开始处执行
            else:
                coord = (event.mouse_region_x, event.mouse_region_y)
                region = context.region
                rv3d = context.region_data
                
                ray_direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
                ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
                if hasattr(rv3d, "is_perspective") and not rv3d.is_perspective and getattr(rv3d, "view_perspective", "") == "CAMERA":
                    cam = getattr(context.space_data, "camera", None)
                    cam_data = getattr(cam, "data", None) if cam else None
                    if cam_data and getattr(cam_data, "type", "") == "ORTHO":
                        view_location = rv3d.view_location
                        depth_location = view3d_utils.region_2d_to_location_3d(region, rv3d, coord, view_location)
                        clip_start = getattr(cam_data, "clip_start", 0.1)
                        ray_origin = depth_location - ray_direction * max(clip_start * 10.0, 1.0)
                heavy_gn_scene = is_heavy_geometry_nodes_scene(context)
                result = find_visible_hit(context, ray_origin, ray_direction, ignore_gn_instances=heavy_gn_scene)
                
                if result[0]:  # 如果射线击中物体
                    hit_location = result[1]
                    hit_normal = result[2].copy()  # 创建法线的副本，以便后面可能的修改
                    if hasattr(rv3d, 'is_perspective') and not rv3d.is_perspective:
                        self._mouse_world_position = hit_location.copy()
                    else:
                        self._mouse_world_position = None
                    
                    # Shift键多面反射功能
                    if event.shift:
                        # 采样鼠标周围的多个面
                        sampled_normals = self.sample_nearby_faces(
                            context, 
                            coord, 
                            self.MULTI_FACE_SAMPLE_RADIUS,
                            self.MULTI_FACE_SAMPLE_COUNT
                        )
                        
                        # 如果找到多个不同的面，计算平均法线
                        if len(sampled_normals) > 1:
                            avg_normal = self.calculate_average_normal(sampled_normals)
                            if avg_normal is not None:
                                hit_normal = avg_normal
                    
                    # 如果尚未设置初始距离，现在根据当前灯光和命中点的距离来设置
                    if self._initial_distance is None:
                        self._initial_distance = (hit_location - light_obj.matrix_world.translation).length
                    
                    # 设置移动速度
                    if self._last_hit_location is None:
                        self._last_hit_location = hit_location.copy()
                        self._last_hit_normal = hit_normal.copy()
                    
                    lerp_factor = 1.0 if heavy_gn_scene else 0.15
                    
                    # 在当前位置和新位置之间插值
                    smoothed_location = self._last_hit_location.lerp(hit_location, lerp_factor)
                    smoothed_normal = self._last_hit_normal.lerp(hit_normal, lerp_factor)
                    
                    # 更新最后位置和法线
                    self._last_hit_location = smoothed_location
                    self._last_hit_normal = smoothed_normal
                    
                    # 优化的对齐与静止判断机制
                    prev_coord = getattr(self, "_prev_mouse_coord", None)
                    
                    # 使用更精确的移动检测，考虑鼠标移动速度和方向
                    if prev_coord is None:
                        moved = True
                    else:
                        # 计算鼠标移动距离和速度
                        dx = abs(coord[0] - prev_coord[0])
                        dy = abs(coord[1] - prev_coord[1])
                        moved = (dx + dy) >= 1.0
                        
                        # 检测鼠标移动趋势（防止微小抖动触发重绘）
                        if hasattr(self, "_mouse_movement_history"):
                            self._mouse_movement_history.append((dx, dy))
                            # 只保留最近5次移动记录
                            if len(self._mouse_movement_history) > 5:
                                self._mouse_movement_history.pop(0)
                        else:
                            self._mouse_movement_history = [(dx, dy)]
                    
                    self._prev_mouse_coord = coord
                    
                    # 更精确的位置和法线对齐检测
                    pos_delta = (hit_location - self._last_hit_location).length
                    normal_dot = max(min(self._last_hit_normal.normalized().dot(hit_normal.normalized()), 1.0), -1.0)
                    
                    # 动态调整对齐阈值，根据鼠标移动速度自适应
                    pos_epsilon = getattr(self, "ALIGN_POS_EPSILON", 0.001)
                    norm_epsilon = getattr(self, "ALIGN_NORM_EPSILON", 0.001)
                    
                    # 如果鼠标移动速度较快，放宽对齐阈值
                    if hasattr(self, "_mouse_movement_history") and len(self._mouse_movement_history) >= 3:
                        avg_movement = sum(sum(move) for move in self._mouse_movement_history) / len(self._mouse_movement_history)
                        if avg_movement > 5.0:  # 快速移动时
                            pos_epsilon *= 2.0
                            norm_epsilon *= 2.0
                    
                    aligned_now = (pos_delta <= pos_epsilon) and ((1.0 - normal_dot) <= norm_epsilon)
                    
                    if not moved and aligned_now:
                        if not getattr(self, "_aligned", False):
                            # 首次进入对齐状态时，进行一次最终精确更新
                            self._last_hit_location = hit_location.copy()
                            self._last_hit_normal = hit_normal.copy()
                            update_light_transform(
                                context.region_data,
                                light_obj,
                                self._last_hit_location,
                                self._last_hit_normal,
                                self._initial_distance,
                                ray_origin,
                                ray_direction,
                                context,
                                getattr(self, "_mouse_world_position", None)
                            )

                        self._aligned = True
                        self._needs_redraw = False
                    else:
                        self._aligned = False
                        # 应用反射计算
                        update_light_transform(
                            context.region_data,
                            light_obj,
                            smoothed_location,
                            smoothed_normal,
                            self._initial_distance,
                            ray_origin,
                            ray_direction,
                            context,
                            getattr(self, "_mouse_world_position", None)
                        )
                        
                        # 在正交模式下，如果计算出了鼠标实际指向的位置，更新灯光指向
                        if hasattr(self, '_mouse_world_position') and self._mouse_world_position is not None:
                            # 计算从灯光到鼠标实际指向位置的方向
                            to_mouse = (self._mouse_world_position - light_obj.matrix_world.translation).normalized()
                            # 设置灯光旋转以面向鼠标实际指向的位置
                            set_light_world_orientation(light_obj, to_mouse)
                        else:
                            # 如果无法计算鼠标实际指向位置，使用命中点作为目标
                            to_target = (hit_location - light_obj.matrix_world.translation).normalized()
                            set_light_world_orientation(light_obj, to_target)
                        
                        # 标记需要重绘（灯光属性已变化）
                        self._needs_redraw = True
                        self._pending_redraw = True
                    
                    # 更新击中点
                    self._hit_point = hit_location
                    
                    # sleep(0.0015) 已在 modal 开始处执行

        elif event.type == 'MOUSEMOVE':
            # 只在精确模式下处理鼠标移动，避免不必要的重绘
            if self._precise_mode:
                # 获取当前视口区域
                region = context.region
                region_width = region.width
                region_height = region.height
                
                # 获取鼠标在视口中的局部坐标
                local_x = event.mouse_region_x
                local_y = event.mouse_region_y
                
                # 记录原始位置用于计算偏移
                original_x = local_x
                original_y = local_y
                
                # 检测边界并计算新位置
                wrap_x = False
                new_x = local_x
                if local_x <= self.EDGE_THRESHOLD:
                    new_x = region_width - self.EDGE_THRESHOLD
                    wrap_x = True
                elif local_x >= region_width - self.EDGE_THRESHOLD:
                    new_x = self.EDGE_THRESHOLD
                    wrap_x = True
                    
                wrap_y = False
                new_y = local_y
                if local_y <= self.EDGE_THRESHOLD:
                    new_y = region_height - self.EDGE_THRESHOLD
                    wrap_y = True
                elif local_y >= region_height - self.EDGE_THRESHOLD:
                    new_y = self.EDGE_THRESHOLD
                    wrap_y = True
                
                # 如果需要包裹，执行鼠标位置重置
                if wrap_x or wrap_y:
                    # 计算实际移动差值
                    if wrap_x:
                        dx = new_x - original_x
                        if original_x <= self.EDGE_THRESHOLD:
                            dx = -(region_width - 2 * self.EDGE_THRESHOLD)
                        else:
                            dx = region_width - 2 * self.EDGE_THRESHOLD
                    else:
                        dx = 0
                        
                    if wrap_y:
                        dy = new_y - original_y
                        if original_y <= self.EDGE_THRESHOLD:
                            dy = -(region_height - 2 * self.EDGE_THRESHOLD)
                        else:
                            dy = region_height - 2 * self.EDGE_THRESHOLD
                    else:
                        dy = 0
                    
                    # 更新鼠标位置
                    context.window.cursor_warp(
                        context.region.x + new_x,
                        context.region.y + new_y
                    )
                    
                    # 更新last_mouse_pos以保持运动连续性
                    self._last_mouse_pos = (new_x, new_y)
                    
                    # 应用移动
                    current_mouse = (new_x, new_y)
                    update_light_precise_transform(
                        context,
                        context.active_object,
                        self._last_hit_location,
                        self._last_hit_normal,
                        current_mouse,
                        self._last_mouse_pos,
                        event.shift
                    )
                    
                else:
                    # 正常的鼠标移动处理
                    current_mouse = (event.mouse_region_x, event.mouse_region_y)
                    update_light_precise_transform(
                        context,
                        context.active_object,
                        self._last_hit_location,
                        self._last_hit_normal,
                        current_mouse,
                        self._last_mouse_pos,
                        event.shift
                    )
                    self._last_mouse_pos = current_mouse
                    
                # 标记需要重绘（由TIMER事件处理）
                self._needs_redraw = True
                
                # sleep(0.0015) 已在 modal 开始处执行
            else:
                # 非精确模式下的原有处理逻辑
                pass
        
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            # 确认时保存落点数据
            if self._last_hit_location is not None:
                light = context.active_object
                # 保存落点数据到自定义属性（Light级别）
                props = light.data.quick_studio_light
                props.last_hit_location = self._last_hit_location.copy()
                props.last_hit_distance = self._last_hit_distance
                props.last_hit_normal = self._last_hit_normal.copy()
                
                # 启动淡出效果，但不立即结束操作器
                self.cleanup(context, cancel=False)
                self._finishing = True  # 标记正在结束
                
                return {'RUNNING_MODAL'}  # 继续运行直到淡出完成
            return {'CANCELLED'}
            
        elif event.type == 'RIGHTMOUSE' and event.value == 'PRESS' and not self._distance_mode and not self._scale_mode:
            # 取消时恢复初始状态，不保存落点
            light = context.active_object
            old_location = light.location.copy()
            old_rotation = light.rotation_euler.copy()
            old_scale = light.scale.copy()
            
            light.location = self._initial_location
            light.rotation_euler = self._initial_rotation
            light.scale = self._original_scale
            
            # 启动淡出效果，但不立即结束操作器
            self.cleanup(context, cancel=True)
            self._finishing = True  # 标记正在结束
            return {'RUNNING_MODAL'}  # 继续运行直到淡出完成

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        """Start reflection mode"""
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        if not (area and area.type == 'VIEW_3D' and region and rv3d):
            return {'PASS_THROUGH'}
        if context.area.type == 'VIEW_3D':
            # 记录初始变换
            light_obj = context.active_object
            self._initial_location = light_obj.location.copy()
            self._initial_rotation = light_obj.rotation_euler.copy()
            self._original_scale = light_obj.scale.copy()
            
            # 隐藏UI元素（工具栏、侧面板、覆盖层、小工具）
            hide_ui_elements(context)
            
            # 初始化资源列表
            self._timers = []
            self._draw_handles = []
            
            # 使用计时器控制反射模式
            wm = context.window_manager
            timer = wm.event_timer_add(0.016, window=context.window)
            self._timers.append(timer)
            wm.modal_handler_add(self)
            self.is_active = True
            self._active_area = context.area
            
            # 对齐控制相关状态
            self.ALIGN_POS_EPSILON = 0.001
            self.ALIGN_NORM_EPSILON = 0.001
            self._aligned = False
            self._prev_mouse_coord = (event.mouse_region_x, event.mouse_region_y)
            
            # 智能重绘控制相关状态
            self._pending_redraw = False
            self._last_timer_redraw = time.time()
            self._last_redraw_time = time.time()
            self._needs_redraw = False
            
            # 鼠标移动历史记录
            self._mouse_movement_history = []
            
            # 添加绘制回调
            args = (self, context)
            draw_handle = bpy.types.SpaceView3D.draw_handler_add(
                draw_callback_px, args, 'WINDOW', 'POST_PIXEL'
            )
            self._draw_handles.append(draw_handle)

            draw_handle_view = bpy.types.SpaceView3D.draw_handler_add(
                draw_callback_view, args, 'WINDOW', 'POST_VIEW'
            )
            self._draw_handles.append(draw_handle_view)
            
            # 检查并应用性能模式
            wm_props = context.window_manager.lighting_gadgets_props
            if wm_props.performance_mode:
                apply_performance_material_override(context)
                self._performance_mode_active = True
            else:
                self._performance_mode_active = False
            
            # 通知用户反射模式已启动
            template = bpy.app.translations.pgettext("Reflection mode started: Move mouse to adjust light, hold Shift for multi-surface reflection, left-click to confirm, right-click to cancel")
            self.report({'INFO'}, template)
            
            # 尝试读取上次命中数据
            if hasattr(light_obj.data, "quick_studio_light"):
                self.load_last_hit_data(light_obj.data)
            
            # 启动淡入效果
            self._fade_start_time = time.time()
            self._is_fading_in = True
            self._is_fading_out = False
            self._current_fade_alpha = 0.0
            self._needs_final_cleanup = False
            self._finishing = False
                
            return {'RUNNING_MODAL'}
        else:
            template = bpy.app.translations.pgettext("Reflection mode can only be used in the 3D View")
            self.report({'WARNING'}, template)
            return {'CANCELLED'}

    def load_last_hit_data(self, light):
        """Load last hit point data from the light object"""
        try:
            if hasattr(light, "quick_studio_light"):
                props = light.quick_studio_light
                if props.last_hit_location and props.last_hit_normal is not None:
                    self._last_hit_location = Vector(props.last_hit_location)
                    self._last_hit_normal = Vector(props.last_hit_normal)
                    self._last_hit_distance = float(props.last_hit_distance)
                    self._hit_point = self._last_hit_location
                    return True
            return False
        except AttributeError as e:
            return False
        except ValueError as e:
            return False
        except Exception as e:
            return False

    def cleanup(self, context, cancel):
        # 启动淡出效果而不是立即清理
        if not self._is_fading_out:
            self._fade_start_time = time.time()
            self._is_fading_out = True
            self._is_fading_in = False
            
            if cancel:
                # 恢复初始状态 - 检查对象是否仍然有效
                try:
                    if context.active_object and context.active_object.type == 'LIGHT':
                        # 检查对象是否仍然有效
                        _ = context.active_object.name
                        if context.active_object.name in context.scene.objects:
                            context.active_object.location = self._initial_location
                            context.active_object.rotation_euler = self._initial_rotation
                            context.active_object.scale = self._original_scale
                except (ReferenceError, AttributeError):
                    # 对象已被删除或无效，跳过恢复
                    pass
        else:
            # 如果已经在淡出，直接完成清理
            self.final_cleanup(context)
    
    def final_cleanup(self, context):
        """最终清理，移除所有回调和计时器"""
        # 清理所有计时器
        if hasattr(self, '_timers'):
            for timer in self._timers:
                try:
                    context.window_manager.event_timer_remove(timer)
                except:
                    pass
            self._timers.clear()
        # 兼容旧代码：检查是否存在单个计时器属性
        elif hasattr(self, '_timer') and self._timer:
            try:
                context.window_manager.event_timer_remove(self._timer)
            except:
                pass
            self._timer = None
            
        # 清理所有绘制回调
        if hasattr(self, '_draw_handles'):
            for handle in self._draw_handles:
                try:
                    bpy.types.SpaceView3D.draw_handler_remove(handle, 'WINDOW')
                except:
                    pass
            self._draw_handles.clear()
        # 兼容旧代码：检查是否存在单个绘制回调属性
        elif hasattr(self, '_draw_handle') and self._draw_handle:
            try:
                bpy.types.SpaceView3D.draw_handler_remove(self._draw_handle, 'WINDOW')
            except:
                pass
            self._draw_handle = None
            
        # 移除性能模式材质覆盖
        wm_props = context.window_manager.lighting_gadgets_props
        if wm_props.performance_mode:
            remove_performance_material_override(context)
            
        # 恢复UI元素（工具栏、侧面板、覆盖层、小工具）- 恢复所有3D视口
        restore_ui_elements(context)
            
        self.is_active = False
        if self._active_area:
            self._active_area.tag_redraw()



    def sample_nearby_faces(self, context, center_coord, radius, samples):
        """采样鼠标周围的多个面
        Args:
            context: 当前上下文
            center_coord: 鼠标中心坐标(x, y)
            radius: 采样半径(像素)
            samples: 采样数量
        Returns:
            list: 有效的法线列表
        """
        region = context.region
        rv3d = context.region_data
        normals = []
        ignore_gn_instances = is_heavy_geometry_nodes_scene(context)
        
        # 中心点射线检测结果
        center_direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, center_coord)
        center_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, center_coord)
        if hasattr(rv3d, 'is_perspective') and not rv3d.is_perspective:
            center_plane = view3d_utils.region_2d_to_location_3d(region, rv3d, center_coord, rv3d.view_location)
            clip_end = getattr(context.space_data, 'clip_end', 1000.0)
            center_origin = center_plane - center_direction * clip_end
        center_result = find_visible_hit(context, center_origin, center_direction, ignore_gn_instances=ignore_gn_instances)
        
        if center_result[0]:
            # 添加中心点的法线
            normals.append(center_result[2])
            
            # 生成周围点的采样
            for i in range(samples):
                # 计算采样点在圆周上的位置
                angle = 2.0 * math.pi * i / samples
                x = center_coord[0] + radius * math.cos(angle)
                y = center_coord[1] + radius * math.sin(angle)
                
                # 确保采样点在区域内
                if x < 0 or y < 0 or x >= region.width or y >= region.height:
                    continue
                    
                # 对采样点进行射线检测
                direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, (x, y))
                origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, (x, y))
                if hasattr(rv3d, 'is_perspective') and not rv3d.is_perspective:
                    sample_plane = view3d_utils.region_2d_to_location_3d(region, rv3d, (x, y), rv3d.view_location)
                    clip_end = getattr(context.space_data, 'clip_end', 1000.0)
                    origin = sample_plane - direction * clip_end
                result = find_visible_hit(context, origin, direction, ignore_gn_instances=ignore_gn_instances)
                
                if result[0]:
                    # 检查采样点是否在不同的面上(通过法线差异判断)
                    is_different_face = True
                    for normal in normals:
                        # 如果法线非常接近(夹角小于15度)，认为是同一个面
                        if normal.dot(result[2]) > 0.96:  # cos(15°) ≈ 0.96
                            is_different_face = False
                            break
                    
                    if is_different_face:
                        normals.append(result[2])
        
        return normals
        
    def calculate_average_normal(self, normals):
        """计算多个法线的加权平均值"""
        if not normals:
            return None
            
        # 如果只有一个法线，直接返回
        if len(normals) == 1:
            return normals[0]
            
        # 计算平均法线
        avg_normal = Vector((0, 0, 0))
        for normal in normals:
            avg_normal += normal
            
        # 归一化
        if avg_normal.length > 0:
            avg_normal.normalize()
            
        return avg_normal

class LIGHTING_GADGETS_PT_QUICK_PANEL(Panel):
    bl_label = "Light Settings"
    bl_idname = "LIGHTING_GADGETS_PT_quick_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_ui_units_x = 16

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'LIGHT'

    def find_connected_nodes(self, output_node, connected_nodes=None):
        """Recursively find all nodes connected to the output node"""
        if connected_nodes is None:
            connected_nodes = set()
            
        # 如果节点已经处理过，直接返回
        if output_node in connected_nodes:
            return connected_nodes
            
        connected_nodes.add(output_node)
        
        # 遍历所有输入端口
        for input in output_node.inputs:
            # 检查输入端口是否有连接
            if input.links:
                # 获取连接的来源节点
                from_node = input.links[0].from_node
                # 递归处理来源节点
                self.find_connected_nodes(from_node, connected_nodes)
                
        return connected_nodes

    def draw_node_group_inputs(self, layout, node):
        """Draw input parameters for a node group"""
        if not node.node_tree:
            return
            
        # 检查节点是否有任何未连接的输入端口
        has_unconnected_inputs = False
        for input in node.inputs:
            if not input.links and not input.hide:
                # 检查是否有任何可调整的属性
                if (hasattr(input, "default_value") or 
                    hasattr(input, "default_value_raw") or
                    input.type in {'VECTOR', 'NORMAL', 'RGBA', 'BOOLEAN'}):
                    has_unconnected_inputs = True
                    break
                
        # 如果没有未连接的输入端口，不显示这个节点组
        if not has_unconnected_inputs:
            return
            
        # 为节点组创建容器
        box = layout.box()
        row = box.row()
        row.label(text=node.name)
        row.prop(node, "mute", text="", icon='HIDE_OFF' if not node.mute else 'HIDE_ON', emboss=False)
        
        # 收集所有可显示的输入参数
        displayable_inputs = []
        for input in node.inputs:
            # 跳过已连接或隐藏的输入
            if input.links or input.hide:
                continue
            # 检查是否有可调整的属性
            if (hasattr(input, "default_value") or 
                hasattr(input, "default_value_raw") or
                input.type in {'VECTOR', 'NORMAL', 'RGBA', 'BOOLEAN'}):
                displayable_inputs.append(input)
        
        # 如果没有可显示的输入，直接返回
        if not displayable_inputs:
            return
        
        # 如果参数总数少于10个，所有参数都单独占一行
        if len(displayable_inputs) < 10:
            for input in displayable_inputs:
                row = box.row(align=True)
                is_long = len(input.name) > 12
                self._draw_single_input_parameter(input, row, is_long_row=is_long)
        else:
            # 参数较多时，分类参数：长名称和短名称
            long_name_inputs = []
            short_name_inputs = []
            
            for input in displayable_inputs:
                # 判断名称长度，超过12个字符的认为是长名称
                if len(input.name) > 12:
                    long_name_inputs.append(input)
                else:
                    short_name_inputs.append(input)
            
            # 先绘制长名称参数，每个单独占一行
            for input in long_name_inputs:
                row = box.row(align=True)
                self._draw_single_input_parameter(input, row, is_long_row=True)
            
            # 再绘制短名称参数，使用网格流布局横向排列
            if short_name_inputs:
                flow = box.grid_flow(row_major=True, columns=3, even_columns=True, even_rows=False, align=True)
                for input in short_name_inputs:
                    col = flow.column(align=True)
                    self._draw_single_input_parameter(input, col, is_long_row=False)
    
    def _draw_single_input_parameter(self, input, layout, is_long_row=False):
        """绘制单个输入参数"""
        # 单独一行的长文本：分栏布局，左侧名称，右侧控件更窄
        if is_long_row:
            split = layout.split(factor=0.75, align=True)  # 左 75%：名称；右 25%：控件
            left = split.column(align=True)
            right = split.column(align=True)
            left.label(text=input.name)

            if input.type == 'BOOLEAN':
                if hasattr(input, "default_value"):
                    right.prop(input, "default_value", text="")
            elif input.type in {'VECTOR', 'NORMAL'}:
                if hasattr(input, "default_value"):
                    right.prop(input, "default_value", text="")
                elif hasattr(input, "default_value_raw"):
                    right.prop(input, "default_value_raw", text="")
            elif input.type == 'RGBA':
                if hasattr(input, "default_value"):
                    right.prop(input, "default_value", text="")
            elif hasattr(input, "default_value"):
                if isinstance(input.default_value, float):
                    right.prop(input, "default_value", text="")
                elif isinstance(input.default_value, (tuple, list)):
                    if len(input.default_value) == 3:  # 颜色
                        right.prop(input, "default_value", text="")
                    elif len(input.default_value) == 2:  # Vector2
                        r = right.row(align=True)
                        r.prop(input, "default_value", text="", index=0)
                        r.prop(input, "default_value", text="", index=1)
                    elif len(input.default_value) == 3:  # Vector3（显式）
                        r = right.row(align=True)
                        r.prop(input, "default_value", text="", index=0)
                        r.prop(input, "default_value", text="", index=1)
                        r.prop(input, "default_value", text="", index=2)
            return

        # 非长文本（或网格排列）保持原有紧凑绘制逻辑
        # 处理不同类型的输入
        if input.type == 'BOOLEAN':
            # 布尔值输入
            if hasattr(input, "default_value"):
                layout.prop(input, "default_value", text=input.name)
                
        elif input.type == 'VECTOR' or input.type == 'NORMAL':
            # 为矢量和法线类型创建紧凑布局
            layout.label(text=input.name)
            if hasattr(input, "default_value"):
                layout.prop(input, "default_value", text="")
            elif hasattr(input, "default_value_raw"):
                # 某些节点使用 default_value_raw
                layout.prop(input, "default_value_raw", text="")
            
        elif input.type == 'RGBA':
            # 颜色输入
            layout.label(text=input.name)
            if hasattr(input, "default_value"):
                layout.prop(input, "default_value", text="")
            
        elif hasattr(input, "default_value"):
            # 处理其他类型的输入
            layout.label(text=input.name)
            
            if isinstance(input.default_value, float):
                # 数值输入
                layout.prop(input, "default_value", text="")
            elif isinstance(input.default_value, (tuple, list)):
                if len(input.default_value) == 3:  # 颜色
                    layout.prop(input, "default_value", text="")
                elif len(input.default_value) == 2:  # Vector2
                    row = layout.row(align=True)
                    row.prop(input, "default_value", text="", index=0)
                    row.prop(input, "default_value", text="", index=1)
                elif len(input.default_value) == 3:  # Vector3
                    row = layout.row(align=True)
                    row.prop(input, "default_value", text="", index=0)
                    row.prop(input, "default_value", text="", index=1)
                    row.prop(input, "default_value", text="", index=2)

    def draw(self, context):
        layout = self.layout
        light = context.active_object.data
        
        # 灯光类型
        row = layout.row()
        row.prop(light, "type", expand=True)

        # 通用属性
        col = layout.column()
        col.prop(light, "energy")
        col.prop(light, "color")
        
        # 基于灯光类型的特定属性
        if light.type == 'POINT':
            col.prop(light, "shadow_soft_size", text=bpy.app.translations.pgettext("Radius"))
        elif light.type == 'SPOT':
            col.prop(light, "shadow_soft_size", text=bpy.app.translations.pgettext("Radius"))
            col.prop(light, "spot_size")
            col.prop(light, "spot_blend")
        elif light.type == 'SUN':
            col.prop(light, "angle")
        elif light.type == 'AREA':
            # 区域光源特有的spread属性
            col.prop(light, "spread")
            col.prop(light, "shape")
            sub = col.column(align=True)
            if light.shape in {'SQUARE', 'DISK'}:
                sub.prop(light, "size")
            else:
                sub.prop(light, "size", text=bpy.app.translations.pgettext("Size X"))
                sub.prop(light, "size_y", text=bpy.app.translations.pgettext("Size Y"))
        
        # 灯光可见性控制
        layout.separator()
        box = layout.box()
        
        col = box.column()
        row = col.row(align=True)
        row.prop(context.active_object, "visible_diffuse", text=bpy.app.translations.pgettext("Diffuse"), toggle=True, icon='SHADING_TEXTURE')
        row.prop(context.active_object, "visible_glossy", text=bpy.app.translations.pgettext("Glossy"), toggle=True, icon='SHADING_RENDERED')
        
        row = col.row(align=True)
        row.prop(context.active_object, "visible_transmission", text=bpy.app.translations.pgettext("Transmission"), toggle=True, icon='SHADING_SOLID')
        row.prop(context.active_object, "visible_camera", text=bpy.app.translations.pgettext("Camera"), toggle=True, icon='CAMERA_DATA')
        
        # 投射阴影控制
        row = col.row(align=True)
        row.prop(light, "use_shadow", text=bpy.app.translations.pgettext("Cast Shadow"), toggle=True, icon='SHADING_SOLID')
        
        # 交互式灯光控制
        layout.separator()
        box = layout.box()
        col = box.column()
        col.label(text=bpy.app.translations.pgettext("Interactive Studio Light Controls"))
        
        # 获取窗口管理器属性
        wm_props = context.window_manager.lighting_gadgets_props
        
        # 切换按钮
        row = col.row()
        if wm_props.show_studio_light_controls:
            row.operator("lighting_gadgets.toggle_studio_light_controls", text=bpy.app.translations.pgettext("Disable Studio Light Controls"), icon='HIDE_OFF', depress=True)
        else:
            row.operator("lighting_gadgets.toggle_studio_light_controls", text=bpy.app.translations.pgettext("Enable Studio Light Controls"), icon='HIDE_ON', depress=False)
        
        row = col.row(align=True)
        split = row.split(factor=0.85, align=True)
        split.operator("lighting_gadgets.mirror_selected_light", text=bpy.app.translations.pgettext("Mirror Selected Light"), icon='MOD_MIRROR')
        split.prop(wm_props, "mirror_axis", text="")

        # 性能模式开关
        row = col.row()
        row.prop(wm_props, "performance_mode", text=bpy.app.translations.pgettext("Performance Mode"), icon='SETTINGS')
        
        # 如果启用了控制，显示说明
        if wm_props.show_studio_light_controls:
            col.separator()
        
        # 节点组部分
        if light.use_nodes:
            # 找到 Light Output 节点
            output_node = None
            for node in light.node_tree.nodes:
                if node.type == 'OUTPUT_LIGHT':
                    output_node = node
                    break
                    
            if output_node:
                # 获取所有与输出节点相连的节点
                connected_nodes = self.find_connected_nodes(output_node)
                
                # 检查是否有节点组需要显示
                has_node_groups = False
                for node in connected_nodes:
                    if node.type == 'GROUP':
                        # 检查是否有未连接的输入端口
                        for input in node.inputs:
                            if not input.links and hasattr(input, "default_value") and not input.hide:
                                has_node_groups = True
                                break
                        if has_node_groups:
                            break
                
                if has_node_groups:
                    layout.separator()
                    layout.label(text=bpy.app.translations.pgettext("Node Groups"))
                    
                    # 只显示相连节点中的节点组
                    for node in connected_nodes:
                        if node.type == 'GROUP':
                            self.draw_node_group_inputs(layout, node)

class LIGHTING_GADGETS_OT_QUICK_PANEL(Operator):
    bl_idname = "lighting_gadgets.quick_panel"
    bl_label = "Light Settings"
    
    @classmethod
    def poll(cls, context):
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        return (
            area and area.type == 'VIEW_3D' and region and rv3d and
            context.mode == 'OBJECT' and
            context.active_object and context.active_object.type == 'LIGHT'
        )

    def invoke(self, context, event):
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        if not (area and area.type == 'VIEW_3D' and region and rv3d):
            return {'PASS_THROUGH'}
        # 检查是否处于物体模式
        if context.mode != 'OBJECT':
            return {'PASS_THROUGH'}  # 在非物体模式下传递事件，不拦截快捷键
            
        # 检查是否选择了灯光对象，如果不是则静默忽略
        if not context.active_object or context.active_object.type != 'LIGHT':
            return {'PASS_THROUGH'}  # 静默忽略非灯光对象

        bpy.ops.wm.call_panel(name="LIGHTING_GADGETS_PT_quick_panel")
        return {'FINISHED'}

class LIGHTING_GADGETS_OT_MIRROR_SELECTED_LIGHT(Operator):
    bl_idname = "lighting_gadgets.mirror_selected_light"
    bl_label = "Mirror Selected Light"
    bl_description = "Mirror selected light(s) across world X=0 without negative scale"
    bl_options = {'REGISTER', 'UNDO'}

    @staticmethod
    def _reflect_point(vec, axis_index, pivot_value):
        out = vec.copy()
        out[axis_index] = (2.0 * pivot_value) - out[axis_index]
        return out

    @staticmethod
    def _reflect_direction(vec, axis_index):
        out = vec.copy()
        out[axis_index] = -out[axis_index]
        return out

    @classmethod
    def _mirrored_rotation_matrix(cls, matrix_world, axis_index):
        r = matrix_world.to_3x3()

        direction = r @ Vector((0.0, 0.0, -1.0))
        up = r @ Vector((0.0, 1.0, 0.0))

        direction = cls._reflect_direction(direction, axis_index)
        up = cls._reflect_direction(up, axis_index)

        z_axis = -direction
        if z_axis.length <= 1e-10:
            z_axis = Vector((0.0, 0.0, 1.0))
        else:
            z_axis.normalize()

        y_axis = up - z_axis * up.dot(z_axis)
        if y_axis.length <= 1e-10:
            fallback = Vector((0.0, 0.0, 1.0)) if abs(z_axis.z) < 0.9 else Vector((0.0, 1.0, 0.0))
            y_axis = fallback - z_axis * fallback.dot(z_axis)

        y_axis.normalize()

        x_axis = y_axis.cross(z_axis)
        if x_axis.length <= 1e-10:
            x_axis = Vector((1.0, 0.0, 0.0))
        else:
            x_axis.normalize()

        y_axis = z_axis.cross(x_axis)
        y_axis.normalize()

        return Matrix((x_axis, y_axis, z_axis)).transposed()

    @classmethod
    def _mirrored_matrix_world(cls, matrix_world, axis_index, pivot_value):
        loc = matrix_world.translation
        loc = cls._reflect_point(loc, axis_index, pivot_value)

        rot = cls._mirrored_rotation_matrix(matrix_world, axis_index)

        scale = matrix_world.to_scale()
        scale = Vector((abs(scale.x), abs(scale.y), abs(scale.z)))

        scale_m = Matrix.Diagonal((scale.x, scale.y, scale.z, 1.0))
        m = rot.to_4x4() @ scale_m
        m.translation = loc
        return m

    @classmethod
    def poll(cls, context):
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        return (
            area and area.type == 'VIEW_3D' and region and rv3d and
            context.mode == 'OBJECT'
        )

    def execute(self, context):
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        if not (area and area.type == 'VIEW_3D' and region and rv3d):
            return {'PASS_THROUGH'}
        lights = [obj for obj in context.selected_objects if obj and obj.type == 'LIGHT']
        if not lights and context.active_object and context.active_object.type == 'LIGHT':
            lights = [context.active_object]

        if not lights:
            return {'CANCELLED'}

        previous_selected = list(context.selected_objects)
        for obj in previous_selected:
            try:
                obj.select_set(False)
            except Exception:
                pass

        axis_index = 0
        pivot_value = 0.0
        
        # 获取镜像轴设置
        if hasattr(context.window_manager, 'lighting_gadgets_props'):
            axis_index = int(context.window_manager.lighting_gadgets_props.mirror_axis)
            
        new_objects = []

        # 根据当前语言环境决定后缀
        lang = context.preferences.view.language
        if lang == 'zh_CN':
            suffix = "_镜像"
        elif lang == 'ja_JP':
            suffix = "_ミラー"
        else:
            suffix = "_Mirror"

        for src in lights:
            new_obj = src.copy()
            new_obj.name = src.name + suffix
            new_obj.data = src.data.copy()

            if src.users_collection:
                for coll in src.users_collection:
                    coll.objects.link(new_obj)
            else:
                context.scene.collection.objects.link(new_obj)

            new_obj.matrix_world = self._mirrored_matrix_world(src.matrix_world, axis_index, pivot_value)
            if getattr(new_obj.data, "use_nodes", False) and getattr(new_obj.data, "node_tree", None):
                try:
                    from .lighting_nodes import mirror_softbox_group_node_parameters
                    mirror_softbox_group_node_parameters(new_obj.data.node_tree)
                except Exception:
                    pass
            new_obj.select_set(True)
            new_objects.append(new_obj)

        if new_objects:
            context.view_layer.objects.active = new_objects[-1]

        return {'FINISHED'}

class LIGHTING_GADGETS_OT_SELECT_LIGHT_BY_REFLECTION(Operator):
    bl_idname = "lighting_gadgets.select_light_by_reflection"
    bl_label = "Select Light by Reflection"
    bl_description = "Select the light that would reflect from the surface point to the view (Alt + Right Mouse)"
    bl_options = {'REGISTER'}
    
    # 添加类变量，用于存储绘制回调和状态
    _draw_handle = None
    _timer = None
    _hit_location = None
    _selected_light = None
    _line_opacity = 1.0
    _draw_duration = 1.0  # 绘制持续时间（秒），缩短一半
    _start_time = 0
    _multi_select = False  # 是否为多选模式
    _selected_lights = []  # 多选模式下的灯光列表
    
    # 注意：循环选择状态现在存储在全局状态管理器中，而不是操作符实例中
    
    @classmethod
    def poll(cls, context):
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        return (
            area and area.type == 'VIEW_3D' and region and rv3d and
            context.mode == 'OBJECT'
        )

    def modal(self, context, event):
        """处理绘制回调的模态操作"""
        # 即使是极短的sleep(0.0015)也能触发布局/绘制线程的上下文切换，
        # 显著减少输入延迟，让操作更"跟手"
        # 无论是否绘制文本，这个让步必须执行
        if is_vulkan_backend():
            time.sleep(0.0015)  # Vulkan后端需要让步以避免Cycles渲染卡顿
        # time.sleep(0.0015)
        
        # 只在计时器事件时重绘（淡出效果需要）
        if event.type == 'TIMER':
            # 检查并恢复灯光颜色
            _state_manager.check_restore_colors()
            
            if context.area:
                # 计算已经过去的时间
                elapsed = time.time() - self._start_time
                if elapsed > self._draw_duration:
                    # 如果超过绘制持续时间，清理并退出
                    self.cleanup(context)
                    return {'FINISHED'}
                else:
                    # 更新线条的不透明度，实现淡出效果
                    self._line_opacity = 1.0 - (elapsed / self._draw_duration)
                    # 只在淡出效果变化时重绘
                    context.area.tag_redraw()
                
        return {'PASS_THROUGH'}
            
    @staticmethod
    def draw_selection_ray(op_instance, context):
        """绘制反选灯光时的独立命中选择视觉效果"""
        try:
            # 只在激活视口绘制，减少性能开销
            if not hasattr(op_instance, "_active_area") or context.area != op_instance._active_area:
                return
                
            if not hasattr(op_instance, "_hit_location") or not hasattr(op_instance, "_selected_light") or op_instance._hit_location is None or op_instance._selected_light is None:
                return
                
            # 检查灯光对象是否仍然有效（未被删除）
            try:
                # 尝试访问对象的名称来检查对象是否仍然有效
                _ = op_instance._selected_light.name
                # 检查对象是否仍在场景中
                if op_instance._selected_light.name not in context.scene.objects:
                    return
            except ReferenceError:
                # 对象已被删除，清理引用并返回
                op_instance._selected_light = None
                return
                
            # 3D坐标点
            hit_3d = op_instance._hit_location
            light_3d = op_instance._selected_light.matrix_world.translation
            
            # 获取灯光颜色
            light_data = op_instance._selected_light.data
            light_color = light_data.color
            
            # 检查是否处于临时闪烁状态，如果是则使用原始颜色
            # 注意：_state_manager 是模块级全局变量
            if light_data.name in _state_manager._temp_color_lights:
                light_color = _state_manager._temp_color_lights[light_data.name]['original_color']
            
            # 组合颜色和不透明度，使用灯光自身的颜色
            color = (light_color[0], light_color[1], light_color[2], op_instance._line_opacity)
            
            # 使用新的深度测试实现绘制反射线，使用更粗的线条（3.0）
            draw_reflection_line_depth(context, hit_3d, light_3d, color, op_instance._line_opacity, thickness=3.0)
                
        except Exception as e:
            pass

    def draw_reflection_line(op_instance, context):
        """绘制从命中点到灯光的指示线，使用新的深度测试实现"""
        try:
            # 只在激活视口绘制，减少性能开销
            if not hasattr(op_instance, "_active_area") or context.area != op_instance._active_area:
                return
                
            if not hasattr(op_instance, "_hit_location") or not hasattr(op_instance, "_selected_light") or op_instance._hit_location is None or op_instance._selected_light is None:
                return
                
            # 检查灯光对象是否仍然有效（未被删除）
            try:
                # 尝试访问对象的名称来检查对象是否仍然有效
                _ = op_instance._selected_light.name
                # 检查对象是否仍在场景中
                if op_instance._selected_light.name not in context.scene.objects:
                    return
            except ReferenceError:
                # 对象已被删除，清理引用并返回
                op_instance._selected_light = None
                return
                
            # 3D坐标点
            hit_3d = op_instance._hit_location
            light_3d = op_instance._selected_light.matrix_world.translation
            
            # 使用新的深度测试实现绘制反射线
            color = (1.0, 1.0, 0.2, op_instance._line_opacity)  # 亮黄色
            draw_reflection_line_depth(context, hit_3d, light_3d, color, op_instance._line_opacity)
                
        except Exception as e:
            pass

    def draw_reflection_lines(op_instance, context):
        """绘制从命中点到多个灯光的指示线，使用新的深度测试实现"""
        try:
            # 只在激活视口绘制，减少性能开销
            if not hasattr(op_instance, "_active_area") or context.area != op_instance._active_area:
                return
                
            if not hasattr(op_instance, "_hit_location") or not hasattr(op_instance, "_selected_lights") or op_instance._hit_location is None or not op_instance._selected_lights:
                return
                
            # 3D击中点
            hit_3d = op_instance._hit_location
            
            # 为每个灯光绘制一条线
            for light in op_instance._selected_lights:
                # 检查灯光对象是否仍然有效（未被删除）
                try:
                    # 尝试访问对象的名称来检查对象是否仍然有效
                    _ = light.name
                    # 检查对象是否仍在场景中
                    if light.name not in context.scene.objects:
                        continue
                except ReferenceError:
                    # 对象已被删除，跳过
                    continue
                    
                # 3D灯光位置
                light_3d = light.matrix_world.translation
                
                # 获取灯光颜色
                light_data = light.data
                light_color = light_data.color
                
                # 检查是否处于临时闪烁状态，如果是则使用原始颜色
                # 注意：_state_manager 是模块级全局变量
                if light_data.name in _state_manager._temp_color_lights:
                    light_color = _state_manager._temp_color_lights[light_data.name]['original_color']
                
                # 使用新的深度测试实现绘制反射线
                # color = (1.0, 1.0, 0.2, op_instance._line_opacity)  # 亮黄色
                color = (light_color[0], light_color[1], light_color[2], op_instance._line_opacity)
                draw_reflection_line_depth(context, hit_3d, light_3d, color, op_instance._line_opacity, thickness=3.0)
                
        except Exception as e:
            pass
            
    def cleanup(self, context):
        """清理绘制回调和计时器"""
        # 尝试检查并恢复颜色（以防万一）
        global _state_manager
        _state_manager.check_restore_colors()
        
        # 移除绘制回调
        if self._draw_handle is not None:
            try:
                bpy.types.SpaceView3D.draw_handler_remove(self._draw_handle, 'WINDOW')
            except:
                pass
            self._draw_handle = None
            
        # 移除计时器
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
            
        # 重设属性
        self._hit_location = None
        self._selected_light = None
        self._selected_lights = []
        self._line_opacity = 1.0
        self._multi_select = False
        
        # 注意：循环选择状态现在存储在全局状态管理器中，不需要在这里重置
        # 全局状态管理器会保持这些状态，以便支持多次调用操作符时的循环选择功能
        
    def invoke(self, context, event):
        global _state_manager
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        if not (area and area.type == 'VIEW_3D' and region and rv3d):
            return {'PASS_THROUGH'}
        
        # 检查是否按下了Shift键，如果是则启用多选模式
        self._multi_select = event.shift
        
        # 记录激活视口，用于限制绘制范围
        self._active_area = context.area
        
        # 获取鼠标位置
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        
        # 获取视图信息
        region = context.region
        rv3d = context.region_data
        
        # 从鼠标位置创建射线（兼容正交视图）
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos)
        if hasattr(rv3d, 'is_perspective') and not rv3d.is_perspective:
            # 正交模式下的正确射线计算
            plane_point = view3d_utils.region_2d_to_location_3d(region, rv3d, mouse_pos, rv3d.view_location)
            clip_start = getattr(context.space_data, 'clip_start', 0.1)
            # 在正交模式下，射线原点应该在视口平面前方，确保能正确检测到模型表面
            ray_origin = plane_point - view_vector * max(clip_start * 10, 1.0)
        
        # 执行射线检测，跳过不可见物体
        result = find_visible_hit(context, ray_origin, view_vector)
        
        if result[0]:  # 如果射线击中了物体
            hit_location = result[1]
            hit_normal = result[2]
            hit_object = result[4]  # 获取被击中的物体
            is_instance_hit = result[5] if len(result) > 5 else False
            
            # 存储命中点位置用于绘制
            self._hit_location = hit_location
            
            # 计算反射方向
            # 使用公式: R = V - 2(V·N)N，其中V是视图方向，N是表面法线
            dot_product = view_vector.dot(hit_normal)
            reflection_dir = view_vector - (2 * dot_product * hit_normal)
            reflection_dir.normalize()
            
            # 查找所有可见的灯光
            all_lights = [obj for obj in context.scene.objects if obj.type == 'LIGHT']
            lights = [light for light in all_lights if is_light_visible_and_in_view_layer(light, context.view_layer)]
            
            # 过滤出与被击中物体有灯光链接关系的灯光
            linked_lights = [light for light in lights if check_light_linking(light, hit_object, is_instance_hit)]
            
            # 如果没有与物体链接的灯光，使用所有可见灯光作为备选
            if linked_lights:
                candidate_lights = linked_lights
            else:
                # 只有当没有任何灯光链接到该物体时，才回退到所有灯光
                # 这可能是因为没有使用灯光链接，或者逻辑判定失败
                # 为了避免用户困惑，我们可以选择只在调试模式下报告
                # print(f"Warning: No linked lights found for {hit_object.name}, falling back to all lights")
                candidate_lights = lights
            
            # 如果没有候选灯光，返回
            if not candidate_lights:
                if lights:
                    template = bpy.app.translations.pgettext("Found visible lights, but none has a light linking relationship with the clicked object '{name}'")
                    self.report({'WARNING'}, template.format(name=hit_object.name))
                elif all_lights:
                    template = bpy.app.translations.pgettext("There are lights in the scene, but none are in the current view layer or they are hidden")
                    self.report({'WARNING'}, template)
                else:
                    template = bpy.app.translations.pgettext("No lights found. Please add a light to the scene first.")
                    self.report({'WARNING'}, template)
                return {'CANCELLED'}
            
            # 根据是否为多选模式，选择不同的灯光
            if self._multi_select:
                # 多选模式：选择所有与反射方向夹角小于约31.8度的灯光（余弦值大于0.85）
                selected_lights = []
                for light in candidate_lights:
                    # 计算从命中点到灯光的方向
                    to_light = (light.matrix_world.translation - hit_location).normalized()
                    
                    # 计算与反射方向的点积（余弦相似度）
                    similarity = reflection_dir.dot(to_light)
                    
                    # 如果夹角小于约31度（余弦值大于0.85），则选择该灯光
                    if similarity > ANGLE_SIMILARITY_LOW:
                        # 确保灯光在当前视图层中
                        if light.name in context.view_layer.objects:
                            selected_lights.append((light, similarity))
                
                # 如果没有找到符合条件的灯光
                if not selected_lights:
                    template = bpy.app.translations.pgettext("No suitable light found")
                    self.report({'WARNING'}, template)
                    return {'CANCELLED'}
                
                # 按相似度排序，从高到低
                selected_lights.sort(key=lambda x: x[1], reverse=True)
                
                # 存储选中的灯光列表
                self._selected_lights = [light for light, _ in selected_lights]
                
                try:
                    # 取消选择所有对象
                    for obj in context.selected_objects:
                        obj.select_set(False)
                    
                    # 选择所有符合条件的灯光
                    for light in self._selected_lights:
                        light.select_set(True)
                    
                    # 激活第一个（最匹配的）灯光
                    context.view_layer.objects.active = self._selected_lights[0]
                    
                    # 颜色闪烁反馈
                    try:
                        # 获取插件首选项 - 使用更健壮的方式
                        addon_prefs = None
                        package_name = __package__
                        
                        # 1. 尝试直接使用 __package__
                        if package_name and package_name in context.preferences.addons:
                            addon_prefs = context.preferences.addons[package_name].preferences
                        # 2. 尝试使用顶层包名
                        elif __name__ and __name__.partition('.')[0] in context.preferences.addons:
                            addon_prefs = context.preferences.addons[__name__.partition('.')[0]].preferences
                        
                        if addon_prefs and hasattr(addon_prefs, "enable_selection_color_flash") and addon_prefs.enable_selection_color_flash:
                            flash_color = addon_prefs.selection_flash_color
                            flash_duration = 0.2  # 闪烁持续时间
                            for light in self._selected_lights:
                                _state_manager.set_temp_color(light.data, flash_color, flash_duration)
                    except Exception as e:
                        print(f"Error in selection color flash: {e}")
                    
                    # 设置开始时间
                    self._start_time = time.time()
                    
                    # 添加绘制回调
                    self._draw_handle = bpy.types.SpaceView3D.draw_handler_add(
                        LIGHTING_GADGETS_OT_SELECT_LIGHT_BY_REFLECTION.draw_reflection_lines, (self, context), 'WINDOW', 'POST_PIXEL')
                    
                    # 添加计时器
                    self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
                    context.window_manager.modal_handler_add(self)
                    
                    # 报告选择的灯光数量
                    template = bpy.app.translations.pgettext("Selected {count} lights")
                    self.report({'INFO'}, template.format(count=len(self._selected_lights)))
                    
                    # 返回RUNNING_MODAL，让我们的回调继续运行
                    return {'RUNNING_MODAL'}
                except RuntimeError as e:
                    template = bpy.app.translations.pgettext("Could not select lights: {error}")
                    self.report({'ERROR'}, template.format(error=str(e)))
                    return {'CANCELLED'}
            else:
                # 单选模式：实现循环选择逻辑
                
                # 1. 始终重新计算当前所有符合条件的候选灯光
                current_candidates = []
                for light in candidate_lights:
                    # 计算从命中点到灯光的方向
                    to_light = (light.matrix_world.translation - hit_location).normalized()
                    
                    # 计算与反射方向的点积（余弦相似度）
                    similarity = reflection_dir.dot(to_light)
                    
                    # 如果夹角小于约31度（余弦值大于0.85），则加入候选列表
                    if similarity > ANGLE_SIMILARITY_LOW:
                        # 确保灯光在当前视图层中
                        if light.name in context.view_layer.objects:
                            current_candidates.append((light, similarity))
                
                # 按相似度排序，从高到低
                current_candidates.sort(key=lambda x: x[1], reverse=True)
                
                if not current_candidates:
                    template = bpy.app.translations.pgettext("No suitable light found")
                    self.report({'WARNING'}, template)
                    return {'CANCELLED'}

                # 2. 检查是否在同一位置点击（位置变化小于0.01单位视为同一位置）
                is_same_location = (_state_manager.light_selection_last_hit_location is not None and 
                                  (hit_location - _state_manager.light_selection_last_hit_location).length < 0.01)

                # 3. 确定要选择的灯光索引
                target_index = 0
                
                if is_same_location:
                    # 尝试在新的候选列表中找到上一次选择的灯光（或当前激活的灯光）
                    last_selected_light = context.active_object
                    found_index = -1
                    
                    if last_selected_light:
                        for i, (light, _) in enumerate(current_candidates):
                            if light == last_selected_light:
                                found_index = i
                                break
                    
                    if found_index != -1:
                        # 如果找到了，选择下一个
                        target_index = (found_index + 1) % len(current_candidates)
                    else:
                        # 如果没找到（比如灯光被删除了），或者没有激活对象，从0开始
                        target_index = 0
                else:
                    # 新位置，重置为0
                    target_index = 0

                # 更新状态管理器
                _state_manager.light_selection_candidates = current_candidates
                _state_manager.light_selection_current_index = target_index
                _state_manager.light_selection_last_hit_location = hit_location
                _state_manager.light_selection_last_view_matrix = context.region_data.view_matrix.copy()

                # 4. 执行选择
                selected_light, similarity = current_candidates[target_index]
                
                try:
                    # 取消选择所有对象
                    for obj in context.selected_objects:
                        obj.select_set(False)
                    
                    # 选择并激活当前灯光
                    selected_light.select_set(True)
                    context.view_layer.objects.active = selected_light
                    
                    # 颜色闪烁反馈
                    try:
                        prefs = context.preferences.addons[__package__].preferences
                        if prefs.enable_selection_color_flash:
                            flash_color = prefs.selection_flash_color
                            flash_duration = 0.2  # 闪烁持续时间
                            _state_manager.set_temp_color(selected_light.data, flash_color, flash_duration)
                    except Exception as e:
                        pass
                    
                    # 存储选中的灯光用于绘制
                    self._selected_light = selected_light
                    
                    # 设置开始时间
                    self._start_time = time.time()
                    
                    # 添加绘制回调，使用新的独立视觉效果
                    args = (self, context)
                    self._draw_handle = bpy.types.SpaceView3D.draw_handler_add(
                        LIGHTING_GADGETS_OT_SELECT_LIGHT_BY_REFLECTION.draw_selection_ray, args, 'WINDOW', 'POST_PIXEL')
                    
                    # 添加计时器
                    self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
                    context.window_manager.modal_handler_add(self)
                    
                    # 报告选择的灯光信息（包括当前索引和总数）
                    if len(current_candidates) > 1:
                        template = bpy.app.translations.pgettext("Selected light: {name} ({current}/{total})")
                        self.report({'INFO'}, template.format(
                            name=selected_light.name, 
                            current=target_index + 1, 
                            total=len(current_candidates)))
                    else:
                        template = bpy.app.translations.pgettext("Selected light: {name}")
                        self.report({'INFO'}, template.format(name=selected_light.name))
                    
                    # 返回RUNNING_MODAL，让我们的回调继续运行
                    return {'RUNNING_MODAL'}
                except RuntimeError as e:
                    template = bpy.app.translations.pgettext("Could not select lights: {error}")
                    self.report({'ERROR'}, template.format(error=str(e)))
                    return {'CANCELLED'}
        else:
            template = bpy.app.translations.pgettext("No surface hit. Make sure the mouse is pointing at an object in the scene.")
            self.report({'WARNING'}, template)
            return {'CANCELLED'}

class LIGHTING_GADGETS_OT_clean_light_linking(Operator):
    """Organize Light Linking Collections (Hide used light/shadow linking collections)"""
    bl_idname = "lighting.clean_light_linking"
    bl_label = "Organize Light Linking Collections"
    bl_description = "Hide collections used for light and shadow linking to clean up the Outliner"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        used_collections = set()
        for obj in bpy.data.objects:
            if obj.type == 'LIGHT':
                # 检查灯光链接
                ll = getattr(obj, "light_linking", None)
                if ll and ll.receiver_collection:
                    used_collections.add(ll.receiver_collection)
                
                # 检查阴影链接
                sl = getattr(obj, "shadow_linking", None)
                if sl and sl.receiver_collection:
                    used_collections.add(sl.receiver_collection)

        # 识别关键词
        keywords = ["的灯光链接", "的阴影链接", "Light Link", "Shadow Link", ".LL", ".SL"]

        count = 0
        for scene in bpy.data.scenes:
            root_col = scene.collection
            to_hide = []
            
            # 仅检查根目录下的直接子集合 (更安全)
            for child in root_col.children:
                # A. 基础过滤：本地数据且非资产
                if child.library is not None or child.asset_data is not None:
                    continue
                
                # B. 显式引用检查：灯光正在使用的
                is_explicitly_used = child in used_collections
                
                # C. 名称匹配
                name_match = any(k in child.name for k in keywords)
                
                # D. 核心优化：全内容共享验证 (支持物体和子集合)
                contents = list(child.objects) + list(child.children)
                
                def is_item_shared(item):
                    if isinstance(item, bpy.types.Object):
                        return len(item.users_collection) > 1
                    elif isinstance(item, bpy.types.Collection):
                        # 检查有多少个集合或场景包含这个子集合
                        count = sum(1 for c in bpy.data.collections if item.name in c.children)
                        count += sum(1 for s in bpy.data.scenes if item.name in s.collection.children)
                        return count > 1
                    return False

                # 如果没有内容，或者所有内容都是共享的，则视为冗余
                all_content_shared = True
                if contents:
                    all_content_shared = all(is_item_shared(item) for item in contents)
                
                # 最终判定逻辑
                if is_explicitly_used or (name_match and all_content_shared):
                    to_hide.append(child)

            for child in to_hide:
                try:
                    root_col.children.unlink(child)
                    count += 1
                except Exception:
                    pass
        
        template = bpy.app.translations.pgettext("Hidden {count} light linking collections")
        self.report({'INFO'}, template.format(count=count))
        return {'FINISHED'}

class LIGHTING_GADGETS_OT_TOGGLE_STUDIO_LIGHT_CONTROLS(Operator):
    bl_idname = "lighting_gadgets.toggle_studio_light_controls"
    bl_label = "Toggle Light Controls"
    bl_description = "Toggle the display of light control points"
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context):
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        return area and area.type == 'VIEW_3D' and region and rv3d
    
    def execute(self, context):
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        if not (area and area.type == 'VIEW_3D' and region and rv3d):
            return {'PASS_THROUGH'}
        # 使用窗口管理器级别的属性
        if hasattr(context.window_manager, 'lighting_gadgets_props'):
            scene_props = context.window_manager.lighting_gadgets_props
            # 切换状态
            scene_props.show_studio_light_controls = not scene_props.show_studio_light_controls
            # 直接调用更新函数
            update_studio_light_controls_display(scene_props, context)
            
            if scene_props.show_studio_light_controls:
                self.report({'INFO'}, bpy.app.translations.pgettext("Light controls enabled"))
            else:
                self.report({'INFO'}, bpy.app.translations.pgettext("Light controls disabled"))
        else:
            self.report({'ERROR'}, bpy.app.translations.pgettext("Light controls property not found"))
        
        return {'FINISHED'}

class LIGHTING_GADGETS_OT_STUDIO_LIGHT_CONTROL_MODAL(Operator):
    bl_idname = "lighting_gadgets.studio_light_control_modal"
    bl_label = "Light Control Modal"
    bl_description = "Modal operator for light control interactions"
    bl_options = {'REGISTER'}
    
    # 类变量用于存储状态
    _clicked_light = None
    _solo_mode = False
    _original_visibility = {}
    # 新增：临时关闭灯光强度的状态
    _temp_disabled_light = None
    _original_energy = None
    
    @classmethod
    def poll(cls, context):
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        return area and area.type == 'VIEW_3D' and region and rv3d
    
    def invoke(self, context, event):
        """启动模态操作符"""
        global _state_manager
        
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        if not (area and area.type == 'VIEW_3D' and region and rv3d):
            return {'PASS_THROUGH'}
        
        try:
            scene_props = context.window_manager.lighting_gadgets_props
            if not scene_props.show_studio_light_controls:
                return {'CANCELLED'}
        except Exception:
            return {'CANCELLED'}

        # 如果已经有模态操作符在运行，直接返回
        if _state_manager.modal_operator_running:
            return {'CANCELLED'}
        
        # 重置状态
        self._clicked_light = None
        _state_manager.solo_mode = False
        _state_manager.original_visibility.clear()
        # 重置临时关闭灯光的状态
        _state_manager.temp_disabled_light = None
        _state_manager.original_energy = None
        
        # 记录激活视口
        _state_manager.active_area = context.area
        
        # 注意：独显功能不应该自动隐藏UI元素，这是两个独立的功能
        # 只有在用户明确需要时才隐藏UI元素，不由独显模式自动触发
        
        # 标记模态操作符正在运行
        _state_manager.modal_session_id += 1
        self._session_id = _state_manager.modal_session_id
        self._timer = None
        _state_manager.modal_operator_running = True
        
        try:
            self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        except Exception:
            self._timer = None

        # 添加模态处理器
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        global _state_manager
        
        if event.type == 'ESC' and event.value == 'PRESS':
            try:
                scene_props = context.window_manager.lighting_gadgets_props
                scene_props.show_studio_light_controls = False
            except Exception:
                pass
            self.cleanup(context)
            return {'CANCELLED'}

        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            return {'PASS_THROUGH'}

        if event.type == 'TIMER':
            try:
                if getattr(self, "_session_id", None) != _state_manager.modal_session_id:
                    self.cleanup(context)
                    return {'CANCELLED'}
            except Exception:
                self.cleanup(context)
                return {'CANCELLED'}

            if not _state_manager.modal_operator_running:
                self.cleanup(context)
                return {'CANCELLED'}

            try:
                scene_props = context.window_manager.lighting_gadgets_props
                if not scene_props.show_studio_light_controls:
                    self.cleanup(context)
                    return {'CANCELLED'}
            except Exception:
                self.cleanup(context)
                return {'CANCELLED'}

            if _state_manager.active_area is None:
                self.cleanup(context)
                return {'CANCELLED'}

            try:
                if _state_manager.active_area.type != 'VIEW_3D':
                    self.cleanup(context)
                    return {'CANCELLED'}
                _state_manager.active_area.tag_redraw()
            except Exception:
                pass

        # 注意：现在直接使用 event.shift 检测实时状态，不再需要跟踪shift键状态
        
        # 只处理操控点相关的鼠标事件
        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                # 检查是否点击在操控点上
                clicked_light = self.get_light_at_mouse(context, event)
                if clicked_light:
                    # 直接检测当前事件的Shift键状态，而不依赖跟踪的状态
                    if event.shift:
                        # Shift+左键：临时关闭灯光强度
                        if _state_manager.temp_disabled_light != clicked_light:
                            # 如果之前有其他灯光被临时关闭，先恢复它
                            if _state_manager.temp_disabled_light and _state_manager.original_energy is not None:
                                _state_manager.temp_disabled_light.data.energy = _state_manager.original_energy
                            
                            # 保存当前灯光的原始强度并设为0
                            _state_manager.temp_disabled_light = clicked_light
                            _state_manager.original_energy = clicked_light.data.energy
                            clicked_light.data.energy = 0.0
                            
                            # 强制刷新视图
                            context.area.tag_redraw()
                        return {'RUNNING_MODAL'}
                    else:
                        # 普通左键：进入独显模式
                        self._clicked_light = clicked_light
                        self.enter_solo_mode(context, self._clicked_light)
                        return {'RUNNING_MODAL'}
                # 如果没有点击在操控点上，让事件正常传递
                return {'PASS_THROUGH'}
            
            elif event.value == 'RELEASE':
                # 松开左键时的处理
                if _state_manager.temp_disabled_light and _state_manager.original_energy is not None:
                    # 如果有临时关闭的灯光，恢复其强度（无论是否按住Shift）
                    _state_manager.temp_disabled_light.data.energy = _state_manager.original_energy
                    _state_manager.temp_disabled_light = None
                    _state_manager.original_energy = None
                    
                    # 灯光属性已变化，让Blender自动重绘（移除手动重绘）
                    return {'RUNNING_MODAL'}
                elif self._clicked_light and not event.shift:
                    # 普通左键松开：恢复所有灯光（仅在非Shift模式下）
                    self.exit_solo_mode(context)
                    # 选择点击的灯光
                    for obj in context.selected_objects:
                        obj.select_set(False)
                    self._clicked_light.select_set(True)
                    context.view_layer.objects.active = self._clicked_light
                    self._clicked_light = None
                    return {'RUNNING_MODAL'}
                # 如果没有需要处理的状态，让事件正常传递
                return {'PASS_THROUGH'}
        
        # 让其他所有事件正常传递，不拦截
        return {'PASS_THROUGH'}
    
    def get_light_at_mouse(self, context, event):
        """获取鼠标位置下的灯光对象"""
        # 检查操控点功能是否开启
        try:
            scene_props = context.window_manager.lighting_gadgets_props
            if not scene_props.show_studio_light_controls:
                return None
        except AttributeError:
            # 如果属性不存在，说明插件未正确初始化，直接返回None
            return None
            
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        region = context.region
        rv3d = context.region_data
        
        # 检查3D视图上下文是否有效
        if not region or not rv3d:
            return None
        
        # 检查所有可见且选中的灯光
        for obj in context.scene.objects:
            if obj.type == 'LIGHT' and obj.visible_get() and obj.select_get():
                try:
                    # 将灯光的世界坐标转换为屏幕坐标
                    light_pos_2d = location_3d_to_region_2d(region, rv3d, obj.location)
                    if light_pos_2d:
                        # 计算鼠标与操控点的距离
                        distance = ((mouse_pos[0] - light_pos_2d[0]) ** 2 + 
                                   (mouse_pos[1] - light_pos_2d[1]) ** 2) ** 0.5
                        if distance <= 15:  # 操控点半径
                            return obj
                except (AttributeError, TypeError) as e:
                    continue
        return None
    
    def enter_solo_mode(self, context, light_obj):
        """进入独显模式"""
        global _state_manager
        
        if _state_manager.solo_mode:
            # 如果已经在独显模式，先退出
            self.exit_solo_mode(context)
        
        # 进入独显模式
        _state_manager.solo_mode = True
        _state_manager.original_visibility.clear()
        
        # 保存所有灯光的原始可见性并隐藏其他灯光
        for obj in context.scene.objects:
            if obj.type == 'LIGHT':
                _state_manager.original_visibility[obj.name] = obj.visible_get()
                if obj != light_obj:
                    # 检查对象是否在当前视图层中，避免隐藏不在视图层中的对象
                    try:
                        if obj.name in context.view_layer.objects:
                            obj.hide_set(True)
                    except (RuntimeError, AttributeError) as e:
                        pass
        
        # 暂时禁用世界环境的世界输出节点
        try:
            world = context.scene.world
            if world and world.node_tree:
                for node in world.node_tree.nodes:
                    if node.type == 'OUTPUT_WORLD':
                        _state_manager.world_output_node = node
                        _state_manager.world_output_muted = node.mute
                        
                        # 禁用输出节点本身
                        if not node.mute:
                            node.mute = True
                        
                        # 查找并禁用连接到表面输入插座的节点或节点组
                        surface_input = node.inputs.get('Surface')
                        if surface_input and surface_input.is_linked:
                            # 获取连接到表面输入的所有链接
                            for link in surface_input.links:
                                from_node = link.from_node
                                # 禁用连接到表面输入的节点
                                if hasattr(from_node, 'mute'):
                                    # 保存原始状态
                                    if from_node.name not in _state_manager.original_visibility:
                                        _state_manager.original_visibility[from_node.name] = from_node.mute
                                    # 禁用节点
                                    from_node.mute = True
                        
                        break
        except Exception as e:
            pass
        
        # 强制刷新视图
        context.area.tag_redraw()
    
    def exit_solo_mode(self, context):
        """退出独显模式"""
        global _state_manager
        
        if not _state_manager.solo_mode:
            return
        
        _state_manager.solo_mode = False
        
        # 恢复所有灯光的原始可见性
        for obj in context.scene.objects:
            if obj.type == 'LIGHT' and obj.name in _state_manager.original_visibility:
                # 检查对象是否在当前视图层中，避免操作不在视图层中的对象
                try:
                    if obj.name in context.view_layer.objects:
                        obj.hide_set(not _state_manager.original_visibility[obj.name])
                except (RuntimeError, AttributeError) as e:
                    pass
        
        # 恢复临时关闭的灯光强度
        if _state_manager.temp_disabled_light and _state_manager.original_energy is not None:
            _state_manager.temp_disabled_light.data.energy = _state_manager.original_energy
            _state_manager.temp_disabled_light = None
            _state_manager.original_energy = None
        
        # 恢复世界环境输出节点的原始状态
        try:
            if _state_manager.world_output_node is not None:
                # 恢复输出节点本身
                _state_manager.world_output_node.mute = _state_manager.world_output_muted
                
                # 恢复连接到表面输入插座的节点或节点组
                surface_input = _state_manager.world_output_node.inputs.get('Surface')
                if surface_input and surface_input.is_linked:
                    # 获取连接到表面输入的所有链接
                    for link in surface_input.links:
                        from_node = link.from_node
                        # 恢复连接到表面输入的节点
                        if hasattr(from_node, 'mute') and from_node.name in _state_manager.original_visibility:
                            from_node.mute = _state_manager.original_visibility[from_node.name]
                            # 从状态管理器中移除
                            del _state_manager.original_visibility[from_node.name]
                
                _state_manager.world_output_node = None
                _state_manager.world_output_muted = False
        except Exception as e:
            pass
        
        # 强制刷新视图
        context.area.tag_redraw()
        
        _state_manager.original_visibility.clear()
        self.report({'INFO'}, bpy.app.translations.pgettext("Exited solo mode"))
    
    def cancel(self, context):
        """操作符被取消时的清理"""
        self.cleanup(context)
        return {'CANCELLED'}
    
    def finish(self, context):
        """操作符正常完成时的清理"""
        self.cleanup(context)
        return {'FINISHED'}
    
    def cleanup(self, context):
        """操作符退出时的统一清理"""
        global _state_manager
        
        if getattr(self, "_timer", None) is not None:
            try:
                context.window_manager.event_timer_remove(self._timer)
            except Exception:
                pass
            self._timer = None

        # 清理操作符自身的状态
        if _state_manager.solo_mode:
            self.exit_solo_mode(context)
        
        # 清理临时灯光状态
        if _state_manager.temp_disabled_light and _state_manager.original_energy is not None:
            _state_manager.temp_disabled_light.data.energy = _state_manager.original_energy
            _state_manager.temp_disabled_light = None
            _state_manager.original_energy = None
        
        # 重置状态管理器的模态操作符状态
        _state_manager.modal_operator_running = False
        
        # 注意：不清除循环选择相关状态，以便支持多次调用操作符时的循环选择功能
        # 只清理与当前模态操作符相关的状态
        _state_manager.solo_mode = False
        _state_manager.original_visibility.clear()
        _state_manager.temp_disabled_light = None
        _state_manager.original_energy = None
        _state_manager.world_output_node = None
        _state_manager.world_output_muted = False
        
        # 强制刷新视图
        if context and context.area:
            context.area.tag_redraw()

class LIGHTING_GADGETS_OT_SELECT_MULTIPLE_LIGHTS_BY_REFLECTION(Operator):
    bl_idname = "lighting_gadgets.select_multiple_lights_by_reflection"
    bl_label = "Select Multiple Lights by Reflection"
    bl_description = "Select multiple lights that would reflect from the surface point to the view (Shift + Alt + Right Mouse)"
    bl_options = {'REGISTER'}
    
    # 添加类变量，用于存储绘制回调和状态
    _draw_handle = None
    _timer = None
    _hit_location = None
    _selected_lights = []
    _line_opacity = 1.0
    _draw_duration = 1.0  # 绘制持续时间（秒），缩短一半
    _start_time = 0
    
    @classmethod
    def poll(cls, context):
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        return (
            area and area.type == 'VIEW_3D' and region and rv3d and
            context.mode == 'OBJECT'
        )
        
    def modal(self, context, event):
        """处理绘制回调的模态操作"""
        # 强制重绘区域，确保可以看到线条
        if context.area:
            context.area.tag_redraw()
            
        # 检查计时器
        if event.type == 'TIMER':
            # 计算已经过去的时间
            elapsed = time.time() - self._start_time
            if elapsed > self._draw_duration:
                # 如果超过绘制持续时间，清理并退出
                self.cleanup(context)
                return {'FINISHED'}
            else:
                # 更新线条的不透明度，实现淡出效果
                self._line_opacity = 1.0 - (elapsed / self._draw_duration)
                
        return {'PASS_THROUGH'}
            
    def cleanup(self, context):
        """清理绘制回调和计时器"""
        # 移除绘制回调
        if self._draw_handle is not None:
            try:
                bpy.types.SpaceView3D.draw_handler_remove(self._draw_handle, 'WINDOW')
            except:
                pass
            self._draw_handle = None
            
        # 移除计时器
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
            
        # 重设属性
        self._hit_location = None
        self._selected_lights = []
        self._line_opacity = 1.0
        # 重置最新选中的灯光
        if hasattr(self, '_latest_selected_light'):
            self._latest_selected_light = None
        
    def draw_reflection_lines(self, context):
        """绘制从命中点到多个灯光的指示线，使用新的深度测试实现"""
        try:
            # 只在激活视口绘制，减少性能开销
            if not hasattr(self, "_active_area") or context.area != self._active_area:
                return
                
            if not hasattr(self, "_hit_location") or not hasattr(self, "_selected_lights") or self._hit_location is None or not self._selected_lights:
                return
                
            # 3D击中点
            hit_3d = self._hit_location
            
            # 只绘制最新选中的灯光，而不是所有选中的灯光
            lights_to_draw = []
            if hasattr(self, '_latest_selected_light') and self._latest_selected_light:
                lights_to_draw = [self._latest_selected_light]
            else:
                # 如果没有最新选中的灯光，绘制所有选中的灯光（兼容旧逻辑）
                lights_to_draw = self._selected_lights
            
            # 为每个灯光绘制一条线
            for light in lights_to_draw:
                # 检查灯光对象是否仍然有效（未被删除）
                try:
                    # 尝试访问对象的名称来检查对象是否仍然有效
                    _ = light.name
                    # 检查对象是否仍在场景中
                    if light.name not in context.scene.objects:
                        continue
                except ReferenceError:
                    # 对象已被删除，跳过
                    continue
                    
                # 3D灯光位置
                light_3d = light.location
                
                # 使用新的深度测试实现绘制反射线
                # 获取灯光颜色
                light_data = light.data
                light_color = light_data.color
                
                # 检查是否处于临时闪烁状态，如果是则使用原始颜色
                # 注意：_state_manager 是模块级全局变量
                if light_data.name in _state_manager._temp_color_lights:
                    light_color = _state_manager._temp_color_lights[light_data.name]['original_color']
                
                color = (light_color[0], light_color[1], light_color[2], self._line_opacity)
                draw_reflection_line_depth(context, hit_3d, light_3d, color, self._line_opacity, thickness=3.0)
                
        except Exception as e:
            pass
        
    def invoke(self, context, event):
        # 记录激活视口，用于限制绘制范围
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        if not (area and area.type == 'VIEW_3D' and region and rv3d):
            return {'PASS_THROUGH'}
        self._active_area = context.area
        
        # 获取鼠标位置
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        
        # 获取视图信息
        region = context.region
        rv3d = context.region_data
        
        # 从鼠标位置创建射线（兼容正交视图）
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos)
        if hasattr(rv3d, 'is_perspective') and not rv3d.is_perspective:
            # 正交模式下的正确射线计算
            plane_point = view3d_utils.region_2d_to_location_3d(region, rv3d, mouse_pos, rv3d.view_location)
            clip_start = getattr(context.space_data, 'clip_start', 0.1)
            # 在正交模式下，射线原点应该在视口平面前方，确保能正确检测到模型表面
            ray_origin = plane_point - view_vector * max(clip_start * 10, 1.0)
        
        # 执行射线检测，跳过不可见物体
        result = find_visible_hit(context, ray_origin, view_vector)
        
        if result[0]:  # 如果射线击中了物体
            hit_location = result[1]
            hit_normal = result[2]
            hit_object = result[4]  # 获取被击中的物体
            is_instance_hit = result[5] if len(result) > 5 else False
            
            # 存储命中点位置用于绘制
            self._hit_location = hit_location
            
            # 计算反射方向
            # 使用公式: R = V - 2(V·N)N，其中V是视图方向，N是表面法线
            dot_product = view_vector.dot(hit_normal)
            reflection_dir = view_vector - (2 * dot_product * hit_normal)
            reflection_dir.normalize()
            
            # 查找所有可见的灯光
            all_lights = [obj for obj in context.scene.objects if obj.type == 'LIGHT']
            lights = [light for light in all_lights if is_light_visible_and_in_view_layer(light, context.view_layer)]
            
            # 过滤出与被击中物体有灯光链接关系的灯光
            linked_lights = [light for light in lights if check_light_linking(light, hit_object, is_instance_hit)]
            
            # 如果没有与物体链接的灯光，使用所有可见灯光作为备选
            candidate_lights = linked_lights if linked_lights else lights
            
            # 如果没有候选灯光，返回
            if not candidate_lights:
                if lights:
                    template = bpy.app.translations.pgettext("Found visible lights, but none has a light linking relationship with the clicked object '{name}'")
                    self.report({'WARNING'}, template.format(name=hit_object.name))
                elif all_lights:
                    template = bpy.app.translations.pgettext("There are lights in the scene, but none are in the current view layer or they are hidden")
                    self.report({'WARNING'}, template)
                else:
                    template = bpy.app.translations.pgettext("No lights found. Please add a light to the scene first.")
                    self.report({'WARNING'}, template)
                return {'CANCELLED'}
            
            # 计算所有灯光与反射方向的相似度
            light_scores = []
            for light in candidate_lights:
                # 计算从命中点到灯光的方向
                to_light = (light.matrix_world.translation - hit_location).normalized()
                
                # 计算与反射方向的点积（余弦相似度）
                similarity = reflection_dir.dot(to_light)
                
                # 只考虑与反射方向夹角小于约31度（余弦值大于0.85）的灯光
                if similarity > ANGLE_SIMILARITY_LOW:
                    light_scores.append((light, similarity))
            
            # 按相似度排序
            light_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 选择最相似的一个灯光
            if not light_scores:
                template = bpy.app.translations.pgettext("No suitable light found")
                self.report({'WARNING'}, template)
                return {'CANCELLED'}
                
            best_light = light_scores[0][0]
            
            # 确保选中的灯光在当前视图层中
            if best_light.name not in context.view_layer.objects:
                template = bpy.app.translations.pgettext("Light '{name}' is not in the current view layer and cannot be selected")
                self.report({'WARNING'}, template.format(name=best_light.name))
                return {'CANCELLED'}
            
            try:
                # 如果灯光已经被选中，则取消选择
                if best_light.select_get():
                    best_light.select_set(False)
                    # 如果这是活动对象，取消活动状态
                    if context.view_layer.objects.active == best_light:
                        # 找到另一个选中的灯光作为活动对象
                        selected_lights = [obj for obj in context.selected_objects if obj.type == 'LIGHT' and obj != best_light]
                        if selected_lights:
                            context.view_layer.objects.active = selected_lights[0]
                        else:
                            context.view_layer.objects.active = None
                    
                    # 从绘制列表中移除
                    if hasattr(self, '_selected_lights') and best_light in self._selected_lights:
                        self._selected_lights.remove(best_light)
                    
                    template = bpy.app.translations.pgettext("Deselected light: {name}")
                    self.report({'INFO'}, template.format(name=best_light.name))
                else:
                    # 选择新灯光
                    best_light.select_set(True)
                    context.view_layer.objects.active = best_light
                    
                    # 添加到绘制列表，但只保留最新选中的灯光用于绘制
                    if not hasattr(self, '_selected_lights'):
                        self._selected_lights = []
                    if best_light not in self._selected_lights:
                        self._selected_lights.append(best_light)
                    
                    # 只保留最新选中的灯光用于绘制命中线
                    self._latest_selected_light = best_light
                    
                    template = bpy.app.translations.pgettext("Selected light: {name}")
                    self.report({'INFO'}, template.format(name=best_light.name))
                    
                    # 颜色闪烁反馈
                    try:
                        # 获取插件首选项 - 使用更健壮的方式
                        addon_prefs = None
                        package_name = __package__
                        
                        # 1. 尝试直接使用 __package__
                        if package_name and package_name in context.preferences.addons:
                            addon_prefs = context.preferences.addons[package_name].preferences
                        # 2. 尝试使用顶层包名
                        elif __name__ and __name__.partition('.')[0] in context.preferences.addons:
                            addon_prefs = context.preferences.addons[__name__.partition('.')[0]].preferences
                        
                        if addon_prefs and hasattr(addon_prefs, "enable_selection_color_flash") and addon_prefs.enable_selection_color_flash:
                            flash_color = addon_prefs.selection_flash_color
                            flash_duration = 0.2  # 闪烁持续时间
                            _state_manager.set_temp_color(best_light.data, flash_color, flash_duration)
                    except Exception as e:
                        print(f"Error in selection color flash: {e}")
                
                # 设置开始时间
                self._start_time = time.time()
                
                # 如果已有绘制回调，先移除
                if self._draw_handle is not None:
                    # 检查当前上下文是否在3D视图中，避免在其他空间类型中移除区域类型
                    if hasattr(context, 'area') and context.area and context.area.type == 'VIEW_3D':
                        bpy.types.SpaceView3D.draw_handler_remove(self._draw_handle, 'WINDOW')
                    self._draw_handle = None
                
                # 如果已有计时器，先移除
                if self._timer is not None:
                    context.window_manager.event_timer_remove(self._timer)
                    self._timer = None
                
                # 只有在有选中的灯光时才添加绘制回调和计时器
                if self._selected_lights:
                    # 添加绘制回调
                    self._draw_handle = bpy.types.SpaceView3D.draw_handler_add(
                        LIGHTING_GADGETS_OT_SELECT_MULTIPLE_LIGHTS_BY_REFLECTION.draw_reflection_lines, (self, context), 'WINDOW', 'POST_PIXEL')
                    
                    # 添加计时器
                    self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
                    context.window_manager.modal_handler_add(self)
                
                # 返回RUNNING_MODAL，让我们的回调继续运行
                return {'RUNNING_MODAL'}
            except RuntimeError as e:
                template = bpy.app.translations.pgettext("Could not select lights: {error}")
                self.report({'ERROR'}, template.format(error=str(e)))
                return {'CANCELLED'}
        else:
            template = bpy.app.translations.pgettext("No surface hit. Make sure the mouse is pointing at an object in the scene.")
            self.report({'WARNING'}, template)
            return {'CANCELLED'}
