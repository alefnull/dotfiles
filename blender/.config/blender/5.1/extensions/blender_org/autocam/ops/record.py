"""
Walk/fly POV recorder: capture a flythrough as keyframes on the active camera.

- Switches to WALK navigation and continuous mouse, enables auto keyframing, and starts timeline playback in Camera view.
- Modal loop stores camera matrix per frame while playback runs.
- On "Esc", "Right Click", or "Left Click": stops playback, writes location/rotation_euler keys for all recorded frames, restores user preferences, and removes the timeline extender.

"""


import bpy
from ..core.utils import _extend_timeline, _insert_key


# Flythrough Recording

class AUTOCAM_OT_fly_record(bpy.types.Operator):
    """Capture a Walk-navigation fly-through from the active camera"""
    bl_idname = "autocam.fly_record"
    bl_label = "Start Recording"
    bl_description = "Capture a flythrough from the active camera's POV"
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}

    def invoke(self, context, event):
        cam = context.scene.camera

        if cam is None:
            def draw(self, _ctx):
                self.layout.label(text="No active camera!", icon='ERROR')
            context.window_manager.popup_menu(
                draw, title="Cannot Record", icon='ERROR')
            return {'CANCELLED'}

        # Always confirm to ensure consistent initialization (fixes cursor limit on first run)
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        sc = context.scene
        cam = sc.camera

        if cam.animation_data:
            cam.animation_data_clear()

        prefs_in = context.preferences.inputs
        prefs_edit = context.preferences.edit
        self._old_continuous = prefs_in.use_mouse_continuous
        self._old_nav_mode = prefs_in.navigation_mode
        self._old_only = prefs_edit.use_keyframe_insert_available

        prefs_in.use_mouse_continuous = True
        prefs_in.navigation_mode = 'WALK'
        prefs_edit.use_keyframe_insert_available = False

        sc.tool_settings.use_keyframe_insert_auto = True
        if _extend_timeline not in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.append(_extend_timeline)

        bpy.ops.screen.animation_play()

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.region_3d.view_perspective = 'CAMERA'
                region = next(r for r in area.regions if r.type == 'WINDOW')
                override = {'area': area,
                            'region': region, 'space_data': space}
                if hasattr(context, "temp_override"):
                    with context.temp_override(**override):
                        bpy.ops.view3d.walk('INVOKE_DEFAULT')
                else:
                    bpy.ops.view3d.walk(override, 'INVOKE_DEFAULT')
                break

        self._recorded = {}

        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "Recording... press Esc, Right Click, or Left Click to finish.")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        sc = context.scene
        cam = sc.camera

        if (event.type == 'ESC' and event.value == 'PRESS') or \
           (event.type == 'RIGHTMOUSE' and event.value == 'PRESS') or \
           (event.type == 'LEFTMOUSE' and event.value == 'PRESS'):

            if context.screen.is_animation_playing:
                bpy.ops.screen.animation_play()

            for f, mat in self._recorded.items():
                cam.matrix_world = mat
                _insert_key(cam, "location",       f)
                _insert_key(cam, "rotation_euler", f)

            sc.tool_settings.use_keyframe_insert_auto = False
            if _extend_timeline in bpy.app.handlers.frame_change_post:
                bpy.app.handlers.frame_change_post.remove(_extend_timeline)

            prefs_in = context.preferences.inputs
            prefs_edit = context.preferences.edit
            prefs_in.use_mouse_continuous = self._old_continuous
            prefs_in.navigation_mode = self._old_nav_mode
            prefs_edit.use_keyframe_insert_available = self._old_only

            self.report({'INFO'}, "Recording stopped; keyframes saved.")
            return {'FINISHED', 'PASS_THROUGH'}

        if context.screen.is_animation_playing:
            f = sc.frame_current
            if f not in self._recorded:
                self._recorded[f] = cam.matrix_world.copy()

        return {'PASS_THROUGH'}


classes = (AUTOCAM_OT_fly_record,)
