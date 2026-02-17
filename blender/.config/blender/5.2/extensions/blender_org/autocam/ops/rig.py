"""
Build the AutoCam follow-path rig around a generated curve.

- Allocates a unique rig collection & names; re-homes the path curve under it.
- Creates rig objects:
    Dolly (path follower) - Empty (Sphere).
    Aim (camera parent) - Empty (Arrow), parented to Dolly.
    LookAt - Empty placed at a ray-cast hit ahead of the original camera (or fallback).
    FocusPoint - Empty parented to LookAt, used for camera DOF.
    Camera - copy of the original camera, parented to Aim, 180 deg flip for correct view.
- Sets a TRACK_TO on Aim -> LookAt; enables DOF and binds to FocusPoint.
- Hides the original camera; sets the scene camera to the rig camera.
- Cleans any speed fcurves on the path, marks rig as built, registers with the
  session registry, applies default rig mode from preferences, and builds arc tables.

  """


import bpy
import re
import math
from mathutils import Vector
from ..handlers import _build_arc_table
from ..core.utils import tag_autocam, find_ac_curve
from ..core.constants import MASTER_COLL
from ..core.props import prefs
from ..core.registry import add as _reg_add
from ..core.registry import stamp_rig
from ..core.fcurves import action_fcurves
from ..core.timing import _apply_inherited_timing, _has_location_animation


_RIG_PREFIX = "AutoCam_Rig"


# helper

def _next_rig_index() -> int:
    """Scan collections named AutoCam_RigNN and return max(NN)+1 (NN is 2 digits)."""
    pat = re.compile(rf"^{_RIG_PREFIX}(\d+)$")
    mx = 0
    for c in bpy.data.collections:
        m = pat.match(c.name)
        if m:
            try:
                mx = max(mx, int(m.group(1)))
            except ValueError:
                pass
    return mx + 1


def _alloc_autocam_rig_names():
    """
    Allocate a unique rig base and all child names.
    Ensures no collisions with existing collections/objects.
    """
    i = _next_rig_index()
    while True:
        base = f"{_RIG_PREFIX}{i:02d}"
        names = {
            "index":  i,
            "coll":   base,
            "path":   f"{base}_Path",
            "dolly":  f"{base}_Dolly",
            "aim":    f"{base}_Aim",
            "lookat": f"{base}_LookAt",
            "focus":  f"{base}_FocusPoint",
            "camera": f"{base}_Camera",
        }

        if (base in bpy.data.collections or
                any(n in bpy.data.objects for n in names.values() if isinstance(n, str))):
            i += 1
            continue
        return base, names


