"""
Timing inheritance: compute and bake offset_factor keyframes from source camera timing.

This module provides functions to preserve the source camera's velocity profile
(pauses, accelerations) when generating an AutoCam rig.

- _compute_arc_distances(): compute cumulative arc lengths for a list of points
- _evaluate_camera_positions(): sample camera world positions at each frame
- _apply_inherited_timing(): bake per-frame offset_factor keys on the dolly
- _clear_inherited_timing(): remove inherited timing and revert to constant speed
- _store_timing_data(): persist timing info as JSON on the curve for later use

"""

import json
import bpy
from mathutils import Vector
from .fcurves import action_fcurves
from .path_follow import _fp_data_path, _ensure_follow_path_on_dolly


def _compute_arc_distances(points):
    """
    Compute cumulative arc-length distances for a list of points.
    
    Returns a list of distances where distances[i] is the cumulative
    arc length from points[0] to points[i].
    """
    if not points:
        return []
    distances = [0.0]
    for i in range(1, len(points)):
        distances.append(distances[-1] + (points[i] - points[i-1]).length)
    return distances


def _evaluate_camera_positions(camera, frame_start, frame_end, scene):
    """
    Evaluate camera world positions at each frame in range.
    
    This handles constraint-driven cameras, fcurve animation, and drivers.
    Returns dict mapping frame -> Vector world position.
    """
    orig_frame = scene.frame_current
    positions = {}
    
    # Temporarily unhide camera - hidden objects don't evaluate properly
    was_hidden_viewport = camera.hide_viewport
    was_hidden_render = camera.hide_render
    camera.hide_viewport = False
    camera.hide_render = False
    
    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        # Force depsgraph update and get evaluated camera
        deps = bpy.context.evaluated_depsgraph_get()
        eval_camera = camera.evaluated_get(deps)
        positions[frame] = eval_camera.matrix_world.to_translation().copy()
    
    # Restore hidden state
    camera.hide_viewport = was_hidden_viewport
    camera.hide_render = was_hidden_render
    
    scene.frame_set(orig_frame)
    return positions


def _get_curve_sample_points(curve):
    """
    Get high-resolution sample points from the curve in world space.
    
    Returns (verts, distances, total_length) where:
    - verts: list of Vector world positions
    - distances: cumulative arc distances
    - total_length: total arc length
    """
    print(f"AutoCam: _get_curve_sample_points called for {curve.name}")
    print(f"  Curve type: {curve.type}, data type: {type(curve.data)}")
    
    if not curve.data or not hasattr(curve.data, 'splines'):
        print("  ERROR: curve.data has no splines attribute")
        return [], [], 0.0
    
    print(f"  Number of splines: {len(curve.data.splines)}")
    if len(curve.data.splines) == 0:
        print("  ERROR: No splines in curve")
        return [], [], 0.0
    
    try:
        # Temporarily increase resolution for accurate sampling
        orig_res = [sp.resolution_u for sp in curve.data.splines]
        for sp in curve.data.splines:
            sp.resolution_u = 64
        
        # Force depsgraph update
        bpy.context.view_layer.update()
        
        deps = bpy.context.evaluated_depsgraph_get()
        eval_curve = curve.evaluated_get(deps)
        print(f"  Evaluated curve: {eval_curve.name}")
        
        mesh = eval_curve.to_mesh()
        print(f"  Mesh vertices: {len(mesh.vertices)}")
        
        if len(mesh.vertices) == 0:
            print("  ERROR: to_mesh() returned 0 vertices")
            eval_curve.to_mesh_clear()
            for sp, r in zip(curve.data.splines, orig_res):
                sp.resolution_u = r
            return [], [], 0.0
        
        verts = [curve.matrix_world @ v.co for v in mesh.vertices]
        eval_curve.to_mesh_clear()  # Proper cleanup for evaluated object mesh
        
        # Restore original resolution
        for sp, r in zip(curve.data.splines, orig_res):
            sp.resolution_u = r
            
    except Exception as e:
        print(f"  EXCEPTION in _get_curve_sample_points: {e}")
        import traceback
        traceback.print_exc()
        return [], [], 0.0
    
    if len(verts) < 2:
        print(f"  ERROR: Only {len(verts)} vertices, need at least 2")
        return [], [], 0.0
    
    # Compute arc distances
    distances = _compute_arc_distances(verts)
    total_length = distances[-1] if distances else 1.0
    
    print(f"  SUCCESS: {len(verts)} vertices, total length: {total_length:.2f}")
    return verts, distances, total_length


