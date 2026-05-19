import math
import time
from math import radians, sqrt, sin, cos, pi, atan2, acos

import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

_GN_SCENE_HEAVY_CACHE = {
    "scene_ptr": 0,
    "last_check": 0.0,
    "heavy": False,
}

def _has_geometry_nodes_modifier(obj) -> bool:
    if not obj:
        return False
    try:
        for mod in getattr(obj, "modifiers", ()):
            if mod and getattr(mod, "type", None) == 'NODES' and getattr(mod, "show_viewport", True):
                return True
    except Exception:
        return False
    return False

def is_heavy_geometry_nodes_scene(context) -> bool:
    scene = getattr(context, "scene", None)
    if not scene:
        return False

    now = time.monotonic()
    scene_ptr = 0
    try:
        scene_ptr = scene.as_pointer()
    except Exception:
        scene_ptr = id(scene)

    if _GN_SCENE_HEAVY_CACHE["scene_ptr"] == scene_ptr and (now - _GN_SCENE_HEAVY_CACHE["last_check"]) < 1.0:
        return _GN_SCENE_HEAVY_CACHE["heavy"]

    has_gn = False
    for obj in scene.objects:
        if _has_geometry_nodes_modifier(obj):
            has_gn = True
            break

    heavy = False
    if has_gn:
        try:
            depsgraph = context.evaluated_depsgraph_get()
            instance_count = 0
            for _ in depsgraph.object_instances:
                instance_count += 1
                if instance_count > 3000:
                    heavy = True
                    break
        except Exception:
            heavy = True

    _GN_SCENE_HEAVY_CACHE["scene_ptr"] = scene_ptr
    _GN_SCENE_HEAVY_CACHE["last_check"] = now
    _GN_SCENE_HEAVY_CACHE["heavy"] = heavy
    return heavy

def get_view_info(region_data):
    """Get view information"""
    view_matrix = region_data.view_matrix
    view_dir = view_matrix.to_3x3().inverted() @ Vector((0.0, 0.0, -1.0))
    return view_dir

def calculate_light_orientation(direction):
    """Calculate light orientation
    
    Args:
        direction: Direction vector
        
    Returns:
        Euler rotation
    """
    # 使用四元数计算旋转，使灯光朝向目标点
    rotation = direction.to_track_quat('-Z', 'Y')
    return rotation.to_euler()


def get_light_world_location(light_obj):
    """获取灯光的世界坐标位置（兼容有父物体的情况）"""
    return light_obj.matrix_world.translation.copy()


def set_light_world_location(light_obj, world_location):
    """将世界坐标位置设置到灯光上（自动处理父物体坐标转换）"""
    if light_obj.parent:
        # 有父物体：将世界坐标转换为局部坐标
        parent_inv = light_obj.parent.matrix_world.inverted()
        local_location = parent_inv @ world_location
        light_obj.location = local_location
    else:
        # 无父物体：世界坐标就是局部坐标
        light_obj.location = world_location


def set_light_world_orientation(light_obj, world_direction):
    """根据世界方向设置灯光朝向（自动处理父物体旋转转换）
    
    world_direction: 灯光在世界坐标系中应该朝向的方向向量
    """
    # 计算世界空间下的目标旋转四元数
    world_rot = world_direction.to_track_quat('-Z', 'Y')
    
    if light_obj.parent:
        # 有父物体：将世界旋转转换为局部旋转
        parent_rot = light_obj.parent.matrix_world.to_quaternion()
        local_rot = parent_rot.inverted() @ world_rot
        # 传入当前旋转作为参考，避免欧拉角跳变
        light_obj.rotation_euler = local_rot.to_euler(light_obj.rotation_euler.order, light_obj.rotation_euler)
    else:
        light_obj.rotation_euler = world_rot.to_euler(light_obj.rotation_euler.order, light_obj.rotation_euler)


def calculate_hit_distance(light_obj, hit_location):
    """计算灯光到击中点的距离
    
    参数:
        light_obj: 灯光对象
        hit_location: 击中点位置
        
    返回:
        距离
    """
    return (hit_location - get_light_world_location(light_obj)).length

