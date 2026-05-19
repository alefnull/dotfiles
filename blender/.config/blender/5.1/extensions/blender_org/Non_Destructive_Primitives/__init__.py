# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ***** END GPL LICENSE BLOCK *****
import bpy
from bpy.app.handlers import persistent
from .addon_preferences import ND_Primitives_Preferences
from .pie_menu import AddModifierPie
from .add_nd_primitive import Add_ND_Primitive
from .add_menu import register_add_menu, VIEW3D_MT_nd_primitive_menu, unregister_add_menu
from .utils import keymap_register
from .mesh_utils import on_edit_mode_apply_nd_primitive

addon_keymaps = []

@persistent
def register_msgbus_nd_primitive(dummy):
    bpy.msgbus.subscribe_rna(
    key=(bpy.types.Object, 'mode'),
    owner=bpy,
    args=tuple(),
    notify=on_edit_mode_apply_nd_primitive,
)

def register():
    bpy.utils.register_class(ND_Primitives_Preferences)
    bpy.utils.register_class(AddModifierPie)
    bpy.utils.register_class(Add_ND_Primitive)
    bpy.utils.register_class(VIEW3D_MT_nd_primitive_menu)
    register_msgbus_nd_primitive(None)
    bpy.app.handlers.load_post.append(register_msgbus_nd_primitive)
    wm = bpy.context.window_manager
    register_add_menu()

    if wm.keyconfigs.addon:
        global addon_keymaps
        addon_keymaps = keymap_register(wm)

def unregister():
    bpy.utils.unregister_class(ND_Primitives_Preferences)
    bpy.utils.unregister_class(Add_ND_Primitive)
    bpy.utils.unregister_class(AddModifierPie)
    bpy.utils.unregister_class(VIEW3D_MT_nd_primitive_menu)
    unregister_add_menu()

    if register_msgbus_nd_primitive in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(register_msgbus_nd_primitive)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()