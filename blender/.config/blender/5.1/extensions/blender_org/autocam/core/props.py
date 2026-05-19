"""
AutoCam properties, preferences, and live-update glue.

- Add-on prefs (AutoCamPreferences): global defaults (spline type, tolerance, default rig mode, show/hide "Danger Zone").
- Update callbacks: switch Simple-Dynamic modes, rescale Simple mode offset keys when speed changes, toggle "Recorded Rotations" and apply live smoothing/simplify when RecRot sliders move.
- Operators:
  * AUTOCAM_OT_sync_speed_from_keys - read Follow Path offset keys and sync the UI speed.
  * AUTOCAM_OT_apply_recorded_rot - copy rotation from the recorded camera, bake
    rotation-only keys over the rig's frame range, and prep data for RecRot.
- Property groups:
  * AutoCamObjProps - per-rig pointers (curve/camera/dolly), UI state, mode,
    speed, LookAt automation, and RecRot controls.
  * AutoCamBakeSettings - frame range, step, DOF handling, naming, and scene
    camera replacement options for baking.
- Registration helpers: attach/detach PointerProperties on Object and Scene,
  class list for register/unregister, and a prefs() accessor.

  """

import bpy
from bpy.props import (
    PointerProperty, BoolProperty, IntProperty, FloatProperty, EnumProperty, StringProperty
)
from bpy.types import AddonPreferences, PropertyGroup, Operator

# modules
from .constants import ROOT_ID
from .path_follow import (
    _ensure_follow_path_on_dolly,
    _ensure_simple_keys,
    _compute_speed_from_keys,
    _scale_simple_keys_for_speed,
    _apply_simple_mode,
    _remove_simple_mode,
    _curve_range,
)
from .rig_state import (
    _rig_objects_for_curve,
    _find_trackto,
    _set_parent_keep_world,
    _ensure_childof_follow,
    _snapshot_manual_state,
    _restore_manual_state,
    _get_hide_state,
    _set_hide_state,
)
from .fcurves import (
    _rot_fcurves,
    _remove_non_rotation_fcurves,
)
from .recrot import (
    _recrot_cam,
    _recrot_make_base_from_current,
    _recrot_reapply_live,
)
from . import licensing


# ------------------------------------------------------------
# Preferences
# ------------------------------------------------------------

