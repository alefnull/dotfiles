import bpy


def _qsl_strip_numeric_suffix(name):
    parts = name.rsplit('.', 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0]
    return name


_QSL_SOFTBOX_GROUP_NAMES = {"Softbox", "柔光灯", "ソフトボックス", "소프트박스"}
_QSL_SOFTBOX_INPUT_ROTATION = {"Rotation", "旋转", "回転", "회전"}


def mirror_softbox_group_node_parameters(node_tree):
    if not node_tree:
        return

    for node in node_tree.nodes:
        if node.type != 'GROUP' or not node.node_tree:
            continue

        group_base_name = _qsl_strip_numeric_suffix(node.node_tree.name)
        if group_base_name not in _QSL_SOFTBOX_GROUP_NAMES:
            continue

        for socket in node.inputs:
            if not hasattr(socket, "default_value"):
                continue

            if socket.name in _QSL_SOFTBOX_INPUT_ROTATION:
                value = float(socket.default_value)
                value = (value + 180.0) % 360.0
                if value > 180.0:
                    value -= 360.0
                socket.default_value = value



def create_ps_blur_node_group():
    """
    创建柔光灯节点组 (真实高斯衰减)
    公式: exp( - (x * 3)^2 ) 用于平滑拖尾
    """
    # --- 多语言支持 (中日韩) ---
    texts = {
        'group_name': "Softbox",
        'Vector': "Vector",
        'Feather': "Feather",
        'Global Scale': "Scale",
        'Center X': "Center X",
        'Center Y': "Center Y",
        'Cut Softness': "Cut Softness",
        'Rotation': "Rotation",
        'Radial Settings': "Radial Settings",
        'Half Cut Settings': "Half Cut Settings",
        'Factor': "Factor",
        'Corner Radius': "Corner Radius"
    }
    
    lang = bpy.app.translations.locale
    if lang == 'DEFAULT':
        lang = bpy.context.preferences.view.language

    if lang in {'zh_CN', 'zh_HANS'}:
        texts.update({
            'group_name': "柔光灯",
            'Vector': "矢量",
            'Feather': "羽化强度",
            'Global Scale': "缩放",
            'Center X': "中心 X",
            'Center Y': "中心 Y",
            'Cut Softness': "切边柔化",
            'Rotation': "旋转",
            'Radial Settings': "径向设置",
            'Half Cut Settings': "半圆切除设置",
            'Factor': "系数",
            'Corner Radius': "圆角度"
        })
    elif lang == 'ja_JP':
        texts.update({
            'group_name': "ソフトボックス",
            'Vector': "ベクトル",
            'Feather': "ぼかし強度",
            'Global Scale': "スケール",
            'Center X': "センター X",
            'Center Y': "センター Y",
            'Cut Softness': "カットの柔らかさ",
            'Rotation': "回転",
            'Radial Settings': "放射状設定",
            'Half Cut Settings': "ハーフカット設定",
            'Factor': "係数",
            'Corner Radius': "コーナー半径"
        })
    elif lang == 'ko_KR':
        texts.update({
            'group_name': "소프트박스",
            'Vector': "벡터",
            'Feather': "페더 강도",
            'Global Scale': "스케일",
            'Center X': "중심 X",
            'Center Y': "중심 Y",
            'Cut Softness': "컷 부드러움",
            'Rotation': "회전",
            'Radial Settings': "방사형 설정",
            'Half Cut Settings': "하프 컷 설정",
            'Factor': "팩터",
            'Corner Radius': "코너 반경"
        })
    
    group_name = texts['group_name']

    # 始终创建新的节点组
    ng = bpy.data.node_groups.new(name=group_name, type='ShaderNodeTree')
    
    # --- 创建接口 ---
    # 面板: 径向设置
    panel_radial = ng.interface.new_panel(texts['Radial Settings'])
    
    socket_feather = ng.interface.new_socket(texts['Feather'], in_out='INPUT', socket_type='NodeSocketFloat', parent=panel_radial)
    socket_feather.default_value = 1.0
    socket_feather.min_value = 0.0
    socket_feather.max_value = 1.0
    socket_feather.subtype = 'FACTOR'

    socket_gscale = ng.interface.new_socket(texts['Global Scale'], in_out='INPUT', socket_type='NodeSocketFloat', parent=panel_radial)
    socket_gscale.default_value = 0.5
    socket_gscale.min_value = 0.01
    socket_gscale.max_value = 1.0
    socket_gscale.subtype = 'FACTOR'
    
    # 圆角半径
    socket_corner = ng.interface.new_socket(texts['Corner Radius'], in_out='INPUT', socket_type='NodeSocketFloat', parent=panel_radial)
    socket_corner.default_value = 1.0
    socket_corner.min_value = 0.0
    socket_corner.max_value = 1.0
    socket_corner.subtype = 'FACTOR'
    

    # 中心 X/Y
    socket_center_x = ng.interface.new_socket(texts['Center X'], in_out='INPUT', socket_type='NodeSocketFloat', parent=panel_radial)
    socket_center_x.default_value = 0.0
    socket_center_x.min_value = -2.0
    socket_center_x.max_value = 2.0
    socket_center_x.subtype = 'NONE'

    socket_center_y = ng.interface.new_socket(texts['Center Y'], in_out='INPUT', socket_type='NodeSocketFloat', parent=panel_radial)
    socket_center_y.default_value = 0.0
    socket_center_y.min_value = -2.0
    socket_center_y.max_value = 2.0
    socket_center_y.subtype = 'NONE'
    
    # 面板: 半圆切除设置
    panel_cut = ng.interface.new_panel(texts['Half Cut Settings'])
    
    socket_cut_soft = ng.interface.new_socket(texts['Cut Softness'], in_out='INPUT', socket_type='NodeSocketFloat', parent=panel_cut)
    socket_cut_soft.default_value = 0.0
    socket_cut_soft.min_value = 0.0
    socket_cut_soft.max_value = 1.0
    socket_cut_soft.subtype = 'FACTOR'
    
    socket_rot = ng.interface.new_socket(texts['Rotation'], in_out='INPUT', socket_type='NodeSocketFloat', parent=panel_cut)
    socket_rot.default_value = 0.0
    socket_rot.subtype = 'NONE'
    
    # 输出
    ng.interface.new_socket(texts['Factor'], in_out='OUTPUT', socket_type='NodeSocketFloat')
    
    # --- 创建节点 ---
    nodes = ng.nodes
    links = ng.links
    
    # 辅助函数：创建节点框
    def create_frame(label, nodes_list, color=(0.3, 0.3, 0.3)):
        frame = nodes.new('NodeFrame')
        frame.label = label
        frame.use_custom_color = True
        frame.color = color
        for node in nodes_list:
            node.parent = frame
        return frame

    # 1. 输入输出节点
    node_input = nodes.new('NodeGroupInput')
    node_input.location = (-1600, 0)
    
    node_output = nodes.new('NodeGroupOutput')
    node_output.location = (3200, 0)
    
    # 2. 基础坐标与旋转
    node_tex_coord = nodes.new('ShaderNodeTexCoord')
    node_tex_coord.location = (-1400, 200)
    
    node_rad = nodes.new('ShaderNodeMath')
    node_rad.operation = 'RADIANS'
    node_rad.location = (-1200, -200)
    
    node_rot = nodes.new('ShaderNodeVectorRotate')
    node_rot.rotation_type = 'Z_AXIS'
    node_rot.location = (-1200, 0)
    
    create_frame("基础坐标与旋转", [node_tex_coord, node_rad, node_rot], color=(0.2, 0.4, 0.6))

    # 3. 中心偏移与扭曲
    node_dist_len = nodes.new('ShaderNodeVectorMath')
    node_dist_len.operation = 'LENGTH'
    node_dist_len.location = (-600, 500)
    
    node_dist_weight = nodes.new('ShaderNodeMapRange')
    node_dist_weight.interpolation_type = 'SMOOTHSTEP'
    node_dist_weight.clamp = True
    node_dist_weight.inputs['From Min'].default_value = 0.0
    node_dist_weight.inputs['From Max'].default_value = 1.0
    node_dist_weight.inputs['To Min'].default_value = 1.0
    node_dist_weight.inputs['To Max'].default_value = 0.0
    node_dist_weight.location = (-200, 550)
    
    node_combine_center = nodes.new('ShaderNodeCombineXYZ')
    node_combine_center.location = (-200, 350)
    
    node_weighted_center = nodes.new('ShaderNodeVectorMath')
    node_weighted_center.operation = 'SCALE'
    node_weighted_center.location = (0, 350)
    
    node_apply_offset = nodes.new('ShaderNodeVectorMath')
    node_apply_offset.operation = 'SUBTRACT'
    node_apply_offset.location = (200, 400)
    
    create_frame("中心偏移与扭曲", [node_dist_len, node_dist_weight, node_combine_center, node_weighted_center, node_apply_offset], color=(0.6, 0.4, 0.2))

    # 4. 全局缩放与绝对值
    node_global_scale = nodes.new('ShaderNodeVectorMath')
    node_global_scale.operation = 'DIVIDE'
    node_global_scale.location = (400, 250)
    
    node_shape_abs = nodes.new('ShaderNodeVectorMath')
    node_shape_abs.operation = 'ABSOLUTE'
    node_shape_abs.location = (600, 250)
    
    node_shape_sep = nodes.new('ShaderNodeSeparateXYZ')
    node_shape_sep.location = (800, 250)

    create_frame("全局缩放与预处理", [node_global_scale, node_shape_abs, node_shape_sep], color=(0.4, 0.6, 0.2))

    # 5. 羽化参数计算
    node_safe_feather = nodes.new('ShaderNodeMath')
    node_safe_feather.operation = 'MAXIMUM'
    node_safe_feather.inputs[1].default_value = 0.0001
    node_safe_feather.location = (1000, 600)

    node_feather_half = nodes.new('ShaderNodeMath')
    node_feather_half.operation = 'MULTIPLY'
    node_feather_half.inputs[1].default_value = 2.0
    node_feather_half.location = (1200, 600)
    
    node_feather_uniform = nodes.new('ShaderNodeMath')
    node_feather_uniform.operation = 'MULTIPLY'
    node_feather_uniform.inputs[1].default_value = 0.5
    node_feather_uniform.location = (1400, 600)

    node_feather_sub = nodes.new('ShaderNodeMath')
    node_feather_sub.operation = 'SUBTRACT'
    node_feather_sub.inputs[0].default_value = 1.0
    node_feather_sub.location = (1600, 650)
    
    node_feather_from_min = nodes.new('ShaderNodeMath')
    node_feather_from_min.operation = 'MAXIMUM'
    node_feather_from_min.inputs[1].default_value = 0.0
    node_feather_from_min.location = (1800, 650)

    node_feather_from_max = nodes.new('ShaderNodeMath')
    node_feather_from_max.operation = 'ADD'
    node_feather_from_max.inputs[0].default_value = 1.0
    node_feather_from_max.location = (1800, 500)
    
    create_frame("羽化参数计算", [node_safe_feather, node_feather_half, node_feather_uniform, node_feather_sub, node_feather_from_min, node_feather_from_max], color=(0.5, 0.2, 0.5))

    # 6. 超椭圆形状算法
    node_radius_map = nodes.new('ShaderNodeMapRange')
    node_radius_map.interpolation_type = 'LINEAR'
    node_radius_map.inputs['From Min'].default_value = 0.0
    node_radius_map.inputs['From Max'].default_value = 1.0
    node_radius_map.inputs['To Min'].default_value = 0.065
    node_radius_map.inputs['To Max'].default_value = 0.5
    node_radius_map.location = (1000, 0)

    node_radius_div = nodes.new('ShaderNodeMath')
    node_radius_div.operation = 'DIVIDE'
    node_radius_div.inputs[0].default_value = 1.0
    node_radius_div.location = (1200, -100)

    node_pow_x = nodes.new('ShaderNodeMath')
    node_pow_x.operation = 'POWER'
    node_pow_x.location = (1400, 200)
    
    node_pow_y = nodes.new('ShaderNodeMath')
    node_pow_y.operation = 'POWER'
    node_pow_y.location = (1400, 0)
    
    node_pow_add = nodes.new('ShaderNodeMath')
    node_pow_add.operation = 'ADD'
    node_pow_add.location = (1600, 100)
    
    node_pow_root = nodes.new('ShaderNodeMath')
    node_pow_root.operation = 'POWER'
    node_pow_root.location = (1800, 100)

    create_frame("超椭圆形状算法", [node_radius_map, node_radius_div, node_pow_x, node_pow_y, node_pow_add, node_pow_root], color=(0.2, 0.5, 0.5))

    # 7. 高斯衰减计算
    node_gauss_map = nodes.new('ShaderNodeMapRange')
    node_gauss_map.interpolation_type = 'LINEAR'
    node_gauss_map.clamp = True
    node_gauss_map.inputs['To Min'].default_value = 0.0
    node_gauss_map.inputs['To Max'].default_value = 3.0
    node_gauss_map.location = (2200, 200)
    
    node_gauss_pow2 = nodes.new('ShaderNodeMath')
    node_gauss_pow2.operation = 'POWER'
    node_gauss_pow2.inputs[1].default_value = 2.0
    node_gauss_pow2.location = (2400, 200)
    
    node_gauss_neg = nodes.new('ShaderNodeMath')
    node_gauss_neg.operation = 'MULTIPLY'
    node_gauss_neg.inputs[1].default_value = -1.0
    node_gauss_neg.location = (2600, 200)
    
    node_gauss_exp = nodes.new('ShaderNodeMath')
    node_gauss_exp.operation = 'EXPONENT'
    node_gauss_exp.location = (2800, 200)

    create_frame("高斯衰减计算", [node_gauss_map, node_gauss_pow2, node_gauss_neg, node_gauss_exp], color=(0.7, 0.3, 0.3))

    # 8. 半圆切除逻辑
    node_sep = nodes.new('ShaderNodeSeparateXYZ')
    node_sep.location = (-800, -100)
    
    node_safe_soft = nodes.new('ShaderNodeMath')
    node_safe_soft.operation = 'MAXIMUM'
    node_safe_soft.inputs[1].default_value = 0.001
    node_safe_soft.location = (-1000, -300)
    
    node_cut_shift = nodes.new('ShaderNodeMapRange')
    node_cut_shift.interpolation_type = 'LINEAR'
    node_cut_shift.inputs['From Min'].default_value = 0.0
    node_cut_shift.inputs['From Max'].default_value = 1.0
    node_cut_shift.inputs['To Min'].default_value = -1.1
    node_cut_shift.inputs['To Max'].default_value = -0.001
    node_cut_shift.location = (-800, -200)

    node_cut_tail = nodes.new('ShaderNodeMapRange')
    node_cut_tail.interpolation_type = 'LINEAR'
    node_cut_tail.inputs['From Min'].default_value = 0.0
    node_cut_tail.inputs['From Max'].default_value = 1.0
    node_cut_tail.inputs['To Min'].default_value = -2.2
    node_cut_tail.inputs['To Max'].default_value = -0.002
    node_cut_tail.location = (-800, -400)
    
    node_map_cut = nodes.new('ShaderNodeMapRange')
    node_map_cut.interpolation_type = 'SMOOTHERSTEP'
    node_map_cut.inputs['From Max'].default_value = 0.0
    node_map_cut.inputs['To Min'].default_value = 1.0
    node_map_cut.inputs['To Max'].default_value = 0.0
    node_map_cut.location = (-500, -100)
    
    node_sub_cut = nodes.new('ShaderNodeMath')
    node_sub_cut.operation = 'SUBTRACT'
    node_sub_cut.inputs[0].default_value = 1.0
    node_sub_cut.location = (0, -100)
    
    create_frame("半圆切除逻辑", [node_sep, node_safe_soft, node_cut_shift, node_cut_tail, node_map_cut, node_sub_cut], color=(0.3, 0.3, 0.7))

    # 9. 最终混合
    node_final_mult_cut = nodes.new('ShaderNodeMath')
    node_final_mult_cut.operation = 'MULTIPLY'
    node_final_mult_cut.location = (3000, 200)
    
    create_frame("最终混合", [node_final_mult_cut], color=(0.6, 0.6, 0.6))
    
    # --- 连接节点 ---
    
    # 旋转
    links.new(node_input.outputs[texts['Rotation']], node_rad.inputs[0])
    links.new(node_rad.outputs['Value'], node_rot.inputs['Angle'])
    links.new(node_tex_coord.outputs['Object'], node_rot.inputs['Vector'])
    
    # 半圆切除逻辑 (优先连接，因为位置在左侧)
    links.new(node_input.outputs[texts['Cut Softness']], node_safe_soft.inputs[0])
    links.new(node_safe_soft.outputs['Value'], node_cut_shift.inputs['Value'])
    links.new(node_safe_soft.outputs['Value'], node_cut_tail.inputs['Value'])
    
    links.new(node_rot.outputs['Vector'], node_sep.inputs[0])
    links.new(node_sep.outputs['X'], node_map_cut.inputs['Value'])
    
    links.new(node_cut_shift.outputs['Result'], node_map_cut.inputs['From Max'])
    links.new(node_cut_tail.outputs['Result'], node_map_cut.inputs['From Min'])
    
    links.new(node_map_cut.outputs['Result'], node_sub_cut.inputs[1])
    
    # 偏移逻辑 (扭曲)
    links.new(node_rot.outputs['Vector'], node_dist_len.inputs[0])
    links.new(node_dist_len.outputs['Value'], node_dist_weight.inputs['Value'])
    
    links.new(node_input.outputs[texts['Center X']], node_combine_center.inputs['X'])
    links.new(node_input.outputs[texts['Center Y']], node_combine_center.inputs['Y'])
    
    links.new(node_combine_center.outputs['Vector'], node_weighted_center.inputs['Vector'])
    links.new(node_dist_weight.outputs['Result'], node_weighted_center.inputs['Scale'])
    
    links.new(node_rot.outputs['Vector'], node_apply_offset.inputs[0])
    links.new(node_weighted_center.outputs['Vector'], node_apply_offset.inputs[1])
    
    # 全局缩放逻辑
    links.new(node_apply_offset.outputs['Vector'], node_global_scale.inputs[0])
    links.new(node_input.outputs[texts['Global Scale']], node_global_scale.inputs[1])
    
    # 形状与羽化预处理
    links.new(node_global_scale.outputs['Vector'], node_shape_abs.inputs[0])
    links.new(node_shape_abs.outputs['Vector'], node_shape_sep.inputs[0])
    
    # 羽化参数计算
    links.new(node_input.outputs[texts['Feather']], node_safe_feather.inputs[0])
    links.new(node_safe_feather.outputs['Value'], node_feather_half.inputs[0])
    links.new(node_feather_half.outputs['Value'], node_feather_uniform.inputs[0])

    links.new(node_feather_uniform.outputs['Value'], node_feather_sub.inputs[1]) # 1.0 - Feather
    links.new(node_feather_uniform.outputs['Value'], node_feather_from_max.inputs[1]) # 1.0 + Feather
    
    links.new(node_feather_sub.outputs['Value'], node_feather_from_min.inputs[0])

    # 超椭圆逻辑
    links.new(node_input.outputs[texts['Corner Radius']], node_radius_map.inputs['Value'])
    links.new(node_radius_map.outputs['Result'], node_radius_div.inputs[1])
    
    links.new(node_radius_map.outputs['Result'], node_pow_root.inputs[1]) # Root (1/n)
    links.new(node_radius_div.outputs['Value'], node_pow_x.inputs[1]) # Pow X (n)
    links.new(node_radius_div.outputs['Value'], node_pow_y.inputs[1]) # Pow Y (n)

    links.new(node_shape_sep.outputs['X'], node_pow_x.inputs[0])
    links.new(node_shape_sep.outputs['Y'], node_pow_y.inputs[0])
    
    links.new(node_pow_x.outputs['Value'], node_pow_add.inputs[0])
    links.new(node_pow_y.outputs['Value'], node_pow_add.inputs[1])
    
    links.new(node_pow_add.outputs['Value'], node_pow_root.inputs[0])
    
    # 高斯衰减连接
    links.new(node_pow_root.outputs['Value'], node_gauss_map.inputs['Value'])
    links.new(node_feather_from_min.outputs['Value'], node_gauss_map.inputs['From Min'])
    links.new(node_feather_from_max.outputs['Value'], node_gauss_map.inputs['From Max'])
    
    links.new(node_gauss_map.outputs['Result'], node_gauss_pow2.inputs[0])
    links.new(node_gauss_pow2.outputs['Value'], node_gauss_neg.inputs[0])
    links.new(node_gauss_neg.outputs['Value'], node_gauss_exp.inputs[0])
    
    # 最终混合
    links.new(node_gauss_exp.outputs['Value'], node_final_mult_cut.inputs[0])
    links.new(node_sub_cut.outputs['Value'], node_final_mult_cut.inputs[1])
    
    # 输出
    links.new(node_final_mult_cut.outputs['Value'], node_output.inputs[texts['Factor']])
    
    return ng


