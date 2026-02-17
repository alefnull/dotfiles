# ##### BEGIN GPL LICENSE BLOCK #####
#
#  SPDX-License-Identifier: GPL-3.0-or-later
#
#  AutoCam - Intuitive camera tools, built for artists.
#  Copyright (C) 2025  Agniv Duarah  (RenderRides)  <support@renderrides.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####


"""
Blender add-on entrypoint for AutoCam: metadata, load order, and registration.

- bl_info: add-on name, author, version, min Blender, category, and license tag.
- _gather(): imports core/ops/ui modules, reloads them, aggregates their classes.
- register(): registers classes, attaches PointerProperties, and registers handlers.
- unregister(): unregisters handlers, detaches properties, and unregisters classes.

"""

import importlib
import bpy
from . import handlers
from .core import props
from .core.constants import ROOT_ID
from .core import registry as _reg


bl_info = {
    "name":        "AutoCam",
    "author":      "RenderRides",
    "version":     (2, 0, 5),
    "blender":     (4, 0, 0),
    "location":    "View3D > Sidebar > AutoCam",
    "description": (
        "Intuitive camera tools, built for artists"
    ),
    "category":    "Camera",
    "license": "SPDX:GPL-3.0-or-later",
}


def _gather():
    from .ops import record, camera_to_curve, rig, misc, bake
    from .ui import panels

    modules = (props, record, camera_to_curve, rig, misc, panels, bake)

    classlist = []
    for m in modules:
        importlib.reload(m)
        classlist.extend(m.classes)
    return classlist


_CLASSES = _gather()


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    props.attach_pointer()
    handlers.register()

    def _deferred_seed():
        try:
            _reg.seed_from_scene()
        except Exception as e:
            print("[AutoCam] seed_from_scene (deferred) failed:", e)
        return None

    bpy.app.timers.register(_deferred_seed, first_interval=0.01)


def unregister():
    handlers.unregister()
    props.detach_pointer()
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