def evaluate_object_ray_cast(context, origin, direction, hit_obj, world_matrix=None):
    """对实例物体进行精确的光线投射，应用所有修改器"""
    if not hit_obj:
        return None

    if hit_obj.type != 'MESH':
        return None
    if world_matrix is None:
        world_matrix = hit_obj.matrix_world
        
    try:
        # Get depsgraph for evaluating modifiers
        depsgraph = context.evaluated_depsgraph_get()
        
        # 获取评估后的物体（应用了所有修改器）
        evaluated_obj = hit_obj.evaluated_get(depsgraph)
        
        # 使用评估后的物体进行精确的光线投射
        if evaluated_obj and evaluated_obj.type == 'MESH':
            # 将射线原点和方向转换到物体的局部坐标系
            local_origin = world_matrix.inverted() @ origin
            local_direction = world_matrix.inverted().to_3x3() @ direction
            local_direction.normalize()
            
            # 对评估后的物体进行光线投射（在局部坐标系中）
            eval_result = evaluated_obj.ray_cast(
                origin=local_origin,
                direction=local_direction
            )
            
            if eval_result[0]:
                # 将命中结果转换回世界坐标系
                world_location = world_matrix @ eval_result[1]
                
                # 计算世界坐标系中的法线（考虑模型的旋转和缩放）
                world_normal = world_matrix.to_3x3().inverted().transposed() @ eval_result[2]
                world_normal.normalize()
                
                # 返回评估后的命中结果（在世界坐标系中）
                return (True, world_location, world_normal, eval_result[3], hit_obj)
    except Exception as e:
        # 如果评估失败，返回None
        pass
        
    return None

def is_point_occluded(context, screen_xy, world_point, region=None, rv3d=None):
    """检查屏幕坐标对应的3D点是否被遮挡
    
    Args:
        context: 当前上下文
        screen_xy: 屏幕坐标 (x, y)
        world_point: 世界坐标系中的目标点
        region: 可选的region对象，如果未提供则从context获取
        rv3d: 可选的rv3d对象，如果未提供则从context获取
        
    Returns:
        bool: True如果点被遮挡，False如果可见
    """
    try:
        if not region:
            region = context.region
        if not rv3d:
            rv3d = context.region_data
            
        if not region or not rv3d:
            return False
            
        # 计算从屏幕点到3D的射线
        direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, screen_xy)
        origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, screen_xy)
        
        # 处理正交投影情况
        if hasattr(rv3d, 'is_perspective') and not rv3d.is_perspective:
            sample_plane = view3d_utils.region_2d_to_location_3d(region, rv3d, screen_xy, rv3d.view_location)
            clip_end = getattr(context.space_data, 'clip_end', 1000.0)
            origin = sample_plane - direction * clip_end
        
        # 获取depsgraph用于评估实例物体
        depsgraph = context.evaluated_depsgraph_get()
        
        # 使用评估后的场景进行光线投射，正确处理实例物体和修改器
        result = context.scene.ray_cast(
            depsgraph=depsgraph,
            origin=origin,
            direction=direction
        )
        
        if not result[0]:
            return False
            
        hit_loc = result[1]
        dir_norm = direction.normalized()
        dist_to_point = (world_point - origin).dot(dir_norm)
        dist_to_hit = (hit_loc - origin).dot(dir_norm)
        
        # 如果击中点比目标点更近，则目标被遮挡
        return dist_to_point > dist_to_hit + 1e-5
        
    except Exception as e:
        # 出现异常时假设不遮挡，避免影响绘制
        pass
        return False


def find_closest_surface_point(context, light_obj):
    """Find closest surface point in light's forward direction
    
    Args:
        context: Current context
        light_obj: Light object
        
    Returns:
        tuple: (hit_location, hit_normal, distance) or (None, None, None)
    """
    # Get light direction (-Z axis)
    direction = light_obj.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))
    direction.normalize()
    
    # 从灯光位置投射射线
    # 获取depsgraph用于评估实例物体
    depsgraph = context.evaluated_depsgraph_get()
    
    # 使用评估后的场景进行光线投射，正确处理实例物体和修改器
    result = context.scene.ray_cast(
        depsgraph=depsgraph,
        origin=light_obj.location,
        direction=direction
    )
    
    if result[0]:  # 如果射线击中物体
        hit_obj = result[4]
        
        # 如果是网格物体，使用评估后的网格进行精确计算
        if hit_obj and hit_obj.type == 'MESH' and not _has_geometry_nodes_modifier(hit_obj):
            hit_matrix = None
            try:
                hit_matrix = result[5]
            except Exception:
                hit_matrix = None
            eval_result = evaluate_object_ray_cast(
                context, 
                light_obj.location, 
                direction, 
                hit_obj,
                world_matrix=hit_matrix
            )
            
            if eval_result:
                return eval_result[1], eval_result[2], calculate_hit_distance(light_obj, eval_result[1])
        
        # 回退到原始结果
        return result[1], result[2], calculate_hit_distance(light_obj, result[1])
    
    return None, None, None

