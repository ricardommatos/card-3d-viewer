"""Neon type-grid poster as a candy-plastic relief, traced from its pixels.

Every colour region rises off a black base; the smaller the region, the
higher it stands, so glyphs, symbols and marks pop like letterpress type
while the big tiles stay low.

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
from mathutils import Vector  # noqa: E402

import acrylic_poster as ap  # noqa: E402
import solids as so  # noqa: E402
import trace  # noqa: E402

REFERENCE = os.path.join(HERE, "reference.webp")
PALETTE = {  # sRGB 0-255, sampled with k-means from the reference
    "black": (5, 4, 4),
    "magenta": (249, 2, 249),
    "red": (250, 52, 3),
    "lime": (204, 253, 5),
    "yellow": (252, 204, 5),
    "blue": (11, 148, 241),
    "green": (17, 140, 16),
}
LOW, HIGH = 0.015, 0.17   # m: big tiles stay low, small marks stand tall
REF_SIDE = 330            # px: regions this size or larger sit at LOW


class Poster:
    W, H = 1024, 1280


poster = Poster()
ap.PX = 0.0015
FULL = (1600, 2000)


def height(area):
    t = min(1.0, math.sqrt(area) / REF_SIDE)
    return LOW + (HIGH - LOW) * (1 - t) ** 1.6


def setup():
    scene = ap.reset_scene()
    root = scene.collection
    cols = {n: bpy.data.collections.new(n) for n in ("Poster", "Studio", "Lights", "Cameras")}
    for c in cols.values():
        root.children.link(c)

    base = ap.matte_material("base_black", (0.02, 0.02, 0.02), 0.6, 0.0)
    ap.paper_board(poster, base, base, cols["Poster"])
    labels = trace.classify(trace.load_rgb(REFERENCE), list(PALETTE.values()))
    for i, (name, rgb) in enumerate(PALETTE.items()):
        if name == "black":
            continue  # the base plate is the black
        mat = ap.lacquer_material(f"candy_{name}", tuple(c / 255 for c in rgb))
        items = [(o, h, height(a)) for o, h, a in trace.regions(labels, i, scale=2.0)]
        so.relief(poster, f"relief_{name}", items, mat, cols["Poster"])

    ap.cyclorama(ap.matte_material("studio", (0.1, 0.1, 0.1), 0.9), cols["Studio"])
    world_ = bpy.data.worlds.new("World")
    world_.use_nodes = True
    world_.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.08
    scene.world = world_

    c = ap.poster_center(poster)
    L, C = cols["Lights"], cols["Cameras"]
    globe = so.w(poster, 210, 210, 0.05)
    sun = so.w(poster, 810, 210, 0.05)
    nine = so.w(poster, 470, 620, 0.05)
    small = so.w(poster, 700, 960, 0.08)
    print_rig = [ap.sun_light("print_sun", L, (-0.07, -1.0, 0.06), 4.2, 1.5)]
    studio_rig = [
        ap.spot_light("studio_key", L, c + Vector((-2.6, -2.2, 2.2)), c, 9000, 50, 0.6, 0.12, (1.0, 0.96, 0.9)),
        ap.area_light("studio_rim", L, c + Vector((2.6, -0.6, 0.6)), c, 1.5, 500, (0.8, 0.9, 1.0)),
        ap.area_light("studio_fill", L, c + Vector((0.3, -5, 0.2)), c, 5.0, 150),
    ]
    shots = {
        "front": ap.camera("cam_front", C, (0, -10, c.z), c, ortho_scale=poster.H * ap.PX),
        "three_quarter": ap.camera("cam_three_quarter", C, c + Vector((-1.6, -2.6, 0.6)), c, lens=48,
                                   dof=(c, 8)),
        "raking": ap.camera("cam_raking", C, c + Vector((1.9, -0.9, -0.5)), c + Vector((-0.1, 0, 0.1)), lens=45),
        "nine": ap.camera("cam_nine", C, nine + Vector((-0.35, -0.75, -0.2)), nine, lens=60, dof=(nine, 2.8)),
        "symbols": ap.camera("cam_symbols", C, small + Vector((0.45, -0.7, 0.35)), small, lens=70,
                             dof=(small, 2.8)),
    }
    return scene, shots, (print_rig, studio_rig)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--shots", default="front,three_quarter,raking,nine,symbols")
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--exposure", type=float, default=-0.6)
    p.add_argument("--no-render", action="store_true")
    args = p.parse_args(argv)

    scene, shots, (print_rig, studio_rig) = setup()
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "build", "neon-grid.blend"), compress=True)
    if args.no_render:
        return
    size = (round(FULL[0] * args.scale), round(FULL[1] * args.scale))
    for name in filter(None, args.shots.split(",")):
        front = name == "front"
        ap.render(scene, shots[name], os.path.join(HERE, "build", "renders", f"{name}.png"),
                  size, args.samples, print_rig if front else studio_rig, print_rig + studio_rig,
                  "Standard", 1 / 3 if front else 0.8, 0.0 if front else args.exposure)


if __name__ == "__main__":
    main()