def _find_closest_param_in_samples(verts, distances, total_length, target_pos):
    """
    Find the offset_factor (0.0-1.0) closest to target_pos in pre-computed samples.
    """
    if not verts or total_length < 1e-9:
        return 0.0
    
    # Find vertex closest to target
    min_dist = float('inf')
    best_idx = 0
    for i, v in enumerate(verts):
        d = (v - target_pos).length
        if d < min_dist:
            min_dist = d
            best_idx = i
    
    # Return normalized parameter
    return distances[best_idx] / total_length


def _store_timing_data(curve, frame_to_offset):
    """
    Store timing data as JSON on the curve.
    
    frame_to_offset: dict mapping frame number -> offset_factor (0.0-1.0)
    """
    try:
        # Convert to list of [frame, offset] pairs for compact JSON
        data = [[int(f), float(o)] for f, o in sorted(frame_to_offset.items())]
        curve["autocam_timing_keys"] = json.dumps(data)
    except Exception:
        pass


def _load_timing_data(curve):
    """
    Load stored timing data from curve.
    
    Returns dict mapping frame -> offset_factor, or None if not found.
    """
    raw = curve.get("autocam_timing_keys")
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return {int(f): float(o) for f, o in data}
    except Exception:
        return None


def _get_camera_keyframe_frames(camera):
    """
    Get all unique keyframe frame numbers from camera's location animation.
    Returns sorted list of frame numbers.
    """
    frames = set()
    
    ad = getattr(camera, "animation_data", None)
    act = ad.action if (ad and ad.action) else None
    if not act:
        return []
    
    # Check all location fcurves (X, Y, Z)
    fcurves = action_fcurves(act, owner=camera)
    for fcu in fcurves:
        if 'location' in (fcu.data_path or ""):
            for kp in fcu.keyframe_points:
                frames.add(int(kp.co[0]))
    
    return sorted(frames)


def _get_keypoint_interpolation_info(camera, frame):
    """
    Get the interpolation type and handle info at a specific frame.
    Returns (interpolation, handle_left_type, handle_right_type) or None.
    """
    ad = getattr(camera, "animation_data", None)
    act = ad.action if (ad and ad.action) else None
    if not act:
        return None
    
    # Find keypoint at this frame in any location channel
    fcurves = action_fcurves(act, owner=camera)
    for fcu in fcurves:
        if 'location' in (fcu.data_path or ""):
            for kp in fcu.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:
                    return (kp.interpolation, kp.handle_left_type, kp.handle_right_type)
    
    return None