def update_light_transform(activeRegion3D, lightObject, hitLocation, hitNormal, initial_distance=None, ray_origin=None, ray_direction=None, context=None, mouse_world_pos=None):
    """Update light transformation based on hit point and view direction"""
    is_orthographic = False
    if context and hasattr(context.region_data, 'is_perspective'):
        is_orthographic = not context.region_data.is_perspective
    
    # 获取灯光的世界坐标位置（兼容有父物体的情况）
    light_world_pos = get_light_world_location(lightObject)
    
    if is_orthographic:
        if ray_direction is not None:
            view_dir = ray_direction.normalized()
            if view_dir.dot(hitNormal) > 0:
                surface_normal = hitNormal
            else:
                surface_normal = -hitNormal
            dot_product = view_dir.dot(surface_normal)
            reflection_dir = view_dir - (2 * dot_product * surface_normal)
            reflection_dir.normalize()
            target_point = mouse_world_pos if mouse_world_pos is not None else hitLocation
            if target_point is None and context and ray_origin is not None:
                plane_normal = view_dir
                plane_point = hitLocation
                denom = plane_normal.dot(ray_direction)
                if abs(denom) > 1e-6:
                    t = (plane_point - ray_origin).dot(plane_normal) / denom
                    if t > 0:
                        target_point = ray_origin + ray_direction * t
            if target_point is None:
                target_point = hitLocation
            if initial_distance is None:
                current_distance = (target_point - light_world_pos).length
                initial_distance = max(current_distance, 1.0)
            new_world_location = target_point + reflection_dir * initial_distance
            set_light_world_location(lightObject, new_world_location)
            to_target = (target_point - new_world_location).normalized()
            set_light_world_orientation(lightObject, to_target)
            return
    
    # 透视相机模式下的原有逻辑
    # 使用精确的射线方向（如果提供）或回退到通用视图方向
    if ray_origin is not None and ray_direction is not None:
        # 使用精确的射线方向而非一般视图方向
        view_dir = ray_direction.normalized()
        # 使用精确的相机位置到点击点的方向
        exact_view_dir = (hitLocation - ray_origin).normalized()
        
        # 透视强度因子（基于射线方向与精确视图方向的差异）
        perspective_factor = 1.0 - exact_view_dir.dot(view_dir)
        
        # 在强透视下（小焦距）进行法线调整以获得更准确的反射
        if perspective_factor > 0.01:  # 有明显的透视效果
            # 计算调整后的法线，略微偏向精确视图方向
            adjusted_normal = hitNormal.lerp(exact_view_dir, perspective_factor * 0.2).normalized()
            
            # 使用调整后的法线计算反射
            dot_product = view_dir.dot(adjusted_normal)
            reflection_dir = view_dir - (2 * dot_product * adjusted_normal)
        else:
            # 透视效果不明显时使用标准反射
            dot_product = view_dir.dot(hitNormal)
            reflection_dir = view_dir - (2 * dot_product * hitNormal)
    else:
        # 回退到原来的计算方法
        view_dir = get_view_info(activeRegion3D)
        dot_product = view_dir.dot(hitNormal)
        reflection_dir = view_dir - (2 * dot_product * hitNormal)
    
    reflection_dir.normalize()
    
    # If no distance specified, use current distance from light to hit point
    if initial_distance is None:
        initial_distance = calculate_hit_distance(lightObject, hitLocation)
    
    # 计算新的世界坐标位置
    new_world_location = hitLocation + reflection_dir * initial_distance
    set_light_world_location(lightObject, new_world_location)
    
    # Calculate direction vector from light position to hit point
    to_target = (hitLocation - new_world_location).normalized()
    
    # Set light rotation to face hit point
    set_light_world_orientation(lightObject, to_target)

def lerp(a, b, t):
    """Linear interpolation between a and b with factor t"""
    return a + (b - a) * t

