"""
Dynamic mode engine: arc-length caching and per-frame dolly updates.

 - _build_arc_table(): samples the evaluated curve (temp high resolution), computes cumulative arc distances/fractions and stores JSON copies on the curve alongside cached verts.
 - _ensure_arc_cache(): ensures cached arc data is present (rebuilds or loads JSON, upgrades legacy caches).
 - _update_offset(): advances/rewinds traversal distance each frame using Scene frame, curve start/end, and a distance-per-second speed value (property or fcurve).
 - _apply_dolly_transform(): interpolates along cached verts by the current normalized distance and orients the dolly using track-quat in the curve's world space.
- ac_frame_change_handler(): persistent frame_change_pre handler that updates all registered AutoCam rigs set to Dynamic mode each frame.
- register()/unregister(): add/remove the handler.

"""


import json
import bisect
import bpy
from mathutils import Vector
from bpy.app.handlers import persistent
from .core import registry as _reg
from .core.props import prefs, ROOT_ID
from .core.fcurves import action_fcurves

_ARC_CACHE: dict[int, dict] = {}
_SPEED_UNITS_KEY = "_ac_speed_units"
_SPEED_UNITS_CURRENT = "DIST_PER_SEC"
_SPEED_UNITS_LEGACY_FRAME = "DISTANCE"


def _arc_ptr(curve) -> int:
    try:
        return curve.as_pointer()
    except Exception:
        return id(curve)


def _scene_fps(scene=None) -> float:
    try:
        render = (scene or bpy.context.scene).render
        base = getattr(render, "fps_base", 1.0) or 1.0
        fps = float(render.fps) / float(base)
        return fps if fps > 1e-6 else 24.0
    except Exception:
        return 24.0


def _sync_distance_state(curve, *, total_length: float) -> None:
    """Ensure legacy rigs upgrade to distance-based traversal and stay in range."""
    total_length = float(total_length) if total_length else 0.0
    safe_total = total_length if total_length > 1e-9 else 0.0

    if "ac_arc_dist" not in curve:
        legacy_offset = float(curve.get("ac_offset", 0.0))
        legacy_offset = max(0.0, min(1.0, legacy_offset))
        curve["ac_arc_dist"] = legacy_offset * safe_total

    dist = float(curve.get("ac_arc_dist", 0.0))
    if safe_total and dist > safe_total:
        dist = safe_total
    elif dist < 0.0:
        dist = 0.0
    curve["ac_arc_dist"] = dist

    curve["_ac_cache_length"] = safe_total
    curve["ac_offset"] = (dist / safe_total) if safe_total else 0.0


def _maybe_upgrade_speed_units(curve, *, total_length: float, scene=None) -> None:
    """Convert legacy speed values to units/second."""
    ptr = _arc_ptr(curve)
    cache = _ARC_CACHE.setdefault(ptr, {})
    units_prop = curve.get(_SPEED_UNITS_KEY)
    cache_units = cache.get("units")

    if cache_units == _SPEED_UNITS_CURRENT and units_prop != _SPEED_UNITS_CURRENT:
        curve[_SPEED_UNITS_KEY] = _SPEED_UNITS_CURRENT
        return
    if units_prop == _SPEED_UNITS_CURRENT:
        cache["units"] = _SPEED_UNITS_CURRENT
        return

    fps = _scene_fps(scene)
    ac = getattr(curve, "autocam", None)
    if not ac:
        curve[_SPEED_UNITS_KEY] = _SPEED_UNITS_CURRENT
        cache["units"] = _SPEED_UNITS_CURRENT
        return

    try:
        start, end = _curve_range(curve)
        duration = max(1.0, float(end - start))
        length = float(total_length)

        units = str(units_prop or "")
        if units == _SPEED_UNITS_LEGACY_FRAME:
            factor = fps
        else:
            if length <= 0.0:
                curve[_SPEED_UNITS_KEY] = _SPEED_UNITS_CURRENT
                cache["units"] = _SPEED_UNITS_CURRENT
                return
            factor = (length / duration) * fps

        if abs(factor - 1.0) > 1e-6:
            ac.speed = float(ac.speed) * factor
            ad = curve.animation_data
            act = ad.action if (ad and ad.action) else None
            fcurves = action_fcurves(act, owner=curve) if act else None
            fcu = fcurves.find("autocam.speed") if fcurves else None
            if fcu and len(fcu.keyframe_points):
                for kp in fcu.keyframe_points:
                    kp.co.y *= factor
                    kp.handle_left.y *= factor
                    kp.handle_right.y *= factor
                fcu.update()
    except Exception:
        pass

    curve[_SPEED_UNITS_KEY] = _SPEED_UNITS_CURRENT
    cache["units"] = _SPEED_UNITS_CURRENT


