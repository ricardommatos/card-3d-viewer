"""Simon Page's grey bars as a data landscape, read from the pixels.

Each row is read as a brightness profile and cut where the grey changes;
every segment becomes a porcelain block whose height follows its grey, so
the image turns into a skyline of light. Lies flat; "top" looks straight
down and gives back the original.

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

REFERENCE = os.path.join(HERE, "reference.jpg")
W = H = 540
PX = 0.003
FULL = (2000, 2000)
BLACK = 14            # grey at or below this is the ground
H_MIN, H_MAX = 0.006, 0.2
STEP = 7              # grey jump that starts a new segment


def world(x, y, z=0.0):
    return Vector(((x - W / 2) * PX, (H / 2 - y) * PX, z))


def read_bars():
    g = cv2.cvtColor(cv2.imread(REFERENCE), cv2.COLOR_BGR2GRAY).astype(float)
    on = g[:, 40:500].mean(1) > 12
    edges = np.flatnonzero(np.diff(on.astype(int))) + 1
    bands = [(a, b) for a, b in zip(edges[::2], edges[1::2]) if b - a >= 4] if on[0] == 0 else \
            [(a, b) for a, b in zip(edges[1::2], edges[2::2]) if b - a >= 4]
    bars = []
    for y0, y1 in bands:
        prof = np.median(g[y0 + 1:y1 - 1], axis=0)
        start = 0
        for x in range(1, W + 1):
            if x == W or abs(prof[x] - np.median(prof[start:x])) > STEP:
                if x - start >= 3:
                    v = float(np.median(prof[start:x]))
                    if v > BLACK:
                        bars.append((start, x, y0, y1, v))
                start = x
    return bars


def setup():
    scene = ap.reset_scene()
    root = scene.collection
    cols = {n: bpy.data.collections.new(n) for n in ("Poster", "Studio", "Lights", "Cameras")}
    for c in cols.values():
        root.children.link(c)
    bars = read_bars()
    print(f"{len(bars)} bars")

    # one porcelain material; each block carries its grey as the object colour
    mat = ap.lacquer_material("porcelain", (1, 1, 1))
    p = mat.node_tree.nodes["Principled BSDF"]
    info = mat.node_tree.nodes.new("ShaderNodeObjectInfo")
    mat.node_tree.links.new(info.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Coat Roughness"].default_value = 0.02  # a tight coat keeps the top-light off the greys

    bpy.ops.mesh.primitive_cube_add(size=1)
    unit = bpy.context.object.data
    bpy.data.objects.remove(bpy.context.object)
    unit.materials.append(mat)
    for i, (x0, x1, y0, y1, v) in enumerate(bars):
        t = (v - BLACK) / (255 - BLACK)
        hgt = H_MIN + (H_MAX - H_MIN) * t ** 1.6
        obj = bpy.data.objects.new(f"bar_{i:04d}", unit)
        obj.location = world((x0 + x1) / 2, (y0 + y1) / 2, hgt / 2)
        obj.scale = ((x1 - x0) * PX - 0.0015, (y1 - y0) * PX, hgt)
        lin = (v / 255) ** 2.2
        obj.color = (lin, lin, lin, 1)
        cols["Poster"].objects.link(obj)
        bev = obj.modifiers.new("soft", "BEVEL")
        bev.width, bev.segments = 0.0012, 2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.01))
    plate = bpy.context.object
    plate.name = "base_black"
    plate.scale = (W * PX, H * PX, 0.02)
    plate.data.materials.append(ap.matte_material("base_black", (0.02, 0.02, 0.02), 0.5, 0.0))
    for cc in plate.users_collection:
        cc.objects.unlink(plate)
    cols["Poster"].objects.link(plate)

    sweep = ap.cyclorama(ap.matte_material("studio", (0.06, 0.06, 0.06), 0.9), cols["Studio"], radius=3.0)
    sweep.location.y = 3.0
    world_ = bpy.data.worlds.new("World")
    world_.use_nodes = True
    world_.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.03
    scene.world = world_

    L, C = cols["Lights"], cols["Cameras"]
    centre = Vector((0, 0, 0.05))
    top_rig = [ap.sun_light("print_sun", L, (-0.05, 0.04, 1.0), 4.0, 1.5)]
    studio_rig = [
        ap.sun_light("studio_sun", L, (-1.0, 0.25, 0.32), 4.5, 1.0),
        ap.area_light("studio_fill", L, (2.5, -2.5, 1.8), centre, 4.0, 150, (0.85, 0.9, 1.0)),
        ap.area_light("studio_top", L, (0, 0, 3), centre, 3.0, 120),
    ]
    shots = {
        "top": ap.camera("cam_top", C, (0, 0, 8), Vector((0, 0, 0)), ortho_scale=W * PX),
        "three_quarter": ap.camera("cam_three_quarter", C, (-1.5, -2.0, 1.3), Vector((0, 0, 0.05)), lens=40,
                                   dof=(Vector((0, -0.1, 0.05)), 8)),
        "skyline": ap.camera("cam_skyline", C, (1.15, -0.25, 0.09), Vector((-0.3, 0.05, 0.1)), lens=28),
        "ridge": ap.camera("cam_ridge", C, (0.35, -1.05, 0.32), Vector((0.1, -0.25, 0.12)), lens=60,
                           dof=(Vector((0.12, -0.35, 0.12)), 2.8)),
        "corner": ap.camera("cam_corner", C, (1.4, 1.5, 1.6), Vector((0, 0, 0.05)), lens=40),
    }
    return scene, shots, (top_rig, studio_rig)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--shots", default="top,three_quarter,skyline,ridge,corner")
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--exposure", type=float, default=-0.3)
    p.add_argument("--no-render", action="store_true")
    args = p.parse_args(argv)

    scene, shots, (top_rig, studio_rig) = setup()
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "build", "simon-page-bars.blend"), compress=True)
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
