#region Information
'''
This file contains the classes for creating the tool panels that appear
alongside the 3D viewport.
'''
#endregion
#region Module Imports
import bpy
from bpy.props import *
from bpy.types import (Panel,Menu,Operator,PropertyGroup)
#endregion
#region Panel - Tool - Tools
class OBJECT_PT_ByGenTools(Panel):
    bl_idname = "OBJECT_PT_ByGenTools"
    bl_label = "Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BY-GEN"

    def draw_header(self, context):
        self.layout.label(text = "", icon = "TOOL_SETTINGS")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        bytool = scene.by_tool

        #Operations Layout
        box = layout.box()
        box.label(text="Useful Operations")
        col = box.column()
        colrow = col.row(align=True)
        colrow.operator("object.bygen_apply_modifiers")
        colrow = col.row(align=True)
        colrow.operator("object.bygen_purge_textures")
        colrow = col.row(align=True)
        colrow.operator("object.bygen_clear_generation_result")
        colrow = col.row(align=True)
        colrow.operator("object.bygen_backup_generation_result")
#endregion
#region Panel - Tool - Info
class OBJECT_PT_ByGenInfo(Panel):
    bl_idname = "OBJECT_PT_ByGenInfo"
    bl_label = "Info"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BY-GEN"

    def draw_header(self, context):
        self.layout.label(text = "", icon = "INFO")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        bytool = scene.by_tool

        #Operations Layout
        box = layout.box()
        box.operator("wm.url_open", text="Created by Curtis Holt", icon='FILE_SCRIPT').url = "https://www.curtisholt.online"
#endregion
#region Registration
classes = (
    #OBJECT_PT_ByGenTools, # Removed for V10. Can re-add if becomes useful again.
    OBJECT_PT_ByGenInfo,
)
def register():
    # Importing register class
    from bpy.utils import register_class

    # Registering main classes:
    for cls in classes:
        register_class(cls)

def unregister():
    # Importing unregister class
    from bpy.utils import unregister_class

    # Unregistering main classes:
    for cls in reversed(classes):
        unregister_class(cls)
#endregion