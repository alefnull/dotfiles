import bpy
import os
import bpy.utils.previews
import shutil
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from . import bagapie_geopack_icon
from .utils import Get_addon_pref

previews = bpy.utils.previews.new()

def import_icons():
    global previews

    pref = Get_addon_pref()
    filepath = pref.geopack_packs_location
    
    for  dirpath, dirnames, filenames in os.walk(filepath):
        if 'geopack.config' in filenames:
            for file in os.listdir(dirpath):
                file_path = os.path.join(dirpath, file)
                if os.path.isfile(file_path) and file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
                    icon_name = os.path.splitext(file)[0]
                    if icon_name not in bagapie_geopack_icon.previews:
                        previews.load(icon_name, file_path, 'IMAGE')
                    else:
                        alt_name = icon_name.replace(" ", "_")
                        if alt_name not in bagapie_geopack_icon.previews:
                            previews.load(alt_name, file_path, 'IMAGE')

def unload_icons():
    global previews
    try:
        bpy.utils.previews.remove(previews)
    except:
        pass

class BAGAPIE_OT_add_icon(Operator, ImportHelper):
    bl_idname = "bagapie.add_icon"
    bl_label = "Copier l'image dans le dossier du GeoPack"

    filter_glob: bpy.props.StringProperty(
        default="*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff",
        options={'HIDDEN'},
    ) # type: ignore

    target_folder: bpy.props.StringProperty(
        name="Dossier Cible",
        default="//",
        subtype='DIR_PATH',
        options={'HIDDEN'},
    ) # type: ignore
    img_mo_name: bpy.props.StringProperty(
        name="None",
        default="",
        options={'HIDDEN'},
    ) # type: ignore

    def execute(self, context):
        filepath = self.properties.filepath #file selected by user

        shutil.copy(filepath, self.target_folder) #copy file

        # Obtien nom du fichier sans le chemin et son extension
        original_name, file_extension = os.path.splitext(os.path.basename(filepath))
        
        new_name = self.img_mo_name + file_extension
        
        current_file_path = os.path.join(self.target_folder, original_name + file_extension)
        
        new_file_path = os.path.join(self.target_folder, new_name)
        
        os.rename(current_file_path, new_file_path)
        
        import_icons()

        return {'FINISHED'}

class BAGAPIE_OT_remove_icon(Operator):
    bl_idname = "bagapie.remove_icon"
    bl_label = "Delete Icon"

    target_folder: bpy.props.StringProperty(
        name="Dossier Cible",
        default="//",
        subtype='DIR_PATH'
    ) # type: ignore
    img_mo_name: bpy.props.StringProperty(
        name="image_name",
        default="",
    ) # type: ignore

    def execute(self, context):
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff']

        abs_target_folder = bpy.path.abspath(self.target_folder) # absolute path
        file_path = os.path.join(abs_target_folder, self.img_mo_name) # complete path

        for ext in image_extensions:
            file_path = os.path.join(abs_target_folder, self.img_mo_name + ext)
            if os.path.isfile(file_path):
                os.remove(file_path)
                break
        
        unload_icons()
        import_icons()

        return {'FINISHED'}

class BAGAPIE_OT_refresh_icons(Operator):
    """Reload all GeoPack icons from disk"""
    bl_idname = "bagapie.refresh_icons"
    bl_label = "Refresh GeoPack Icons"

    def execute(self, context):
        unload_icons()
        import_icons()
        self.report({'INFO'}, "GeoPack icons refreshed")
        return {'FINISHED'}

classes = [
    BAGAPIE_OT_add_icon,
    BAGAPIE_OT_remove_icon,
    BAGAPIE_OT_refresh_icons,
]