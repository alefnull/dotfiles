import bpy
from bpy.types import AddonPreferences, PropertyGroup
from bpy.props import EnumProperty, BoolProperty, FloatVectorProperty, FloatProperty, PointerProperty

# 导入翻译字典并在注册时向Blender注册
from .translations.translations import translations_dict

from .lighting_gadgets_ops import (
    LIGHTING_GADGETS_PT_QUICK_PANEL,
    LIGHTING_GADGETS_OT_QUICK_PANEL,
    LIGHTING_GADGETS_OT_MIRROR_SELECTED_LIGHT,
    LIGHTING_GADGETS_OT_REFLECTION_MODE,
    LIGHTING_GADGETS_OT_SELECT_LIGHT_BY_REFLECTION,
    LIGHTING_GADGETS_OT_SELECT_MULTIPLE_LIGHTS_BY_REFLECTION,
    LIGHTING_GADGETS_OT_TOGGLE_STUDIO_LIGHT_CONTROLS,
    LIGHTING_GADGETS_OT_STUDIO_LIGHT_CONTROL_MODAL,
    QuickStudioLightProperties
)

from .lighting_nodes import LIGHTING_GADGETS_OT_add_ps_gaussian_node, register_menus, unregister_menus

def get_key_items():
    """返回所有可用的快捷键选项"""
    # 鼠标按键
    mouse_buttons = [
        ('LEFTMOUSE', "Left Mouse", "Left mouse button"),
        ('MIDDLEMOUSE', "Middle Mouse", "Middle mouse button"),
        ('RIGHTMOUSE', "Right Mouse", "Right mouse button"),
        ('BUTTON4MOUSE', "Mouse Button 4", "Mouse side button 4"),
        ('BUTTON5MOUSE', "Mouse Button 5", "Mouse side button 5"),
        ('BUTTON6MOUSE', "Mouse Button 6", "Mouse side button 6"),
        ('BUTTON7MOUSE', "Mouse Button 7", "Mouse side button 7"),
    ]
    
    # 常用键盘按键
    keyboard_keys = [
        ('SPACE', "Spacebar", "Spacebar key"),
        ('TAB', "Tab", "Tab key"),
        ('A', "A", "A key"),
        ('B', "B", "B key"),
        ('C', "C", "C key"),
        ('D', "D", "D key"),
        ('E', "E", "E key"),
        ('F', "F", "F key"),
        ('G', "G", "G key"),
        ('Q', "Q", "Q key"),
        ('R', "R", "R key"),
        ('S', "S", "S key"),
        ('W', "W", "W key"),
        ('X', "X", "X key"),
        ('Y', "Y", "Y key"),
        ('Z', "Z", "Z key"),
        ('F1', "F1", "F1 key"),
        ('F2', "F2", "F2 key"),
        ('F3', "F3", "F3 key"),
        ('F4', "F4", "F4 key"),
        ('F5', "F5", "F5 key"),
        ('F6', "F6", "F6 key"),
        ('F7', "F7", "F7 key"),
        ('F8', "F8", "F8 key"),
        ('F9', "F9", "F9 key"),
        ('F10', "F10", "F10 key"),
        ('F11', "F11", "F11 key"),
        ('F12', "F12", "F12 key"),
    ]
    
    return [*mouse_buttons, *keyboard_keys]

def update_keybind(self, context):
    """当快捷键设置改变时更新快捷键绑定"""
    # 移除现有的快捷键
    for km, kmi in addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except:
            pass
    addon_keymaps.clear()
    
    # 重新注册快捷键
    wm = context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        # 创建主keymap
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        
        # 注册快速面板快捷键
        if self.enable_quick_panel_shortcut:
            kmi = km.keymap_items.new(
                LIGHTING_GADGETS_OT_QUICK_PANEL.bl_idname,
                type=self.quick_panel_key,
                value='PRESS',
                ctrl=self.quick_panel_ctrl,
                shift=self.quick_panel_shift,
                alt=self.quick_panel_alt
            )
            addon_keymaps.append((km, kmi))
        
        # 注册反射模式快捷键
        kmi = km.keymap_items.new(
            LIGHTING_GADGETS_OT_REFLECTION_MODE.bl_idname,
            type=self.reflection_key,
            value='PRESS',
            ctrl=self.reflection_ctrl,
            shift=self.reflection_shift,
            alt=self.reflection_alt
        )
        addon_keymaps.append((km, kmi))
        
        # 注册选择灯光快捷键
        if self.enable_select_light_shortcut:
            kmi = km.keymap_items.new(
                LIGHTING_GADGETS_OT_SELECT_LIGHT_BY_REFLECTION.bl_idname,
                type='RIGHTMOUSE',
                value='PRESS',
                ctrl=False,
                shift=False,
                alt=True
            )
            addon_keymaps.append((km, kmi))
            
        if self.enable_select_multiple_lights_shortcut:
            kmi = km.keymap_items.new(
                LIGHTING_GADGETS_OT_SELECT_MULTIPLE_LIGHTS_BY_REFLECTION.bl_idname,
                type='RIGHTMOUSE',
                value='PRESS',
                ctrl=False,
                shift=True,
                alt=True
            )
            addon_keymaps.append((km, kmi))