class AutoCamPreferences(AddonPreferences):
    bl_idname = ROOT_ID

    show_danger: BoolProperty(
        name="Show 'Danger Zone'",
        default=True,
        description="Enable destructive tools panel"
    )  # type: ignore
    default_spline: EnumProperty(
        name="Spline",
        description="Curve type used when building the path from camera motion. Can be modified using Apply/Reset",
        items=[("BEZIER", "Bezier", ""),
               ("POLY", "Poly", ""), ("NURBS", "NURBS", "")],
        default="BEZIER"
    )  # type: ignore
    default_tol: FloatProperty(
        name="Tolerance",
        description="Curve simplification tolerance used by Apply/Reset.",
        default=0.05,
        min=0.0, max=100.0, soft_min=0.0, soft_max=1.0
    )  # type: ignore
    default_rig_mode: EnumProperty(
        name="Rig Mode",
        description="How the rig moves along the path during playback",
        items=[
            ("DYNAMIC", "Dynamic (Realtime)", "Use AutoCam's realtime handler"),
            ("SIMPLE",  "Simple (Keyframed)",
             "Use Blender's Follow Path constraint"),
        ],
        default="DYNAMIC",
    )  # type: ignore
    default_speed: FloatProperty(
        name="Speed",
        description=(
            "Default movement speed for new rigs (Blender units per second). "
            "Simple mode still rescales offset keys, Dynamic mode reads this as a direct distance per second."
        ),
        default=1.0, soft_min=-100.0, soft_max=100.0
    )  # type: ignore

    default_tracking: EnumProperty(
        name="Tracking",
        description="How the camera aims by default when a rig is built",
        items=[
            ("MANUAL",        "Manual Aim", "No automation; LookAt is static."),
            ("RECORDED_ROT",  "Match Recording",
             "Inherit rotation from the recorded camera.")
        ],
        default="MANUAL",
    )  # type: ignore

    default_recrot_smoothing: FloatProperty(
        name="Smoothing",
        description="Softens range of motion (0% = raw)",
        default=15.0, min=0.0, soft_max=100.0, subtype='PERCENTAGE', precision=0
    )  # type: ignore

    default_recrot_simplify: FloatProperty(
        name="Simplify",
        description="Removes keys while keeping the same overall motion (0% = exact)",
        default=30.0, min=0.0, soft_max=100.0, subtype='PERCENTAGE', precision=0
    )  # type: ignore

    default_inherit_original_speed: BoolProperty(
        name="Inherit Original Speed",
        description="Preserve the source camera's speed changes (pauses, accelerations) when generating a rig",
        default=True
    )  # type: ignore

    # Bake defaults
    default_bake_step: IntProperty(
        name="Step",
        description="Frame step for baking (higher values = fewer baked frames)",
        default=1, min=1
    )  # type: ignore
    default_bake_dof: EnumProperty(
        name="DOF Mode",
        description="How to handle DOF when baking",
        items=[("KEYFRAMES", "Keyframes", "Bake Focus Distance into keyframes"),
               ("OBJECT", "Use Focus Object",
                "Keep the rig's FocusPoint object linked"),
               ("OFF", "Off", "Disable DOF and clear any focus object")],
        default="KEYFRAMES",
    )  # type: ignore
    default_bake_suffix: StringProperty(
        name="Suffix",
        description="Text appended to baked names (camera/collection) to keep them unique.",
        default="_Baked", maxlen=64
    )  # type: ignore
    default_bake_set_active: BoolProperty(
        name="Set Active Scene Camera",
        description="After baking, set the baked camera as the scene's active camera.",
        default=True
    )  # type: ignore

    def draw(self, _ctx):
        col = self.layout.column()
        col.prop(self, "show_danger")

        col.separator()
        box = col.box()
        box.label(text="Path Defaults")
        box.prop(self, "default_spline")
        box.prop(self, "default_tol")

        col.separator()
        box = col.box()
        box.label(text="Rig Defaults")
        box.prop(self, "default_rig_mode")
        box.prop(self, "default_speed")
        if licensing.is_pro():
            box.prop(self, "default_inherit_original_speed")
        box.prop(self, "default_tracking")
        row = box.row(align=True)
        row.prop(self, "default_recrot_smoothing")
        row.prop(self, "default_recrot_simplify")

        col.separator()
        box = col.box()
        box.label(text="Bake Defaults")
        row = box.row(align=True)
        row.prop(self, "default_bake_step")
        row.prop(self, "default_bake_dof")
        row = box.row(align=True)
        row.prop(self, "default_bake_suffix")
        row.prop(self, "default_bake_set_active")

        # Dev Tools (only visible in dev environment)
        if licensing.is_dev_environment():
            col.separator()
            box = col.box()
            box.label(text="Dev Tools", icon='TOOL_SETTINGS')
            edition = licensing.get_edition()
            icon = 'CHECKMARK' if edition == licensing.Edition.PRO else 'X'
            box.operator(
                "autocam.toggle_dev_edition",
                text=f"Edition: {edition.name}",
                icon=icon,
                depress=(edition == licensing.Edition.PRO)
            )


# ------------------------------------------------------------
# Update callbacks + helpers
# ------------------------------------------------------------

def _on_mode_update(self, context):
    curve = getattr(self, "id_data", None)
    if not curve or not getattr(curve.autocam, "rig_built", False):
        return

    if self.mode == 'SIMPLE':
        _apply_simple_mode(curve, context)

    elif self.mode == 'DYNAMIC':
        _remove_simple_mode(curve)
        context.scene.frame_set(context.scene.frame_current)


def _auto_key_speed_if_needed(curve, context):
    scene = getattr(context, "scene", None)
    ts = getattr(scene, "tool_settings", None)
    if not (scene and ts and getattr(ts, "use_keyframe_insert_auto", False)):
        return
    try:
        curve.keyframe_insert(
            data_path="autocam.speed", frame=scene.frame_current)
    except Exception:
        pass


def _on_speed_update(self, context):
    """Dynamic mode speed changes bump the revision and optionally auto-key."""
    curve = getattr(self, "id_data", None)
    if curve and "_ac_skip_speed_update" in curve.keys():
        del curve["_ac_skip_speed_update"]
        return
    if not curve or not getattr(curve.autocam, "rig_built", False):
        return
    mode = getattr(curve.autocam, "mode", "DYNAMIC")
    if mode != 'DYNAMIC':
        return
    scene = getattr(context, "scene", None)
    if scene:
        try:
            curve["ac_last_frame"] = scene.frame_current
        except Exception:
            pass
    curve["_ac_speed_revision"] = int(
        curve.get("_ac_speed_revision", 0)) + 1
    _auto_key_speed_if_needed(curve, context)


