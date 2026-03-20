import bpy
import subprocess
import os
import platform
import shutil
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from .utils import Warning

###################################################################################
# GET ADDON PATH
###################################################################################
def Get_Addon_Path(self, context):
    filepath = os.path.dirname(__file__)
    return filepath

###################################################################################
# Create asset library for the selected pack
###################################################################################
class BAGAPIE_OT_geopack_create_assetlib(Operator):
    """ Create new asset library for the selected pack """
    bl_idname = "bagapie.geopack_create_assetlib"
    bl_label = 'Create Asset Library'
    
    pack_name: bpy.props.StringProperty()
    pack_path: bpy.props.StringProperty()

    def execute(self, context):

        prefs = bpy.context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries

        add = True
        for lib in asset_libraries:
            if lib.name == self.pack_name:
                Warning(message = "The library is already installed.", title = "INFO", icon = 'INFO')
                add = False
        if add:

            # Create a new folder in the pack directory
            new_folder_name = "Assets"
            new_folder_path = os.path.join(self.pack_path, new_folder_name)
            # Check if the "Assets" folder already exists
            assets_folder_path = os.path.join(self.pack_path, "Assets")
            if not os.path.exists(assets_folder_path):
                os.mkdir(new_folder_path)

            # Add the new folder as an asset library
            bpy.ops.preferences.asset_library_add(directory=new_folder_path)
            asset_libraries[len(asset_libraries)-1].name = self.pack_name

            Warning(message = "Add your blend files here (content visible in the Asset Browser)", title = self.pack_name +"'s library created", icon = 'INFO')

        return {'FINISHED'}


###################################################################################
# ADD BLEND FILE TO LIBRARY
###################################################################################
class BAGAPIE_OT_geopack_assetlib_add_file(Operator, ImportHelper):
    """ Create new asset library for the selected pack """
    bl_idname = "bagapie.geopack_assetlib_add_file"
    bl_label = 'Add blend file to the pack library'

    filter_glob: bpy.props.StringProperty(
        default='*.blend',
        options={'HIDDEN'}
    ) # type: ignore

    pack_path: bpy.props.StringProperty(
        options={'HIDDEN'}
    ) # type: ignore

    def execute(self, context):

        # Get the absolute path of the pack's "Assets" folder
        assets_folder_path = os.path.join(self.pack_path, "Assets")

        # Copy the .blend file to the pack's "Assets" folder
        filename = os.path.basename(self.filepath)
        destination_path = os.path.join(assets_folder_path, filename)
        shutil.copy2(self.filepath, destination_path)

        # Display a message to the user
        message = f"{filename} has been added to the asset library."
        title = "Blend file added !"
        Warning(message=message, title=title, icon='INFO')

        return {'FINISHED'}


###################################################################################
# OPEN FILE EXPLORER
###################################################################################
class BAGAPIE_OT_open_file_explorer(Operator):
    """Open File Explorer"""
    bl_idname = "bagapie.open_file_explorer"
    bl_label = "Open File Explorer"

    filepath: bpy.props.StringProperty()

    def execute(self, context):
        try:
            # Get the user's operating system
            os_name = platform.system().lower()
            path = os.path.join(self.filepath, "Assets")

            # Open the file explorer at the given filepath based on the operating system
            if os_name == 'windows':
                subprocess.Popen(['explorer', path])
            elif os_name == 'darwin':
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])
                
        except:
            Warning(message="Could not open file explorer", title="Error", icon='ERROR')

        return {'FINISHED'}


classes = [
    BAGAPIE_OT_geopack_create_assetlib,
    BAGAPIE_OT_geopack_assetlib_add_file,
    BAGAPIE_OT_open_file_explorer,
]