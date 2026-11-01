"""IBM sticks poster as a real game of pick-up sticks, detected from its pixels.

Each stick is found as a rotated rectangle per colour. A stick cut short by
another one is extended under it to full length, and the one on top is
recorded, so the sticks stack physically. The poster lies flat on a table;
the "front" view looks straight down.

    python build.py --scale 0.3 --samples 24     # quick look
    python build.py                              # full size
"""

import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))

import bpy  # noqa: E402  (bpy first: it provides bmesh)
import cv2  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import acrylic_poster as ap  # noqa: E402
import trace  # noqa: E402

REFERENCE = os.path.join(HERE, "reference.webp")
FONT = os.path.join(HERE, "..", "fonts", "AlfaSlabOne-Regular.ttf")
PALETTE = {  # sRGB 0-255, k-means on the reference
    "white": (255, 255, 255),
    "red": (212, 24, 26),
    "orange": (232, 78, 35),
    "green": (18, 102, 59),
    "yellow": (247, 178, 42),
    "blue": (14, 73, 150),
    "pink": (227, 34, 130),
    "black": (35, 32, 33),
}
W, H = 830, 1173
PX = 0.002            # m per px: sticks come out ~30 cm long
THICK = 0.022         # stick thickness, m
FULL = (1415, 2000)


def world(x, y, z=0.0):
    """Poster px on the table (z up)."""
    return Vector(((x - W / 2) * PX, (H / 2 - y) * PX, z))


def detect():
    labels = trace.classify(trace.load_rgb(REFERENCE), list(PALETTE.values()))
    names = list(PALETTE)
    sticks, comp_of = [], -np.ones(labels.shape, int)
    for ci, name in enumerate(names):
        if name == "white":
            continue
        n, comp, stats, _ = cv2.connectedComponentsWithStats((labels == ci).astype(np.uint8), 8)
        for k in range(1, n):
            if stats[k, cv2.CC_STAT_AREA] < 400:
                continue
            ys, xs = np.nonzero(comp == k)
            (cx, cy), (rw, rh), ang = cv2.minAreaRect(np.column_stack([xs, ys]).astype(np.float32))
            if rw < rh:
                rw, rh, ang = rh, rw, ang + 90
            a = math.radians(ang)
            comp_of[comp == k] = len(sticks)
            sticks.append(dict(ink=name, c=np.array([cx, cy]), u=np.array([math.cos(a), math.sin(a)]),
                               length=rw, width=rh, above=set()))
    full = np.percentile([s["length"] for s in sticks], 85)
    width = np.median([s["width"] for s in sticks])
    for i, s in enumerate(sticks):
        s["width"] = width
        short = full - s["length"]
        ends = []
        for sign in (1, -1):
            # look just past each end: another stick there means it hides this one
            for d in range(3, 12):
                x, y = (s["c"] + s["u"] * sign * (s["length"] / 2 + d)).round().astype(int)
                if 0 <= x < W and 0 <= y < H and comp_of[y, x] not in (-1, i):
                    ends.append(sign)
                    s["above"].add(int(comp_of[y, x]))
                    break
        if short > 4 and ends:
            shift = sum(ends) / len(ends)  # 0 when both ends are hidden
            s["c"] = s["c"] + s["u"] * shift * short / 2
            s["length"] = full
    # any overlap counts: whoever's colour shows in the shared area is on top
    for i, s in enumerate(sticks):
        for j, t in enumerate(sticks):
            if i < j and _overlap(s, t):
                top = _visible_owner(s, t, comp_of)
                if top is not None:
                    (s if top == j else t)["above"].add(top)
    # "above" lists the sticks lying on top of each stick: a stick's level is
    # one more than the highest stick it rests on
    level = {}
    rests_on = {i: {j for j, t in enumerate(sticks) if i in t["above"]} for i in range(len(sticks))}

    def height(i, seen=()):
        if i not in level:
            level[i] = 1 + max((height(j, seen + (i,)) for j in rests_on[i] if j not in seen), default=-1)
        return level[i]

    for i, s in enumerate(sticks):
        s["level"] = height(i)
    return sticks


def _corners(s):
    v = np.array([-s["u"][1], s["u"][0]])
    return np.array([s["c"] + s["u"] * a * s["length"] / 2 + v * b * s["width"] / 2
                     for a, b in ((1, 1), (-1, 1), (-1, -1), (1, -1))], np.float32)


def _overlap(s, t):
    inter, _ = cv2.intersectConvexConvex(_corners(s), _corners(t))
    return inter > 30


def _visible_owner(s, t, comp_of):
    """Which of two overlapping sticks shows in their shared area."""
    mask = np.zeros(comp_of.shape, np.uint8)
    cv2.fillConvexPoly(mask, _corners(s).astype(np.int32), 1)
    m2 = np.zeros_like(mask)
    cv2.fillConvexPoly(m2, _corners(t).astype(np.int32), 1)
    shared = comp_of[(mask & m2) > 0]
    ids, counts = np.unique(shared[shared >= 0], return_counts=True)
    if not len(ids):
        return None
    return int(ids[counts.argmax()])