def _sample_speed_value(curve, fcurve, frame: int) -> float:
    if fcurve:
        try:
            return float(fcurve.evaluate(frame))
        except Exception:
            pass
    ac = getattr(curve, "autocam", None)
    return float(getattr(ac, "speed", 0.0)) if ac else 0.0


def _speed_units(curve) -> str:
    return str(curve.get(_SPEED_UNITS_KEY, _SPEED_UNITS_CURRENT))


def _speed_to_distance(speed_value: float, *,
                       total_length: float, duration: float,
                       units: str, fps: float) -> float:
    if units == _SPEED_UNITS_CURRENT:
        return float(speed_value) / max(1e-6, fps)
    if units == _SPEED_UNITS_LEGACY_FRAME:
        return float(speed_value)
    if duration <= 0.0:
        return 0.0
    return float(speed_value) * ((float(total_length) / duration) / max(1e-6, fps))


def _build_arc_table(curve, samples=500):
    """
    Builds a lookup table for arc-length parameterization.
    
    This allows us to move the dolly at a constant speed along the curve regardless of 
    control point density. We sample the curve at high resolution, calculate cumulative 
    distance, and store normalized fractions (0.0-1.0) mapped to cumulative distance.
    
    Data is stored as JSON strings on the curve object to persist across sessions 
    without needing a custom property group for large arrays.
    """

    fp_parts = [s.type for s in curve.data.splines]
    for s in curve.data.splines:
        if s.type == 'BEZIER':
            for bp in s.bezier_points:
                fp_parts.extend((
                    *bp.co, *bp.handle_left, *bp.handle_right))
        else:
            for p in s.points:
                fp_parts.extend(p.co)

    fp_tuple = tuple(round(v, 6) if isinstance(v, (int, float)) else v
                     for v in fp_parts)
    fp_hash = str(hash(fp_tuple))

    if curve.get("_arc_fp") == fp_hash:
        return
    curve["_arc_fp"] = fp_hash

    deps = bpy.context.evaluated_depsgraph_get()
    eval_curve = curve.evaluated_get(deps)

    orig_res = [sp.resolution_u for sp in curve.data.splines]
    for sp in curve.data.splines:
        sp.resolution_u = 64

    mesh = eval_curve.to_mesh()
    verts = [v.co.copy() for v in mesh.vertices]
    try:
        bpy.data.meshes.remove(mesh, do_unlink=True)
    except RuntimeError:
        pass

    for sp, r in zip(curve.data.splines, orig_res):
        sp.resolution_u = r

    cumdist = [0.0]
    for i in range(1, len(verts)):
        cumdist.append(cumdist[-1] + (verts[i] - verts[i - 1]).length)

    total = cumdist[-1] if cumdist else 0.0
    safe_total = total if total > 1e-9 else 1.0
    fracs = [d / safe_total for d in cumdist]

    curve["_arc_frac"] = json.dumps(fracs)
    curve["_arc_cumdist"] = json.dumps(cumdist)
    curve["_arc_verts"] = json.dumps([tuple(v) for v in verts])
    curve["_arc_total"] = float(total)

    _sync_distance_state(curve, total_length=total)
    _maybe_upgrade_speed_units(curve, total_length=total)

    ptr = _arc_ptr(curve)
    _ARC_CACHE[ptr] = {
        "fracs": fracs,
        "cumdist": cumdist,
        "verts": verts,
        "total": total,
        "units": str(curve.get(_SPEED_UNITS_KEY, "")),
    }


# helper utilities

@persistent
def ac_seed_bake_defaults_on_load(_dummy):
    # Local import to avoid circulars
    p = prefs()
    if not p:
        return

    # Safe to write here (post-load, not UI draw)
    for sc in bpy.data.scenes:
        if sc.get("_ac_bake_seeded"):
            continue
        s = sc.autocam_bake
        s.step = p.default_bake_step
        s.dof_mode = p.default_bake_dof
        s.name_suffix = p.default_bake_suffix
        s.replace_scene_camera = p.default_bake_set_active
        sc["_ac_bake_seeded"] = True