def lerp_angle(a, b, t):
    """Angle interpolation with angle wrapping handling"""
    # 确保角度差在 -pi 和 pi 之间
    diff = (b - a + pi) % (2 * pi) - pi
    return a + diff * t

def cartesian_to_spherical(v):
    """Convert Cartesian coordinates to spherical coordinates"""
    x, y, z = v
    r = sqrt(x*x + y*y + z*z)
    if r == 0:
        return 0, 0, 0
    theta = atan2(y, x)  # azimuthal angle
    phi = acos(z/r)      # polar angle
    return r, theta, phi

def spherical_to_cartesian(r, theta, phi):
    """Convert spherical coordinates to Cartesian coordinates"""
    x = r * sin(phi) * cos(theta)
    y = r * sin(phi) * sin(theta)
    z = r * cos(phi)
    return Vector((x, y, z))

def update_light_precise_transform(context, light_obj, hit_location, hit_normal, current_mouse, last_mouse, is_slow=False):
    """Update light position in precise control mode using spherical coordinates
    
    Args:
        context: Current context
        light_obj: Light object
        hit_location: Hit point location (rotation center)
        hit_normal: Hit point normal
        current_mouse: Current mouse position (x, y)
        last_mouse: Last mouse position (x, y)
        is_slow: Whether to use slow mode
    """
    # Get region dimensions
    region = context.region
    width = region.width
    height = region.height

    disable_interpolation = is_heavy_geometry_nodes_scene(context)
    
    # 计算鼠标移动增量（考虑边界环绕）
    def calculate_delta(current, last, size):
        delta = current - last
        if abs(delta) > size / 2:
            if delta > 0:
                delta = delta - size
            else:
                delta = size + delta
        return delta
    
    # 计算X和Y移动
    delta_x = calculate_delta(current_mouse[0], last_mouse[0], width)
    delta_y = calculate_delta(current_mouse[1], last_mouse[1], height)
    
    # Adjust rotation speed (consistent with reflection mode)
    # 精确模式：正常速度提高一倍，慢速模式保持不变
    speed_factor = 0.3 if is_slow else 2.0  # 正常模式速度翻倍，慢速模式保持0.3
    delta_x *= speed_factor / width
    delta_y *= speed_factor / height
    
    # 获取灯光的世界坐标位置（兼容有父物体的情况）
    light_world_pos = get_light_world_location(light_obj)
    
    # Get current light vector relative to hit point
    to_light = light_world_pos - hit_location
    
    # 转换为球坐标
    r, theta, phi = cartesian_to_spherical(to_light)
    
    # Update angles using faster interpolation for smoother response
    # 水平旋转（方位角）
    target_theta = theta + delta_x * 2 * pi  # Map movement to full circle
    if disable_interpolation:
        theta = target_theta
    else:
        theta = lerp_angle(theta, target_theta, 0.5)  # Increased interpolation factor for faster response
    
    # 垂直旋转（极角）
    target_phi = phi - delta_y * pi  # 将移动映射到半圆
    if disable_interpolation:
        phi = target_phi
    else:
        phi = lerp(phi, target_phi, 0.5)  # 增加插值因子以获得更快的响应
    
    # Limit angle ranges
    # Azimuthal angle wraps (0-2π)
    theta = theta % (2 * pi)
    # 极角限制（0-π），避免极点奇点
    phi = max(0.001, min(pi - 0.001, phi))  # 避免极点奇点
    
    # Convert back to Cartesian coordinates
    new_pos = spherical_to_cartesian(r, theta, phi)

    # Smoothly interpolate position with faster response
    target_location = hit_location + new_pos
    if disable_interpolation:
        set_light_world_location(light_obj, target_location)
    else:
        new_world_pos = light_world_pos.lerp(target_location, 0.5)  # Increased interpolation for faster movement
        set_light_world_location(light_obj, new_world_pos)
    
    # 确保灯光始终朝向击中点（使用设置后的实际世界坐标）
    actual_world_pos = get_light_world_location(light_obj)
    direction = hit_location - actual_world_pos
    world_rot = direction.to_track_quat('-Z', 'Y')
    
    if light_obj.parent:
        parent_rot = light_obj.parent.matrix_world.to_quaternion()
        target_local_rot = parent_rot.inverted() @ world_rot
    else:
        target_local_rot = world_rot
    
    if disable_interpolation:
        # 传入当前旋转作为参考，避免欧拉角跳变
        light_obj.rotation_euler = target_local_rot.to_euler(light_obj.rotation_euler.order, light_obj.rotation_euler)
    else:
        current_quat = light_obj.rotation_euler.to_quaternion()
        new_quat = current_quat.slerp(target_local_rot, 0.5)
        light_obj.rotation_euler = new_quat.to_euler(light_obj.rotation_euler.order, light_obj.rotation_euler)