def _on_simple_speed_update(self, context):
    """In Simple mode, scale entire offset key range in time (and flip values for negative speed)."""
    curve = getattr(self, "id_data", None)
    if curve and "_ac_skip_simple_speed_update" in curve.keys():
        del curve["_ac_skip_simple_speed_update"]
        return
    if not curve or not getattr(curve.autocam, "rig_built", False):
        return
    mode = getattr(curve.autocam, "mode", "DYNAMIC")
    if mode != 'SIMPLE':
        return

    _ensure_follow_path_on_dolly(curve)
    _ensure_simple_keys(curve)
    _scale_simple_keys_for_speed(curve, float(getattr(self, "simple_speed", 0.0)))
    scene = getattr(context, "scene", None)
    if scene:
        scene.frame_set(scene.frame_current)


def _on_lookat_mode_update(self, context):
    """Switch between Manual vs Use Recorded Rotations."""
    curve = getattr(self, "id_data", None)
    if not curve or not getattr(curve.autocam, "rig_built", False):
        return

    cam, dolly, aim, look, focus = _rig_objects_for_curve(curve)

    if self.lookat_mode == 'RECORDED_ROT':
        _snapshot_manual_state(curve)
        _set_hide_state(aim, True, True)
        _set_hide_state(look, True, True)
        try:
            bpy.ops.autocam.apply_recorded_rot(curve_name=curve.name)
        except Exception:
            pass

    elif self.lookat_mode == 'MANUAL':
        _restore_manual_state(curve)


def _on_recrot_params_update(self, context):
    """Realtime apply smoothing/simplify when sliders change (in Recorded Rotations mode)."""
    curve = getattr(self, "id_data", None) or getattr(self, "curve", None)
    if not curve or not getattr(curve.autocam, "rig_built", False):
        return
    if getattr(curve.autocam, "lookat_mode", "MANUAL") != 'RECORDED_ROT':
        return
    cam = _recrot_cam(curve)
    if not cam:
        return
    fcurves, act = _rot_fcurves(cam)
    if not fcurves or not act:
        return
    _recrot_reapply_live(curve, context)


def _on_timing_simplify_update(self, context):
    """Real-time timing simplification - restore from base and apply new simplification."""
    curve = getattr(self, "id_data", None)
    if not curve or not getattr(curve.autocam, "rig_built", False):
        return
    if not getattr(curve.autocam, "timing_inherited", False):
        return
    
    from .timing import _timing_reapply_live
    _timing_reapply_live(curve, context)


def ensure_bake_defaults(scene):
    """Seed this scene's bake settings once from add-on prefs."""
    try:
        if scene.get("_ac_bake_seeded"):
            return
    except Exception:
        pass

    p = prefs()
    if not p:
        return

    s = scene.autocam_bake
    s.step = p.default_bake_step
    s.dof_mode = p.default_bake_dof
    s.name_suffix = p.default_bake_suffix
    s.replace_scene_camera = p.default_bake_set_active

    scene["_ac_bake_seeded"] = True


# ------------------------------------------------------------
# Operators
# ------------------------------------------------------------

class AUTOCAM_OT_toggle_dev_edition(Operator):
    """Toggle between Free and Pro edition for development testing."""
    bl_idname = "autocam.toggle_dev_edition"
    bl_label = "Toggle Dev Edition"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        current = licensing.get_edition()
        if current == licensing.Edition.PRO:
            licensing.set_runtime_edition(licensing.Edition.FREE)
            self.report({'INFO'}, "Switched to FREE edition")
        else:
            licensing.set_runtime_edition(licensing.Edition.PRO)
            self.report({'INFO'}, "Switched to PRO edition")
        # Force UI redraw
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return licensing.is_dev_environment()

