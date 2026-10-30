"""Build and render the Lettera 22 sculpture: arches leaping out of the paper.

    python build.py --scale 0.3 --samples 24     # quick look at all 5 shots
    python build.py                              # full size
"""

import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, HERE)

import bpy  # noqa: E402  (bpy first: it provides bmesh)
from mathutils import Vector  # noqa: E402

import acrylic_poster as ap  # noqa: E402
import paper_texture  # noqa: E402
import poster  # noqa: E402

FULL = (1416, 2000)
KEY_DEPTH = 0.035
LEAP_H = 420  # px of height over which an arch leaves the paper
INTER_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"


def world(x, y, depth):
    wx, wz = ap.to_world(poster, x, y)
    return Vector((wx, -depth, wz))


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def leg_depth(y_key, y, reach):
    """Depth off the paper of a point on a leg whose key sits at y_key."""
    return KEY_DEPTH * 0.6 + reach * smooth((y_key - y) / LEAP_H) ** 1.1


def arch_points(left, right, crown, reach, start_y=None, step=6):
    """Leg up from `left` key (or from start_y on that leg), round crown,
    leg down to `right` key. Returns world points."""
    (xa, ya, _), (xb, yb, _) = left, right
    a = (xb - xa) / 2
    xc, ys = (xa + xb) / 2, crown + a          # springing line of the crown
    pts = []
    y0 = ya if start_y is None else start_y
    for i in range(int(max(0, y0 - ys) / step) + 1):
        y = y0 - i * step
        pts.append(world(xa, y, leg_depth(ya, y, reach)))
    n = max(12, int(math.pi * a / step))
    for i in range(1, n):
        t = math.pi * i / n
        x, y = xc - a * math.cos(t), ys - a * math.sin(t)
        u = i / n  # blend the two legs' depth laws across the crown
        pts.append(world(x, y, (1 - u) * leg_depth(ya, y, reach) + u * leg_depth(yb, y, reach)))
    for i in range(int(max(0, yb - ys) / step) + 1):
        y = ys + i * step
        pts.append(world(xb, y, leg_depth(yb, y, reach)))
    pts.append(world(xb, yb, leg_depth(yb, yb, reach)))
    return pts


def tube(name, pts, radius, material, collection):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = radius
    data.bevel_resolution = 6
    data.use_fill_caps = True
    sp = data.splines.new("NURBS")
    sp.points.add(len(pts) - 1)
    for p, v in zip(sp.points, pts):
        p.co = (*v, 1)
    sp.order_u = 4
    sp.use_endpoint_u = True
    sp.resolution_u = 2
    data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    return obj


def label(name, text, font, center, height, depth, material, collection):
    """White letter standing on a key face, centred at world `center`."""
    data = bpy.data.curves.new(name, "FONT")
    data.body = text
    data.font = font
    data.align_x, data.align_y = "CENTER", "CENTER"
    data.size = height
    data.extrude = depth / 2
    data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    obj.rotation_euler = (math.radians(90), 0, 0)
    obj.location = center
    collection.objects.link(obj)
    return obj


def key(name, x, y, z_front, mats, font, collection, r_px=poster.KEY_R, letter=None):
    """Lettera 22 key: black cap in a chrome ring, white letter on top."""
    r = r_px * ap.PX
    c = world(x, y, 0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=r, depth=KEY_DEPTH,
                                        location=(c.x, -(z_front - KEY_DEPTH / 2), c.z),
                                        rotation=(math.radians(90), 0, 0))
    cap = bpy.context.object
    cap.name = name
    cap.data.materials.append(mats["cap"])
    bev = cap.modifiers.new("soft", "BEVEL")
    bev.width, bev.segments = r * 0.25, 4
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_torus_add(major_radius=r * 1.02, minor_radius=r * 0.12,
                                     location=(c.x, -(z_front - KEY_DEPTH * 0.75), c.z),
                                     rotation=(math.radians(90), 0, 0))
    ring = bpy.context.object
    ring.name = name + "_ring"
    ring.data.materials.append(mats["chrome"])
    bpy.ops.object.shade_smooth()
    for o in (cap, ring):
        for col in o.users_collection:
            col.objects.unlink(o)
        collection.objects.link(o)
    if letter:
        label(name + "_letter", letter, font, Vector((c.x, -(z_front + 0.001), c.z)), r * 1.15, 0.002,
              mats["ink"], collection)