def _apply_inherited_timing(curve, dolly, frame_start, frame_end, context):
    """
    Bake offset_factor keyframes that match the source camera's timing.
    
    Uses the original samples stored during curve creation (before simplification)
    to compute exact arc-length offsets for each frame.
    """
    import json
    from mathutils import Vector
    
    con = _ensure_follow_path_on_dolly(curve)
    if not con:
        return False
    
    # Get source camera (just to verify it exists)
    src = getattr(curve.autocam, "camera", None)
    if not src or src.name not in bpy.data.objects:
        return False
    
    total_frames = frame_end - frame_start
    if total_frames <= 0:
        return False
    
    # Get the ORIGINAL samples stored during curve creation (before simplification)
    raw_samples = curve.get('autocam_samples_orig')
    if not raw_samples:
        print("AutoCam: No original samples found - using fallback")
        # Fallback: use spline control points
        raw_samples = None
    
    if raw_samples:
        try:
            samples_data = json.loads(raw_samples)
            points = [Vector(p) for p in samples_data]
        except Exception as e:
            print(f"AutoCam: Error loading original samples: {e}")
            points = None
    else:
        points = None
    
    # Fallback to spline control points if no stored samples
    if not points:
        if not curve.data.splines:
            print("AutoCam: Curve has no splines")
            return False
        spline = curve.data.splines[0]
        if spline.type == 'POLY':
            points = [curve.matrix_world @ p.co.to_3d() for p in spline.points]
        elif spline.type == 'BEZIER':
            points = [curve.matrix_world @ p.co for p in spline.bezier_points]
        else:
            points = [curve.matrix_world @ p.co.to_3d() for p in spline.points]
    
    num_samples = len(points)
    if num_samples < 2:
        print("AutoCam: Less than 2 sample points")
        return False
    
    print(f"AutoCam: Using {num_samples} original samples for {total_frames + 1} frames")
    
    # Compute cumulative arc length at each sample point
    arc_lengths = [0.0]
    for i in range(1, num_samples):
        segment_length = (points[i] - points[i-1]).length
        arc_lengths.append(arc_lengths[i-1] + segment_length)
    
    total_arc_length = arc_lengths[-1]
    if total_arc_length <= 0:
        print("AutoCam: Curve has zero length")
        return False
    
    # Normalize arc lengths to 0-1 range
    normalized_offsets = [al / total_arc_length for al in arc_lengths]
    
    # Map frame → sample index → normalized arc length
    # The samples are 1:1 with frames (recorded at each frame)
    frame_to_offset = {}
    
    print(f"AutoCam: Calculating timing for {total_frames + 1} frames...")
    
    for frame in range(frame_start, frame_end + 1):
        frame_idx = frame - frame_start
        
        if num_samples == total_frames + 1:
            # Perfect 1:1 mapping - each frame has its own sample
            offset = normalized_offsets[frame_idx]
        else:
            # Interpolate between sample points (shouldn't happen but just in case)
            t = frame_idx / total_frames
            sample_pos = t * (num_samples - 1)
            sample_lo = int(sample_pos)
            sample_hi = min(sample_lo + 1, num_samples - 1)
            frac = sample_pos - sample_lo
            offset = normalized_offsets[sample_lo] + frac * (normalized_offsets[sample_hi] - normalized_offsets[sample_lo])
        
        frame_to_offset[frame] = offset
    
    # Store timing data
    _store_timing_data(curve, frame_to_offset)
    
    # Bake keyframes on offset_factor
    data_path = _fp_data_path(con.name)
    
    for frame, offset in sorted(frame_to_offset.items()):
        con.offset_factor = offset
        dolly.keyframe_insert(data_path=data_path, frame=frame)
    
    # Set interpolation to LINEAR for exact matching
    ad = dolly.animation_data
    act = ad.action if (ad and ad.action) else None
    if act:
        fcurves = action_fcurves(act, owner=dolly)
        fcu = fcurves.find(data_path) if fcurves else None
        if fcu:
            for kp in fcu.keyframe_points:
                kp.interpolation = 'LINEAR'
            fcu.update()
    
    # Store base keys for live simplification
    _timing_make_base(curve, dolly)
    
    print(f"AutoCam: Timing inheritance complete - {len(frame_to_offset)} keyframes")
    print(f"  Original samples: {num_samples}, Frames: {total_frames + 1}")
    return True


def _simplify_timing_keys(curve, dolly, tolerance_pct):
    """
    Simplify timing keyframes using RDP algorithm (same as Match Recording).
    
    tolerance_pct: 0-100% slider value (higher = fewer keys)
    """
    from .filters import simplify_rdp, _simplify_flat_runs
    
    # Map 0-100% to epsilon (0.0-0.05 range for offset values)
    # Using power curve for finer control at low values
    eps = pow(tolerance_pct / 100.0, 2.0) * 0.05
    
    if eps <= 0:
        return 0  # No simplification
    
    # Find the follow path constraint
    con = None
    for c in dolly.constraints:
        if c.type == 'FOLLOW_PATH' and c.target == curve:
            con = c
            break
    if not con:
        return 0
    
    data_path = _fp_data_path(con.name)
    
    ad = dolly.animation_data
    act = ad.action if (ad and ad.action) else None
    if not act:
        return 0
    
    fcurves = action_fcurves(act, owner=dolly)
    fcu = fcurves.find(data_path) if fcurves else None
    if not fcu:
        return 0
    
    # Get current keyframes
    kfs = sorted(fcu.keyframe_points, key=lambda k: k.co.x)
    original_count = len(kfs)
    
    if original_count < 3:
        return 0
    
    frames = [float(k.co.x) for k in kfs]
    values = [float(k.co.y) for k in kfs]
    
    # Apply simplification (same as recrot.py)
    frames, values = _simplify_flat_runs(frames, values, eps)
    frames, values = simplify_rdp(frames, values, eps)
    
    new_count = len(frames)
    
    # Clear and rebuild
    fcu.keyframe_points.clear()
    for fr, val in zip(frames, values):
        k = fcu.keyframe_points.insert(fr, val, options={'FAST'})
        k.interpolation = 'BEZIER'
        try:
            k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'
        except Exception:
            pass
    fcu.update()
    
    return original_count - new_count