class AUTOCAM_OT_build_camera_rig(bpy.types.Operator):
    """Build the camera rig to follow the adaptive curve"""
    bl_idname = "autocam.build_camera_rig"
    bl_label = "Build Camera Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        curve = find_ac_curve(context.object)
        return bool(curve and not curve.autocam.rig_built)

    def execute(self, context):
        sc = context.scene
        curve = find_ac_curve(context.object)
        if not curve:
            self.report({'ERROR'}, "Select the generated curve first")
            return {'CANCELLED'}

        frame_start = int(curve.get("autocam.frame_start",
                          context.scene.frame_start))
        frame_end = int(curve.get("autocam.frame_end",
                        context.scene.frame_end))

        orig = curve.autocam.camera
        if not orig or orig.name not in bpy.data.objects:
            self.report(
                {'ERROR'}, "Original camera is missing or has been renamed or deleted")
            return {'CANCELLED'}

        rig_base, N = _alloc_autocam_rig_names()

        cam = orig.copy()
        cam.data = orig.data.copy()
        cam.name = N["camera"]

        cam.animation_data_clear()
        cam.data.animation_data_clear()

        master = bpy.data.collections.get(
            MASTER_COLL) or bpy.data.collections.new(MASTER_COLL)
        if master.name not in sc.collection.children:
            sc.collection.children.link(master)

        master["ac_master"] = True

        rig_col = bpy.data.collections.new(N["coll"])
        master.children.link(rig_col)

        curve.name = N["path"]

        for col in list(curve.users_collection):
            col.objects.unlink(curve)
        rig_col.objects.link(curve)
        tag_autocam(curve, curve)

        dolly = bpy.data.objects.new(N["dolly"], None)
        rig_col.objects.link(dolly)
        tag_autocam(dolly, curve)
        dolly.empty_display_type = 'SPHERE'
        dolly.empty_display_size = 0.25
        curve.autocam.dolly = dolly

        aim = bpy.data.objects.new(N["aim"], None)
        rig_col.objects.link(aim)
        tag_autocam(aim, curve)
        aim.empty_display_type = 'SINGLE_ARROW'
        aim.empty_display_size = 3.0
        aim.rotation_euler = (0, -math.pi/2, 0)
        aim.parent = dolly
        aim.matrix_parent_inverse = dolly.matrix_world.inverted()

        cam.matrix_world = dolly.matrix_world.copy()
        rig_col.objects.link(cam)
        tag_autocam(cam, curve)
        curve.autocam.rigcam = cam
        cam.parent = aim
        cam.matrix_parent_inverse = aim.matrix_world.inverted()
        if cam.rotation_mode.startswith('QUAT'):
            cam.rotation_mode = 'XYZ'
        cam.delta_rotation_euler = (0.0, math.pi, 0.0)

        orig.hide_viewport = orig.hide_render = True
        sc.camera = cam

        mid = (frame_start + frame_end) // 2
        sc.frame_set(mid)
        ori = orig.matrix_world.to_translation()
        fwd = orig.matrix_world.to_quaternion() @ Vector((0, 0, -1))

        if bpy.app.version >= (2, 90, 0):
            deps = context.evaluated_depsgraph_get()
            hit, loc, normal, face_idx, obj, mat = sc.ray_cast(
                deps, ori + fwd*0.01, fwd)
        else:
            view_layer = context.view_layer
            hit, loc, normal, face_idx, obj, mat = sc.ray_cast(
                view_layer, ori + fwd*0.01, fwd)

        lp = loc if hit else ori + fwd * 10

        look = bpy.data.objects.new(N["lookat"], None)
        rig_col.objects.link(look)
        tag_autocam(look, curve)
        look.empty_display_type = 'SPHERE'
        look.empty_display_size = 0.75
        look.location = lp

        focus = bpy.data.objects.new(N["focus"], None)
        rig_col.objects.link(focus)
        tag_autocam(focus, curve)
        focus.empty_display_type = 'PLAIN_AXES'
        focus.parent = look

        tt = aim.constraints.new('TRACK_TO')
        tt.target = look
        tt.track_axis = 'TRACK_Z'
        tt.up_axis = 'UP_Y'

        cam.data.dof.use_dof = True
        cam.data.dof.focus_object = focus

        if curve.animation_data and curve.animation_data.action:
            action = curve.animation_data.action
            fcurves = action_fcurves(action, owner=curve)
            for fcu in list(fcurves):
                if 'autocam.speed' in fcu.data_path or 'autocam.simple_speed' in fcu.data_path:
                    fcurves.remove(fcu)

        stamp_rig(
            curve,
            dolly,
            rigcam=cam,
            look=look,
            focus=focus,
            coll=rig_col,
            version_str="2.0.1"
        )

        curve.autocam.rig_built = True

        _reg_add(curve)

        curve.autocam.rig_name = rig_base
        curve.autocam.rig_index = N["index"]

        if prefs():
            curve.autocam.mode = prefs().default_rig_mode
            curve.autocam.speed = prefs().default_speed
            curve.autocam.simple_speed = prefs().default_speed
            curve.autocam.recrot_simplify = prefs().default_recrot_simplify
            curve.autocam.recrot_smoothing = prefs().default_recrot_smoothing

            _build_arc_table(curve)
            curve["_ac_speed_units"] = "DIST_PER_SEC"
            context.scene.frame_set(frame_start)
            try:
                bpy.context.view_layer.update()   # ensure depsgraph caught up
            except Exception:
                pass

            curve.autocam.lookat_mode = prefs().default_tracking

        return {'FINISHED'}


classes = (AUTOCAM_OT_build_camera_rig,)
