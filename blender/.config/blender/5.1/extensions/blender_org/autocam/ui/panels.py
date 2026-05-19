"""
UI panels for the full AutoCam flow (Record -> Path -> Rig -> Bake), plus helpers.

- word_wrap(): robust text wrapper for consistent, left-aligned panel text.
- AUTOCAM_PT_header: always-on header showing the selected Rig/Camera context or a tip.
- AUTOCAM_PT_record: start flythrough recording (Esc or Left/Right Click to finish).
- AUTOCAM_PT_path_extract_root: generate a path from an animated Camera (non-AutoCam context).
- AUTOCAM_PT_path_settings_root: edit Spline/Tolerance, Apply or Reset; helpful tips.
- AUTOCAM_PT_rig_generate_root: create the rig once a path exists.
- AUTOCAM_PT_rig_settings_root: choose Simple/Dynamic, control Speed, sync from keys; tip for baking.
- AUTOCAM_PT_rig_tracking: LookAt modes UI (Manual/Match Recording).
- AUTOCAM_PT_bake & AUTOCAM_PT_bake_settings: one-click Bake with popover settings.
- AUTOCAM_PT_danger_zone: destructive "Clear All Rigs" action (gated by prefs).

"""


import bpy
import textwrap
from ..core.utils import find_ac_curve
from ..core.props import prefs, ROOT_ID
from ..core.fcurves import action_fcurves
from ..core.licensing import is_pro


# helpers

def word_wrap(
    string="", layout=None, alignment="LEFT", max_char="auto",
    char_auto_sidepadding=0.93, context=None,
    active=False, alert=False, icon=None, scale_y=1.0,
    *, icon_px=28, pad_px=56, break_long_words=True
):
    if max_char == "auto" and context is not None:
        pref = getattr(context, "preferences", None)
        ui_scale = (getattr(getattr(pref, "view", None), "ui_scale", None)
                    or getattr(getattr(pref, "system", None), "ui_scale", 1.0) or 1.0)
        region_w = getattr(getattr(context, "region", None),
                           "width", 320) or 320
        approx_char_px = 7.0 * float(ui_scale)
        usable_px = int(region_w * float(char_auto_sidepadding)
                        ) - pad_px - (icon_px if icon else 0)
        usable_px = max(120, usable_px)
        max_char = max(8, int(usable_px / approx_char_px))
    else:
        max_char = max(8, int(max_char))

    def _wrap_line(s: str):
        s = " ".join(s.split())
        if not s:
            return [""]
        if not break_long_words:
            return textwrap.wrap(s, width=max_char, break_long_words=False, break_on_hyphens=False) or [""]
        lines, cur, cur_len = [], [], 0
        for w in s.split(" "):
            while len(w) > max_char:
                chunk, w = w[:max_char], w[max_char:]
                if cur:
                    lines.append(" ".join(cur))
                    cur, cur_len = [], 0
                lines.append(chunk)
            extra = (1 if cur else 0) + len(w)
            if cur_len + extra > max_char:
                lines.append(" ".join(cur))
                cur, cur_len = [w], len(w)
            else:
                cur.append(w)
                cur_len += extra
        if cur:
            lines.append(" ".join(cur))
        return lines

    text = str(string).replace("\r\n", "\n")
    paragraphs = text.split("\n")
    wrapped_lines = []
    for i, p in enumerate(paragraphs):
        if i and p != "":
            wrapped_lines.append("")
        wrapped_lines.extend(_wrap_line(p))
    wrapped = "\n".join(wrapped_lines)

    if layout is not None:
        col = layout.column(align=True)
        col.active = bool(active)
        col.alert = bool(alert)
        col.scale_y = float(scale_y)
        row = col.row(align=True)
        if icon:
            if isinstance(icon, int):
                row.label(text="", icon_value=icon)
            else:
                row.label(text="", icon=str(icon))
            txt = row.column(align=True)
        else:
            txt = row
        txt.alignment = alignment
        for ln in wrapped_lines:
            txt.label(text=ln)

    return wrapped


def _is_baked_camera(obj):
    if not obj or obj.type != 'CAMERA':
        return False
    return bool(obj.get("autocam_is_baked"))


def _is_camera_with_keys(obj):
    if not obj or obj.type != 'CAMERA':
        return False
    ad = getattr(obj, "animation_data", None)
    if not ad:
        return False
    
    act = getattr(ad, "action", None)
    if act:
        # Method 1: Check legacy fcurves
        fcurves = action_fcurves(act, owner=obj)
        try:
            next(iter(fcurves))
            return True
        except (StopIteration, TypeError):
            pass
        
        # Method 2: Check action frame_range (works for layered actions)
        try:
            fr = act.frame_range
            if fr[1] > fr[0]:
                return True
        except Exception:
            pass
    
    # Method 3: Check NLA tracks
    nla_tracks = getattr(ad, "nla_tracks", None)
    if nla_tracks:
        try:
            for track in nla_tracks:
                if track.strips:
                    return True
        except Exception:
            pass
    
    return False


