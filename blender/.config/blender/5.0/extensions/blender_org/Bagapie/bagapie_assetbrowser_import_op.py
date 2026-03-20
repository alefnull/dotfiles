import bpy
import os
from bpy.types import Operator
import ntpath
import time
from pathlib import Path
from .utils import Warning


class BAGAPIE_OT_assetbrowser(Operator):
    """ import and use assets based on the asset browser """
    bl_idname = "bagapie.asset_browser"
    bl_label = 'import asset browser'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object
        area = find_areas('ASSETS')
        if o is not None and o.type == 'MESH'and area is not None:
            win = find_window('ASSETS')
            if area.ui_type == 'ASSETS':
                with context.temp_override(window=win, area = area):
                    return context.selected_assets

    import_mode: bpy.props.StringProperty(
            name = 'import',
            default = ''
            ) # type: ignore
    paint_mode: bpy.props.BoolProperty(default=False) # type: ignore

    def execute(self, context):
        
        context.scene["BP_Atypes"] = self.import_mode
        area = find_areas('ASSETS')
        win = find_window('ASSETS')

        current_library_name = area.spaces.active.params.asset_library_reference
        if current_library_name == "LOCAL":
            library_path = Path(bpy.data.filepath)
        else:
            try:
                library_path = Path(context.preferences.filepaths.asset_libraries.get(current_library_name).path) 
            except:
                Warning(message = "The library 'All' isn't valid. Go to the library that contains the assets to select them.", title = "Asset Browser : Library not supported", icon = 'INFO')
                return {'FINISHED'}
        
        if bpy.data.collections.get("BagaPie") is None:
            main_coll = bpy.data.collections.new("BagaPie")
            bpy.context.scene.collection.children.link(main_coll)
            if bpy.data.collections.get("BagaPie_Assets") is None:
                asset_coll = bpy.data.collections.new("BagaPie_Assets")
                main_coll.children.link(asset_coll)
            else:
                asset_coll = bpy.data.collections["BagaPie_Assets"]
        else:
            main_coll = bpy.data.collections["BagaPie"]
            if bpy.data.collections.get("BagaPie_Assets") is None:
                asset_coll = bpy.data.collections.new("BagaPie_Assets")
                main_coll.children.link(asset_coll)
            else:
                asset_coll = bpy.data.collections["BagaPie_Assets"]

        original_target = bpy.context.active_object
        psi_pass = False
        current_window = bpy.context.window
        current_region = bpy.context.region
        current_area = None
        for cr_area in current_window.screen.areas:
            if cr_area.type == 'VIEW_3D':
                current_area = cr_area
                break
        
        for o in context.selected_objects:
            if o != original_target:
                o.select_set(False)

        with context.temp_override(window=win, area = area):
            print("Imported Assets :")
            assets_imported = []
            for asset_file in context.selected_assets:
                asset_fullpath = library_path / asset_file.full_path
                if current_library_name == "LOCAL":
                    asset_fullpath /= asset_file.local_id.name

                asset_filepath = asset_fullpath.parent.parent
                inner_path = ntpath.basename(ntpath.dirname(asset_fullpath))
                asset_name = ntpath.basename(asset_fullpath)
                print('"'+asset_name+'"' + " from type : " + inner_path)
                time.sleep(1)
                try:
                    bpy.data.objects[asset_name].select_set(True)
                    objs = bpy.context.selected_objects
                    for a in objs:
                        assets_imported.append(a)

                except:
                    if inner_path == 'Collection':
                        psi_pass = True
                    if inner_path == 'Collection' or inner_path == 'Object':
                        bpy.ops.wm.append(
                            filepath=os.path.join(asset_filepath, inner_path, asset_name),
                            directory=os.path.join(asset_filepath, inner_path),
                            filename=asset_name
                            )
                        objs = bpy.context.selected_objects
                        for a in objs:
                            for col in a.users_collection:
                                col.objects.unlink(a)
                            asset_coll.objects.link(a)
                            assets_imported.append(a)
                            
                        if inner_path == 'Collection':
                            bpy.data.collections.remove(bpy.data.collections[asset_name])
                    else:
                        print('"'+asset_name+'"' + " isn't a Collection or Object")

            for ob in assets_imported:
                ob.select_set(True)
                if self.import_mode == 'DrawArray' or 'PointSnapInstance':
                    bpy.context.view_layer.objects.active = ob
            
            if self.import_mode != 'DrawArray' or 'PointSnapInstance':
                target = bpy.context.active_object
                target.select_set(True)
            
            if self.import_mode == 'AddAssets':
                bpy.context.view_layer.objects.active = original_target
                original_target.select_set(True)
                bpy.ops.add.asset('INVOKE_DEFAULT')
            
            elif self.import_mode == 'DrawArray':
                with context.temp_override(window=current_window, area = current_area, region = current_region):
                    bpy.ops.bagapie.drawarray('INVOKE_DEFAULT')
            
            elif self.import_mode == 'PointSnapInstance':
                if not psi_pass:
                    with context.temp_override(window=current_window, area = current_area, region = current_region):
                        for ob in assets_imported:
                            ob.select_set(True)
                        bpy.context.view_layer.objects.active = original_target
                        original_target.select_set(True)
                        bpy.ops.bagapie.pointsnapinstance('INVOKE_DEFAULT')
                else:
                    Warning(message = "This asset is a collection ! Import it then select assets manually.", title = "Exception", icon = 'INFO')

            else:
                bpy.context.view_layer.objects.active = original_target
                original_target.select_set(True)
                if self.import_mode.startswith('ScatterPaint'):
                    self.paint_mode = True
                else:
                    self.paint_mode = False
                bpy.ops.wm.scatter('INVOKE_DEFAULT', paint_mode = self.paint_mode)

            bpy.context.scene["BP_Atypes"] = ""

        return {'FINISHED'}


###################################################################################
# FIND AREAS
###################################################################################
def find_areas(type):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.ui_type == type:
                with bpy.context.temp_override(window=window, area = area):
                    if bpy.context.selected_assets: # CHECK IF SOMETHING IS SELECTED
                        return area
    return None

###################################################################################
# FIND WINDOWS
###################################################################################
def find_window(type):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.ui_type == type:
                with bpy.context.temp_override(window=window, area = area):
                    if bpy.context.selected_assets: # CHECK IF SOMETHING IS SELECTED
                        return window
    return None

classes = [
    BAGAPIE_OT_assetbrowser,
]