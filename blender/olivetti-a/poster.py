"""Olivetti "De A à Z" poster (c. 1950s) traced as overprinted ink layers.

All coordinates are in pixels of the 1577 x 2000 reference scan
(origin top-left, y down). Each shape is one flat ink layer; where layers
overlap the poster shows the overprint mix, which the coloured acrylic
reproduces physically.

Per shape:
  ink    key into INKS
  z      distance (m) from the paper to the back face of the slab
  depth  slab thickness (m)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from shapes2d import line_intersection as cross, x_at_y  # noqa: E402

W, H = 1577, 2000

# Construction lines of the two giant letters
LA = ((690, 0), (300, 1126))      # left stroke of the "A"
RA = ((895, 0), (1320, 1242))     # right stroke of the "A"
L1 = ((1190, 186), (300, 1126))   # blue hypotenuse / cream band, upper edge
L2 = ((1577, 198), (375, 1452))   # cream band, lower edge
Z_INNER = ((300, 300), (180, 517))  # inner diagonal of the red "Z"
BAR_L = ((443, 1224), (409, 1340))
BAR_R = ((1006, 1224), (1042, 1340))

TOP_BAR_Y = 186
FOOT_Y = 1452

la_top = (x_at_y(*LA, TOP_BAR_Y), TOP_BAR_Y)
la_l1 = cross(*LA, *L1)
ra_l2 = cross(*RA, *L2)
z_corner = cross((0, TOP_BAR_Y), (1, TOP_BAR_Y), *Z_INNER)
z_foot = (x_at_y(*Z_INNER, 517), 517)
l1_left = (0, L1[1][1] + (L1[1][1] - L1[0][1]) / (L1[1][0] - L1[0][0]) * (0 - L1[1][0]))

INKS = {
    # sRGB sampled from the scan
    "red": (0.91, 0.24, 0.13),
    "blue": (0.02, 0.74, 0.93),
    "green": (0.01, 0.70, 0.28),
    "yellow": (0.99, 0.78, 0.05),
    "black": (0.08, 0.08, 0.09),
    "brown": (0.20, 0.10, 0.08),
}
PAPER = (0.97, 0.935, 0.87)

SHAPES = {
    # --- back plane: the black ink, glossy and close to the paper
    "black_corner": dict(ink="brown", z=0.010, depth=0.012,
                         pts=[(0, 0), (285, 0), (0, 500)]),
    "black_left": dict(ink="black", z=0.010, depth=0.012,
                       pts=[(0, 517), z_foot, (*z_corner, 129, 113), la_top, la_l1, l1_left]),
    "black_right": dict(ink="black", z=0.010, depth=0.012,
                        pts=[(W, 198), ra_l2, (1320, 1242), (1387, 1125), (W, 1125)]),

    # --- red "Z" sweeping in from the top left
    "red_z": dict(ink="red", z=0.09, depth=0.03,
                  pts=[(285, 0), (x_at_y(*LA, 0), 0), la_top, (*z_corner, 113, 129),
                       z_foot, (0, 517), (0, 500)]),
    # --- the big "A": blue left half, red feet
    "blue_a": dict(ink="blue", z=0.20, depth=0.03,
                   pts=[la_top, (1190, TOP_BAR_Y), la_l1]),
    "red_foot_left": dict(ink="red", z=0.13, depth=0.03,
                          pts=[la_l1, (x_at_y(*LA, 1447), 1447, 160, 139), (0, 1447), l1_left]),
    "red_foot_right": dict(ink="red", z=0.16, depth=0.03,
                           pts=[ra_l2, (1320, 1242), (1228, FOOT_Y, 225, 235, 0.72), (375, FOOT_Y)]),
    "green_top": dict(ink="green", z=0.32, depth=0.03,
                      pts=[(895, 0), (W, 0), (W, 198), ra_l2]),
    # --- the counter: a yellow triangle floating furthest out
    "yellow_counter": dict(ink="yellow", z=0.46, depth=0.04,
                           pts=[(728, 405), (948, 1055), (502, 1055)]),
    # --- the green base: bar, stem and the next letter's foot
    "green_bar": dict(ink="green", z=0.58, depth=0.04,
                      pts=[BAR_L[0], BAR_R[0], (x_at_y(*BAR_R, 1450), 1450, 115, 116),
                           (x_at_y(*BAR_L, 1450), 1450, 95, 115)]),
    "green_stem": dict(ink="green", z=0.28, depth=0.04,
                       pts=[(555, 1450), (895, 1450), (895, 1618), (555, 1618)]),
    "green_next": dict(ink="green", z=0.40, depth=0.03,
                       pts=[(1387, 1125), (W, 1125), (W, FOOT_Y), (1325, FOOT_Y, 225, 200),
                            (1320, 1242)]),
    "yellow_next": dict(ink="yellow", z=0.24, depth=0.03,
                        pts=[(W, 1130), (W, 1618), (1296, 1618), (1424, FOOT_Y)]),
}

LOGO = dict(text="olivetti", x=190, baseline=1702, size=60, width=250, ink="black")
BODY = dict(
    x=556, first_baseline=1681, leading=28.5, size=24, ink="black",
    lines=[
        "De “A” à “Z”,",
        "la gamme entière des lettres",
        "de l’alphabet donne vie",
        "et parole à toute pensée.",
        "Ainsi la gamme",
        "des machines Olivetti",
        "résoud tous les problèmes",
        "fondamentaux",
        "du travail de bureau",
        "moderne: pour écrire,",
        "calculer, administrer.",
    ],
)

# Alternative takes: per-shape overrides laid over SHAPES (build.py --variant).
# finish: clear | frosted | resin | lacquer | card   (see acrylic_poster.FINISHES)
VARIANTS = {
    # mixed media: the black becomes deep matte blocks, the Z a chunky
    # lacquered extrusion, the counter a thick cast-resin wedge, and the
    # green base grows straight out of the paper as solid card
    "mixed": {
        "black_corner": dict(finish="card", depth=0.07, bevel=0.004),
        "black_left": dict(finish="card", depth=0.07, bevel=0.004),
        "black_right": dict(finish="card", depth=0.07, bevel=0.004),
        "red_z": dict(finish="lacquer", z=0.10, depth=0.10, bevel=0.012),
        "red_foot_left": dict(finish="lacquer", z=0.10, depth=0.06, bevel=0.010),
        "red_foot_right": dict(finish="frosted"),
        "green_top": dict(finish="frosted"),
        "yellow_counter": dict(finish="resin", z=0.34, depth=0.18, bevel=0.008),
        "green_bar": dict(finish="resin", z=0.50, depth=0.10, bevel=0.010),
        "green_stem": dict(finish="card", z=0.0, depth=0.30, bevel=0.006),
        "yellow_next": dict(finish="card", z=0.0, depth=0.14, bevel=0.006),
    },
}
