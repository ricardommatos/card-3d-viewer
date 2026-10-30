"""Build and render the Eye-Bee-M sculpture.

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
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import acrylic_poster as ap  # noqa: E402
import poster  # noqa: E402

ap.PX = 0.0035
FULL = (1600, 2000)
FONT = os.path.join(HERE, "..", "fonts", "AlfaSlabOne-Regular.ttf")


def w(x, y, depth=0.0):
    wx, wz = ap.to_world(poster, x, y)
    return Vector((wx, -depth, wz))


def arc(p0, p1, sag, n=40):
    """Circular arc from p0 to p1 (px) bulging by `sag` px to the left of p0->p1."""
    p0, p1 = Vector(p0), Vector(p1)
    c = (p1 - p0).length / 2
    r = (c * c + sag * sag) / (2 * abs(sag))
    mid = (p0 + p1) / 2
    normal = Vector((-(p1 - p0).y, (p1 - p0).x)).normalized() * (1 if sag > 0 else -1)
    center = mid - normal * (r - abs(sag))
    a0 = math.atan2(*(p0 - center).yx)
    a1 = math.atan2(*(p1 - center).yx)
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    pts = [center + Vector((math.cos(a0 + da * t / n), math.sin(a0 + da * t / n))) * r for t in range(n + 1)]
    # take the short or long way so the arc really bulges by `sag`
    if (pts[n // 2] - mid).length > abs(sag) * 1.5:
        da = da - math.copysign(2 * math.pi, da)
        pts = [center + Vector((math.cos(a0 + da * t / n), math.sin(a0 + da * t / n))) * r for t in range(n + 1)]
    return [tuple(p) for p in pts]


def lens(p0, p1, half_h):
    """Almond / leaf from p0 to p1 (px), half_h px thick each side."""
    return arc(p0, p1, half_h)[:-1] + arc(p1, p0, half_h)[:-1]


def piece(name, pts_px, front, depth, material, collection, bevel=0.004, pivot=None):
    """Extrude a px outline into a solid from y=-front back to y=-(front-depth).
    With pivot (px), the object's origin sits there so it can be rotated."""
    origin = w(*pivot, front) if pivot else Vector((0, 0, 0))
    bm = bmesh.new()
    verts = [bm.verts.new(w(x, y, front) - origin) for x, y in pts_px]
    face = bm.faces.new(verts)
    ext = bmesh.ops.extrude_face_region(bm, geom=[face], use_keep_orig=True)
    moved = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=moved, vec=Vector((0, depth, 0)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return finish(name, bm, origin, material, collection, bevel)


def finish(name, bm, origin, material, collection, bevel):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.set_sharp_from_angle(angle=math.radians(35))
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = origin
    collection.objects.link(obj)
    if bevel:
        mod = obj.modifiers.new("soft", "BEVEL")
        mod.width, mod.segments = bevel, 4
        mod.limit_method = "ANGLE"
        mod.harden_normals = True
    return obj


def primitive(op, name, material, collection, **kw):
    op(**kw)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    for col in obj.users_collection:
        col.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def eye(m, col):
    e = poster.EYE
    piece("eye_white", lens((e["x0"], e["cy"]), (e["x1"], e["cy"]), e["half_h"]), 0.09, 0.07,
          m["porcelain"], col, bevel=0.03)
    ix, iy, ir = e["iris"]
    c = w(ix, iy)
    r = ir * ap.PX
    primitive(bpy.ops.mesh.primitive_cylinder_add, "iris", m["tan"], col, vertices=96, radius=r, depth=0.012,
              location=(c.x, -0.096, c.z), rotation=(math.radians(90), 0, 0))
    primitive(bpy.ops.mesh.primitive_cylinder_add, "pupil", m["black_gloss"], col, vertices=64,
              radius=e["pupil"] * ap.PX, depth=0.012, location=(c.x, -0.1, c.z), rotation=(math.radians(90), 0, 0))
    dome = primitive(bpy.ops.mesh.primitive_uv_sphere_add, "cornea", m["glass"], col, segments=96, ring_count=48,
                     radius=r * 1.02, location=(c.x, -0.09, c.z))
    dome.scale = (1, 0.55, 1)
    b = poster.BROW
    # sag > 0 bulges to the right of travel: left->right goes down in px, so negate to arch up
    outer = arc((b["x0"], b["base_y"]), (b["x1"], b["base_y"]), -(b["base_y"] - b["outer_peak"]))
    inner = arc((b["x1"], b["base_y"] - 2), (b["x0"], b["base_y"] - 2), b["base_y"] - b["inner_peak"])
    piece("brow", outer[:-1] + inner[:-1], 0.24, 0.05, m["copper"], col, bevel=0.01)


def bee(m, col):
    b = poster.BEE
    r = b["half_w"] * ap.PX
    n = len(b["bands"])
    band_h = (b["bottom"] - b["top"]) / n
    for i, ink in enumerate(b["bands"]):
        y = b["top"] + band_h * (i + 0.5)
        c = w(b["cx"], y)
        end = i in (0, n - 1)
        obj = primitive(bpy.ops.mesh.primitive_cylinder_add, f"bee_band_{i}",
                        m["black_gloss"] if ink == "black" else m["bee_yellow"], col, vertices=96, radius=r,
                        depth=band_h * ap.PX * 0.9, location=(c.x, -(0.04 + r), c.z))
        mod = obj.modifiers.new("soft", "BEVEL")
        mod.width = r * 0.55 if end else 0.004
        mod.segments = 8 if end else 3
        mod.limit_method = "ANGLE"
    for i, (x, y, rr) in enumerate(b["eyes"]):
        c = w(x, y)
        primitive(bpy.ops.mesh.primitive_uv_sphere_add, f"bee_eye_{i}", m["pink"], col, segments=64, ring_count=32,
                  radius=rr * ap.PX, location=(c.x, -(0.04 + r * 0.9), c.z))
    wing = b["wing"]
    (rx, ry), (tx, ty) = wing["root"], wing["tip"]
    for side in (-1, 1):
        root = (b["cx"] + side * (b["cx"] - rx), ry)
        tip = (b["cx"] + side * (b["cx"] - tx), ty)
        obj = piece(f"bee_wing_{'lr'[side > 0]}", lens(root, tip, wing["width"] / 2), 0.04 + r, 0.012,
                    m["wing"], col, bevel=0.003, pivot=root)
        obj.rotation_euler = (0, 0, -math.radians(32) * side)  # wings lift towards the viewer


def striped_m(m, col):
    s = poster.M
    data = bpy.data.curves.new("M_glyph", "FONT")
    data.body = "M"
    data.font = bpy.data.fonts.load(FONT)
    data.extrude = 0.5
    text = bpy.data.objects.new("M_glyph", data)
    col.objects.link(text)
    dg = bpy.context.evaluated_depsgraph_get()
    glyph = bpy.data.meshes.new_from_object(text.evaluated_get(dg))
    bpy.data.objects.remove(text)
    xs = [v.co.x for v in glyph.vertices]
    ys = [v.co.y for v in glyph.vertices]
    left, top = w(s["x0"], s["top"]), w(s["x1"], s["bottom"])
    sx = (top.x - left.x) / (max(xs) - min(xs))
    sz = (left.z - top.z) / (max(ys) - min(ys))
    depth = 0.04
    unit = (s["bottom"] - s["top"]) / (2 * s["stripes"] - 1)
    for i in range(s["stripes"]):
        y0 = s["top"] + 2 * i * unit
        pivot = w((s["x0"] + s["x1"]) / 2, y0 + unit / 2, 0.16)
        bm = bmesh.new()
        bm.from_mesh(glyph)
        for v in bm.verts:
            v.co = Vector((left.x + (v.co.x - min(xs)) * sx, -0.16 + v.co.z * depth,
                           top.z + (v.co.y - min(ys)) * sz)) - pivot
        # keep only this stripe's slice of the glyph
        for z_cut, keep_above in ((w(0, y0)[2] - pivot.z, False), (w(0, y0 + unit)[2] - pivot.z, True)):
            res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                                         plane_co=(0, 0, z_cut), plane_no=(0, 0, 1),
                                         clear_outer=not keep_above, clear_inner=keep_above)
            edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
            bmesh.ops.holes_fill(bm, edges=edges)
        obj = finish(f"M_stripe_{i}", bm, pivot, m["blue_glass"], col, 0.002)
        # louvres: each slat turns a little further, like blinds opening
        obj.rotation_euler = (math.radians(-38) * i / (s["stripes"] - 1), 0, 0)
    bpy.data.meshes.remove(glyph)