class QUICK_STUDIO_LIGHT_preferences(AddonPreferences):
    bl_idname = __package__

    # --- 快捷键总开关 ---
    enable_quick_panel_shortcut: BoolProperty(
        name="Enable Quick Panel Shortcut",
        description="Enable the shortcut for the Quick Panel (Default: Ctrl + Right Mouse)",
        default=True,
        update=update_keybind
    )
    enable_select_light_shortcut: BoolProperty(
        name="Enable Select Light by Reflection Shortcut",
        description="Enable the shortcut for selecting light by reflection (Default: Alt + Right Mouse)",
        default=True,
        update=update_keybind
    )
    enable_select_multiple_lights_shortcut: BoolProperty(
        name="Enable Select Multiple Lights by Reflection Shortcut",
        description="Enable the shortcut for selecting multiple lights by reflection (Default: Shift + Alt + Right Mouse)",
        default=True,
        update=update_keybind
    )

    quick_panel_key: EnumProperty(
        name="Quick Panel Key",
        description="Select the key for opening the quick panel",
        items=get_key_items(),
        default='RIGHTMOUSE',
        update=update_keybind
    )
    quick_panel_ctrl: BoolProperty(
        name="Ctrl",
        description="Use Ctrl modifier for quick panel shortcut",
        default=True,
        update=update_keybind
    )
    quick_panel_shift: BoolProperty(
        name="Shift",
        description="Use Shift modifier for quick panel shortcut",
        default=False,
        update=update_keybind
    )
    quick_panel_alt: BoolProperty(
        name="Alt",
        description="Use Alt modifier for quick panel shortcut",
        default=False,
        update=update_keybind
    )

    reflection_key: EnumProperty(
        name="Reflection Mode Key",
        description="Select the key for reflection mode",
        items=get_key_items(),
        default='R',
        update=update_keybind
    )
    reflection_ctrl: BoolProperty(
        name="Ctrl",
        description="Use Ctrl modifier for reflection mode shortcut",
        default=False,
        update=update_keybind
    )
    reflection_shift: BoolProperty(
        name="Shift",
        description="Use Shift modifier for reflection mode shortcut",
        default=True,
        update=update_keybind
    )
    reflection_alt: BoolProperty(
        name="Alt",
        description="Use Alt modifier for reflection mode shortcut",
        default=False,
        update=update_keybind
    )
    

    rainbow_border: bpy.props.BoolProperty(
        name="Rainbow Border",
        description="Enable rainbow gradient border in UI",
        default=False
    )
    border_thickness: bpy.props.FloatProperty(
        name="Border Thickness",
        description="Thickness of the viewport border",
        default=3.0,
        min=1.0,
        max=15.0,
        subtype='PIXEL'
    )
    
    text_size: bpy.props.IntProperty(
        name="Text Size",
        description="Size of the mode text",
        default=14,
        min=6,
        max=72
    )
    
    border_opacity: bpy.props.FloatProperty(
        name="Border Opacity",
        description="Opacity of the viewport border",
        default=0.8,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    
    text_opacity: bpy.props.FloatProperty(
        name="Text Opacity",
        description="Opacity of the mode text",
        default=0.8,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    
    # 反射模式颜色
    reflection_color: bpy.props.FloatVectorProperty(
        name="Reflection Mode Color:",
        description="Color for reflection mode UI elements",
        default=(0.52, 0.4, 1.0),
        min=0.0,
        max=1.0,
        size=3,
        subtype='COLOR'
    )
    
    # 精确模式颜色
    precise_color: bpy.props.FloatVectorProperty(
        name="Precise Mode Color:",
        description="Color for precise mode UI elements",
        default=(1.0, 0.4, 0.4),
        min=0.0,
        max=1.0,
        size=3,
        subtype='COLOR'
    )
    
    studio_light_control_color: bpy.props.FloatVectorProperty(
        name="Light Control Points Color",
        description="Color for light control points in viewport",
        default=(1.0, 1.0, 0.0),  # 默认黄色
        min=0.0,
        max=1.0,
        size=3,
        subtype='COLOR'
    )
    
    # 反选灯光颜色提示设置
    enable_selection_color_flash: bpy.props.BoolProperty(
        name="Flash Color on Selection",
        description="Temporarily change light color to orange when selected to provide visual feedback",
        default=True
    )
    
    selection_flash_color: bpy.props.FloatVectorProperty(
        name="Selection Flash Color",
        description="Color to flash when light is selected",
        default=(1.0, 0.5, 0.0),  # 默认橘黄色
        min=0.0,
        max=1.0,
        size=3,
        subtype='COLOR'
    )
    
    hide_all_overlays_in_lighting: bpy.props.BoolProperty(
        name="Hide View Overlays in Lighting Mode",
        description="Hide toolbar, sidebar, overlays and gizmos when entering lighting mode",
        default=True
    )

    
    # 折叠面板状态控制
    ui_display_expanded: bpy.props.BoolProperty(
        name="UI Display Expanded",
        description="Expand UI Display Settings panel",
        default=True
    )
    color_expanded: bpy.props.BoolProperty(
        name="Color Settings Expanded",
        description="Expand Color Settings panel",
        default=True
    )

    def draw(self, context):
        layout = self.layout

        # --- 快速面板 ---
        box = layout.box()
        row = box.row()
        row.prop(self, "enable_quick_panel_shortcut", text=bpy.app.translations.pgettext("Enable Quick Panel Shortcut"))
        
        if self.enable_quick_panel_shortcut:
            sub_box = box.box()
            sub_box.label(text=bpy.app.translations.pgettext("Quick Panel Shortcut Key"))
            row = sub_box.row(align=True)
            row.prop(self, "quick_panel_key", text=bpy.app.translations.pgettext("Key"))
            row.prop(self, "quick_panel_ctrl", text=bpy.app.translations.pgettext("Ctrl"), toggle=True)
            row.prop(self, "quick_panel_shift", text=bpy.app.translations.pgettext("Shift"), toggle=True)
            row.prop(self, "quick_panel_alt", text=bpy.app.translations.pgettext("Alt"), toggle=True)
            sub_box.label(text=f"{bpy.app.translations.pgettext('Current:')} {self.get_shortcut_text('quick_panel')}", icon='KEYINGSET')

        # --- 反射模式 ---
        box = layout.box()
        box.label(text=bpy.app.translations.pgettext("Reflection Mode Shortcut"))
        row = box.row(align=True)
        row.prop(self, "reflection_key", text=bpy.app.translations.pgettext("Key"))
        row.prop(self, "reflection_ctrl", text=bpy.app.translations.pgettext("Ctrl"), toggle=True)
        row.prop(self, "reflection_shift", text=bpy.app.translations.pgettext("Shift"), toggle=True)
        row.prop(self, "reflection_alt", text=bpy.app.translations.pgettext("Alt"), toggle=True)
        box.label(text=f"{bpy.app.translations.pgettext('Current:')} {self.get_shortcut_text('reflection')}", icon='KEYINGSET')

        box = layout.box()
        row = box.row()
        row.prop(self, "enable_select_light_shortcut", text=bpy.app.translations.pgettext("Enable Select Light by Reflection Shortcut (Alt + Right Mouse)"))
        
        row = box.row()
        row.prop(self, "enable_select_multiple_lights_shortcut", text=bpy.app.translations.pgettext("Enable Select Multiple Lights by Reflection Shortcut (Shift + Alt + Right Mouse)"))

        box = layout.box()
        ui_display_expanded = box.prop(self, "ui_display_expanded", text=bpy.app.translations.pgettext("UI Display Settings:"), emboss=False, icon='TRIA_DOWN' if self.ui_display_expanded else 'TRIA_RIGHT')
        
        if self.ui_display_expanded:
            col = box.column(align=True)
            col.label(text=bpy.app.translations.pgettext("Size Settings:"))
            col.prop(self, "border_thickness", slider=True)
            col.prop(self, "text_size", slider=True)
            
            col = box.column(align=True)
            col.label(text=bpy.app.translations.pgettext("Opacity Settings:"))
            col.prop(self, "border_opacity")
            col.prop(self, "text_opacity")
            
            col = box.column(align=True)
            col.label(text=bpy.app.translations.pgettext("Border Style:"))
            col.prop(self, "rainbow_border", toggle=True)
            
            col = box.column(align=True)
            col.label(text=bpy.app.translations.pgettext("UI Hiding Settings:"))
            col.prop(self, "hide_all_overlays_in_lighting", toggle=True)
        
        box = layout.box()
        color_expanded = box.prop(self, "color_expanded", text=bpy.app.translations.pgettext("Color Settings:"), emboss=False, icon='TRIA_DOWN' if self.color_expanded else 'TRIA_RIGHT')
        
        if self.color_expanded:
            col = box.column(align=True)
            col.prop(self, "reflection_color")
            col.prop(self, "precise_color")
            col.prop(self, "studio_light_control_color")
            
            col.separator()
            col.label(text=bpy.app.translations.pgettext("Selection Feedback:"))
            row = col.row(align=True)
            row.prop(self, "enable_selection_color_flash", text=bpy.app.translations.pgettext("Flash Color on Selection"), toggle=True)
            if self.enable_selection_color_flash:
                row.prop(self, "selection_flash_color", text="")
        
    def get_shortcut_text(self, shortcut_type):
        """返回当前快捷键组合的文本描述"""
        if shortcut_type == "quick_panel":
            key = self.quick_panel_key
            ctrl = self.quick_panel_ctrl
            shift = self.quick_panel_shift
            alt = self.quick_panel_alt
        elif shortcut_type == "reflection":
            key = self.reflection_key
            ctrl = self.reflection_ctrl
            shift = self.reflection_shift
            alt = self.reflection_alt
        elif shortcut_type == "select_light":
            return f"{bpy.app.translations.pgettext('Alt')} + {bpy.app.translations.pgettext('Right Mouse')}"
        elif shortcut_type == "select_multiple_lights":
            return f"{bpy.app.translations.pgettext('Shift')} + {bpy.app.translations.pgettext('Alt')} + {bpy.app.translations.pgettext('Right Mouse')}"
        else:
            return bpy.app.translations.pgettext("Unknown")
            
        modifiers = []
        if ctrl:
            modifiers.append(bpy.app.translations.pgettext("Ctrl"))
        if shift:
            modifiers.append(bpy.app.translations.pgettext("Shift"))
        if alt:
            modifiers.append(bpy.app.translations.pgettext("Alt"))
            
        key_text = key  # 默认使用键值
        for item in get_key_items():
            if isinstance(item, tuple) and item[0] == key:
                key_text = item[1]
                break
        
        return " + ".join(modifiers + [key_text]) if modifiers else key_text

classes = (
    QuickStudioLightProperties,  # 确保PropertyGroup首先注册
    LIGHTING_GADGETS_PT_QUICK_PANEL,
    LIGHTING_GADGETS_OT_QUICK_PANEL,
    LIGHTING_GADGETS_OT_MIRROR_SELECTED_LIGHT,
    LIGHTING_GADGETS_OT_REFLECTION_MODE,
    LIGHTING_GADGETS_OT_SELECT_LIGHT_BY_REFLECTION,
    LIGHTING_GADGETS_OT_SELECT_MULTIPLE_LIGHTS_BY_REFLECTION,
    LIGHTING_GADGETS_OT_TOGGLE_STUDIO_LIGHT_CONTROLS,
    LIGHTING_GADGETS_OT_STUDIO_LIGHT_CONTROL_MODAL,
    LIGHTING_GADGETS_OT_add_ps_gaussian_node,
    QUICK_STUDIO_LIGHT_preferences,
)

addon_keymaps = []

def register():
    """Register the addon"""
    # Register classes
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # --- 注册翻译 ---
    try:
        bpy.app.translations.register(__name__, translations_dict)
    except Exception as e:
        pass
    
    # Register custom properties
    bpy.types.WindowManager.lighting_gadgets_props = PointerProperty(type=QuickStudioLightProperties)
    
    bpy.types.Light.quick_studio_light = PointerProperty(type=QuickStudioLightProperties)
    
    # Register keymaps
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    
    # 注册菜单
    register_menus()
    
    if kc:
        # 创建主keymap
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        
        try:
            prefs = bpy.context.preferences.addons[__package__].preferences
            
            # 注册快速面板快捷键
            if prefs.enable_quick_panel_shortcut:
                kmi = km.keymap_items.new(
                    LIGHTING_GADGETS_OT_QUICK_PANEL.bl_idname,
                    type=prefs.quick_panel_key,
                    value='PRESS',
                    ctrl=prefs.quick_panel_ctrl,
                    shift=prefs.quick_panel_shift,
                    alt=prefs.quick_panel_alt
                )
                addon_keymaps.append((km, kmi))
            
            # 注册反射模式快捷键
            kmi = km.keymap_items.new(
                LIGHTING_GADGETS_OT_REFLECTION_MODE.bl_idname,
                type=prefs.reflection_key,
                value='PRESS',
                ctrl=prefs.reflection_ctrl,
                shift=prefs.reflection_shift,
                alt=prefs.reflection_alt
            )
            addon_keymaps.append((km, kmi))
            
            if prefs.enable_select_light_shortcut:
                kmi = km.keymap_items.new(
                    LIGHTING_GADGETS_OT_SELECT_LIGHT_BY_REFLECTION.bl_idname,
                    type='RIGHTMOUSE',
                    value='PRESS',
                    ctrl=False,
                    shift=False,
                    alt=True
                )
                addon_keymaps.append((km, kmi))
            
            if prefs.enable_select_multiple_lights_shortcut:
                kmi = km.keymap_items.new(
                    LIGHTING_GADGETS_OT_SELECT_MULTIPLE_LIGHTS_BY_REFLECTION.bl_idname,
                    type='RIGHTMOUSE',
                    value='PRESS',
                    ctrl=False,
                    shift=True,
                    alt=True
                )
                addon_keymaps.append((km, kmi))
                
        except (AttributeError, KeyError):
            # 如果无法获取首选项，使用默认快捷键
            # 快速面板 - Ctrl + 右键
            kmi = km.keymap_items.new(
                LIGHTING_GADGETS_OT_QUICK_PANEL.bl_idname,
                type='RIGHTMOUSE',
                value='PRESS',
                ctrl=True
            )
            addon_keymaps.append((km, kmi))
            
            # 反射模式 - Shift + R
            kmi = km.keymap_items.new(
                LIGHTING_GADGETS_OT_REFLECTION_MODE.bl_idname,
                type='R',
                value='PRESS',
                shift=True
            )
            addon_keymaps.append((km, kmi))
            
            # 选择灯光 - Alt + 右键
            kmi = km.keymap_items.new(
                LIGHTING_GADGETS_OT_SELECT_LIGHT_BY_REFLECTION.bl_idname,
                type='RIGHTMOUSE',
                value='PRESS',
                alt=True
            )
            addon_keymaps.append((km, kmi))
            
            # 选择多个灯光 - Shift + Alt + 右键
            kmi = km.keymap_items.new(
                LIGHTING_GADGETS_OT_SELECT_MULTIPLE_LIGHTS_BY_REFLECTION.bl_idname,
                type='RIGHTMOUSE',
                value='PRESS',
                shift=True,
                alt=True
            )
            addon_keymaps.append((km, kmi))

def unregister():
    """Unregister the addon"""
    # --- 注销翻译 ---
    # 统一注销翻译，不依赖语言环境，避免语言切换带来的意外状态
    try:
        bpy.app.translations.unregister(__name__)
    except Exception as e:
        pass
    
    # Unregister keymaps - 增强错误处理
    for km, kmi in addon_keymaps:
        try:
            if km and kmi:
                km.keymap_items.remove(kmi)
        except (ReferenceError, AttributeError, RuntimeError):
            # 快捷键可能已被移除或无效
            pass
    addon_keymaps.clear()
    
    # 注销菜单
    try:
        unregister_menus()
    except Exception:
        pass
    
    # 删除窗口管理器级别的属性
    if hasattr(bpy.types.WindowManager, 'lighting_gadgets_props'):
        try:
            del bpy.types.WindowManager.lighting_gadgets_props
        except (AttributeError, ReferenceError):
            pass
    
    # 删除Light级别的属性
    if hasattr(bpy.types.Light, 'quick_studio_light'):
        try:
            del bpy.types.Light.quick_studio_light
        except (AttributeError, ReferenceError):
            pass
    
    # Unregister classes - 增强错误处理
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except (RuntimeError, ValueError):
            # 类可能已被注销或不存在
            pass
    
    # 确保操作文件中的状态管理器被清理
    try:
        from .lighting_gadgets_ops import _state_manager
        if _state_manager:
            _state_manager.clear_all_states()
    except:
        pass

if __name__ == "__main__":
    register()