def are_objects_equal(obj1, obj2):
    """比较两个物体是否相同（兼容 Evaluated Object）"""
    if obj1 == obj2:
        return True
    if not obj1 or not obj2:
        return False
    # 比较名称
    if obj1.name == obj2.name:
        return True
    # 比较原始数据块（如果可用）
    if getattr(obj1, "original", None) == getattr(obj2, "original", None) and getattr(obj1, "original", None) is not None:
        return True
    return False

def check_light_linking(light_obj, target_obj, is_instance_hit=False):
    """
    检查灯光链接关系
    返回 True 如果灯光应该照亮该物体
    返回 False 如果灯光排除该物体
    """
    try:
        # 由于追加的实例（如集合实例）命中返回的是内部网格，且它可能不在直接的 light_linking 规则中，
        # 为了让反选灯光功能对此类实例依然有效，我们对实例命中暂时放行
        if is_instance_hit:
            return True
            
        # 1. 检查是否有 light_linking 属性 (Blender 4.0+)
        if not hasattr(light_obj, "light_linking"):
            return True
            
        linking = light_obj.light_linking
        if not linking:
            return True
            
        # 2. 获取接收者集合
        # 注意：在 Blender 4.0+ 中，排除/包含的状态是存储在集合成员上的，而不是灯光本身
        # 灯光只持有一个接收者集合 (receiver_collection)
        root_coll = linking.receiver_collection
        if not root_coll:
            # 如果没有设置接收者集合，说明没有启用灯光链接（或者是默认照亮所有）
            return True

        # 辅助函数：检查物体是否在集合中（递归）
        def is_object_in_collection_recursive(obj, col, visited=None):
            if visited is None:
                visited = set()
            if col in visited:
                return False
            visited.add(col)
            
            # 检查物体是否直接在集合中
            if obj.name in col.objects:
                return True
                
            # 如果名称查找失败，尝试更深度的相等性检查（针对评估对象）
            # 虽然通常 obj.name in col.objects 足够，但为了保险起见
            for o in col.objects:
                if are_objects_equal(o, obj):
                    return True
                
            for child in col.children:
                if is_object_in_collection_recursive(obj, child, visited):
                    return True
            return False

        # 3. 遍历集合成员，获取包含/排除规则
        # Blender 的逻辑：
        # - 如果只有 EXCLUDE 规则：默认全亮，除了被排除的
        # - 如果有 INCLUDE 规则：默认全暗，只有被包含的（且未被排除的）亮
        
        has_include_rules = False
        is_target_included = False
        is_target_excluded = False
        
        # 3.1 检查直接关联的物体 (CollectionObject)
        if hasattr(root_coll, "collection_objects"):
            # Blender 5.0+: collection_objects 可能是没有 .object 属性的
            # 但它通常与 root_coll.objects 索引对应
            
            # 安全检查：确保长度匹配
            num_objs = len(root_coll.objects)
            num_col_objs = len(root_coll.collection_objects)
            
            # 我们尽量使用索引对应，如果不匹配则无法安全判断
            # 但通常它们是同步的
            loop_count = min(num_objs, num_col_objs)
            
            for i in range(loop_count):
                obj = root_coll.objects[i]
                col_obj = root_coll.collection_objects[i]
                
                # 获取规则状态
                state = 'INCLUDE' # 默认
                if hasattr(col_obj, "light_linking") and hasattr(col_obj.light_linking, "link_state"):
                    state = col_obj.light_linking.link_state
                
                if state == 'INCLUDE':
                    has_include_rules = True
                    # 使用增强的相等性检查
                    if are_objects_equal(obj, target_obj):
                        is_target_included = True
                elif state == 'EXCLUDE':
                    if are_objects_equal(obj, target_obj):
                        is_target_excluded = True
                        
        # 3.2 检查关联的子集合 (CollectionChild)
        if hasattr(root_coll, "collection_children"):
            num_children = len(root_coll.children)
            num_col_children = len(root_coll.collection_children)
            loop_count = min(num_children, num_col_children)
            
            for i in range(loop_count):
                child_coll = root_coll.children[i]
                col_child = root_coll.collection_children[i]
                
                # 获取规则状态
                state = 'INCLUDE'
                if hasattr(col_child, "light_linking") and hasattr(col_child.light_linking, "link_state"):
                    state = col_child.light_linking.link_state
                
                # 如果规则相关，检查物体是否在该子集合中
                if state == 'INCLUDE':
                    has_include_rules = True
                    if not is_target_included:
                        if is_object_in_collection_recursive(target_obj, child_coll):
                            is_target_included = True
                            
                elif state == 'EXCLUDE':
                    if not is_target_excluded:
                        if is_object_in_collection_recursive(target_obj, child_coll):
                            is_target_excluded = True
        
        # 3.3 如果 collection_objects 为空（或者是标准集合），我们需要检查 collection.objects
        # 标准集合中的对象被视为 INCLUDE（如果没有被上面的规则覆盖）
        # 注意：如果 root_coll 本身就是一个混合了 collection_objects 的集合，
        # 我们需要小心不要重复计算。但通常 object 都在 objects 中。
        # 如果我们已经判定了 is_target_included，就不需要再查了。
        # 如果 has_include_rules 已经是 True，我们也不一定需要查，除非该物体是在 collection.objects 中但不在 collection_objects 中？
        # 实际上，只要 root_coll 被用作 receiver_collection，其中的所有对象都应该被视为 target。
        # 除非它们被显式 EXCLUDE。
        
        # 如果还没有发现包含规则，或者目标还没被包含，我们需要检查标准对象列表
        # 这对于没有使用高级 Light Linking UI 而是直接拖拽集合的情况很重要
        if not is_target_included:
            # 检查目标物体是否在根集合的标准对象列表中
            if is_object_in_collection_recursive(target_obj, root_coll):
                 # 只要在集合中，就视为潜在的 INCLUDE
                 # 但是，我们需要确定这是否算作 "Include Rule"？
                 # 是的，如果集合被分配了，它就是包含集合。
                 has_include_rules = True
                 is_target_included = True

        # 4. 根据规则判定
        if has_include_rules:
            # 混合模式或仅包含模式：必须被包含且未被排除
            return is_target_included and not is_target_excluded
        else:
            # 仅排除模式（或无规则）：只要未被排除即可
            return not is_target_excluded

    except Exception as e:
        print(f"Error in check_light_linking: {e}")
        import traceback
        traceback.print_exc()
        # 发生错误时，为了安全起见，默认返回 True (Fail-Open)
        return True