def _timing_make_base(curve, dolly):
    """Store current timing keys as base for live simplification."""
    con = None
    for c in dolly.constraints:
        if c.type == 'FOLLOW_PATH' and c.target == curve:
            con = c
            break
    if not con:
        return
    
    data_path = _fp_data_path(con.name)
    ad = dolly.animation_data
    act = ad.action if (ad and ad.action) else None
    if not act:
        return
    
    fcurves = action_fcurves(act, owner=dolly)
    fcu = fcurves.find(data_path) if fcurves else None
    if not fcu:
        return
    
    # Store keyframes as JSON
    import json
    keys = [(kp.co[0], kp.co[1]) for kp in fcu.keyframe_points]
    curve["_ac_timing_base_keys"] = json.dumps(keys)


def _timing_restore_from_base(curve, dolly):
    """Restore timing keys from base."""
    import json
    raw = curve.get("_ac_timing_base_keys")
    if not raw:
        return False
    
    try:
        keys = json.loads(raw)
    except Exception:
        return False
    
    if not keys:
        return False
    
    con = None
    for c in dolly.constraints:
        if c.type == 'FOLLOW_PATH' and c.target == curve:
            con = c
            break
    if not con:
        return False
    
    data_path = _fp_data_path(con.name)
    ad = dolly.animation_data
    act = ad.action if (ad and ad.action) else None
    if not act:
        return False
    
    fcurves = action_fcurves(act, owner=dolly)
    fcu = fcurves.find(data_path) if fcurves else None
    if not fcu:
        return False
    
    # Clear and restore
    fcu.keyframe_points.clear()
    for fr, val in keys:
        k = fcu.keyframe_points.insert(fr, val, options={'FAST'})
        k.interpolation = 'BEZIER'
        try:
            k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'
        except Exception:
            pass
    fcu.update()
    return True


def _timing_reapply_live(curve, context):
    """Live update: restore from base and apply current simplification value."""
    ac = curve.autocam
    dolly = getattr(ac, "dolly", None)
    if not dolly:
        return
    
    # Ensure base exists
    if not curve.get("_ac_timing_base_keys"):
        _timing_make_base(curve, dolly)
    
    # Restore from base
    if not _timing_restore_from_base(curve, dolly):
        return
    
    # Apply simplification
    simplify_pct = float(getattr(ac, "timing_simplify", 0.0))
    if simplify_pct > 0:
        _simplify_timing_keys(curve, dolly, simplify_pct)
    
    # Refresh viewport
    try:
        scene = context.scene
        scene.frame_set(scene.frame_current)
    except Exception:
        pass


def _store_user_keys(curve, dolly):
    """Store user's manual offset_factor keys before inheritance (for restore on clear)."""
    import json
    
    con = None
    for c in dolly.constraints:
        if c.type == 'FOLLOW_PATH' and c.target == curve:
            con = c
            break
    if not con:
        return
    
    data_path = _fp_data_path(con.name)
    ad = dolly.animation_data
    act = ad.action if (ad and ad.action) else None
    if not act:
        return
    
    fcurves = action_fcurves(act, owner=dolly)
    fcu = fcurves.find(data_path) if fcurves else None
    if not fcu or len(fcu.keyframe_points) < 1:
        return
    
    # Store keyframes as JSON (frame, value, interpolation, handle types)
    keys = []
    for kp in fcu.keyframe_points:
        keys.append({
            'frame': kp.co[0],
            'value': kp.co[1],
            'interp': kp.interpolation,
            'hl': kp.handle_left_type,
            'hr': kp.handle_right_type
        })
    curve["_ac_user_offset_keys"] = json.dumps(keys)