class AUTOCAM_OT_sync_speed_from_keys(Operator):
    """Sample the Follow Path offset curve and push the derived speed back into the Simple mode slider."""
    bl_idname = "ac.sync_speed_from_keys"
    bl_label = "Sync Speed to Keys"
    bl_options = {'INTERNAL', 'UNDO'}

    curve_name: StringProperty(name="Curve")

    def execute(self, context):
        curve = bpy.data.objects.get(self.curve_name)
        if not curve or not getattr(curve, "autocam", None):
            self.report({'ERROR'}, "Curve not found")
            return {'CANCELLED'}

        spd = _compute_speed_from_keys(curve)
        if spd is None:
            self.report({'WARNING'}, "No offset keys found on Follow Path")
            return {'CANCELLED'}

        curve["_ac_skip_simple_speed_update"] = True
        curve.autocam.simple_speed = float(spd)
        self.report({'INFO'}, f"Speed synced to {spd:.4f}")
        return {'FINISHED'}


class AUTOCAM_OT_inherit_timing(Operator):
    """Inherit timing from the original camera's animation (speed, pauses, accelerations)."""
    bl_idname = "autocam.inherit_timing"
    bl_label = "Inherit Speed"
    bl_options = {'INTERNAL', 'UNDO'}

    curve_name: StringProperty(name="Curve")

    @classmethod
    def poll(cls, context):
        from .utils import find_ac_curve
        curve = find_ac_curve(context.object)
        if not curve or not getattr(curve.autocam, "rig_built", False):
            return False
        # Only show if timing not already inherited
        if getattr(curve.autocam, "timing_inherited", False):
            return False
        # Check if source camera has location animation
        src = getattr(curve.autocam, "camera", None)
        if not src:
            return False
        ad = getattr(src, "animation_data", None)
        return bool(ad and ad.action)

    def execute(self, context):
        from .timing import _apply_inherited_timing
        from .path_follow import _curve_range

        curve = bpy.data.objects.get(self.curve_name)
        if not curve or not getattr(curve, "autocam", None):
            self.report({'ERROR'}, "Curve not found")
            return {'CANCELLED'}

        dolly = getattr(curve.autocam, "dolly", None)
        if not dolly:
            self.report({'ERROR'}, "Dolly not found")
            return {'CANCELLED'}

        # Use source camera's animation range instead of stored curve range
        src = getattr(curve.autocam, "camera", None)
        ad = src.animation_data if src else None
        act = ad.action if (ad and ad.action) else None
        if act:
            # Get frame range from animation
            f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        else:
            # Fallback to curve range
            f0, f1 = _curve_range(curve)
        
        # Store user's manual keys before overwriting (for restore on clear)
        from .timing import _store_user_keys
        _store_user_keys(curve, dolly)
        
        # Clear any old inherited timing data
        if "_ac_timing_base_keys" in curve:
            del curve["_ac_timing_base_keys"]
        if "autocam_timing_keys" in curve:
            del curve["autocam_timing_keys"]
        
        success = _apply_inherited_timing(curve, dolly, f0, f1, context)
        if success:
            curve.autocam.timing_inherited = True
            curve.autocam.timing_simplify = 0.0  # Reset simplify slider
            curve.autocam.mode = 'SIMPLE'
            self.report({'INFO'}, "Timing inherited from source camera")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Could not inherit timing - source camera may not have location animation")
            return {'CANCELLED'}


class AUTOCAM_OT_clear_inherited_timing(Operator):
    """Clear inherited timing keyframes and restore previous keyframes."""
    bl_idname = "autocam.clear_inherited_timing"
    bl_label = "Clear Inherited Timing?"
    bl_options = {'INTERNAL', 'UNDO'}

    curve_name: StringProperty(name="Curve")

    @classmethod
    def poll(cls, context):
        from .utils import find_ac_curve
        curve = find_ac_curve(context.object)
        return bool(curve and getattr(curve.autocam, "timing_inherited", False))

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        from .timing import _clear_inherited_timing
        from .path_follow import _curve_range

        curve = bpy.data.objects.get(self.curve_name)
        if not curve or not getattr(curve, "autocam", None):
            self.report({'ERROR'}, "Curve not found")
            return {'CANCELLED'}

        dolly = getattr(curve.autocam, "dolly", None)
        if not dolly:
            self.report({'ERROR'}, "Dolly not found")
            return {'CANCELLED'}

        # Check if user keys will be restored
        has_user_keys = "_ac_user_offset_keys" in curve

        f0, f1 = _curve_range(curve)
        success = _clear_inherited_timing(curve, dolly, f0, f1)
        if success:
            if has_user_keys:
                self.report({'INFO'}, "Inherited timing cleared - previous keyframes restored")
            else:
                self.report({'INFO'}, "Inherited timing cleared")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Could not clear inherited timing")
            return {'CANCELLED'}