def rounded_box(name, box, depth, radius, material, collection):
    x0, y0, x1, y1 = box
    a, b = world(x0, y1, 0), world(x1, y0, 0)
    bpy.ops.mesh.primitive_cube_add(size=1, location=((a.x + b.x) / 2, -depth / 2, (a.z + b.z) / 2))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (b.x - a.x, depth, b.z - a.z)
    bpy.ops.object.transform_apply(scale=True)
    bev = obj.modifiers.new("round", "BEVEL")
    bev.width, bev.segments = radius, 8
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    for col in obj.users_collection:
        col.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def rod(name, a, b, radius, material, collection):
    """Thin cylinder from world point a to b."""
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=d.length, location=(a + b) / 2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    for col in obj.users_collection:
        col.objects.unlink(obj)
    collection.objects.link(obj)


def machine(mats, font, collection):
    """The typewriter distilled: a raked keyboard of keys on chrome levers
    springing from the paper, and the platen floating above it."""
    m = poster.MACHINE
    x0, y0, x1, y1 = m["platen"]
    a, b = world(x0, (y0 + y1) / 2, 0), world(x1, (y0 + y1) / 2, 0)
    r = (y1 - y0) / 2 * ap.PX
    depth = 0.16
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=r, depth=b.x - a.x,
                                        location=((a.x + b.x) / 2, -depth, a.z), rotation=(0, math.radians(90), 0))
    platen = bpy.context.object
    platen.name = "platen"
    platen.data.materials.append(mats["rubber"])
    bpy.ops.object.shade_smooth()
    for col in platen.users_collection:
        col.objects.unlink(platen)
    collection.objects.link(platen)
    for side, x in (("l", a.x - 0.02), ("r", b.x + 0.02)):
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=r * 0.7, depth=0.04,
                                            location=(x, -depth, a.z), rotation=(0, math.radians(90), 0))
        knob = bpy.context.object
        knob.name = f"platen_knob_{side}"
        knob.data.materials.append(mats["chrome"])
        bpy.ops.object.shade_smooth()
        for col in knob.users_collection:
            col.objects.unlink(knob)
        collection.objects.link(knob)
        rod(f"platen_arm_{side}", Vector((x, 0, a.z)), Vector((x, -depth, a.z)), 0.006, mats["chrome"],
            collection)
    kx0, ky0, kx1, ky1 = m["keys_area"]
    rows = m["rows"]
    pitch = (kx1 - kx0) / 10
    for r_i, row in enumerate(rows):
        y = ky0 + r_i * (ky1 - ky0) / (len(rows) - 1)
        x_start = kx0 + r_i * pitch * 0.35
        front = 0.16 + 0.05 * r_i  # raked: the bottom row stands furthest out
        for k_i, ch in enumerate(row):
            x = x_start + k_i * pitch
            key(f"kb_{ch}", x, y, front, mats, font, collection, r_px=pitch * 0.44, letter=ch)
            # the lever dives back and up into the paper, like a typebar
            rod(f"kb_{ch}_lever", world(x, y, front - KEY_DEPTH), world(x, y - 120 - 25 * r_i, 0), 0.0035,
                mats["chrome"], collection)


