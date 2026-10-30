"""Pure-Python 2D helpers for tracing poster shapes.

Shapes are described in poster pixel space (origin top-left, y down) as a
list of vertices. A vertex can be a plain ``(x, y)`` or a rounded corner
``(x, y, t_in, t_out[, k])``: the sharp corner at (x, y) is replaced by a cubic
curve that leaves the incoming edge ``t_in`` px before the corner and joins
the outgoing edge ``t_out`` px after it; ``k`` sets how full the curve is. Unequal tangents give the slightly
elliptical, hand-drawn corners typical of mid-century lettering.
"""

import math

CORNER_SEGMENTS = 24
CORNER_K = 0.55  # 0.55 ~ circular arc; lower = flatter, higher = tighter


def line_intersection(p1, p2, p3, p4):
    """Intersection of infinite lines p1-p2 and p3-p4."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    a = x1 * y2 - y1 * x2
    b = x3 * y4 - y3 * x4
    return ((a * (x3 - x4) - (x1 - x2) * b) / d, (a * (y3 - y4) - (y1 - y2) * b) / d)


def x_at_y(p1, p2, y):
    """x where the line p1-p2 crosses height y."""
    (x1, y1), (x2, y2) = p1, p2
    return x1 + (x2 - x1) * (y - y1) / (y2 - y1)


def _toward(a, b, dist):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    return (a[0] + dx / n * dist, a[1] + dy / n * dist)


def _cubic(p0, p1, p2, p3, steps):
    out = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        out.append((
            u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
        ))
    return out


def resolve(spec, k=CORNER_K, segments=CORNER_SEGMENTS):
    """Expand rounded-corner vertices into a flat list of points."""
    pts = []
    n = len(spec)
    for i, v in enumerate(spec):
        if len(v) == 2:
            pts.append((float(v[0]), float(v[1])))
            continue
        x, y, t_in, t_out = v[:4]
        kk = v[4] if len(v) > 4 else k
        corner = (x, y)
        prev = spec[i - 1][:2]
        nxt = spec[(i + 1) % n][:2]
        a = _toward(corner, prev, t_in)
        b = _toward(corner, nxt, t_out)
        c1 = (a[0] + (x - a[0]) * kk, a[1] + (y - a[1]) * kk)
        c2 = (b[0] + (x - b[0]) * kk, b[1] + (y - b[1]) * kk)
        pts.extend(_cubic(a, c1, c2, b, segments))
    return pts


def signed_area(pts):
    return 0.5 * sum(
        pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
        for i in range(len(pts))
    )
