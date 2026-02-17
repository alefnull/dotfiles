"""
Rig object discovery and state transitions between Manual/Simple/Dynamic.

- _rig_objects_for_curve(): resolve (cam, dolly, aim, look, focus) for a rig curve.
- Parenting/constraints: _set_parent_keep_world(), _ensure_childof_follow() for translation-only follow.
- Visibility & key cleanup: _get_hide_state/_set_hide_state, _clear_rotation_keys.
- Manual snapshot/restore: persist and restore parent/poses/visibility when toggling modes.

"""


import bpy
import math
from mathutils import Matrix
from .fcurves import action_fcurves


def _rig_objects_for_curve(curve):
    ac = getattr(curve, "autocam", None)
    cam = getattr(ac, "rigcam", None)
    dolly = getattr(ac, "dolly", None)

    aim = cam.parent if (
        cam and cam.parent and cam.parent.name.endswith("_Aim")) else None
    look = None
    focus = None

    for o in bpy.data.objects:
        oac = getattr(o, "autocam", None)
        if not oac or oac.curve != curve:
            continue
        n = o.name
        if aim is None and n.endswith("_Aim"):
            aim = o
        elif look is None and n.endswith("_LookAt"):
            look = o
        elif focus is None and n.endswith("_FocusPoint"):
            focus = o

    return cam, dolly, aim, look, focus


def _find_trackto(aim_obj):
    if not aim_obj:
        return None
    for c in aim_obj.constraints:
        if c.type == 'TRACK_TO':
            return c
    return None


def _set_parent_keep_world(obj, new_parent):
    if not obj:
        return
    mw = obj.matrix_world.copy()
    obj.parent = new_parent
    if new_parent:
        obj.matrix_parent_inverse = new_parent.matrix_world.inverted()
    else:
        obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_world = mw


def _ensure_childof_follow(context, cam, dolly):

    for c in list(cam.constraints):
        if c.type == 'CHILD_OF' and c.name == "AC_FollowDolly":
            cam.constraints.remove(c)

    co = cam.constraints.new('CHILD_OF')
    co.name = "AC_FollowDolly"
    co.target = dolly

    co.use_location_x = co.use_location_y = co.use_location_z = True
    co.use_rotation_x = co.use_rotation_y = co.use_rotation_z = False
    co.use_scale_x = co.use_scale_y = co.use_scale_z = False

    for o in context.selected_objects:
        o.select_set(False)
    cam.select_set(True)
    context.view_layer.objects.active = cam
    try:
        bpy.ops.constraint.childof_set_inverse(
            constraint=co.name, owner='OBJECT')
    except Exception:
        pass


def _clear_rotation_keys(obj):
    ad = getattr(obj, "animation_data", None)
    act = ad.action if (ad and ad.action) else None
    if not act:
        return
    fcurves = action_fcurves(act, owner=obj)
    for fcu in list(fcurves):
        if (fcu.data_path or "").startswith("rotation_"):
            fcurves.remove(fcu)


def _get_hide_state(obj):
    if not obj:
        return (False, False)
    # Viewport
    hv = False
    if hasattr(obj, "hide_viewport"):
        hv = bool(getattr(obj, "hide_viewport"))
    else:
        try:
            hv = bool(obj.hide_get())
        except Exception:
            hv = False
    # Render
    hr = bool(getattr(obj, "hide_render", False))
    return (hv, hr)


def _set_hide_state(obj, viewport_hidden: bool, render_hidden: bool):
    if not obj:
        return
    # Viewport
    try:
        obj.hide_set(viewport_hidden)
    except Exception:
        if hasattr(obj, "hide_viewport"):
            obj.hide_viewport = viewport_hidden
    # Render
    try:
        obj.hide_render = render_hidden
    except Exception:
        pass