class AUTOCAM_OT_update_timing_base(Operator):
    """Capture current keyframes as the new base for the Simplify slider. Use after direct keyframe edits."""
    bl_idname = "autocam.update_timing_base"
    bl_label = "Update Base"
    bl_options = {'INTERNAL', 'UNDO'}

    curve_name: StringProperty(name="Curve")

    @classmethod
    def poll(cls, context):
        from .utils import find_ac_curve
        curve = find_ac_curve(context.object)
        return bool(curve and getattr(curve.autocam, "timing_inherited", False))

    def execute(self, context):
        from .timing import _timing_make_base

        curve = bpy.data.objects.get(self.curve_name)
        if not curve or not getattr(curve, "autocam", None):
            self.report({'ERROR'}, "Curve not found")
            return {'CANCELLED'}

        dolly = getattr(curve.autocam, "dolly", None)
        if not dolly:
            self.report({'ERROR'}, "Dolly not found")
            return {'CANCELLED'}

        _timing_make_base(curve, dolly)
        
        # Reset simplify slider to 0 since we have a new base
        curve.autocam.timing_simplify = 0.0
        
        self.report({'INFO'}, "Base updated - current keyframes captured")
        return {'FINISHED'}

class AUTOCAM_OT_simplify_timing(Operator):
    """Simplify inherited timing keyframes while preserving motion."""
    bl_idname = "autocam.simplify_timing"
    bl_label = "Simplify Timing"
    bl_options = {'INTERNAL', 'UNDO'}

    curve_name: StringProperty(name="Curve")
    tolerance: FloatProperty(
        name="Simplify",
        description="Simplification tolerance (higher = fewer keys)",
        default=30.0, min=0.0, max=100.0, subtype='PERCENTAGE'
    )

    @classmethod
    def poll(cls, context):
        from .utils import find_ac_curve
        curve = find_ac_curve(context.object)
        return bool(curve and getattr(curve.autocam, "timing_inherited", False))

    def execute(self, context):
        from .timing import _simplify_timing_keys

        curve = bpy.data.objects.get(self.curve_name)
        if not curve or not getattr(curve, "autocam", None):
            self.report({'ERROR'}, "Curve not found")
            return {'CANCELLED'}

        dolly = getattr(curve.autocam, "dolly", None)
        if not dolly:
            self.report({'ERROR'}, "Dolly not found")
            return {'CANCELLED'}

        removed = _simplify_timing_keys(curve, dolly, self.tolerance)
        self.report({'INFO'}, f"Removed {removed} keyframes")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "tolerance", slider=True)


