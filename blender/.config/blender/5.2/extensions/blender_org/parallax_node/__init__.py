# This file is part of parallax Nodes blender add-on.
#
# Copyright (C) 2024 crantisz@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Some code in this file is adapted from or inspired by the Noise Nodes add-on:
# https://github.com/haseebahmed295/Noise-Nodes
#
import bpy
import bl_ui
from .node_imp import NodeLib
from .na import ng_register , ng_unregister

bl_info = {
    "name": "Parallax Nodes",
    "description": "Parallax nodes for blender",
    "author": "crantisz@gmail.com",
    "version": (1, 1, 1),
    "blender": (5, 0, 0),
    "location": "Shader Node Editor > Add Menu",
    "doc_url": "",
    "tracker_url": "",
    "category": "Node",
}

class NODE_MT_category_parallax(bpy.types.Menu):
    bl_idname = "NODE_MT_category_paralax"
    bl_label = "Parallax Nodes"
    bl_description = "Nodes for parallax mapping"

    @classmethod
    def poll(cls, context):
        """Only show menu in supported node editors"""
        return context.space_data.tree_type in {"ShaderNodeTree"}

    def draw(self, context):
        layout = self.layout
        shader_nodes = NodeLib.get_node_sets()

        if not shader_nodes:
            layout.label(text="No nodes available", icon="ERROR")
            return

        # Draw nodes with separators for better organization
        for node_class in sorted(shader_nodes, key=lambda x: x.bl_label):
            props = layout.operator(
                "node.add_node",
                text=node_class.bl_label,
            )
            props.type = node_class.__name__
            props.use_transform = True

        # Draw asset catalog integration
        # bl_ui.node_add_menu.draw_assets_for_catalog(layout, self.bl_label)


def menu_draw(self, context):
    """Draw menu entry if conditions are met"""
    if NODE_MT_category_parallax.poll(context):
        self.layout.menu(NODE_MT_category_parallax.bl_idname)


def register():

        # Register icons and classes
        bpy.utils.register_class(NODE_MT_category_parallax)

        # Add to menus
        bpy.types.NODE_MT_shader_node_add_all.append(menu_draw)

        # Register node classes
        shader_nodes = NodeLib.get_node_sets()
        for cls in  shader_nodes:
            bpy.utils.register_class(cls)


def unregister():
        try:
            ng_unregister()
        except Exception as e:
            print(f"Unregistration failed: {e}")
        # Remove from menus
        bpy.types.NODE_MT_shader_node_add_all.remove(menu_draw)

        # Unregister classes
        bpy.utils.unregister_class(NODE_MT_category_parallax)

        # Unregister nodes
        shader_nodes = NodeLib.get_node_sets()
        for cls in shader_nodes:
            bpy.utils.unregister_class(cls)


    

if __name__ == "__main__":
    register()
