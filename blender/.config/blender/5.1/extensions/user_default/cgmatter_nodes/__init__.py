# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "cgmatter_nodes",
    "author" : "CGMatter", 
    "description" : "cgmatter nodes installer",
    "blender" : (4, 0, 0),
    "version" : (1, 0, 0),
    "location" : "",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "3D View" 
}


import bpy
import bpy.utils.previews
import urllib.request
import os
import webbrowser




def string_to_int(value):
    if value.isdigit():
        return int(value)
    return 0


def string_to_icon(value):
    if value in bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.keys():
        return bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items[value].value
    return string_to_int(value)


addon_keymaps = {}
_icons = None
class SNA_AddonPreferences_C98A2(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        if not (False):
            layout = self.layout 
            split_818CC = layout.split(factor=0.30416667461395264, align=True)
            split_818CC.alert = False
            split_818CC.enabled = True
            split_818CC.active = True
            split_818CC.use_property_split = False
            split_818CC.use_property_decorate = False
            split_818CC.scale_x = 1.0
            split_818CC.scale_y = 1.0
            split_818CC.alignment = 'Expand'.upper()
            if not True: split_818CC.operator_context = "EXEC_DEFAULT"
            split_818CC.label(text='To support what I do:', icon_value=0)
            op = split_818CC.operator('sna.cgmatter_nodes_join_website_23dab', text='Join CGMatter.com (optional)', icon_value=string_to_icon('FUND'), emboss=True, depress=False)
            layout.prop(bpy.context.preferences.system, 'use_online_access', text='Allow online access', icon_value=0, emboss=True)
            col_3C31D = layout.column(heading='', align=False)
            col_3C31D.alert = False
            col_3C31D.enabled = bpy.context.preferences.system.use_online_access
            col_3C31D.active = True
            col_3C31D.use_property_split = False
            col_3C31D.use_property_decorate = False
            col_3C31D.scale_x = 1.0
            col_3C31D.scale_y = 1.0
            col_3C31D.alignment = 'Expand'.upper()
            col_3C31D.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
            col_3C31D.prop(bpy.context.scene, 'sna_cgmatter_nodes_directory', text='', icon_value=0, emboss=True)
            row_F7E7B = col_3C31D.row(heading='', align=False)
            row_F7E7B.alert = False
            row_F7E7B.enabled =  not (bpy.context.scene.sna_cgmatter_nodes_directory == '')
            row_F7E7B.active = True
            row_F7E7B.use_property_split = False
            row_F7E7B.use_property_decorate = False
            row_F7E7B.scale_x = 1.0
            row_F7E7B.scale_y = 1.0
            row_F7E7B.alignment = 'Expand'.upper()
            row_F7E7B.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
            op = row_F7E7B.operator('sna.cgmatter_nodes_install_c384b', text='Install/Update', icon_value=string_to_icon('INTERNET'), emboss=True, depress=False)


class SNA_OT_Cgmatter_Nodes_Install_C384B(bpy.types.Operator):
    bl_idname = "sna.cgmatter_nodes_install_c384b"
    bl_label = "cgmatter_nodes_install"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.sna.cgmatter_nodes_check_existing_30676('INVOKE_DEFAULT', )
        if bpy.context.scene.sna_cgmatter_nodes_exists:
            blend_path = os.path.join(bpy.context.scene.sna_cgmatter_nodes_directory,'cgmatter_nodes.blend')
            cats_path = os.path.join(bpy.context.scene.sna_cgmatter_nodes_directory,'blender_assets.cats.txt')
            url = "https://cgmatter.github.io/website/nodes/cgmatter_nodes.blend"
            urllib.request.urlretrieve(url, blend_path)
            url = "https://cgmatter.github.io/website/nodes/blender_assets.cats.txt"
            urllib.request.urlretrieve(url, cats_path)
            if bpy.context and bpy.context.screen:
                for a in bpy.context.screen.areas:
                    a.tag_redraw()
        else:
            bpy.ops.sna.cgmatter_nodes_choose_directory_1d5b8('INVOKE_DEFAULT', )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Cgmatter_Nodes_Choose_Directory_1D5B8(bpy.types.Operator):
    bl_idname = "sna.cgmatter_nodes_choose_directory_1d5b8"
    bl_label = "cgmatter_nodes_choose_directory"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.ops.preferences.asset_library_add(directory=bpy.context.scene.sna_cgmatter_nodes_directory)
        bpy.context.scene.sna_cgmatter_nodes_exists = True
        bpy.context.preferences.filepaths.asset_libraries[int(len(bpy.context.preferences.filepaths.asset_libraries) - 1.0)].name = 'cgmatter_nodes'
        if bpy.context and bpy.context.screen:
            for a in bpy.context.screen.areas:
                a.tag_redraw()
        blend_path = os.path.join(bpy.context.scene.sna_cgmatter_nodes_directory,'cgmatter_nodes.blend')
        cats_path = os.path.join(bpy.context.scene.sna_cgmatter_nodes_directory,'blender_assets.cats.txt')
        url = "https://cgmatter.github.io/website/nodes/cgmatter_nodes.blend"
        urllib.request.urlretrieve(url, blend_path)
        url = "https://cgmatter.github.io/website/nodes/blender_assets.cats.txt"
        urllib.request.urlretrieve(url, cats_path)
        if bpy.context and bpy.context.screen:
            for a in bpy.context.screen.areas:
                a.tag_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Cgmatter_Nodes_Check_Existing_30676(bpy.types.Operator):
    bl_idname = "sna.cgmatter_nodes_check_existing_30676"
    bl_label = "cgmatter_nodes_check_existing"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.sna_cgmatter_nodes_exists = False
        for i_68377 in range(len(bpy.context.preferences.filepaths.asset_libraries)):
            if (bpy.context.preferences.filepaths.asset_libraries[i_68377].name == 'cgmatter_nodes'):
                bpy.context.scene.sna_cgmatter_nodes_directory = bpy.context.preferences.filepaths.asset_libraries[i_68377].path
                bpy.context.scene.sna_cgmatter_nodes_exists = True
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Cgmatter_Nodes_Join_Website_23Dab(bpy.types.Operator):
    bl_idname = "sna.cgmatter_nodes_join_website_23dab"
    bl_label = "cgmatter_nodes_join_website"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        webbrowser.open("https://www.cgmatter.com/catalog")
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


def register():
    global _icons
    _icons = bpy.utils.previews.new()
    bpy.types.Scene.sna_cgmatter_nodes_directory = bpy.props.StringProperty(name='cgmatter_nodes_directory', description='', default='', subtype='DIR_PATH', maxlen=0)
    bpy.types.Scene.sna_cgmatter_nodes_exists = bpy.props.BoolProperty(name='cgmatter_nodes_exists', description='', default=False)
    bpy.utils.register_class(SNA_AddonPreferences_C98A2)
    bpy.utils.register_class(SNA_OT_Cgmatter_Nodes_Install_C384B)
    bpy.utils.register_class(SNA_OT_Cgmatter_Nodes_Choose_Directory_1D5B8)
    bpy.utils.register_class(SNA_OT_Cgmatter_Nodes_Check_Existing_30676)
    bpy.utils.register_class(SNA_OT_Cgmatter_Nodes_Join_Website_23Dab)


def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    del bpy.types.Scene.sna_cgmatter_nodes_exists
    del bpy.types.Scene.sna_cgmatter_nodes_directory
    bpy.utils.unregister_class(SNA_AddonPreferences_C98A2)
    bpy.utils.unregister_class(SNA_OT_Cgmatter_Nodes_Install_C384B)
    bpy.utils.unregister_class(SNA_OT_Cgmatter_Nodes_Choose_Directory_1D5B8)
    bpy.utils.unregister_class(SNA_OT_Cgmatter_Nodes_Check_Existing_30676)
    bpy.utils.unregister_class(SNA_OT_Cgmatter_Nodes_Join_Website_23Dab)
