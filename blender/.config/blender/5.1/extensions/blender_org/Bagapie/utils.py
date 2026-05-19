import re
import unicodedata
import bpy
import os
import inspect

def isEqualZero( val, decimal_points = 5 ):
    ''' Returns True if val equale to zero when
        rounded by the provided number of decimal_points
    '''
    return round(val, decimal_points) == 0


def sanitize_filename_old(input_string):
    # Replace accentuated letters with non-accentuated letters
    normalized_string = unicodedata.normalize('NFKD', input_string).encode('ASCII', 'ignore').decode('utf-8')
    # Keep only alphanumeric characters, hyphens and underscores
    return re.sub(r'[^a-zA-Z0-9-_]', '', normalized_string)


def sanitize_filename(input_string):
    import unicodedata
    import re
    # Replace accentuated letters with non-accentuated letters
    normalized_string = unicodedata.normalize('NFKD', input_string).encode('ASCII', 'ignore').decode('utf-8')
    # Replace spaces with underscores
    normalized_string = re.sub(r'\s+', '_', normalized_string)
    # Keep only alphanumeric characters, hyphens and underscores, and ensure there are no multiple consecutive underscores
    return re.sub(r'[^a-zA-Z0-9_-]|_{2,}', '_', normalized_string)


def is_in_local_view():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D' and space.local_view is not None:
                    return True
    return False


def get_or_create_collection(name, parent_collection=None):
    new_collection = None

    # Si une collection parente est fournie, chercher dans ses enfants
    if parent_collection:
        for coll in parent_collection.children:
            if coll.name.startswith(name):
                new_collection = coll
                break
    else:  # Sinon, chercher dans la scène actuelle
        for coll in bpy.context.scene.collection.children:
            if coll.name.startswith(name):
                new_collection = coll
                break

    # Si aucune collection existante n'a été trouvée, en créer une nouvelle
    if new_collection is None:
        new_collection = bpy.data.collections.new(name)
        if parent_collection:
            parent_collection.children.link(new_collection)
        else:
            bpy.context.scene.collection.children.link(new_collection)

    return new_collection


def Warning(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


def Get_addon_pref():
    addon_pref=bpy.context.preferences.addons[__package__].preferences
    return addon_pref


def Import_Nodes(self, context, nodes_name, blend_file="BagaPie_Nodes.blend"):
    file_dir = os.path.dirname(__file__)
    file_path = os.path.join(file_dir, blend_file)
    inner_path = "NodeTree"

    # Check if the file path exists
    if not os.path.exists(file_path):
        Warning(message=f"File path not found: {file_path}", title="File Path Error", icon='ERROR')
        return {'FINISHED'}

    bpy.ops.wm.append(
        filepath=os.path.join(file_path, inner_path, nodes_name),
        directory=os.path.join(file_path, inner_path),
        filename=nodes_name
        )
    
    return {'FINISHED'}


def Add_NodeGroup(self,context,modifier, nodegroup_name):
    try:
        modifier.node_group = bpy.data.node_groups[nodegroup_name]
    except:
        Import_Nodes(self,context,nodegroup_name)
        modifier.node_group = bpy.data.node_groups[nodegroup_name]


def debug(txt="Error Unknown"):
    bagapie_pref = Get_addon_pref()
    if bagapie_pref.debug == True:
        print(txt)