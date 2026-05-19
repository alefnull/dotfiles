import bpy
import os
from bpy.types import Operator
import shutil
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper,ExportHelper
import ntpath
from zipfile import ZipFile
from .utils import sanitize_filename
from . import bagapie_geopack_icon
from .utils import Get_addon_pref, Warning, debug
import subprocess
import platform


def generate_baga_libraries(lite_versions, full_versions):
    return [f'Bagapieassets_database_lite_V{i}.blend' for i in range(1, lite_versions + 1)] + \
           [f'Bagapieassets_database_V{i}.blend' for i in range(1, full_versions + 1)] + \
           ['Bagapieassets_database_free.blend',
            'Bagapieassets_database_essential.blend',
            'blender_assets.cats.txt']

def generate_baga_packages(lite_volumes, full_volumes):
    return [f'BagaPie_Assets_Lite_Vol_{i}.baga' for i in range(1, lite_volumes + 1)] + \
           [f'BagaPie_Assets_Vol_{i}.baga' for i in range(1, full_volumes + 1)] + \
           ['BagaPie_Assets_Free.baga', 'BagaPie_Assets_Essential.baga']

# Specify the number of lite versions and full versions
lite_versions = 10
full_versions = 20

baga_libraries = generate_baga_libraries(lite_versions, full_versions)
baga_packages = generate_baga_packages(lite_versions, full_versions)


###################################################################################
# OPEN ASSET REPO FOLDER
###################################################################################
class BAGAPIE_OT_setup_package_location(Operator, ImportHelper):
    """Set BagaPie Package Location"""
    bl_idname = 'bagapie.setuppacklocation'
    bl_label = 'Select Library Location'
    bl_options = {'REGISTER', 'UNDO'}

    filter_folder = True
    filter_image = False
    filter_blender = False

    def execute(self, context):
        pref = Get_addon_pref()
        location_new = os.path.normpath(self.filepath) + os.sep
        
        if not location_new.endswith(os.sep):
            location_new += os.sep

        pref.library_location = location_new
        filepaths = context.preferences.filepaths
        asset_libraries = filepaths.asset_libraries

        existing_lib = next((lib for lib in asset_libraries if lib.name == "BagaPie Assets"), None)
        
        if existing_lib:
            existing_lib.path = location_new
        else:
            bpy.ops.preferences.asset_library_add(directory=location_new)
            asset_libraries[-1].name = "BagaPie Assets"

        Warning(message="Now you can install BagaPie asset pack !", title="Location Set", icon='NONE')

        return {'FINISHED'}


###################################################################################
# OPEN ASSET REPO FOLDER
###################################################################################
class BAGAPIE_OT_open_lib_folder(Operator):
    """Open the asset repository"""
    bl_idname = 'bagapie.openlibfolder'
    bl_label = 'Open Library Folder'

    def execute(self, context):
        pref = Get_addon_pref()
        location_library = pref.library_location

        if location_library == "NONE":
            location_library = bpy.utils.user_resource('DATAFILES', path="Bagapie", create=True)

        # Normalize path
        location_library = bpy.path.abspath(location_library)
        location_library = os.path.normpath(location_library)

        try:
            os_name = platform.system().lower()

            if os_name == 'windows':
                os.startfile(location_library)

            elif os_name == 'darwin':
                subprocess.Popen(['open', location_library])

            else:
                subprocess.Popen(['xdg-open', location_library])

        except Exception as e:
            Warning(message=f"Could not open file explorer\n{e}", title="Error", icon='ERROR')

        return {'FINISHED'}