def find_visible_hit(context, origin, direction, max_depth=10, ignore_gn_instances=False):
    """
    递归地在可见模型上查找命中点，正确处理实例和修改器。
    首先使用 scene.ray_cast 快速找到命中的实例，然后对网格物体
    使用 object.ray_cast 在评估后的网格上进行精确投射，以获得
    应用了修改器（如细分）的准确位置和法线。
    
    Args:
        context: Blender上下文
        origin: 射线起点
        direction: 射线方向
        max_depth: 最大递归深度
        
    Returns:
        tuple: (命中结果, 位置, 法线, 面索引, 物体, 是否为实例命中)
    """
    if max_depth <= 0:
        return (False, None, None, None, None, False)

    depsgraph = context.evaluated_depsgraph_get()
    
    # 第一遍：使用 scene.ray_cast 快速找到命中的对象（正确处理实例）
    try:
        result, location, normal, index, hit_obj, matrix = context.scene.ray_cast(
            depsgraph=depsgraph,
            origin=origin,
            direction=direction
        )
    except Exception:
        return (False, None, None, None, None, False)

    if not result:
        return (False, None, None, None, None, False)
        
    # 检查是否是实例命中
    is_instance_hit = False
    try:
        if matrix is not None and hit_obj is not None:
            is_instance_hit = (matrix != hit_obj.matrix_world)
    except Exception:
        pass

    # 检查物体可见性
    is_visible = True
    
    # 只有当非实例命中时，才严格检查原物体可见性
    # 因为集合实例/集合追加中，原始物体经常被隐藏，但实例本身是可见的
    if not is_instance_hit:
        # 1. 检查视口隐藏 (小眼睛) 和 全局视口隐藏 (显示器)
        if hit_obj.hide_get() or hit_obj.hide_viewport:
            is_visible = False
            
        # 2. 检查局部视图 (Local View)
        # 如果当前处于局部视图模式，只有在局部视图中的物体才被视为可见
        elif context.space_data and context.space_data.type == 'VIEW_3D' and context.space_data.local_view:
            if not hit_obj.local_view_get(context.space_data):
                is_visible = False

    # 如果命中不可见物体，或者显示类型为边界/线框，或者渲染不可见，则递归查找
    if not is_visible or hit_obj.display_type in {'BOUNDS', 'WIRE'} or hit_obj.hide_render or not hit_obj.visible_camera:
        if is_instance_hit and hit_obj.display_type not in {'BOUNDS', 'WIRE'}:
            pass # 实例视为可见
        else:
            next_origin = location + direction * 0.001
            return find_visible_hit(context, next_origin, direction, max_depth - 1, ignore_gn_instances=ignore_gn_instances)

    if ignore_gn_instances:
        if is_instance_hit:
            step = 0.01
            try:
                obj_size = float(max(hit_obj.dimensions)) if hasattr(hit_obj, "dimensions") else 0.0
                inst_scale = matrix.to_scale() if hasattr(matrix, "to_scale") else None
                scale_factor = float(max(inst_scale)) if inst_scale is not None else 1.0
                step = max(0.01, obj_size * scale_factor * 1.1)
            except Exception:
                step = 0.05

            try:
                direction_norm = direction.normalized()
            except Exception:
                direction_norm = direction

            next_origin = location + direction_norm * step
            alt_hit = find_visible_hit(context, next_origin, direction, max_depth - 1, ignore_gn_instances=ignore_gn_instances)
            if alt_hit and alt_hit[0]:
                return alt_hit
            return (True, location, normal, index, hit_obj, is_instance_hit)

    if _has_geometry_nodes_modifier(hit_obj) or ignore_gn_instances:
        return (True, location, normal, index, hit_obj, is_instance_hit)

    # 第二遍：如果命中网格，进行更精确的投射以处理修改器
    if hit_obj.type == 'MESH':
        try:
            eval_result = evaluate_object_ray_cast(
                context, origin, direction, hit_obj, world_matrix=matrix
            )
            if eval_result:
                return (eval_result[0], eval_result[1], eval_result[2], eval_result[3], eval_result[4], is_instance_hit)
        except Exception:
            pass

    # 对于非网格对象或第二遍投射失败，返回第一遍的结果
    return (True, location, normal, index, hit_obj, is_instance_hit)


