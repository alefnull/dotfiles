"""
Bake an AutoCam rig to a standalone, keyframed camera.

- Determines frame range from Scene/Custom/curve metadata; respects step.
- Duplicates the rig camera, resets deltas/rotation mode, and places it in a unique "_Baked" collection under the AutoCam master collection.
- Temporarily COPY_TRANSFORMS from the rig camera, then runs NLA Bake (visual keying, clears parents/constraints) to record OBJECT transforms.
- Sets first-frame transform explicitly and inserts loc/rot/scale keys.
- DOF options:
    OFF - turn off DOF and remove any focus_distance fcurves.
    OBJECT - keep DOF and bind to the rig's Focus object.
    KEYFRAMES - key focus_distance each frame/step to the Focus distance.
- Optionally replaces Scene camera with the baked one.
- Tidy ups: toggles rig collection visibility for DOF OBJECT mode and reports results.

"""


import bpy
from mathutils import Matrix
from bpy.types import Operator
from ..core.utils import find_ac_curve
from ..core.constants import MASTER_COLL
from ..core.fcurves import action_fcurves


def _unique_name(base):
    name = base
    i = 1
    while bpy.data.objects.get(name):
        name = f"{base}.{i:03d}"
        i += 1
    return name


def _focus_for_curve(curve):
    for o in bpy.data.objects:
        ac = getattr(o, "autocam", None)
        if ac and ac.curve == curve and o.name.endswith("_FocusPoint"):
            return o
    return None


def _rig_collection_for_curve(curve):
    ac = getattr(curve, "autocam", None)
    rig_name = getattr(ac, "rig_name", "") if ac else ""
    if rig_name:
        col = bpy.data.collections.get(rig_name)
        if col:
            return col

    rigcam = getattr(ac, "rigcam", None)
    for col in curve.users_collection:
        if rigcam and rigcam.name in {o.name for o in col.objects}:
            return col

    return curve.users_collection[0] if curve.users_collection else None


def _find_layer_collection(layer_collection, collection):
    if layer_collection.collection == collection:
        return layer_collection
    for child in layer_collection.children:
        hit = _find_layer_collection(child, collection)
        if hit:
            return hit
    return None


class AUTOCAM_OT_bake_autocam(Operator):
    """Bake AutoCam rig to a new, independent camera"""
    bl_idname = "autocam.bake_autocam"
    bl_label = "Bake"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        curve = find_ac_curve(context.object)
        return bool(curve and getattr(curve.autocam, "rig_built", False)
                    and getattr(curve.autocam, "rigcam", None))

    def execute(self, context):
        sc = context.scene
        curve = find_ac_curve(context.object)
        rigcam = curve.autocam.rigcam if curve else None
        if not curve or not rigcam or rigcam.name not in bpy.data.objects:
            self.report({'ERROR'}, "AutoCam rig camera not found")
            return {'CANCELLED'}

        s = getattr(sc, "autocam_bake", None)
        if not s:
            self.report({'ERROR'}, "Bake settings not available")
            return {'CANCELLED'}

        # --- frame range
        if s.range_mode == "SCENE":
            f0, f1 = int(sc.frame_start), int(sc.frame_end)
        elif s.range_mode == "CUSTOM":
            f0 = int(s.frame_start)
            f1 = max(int(s.frame_end), f0 + 1)
        else:
            f0 = int(curve.get("autocam.frame_start", sc.frame_start))
            f1 = int(curve.get("autocam.frame_end",   sc.frame_end))
            if f1 <= f0:
                f1 = f0 + 1
        step = max(1, int(s.step))

        baked = rigcam.copy()
        baked.data = rigcam.data.copy()
        baked.name = _unique_name(rigcam.name + s.name_suffix)
        if baked.data:
            baked.data.name = baked.name
        baked.animation_data_clear()
        baked.delta_location = (0.0, 0.0, 0.0)
        baked.delta_scale = (1.0, 1.0, 1.0)
        baked.delta_rotation_euler = (0.0, 0.0, 0.0)
        baked.rotation_mode = 'XYZ'

        baked["autocam_is_baked"] = True
        baked["autocam_source_curve"] = curve.name

        master = bpy.data.collections.get(MASTER_COLL)
        if not master:
            master = bpy.data.collections.new(MASTER_COLL)
            sc.collection.children.link(master)

        base = f"{curve.name}{s.name_suffix}"
        name = base
        i = 1
        while bpy.data.collections.get(name):
            name = f"{base}.{i:03d}"
            i += 1
        baked_col = bpy.data.collections.new(name)
        master.children.link(baked_col)
        baked_col.objects.link(baked)

        ct = baked.constraints.new('COPY_TRANSFORMS')
        ct.target = rigcam

        context.view_layer.update()

        for o in context.selected_objects:
            o.select_set(False)
        baked.select_set(True)
        context.view_layer.objects.active = baked

        try:
            bpy.ops.nla.bake(
                frame_start=f0, frame_end=f1, step=step,
                only_selected=True, visual_keying=True,
                clear_constraints=True, clear_parents=True,
                use_current_action=False, bake_types={'OBJECT'}
            )
        except Exception as e:
            self.report({'ERROR'}, f"Bake failed: {e}")
            return {'CANCELLED'}

        sc.frame_set(f0)
        mw: Matrix = rigcam.matrix_world.copy()
        loc, rot, scale = mw.decompose()
        baked.rotation_mode = 'XYZ'
        baked.location = loc
        baked.rotation_euler = rot.to_euler('XYZ')
        baked.scale = scale
        baked.keyframe_insert(data_path="location", frame=f0)
        baked.keyframe_insert(data_path="rotation_euler", frame=f0)
        baked.keyframe_insert(data_path="scale", frame=f0)

        focus = _focus_for_curve(curve)
        if s.dof_mode == 'KEYFRAMES' and focus:
            baked.data.dof.use_dof = True
            baked.data.dof.focus_object = None
            orig = sc.frame_current
            for f in range(f0, f1 + 1, step):
                sc.frame_set(f)
                cam_loc = baked.matrix_world.translation
                tgt_loc = focus.matrix_world.translation
                dist = (tgt_loc - cam_loc).length
                baked.data.dof.focus_distance = float(dist)
                baked.data.keyframe_insert(
                    data_path="dof.focus_distance", frame=f)
            sc.frame_set(orig)

        elif s.dof_mode == 'OBJECT' and focus:
            baked.data.dof.use_dof = True
            baked.data.dof.focus_object = focus

        elif s.dof_mode == 'OFF':
            baked.data.dof.use_dof = False
            baked.data.dof.focus_object = None
            ad = baked.data.animation_data
            if ad and ad.action:
                fcurves = action_fcurves(ad.action, owner=baked.data)
                for fc in list(fcurves):
                    if fc.data_path == "dof.focus_distance":
                        fcurves.remove(fc)

        if s.replace_scene_camera:
            sc.camera = baked

        rig_col = _rig_collection_for_curve(curve)
        if rig_col:
            lc = _find_layer_collection(
                context.view_layer.layer_collection, rig_col)
            if lc:
                lc.exclude = True

        lc_baked = _find_layer_collection(
            context.view_layer.layer_collection, baked_col)
        if lc_baked:
            lc_baked.exclude = False
            context.view_layer.active_layer_collection = lc_baked

        self.report(
            {'INFO'}, f"Baked to {baked.name}  [{f0}-{f1}, step {step}]")
        return {'FINISHED'}


classes = (AUTOCAM_OT_bake_autocam,)
