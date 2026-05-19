import bpy
import os
import shutil
import platform
from bpy.types import Menu
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from .utils import Get_addon_pref


class BAGAPIE_MT_pie_menu_geopack(Menu):
    bl_label = "BagaPie GeoPack"
    bl_idname = "BAGAPIE_MT_pie_menu_geopack"

    def draw(self, context:bpy.types.Context):

        bagapie_pref = Get_addon_pref()
        if not bagapie_pref.hide_geopack:
            layout = self.layout
            pie = layout.menu_pie()

            pie_branch_count = len(bagapie_pref.geopacks_list)
            if pie_branch_count == 0:
                box = pie.box()
                box.label(text='No packs detected')
                box.label(text='Setup GeoPack Location or Install Pack')
                box.label(text='Go to Edit > Preferences > Bagapie > GeoPack')

            if pie_branch_count > 8:
                pie_branch_count = 8

            for id in range(pie_branch_count+1):
                col = pie.column(align = True)
                for i, pack_item in enumerate(bagapie_pref.geopacks_list):
                    
                    if not pack_item.pieVisibility:
                        continue

                    if (i + 1) % 8 == id:
                        # a PropertyGroup cannot be assigned to an operator
                        # but it can be passed through the context

                        col.context_pointer_set('my_pack', pack_item)
                        col.operator(operator="wm.call_menu_pie",text= f"{pack_item.name}").name = 'BAGAPIE_MT_geopack_select_modifier'

def same_disk(path1, path2):
    """
    Checks if two directory paths are on the same disk.
    Returns True if they are, False otherwise.
    """
    return os.stat(path1).st_dev == os.stat(path2).st_dev

def _free_space(path):
    stat = shutil.disk_usage(path)
    return stat.free

def _total_size(source):
        total_size = os.path.getsize(source)
        for item in os.listdir(source):
            itempath = os.path.join(source, item)
            if os.path.isfile(itempath):
                total_size += os.path.getsize(itempath)
            elif os.path.isdir(itempath):
                total_size += _total_size(itempath)
        return total_size

class BAGAPIE_OT_bp_move(Operator, ImportHelper):
    """Move all packs to a new location"""
    bl_idname = "bagapie.bp_move"
    bl_label = "New Location"

    filepath: bpy.props.StringProperty(subtype='DIR_PATH') # type: ignore
    sourcePath: bpy.props.StringProperty() # type: ignore
    files: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup) # type: ignore

    def execute(self, context):
        # Determine the platform to use the appropriate file operation
        system_platform = platform.system()
        if system_platform == "Windows":
            move_function = shutil.move
        elif system_platform in ["Linux", "Darwin"]:
            move_function = os.replace

        if self.filepath in self.sourcePath:
            message = "Destination path can not be in source path."
            self.report({'ERROR'}, message)

            return {'CANCELLED'}

        # Check if the new directory already exists
        if not os.path.exists(self.filepath):
            os.makedirs(self.filepath)
        
        directory_size = _total_size(self.sourcePath)
        free_space = _free_space(self.filepath)
        
        if directory_size < free_space or same_disk(self.sourcePath,self.filepath):
            # Loop through each item in the source directory
            for item in os.listdir(self.sourcePath):
                # Check if the item is a directory starting with 'BP_'
                if os.path.isdir(os.path.join(self.sourcePath, item)) and item.startswith("GP_"):
                    # Move the item to the new directory
                    move_function(os.path.join(self.sourcePath, item), os.path.join(self.filepath, item))

            # Display a message to the user
            message = f"All packs have been moved from {self.sourcePath} to {self.filepath}."
            self.report({'INFO'}, message)

            pref = Get_addon_pref()
            pref.geopack_packs_location = self.filepath
            pref.ScanGeoPacks(context)
        else:
            message = f"Not enough disk space in {self.filepath}."
            self.report({'ERROR'}, message)
            return {'CANCELLED'}
        
        return {'FINISHED'}

    # def invoke(self, context, event):
    #     # Set the default directory to the current blend file's directory
    #     blend_dir = os.path.dirname(bpy.data.filepath)
    #     self.directory = blend_dir

    #     # Open the file browser to select the new location
    #     context.window_manager.fileselect_add(self)
    #     return {'RUNNING_MODAL'}

classes = [
    BAGAPIE_MT_pie_menu_geopack,
    BAGAPIE_OT_bp_move,
]