def _infer_rig_name(curve):
    if not curve:
        return None
    ac = getattr(curve, "autocam", None)
    name = getattr(ac, "rig_name", "") if ac else ""
    if name:
        return name
    for coll in bpy.data.collections:
        if curve.name in {ob.name for ob in coll.objects}:
            return coll.name
    return curve.name


def _active_rig_or_camera_label(context):
    obj = context.object
    curve = find_ac_curve(obj)
    if curve:
        rig_name = _infer_rig_name(curve)
        return ("Rig", rig_name, 'OUTLINER_COLLECTION', False, None)
    if obj and obj.type == 'CAMERA':
        is_active = (context.scene.camera == obj)
        return ("Camera", obj.name, 'CAMERA_DATA', is_active, obj)
    return (None, None, None, False, None)


# HEADER (always visible)

class AUTOCAM_PT_header(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AutoCam'
    bl_label = " "
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        L = self.layout
        L.use_property_split = True
        L.use_property_decorate = False

        box = L.box()
        kind, name, icon, is_active, obj = _active_rig_or_camera_label(context)
        row = box.row()

        if kind == "Camera":
            status = "active" if is_active else "inactive"
            row.label(text=f"{name} ({status})", icon=icon)

            if not is_active:
                btn = box.row(align=True)
                op = btn.operator("autocam.set_active_camera",
                                  text="Make Active", icon='CHECKMARK')
                op.camera_name = name

        elif kind:
            # For rigs keep the existing label format
            row.label(text=f"Selected {kind}: {name}", icon=icon)

        else:
            word_wrap(layout=box, context=context, icon='INFO',
                      string="Select a Camera or any AutoCam rig object to begin.",
                      max_char="auto", alignment="LEFT", active=True)


# RECORD

class AUTOCAM_PT_record(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AutoCam'
    bl_label = 'Record'

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj and (_is_baked_camera(obj) or find_ac_curve(obj)):
            return False
        return True

    def draw(self, context):
        L = self.layout
        box = L.box()
        box.label(text="Camera POV Recording", icon='REC')
        row = box.row(align=True)
        row.operator("autocam.fly_record", icon='PLAY', text="Start Recording")
        row = box.row(align=True)
        word_wrap(layout=box, context=context, icon='INFO',
                  string="Press Esc (or Left/Right Click) to finish.", max_char="auto", alignment="LEFT")


# PATH

class AUTOCAM_PT_path_extract_root(bpy.types.Panel):
    """Shown when NOT in an AutoCam context."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AutoCam'
    bl_label = 'Path'
    bl_idname = "AUTOCAM_PT_path_extract_root"

    @classmethod
    def poll(cls, context):
        obj = context.object

        if _is_baked_camera(obj):
            return False

        return find_ac_curve(obj) is None

    def draw(self, context):
        L = self.layout
        L.use_property_split = True
        L.use_property_decorate = False
        obj = context.object

        box = L.box()
        box.label(text="Camera Path Extraction", icon='CURVE_DATA')

        can_convert = bool(obj and obj.type ==
                           'CAMERA' and _is_camera_with_keys(obj))
        row = box.row()
        row.enabled = can_convert
        row.operator("autocam.camera_to_curve", text="Generate Curve")

        if not can_convert:
            if not (obj and obj.type == 'CAMERA'):
                word_wrap(string="Select an animated Camera to generate a path.",
                          layout=box, context=context, icon="INFO", max_char="auto", alignment="LEFT")
            else:
                word_wrap(string="No keyframes on this Camera. Animate it first, then generate a path.",
                          layout=box, context=context, icon="INFO", max_char="auto", alignment="LEFT")


class AUTOCAM_PT_path_settings_root(bpy.types.Panel):
    """Shown when inside an AutoCam rig."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AutoCam'
    bl_label = 'Path Settings'
    bl_idname = "AUTOCAM_PT_path_settings_root"

    @classmethod
    def poll(cls, context):
        if _is_baked_camera(context.object):
            return False
        return bool(find_ac_curve(context.object))

    def draw(self, context):
        L = self.layout
        L.use_property_split = True
        L.use_property_decorate = False

        curve = find_ac_curve(context.object)
        ac = curve.autocam

        box = L.box()
        box.use_property_split = True
        box.use_property_decorate = False

        # State
        try:
            if curve['autocam_samples_base'] == curve['autocam_samples_orig']:
                box.label(text="State: Original", icon='CURVE_DATA')
            else:
                box.label(text="State: Edited", icon='EDITMODE_HLT')
        except Exception:
            box.label(text="State", icon='CURVE_DATA')

        # Controls
        box.prop(ac, "spline", text="Spline Type")
        unit_scale = context.scene.unit_settings.scale_length
        unit_txt = "cm" if unit_scale < 0.01 else (
            "m" if unit_scale < 10 else "km")
        box.prop(ac, "tol", text=f"Tolerance ({unit_txt})", slider=True)

        row = box.row(align=True)
        row.operator("autocam.apply_curve",  icon='FILE_TICK',
                     text="Apply")
        row.operator("autocam.revert_curve", icon='LOOP_BACK',
                     text="Reset")

        # Tip
        if context.mode == 'EDIT_CURVE':
            word_wrap(string="Apply Path Settings to save your edits.",
                      layout=L, context=context, icon="INFO", max_char="auto", alignment="LEFT")
            # Warning if timing was inherited - curve edits will break timing sync (Pro only)
            if is_pro() and getattr(ac, "timing_inherited", False):
                word_wrap(
                    string="Warning: Editing the curve will break inherited timing. Consider clearing inherited timing first.",
                    layout=L, context=context, icon="ERROR", max_char="auto", alignment="LEFT", alert=True
                )
                op = L.operator("autocam.clear_inherited_timing", icon="X", text="Clear Inherited Timing")
                op.curve_name = curve.name
        else:
            word_wrap(string="Switch to Edit Mode to make curve edits.",
                      layout=L, context=context, icon="INFO", max_char="auto", alignment="LEFT")


# RIG

class AUTOCAM_PT_rig_generate_root(bpy.types.Panel):
    """Shown when a path exists but the rig is not built."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AutoCam'
    bl_label = 'Rig'
    bl_idname = "AUTOCAM_PT_rig_generate_root"

    @classmethod
    def poll(cls, context):
        curve = find_ac_curve(context.object)
        return bool(curve and not getattr(curve.autocam, "rig_built", False))

    def draw(self, context):
        L = self.layout
        L.use_property_split = True
        L.use_property_decorate = False
        box = L.box()
        box.label(text="Camera Rig Generation", icon='OUTLINER_OB_CAMERA')
        box.operator("autocam.build_camera_rig", text="Generate Rig")


class AUTOCAM_PT_rig_settings_root(bpy.types.Panel):
    """Shown once the rig is built. Only the settings."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AutoCam'
    bl_label = 'Rig Settings'
    bl_idname = "AUTOCAM_PT_rig_settings_root"

    @classmethod
    def poll(cls, context):
        if _is_baked_camera(context.object):
            return False
        c = find_ac_curve(context.object)
        return bool(c and getattr(c.autocam, "rig_built", False))

    def draw(self, context):
        L = self.layout
        L.use_property_split = True
        L.use_property_decorate = False

        curve = find_ac_curve(context.object)
        ac = curve.autocam

        box = L.box()
        box.use_property_split = True
        box.use_property_decorate = False

        box.prop(ac, "mode", text="Rig Mode")

        if ac.mode == 'SIMPLE':
            box.prop(ac, "simple_speed", text="Speed")
            row = box.row(align=True)
            op = row.operator("ac.sync_speed_from_keys",
                              text="Sync Speed to Keys", icon='FILE_REFRESH')
            op.curve_name = curve.name

            # Show inherited timing controls (PRO feature)
            if is_pro():
                if getattr(ac, "timing_inherited", False):
                    # Clear button (same position as inherit button)
                    op = box.operator("autocam.clear_inherited_timing", icon="X", text="Clear Inherited Keys")
                    op.curve_name = curve.name
                    # Exposed simplify slider with Update Base button
                    row = box.row(align=True)
                    row.prop(ac, "timing_simplify", text="Simplify", slider=True)
                    op = row.operator("autocam.update_timing_base", icon="TRIA_DOWN_BAR", text="")
                    op.curve_name = curve.name
                    # Info message at bottom
                    word_wrap(
                        string="Timing inherited from source camera.",
                        layout=box, context=context, icon="TIME", max_char="auto", alignment="LEFT"
                    )
                else:
                    # Show inherit button if source camera has animation
                    src = getattr(ac, "camera", None)
                    if src:
                        ad = getattr(src, "animation_data", None)
                        if ad and ad.action:
                            op = box.operator("autocam.inherit_timing", icon="TIME", text="Inherit Original Speed")
                            op.curve_name = curve.name

        elif ac.mode == 'DYNAMIC':
            row = box.row(align=True)
            row.use_property_decorate = True
            row.prop(ac, "speed", text="Speed")
            word_wrap(
                string="Realtime handler active; value is interpreted as Blender units per second. Baking before rendering is recommended for stability.",
                layout=L, context=context, icon="INFO", max_char="auto", alignment="LEFT"
            )


class AUTOCAM_PT_rig_tracking(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AutoCam'
    bl_label = "Tracking"
    bl_parent_id = "AUTOCAM_PT_rig_settings_root"
    bl_idname = "AUTOCAM_PT_rig_tracking"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        curve = find_ac_curve(context.object)
        return bool(curve and getattr(curve.autocam, "rig_built", False))

    def draw(self, context):
        L = self.layout
        L.use_property_split = True
        L.use_property_decorate = False
        ac = find_ac_curve(context.object).autocam

        if not hasattr(ac, "lookat_mode"):
            word_wrap(string="Tracking UI props not registered. Reload the add-on.",
                      layout=L, context=context, icon="INFO", max_char="auto", alignment="LEFT")
            row = L.row(align=True)
            row.operator("wm.reload_scripts",
                         text="Reload Scripts", icon='FILE_REFRESH')
            return

        L.prop(ac, "lookat_mode", text="Mode")
        m = ac.lookat_mode
        if m == 'MANUAL':
            word_wrap(
                string="No automation; LookAt object is static.",
                layout=L, context=context, icon="INFO", max_char="auto", alignment="LEFT"
            )

        elif m == 'RECORDED_ROT':
            # Controls for Match Recording
            L.prop(ac, "recrot_smoothing", slider=True)
            L.prop(ac, "recrot_simplify", slider=True)
            


            # Tooltip
            word_wrap(
                string=(
                    "Inherit rotation keyframes from the original camera."),
                layout=L, context=context, icon="ORIENTATION_LOCAL", max_char="auto", alignment="LEFT"
            )


# BAKE

class AUTOCAM_PT_bake(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AutoCam'
    bl_label = 'Bake'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 90

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj and obj.type == 'CAMERA' and obj.get("autocam_is_baked"):
            return False
        curve = find_ac_curve(obj)
        return bool(curve and getattr(curve.autocam, "rig_built", False))

    def draw(self, context):
        L = self.layout
        col = L.box()
        row = col.row(align=True)
        row.operator("autocam.bake_autocam", text="Bake",
                     icon='OUTLINER_OB_CAMERA')
        row.popover(panel="AUTOCAM_PT_bake_settings",
                    text="", icon='PREFERENCES')


class AUTOCAM_PT_bake_settings(bpy.types.Panel):
    bl_idname = "AUTOCAM_PT_bake_settings"
    bl_label = "Bake Settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_ui_units_x = 14

    def draw(self, context):
        s = context.scene.autocam_bake
        L = self.layout
        L.label(text="Frame Range")
        L.prop(s, "range_mode", text="")
        if s.range_mode == 'CUSTOM':
            row = L.row(align=True)
            row.prop(s, "frame_start")
            row.prop(s, "frame_end")
        L.prop(s, "step")
        L.separator()
        L.label(text="Depth of Field")
        L.prop(s, "dof_mode", text="")
        L.separator()
        L.prop(s, "replace_scene_camera")
        L.prop(s, "name_suffix")


# DANGER ZONE

class AUTOCAM_PT_danger_zone(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AutoCam'
    bl_label = " "
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 100

    @classmethod
    def poll(cls, _ctx):
        p = prefs()
        return bool(p and p.show_danger)

    def draw_header(self, context):
        if bpy.app.version >= (2, 90, 0):
            self.layout.alert = True
        self.layout.label(text="Danger Zone", icon='ERROR')

    def draw(self, context):
        row = self.layout.row()
        if hasattr(row, "alert"):
            row.alert = True
        row.operator("autocam.clear_all_rigs", text="Clear All Rigs", icon='TRASH')


# register order

classes = (
    AUTOCAM_PT_header,
    AUTOCAM_PT_record,
    AUTOCAM_PT_path_extract_root,
    AUTOCAM_PT_path_settings_root,
    AUTOCAM_PT_rig_generate_root,
    AUTOCAM_PT_rig_settings_root,
    AUTOCAM_PT_rig_tracking,
    AUTOCAM_PT_bake,
    AUTOCAM_PT_bake_settings,
    AUTOCAM_PT_danger_zone,
)
