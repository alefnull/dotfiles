"""
Vulkan兼容性层
为Quick Studio Light插件提供OpenGL到Vulkan的兼容性支持
基于Blender官方Vulkan后端文档实现
"""

import bpy
import gpu
from gpu_extras.batch import batch_for_shader

# Vulkan兼容性检测
def is_vulkan_backend():
    """检测当前是否使用Vulkan后端"""
    try:
        # 首选方法：使用gpu.platform.backend_type_get()获取运行时实际后端
        if hasattr(gpu, 'platform') and hasattr(gpu.platform, 'backend_type_get'):
            return gpu.platform.backend_type_get() == 'VULKAN'
        
        # 备用方法：检查用户偏好设置（需要重启生效）
        if hasattr(bpy.context.preferences.system, 'gpu_backend'):
            return bpy.context.preferences.system.gpu_backend == 'VULKAN'
        
        # 最后备用：检查命令行参数
        import sys
        return '--debug-gpu-vulkan' in sys.argv or '--debug-gpu-vulkan-local-read' in sys.argv
    except:
        return False

def get_gpu_backend_info():
    """获取当前GPU后端信息"""
    try:
        # 获取运行时实际后端
        backend = "Unknown"
        if hasattr(gpu, 'platform') and hasattr(gpu.platform, 'backend_type_get'):
            backend = gpu.platform.backend_type_get()
        elif hasattr(bpy.context.preferences.system, 'gpu_backend'):
            backend = bpy.context.preferences.system.gpu_backend
        
        # 检查是否启用Vulkan调试扩展
        import sys
        vulkan_debug_enabled = '--debug-gpu-vulkan' in sys.argv or '--debug-gpu-vulkan-local-read' in sys.argv
        
        # 基于实际后端判断是否为Vulkan
        is_vulkan_backend = (backend == 'VULKAN')
        
        # 支持Vulkan的条件：当前后端是Vulkan，或者启用了Vulkan调试模式
        supports_vulkan = is_vulkan_backend or vulkan_debug_enabled
        
        return {
            'backend': backend,
            'supports_vulkan': supports_vulkan,
            'is_vulkan': is_vulkan_backend,
            'vulkan_debug_enabled': vulkan_debug_enabled,
            'blender_version': bpy.app.version_string
        }
    except:
        return {
            'backend': 'OpenGL',
            'supports_vulkan': False,
            'is_vulkan': False,
            'vulkan_debug_enabled': False,
            'blender_version': bpy.app.version_string
        }

# Vulkan兼容的着色器创建
def create_compatible_shader(shader_info):
    """创建兼容Vulkan的着色器"""
    try:
        # 检查是否支持新的着色器创建方法
        if hasattr(gpu.shader, 'create_from_info'):
            return gpu.shader.create_from_info(shader_info)
        else:
            # 回退到内置着色器
            return gpu.shader.from_builtin('UNIFORM_COLOR')
    except Exception as e:
        print(f"Vulkan兼容着色器创建失败: {e}")
        # 使用内置着色器作为回退
        return gpu.shader.from_builtin('UNIFORM_COLOR')

def create_builtin_shader(shader_type='UNIFORM_COLOR'):
    """创建内置着色器，兼容Vulkan和OpenGL"""
    try:
        # 检查支持的着色器类型
        if hasattr(gpu.shader, 'from_builtin'):
            return gpu.shader.from_builtin(shader_type)
        else:
            # 回退方案
            return gpu.shader.from_builtin('UNIFORM_COLOR')
    except Exception as e:
        print(f"内置着色器创建失败: {e}")
        return None

# 深度测试模式映射
def _map_depth_test_mode(mode):
    """将深度测试模式映射到Blender兼容的枚举值"""
    # Blender期望标准的OpenGL枚举值，不需要映射
    valid_modes = {'NONE', 'ALWAYS', 'LESS', 'LESS_EQUAL', 'EQUAL', 'GREATER', 'GREATER_EQUAL', 'NEVER', 'NOTEQUAL'}
    
    # 如果模式有效，直接返回；否则返回'NONE'作为安全值
    if mode in valid_modes:
        return mode
    else:
        print(f"警告: 无效的深度测试模式 '{mode}'，使用'NONE'作为回退")
        return 'NONE'

# Vulkan兼容的状态管理
class VulkanCompatibleStateManager:
    """Vulkan兼容的状态管理器"""
    
    def __init__(self):
        self.is_vulkan = is_vulkan_backend()
        self.original_states = {}
    
    def set_depth_test(self, mode):
        """设置深度测试模式"""
        try:
            # 将模式映射到Vulkan兼容的枚举值
            mapped_mode = _map_depth_test_mode(mode)
            
            # 统一使用gpu.state API，兼容Vulkan和OpenGL
            if hasattr(gpu.state, 'depth_test_set'):
                gpu.state.depth_test_set(mapped_mode)
        except Exception as e:
            print(f"深度测试设置失败: {e}")
    
    def set_blend_mode(self, mode):
        """设置混合模式"""
        try:
            # 统一使用gpu.state API，兼容Vulkan和OpenGL
            if hasattr(gpu.state, 'blend_set'):
                gpu.state.blend_set(mode)
        except Exception as e:
            print(f"混合模式设置失败: {e}")
    
    def set_line_width(self, width):
        """设置线宽"""
        try:
            # 统一使用gpu.state API，兼容Vulkan和OpenGL
            if hasattr(gpu.state, 'line_width_set'):
                if self.is_vulkan:
                    # Vulkan模式下可能需要整数线宽
                    gpu.state.line_width_set(int(width))
                else:
                    gpu.state.line_width_set(width)
        except Exception as e:
            print(f"线宽设置失败: {e}")
    
    def reset_all_states(self):
        """重置所有状态"""
        try:
            # 重置深度测试
            self.set_depth_test('NONE')
            # 重置混合模式
            self.set_blend_mode('NONE')
            # 重置线宽
            self.set_line_width(1.0)
        except Exception as e:
            print(f"状态重置失败: {e}")

# Vulkan兼容的批次创建
def create_compatible_batch(shader, draw_type, content, indices=None):
    """创建兼容Vulkan的批次"""
    try:
        if indices is not None:
            return batch_for_shader(shader, draw_type, content, indices=indices)
        else:
            return batch_for_shader(shader, draw_type, content)
    except Exception as e:
        print(f"批次创建失败: {e}")
        return None

# 性能优化函数
def optimize_for_vulkan():
    """为Vulkan后端优化性能"""
    if not is_vulkan_backend():
        return
    
    try:
        # Vulkan特定的优化
        # 检查是否支持本地读取扩展
        if '--debug-gpu-vulkan-local-read' in __import__('sys').argv:
            pass
        
    except Exception as e:
        pass

# 兼容性检查函数
def check_compatibility():
    """检查当前系统的Vulkan兼容性"""
    info = get_gpu_backend_info()
    
    if info.get('vulkan_debug_enabled', False):
        pass
    
    if info['is_vulkan']:
        optimize_for_vulkan()
    else:
        pass
    
    return info

# 错误处理装饰器
def vulkan_compatible(func):
    """Vulkan兼容性装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Vulkan兼容函数 {func.__name__} 失败: {e}")
            # 尝试回退方案
            return None
    return wrapper

# 全局单例实例
_global_manager = VulkanCompatibleStateManager()

def get_vulkan_manager():
    """获取全局Vulkan状态管理器实例"""
    return _global_manager