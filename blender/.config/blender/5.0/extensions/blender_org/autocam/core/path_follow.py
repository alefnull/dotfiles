"""
Simple mode: follow-path constraint and time/key management for the rig dolly.

- _ensure_follow_path_on_dolly(): creates/configs the FOLLOW_PATH constraint, uses fixed
  location (Blender 4.x), sets axes, restores saved offset when toggling modes.
- _ensure_simple_keys(): ensures two keys on offset_factor mapping frame_start=0 to frame_end=1.
- _compute_speed_from_keys(): derives UI speed from the current offset_factor keys.
- _scale_simple_keys_for_speed(): scales key times to match a desired (+-) speed.
- _apply_simple_mode() / _remove_simple_mode(): enter/exit Simple mode cleanly.

"""


import json
import bpy
from .fcurves import action_fcurves


def _fp_path_name(): return "AC_FollowPath"
def _fp_data_path(name): return f'constraints["{name}"].offset_factor'


def _curve_range(curve):
    f0 = int(curve.get("autocam.frame_start", 1))
    f1 = int(curve.get("autocam.frame_end",   250))
    if f1 <= f0:
        f1 = f0 + 1
    return f0, f1


def _find_follow_path(dolly, curve):
    for c in dolly.constraints:
        if c.type == 'FOLLOW_PATH' and c.target == curve:
            return c
    return None


def _ensure_follow_path_on_dolly(curve):
    dolly = curve.autocam.dolly
    if not dolly or dolly.name not in bpy.data.objects:
        return None

    con = _find_follow_path(dolly, curve)
    if not con:
        con = dolly.constraints.new('FOLLOW_PATH')
        con.name = _fp_path_name()
    con.target = curve

    if hasattr(con, "use_fixed_location"):
        con.use_fixed_location = True

    con.use_curve_follow = True
    try:
        con.forward_axis = 'TRACK_NEGATIVE_Z'
        con.up_axis = 'UP_Y'
    except Exception:
        pass

    try:
        con.offset_factor = float(curve.get("ac_offset", 0.0))
    except Exception:
        pass

    return con


def _ensure_simple_keys(curve):
    dolly = curve.autocam.dolly
    if not dolly:
        return
    con = _ensure_follow_path_on_dolly(curve)
    if not con:
        return

    data_path = _fp_data_path(con.name)

    try:
        dolly.driver_remove(data_path)
    except Exception:
        pass

    f0, f1 = _curve_range(curve)

    ad = dolly.animation_data
    act = ad.action if (ad and ad.action) else None
    fcurves = action_fcurves(act, owner=dolly) if act else None
    fcu = fcurves.find(data_path) if fcurves else None

    if not fcu or len(fcu.keyframe_points) < 2:
        dolly.location = (0.0, 0.0, 0.0)
        dolly.rotation_euler = (0.0, 0.0, 0.0)
        dolly.scale = (1.0, 1.0, 1.0)

        dolly.keyframe_insert(data_path=data_path, frame=f0)
        con.offset_factor = 1.0
        dolly.keyframe_insert(data_path=data_path, frame=f1)

        ad = dolly.animation_data
        act = ad.action if (ad and ad.action) else None
        fcurves = action_fcurves(act, owner=dolly) if act else None
        fcu = fcurves.find(data_path) if fcurves else None
        if fcu:
            k0, k1 = fcu.keyframe_points[0], fcu.keyframe_points[-1]
            k0.co.x, k0.co.y = float(f0), 0.0
            k1.co.x, k1.co.y = float(f1), 1.0
            k0.interpolation = k1.interpolation = 'BEZIER'
            try:
                k0.handle_left_type = k0.handle_right_type = 'AUTO_CLAMPED'
                k1.handle_left_type = k1.handle_right_type = 'AUTO_CLAMPED'
            except Exception:
                pass
        con.offset_factor = 0.0
    return fcu


def _compute_speed_from_keys(curve):
    dolly = curve.autocam.dolly
    if not dolly:
        return None
    con = _find_follow_path(dolly, curve)
    if not con:
        return None

    data_path = _fp_data_path(con.name)
    ad = dolly.animation_data
    act = ad.action if (ad and ad.action) else None
    fcurves = action_fcurves(act, owner=dolly) if act else None
    fcu = fcurves.find(data_path) if fcurves else None
    if not fcu or len(fcu.keyframe_points) < 1:
        return None

    k0 = fcu.keyframe_points[0]
    k1 = fcu.keyframe_points[-1]
    dt = max(1.0, (k1.co.x - k0.co.x))
    do = (k1.co.y - k0.co.y)

    f0, f1 = _curve_range(curve)
    dur = max(1.0, float(f1 - f0))
    return (do * dur) / dt


def _get_offset_fcurve(curve):
    dolly = getattr(curve.autocam, "dolly", None)
    if not dolly or dolly.name not in bpy.data.objects:
        return None, None, None

    con = None
    for c in dolly.constraints:
        if c.type == 'FOLLOW_PATH' and c.target == curve:
            con = c
            break
    if not con:
        return dolly, None, None

    data_path = f'constraints["{con.name}"].offset_factor'
    ad = dolly.animation_data
    act = ad.action if (ad and ad.action) else None
    fcurves = action_fcurves(act, owner=dolly) if act else None
    fcu = fcurves.find(data_path) if fcurves else None
    return dolly, con, fcu


