"""
Danger Zone utility: remove every AutoCam rig and clean state.

- Deletes all objects that belong to any AutoCam rig (by pointer to curve).
- Removes all AutoCam master collections (and their children) even if renamed.
- Unhides remaining non-rig cameras and sets Scene.camera to the first one.
- Clears the in-session rig registry.

"""


import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from ..core.registry import clear_all as _reg_clear


class AUTOCAM_OT_clear_all_rigs(Operator):
    """Remove ALL AutoCam rigs and their collections from the scene. Restores original cameras. Can be undone with Ctrl+Z."""
    bl_idname = "autocam.clear_all_rigs"
    bl_label = "Clear All Rigs?"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):

        for obj in list(bpy.data.objects):
            if getattr(obj, "autocam", None) and obj.autocam.curve:
                bpy.data.objects.remove(obj, do_unlink=True)

        masters = [c for c in bpy.data.collections if c.get("ac_master")]

        for master in masters:

            for child in list(master.children):
                bpy.data.collections.remove(child, do_unlink=True)

            bpy.data.collections.remove(master, do_unlink=True)

        cams = [
            o for o in bpy.data.objects
            if o.type == 'CAMERA' and (not getattr(o, "autocam", None) or not o.autocam.curve)
        ]
        if cams:
            for c in cams:
                c.hide_viewport = False
                c.hide_render = False
            context.scene.camera = cams[0]

        _reg_clear()

        self.report({'INFO'}, "All AutoCam rigs removed")
        return {'FINISHED'}


class AUTOCAM_OT_set_active_camera(Operator):
    """Set the active scene camera to the specified camera by name"""
    bl_idname = "autocam.set_active_camera"
    bl_label = "Set Active Camera"
    bl_options = {'UNDO'}

    camera_name: StringProperty(name="Camera Name")

    def execute(self, context):
        cam = bpy.data.objects.get(self.camera_name)
        if not cam or cam.type != 'CAMERA':
            self.report({'ERROR'}, "Camera not found or not a camera.")
            return {'CANCELLED'}

        context.scene.camera = cam
        # (Optional) also set active object if accessible
        try:
            context.view_layer.objects.active = cam
        except Exception:
            pass

        self.report({'INFO'}, f"Active camera set to {cam.name}")
        return {'FINISHED'}


classes = (AUTOCAM_OT_clear_all_rigs, AUTOCAM_OT_set_active_camera)
