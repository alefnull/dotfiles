import bpy
from .utils import get_addon_prefs

class VIEW3D_MT_nd_primitive_menu(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_nd_primitive_menu"
    bl_label = "ND Primitives"

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return True

    def draw(self, context):
        draw_items(self, context)

def menu_func(self, context):
    layout = self.layout
    layout.menu(VIEW3D_MT_nd_primitive_menu.bl_idname, icon="FILE_3D")
    layout.separator()

def register_add_menu():
    prefs = get_addon_prefs()

    if prefs.show_in_menu == "ADD_MESH":
        bpy.types.VIEW3D_MT_mesh_add.prepend(draw_add_nd_primitive)

    elif prefs.show_in_menu == "OWN_CATEGORY_IN_ADD_MENU":
        bpy.types.VIEW3D_MT_mesh_add.prepend(menu_func)
        
    elif prefs.show_in_menu == "OWN_MENU_CATEGORY":
        bpy.types.VIEW3D_MT_add.prepend(menu_func)

    elif prefs.show_in_menu == "NONE":
        pass

def update_add_menu(self, context):
    unregister_add_menu()

    if self.show_in_menu == "ADD_MESH":
        bpy.types.VIEW3D_MT_mesh_add.prepend(draw_add_nd_primitive)

    elif self.show_in_menu == "OWN_CATEGORY_IN_ADD_MENU":
        bpy.types.VIEW3D_MT_mesh_add.prepend(menu_func)
        
    elif self.show_in_menu == "OWN_MENU_CATEGORY":
        bpy.types.VIEW3D_MT_add.prepend(menu_func)

    elif self.show_in_menu == "NONE":
        unregister_add_menu()

def unregister_add_menu():
    bpy.types.VIEW3D_MT_mesh_add.remove(draw_add_nd_primitive)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    bpy.types.VIEW3D_MT_add.remove(menu_func)

def draw_items(self, context):
    from .addon_preferences import CONST_ITEMS

    if context.mode == 'OBJECT':
        layout = self.layout    
        layout.label(text="ND Primitives", icon='FILE_3D')
        for item_name, icon in CONST_ITEMS:
            if item_name not in ("Other", "CUSTOM_OP"):
                layout.operator("mesh.add_nd_primitive", text=item_name, icon=icon).type = item_name

def draw_add_nd_primitive(self, context):
    draw_items(self, context)
    layout = self.layout    
    layout.separator()