def build_sticks(sticks, mats, col):
    font = bpy.data.fonts.load(FONT)
    for i, s in enumerate(sticks):
        z = THICK / 2 + s["level"] * THICK * 0.92
        c = world(*s["c"], z)
        bpy.ops.mesh.primitive_cube_add(size=1, location=c)
        obj = bpy.context.object
        obj.name = f"stick_{i:02d}_{s['ink']}"
        obj.scale = (s["length"] * PX, s["width"] * PX, THICK)
        obj.rotation_euler = (0, 0, -math.atan2(s["u"][1], s["u"][0]))
        bpy.ops.object.transform_apply(scale=True)
        bev = obj.modifiers.new("soft", "BEVEL")
        bev.width, bev.segments = 0.004, 4
        obj.data.materials.append(mats[s["ink"]])
        bpy.ops.object.shade_smooth()
        for cc in obj.users_collection:
            cc.objects.unlink(obj)
        col.objects.link(obj)
        if s["ink"] == "black":
            # the IBM mark sits near the stick's left-hand end, reading along it
            u = s["u"] if s["u"][0] >= 0 else -s["u"]
            p = s["c"] - u * s["length"] * 0.3
            data = bpy.data.curves.new(f"ibm_{i}", "FONT")
            data.body, data.font = "IBM", font
            data.align_x, data.align_y = "CENTER", "CENTER"
            data.size = s["width"] * PX * 0.55
            data.extrude = 0.0006
            data.materials.append(mats["mark"])
            t = bpy.data.objects.new(f"ibm_{i}", data)
            t.location = world(*p, z + THICK / 2 + 0.0006)
            t.rotation_euler = (0, 0, -math.atan2(u[1], u[0]))
            col.objects.link(t)


def setup():
    scene = ap.reset_scene()
    root = scene.collection
    cols = {n: bpy.data.collections.new(n) for n in ("Poster", "Studio", "Lights", "Cameras")}
    for c in cols.values():
        root.children.link(c)
    mats = {name: ap.lacquer_material(f"stick_{name}", tuple(v / 255 for v in rgb))
            for name, rgb in PALETTE.items() if name != "white"}
    mats["mark"] = ap.lacquer_material("ibm_mark", (0.95, 0.95, 0.93))
    sticks = detect()
    build_sticks(sticks, mats, cols["Poster"])
    print(f"{len(sticks)} sticks, {max(s['level'] for s in sticks) + 1} levels")

    # an endless white sweep, set back so the sticks stay on the flat part
    sweep = ap.cyclorama(ap.matte_material("paper_white", (0.97, 0.97, 0.96), 0.85, 0.2), cols["Studio"],
                         radius=3.0)
    sweep.location.y = 3.0
    world_ = bpy.data.worlds.new("World")
    world_.use_nodes = True
    world_.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
    world_.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    scene.world = world_

    L, C = cols["Lights"], cols["Cameras"]
    centre = Vector((0, 0, 0.02))
    top_rig = [ap.sun_light("print_sun", L, (-0.25, 0.3, 1.0), 3.2, 4.0)]
    studio_rig = [
        ap.sun_light("studio_sun", L, (-1.0, 0.55, 0.42), 3.6, 1.5),
        ap.area_light("studio_fill", L, (3, -3, 2.5), centre, 5.0, 400, (0.88, 0.92, 1.0)),
    ]
    black = min((s for s in sticks if s["ink"] == "black"), key=lambda s: abs(s["c"][1] - H * 0.55))
    u = black["u"] if black["u"][0] >= 0 else -black["u"]
    bc = world(*(black["c"] - u * black["length"] * 0.3), 0.03)  # the IBM mark
    shots = {
        "top": ap.camera("cam_top", C, (0, 0, 8), centre, ortho_scale=H * PX),
        "three_quarter": ap.camera("cam_three_quarter", C, (-1.1, -2.1, 1.25), Vector((0, -0.15, 0)), lens=45,
                                   dof=(Vector((0, -0.2, 0)), 5.6)),
        "table": ap.camera("cam_table", C, (0.1, -1.25, 0.13), Vector((-0.1, -0.35, 0.0)), lens=26,
                           dof=(Vector((0.0, -0.9, 0.03)), 5.6)),
        "ibm": ap.camera("cam_ibm", C, bc + Vector((-0.18, -0.3, 0.2)), bc, lens=80, dof=(bc, 2.8)),
        "high": ap.camera("cam_high", C, (1.0, 1.2, 2.2), Vector((0, 0.05, 0)), lens=40),
    }
    return scene, shots, (top_rig, studio_rig)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--shots", default="top,three_quarter,table,ibm,high")
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--exposure", type=float, default=-0.4)
    p.add_argument("--no-render", action="store_true")
    args = p.parse_args(argv)

    scene, shots, (top_rig, studio_rig) = setup()
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "build", "ibm-sticks.blend"), compress=True)
    if args.no_render:
        return
    size = (round(FULL[0] * args.scale), round(FULL[1] * args.scale))
    for name in filter(None, args.shots.split(",")):
        top = name == "top"
        ap.render(scene, shots[name], os.path.join(HERE, "build", "renders", f"{name}.png"),
                  size, args.samples, top_rig if top else studio_rig, top_rig + studio_rig,
                  "Standard", 1 / 3, 0.0 if top else args.exposure)


if __name__ == "__main__":
    main()