###################################################################################
# INSTALL A NEW BAGAPIE PACKAGE (ASSET PACK)
###################################################################################
class BAGAPIE_OT_install_package(Operator, ImportHelper):
    """Install a BagaPie Pack"""
    bl_idname = 'bagapie.installpack'
    bl_label = 'Install BagaPie Assets Pack'
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(
        default='*.baga',
        options={'HIDDEN'}
        ) # type: ignore

    replace_pack:  bpy.props.BoolProperty(
        name="Replace pack",
        default=False
        ) # type: ignore

    def execute(self, context):
        bagapie_pref = Get_addon_pref()
        location_library = bagapie_pref.library_location
        
        if bagapie_pref.debug:
            print("Location Library : "+location_library)

        filename, extension = os.path.splitext(self.filepath)
        add = True
        pack_to_install = []
        pack_already_installed = []
        
        new_file_path = filename + '.zip'
        
        # Using shutil.move instead of os.rename
        shutil.move(self.filepath, new_file_path)

        try:
            with ZipFile(new_file_path, 'r') as zip_ref:
                for pack in zip_ref.namelist():
                    if os.path.exists(location_library + ntpath.basename(pack)) and not self.replace_pack:
                        print("Package already installed : " + pack)
                        pack_already_installed.append(pack)
                    else:
                        pack_to_install.append(pack)
        except:
            Warning(message = "Please, select a BagaPie_Assets_Vol_X.baga file (the one you downloaded).", title = "Installation Fail", icon = 'INFO')

        if len(pack_to_install) > 0 or self.replace_pack:
            for del_pack in pack_already_installed:
                os.remove(location_library + ntpath.basename(del_pack))
            try:
                os.remove(location_library + ntpath.basename('blender_assets.cats.txt'))
            except:
                pass
            shutil.unpack_archive(new_file_path, location_library)  # Changed filepath to new_file_path

        if len(pack_already_installed) > 1:
            Warning(message = "This pack was already installed.", title = "INFO", icon = 'INFO')
        else :
            Warning(message = "Pack Installed ! Take a look in the Asset Browser > BagaPie Assets.", title = "INFO", icon = 'INFO')

        prefs = bpy.context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries

        for lib in asset_libraries:
            if lib.name == "BagaPie Assets":
                add = False
                
        if bagapie_pref.debug:
            print("Asset Location : " + bagapie_pref.library_location)
        if add:
            file_path = bagapie_pref.library_location
            bpy.ops.preferences.asset_library_add(directory = file_path)
            asset_libraries[len(asset_libraries)-1].name = "BagaPie Assets"

        for lib in asset_libraries:
            if lib.name == "BagaPie Assets":
                if lib.path != bagapie_pref.library_location:
                    lib.path = bagapie_pref.library_location

        # Using shutil.move to rename the file back to .baga
        shutil.move(new_file_path, filename + '.baga')

        return {'FINISHED'}

###################################################################################
# SET CUSTOM ASSETS LOCATION
###################################################################################
class BAGAPIE_OT_set_package_location(Operator, ImportHelper):
    """Set BagaPie Package Location"""
    bl_idname = 'bagapie.setpacklocation'
    bl_label = 'New Location'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pref = Get_addon_pref()
        location_original = pref.library_location

        location_new = os.path.dirname(self.filepath) + os.sep
        if location_new[-1] != os.sep:
            location_new = location_new + os.sep
        pref.library_location = location_new

        for lib in baga_libraries:
            try:
                shutil.move(location_original + lib, location_new + lib)
            except:
                pass

        prefs = bpy.context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries

        assets_lib_found = False
        for lib in asset_libraries:
            if lib.name == "BagaPie Assets":
                assets_lib_found = True

        if not assets_lib_found:
            file_path = location_new
            bpy.ops.preferences.asset_library_add(directory = file_path)
            asset_libraries[len(asset_libraries)-1].name = "BagaPie Assets"
        else :
            for lib in asset_libraries:
                if lib.name == "BagaPie Assets":
                    lib.path = location_new

        return {'FINISHED'}

###################################################################################
# GEOPACK BROWSER
###################################################################################
class BAGAPIE_OT_set_geopacks_location(Operator, ImportHelper):
    """Set BagaPie Geopacks Location"""
    bl_idname = 'bagapie.set_geopacks_location'
    bl_label = 'Set Location'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):        
        # base_path = os.path.dirname(self.filepath)
        # location_new = os.path.normpath(base_path)
        location_new = os.path.dirname(self.filepath) + os.sep

        if location_new[-1] != os.sep:
            location_new = location_new + os.sep
        
        pref = Get_addon_pref()
        pref.geopack_packs_location = location_new
        pref.Initialize(context)

        bagapie_geopack_icon.import_icons()

        return {'FINISHED'}

