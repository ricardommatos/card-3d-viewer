"""IBM Smarter Planet ad, "The tools of collaboration vs the tools of distraction".

Rebuilt from its evident geometry (the reference is too small to trace):
a hub; to the left a fan of translucent colour bands, to the right a burst
of black dots on hairline stems. Coordinates: px of a 468 x 700 poster.
"""

W, H = 468, 700

HUB = (238, 520, 22)               # centre x, y, radius
FAN = dict(radius=226, band=26, count=31, start=95, end=265)   # angles in degrees, px space (0 = right, y down)
FAN_COLORS = ["blue", "purple", "pink", "red", "orange", "yellow", "green", "teal"]
BURST = dict(count=260, radius=(40, 236), angle=(-88, 88), dot=6.5, seed=1418)

INKS = {
    "blue": (0.20, 0.45, 0.85),
    "purple": (0.50, 0.38, 0.70),
    "pink": (0.92, 0.42, 0.62),
    "red": (0.88, 0.18, 0.16),
    "orange": (0.95, 0.52, 0.12),
    "yellow": (0.98, 0.85, 0.12),
    "green": (0.20, 0.66, 0.32),
    "teal": (0.10, 0.60, 0.58),
    "black": (0.06, 0.06, 0.06),
    "white": (0.97, 0.97, 0.96),
}
PAPER = (0.93, 0.92, 0.90)

KICKER = dict(text="Smarter business for a Smarter Planet:", x=22, y=34, size=12)
HEADLINE = dict(lines=["The tools of collaboration", "vs the tools of distraction."], x=22, y=66, size=21)
BODY_COPY = dict(x=22, y=112, width=420, size=8.2, leading=11, text=(
    "If digital intelligence can be pushed far beyond the walls of a server room today, into basic "
    "infrastructures like facilities, utilities, networks, etc. it begs the question: what exactly is a "
    "datacenter. Our smartest datacenters are merging with the physical world. Tightly synchronizing service "
    "delivery to give greater efficiency and flexibility to the business. Not only powering a smarter world "
    "but also giving companies the ability to react to change and operational savings to the tune of about "
    "$1.5 billion per year. From a computing standpoint, the last 50 years were largely about building "
    "machines that were more intelligent. Let's make the next 50 about extending that intelligence across "
    "our entire infrastructure. A smarter business needs smarter tools. Let's build a smarter planet."))
LOGO = dict(x=318, y=222, w=96, h=36)
