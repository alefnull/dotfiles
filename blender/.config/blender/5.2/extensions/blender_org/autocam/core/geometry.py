"""
Lightweight geometry helpers.

- rdp(): Ramer-Douglas-Peucker simplification on Vector point chains, using a squared-distance tolerance; preserves endpoints.

"""


from mathutils import Vector


# GEOMETRY HELPERS

def _dist_sq(p, a, b):
    seg = b - a
    L2 = seg.length_squared
    if L2 == 0:
        return (p - a).length_squared
    t = max(0.0, min(1.0, (p - a).dot(seg) / L2))
    proj = a + seg * t
    return (p - proj).length_squared


def rdp(pts, eps2):
    if len(pts) < 3:
        return pts[:]
    a, b = pts[0], pts[-1]
    maxd, idx = 0.0, 0
    for i, p in enumerate(pts[1:-1], 1):
        d2 = _dist_sq(p, a, b)
        if d2 > maxd:
            maxd, idx = d2, i
    if maxd > eps2:
        L = rdp(pts[: idx+1], eps2)
        R = rdp(pts[idx:],    eps2)
        return L[:-1] + R
    return [a, b]
