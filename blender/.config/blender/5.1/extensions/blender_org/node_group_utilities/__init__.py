bl_info = {
    "name": "Node Group Utilities",
    "author": "Boreo",
    "version": (2, 1, 1),
    "blender": (3, 0, 0),
    "location": "Node Groups Context Menu",
    "description": "Extra options and functions for node groups",
    "doc_url": "https://blendermarket.com/products/node-group-utilities/docs",
    "category": "Nodes",
}

import bpy
from . import saveload4
from . import saveload3
from . import socketmaker

def register():
    socketmaker.register()
    if bpy.app.version >= (4, 0, 0): saveload4.register()  
    else: saveload3.register()  

def unregister():
    socketmaker.unregister()
    if bpy.app.version >= (4, 0, 0): saveload4.unregister()  
    else: saveload3.unregister()  
    