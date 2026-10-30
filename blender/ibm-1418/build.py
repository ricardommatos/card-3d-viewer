"""Build and render the IBM 1418 pin-field sculpture.

    python build.py --scale 0.3 --samples 24     # quick look at all 5 shots
    python build.py                              # full size
    python build.py --eye 300,420                # move the reader's eye (px)
"""

import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, HERE)

import bpy  # noqa: E402  (bpy first: it provides bmesh)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import acrylic_poster as ap  # noqa: E402
import poster  # noqa: E402

ap.PX = 0.0025  # this poster is small in px; make the sculpture ~2 m tall
FONT = os.path.join(HERE, "..", "fonts", "AlfaSlabOne-Regular.ttf")
FULL = (1600, 2000)

LETTER_GAP, LETTER_DEPTH = 0.08, 0.10   # resin letters float off the plate
PIN_REST, PIN_RISE = 0.012, 0.3        # black pin length at rest / extra near the eye
WHITE_PIN = 0.2                         # white dot pins pierce the letters
LETTER_GLOW = 1.0                       # edge-lit resin: letters light the pins
EYE_REACH = 14                          # cells over which pins lean to the eye


def watch_size(d):
    """Watch's dot size (px of its 26.08 grid) at distance d (cells) from the eye."""
    s = poster.WATCH_SIZES
    i = min(len(s) - 1, d)
    k = int(i)
    f = i - k
    return s[-1] if k >= len(s) - 1 else s[k] * (1 - f) + s[k + 1] * f


def add_pin(bm, base, axis, radius, length, segs=20, cap_rings=5):
    """Cylinder with a hemispherical tip, from base along axis."""
    axis = axis.normalized()
    u = axis.orthogonal().normalized()
    v = axis.cross(u)
    r = min(radius, length)
    rings = [(0.0, radius), (length - r, radius)]
    for i in range(1, cap_rings + 1):
        a = math.pi / 2 * i / cap_rings
        rings.append((length - r + r * math.sin(a), radius * math.cos(a)))
    loops = []
    for h, rad in rings[:-1]:
        loops.append([bm.verts.new(base + axis * h + (u * math.cos(t) + v * math.sin(t)) * rad)
                      for t in (2 * math.pi * j / segs for j in range(segs))])
    tip = bm.verts.new(base + axis * rings[-1][0])
    bm.faces.new(list(reversed(loops[0])))
    for a, b in zip(loops, loops[1:]):
        for j in range(segs):
            bm.faces.new((a[j], a[(j + 1) % segs], b[(j + 1) % segs], b[j]))
    for j in range(segs):
        bm.faces.new((loops[-1][j], loops[-1][(j + 1) % segs], tip))


def pin_field(eye, collection, mats):
    """All pins, as two meshes: black field pins and white dot-matrix pins."""
    whites = poster.white_dots()
    ex, ey = eye
    scale = poster.PITCH_X / poster.WATCH_PITCH
    s_min, s_max = poster.WATCH_SIZES[-1], poster.WATCH_SIZES[0]
    meshes = {"black": bmesh.new(), "white": bmesh.new()}
    eye_w = Vector((*ap.to_world(poster, ex, ey),))
    for col in poster.COLS:
        for row in poster.ROWS:
            x, y = poster.cell_center(col, row)
            if not (0 < x < poster.W and 0 < y < poster.H):
                continue
            d = math.hypot((x - ex) / poster.PITCH_X, (y - ey) / poster.PITCH_Y)
            size = watch_size(d)
            grow = ((size - s_min) / (s_max - s_min)) ** 1.5
            # lean towards the eye, like Watch's dots shifting to look at it
            reach = 1.0 if d < EYE_REACH else max(0.0, 1 - (d - EYE_REACH) / 3)
            lean = (1 - size / s_max) * 0.85 * reach * 0.6
            wx, wz = ap.to_world(poster, x, y)
            to_eye = Vector((eye_w.x - wx, 0, eye_w.y - wz))
            axis = Vector((0, -1, 0))
            if to_eye.length > 1e-6:
                axis += to_eye.normalized() * lean
            white = (col, row) in whites
            radius = max(size, 19 / scale if white else 0) * scale * 0.47 * ap.PX
            length = (WHITE_PIN + PIN_RISE * 0.6 * grow) if white else (PIN_REST + PIN_RISE * grow)
            add_pin(meshes["white" if white else "black"], Vector((wx, 0.0, wz)), axis, radius, length)
    for key, bm in meshes.items():
        mesh = bpy.data.meshes.new(f"pins_{key}")
        bm.to_mesh(mesh)
        bm.free()
        for p in mesh.polygons:
            p.use_smooth = True
        mesh.materials.append(mats[key])
        obj = bpy.data.objects.new(f"pins_{key}", mesh)
        collection.objects.link(obj)


