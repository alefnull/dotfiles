"""
Utilities to create/refresh a Blender CURVE object for AutoCam paths.

- _ensure_curve(): reuse or create a 3D path curve, clear splines, enable path evaluation.
- build_xyz(): populate the curve from points.
- BUILDERS: mapping from curve type - builder function.

"""

import bpy


# CURVE BUILDERS


def _ensure_curve(ob):
    if ob and ob.type == "CURVE":
        cu = ob.data
    else:
        cu = bpy.data.curves.new("AutoCamPath", "CURVE")
        cu.dimensions = "3D"
        ob = bpy.data.objects.new("AutoCamPath", cu)
        bpy.context.collection.objects.link(ob)
    cu.animation_data_clear()
    cu.use_path = True
    # clamp only exists in 2.90+ (skip if not present)
    if hasattr(cu, "use_path_clamp"):
        cu.use_path_clamp = True
    cu.splines.clear()

    return ob, cu


def build_poly(ob, pts):
    ob, cu = _ensure_curve(ob)
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts)-1)
    for p, v in zip(sp.points, pts):
        p.co = (*v, 1)
    return ob


def build_bezier(ob, pts):
    ob, cu = _ensure_curve(ob)
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts)-1)
    for bp, v in zip(sp.bezier_points, pts):
        bp.co = v
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    return ob


def build_nurbs(ob, pts):
    ob, cu = _ensure_curve(ob)
    sp = cu.splines.new("NURBS")
    sp.points.add(len(pts)-1)
    for p, v in zip(sp.points, pts):
        p.co = (*v, 1)
    sp.order_u = min(4, len(pts))
    sp.use_endpoint_u = True
    return ob


BUILDERS = {
    "POLY":   build_poly,
    "BEZIER": build_bezier,
    "NURBS":  build_nurbs,
}


__all__ = ("BUILDERS",)