def is_light_visible_and_in_view_layer(light_obj, view_layer):
    """检查灯光是否可见且在当前视图层中
    
    Args:
        light_obj: 灯光对象
        view_layer: 视图层
        
    Returns:
        bool: 是否可见
    """
    # 首先检查灯光是否在当前视图层中
    if light_obj.name not in view_layer.objects:
        return False
        
    # 检查对象本身是否隐藏
    if light_obj.hide_viewport or light_obj.hide_get():
        return False
        
    # 检查对象是否在隐藏的集合中
    for collection in light_obj.users_collection:
        # 检查集合在当前视图层中是否可见
        if collection.name in view_layer.layer_collection.children:
            layer_coll = view_layer.layer_collection.children[collection.name]
            if layer_coll.hide_viewport:
                return False
                
    # 递归检查父集合
    def _check_parent_collections(collection, view_layer_collection):
        # 获取父集合
        parent_collections = [c for c in bpy.data.collections if collection.name in c.children]
        for parent in parent_collections:
            # 找到对应的视图层集合
            for layer_coll in view_layer_collection.children:
                if layer_coll.name == parent.name:
                    # 如果父集合隐藏，灯光不可见
                    if layer_coll.hide_viewport:
                        return False
                    # 递归检查更高级别的父集合
                    if not _check_parent_collections(parent, view_layer_collection):
                        return False
        return True
        
    # 检查包含该灯光的所有父集合
    for collection in light_obj.users_collection:
        if not _check_parent_collections(collection, view_layer.layer_collection):
            return False
            
    return True


def calculate_average_normal(normals):
    """计算多个法线的加权平均值
    
    Args:
        normals: 法线列表
        
    Returns:
        Vector: 平均法线
    """
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