def text_block(name, body, font, box, depth, gap, material, collection, bevel=0.006):
    """Text set in `font`, stretched into box=(x0, x1, top, bottom) in px."""
    data = bpy.data.curves.new(name, "FONT")
    data.body = body
    data.font = font
    data.extrude = depth / 2
    data.bevel_depth = bevel
    data.bevel_resolution = 3
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    bpy.context.view_layer.update()
    xs = [c[0] for c in obj.bound_box]
    ys = [c[1] for c in obj.bound_box]
    x0, x1, top, bottom = box
    left, zb = ap.to_world(poster, x0, bottom)
    right, zt = ap.to_world(poster, x1, top)
    sx = (right - left) / (max(xs) - min(xs))
    sy = (zt - zb) / (max(ys) - min(ys))
    obj.scale = (sx, sy, 1)
    obj.rotation_euler = (math.radians(90), 0, 0)
    obj.location = (left - min(xs) * sx, -(gap + depth / 2), zb - min(ys) * sy)
    data.materials.append(material)
    return obj


def setup(eye):
    scene = ap.reset_scene()
    root = scene.collection
    cols = {n: bpy.data.collections.new(n) for n in ("Poster", "Studio", "Lights", "Cameras")}
    for c in cols.values():
        root.children.link(c)
    inks = poster.INKS

    # no broad specular on the blacks: it would grey them under the print light
    black_card = ap.matte_material("black_card", inks["black"], 0.9, 0.0)
    ap.paper_board(poster, black_card, black_card, cols["Poster"])
    pin_field(eye, cols["Poster"], {
        "black": ap.gloss_black_material("pin_black", inks["black"]),
        "white": ap.lacquer_material("pin_white_ceramic", inks["white"]),
    })

    font = bpy.data.fonts.load(FONT)
    for glyph, ink, (x0, x1) in poster.LETTERS:
        text_block(f"letter_{glyph}", glyph, font, (x0, x1, poster.CAP_TOP, poster.BASELINE),
                   LETTER_DEPTH, LETTER_GAP,
                   ap.resin_material(f"resin_{ink}", inks[ink], LETTER_DEPTH, glow=LETTER_GLOW),
                   cols["Poster"])
    cap = poster.CAPTION
    cap_font = bpy.data.fonts.load(os.path.join("/usr/share/fonts/opentype/inter", "Inter-SemiBold.otf")) \
        if os.path.exists("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf") else font
    text_block("caption", cap["text"], cap_font,
               (cap["x"], cap["x"] + 370, cap["baseline"] - 17, cap["baseline"]),
               0.006, 0.0, ap.lacquer_material("caption_white", inks["white"]), cols["Poster"], bevel=0.0005)

    ap.cyclorama(ap.matte_material("studio", (0.11, 0.105, 0.10), 0.9), cols["Studio"])
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.04
    scene.world = world

    c = ap.poster_center(poster)
    L, C = cols["Lights"], cols["Cameras"]
    e = Vector((*ap.to_world(poster, *eye),))
    eye_w = Vector((e.x, -0.15, e.y))
    print_rig = [ap.sun_light("print_sun", L, (-0.07, -1.0, 0.06), 4.0, 1.5)]
    studio_rig = [
        ap.spot_light("studio_key", L, (-3.0, -1.4, 3.8), (0.2, 0, 1.0), 9000, 45, 0.6, 0.08, (1.0, 0.95, 0.88)),
        ap.area_light("studio_rim", L, (3.2, -0.8, 1.6), eye_w, 1.0, 700, (0.8, 0.9, 1.0)),
        ap.area_light("studio_fill", L, (0.5, -5.5, 1.4), c, 5.0, 60),
    ]
    shots = {
        "front": ap.camera("cam_front", C, (0, -8, c.z), c, ortho_scale=poster.H * ap.PX),
        "three_quarter": ap.camera("cam_three_quarter", C, (-2.2, -3.4, 1.7), (0.05, -0.15, 1.2), lens=50,
                                   dof=(eye_w, 5.6)),
        "grazing": ap.camera("cam_grazing", C, (1.9, -1.15, 0.72), (0.05, -0.12, 1.05), lens=38),
        "macro": ap.camera("cam_macro", C, (1.1, -1.7, 1.45), eye_w, lens=70, dof=(eye_w, 2.8)),
        "above": ap.camera("cam_above", C, (-0.3, -1.6, 3.0), (0.0, -0.12, 1.3), lens=40),
    }
    return scene, shots, (print_rig, studio_rig)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--shots", default="front,three_quarter,grazing,macro,above")
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--samples", type=int, default=128)
    p.add_argument("--exposure", type=float, default=-0.4)
    p.add_argument("--eye", default=",".join(str(v) for v in poster.EYE))
    p.add_argument("--no-render", action="store_true")
    args = p.parse_args(argv)

    eye = tuple(float(v) for v in args.eye.split(","))
    scene, shots, (print_rig, studio_rig) = setup(eye)
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "build", "ibm-1418.blend"), compress=True)
    if args.no_render:
        return
    size = (round(FULL[0] * args.scale), round(FULL[1] * args.scale))
    front_size = (round(poster.W / poster.H * FULL[1] * args.scale), size[1])
    for name in filter(None, args.shots.split(",")):
        front = name == "front"
        ap.render(scene, shots[name], os.path.join(HERE, "build", "renders", f"{name}.png"),
                  front_size if front else size, args.samples,
                  print_rig if front else studio_rig, print_rig + studio_rig,
                  "Standard", 1 / 3, 0.0 if front else args.exposure)


if __name__ == "__main__":
    main()
