# SPDX-License-Identifier: GPL-3.0-or-later

if "bpy" in locals():
    import importlib

    importlib.reload(node_tree_screenshot)
else:
    from . import node_tree_screenshot

import bpy

def register():
    node_tree_screenshot.register()

def unregister():
    node_tree_screenshot.unregister()

if __name__ == '__main__':
    register()