def _snapshot_manual_state(curve):
    cam, dolly, aim, look, focus = _rig_objects_for_curve(curve)
    if not cam:
        return
    key = "ac_manual_snapshot"
    if curve.get(key):
        return

    aim_hv, aim_hr = _get_hide_state(aim)
    look_hv, look_hr = _get_hide_state(look)

    snap = {
        "parent": cam.parent.name if cam.parent else "",
        "loc": tuple(cam.location),
        "rot_euler": tuple(cam.rotation_euler),
        "rot_mode": cam.rotation_mode,
        "scale": tuple(cam.scale),
        "delta_loc": tuple(getattr(cam, "delta_location", (0.0, 0.0, 0.0))),
        "delta_rot": tuple(getattr(cam, "delta_rotation_euler", (0.0, 0.0, 0.0))),
        "mpi": tuple(e for row in cam.matrix_parent_inverse for e in row),
        "aim_tt_muted": False,
        "aim_tt_infl": 1.0,
        "aim_hide_vp": aim_hv,
        "aim_hide_r": aim_hr,
        "look_hide_vp": look_hv,
        "look_hide_r": look_hr,
    }
    tt = _find_trackto(aim)
    if tt:
        snap["aim_tt_muted"] = bool(getattr(tt, "mute", False))
        snap["aim_tt_infl"] = float(getattr(tt, "influence", 1.0))

    curve[key] = snap


def _restore_manual_state(curve):
    cam, dolly, aim, look, focus = _rig_objects_for_curve(curve)
    if not cam:
        return
    snap = curve.get("ac_manual_snapshot")
    tt = _find_trackto(aim)

    for c in list(cam.constraints):
        if c.type == 'CHILD_OF' and c.name == "AC_FollowDolly":
            cam.constraints.remove(c)

    if tt:
        tt.mute = bool(snap["aim_tt_muted"]) if snap else False
        tt.influence = float(snap["aim_tt_infl"]) if snap else 1.0

    if aim and cam.parent != aim:
        mw = cam.matrix_world.copy()
        cam.parent = aim
        if snap and "mpi" in snap:
            M = Matrix(((snap["mpi"][0],  snap["mpi"][1],  snap["mpi"][2],  snap["mpi"][3]),
                        (snap["mpi"][4],  snap["mpi"][5],
                         snap["mpi"][6],  snap["mpi"][7]),
                        (snap["mpi"][8],  snap["mpi"][9],
                         snap["mpi"][10], snap["mpi"][11]),
                        (snap["mpi"][12], snap["mpi"][13], snap["mpi"][14], snap["mpi"][15])))
            cam.matrix_parent_inverse = M
        else:
            cam.matrix_parent_inverse = aim.matrix_world.inverted()
        cam.matrix_world = mw

    if snap:
        cam.rotation_mode = snap.get("rot_mode", "XYZ")
        cam.location = snap.get("loc", (0.0, 0.0, 0.0))
        cam.rotation_euler = snap.get("rot_euler", (0.0, 0.0, 0.0))
        cam.scale = snap.get("scale", (1.0, 1.0, 1.0))
        try:
            cam.delta_location = snap.get("delta_loc", (0.0, 0.0, 0.0))
            cam.delta_rotation_euler = snap.get(
                "delta_rot", (0.0, math.pi, 0.0))
        except Exception:
            pass
    else:
        cam.rotation_mode = 'XYZ'
        try:
            cam.delta_rotation_euler = (0.0, math.pi, 0.0)
        except Exception:
            pass

    _clear_rotation_keys(cam)

    for c in list(cam.constraints):
        if c.type == 'COPY_ROTATION' and c.name == "AC_CopyRot":
            cam.constraints.remove(c)

    if snap:
        _set_hide_state(aim,  snap.get("aim_hide_vp", False),
                        snap.get("aim_hide_r", False))
        _set_hide_state(look, snap.get("look_hide_vp", False),
                        snap.get("look_hide_r", False))
    else:
        _set_hide_state(aim, False, False)
        _set_hide_state(look, False, False)
