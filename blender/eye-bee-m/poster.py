"""Paul Rand's Eye-Bee-M poster (1981), reinterpreted with idealised geometry.

Coordinates are pixels of the poster as seen in the reference image
(568 x 852, origin top-left, y down). Where the reference is too small to
trace, the elements are rebuilt from their evident geometry: true circles,
an almond from two arcs, a crescent from two arcs, a slab-serif M cut into
eight equal stripes.
"""

W, H = 568, 852

EYE = dict(x0=22, x1=175, cy=390, half_h=53,        # almond: two arcs meeting at the corners
           iris=(98, 390, 46), pupil=17)
BROW = dict(x0=24, x1=176, base_y=346, outer_peak=284, inner_peak=306)
BEE = dict(cx=285, top=342, bottom=446, half_w=28,
           bands=["yellow", "black", "yellow", "black", "yellow", "black", "yellow"],
           eyes=[(271, 327, 14), (299, 327, 14)],
           wing=dict(root=(262, 390), tip=(196, 405), width=44))
M = dict(x0=388, x1=542, top=300, bottom=438, stripes=8)

INKS = {
    "white": (0.97, 0.97, 0.95),
    "tan": (0.85, 0.71, 0.57),
    "black": (0.03, 0.03, 0.035),
    "brown": (0.70, 0.36, 0.22),
    "yellow": (0.98, 0.80, 0.32),
    "pink": (0.97, 0.66, 0.74),
    "green": (0.20, 0.50, 0.22),
    "blue": (0.47, 0.56, 0.92),
}