class AUTOCAM_OT_apply_recorded_rot(Operator):
    bl_idname = "autocam.apply_recorded_rot"
    bl_label = "Apply Recorded Rotations"
    bl_options = {'INTERNAL', 'UNDO'}

    curve_name: StringProperty(name="Curve")

    def execute(self, context):
        curve = bpy.data.objects.get(self.curve_name)
        if not curve or not getattr(curve, "autocam", None):
            self.report({'ERROR'}, "Curve not found")
            return {'CANCELLED'}

        cam, dolly, aim, look, focus = _rig_objects_for_curve(curve)
        src = getattr(curve.autocam, "camera", None)

        f0, f1 = _curve_range(curve)
        try:
            context.scene.frame_set(int(f0))
            bpy.context.view_layer.update()
        except Exception:
            pass

        if not cam:
            self.report({'ERROR'}, "Rig camera not found")
            return {'CANCELLED'}
        if not src:
            self.report({'ERROR'}, "Original recorded camera not found")
            return {'CANCELLED'}

        _snapshot_manual_state(curve)

        tt = _find_trackto(aim)
        if tt:
            tt.mute = True
            tt.influence = 0.0

        try:
            _set_parent_keep_world(cam, None)
        except Exception:
            pass
        if dolly:
            _ensure_childof_follow(context, cam, dolly)

        cam.rotation_mode = 'XYZ'
        try:
            cam.delta_rotation_euler = (0.0, 0.0, 0.0)
        except Exception:
            pass

        cname = "AC_CopyRot"
        for c in list(cam.constraints):
            if c.type == 'COPY_ROTATION' and c.name == cname:
                cam.constraints.remove(c)
        cr = cam.constraints.new('COPY_ROTATION')
        cr.name = cname
        cr.target = src
        cr.use_x = cr.use_y = cr.use_z = True
        try:
            cr.target_space = 'WORLD'
            cr.owner_space = 'WORLD'
            cr.mix_mode = 'REPLACE'
        except Exception:
            pass

        f0, f1 = _curve_range(curve)
        for o in context.selected_objects:
            o.select_set(False)
        cam.select_set(True)
        context.view_layer.objects.active = cam
        try:
            bpy.ops.nla.bake(
                frame_start=int(f0), frame_end=int(f1), step=1,
                only_selected=True, visual_keying=True,
                clear_constraints=False, clear_parents=False,
                use_current_action=False, bake_types={'OBJECT'}
            )
        except Exception as e:
            if cr and cr.name in cam.constraints:
                try:
                    cam.constraints.remove(cr)
                except Exception:
                    pass
            self.report({'ERROR'}, f"Recorded Rotations bake failed: {e}")
            return {'CANCELLED'}

        for c in list(cam.constraints):
            if c.type == 'COPY_ROTATION' and c.name == cname:
                cam.constraints.remove(c)
        _remove_non_rotation_fcurves(cam)

        _recrot_make_base_from_current(curve, cam)
        ac = curve.autocam
        if (float(getattr(ac, "recrot_smoothing", 0.0)) > 0.0 or
                float(getattr(ac, "recrot_simplify", 0.0)) > 0.0):
            # Live reapply path depends on those props; just trigger it
            _recrot_reapply_live(curve, context)

        self.report(
            {'INFO'}, "Recorded rotations baked (rotation-only). Aim disabled; rig motion preserved.")
        return {'FINISHED'}


# ------------------------------------------------------------
# Property Groups
# ------------------------------------------------------------

class AutoCamObjProps(PropertyGroup):
    curve: PointerProperty(type=bpy.types.Object)
    camera: PointerProperty(type=bpy.types.Object)
    dolly: PointerProperty(type=bpy.types.Object)
    rigcam: PointerProperty(type=bpy.types.Object)

    rig_built: BoolProperty(default=False)
    spline: EnumProperty(
        name="Spline Type",
        description="Curve type used when building the path from camera motion. Can be modified using Apply/Reset",
        items=[("BEZIER", "Bezier", ""),
               ("POLY", "Poly", ""), ("NURBS", "NURBS", "")],
        default="BEZIER"
    )  # type: ignore
    tol: FloatProperty(
        name="Tolerance",
        description="Curve simplification tolerance used by Apply/Reset.",
        default=0.05, min=0.0, soft_max=1.0
    )  # type: ignore
    speed: FloatProperty(
        name="Dynamic Speed",
        description=(
            "Path traversal speed for Dynamic mode (distance per second; supports keyframing, negative to reverse)."
        ),
        default=1.0, soft_min=-100.0, soft_max=100.0,
        options={'ANIMATABLE'},
        update=_on_speed_update
    )  # type: ignore
    simple_speed: FloatProperty(
        name="Simple Speed",
        description=(
            "Desired travel speed while in Simple mode. Adjusting this stretches the Follow Path offset keys."
        ),
        default=1.0, soft_min=-100.0, soft_max=100.0,
        options={'ANIMATABLE'},
        update=_on_simple_speed_update
    )  # type: ignore
    mode: EnumProperty(
        name="Mode",
        description="How the rig moves along the path during playback",
        items=[
            ("DYNAMIC", "Dynamic (Realtime)", "", "", 0),
            ("SIMPLE", "Simple (Keyframed)", "", "", 1),
        ],
        default="DYNAMIC",
        update=_on_mode_update,
    )  # type: ignore

    # UI foldouts
    ui_path_open:    BoolProperty(
        name="Open Path Settings",    default=True)   # type: ignore
    ui_rig_open:     BoolProperty(
        name="Open Rig Settings",     default=True)   # type: ignore
    ui_track_open:   BoolProperty(
        name="Open Tracking Settings", default=True)  # type: ignore

    # Rig identity for UI (set during rig build)
    rig_name:  StringProperty(name="Rig Name",  default="")  # type: ignore
    rig_index: IntProperty(name="Rig Index", default=0)      # type: ignore

    # Timing inheritance tracking
    timing_inherited: BoolProperty(
        name="Timing Inherited",
        description="Whether this rig inherited timing from the source camera",
        default=False
    )  # type: ignore
    timing_simplify: FloatProperty(
        name="Simplify",
        description="Simplify inherited timing keyframes (higher = fewer keys)",
        default=0.0, min=0.0, soft_max=100.0, subtype='PERCENTAGE', precision=0,
        update=_on_timing_simplify_update,
    )  # type: ignore

    lookat_mode: EnumProperty(
        name="LookAt Automation",
        description="How the camera aims during playback",
        items=[
            ("MANUAL",        "Manual Aim",
             "No automation; LookAt object is static", "", 0),
            ("RECORDED_ROT",  "Match Recording",
             "Inherit rotation from the original recorded camera", "", 1),
        ],
        default="MANUAL",
        update=_on_lookat_mode_update,
    )  # type: ignore

    recrot_smoothing: FloatProperty(
        name="Smoothing",
        description="Softens range of motion (0% = raw)",
        default=0.0, min=0.0, soft_max=100.0, subtype='PERCENTAGE', precision=0,
        update=_on_recrot_params_update,
    )  # type: ignore

    recrot_simplify: FloatProperty(
        name="Simplify",
        description="Removes keys while keeping the same overall motion (0% = exact)",
        default=0.0, min=0.0, soft_max=100.0, subtype='PERCENTAGE', precision=0,
        update=_on_recrot_params_update,
    )  # type: ignore



    lookat_target: PointerProperty(
        name="Target", type=bpy.types.Object)  # type: ignore

    lookahead_distance: FloatProperty(
        name="Look-ahead", default=0.5, min=0.0, soft_max=10.0)  # type: ignore
    path_tangent_use_lookat: BoolProperty(
        name="Use LookAt object", default=True
    )  # type: ignore


