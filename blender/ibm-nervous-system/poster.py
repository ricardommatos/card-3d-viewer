"""IBM Smarter Planet ad, "Can an entire business be given a nervous system?"

The reference image is too small to trace, so the block grid is recomposed
on an ideal module (25 px cells) from the evident vocabulary of the ad:
black slabs, yellow/orange/blue circles, stripe sets, dot grids and two
sunbursts. Coordinates: px of a 490 x 720 poster, origin top-left.

Each block: kind, grid box (col, row, cols, rows), ink, height (m off the
paper) and finish. Kinds: rect, circle, stripes_v, stripes_h, dots,
sunburst, sunburst_disc, rect_inset.
"""

W, H = 490, 720
CELL = 25
GX, GY = 20, 330  # grid origin

INKS = {
    "black": (0.08, 0.08, 0.09),
    "yellow": (0.99, 0.85, 0.10),
    "orange": (0.94, 0.38, 0.12),
    "blue": (0.15, 0.68, 0.92),
    "green": (0.15, 0.62, 0.30),
    "white": (0.97, 0.97, 0.96),
    "headline": (0.88, 0.36, 0.12),
}
PAPER = (0.92, 0.92, 0.91)

BLOCKS = [
    # --- top band
    dict(kind="rect", box=(0, 0, 4, 2), ink="black", h=0.22, finish="gloss"),
    dict(kind="dots", box=(4, 0, 2, 3), ink=["black", "black", "black", "yellow", "blue", "blue"], h=0.05),
    dict(kind="rect", box=(6, 0, 5, 2), ink="black", h=0.34, finish="gloss"),
    dict(kind="stripes_v", box=(11, 0, 2, 4), ink="green", h=0.16, n=5, finish="frosted"),
    dict(kind="circle", box=(14, 0, 2, 2), ink="orange", h=0.10, finish="lacquer"),
    dict(kind="rect", box=(16, 0, 2, 2), ink="yellow", h=0.12, finish="lacquer"),
    # --- second band
    dict(kind="rect", box=(0, 2, 2, 3), ink="yellow", h=0.08, finish="lacquer"),
    dict(kind="rect", box=(2, 2, 2, 2), ink="blue", h=0.06, finish="glass"),
    dict(kind="circle", box=(4, 3, 5, 5), ink="yellow", h=0.06, finish="lacquer"),
    dict(kind="sunburst", box=(9, 2, 4, 4), ink="blue", h=0.12, n=20),
    dict(kind="rect", box=(13, 2, 5, 3), ink="black", h=0.26, finish="gloss"),
    dict(kind="dots", box=(14, 5, 2, 2), ink=["green", "yellow", "yellow", "green"], h=0.05),
    dict(kind="circle", box=(16, 5, 2, 2), ink="green", h=0.14, finish="frosted"),
    # --- middle band
    dict(kind="rect", box=(0, 5, 4, 1), ink="blue", h=0.10, finish="glass"),
    dict(kind="stripes_h", box=(0, 6, 4, 2), ink="green", h=0.08, n=3, finish="frosted"),
    dict(kind="stripes_h", box=(9, 6, 2, 5), ink="black", h=0.18, n=6, finish="gloss"),
    dict(kind="rect", box=(11, 6, 2, 3), ink="yellow", h=0.20, finish="lacquer"),
    dict(kind="circle", box=(13, 7, 3, 3), ink="blue", h=0.16, finish="glass"),
    dict(kind="sunburst_disc", box=(16, 7, 2, 3), ink="orange", h=0.09, n=16),
    # --- bottom band
    dict(kind="rect", box=(0, 8, 2, 7), ink="black", h=0.40, finish="gloss"),
    dict(kind="rect_inset", box=(2, 8, 5, 7), ink="orange", h=0.14, finish="lacquer"),
    dict(kind="rect", box=(7, 8, 2, 4), ink="yellow", h=0.10, finish="lacquer"),
    dict(kind="dots", box=(7, 12, 3, 2), ink=["yellow", "blue", "green", "blue", "green", "yellow"], h=0.05),
    dict(kind="rect", box=(10, 11, 2, 4), ink="yellow", h=0.24, finish="lacquer"),
    dict(kind="rect", box=(12, 10, 1, 5), ink="blue", h=0.30, finish="glass"),
    dict(kind="stripes_v", box=(13, 10, 2, 5), ink="green", h=0.12, n=5, finish="frosted"),
    dict(kind="circle", box=(15, 10, 2, 2), ink="green", h=0.07, finish="frosted"),
    dict(kind="rect", box=(15, 12, 3, 3), ink="black", h=0.30, finish="gloss"),
    dict(kind="circle", box=(17, 10, 1, 1), ink="orange", h=0.05, finish="lacquer"),
]

HEADLINE = dict(lines=["Can an entire business", "be given a nervous system?"], x=60, y=110, size=24,
                ink="headline")
BODY_COPY = dict(x=60, y=150, width=370, size=8.2, leading=11, ink="black", text=(
    "If digital intelligence can be pushed far beyond the walls of a server room today, into basic "
    "infrastructures like facilities, utilities, networks, etc. it begs the question: what exactly is a "
    "datacenter. Our smartest datacenters are merging with the physical world. Tightly synchronizing "
    "service delivery to give greater efficiency and flexibility to the business. Not only powering a "
    "smarter world but also giving companies the ability to react to change and operational savings to "
    "the tune of about $1.5 billion per year. From a computing standpoint, the last 50 years were largely "
    "about building machines that were more intelligent. Let's make the next 50 about extending that "
    "intelligence across our entire infrastructure. A smarter business needs smarter tools. "
    "Let's build a smarter planet. ibm.com/dynamic"))
LOGO_STRIPES = dict(x=362, y=242, w=56, h=24, colors=["blue", "green", "yellow", "orange", "black"])
