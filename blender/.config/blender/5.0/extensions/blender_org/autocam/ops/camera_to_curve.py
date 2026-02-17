"""
Convert a camera's animation into an adaptive path curve, with edit/apply/reset.

- AUTOCAM_OT_camera_to_curve: samples camera transforms over a chosen frame range, builds a curve (Poly/Bezier/NURBS), stores raw/base samples on the curve, and seeds AutoCam properties (spline, tol, speed, frame range, tags).
- AUTOCAM_OT_apply_curve: applies tolerance-based simplification (RDP) to current samples (and to edit-mode geometry if present), rebuilds the curve geometry, and refreshes arc-length tables for Dynamic mode traversal.
- AUTOCAM_OT_revert_curve: restores the original sampled path and refreshes arc tables.

"""


import bpy
import json
from bpy.props import EnumProperty, IntProperty, FloatProperty
from mathutils import Vector
from ..core.geometry import rdp
from ..core.curve_builders import BUILDERS
from ..core.utils import find_ac_curve, tag_autocam
from ..handlers import _build_arc_table
from ..core.props import prefs
from ..core.fcurves import action_fcurves


# Operators

class AUTOCAM_OT_camera_to_curve(bpy.types.Operator):
    """Convert selected camera animation into an adaptive curve"""
    bl_idname = "autocam.camera_to_curve"
    bl_label = "Camera -> Adaptive Curve"
    bl_options = {'REGISTER', 'UNDO'}

    frame_mode: EnumProperty(
        name="Range",
        items=[('ANIM', 'Animated', ''), ('CUSTOM', 'Custom', '')],
        default='ANIM')  # type: ignore
    frame_start: IntProperty(default=1, min=1)  # type: ignore
    frame_end: IntProperty(default=250, min=1)  # type: ignore
    frame_step: IntProperty(default=1, min=1)  # type: ignore
    tolerance: FloatProperty(
        name="Tolerance", default=0.05, min=0.0, max=1.0)  # type: ignore
    spline_type: EnumProperty(
        name="Spline",
        items=[('POLY', 'Poly', ''), ('BEZIER', 'Bezier', ''),
               ('NURBS', 'NURBS', '')],
        default='BEZIER')  # type: ignore

    @classmethod
    def poll(cls, context):
        cam = context.object
        return cam and cam.type == 'CAMERA' and "autocam_curve" not in cam.keys()

    def invoke(self, context, event):
        p = prefs()
        if not p:
            self.report({'ERROR'}, "AutoCam preferences not available")
            return {'CANCELLED'}

        self.spline_type = p.default_spline
        self.tolerance = p.default_tol

        cam = context.object
        if not cam or cam.type != 'CAMERA':
            self.report({'ERROR'}, "Select a Camera first")
            return {'CANCELLED'}
        return self.execute(context)

    def execute(self, context):
        cam = context.object
        if self.frame_mode == 'ANIM':
            ad = cam.animation_data
            act = ad.action if (ad and ad.action) else None
            
            # Try to find range from Action
            start, end = None, None
            if act:
                fcurves = action_fcurves(act, owner=cam)
                # We don't strictly require location fcurves anymore, 
                # but if they exist, we use them to determine range.
                ks = []
                for fc in fcurves:
                    if 'location' in (fc.data_path or ""):
                        ks.extend(kp.co.x for kp in fc.keyframe_points)
                
                if ks:
                    start, end = int(min(ks)), int(max(ks))
            
            # Fallback: if no location keys (e.g. constraint driven), use scene range
            if start is None:
                start, end = context.scene.frame_start, context.scene.frame_end

        else:
            start, end = self.frame_start, self.frame_end
            if end <= start:
                self.report({'ERROR'}, "End must exceed start")
                return {'CANCELLED'}

        pts = []
        sc = context.scene
        orig_f = sc.frame_current
        for f in range(start, end+1, self.frame_step):
            sc.frame_set(f)
            pts.append(cam.matrix_world.to_translation().copy())
        sc.frame_set(orig_f)

        if len(pts) < 3:
            self.report({'ERROR'}, "Need >= 3 samples")
            return {'CANCELLED'}

        curve = BUILDERS[self.spline_type](None, pts)
        raw = json.dumps([tuple(v) for v in pts])
        curve['autocam_samples_orig'] = raw
        curve['autocam_samples_base'] = raw
        curve["autocam.frame_start"] = start
        curve["autocam.frame_end"] = end
        curve.autocam.camera = cam
        curve.autocam.spline = self.spline_type
        curve.autocam.tol = self.tolerance
        curve.autocam.speed = 1.0
        curve.autocam.simple_speed = 1.0
        curve["autocam_path"] = True
        curve.autocam.curve = curve
        curve.autocam.rig_built = False
        tag_autocam(curve, curve)

        if cam.animation_data and cam.animation_data.action:
            f_start, f_end = cam.animation_data.action.frame_range
        else:
            f_start, f_end = context.scene.frame_start, context.scene.frame_end

        context.view_layer.objects.active = curve
        curve.select_set(True)

        try:
            bpy.ops.autocam.apply_curve('EXEC_DEFAULT')
        except Exception as e:
            self.report({'WARNING'}, f"Auto-apply path settings failed: {e}")

        return {'FINISHED'}


class AUTOCAM_OT_apply_curve(bpy.types.Operator):
    """Apply tolerance/changes made in Edit Mode."""
    bl_idname = "autocam.apply_curve"
    bl_label = "Apply Path Settings"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        curve = find_ac_curve(context.object)
        return bool(curve and 'autocam_samples_base' in curve)

    def execute(self, context):
        curve = find_ac_curve(context.object)
        if context.mode == 'EDIT_CURVE':
            pts = []
            for sp in curve.data.splines:
                if sp.type in {'POLY', 'NURBS'}:
                    pts += [curve.matrix_world @
                            Vector(p.co[:3]) for p in sp.points]
                else:
                    pts += [curve.matrix_world @
                            bp.co for bp in sp.bezier_points]
            curve['autocam_samples_base'] = json.dumps([tuple(v) for v in pts])
            bpy.ops.object.mode_set(mode='OBJECT')

        base_pts = [Vector(p)
                    for p in json.loads(curve['autocam_samples_base'])]
        simp = rdp(base_pts, curve.autocam.tol**2)
        curve['autocam_samples'] = json.dumps([tuple(v) for v in simp])
        BUILDERS[curve.autocam.spline](curve, simp)

        _build_arc_table(curve)

        return {'FINISHED'}


class AUTOCAM_OT_revert_curve(bpy.types.Operator):
    """Reset edits back to the original path"""
    bl_idname = "autocam.revert_curve"
    bl_label = "Reset to Original Path"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        curve = find_ac_curve(context.object)
        return bool(curve and 'autocam_samples_orig' in curve)

    def execute(self, context):
        curve = find_ac_curve(context.object)
        raw = [Vector(p) for p in json.loads(curve['autocam_samples_orig'])]
        simp = rdp(raw, curve.autocam.tol**2)
        BUILDERS[curve.autocam.spline](curve, simp)

        _build_arc_table(curve)

        curve['autocam_samples_base'] = curve['autocam_samples_orig']
        return {'FINISHED'}


classes = (AUTOCAM_OT_camera_to_curve,
           AUTOCAM_OT_apply_curve, AUTOCAM_OT_revert_curve)