class AutoCamBakeSettings(PropertyGroup):
    range_mode: EnumProperty(
        name="Range",
        items=[("CURVE", "Curve Range", "Use curve's start/end"),
               ("SCENE", "Scene Range", "Use scene frame range"),
               ("CUSTOM", "Custom", "Specify start/end below")],
        default="CURVE",
    )  # type: ignore
    frame_start: IntProperty(name="Start", default=1, min=0)
    frame_end:   IntProperty(name="End",   default=250, min=1)
    step: IntProperty(
        name="Step",
        description="Frame step for baking (higher values = fewer baked frames)",
        default=1, min=1
    )

    dof_mode: EnumProperty(
        name="Depth of Field",
        description="How to handle DOF when baking",
        items=[("KEYFRAMES", "Keyframes", "Bake Focus Distance into keyframes"),
               ("OBJECT", "Use Focus Object",
                "Keep the rig's FocusPoint object linked"),
               ("OFF", "Off", "Disable DOF and clear any focus object")],
        default="KEYFRAMES",
    )  # type: ignore

    replace_scene_camera: BoolProperty(
        name="Set as active scene camera", default=True)  # type: ignore
    name_suffix: StringProperty(
        name="Suffix",
        description="Text appended to baked names (camera/collection) to keep them unique.",
        default="_Baked",
        maxlen=32
    )  # type: ignore


# ------------------------------------------------------------
# Registration helpers
# ------------------------------------------------------------

def attach_pointer():
    bpy.types.Object.autocam = PointerProperty(type=AutoCamObjProps)
    bpy.types.Scene.autocam_bake = PointerProperty(type=AutoCamBakeSettings)


def detach_pointer():
    if hasattr(bpy.types.Object, "autocam"):
        del bpy.types.Object.autocam
    if hasattr(bpy.types.Scene, "autocam_bake"):
        del bpy.types.Scene.autocam_bake


classes = (
    AutoCamPreferences,
    AutoCamObjProps,
    AUTOCAM_OT_toggle_dev_edition,
    AUTOCAM_OT_apply_recorded_rot,
    AUTOCAM_OT_sync_speed_from_keys,
    AUTOCAM_OT_inherit_timing,
    AUTOCAM_OT_clear_inherited_timing,
    AUTOCAM_OT_update_timing_base,
    AUTOCAM_OT_simplify_timing,
    AutoCamBakeSettings,
)

__all__ = ("ROOT_ID", "prefs")


def prefs():
    addon = bpy.context.preferences.addons.get(ROOT_ID)
    return addon.preferences if addon else None
