"""Olivetti Lettera 22 poster (Giovanni Pintori, 1953), reinterpreted.

Coordinates are pixels of the poster as seen in the reference image
(about 1416 x 2000, origin top-left, y down), traced by eye.

Each colour is a family of "m"-like arches; every leg ends in a typewriter
key carrying a letter. In 3D the arches leap out of the paper (feet on the
paper, crowns towards the viewer), each colour in its own material, and the
photographed typewriter becomes a sculpted body with real keys.
"""

W, H = 1416, 2000
STROKE = 38          # arch stroke width, px
KEY_R = 23           # key cap radius, px

# family: legs as (x, y_of_key, letter), crown heights (y of each arch top),
# material finish and how far (m) the crowns come off the paper
FAMILIES = {
    "blue_top": dict(ink="blue", finish="glass", reach=0.42,
                     legs=[(452, 548, "O"), (585, 660, "R"), (815, 495, "K"), (925, 830, "B")],
                     crowns=[210, 190, 265]),
    "yellow": dict(ink="yellow", finish="neon", reach=0.30,
                   legs=[(235, 890, "G"), (515, 870, "F"), (715, 610, "V"), (870, 720, "C")],
                   crowns=[465, 330, 395]),
    "red": dict(ink="red", finish="lacquer", reach=0.55,
                legs=[(135, 800, "T"), (390, 800, "H"), (645, 705, "L"), (800, 745, "D"),
                      (985, 920, "X"), (1245, 860, "I")],
                crowns=[545, 375, 400, 470, 640]),
    "blue_low": dict(ink="blue", finish="glass", reach=0.36,
                     legs=[(450, 1125, "N"), (680, 980, "S"), (905, 700, "U")],
                     crowns=[775, 610]),
    "green_mid": dict(ink="green", finish="frosted", reach=0.48,
                      legs=[(315, 1230, "J"), (560, 1070, "Z"), (805, 1040, "A")],
                      crowns=[890, 850]),
    "green_low": dict(ink="green", finish="frosted", reach=0.34,
                      legs=[(170, 1585, "Y"), (325, 1710, "M"), (530, 1470, "P")],
                      crowns=[1465, 1285]),
}

INKS = {
    "blue": (0.0, 0.58, 0.80),
    "yellow": (0.99, 0.84, 0.05),
    "red": (0.94, 0.30, 0.10),
    "green": (0.10, 0.60, 0.40),
    "black": (0.06, 0.06, 0.06),
    "white": (0.97, 0.96, 0.93),
    "body": (0.66, 0.62, 0.55),     # Lettera 22 sand-grey
}
PAPER = (0.95, 0.92, 0.86)

# the typewriter, simplified to a sculpted body (px boxes)
BODY = None  # no body copy on the paper (paper_texture convention)
MACHINE = dict(box=(585, 1165, 1150, 1840), depth=0.20, radius=0.05,
               platen=(560, 1185, 1180, 1300), window=(705, 1390, 1025, 1475),
               keys_area=(640, 1625, 1105, 1800),
               rows=["1234567890", "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"])

LOGO = dict(text="Olivetti Lettera 22", x=845, baseline=1062, size=44, width=515, ink="black",
            fonts=("Inter-BlackItalic.otf", "InterDisplay-BlackItalic.otf", "DejaVuSans-BoldOblique.ttf"))