def jade_material(name, srgb):
    """Translucent stone: light enters, scatters and glows back out in its colour."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    p = mat.node_tree.nodes["Principled BSDF"]
    lin = ap.srgb_to_linear(srgb)
    p.inputs["Base Color"].default_value = lin + (1.0,)
    p.inputs["Subsurface Weight"].default_value = 1.0
    p.inputs["Subsurface Radius"].default_value = (0.6, 1.0, 0.5)
    p.inputs["Subsurface Scale"].default_value = 0.03
    p.inputs["Roughness"].default_value = 0.15
    return mat


def setup():
    scene = ap.reset_scene()
    root = scene.collection
    cols = {n: bpy.data.collections.new(n) for n in ("Poster", "Studio", "Lights", "Cameras")}
    for c in cols.values():
        root.children.link(c)
    inks = poster.INKS
    velvet = ap.matte_material("black_velvet", inks["black"], 1.0, 0.0)
    ap.paper_board(poster, velvet, velvet, cols["Poster"])

    m = {
        "porcelain": ap.lacquer_material("porcelain", inks["white"]),
        "tan": ap.matte_material("iris_tan", inks["tan"], 0.6, 0.2),
        "black_gloss": ap.gloss_black_material("black_gloss", inks["black"]),
        "glass": ap.acrylic_material("cornea_glass", (0.98, 0.98, 0.98)),
        "copper": ap.matte_material("brow_copper", (0.55, 0.24, 0.13), 0.3),
        "bee_yellow": ap.lacquer_material("bee_yellow", inks["yellow"]),
        "pink": ap.lacquer_material("bee_pink", inks["pink"]),
        "wing": jade_material("wing_jade", inks["green"]),
        # on black velvet, glass has nothing to show: the slats carry their own light
        "blue_glass": ap.resin_material("m_blue_light", inks["blue"], 0.04, glow=0.5),
    }
    m["copper"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
    eye(m, cols["Poster"])
    bee(m, cols["Poster"])
    striped_m(m, cols["Poster"])

    ap.cyclorama(ap.matte_material("studio", (0.12, 0.115, 0.11), 0.9), cols["Studio"])
    world_ = bpy.data.worlds.new("World")
    world_.use_nodes = True
    world_.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.05
    scene.world = world_

    c = ap.poster_center(poster)
    L, C = cols["Lights"], cols["Cameras"]
    band = w(284, 380, 0.1)
    eye_c, bee_c, m_c = w(98, 380, 0.1), w(285, 395, 0.1), w(465, 370, 0.16)
    print_rig = [ap.sun_light("print_sun", L, (-0.07, -1.0, 0.06), 4.0, 1.5)]
    studio_rig = [
        ap.spot_light("studio_key", L, band + Vector((-2.6, -2.2, 2.4)), band, 9000, 40, 0.7, 0.12,
                      (1.0, 0.95, 0.88)),
        ap.area_light("studio_rim", L, band + Vector((2.8, -0.6, 0.8)), band, 1.2, 600, (0.8, 0.9, 1.0)),
        ap.area_light("studio_fill", L, band + Vector((0.3, -5, 0.2)), band, 5.0, 100),
    ]
    shots = {
        "front": ap.camera("cam_front", C, (0, -12, c.z), c, ortho_scale=poster.H * ap.PX),
        "three_quarter": ap.camera("cam_three_quarter", C, band + Vector((-1.6, -2.6, 0.5)), band, lens=40,
                                   dof=(band, 8)),
        "eye": ap.camera("cam_eye", C, eye_c + Vector((-0.55, -1.0, 0.25)), eye_c, lens=70, dof=(eye_c, 2.8)),
        "bee": ap.camera("cam_bee", C, bee_c + Vector((0.45, -1.0, -0.3)), bee_c, lens=70, dof=(bee_c, 2.8)),
        "louvres": ap.camera("cam_louvres", C, m_c + Vector((1.5, -1.0, 0.15)), m_c + Vector((-0.15, 0, 0)),
                             lens=50, dof=(m_c, 4)),
    }
    return scene, shots, (print_rig, studio_rig)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--shots", default="front,three_quarter,eye,bee,louvres")
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--samples", type=int, default=128)
    p.add_argument("--exposure", type=float, default=-0.5)
    p.add_argument("--no-render", action="store_true")
    args = p.parse_args(argv)

    scene, shots, (print_rig, studio_rig) = setup()
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "build", "eye-bee-m.blend"), compress=True)
    if args.no_render:
        return
    size = (round(FULL[0] * args.scale), round(FULL[1] * args.scale))
    front_size = (round(poster.W / poster.H * FULL[1] * args.scale), size[1])
    for name in filter(None, args.shots.split(",")):
        front = name == "front"
        ap.render(scene, shots[name], os.path.join(HERE, "build", "renders", f"{name}.png"),
                  front_size if front else size, args.samples, print_rig if front else studio_rig,
                  print_rig + studio_rig, "Standard", 1 / 3 if front else 0.8, 0.0 if front else args.exposure)


if __name__ == "__main__":
    main()