class LIGHTING_GADGETS_OT_add_ps_gaussian_node(bpy.types.Operator):
    """添加柔光灯节点"""
    bl_idname = "lighting.add_ps_gaussian_node"
    bl_label = "Add Softbox"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = getattr(context, 'active_object', None)
        if not obj:
            obj = getattr(context, 'object', None)
            
        if not obj:
            return False
        
        if obj.type == 'LIGHT':
            return True
            
        return False
    
    def execute(self, context):
        gaussian_group = create_ps_blur_node_group()
        
        obj = getattr(context, 'active_object', None) or getattr(context, 'object', None)
        tree = None
        
        if not obj:
             self.report({'ERROR'}, "未找到活动物体")
             return {'CANCELLED'}
        
        if obj.type == 'MESH':
            mat = obj.active_material
            mat.use_nodes = True
            tree = mat.node_tree
        elif obj.type == 'LIGHT':
            light = obj.data
            light.use_nodes = True
            tree = light.node_tree
            
        if not tree:
            self.report({'ERROR'}, "无法获取节点树")
            return {'CANCELLED'}
            
        nodes = tree.nodes
        
        group_node = nodes.new('ShaderNodeGroup')
        group_node.node_tree = gaussian_group
        group_node.location = (200, 200) # Offset slightly from default
        
        for node in nodes:
            node.select = False
        group_node.select = True
        nodes.active = group_node
        
        return {'FINISHED'}