def _ensure_arc_cache(curve):
    """Ensure cached arc-length data is available for *curve*."""
    _build_arc_table(curve)
    ptr = _arc_ptr(curve)
    data = _ARC_CACHE.get(ptr)
    if data:
        return data

    try:
        fracs = json.loads(curve["_arc_frac"])
        cumdist = json.loads(curve.get("_arc_cumdist", "[]"))
        verts = [Vector(v) for v in json.loads(curve["_arc_verts"])]
        total = float(curve.get("_arc_total", 0.0))
    except Exception:
        _build_arc_table(curve)
        return _ARC_CACHE[_arc_ptr(curve)]

    if not cumdist or len(cumdist) != len(fracs):
        safe_total = float(total) if total else 1.0
        cumdist = [f * safe_total for f in fracs]

    data = {
        "fracs": fracs,
        "cumdist": cumdist,
        "verts": verts,
        "total": float(total),
        "units": str(curve.get(_SPEED_UNITS_KEY, "")),
    }
    _ARC_CACHE[ptr] = data
    _sync_distance_state(curve, total_length=data["total"])
    _maybe_upgrade_speed_units(curve, total_length=data["total"])
    return data


def _find_dolly(curve):
    """Return the dolly object following *curve* if it exists."""
    dolly = curve.autocam.dolly
    if dolly is None or dolly.name not in bpy.data.objects:
        dolly = next(
            (o for o in bpy.data.objects
             if getattr(o, "autocam", None) and o.autocam.curve == curve),
            None,
        )
    return dolly


def _accumulate_distance(curve, fcurve, frame_from: int, frame_to: int,
                         *, total_length: float, duration: float,
                         units: str, fps: float) -> float:
    """Integrate speed between ``frame_from`` (exclusive) and ``frame_to`` (inclusive)."""
    if frame_from == frame_to or total_length <= 0.0:
        return 0.0

    step = 1 if frame_to > frame_from else -1
    dist = 0.0
    frame = frame_from
    while frame != frame_to:
        next_frame = frame + step
        sample_frame = next_frame if step > 0 else frame
        speed_val = _sample_speed_value(curve, fcurve, sample_frame)
        dist += step * _speed_to_distance(
            speed_val, total_length=total_length,
            duration=duration, units=units, fps=fps)
        frame = next_frame
    return dist


def _recompute_distance_from_start(curve, fcurve, target_frame: int,
                                   *, start_frame: int, total_length: float,
                                   duration: float, units: str, fps: float) -> float:
    if target_frame <= start_frame:
        return 0.0
    dist = 0.0
    frame = start_frame
    while frame < target_frame:
        frame += 1
        speed_val = _sample_speed_value(curve, fcurve, frame)
        dist += _speed_to_distance(
            speed_val, total_length=total_length,
            duration=duration, units=units, fps=fps)
    return dist


def _update_offset(curve, scene):
    """
    Update curve's traversal distance for the current *scene* frame.
    
    This function handles the 'Dynamic' mode logic:
    1. Determines the time delta (or frame jump) since the last update.
    2. Samples the speed property (or fcurve) at the current frame.
    3. Integrates speed * delta_time to get distance traveled.
    4. Updates the 'ac_arc_dist' property which drives the dolly position.
    
    It handles scrubbing (recomputing from start on large jumps) vs playback (accumulating).
    """
    start = int(curve.get("autocam.frame_start", 1))
    end = int(curve.get("autocam.frame_end", 250))
    frame = int(scene.frame_current)
    if end <= start:
        curve["ac_arc_dist"] = 0.0
        curve["ac_offset"] = 0.0
        curve["ac_last_frame"] = frame
        return None
    duration = float(end - start)

    data = _ensure_arc_cache(curve)
    total_length = float(data.get("total", 0.0))
    fps = _scene_fps(scene)
    _maybe_upgrade_speed_units(curve, total_length=total_length, scene=scene)
    units = _speed_units(curve)

    if total_length <= 0.0:
        curve["ac_arc_dist"] = 0.0
        curve["ac_offset"] = 0.0
        curve["ac_last_frame"] = frame
        return None

    fcurve = None
    ad = curve.animation_data
    act = ad.action if (ad and ad.action) else None
    if act:
        fcurves = action_fcurves(act, owner=curve)
        fcurve = fcurves.find("autocam.speed") if fcurves else None

    if "ac_last_frame" not in curve:
        curve["ac_last_frame"] = frame

    last_frame = int(curve.get("ac_last_frame", start))
    dist = float(curve.get("ac_arc_dist", 0.0))
    revision = int(curve.get("_ac_speed_revision", 0))
    last_revision = int(curve.get("_ac_speed_revision_applied", -1))
    if revision != last_revision:
        curve["_ac_speed_revision_applied"] = revision
    else:
        curve["_ac_speed_revision_applied"] = revision

    if frame <= start:
        dist = 0.0
        last_frame = frame
    else:
        large_jump = abs(frame - last_frame) > max(24, int(duration))
        if frame < last_frame or large_jump:
            dist = _recompute_distance_from_start(
                curve, fcurve, frame, start_frame=start,
                total_length=total_length, duration=duration,
                units=units, fps=fps)
        else:
            dist += _accumulate_distance(
                curve, fcurve, last_frame, frame,
                total_length=total_length, duration=duration,
                units=units, fps=fps)
        last_frame = frame

    dist = max(0.0, min(total_length, dist))
    curve["ac_arc_dist"] = dist
    curve["ac_last_frame"] = last_frame
    curve["_ac_speed_revision_applied"] = revision
    curve["ac_offset"] = dist / total_length
    return dist