def _restore_user_keys(curve, dolly):
    """Restore user's manual offset_factor keys from before inheritance."""
    import json
    
    raw = curve.get("_ac_user_offset_keys")
    if not raw:
        return False
    
    try:
        keys = json.loads(raw)
    except Exception:
        return False
    
    if not keys:
        return False
    
    con = None
    for c in dolly.constraints:
        if c.type == 'FOLLOW_PATH' and c.target == curve:
            con = c
            break
    if not con:
        return False
    
    data_path = _fp_data_path(con.name)
    ad = dolly.animation_data
    act = ad.action if (ad and ad.action) else None
    if not act:
        return False
    
    fcurves = action_fcurves(act, owner=dolly)
    fcu = fcurves.find(data_path) if fcurves else None
    if not fcu:
        return False
    
    # Clear and restore
    fcu.keyframe_points.clear()
    for k in keys:
        kp = fcu.keyframe_points.insert(k['frame'], k['value'], options={'FAST'})
        kp.interpolation = k.get('interp', 'BEZIER')
        try:
            kp.handle_left_type = k.get('hl', 'AUTO_CLAMPED')
            kp.handle_right_type = k.get('hr', 'AUTO_CLAMPED')
        except Exception:
            pass
    fcu.update()
    
    # Clear stored keys after restore
    if "_ac_user_offset_keys" in curve:
        del curve["_ac_user_offset_keys"]
    
    return True


def _clear_inherited_timing(curve, dolly, frame_start, frame_end):
    """
    Clear inherited timing and restore user's original keys.
    
    If user had manual keys before inheritance, restores them.
    Otherwise, creates simple two-key linear traversal (0.0→1.0).
    """
    # Try to restore user's original keys first
    if _restore_user_keys(curve, dolly):
        # Successfully restored user keys
        pass
    else:
        # No stored user keys - create default 0→1
        con = None
        for c in dolly.constraints:
            if c.type == 'FOLLOW_PATH' and c.target == curve:
                con = c
                break
        if not con:
            return False
        
        data_path = _fp_data_path(con.name)
        ad = dolly.animation_data
        act = ad.action if (ad and ad.action) else None
        if act:
            fcurves = action_fcurves(act, owner=dolly)
            fcu = fcurves.find(data_path) if fcurves else None
            if fcu:
                try:
                    fcu.keyframe_points.clear()
                except Exception:
                    pass
        
        # Insert two keys for constant speed
        con.offset_factor = 0.0
        dolly.keyframe_insert(data_path=data_path, frame=frame_start)
        con.offset_factor = 1.0
        dolly.keyframe_insert(data_path=data_path, frame=frame_end)
        
        # Set BEZIER interpolation
        ad = dolly.animation_data
        act = ad.action if (ad and ad.action) else None
        if act:
            fcurves = action_fcurves(act, owner=dolly)
            fcu = fcurves.find(data_path) if fcurves else None
            if fcu:
                for kp in fcu.keyframe_points:
                    kp.interpolation = 'BEZIER'
                    try:
                        kp.handle_left_type = 'AUTO_CLAMPED'
                        kp.handle_right_type = 'AUTO_CLAMPED'
                    except Exception:
                        pass
                fcu.update()
    
    # Clear stored timing data
    if "autocam_timing_keys" in curve:
        del curve["autocam_timing_keys"]
    if "_ac_timing_base_keys" in curve:
        del curve["_ac_timing_base_keys"]
    
    curve.autocam.timing_inherited = False
    curve.autocam.timing_simplify = 0.0  # Reset simplify slider
    return True


def _has_location_animation(camera):
    """
    Check if camera has location animation (keyframes, drivers, or constraint).
    
    Returns True if the camera has meaningful location animation to inherit.
    """
    if not camera:
        return False
    
    # Check for location fcurves
    ad = getattr(camera, "animation_data", None)
    act = ad.action if (ad and ad.action) else None
    if act:
        fcurves = action_fcurves(act, owner=camera)
        for fcu in fcurves:
            if 'location' in (fcu.data_path or ""):
                if len(fcu.keyframe_points) > 1:
                    return True
    
    # Check for location drivers
    if ad and ad.drivers:
        for drv in ad.drivers:
            if 'location' in (drv.data_path or ""):
                return True
    
    # Check for constraints that affect location
    for con in camera.constraints:
        if con.type in {'COPY_LOCATION', 'FOLLOW_PATH', 'CHILD_OF', 'ARMATURE'}:
            if con.mute is False and con.influence > 0:
                return True
    
    return False