class BAGAPIE_OT_export_geopack(Operator, ExportHelper):
    """Export a BagaPie Geopack"""
    bl_idname = 'bagapie.geopack_export'
    bl_label = 'Export Geopack'
    bl_options = {'REGISTER', 'UNDO'}

    packIdentifier: bpy.props.StringProperty(name="packIdentifier", options={'HIDDEN'})

    filter_glob: StringProperty( default='*.geopack', options={'HIDDEN'} )

    filename_ext: StringProperty( default='.geopack', options={'HIDDEN'} )
    
    def invoke(self, context, _event):
        if pref := Get_addon_pref():
            pack = pref.GetGeopack(self.packIdentifier)

        if not self.filepath:
            blend_filepath = context.blend_data.filepath
            self.filepath = os.path.join(blend_filepath , sanitize_filename(pack.name))
        elif os.path.isfile(self.filepath):
            self.filepath = os.path.join(os.path.dirname(self.filepath) , sanitize_filename(pack.name))

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        
        if pref := Get_addon_pref():
            pack = pref.GetGeopack(self.packIdentifier)

        if pack:
            # base_path = os.path.dirname(self.filepath)
            # location_new = os.path.normpath(base_path)
            location_new = os.path.dirname(self.filepath) + os.sep
            
            folder = os.path.basename(pack.path)
            path_no_ext = os.path.join(location_new , sanitize_filename(pack.name))

            zip_file = f'{path_no_ext}.geopack'
            with ZipFile(zip_file, 'w') as zip_object:
                # Adding files that need to be zipped
                for file in [ f.path for f in os.scandir(pack.path) if f.is_file() ]:
                    zip_object.write(file , os.path.join(folder,os.path.basename(file)))

                assets_path = os.path.join(pack.path,'Assets')
                if os.path.exists(assets_path):
                    for file in [ f.path for f in os.scandir(assets_path) if f.is_file() ]:
                        zip_object.write(file , os.path.join(folder,'Assets',os.path.basename(file)))

            # Check to see if the zip file is created
            if os.path.exists(zip_file):
                print("ZIP file created")
            else:
                print("ZIP file not created")

        return {'FINISHED'}
    
class BAGAPIE_OT_import_geopack(Operator, ImportHelper):
    """Import a BagaPie Geopack"""
    bl_idname = 'bagapie.geopack_import'
    bl_label = 'Import Geopack'
    bl_options = {'REGISTER', 'UNDO'}
    
    filter_glob: StringProperty( default='*.geopack', options={'HIDDEN'} ) # type: ignore

    def execute(self, context):
        
        pref = Get_addon_pref()
        destination = pref.geopack_packs_location        

        if pref.debug == True:
            print("################################################################")
            print("GeoPack Debug")
            print("Location: ", destination)
            print("Pack: ", self.filepath)
            print(" ")
            for name in os.listdir(destination):
                print(name)
            print("################################################################")

        if os.path.isfile(self.filepath):
            try:
                with ZipFile(self.filepath, 'r') as zip_object:
                    
                    list = zip_object.namelist()
                    if list:
                        tmp = os.path.split(list[0])

                    if os.path.isdir(os.path.join(destination,tmp[0])):
                        Warning("This pack already exists !")
                        return {'FINISHED'}
                    else:
                        zip_object.extractall(destination)
                        bagapie_geopack_icon.import_icons()
            except:
                Warning("Invalid geopack file")
                
        pref.ScanGeoPacks(context)
        return {'FINISHED'}

classes = [
    BAGAPIE_OT_install_package,
    BAGAPIE_OT_set_package_location,
    BAGAPIE_OT_set_geopacks_location,
    BAGAPIE_OT_export_geopack,
    BAGAPIE_OT_import_geopack,
    BAGAPIE_OT_open_lib_folder,
    BAGAPIE_OT_setup_package_location
]

