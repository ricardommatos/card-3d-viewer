"""IBM 1418 Optical Character Reader poster, reinterpreted as a pin field.

Coordinates are pixels of the poster as seen in the reference image
(783 x 892, origin top-left, y down), traced by eye.

Technique: the "Watch" texture (textures.dev/s/watch) in 3D. The whole
poster is a grid of pins; the white dot-matrix "1418" pins stand tall in
white ceramic, and an "eye" — the optical reader — swells, raises and tilts
the pins around it with Watch's falloff curve. The slab-serif IBM letters
float above as thick cast resin, pierced by the dot-matrix pins.
"""

W, H = 783, 892

# dot grid: matches the poster's dot-matrix pitch (wider rows than columns)
PITCH_X, PITCH_Y = 29.3, 44.1
X0, Y0 = 23, 366          # first column / the top row of "1418"
COLS = range(0, 26)
ROWS = range(-8, 12)

# "1418" as the poster sets it: 7 rows, '#' = white dot. Each glyph starts at
# a grid column (the poster's glyph gaps are a touch wider than the pitch).
GLYPHS = [
    (0, ["####.",
         "..##.",
         "..##.",
         "..##.",
         "..##.",
         ".###.",
         "#####"]),
    (5, ["...##...",
         "..##....",
         ".##..##.",
         "###.###.",
         "########",
         ".....##.",
         ".....##."]),
    (13, ["####.",
          "..##.",
          "..##.",
          "..##.",
          "..##.",
          ".###.",
          "#####"]),
    (18, [".#####.",
          "##...##",
          "###.###",
          "#######",
          "##...##",
          "##...##",
          ".#####."]),
]

# where the reader's eye rests (poster px)
EYE = (470, 560)

# Watch's dot sizes by distance from the eye, in cells (px of a 26.08 pitch)
WATCH_SIZES = [23.6, 22.8, 21.65, 19.77, 16.95, 11.3, 9.4, 7.5, 5.6, 3.77]
WATCH_PITCH = 26.08

LETTERS = [
    # glyph, ink, box (x0, x1) in px; caps run from CAP_TOP to BASELINE
    ("I", "blue", (13, 143)),
    ("B", "green", (170, 403)),
    ("M", "red", (423, 753)),
]
CAP_TOP, BASELINE = 175, 467

INKS = {
    "blue": (0.10, 0.62, 0.86),
    "green": (0.10, 0.62, 0.30),
    "red": (0.93, 0.27, 0.13),
    "white": (0.96, 0.95, 0.92),
    "black": (0.035, 0.035, 0.04),
}

CAPTION = dict(text="IBM 1418 Optical Character Reader", x=383, baseline=869, size=22)


def white_dots():
    """Grid cells (col, row) that carry a white dot."""
    cells = set()
    for col0, rows in GLYPHS:
        for r, line in enumerate(rows):
            for c, ch in enumerate(line):
                if ch == "#":
                    cells.add((col0 + c, r))
    return cells


def cell_center(col, row):
    return X0 + col * PITCH_X, Y0 + row * PITCH_Y