def _scale_simple_keys_for_speed(curve, desired_speed):
    dolly, con, fcu = _get_offset_fcurve(curve)
    if not (dolly and con):
        return
    if not fcu or len(fcu.keyframe_points) < 2:
        from .props import _ensure_simple_keys as _ensure_simple_keys
        _ensure_simple_keys(curve)
        dolly, con, fcu = _get_offset_fcurve(curve)
        if not fcu or len(fcu.keyframe_points) < 2:
            return

    kps = sorted(fcu.keyframe_points, key=lambda k: k.co.x)
    k0, kN = kps[0], kps[-1]
    f0, fN = float(k0.co.x), float(kN.co.x)
    if abs(desired_speed) < 1e-6:
        desired_speed = 1e-6

    fstart, fend = _curve_range(curve)
    dur = max(1.0, float(fend - fstart))
    dt_target = dur / abs(desired_speed)

    span_now = max(1e-6, fN - f0)
    scale = dt_target / span_now

    y0, yN = float(k0.co.y), float(kN.co.y)

    for kp in kps:
        kp.co.x = f0 + (float(kp.co.x) - f0) * scale

    if desired_speed < 0.0:
        pivot = (y0 + yN) * 0.5
        for kp in kps:
            kp.co.y = (pivot * 2.0) - float(kp.co.y)

    try:
        for kp in kps:
            kp.interpolation = kp.interpolation or 'BEZIER'
            kp.handle_left_type = kp.handle_left_type or 'AUTO_CLAMPED'
            kp.handle_right_type = kp.handle_right_type or 'AUTO_CLAMPED'
    except Exception:
        pass

    fcu.update()


def _serialize_simple_keys(fcu):
    payload = []
    if not fcu:
        return payload
    try:
        for kp in fcu.keyframe_points:
            payload.append({
                "co": [float(kp.co.x), float(kp.co.y)],
                "hl": [float(kp.handle_left.x), float(kp.handle_left.y)],
                "hr": [float(kp.handle_right.x), float(kp.handle_right.y)],
                "interp": kp.interpolation,
                "hl_type": getattr(kp, "handle_left_type", ""),
                "hr_type": getattr(kp, "handle_right_type", ""),
            })
    except Exception:
        payload = []
    return payload


def _restore_simple_keys_from_curve(curve, fcu):
    if not fcu:
        return
    raw = curve.pop("_ac_simple_keys", None)
    if not raw:
        return
    try:
        records = json.loads(raw)
    except Exception:
        return
    if not isinstance(records, list) or not records:
        return

    try:
        fcu.keyframe_points.clear()
    except Exception:
        pass

    for rec in records:
        try:
            frame = float(rec["co"][0])
            value = float(rec["co"][1])
        except Exception:
            continue
        kp = fcu.keyframe_points.insert(frame, value, options={'FAST'})
        try:
            kp.interpolation = rec.get("interp") or kp.interpolation
        except Exception:
            pass
        hl = rec.get("hl")
        hr = rec.get("hr")
        if hl and hasattr(kp, "handle_left"):
            try:
                kp.handle_left = (float(hl[0]), float(hl[1]))
            except Exception:
                pass
        if hr and hasattr(kp, "handle_right"):
            try:
                kp.handle_right = (float(hr[0]), float(hr[1]))
            except Exception:
                pass
        hl_type = rec.get("hl_type")
        hr_type = rec.get("hr_type")
        try:
            if hl_type:
                kp.handle_left_type = hl_type
            if hr_type:
                kp.handle_right_type = hr_type
        except Exception:
            pass
    try:
        fcu.update()
    except Exception:
        pass


def _apply_simple_mode(curve, context):
    _ensure_follow_path_on_dolly(curve)
    fcu = _ensure_simple_keys(curve)
    _restore_simple_keys_from_curve(curve, fcu)
    context.scene.frame_set(context.scene.frame_current)
    spd = _compute_speed_from_keys(curve)
    if spd is not None:
        curve["_ac_skip_simple_speed_update"] = True
        curve.autocam.simple_speed = float(spd)


def _remove_simple_mode(curve):
    dolly = curve.autocam.dolly
    if not dolly:
        return
    con = _find_follow_path(dolly, curve)
    if not con:
        return
    try:
        curve["ac_offset"] = float(con.offset_factor)
    except Exception:
        pass
    data_path = _fp_data_path(con.name)
    try:
        ad = dolly.animation_data
        act = ad.action if (ad and ad.action) else None
        if act:
            fcurves = action_fcurves(act, owner=dolly)
            fcu = fcurves.find(data_path) if fcurves else None
            if fcu:
                payload = _serialize_simple_keys(fcu)
                if payload:
                    try:
                        curve["_ac_simple_keys"] = json.dumps(payload)
                    except Exception:
                        pass
                fcurves.remove(fcu)
    except Exception:
        pass
    dolly.constraints.remove(con)
