import importlib
from pathlib import Path

import bpy
from bpy.types import NodeSocket
from mathutils import Vector as V

files = list(Path(__file__).parent.glob("socket_location*.py"))
files.sort(key=lambda f: f.name)
bpy_version = tuple(bpy.app.version[:2])

current_file = files[0]
for file in files:
    version = [int(v) for v in file.name.split(".")[0].split("_")[2:]]
    version = tuple(version)
    if version > bpy_version:
        break
    current_file = file

module = importlib.import_module("." + current_file.stem, __package__)


def get_socket_location(socket: NodeSocket) -> V:
    return module.get_socket_location_ctypes(socket)