def _apply_dolly_transform(curve, dolly, deps):
    """Position *dolly* along *curve* using cached arc data."""
    data = _ARC_CACHE.get(_arc_ptr(curve))
    if not data:
        return

    total = float(data.get("total", 0.0))
    dist = float(curve.get("ac_arc_dist", 0.0))
    offset = (dist / total) if total > 1e-9 else 0.0
    offset = max(0.0, min(1.0, offset))
    curve["ac_offset"] = offset

    fracs = data.get("fracs") or [0.0, 1.0]
    verts = data.get("verts") or []
    if len(fracs) < 2 or len(verts) < 2:
        return

    idx = bisect.bisect_left(fracs, offset)
    idx = min(max(idx, 1), len(fracs) - 1)

    f0, f1 = fracs[idx - 1], fracs[idx]
    u = (offset - f0) / (f1 - f0)
    p0, p1 = verts[idx - 1], verts[idx]

    co = p0.lerp(p1, u)
    tangent = (p1 - p0).normalized()

    curve_eval = curve.evaluated_get(deps)
    dolly.location = curve_eval.matrix_world @ co
    rot = tangent.to_track_quat('-Z', 'Y')
    dolly.rotation_euler = (
        curve_eval.matrix_world.to_quaternion() @ rot
    ).to_euler()


@persistent
def ac_frame_change_handler(scene):

    deps = bpy.context.evaluated_depsgraph_get()

    for curve in _reg.resolve_all():
        ac = getattr(curve, "autocam", None)
        if not ac or not getattr(ac, "rig_built", False):
            continue
        if getattr(ac, "mode", "DYNAMIC") != "DYNAMIC":
            continue

        dolly = _find_dolly(curve)
        if not dolly:
            continue

        if _update_offset(curve, scene) is None:
            continue

        _ensure_arc_cache(curve)
        _apply_dolly_transform(curve, dolly, deps)


@persistent
def ac_seed_registry_on_load(_dummy):
    _reg.seed_from_scene()
    # Fallback for older rigs that were never stamped:
    if not _reg.resolve_all():
        for o in bpy.data.objects:
            if o.type == 'CURVE':
                ac = getattr(o, "autocam", None)
                # your rigs already mark these:
                if ac and getattr(ac, "rig_built", False):
                    _reg.add(o)


def _remove_handlers_by_name(container, func_name: str):
    # Remove *all* callbacks with this name (handles hot-reload creating new function objects)
    for cb in list(container):
        try:
            if getattr(cb, "__name__", "") == func_name:
                container.remove(cb)
        except Exception:
            pass


def register():
    _remove_handlers_by_name(
        bpy.app.handlers.frame_change_pre, "ac_frame_change_handler")
    _remove_handlers_by_name(bpy.app.handlers.load_post,
                             "ac_seed_bake_defaults_on_load")
    _remove_handlers_by_name(bpy.app.handlers.load_post,
                             "ac_seed_registry_on_load")

    if ac_frame_change_handler not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(ac_frame_change_handler)
    if ac_seed_bake_defaults_on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(ac_seed_bake_defaults_on_load)
    if ac_seed_registry_on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(ac_seed_registry_on_load)


def unregister():
    if ac_frame_change_handler in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(ac_frame_change_handler)
    if ac_seed_bake_defaults_on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(ac_seed_bake_defaults_on_load)
    if ac_seed_registry_on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(ac_seed_registry_on_load)