def setup():
    tex = paper_texture.make(poster, os.path.join(HERE, "build", "paper.png"))
    scene = ap.reset_scene()
    root = scene.collection
    cols = {n: bpy.data.collections.new(n) for n in ("Poster", "Studio", "Lights", "Cameras")}
    for c in cols.values():
        root.children.link(c)
    inks = poster.INKS
    ap.paper_board(poster, ap.paper_material("paper", tex, poster.PAPER),
                   ap.matte_material("board_edge", poster.PAPER, 0.9), cols["Poster"])

    tube_r = poster.STROKE / 2 * ap.PX
    finishes = {
        "glass": lambda ink: ap.acrylic_material(f"glass_{ink}", inks[ink]),
        "neon": lambda ink: ap.resin_material(f"neon_{ink}", inks[ink], tube_r * 2, glow=0.6),
        "lacquer": lambda ink: ap.lacquer_material(f"lacquer_{ink}", inks[ink]),
        "frosted": lambda ink: ap.frosted_materials(f"frosted_{ink}", inks[ink])[0],
    }
    mats = {
        "cap": ap.gloss_black_material("key_cap", inks["black"]),
        "ink": ap.lacquer_material("key_letter", inks["white"]),
        "chrome": ap.matte_material("chrome", (0.9, 0.9, 0.9), 0.08),
        "body": ap.lacquer_material("machine_body", inks["body"]),
        "rubber": ap.matte_material("rubber", (0.05, 0.05, 0.05), 0.5, 0.3),
    }
    mats["chrome"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
    mats["body"].node_tree.nodes["Principled BSDF"].inputs["Coat Roughness"].default_value = 0.25
    font = bpy.data.fonts.load(INTER_BOLD) if os.path.exists(INTER_BOLD) else bpy.data.fonts.load("<builtin>")

    cache = {}
    for fam, spec in poster.FAMILIES.items():
        key_mat = finishes[spec["finish"]]
        mat = cache.setdefault((spec["finish"], spec["ink"]), key_mat(spec["ink"]))
        legs, crowns = spec["legs"], spec["crowns"]
        for i, crown in enumerate(crowns):
            left, right = legs[i], legs[i + 1]
            a = (right[0] - left[0]) / 2
            # first arch starts at its key; the next ones branch off the leg
            start = None if i == 0 else min(left[1], crown + a + 60)
            tube(f"{fam}_{i}", arch_points(left, right, crown, spec["reach"], start), tube_r, mat,
                 cols["Poster"])
        for x, y, letter in legs:
            key(f"key_{letter}", x, y, KEY_DEPTH, mats, font, cols["Poster"], letter=letter)
    machine(mats, font, cols["Poster"])

    ap.cyclorama(ap.matte_material("studio", (0.16, 0.155, 0.15), 0.9), cols["Studio"])
    world_ = bpy.data.worlds.new("World")
    world_.use_nodes = True
    world_.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.05
    scene.world = world_

    c = ap.poster_center(poster)
    L, C = cols["Lights"], cols["Cameras"]
    print_rig = [ap.sun_light("print_sun", L, (-0.07, -1.0, 0.06), 4.0, 1.5)]
    studio_rig = [
        ap.spot_light("studio_key", L, (-3.2, -2.2, 3.4), (0.1, 0, 1.1), 7000, 50, 0.7, 0.1, (1.0, 0.95, 0.88)),
        ap.area_light("studio_rim", L, (3.0, -0.8, 2.6), (0, -0.35, 1.3), 1.5, 500, (0.85, 0.92, 1.0)),
        ap.area_light("studio_fill", L, (0.5, -5.5, 1.4), c, 5.0, 120),
    ]
    arches = Vector((-0.05, -0.3, 1.45))
    shots = {
        "front": ap.camera("cam_front", C, (0, -8, c.z), c, ortho_scale=poster.H * ap.PX),
        "three_quarter": ap.camera("cam_three_quarter", C, (-2.3, -3.2, 1.6), (0.05, -0.25, 1.2), lens=48,
                                   dof=(arches, 5.6)),
        "profile": ap.camera("cam_profile", C, (2.7, -1.5, 1.35), (-0.1, -0.3, 1.35), lens=45),
        "keys": ap.camera("cam_keys", C, (1.0, -1.5, 0.75), (0.15, -0.2, 0.55), lens=55,
                          dof=(Vector((0.2, -0.25, 0.48)), 2.8)),
        "below": ap.camera("cam_below", C, (-1.2, -2.2, 0.25), (-0.1, -0.35, 1.45), lens=28),
    }
    return scene, shots, (print_rig, studio_rig)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--shots", default="front,three_quarter,profile,keys,below")
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--samples", type=int, default=128)
    p.add_argument("--exposure", type=float, default=-0.7)
    p.add_argument("--no-render", action="store_true")
    args = p.parse_args(argv)

    scene, shots, (print_rig, studio_rig) = setup()
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "build", "lettera-22.blend"), compress=True)
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
