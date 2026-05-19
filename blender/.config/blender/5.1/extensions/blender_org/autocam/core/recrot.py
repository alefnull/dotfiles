"""
Recorded-Rotation (RecRot): non-destructive smoothing/simplification pipeline.

- Duplicates current rotation_euler keys to a hidden 'base' Action, restores from it on each apply.
- Simplify: flat-run collapse then best-of (PLA vs value-only RDP) by epsilon (radians).
- Smooth: zero-phase, detrended Butterworth (strength <= 5). For strength > 5, blends interior keys
  toward a straight line between the first and second-last keys. Endpoints remain exact.
- _recrot_reapply_live(): rebuilds from base and re-applies on UI changes; refreshes the viewport.

"""


import bpy
from .fcurves import _rot_fcurves, _remove_non_rotation_fcurves, action_fcurves
from .filters import (_unwrap_euler, _simplify_flat_runs, simplify_rdp,
                      _butter_zero_phase_detrended, _cutoff_from_slider)
from .path_follow import _curve_range


def _duplicate_rot_action(src_act, owner=None, name_suffix="_RECROT_BASE"):
    if not src_act:
        return None
    
    # Create a full copy of the action (works for both Legacy and Layered)
    new = src_act.copy()
    new.name = src_act.name + name_suffix
    
    # Remove non-rotation fcurves
    fcurves = action_fcurves(new, owner=owner)
    to_remove = []
    
    # Collect first to avoid modification during iteration
    for fcu in fcurves:
        dp = fcu.data_path or ""
        if not (dp.startswith("rotation_euler") or dp.startswith("rotation_quaternion")):
            to_remove.append(fcu)
            
    for fcu in to_remove:
        try:
            fcurves.remove(fcu)
        except Exception:
            pass
            
    return new


def _recrot_cam(curve):
    ac = getattr(curve, "autocam", None)
    return getattr(ac, "rigcam", None) if ac else None


def _recrot_make_base_from_current(curve, cam):
    fcurves, act = _rot_fcurves(cam)
    if not fcurves or not act:
        return None
    base = _duplicate_rot_action(act, owner=cam)
    if base:
        curve["_ac_recrot_base_action"] = base.name
        curve["_ac_recrot_base_source"] = act.name
    return base


def _recrot_get_base_action(curve):
    name = curve.get("_ac_recrot_base_action")
    if name:
        return bpy.data.actions.get(name)
    return None


def _recrot_restore_from_base(curve, cam):
    base = _recrot_get_base_action(curve)
    if not base:
        return False
    ad = cam.animation_data_create()
    if not ad.action:
        ad.action = bpy.data.actions.new(cam.name + "_Rot")
    act = ad.action

    fcurves = action_fcurves(act, owner=cam, create=True)
    for fcu in list(fcurves):
        if (fcu.data_path or "").startswith("rotation_euler"):
            fcurves.remove(fcu)

    base_fcurves = action_fcurves(base, owner=cam)
    for fcu in base_fcurves:
        if not (fcu.data_path or "").startswith("rotation_euler"):
            continue
        nf = fcurves.new(data_path=fcu.data_path, index=fcu.array_index)
        for k in sorted(fcu.keyframe_points, key=lambda k: k.co.x):
            nk = nf.keyframe_points.insert(k.co.x, k.co.y, options={'FAST'})
            nk.interpolation = k.interpolation
            try:
                nk.handle_left_type = k.handle_left_type
                nk.handle_right_type = k.handle_right_type
            except Exception:
                pass
        nf.update()
    return True


def _apply_recrot_smooth_simplify(curve, cam):
    ac = curve.autocam
    
    # Map 0-100% to internal values
    # Smoothing: 0-100 -> 0.0-10.0
    # Using a power curve to keep the useful range (Butterworth) wider: x^2.0
    sm_pct = float(getattr(ac, "recrot_smoothing", 0.0))
    sm = pow(sm_pct / 100.0, 2.0) * 10.0
    
    # Simplify: 0-100 -> 0.0-0.1 radians (approx 5.7 degrees)
    # Using a stronger power curve for finer control at low values: x^2.5
    eps_pct = float(getattr(ac, "recrot_simplify", 0.0))
    eps = pow(eps_pct / 100.0, 2.5) * 0.1

    if sm <= 0.0 and eps <= 0.0:
        return

    ad = getattr(cam, "animation_data", None)
    act = ad.action if (ad and ad.action) else None
    if not act:
        return
    fcurves = action_fcurves(act, owner=cam)

    for axis in (0, 1, 2):
        fcu = fcurves.find("rotation_euler", index=axis)
        if not fcu:
            continue

        kfs = sorted(fcu.keyframe_points, key=lambda k: k.co.x)
        frames = [float(k.co.x) for k in kfs]
        values = [float(k.co.y) for k in kfs]
        n = len(frames)
        if n < 3:
            continue

        values = _unwrap_euler(values)

        if sm > 0.0 and n >= 3:
            a, b = 1, n - 2
            if b >= a:
                seg = values[a:b+1]

                sm_filter = min(sm, 5.0)
                if sm_filter > 0.0 and len(seg) >= 2:
                    cutoff = _cutoff_from_slider(sm_filter)   # existing helper
                    seg = _butter_zero_phase_detrended(seg, cutoff_norm=cutoff)

                if sm > 5.0:
                    alpha = min(1.0, max(0.0, (sm - 5.0) / 5.0))

                    y0 = values[0]
                    y1 = values[n - 2]
                    x0 = frames[0]
                    x1 = frames[n - 2]
                    inv = 1.0 / (x1 - x0) if x1 != x0 else None

                    line_seg = []
                    for i in range(a, b + 1):
                        if inv is None:
                            line_seg.append(y0)
                        else:
                            t = (frames[i] - x0) * inv
                            line_seg.append(y0 + t * (y1 - y0))

                    seg = [(1.0 - alpha) * seg[i - a] + alpha * line_seg[i - a]
                           for i in range(a, b + 1)]

                values[a:b+1] = seg

        if eps > 0.0 and n > 3:
            frames, values = _simplify_flat_runs(frames, values, eps)
            frames, values = simplify_rdp(frames, values, eps)
            n = len(frames)

        fcu.keyframe_points.clear()
        for fr, val in zip(frames, values):
            k = fcu.keyframe_points.insert(fr, val, options={'FAST'})
            k.interpolation = 'BEZIER'
            try:
                k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'
            except Exception:
                pass
        fcu.update()


def _recrot_reapply_live(curve, context):
    cam = _recrot_cam(curve)
    if not cam:
        return

    ac = curve.autocam
    # smooth_strength and tol are read inside _apply_recrot_smooth_simplify

    base = _recrot_get_base_action(curve)
    ad = cam.animation_data
    src_name = ad.action.name if (ad and ad.action) else None
    if (not base) or (src_name and curve.get("_ac_recrot_base_source") != src_name):
        base = _recrot_make_base_from_current(curve, cam)
    if not base:
        return

    _recrot_restore_from_base(curve, cam)
    _apply_recrot_smooth_simplify(curve, cam)
    


    try:
        scene = context.scene
        scene.frame_set(scene.frame_current)
    except Exception:
        pass