def add_node_to_menu(self, context):
    # 仅当活动物体为灯光时显示
    obj = context.active_object
    if not obj or obj.type != 'LIGHT':
        return

    layout = self.layout
    layout.separator()
    layout.operator(LIGHTING_GADGETS_OT_add_ps_gaussian_node.bl_idname, icon='LIGHT_POINT', text="Softbox")

def draw_outliner_clean_linking_menu(self, context):
    layout = self.layout
    layout.separator()
    text = bpy.app.translations.pgettext("Organize Light Linking Collections")
    layout.operator("lighting.clean_light_linking", icon='LIGHT_DATA', text=text)

def register_menus():
    # 尝试添加到 Texture 菜单，如果失败则添加到 Add 菜单
    try:
        if hasattr(bpy.types, "NODE_MT_texture"):
            bpy.types.NODE_MT_texture.append(add_node_to_menu)
        else:
            # 备选: 添加到节点编辑器的 Add 菜单
            bpy.types.NODE_MT_add.append(add_node_to_menu)
    except Exception as e:
        print(f"Error registering node menu: {e}")
        
    # 添加到大纲视图右键菜单
    try:
        bpy.types.OUTLINER_MT_collection.append(draw_outliner_clean_linking_menu)
        bpy.types.OUTLINER_MT_context_menu.append(draw_outliner_clean_linking_menu)
    except Exception as e:
        print(f"Error registering outliner menu: {e}")

def unregister_menus():
    try:
        if hasattr(bpy.types, "NODE_MT_texture"):
            bpy.types.NODE_MT_texture.remove(add_node_to_menu)
        else:
            bpy.types.NODE_MT_add.remove(add_node_to_menu)
    except Exception as e:
        print(f"Error unregistering node menu: {e}")
        
    try:
        bpy.types.OUTLINER_MT_collection.remove(draw_outliner_clean_linking_menu)
        bpy.types.OUTLINER_MT_context_menu.remove(draw_outliner_clean_linking_menu)
    except Exception as e:
        print(f"Error unregistering outliner menu: {e}")
